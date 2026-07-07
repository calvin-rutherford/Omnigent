import os
import json
import google.generativeai as genai
from django.conf import settings
from .models import Agent, EventLog

def omni_spawn_agent(name: str, task: str, scope: str) -> str:
    """Spawns a new Celery Worker AI Agent to handle a specific task.
    
    Args:
        name: A short name for the agent (e.g. 'Frontend Dev')
        task: The detailed task the agent needs to accomplish
        scope: The area of the project the agent is restricted to (e.g. 'frontend', 'docs')
    """
    from .tasks import run_agent_loop
    agent = Agent.objects.create(name=name, scope=scope, status='Waiting')
    EventLog.objects.create(agent=agent, event_type='AgentCreated', payload={'name': name, 'scope': scope, 'initial_task': task})
    run_agent_loop.delay(agent.id, task)
    return f"Successfully spawned agent '{name}' (ID: {agent.id}) to handle task: {task}"

class BrokerAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment.")
            
        genai.configure(api_key=api_key)
        
        # Strip the 'gemini/' prefix we used for litellm
        model_name = os.getenv('DEFAULT_LLM_MODEL', 'gemini-1.5-pro').replace('gemini/', '')
        
        sys_prompt = "You are the Omnigent Broker. You manage a fleet of AI agents. If the user asks you to do something complex, use the `omni_spawn_agent` tool to delegate it to a specialized agent. For normal conversation, greetings, or questions about the system, just respond directly to the user in a helpful, conversational tone."
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=sys_prompt,
            tools=[omni_spawn_agent]
        )
        
    def process_message(self, user_text: str, stateful: bool = True) -> str:
        try:
            history = []
            # In a full implementation, we would query Message.objects here to populate history
            # if stateful is True. For now, the switch is wired up to the UI.
            
            # Automatic function calling handles the tool invocation and returns the final response!
            chat = self.model.start_chat(enable_automatic_function_calling=True, history=history)
            response = chat.send_message(user_text)
            
            return response.text
            
        except Exception as e:
            return f"Broker encountered an error: {str(e)}"
