import time
import uuid
import subprocess
import redis
import os
from django.conf import settings
from celery import shared_task
import google.generativeai as genai
from .models import Agent, EventLog, Message

# Connect to Redis for approvals
r = redis.Redis.from_url(settings.CELERY_RESULT_BACKEND)

def execute_bash(command: str) -> str:
    """Executes a bash command inside the persistent isolated sandbox.
    Requires human approval before execution.
    
    Args:
        command: The bash command to execute (e.g. 'ls -la' or 'python test.py')
    """
    approval_id = str(uuid.uuid4())[:8]
    r.set(f"approval:{approval_id}", "pending")
    
    # Broadcast approval request to UI
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'broker_events',
        {
            'type': 'approval_request',
            'approval_id': approval_id,
            'command': command
        }
    )
    
    # Polling loop
    while True:
        status = r.get(f"approval:{approval_id}")
        if status:
            status = status.decode('utf-8')
            if status == "approved":
                break
            elif status == "denied":
                return f"Error: The user DENIED permission to run '{command}'."
        time.sleep(1)
        
    # Execute in sandbox using docker exec
    try:
        # We assume the sandbox container is named 'omnigent-sandbox'
        result = subprocess.run(
            ["docker", "exec", "omnigent-sandbox", "bash", "-c", command],
            capture_output=True, text=True, timeout=120
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Execution Failed: {str(e)}"

@shared_task
def run_agent_loop(agent_id, initial_task):
    try:
        agent = Agent.objects.get(id=agent_id)
        agent.status = 'Running'
        agent.save()

        EventLog.objects.create(agent=agent, event_type='TaskAssigned', payload={'task': initial_task})
        Message.objects.create(agent=agent, role='user', content=initial_task)
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
            
        genai.configure(api_key=api_key)
        model_name = os.getenv('DEFAULT_LLM_MODEL', 'gemini-1.5-pro').replace('gemini/', '')
        
        sys_prompt = f"You are an AI Agent named {agent.name} with scope {agent.scope}. Solve the task. Use the execute_bash tool to run commands in your secure Ubuntu sandbox."
        model = genai.GenerativeModel(model_name=model_name, system_instruction=sys_prompt, tools=[execute_bash])
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(initial_task)
        
        Message.objects.create(agent=agent, role='model', content=response.text)
        
        EventLog.objects.create(agent=agent, event_type='TaskCompleted', payload={'result': response.text})
        agent.status = 'Complete'
        agent.save()
        return "Task Completed"

    except Exception as e:
        if 'agent' in locals():
            agent.status = 'Error'
            agent.save()
            EventLog.objects.create(agent=agent, event_type='Error', payload={'error': str(e)})
        return f"Failed: {str(e)}"

@shared_task
def process_broker_message(user_text: str, stateful: bool = True):
    from .broker_agent import BrokerAgent
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    broker = BrokerAgent()
    response_text = broker.process_message(user_text, stateful=stateful)
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'broker_events',
        {
            'type': 'broker_event',
            'message': f"Broker > {response_text}"
        }
    )
