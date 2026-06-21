import time
from celery import shared_task
from .models import Agent, EventLog, Message
from .providers import UniversalProvider

@shared_task
def run_agent_loop(agent_id, initial_task):
    """
    This task simulates the lifecycle of an AI Agent.
    It reads context, talks to Gemini, and posts events back to the broker.
    """
    try:
        agent = Agent.objects.get(id=agent_id)
        
        # Log task start
        EventLog.objects.create(
            agent=agent,
            event_type='TaskAssigned',
            payload={'task': initial_task}
        )
        
        agent.status = 'Running'
        agent.save()

        # Initialize Universal Provider
        from .providers import UniversalProvider
        provider = UniversalProvider()
        
        # Save initial user message
        Message.objects.create(agent=agent, role='user', content=initial_task)
        
        # Simulate thinking / processing
        # Send prompt to LLM
        system_prompt = f"You are an AI Agent named {agent.name} with scope {agent.scope}. Solve this task."
        response = provider.generate_content(system_prompt=system_prompt, user_prompt=initial_task)
        
        # Save model response
        Message.objects.create(agent=agent, role='model', content=response)
        
        # Log completion
        EventLog.objects.create(
            agent=agent,
            event_type='TaskCompleted',
            payload={'result': response}
        )

        agent.status = 'Complete'
        agent.save()
        
        return "Task Completed"

    except Exception as e:
        if 'agent' in locals():
            agent.status = 'Error'
            agent.save()
            EventLog.objects.create(
                agent=agent,
                event_type='Error',
                payload={'error': str(e)}
            )
        return f"Failed: {str(e)}"

@shared_task
def process_broker_message(user_text: str):
    """
    Takes a natural language message from the TUI, runs it through the BrokerAgent,
    and broadcasts the result back to the TUI via Channels.
    """
    from .broker_agent import BrokerAgent
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    broker = BrokerAgent()
    response_text = broker.process_message(user_text)
    
    # Send the response back to the WebSocket group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'broker_events',
        {
            'type': 'broker_event',
            'message': f"Broker > {response_text}"
        }
    )

