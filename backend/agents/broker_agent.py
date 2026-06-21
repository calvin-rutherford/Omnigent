import os
import json
import litellm
from django.conf import settings
from .models import Agent, EventLog

def spawn_agent(name: str, task: str, scope: str) -> str:
    from .tasks import run_agent_loop
    agent = Agent.objects.create(name=name, scope=scope, status='Waiting')
    EventLog.objects.create(agent=agent, event_type='AgentCreated', payload={'name': name, 'scope': scope, 'initial_task': task})
    run_agent_loop.delay(agent.id, task)
    return f"Successfully spawned agent '{name}' (ID: {agent.id}) to handle task: {task}"

class BrokerAgent:
    def __init__(self):
        self.model = getattr(settings, 'DEFAULT_LLM_MODEL', os.getenv('DEFAULT_LLM_MODEL', 'gemini/gemini-1.5-pro'))
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "spawn_agent",
                    "description": "Spawns a new Celery Worker AI Agent to handle a specific task.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "A short name for the agent (e.g. 'Frontend Dev')"},
                            "task": {"type": "string", "description": "The detailed task the agent needs to accomplish"},
                            "scope": {"type": "string", "description": "The area of the project the agent is restricted to (e.g. 'frontend', 'docs')"}
                        },
                        "required": ["name", "task", "scope"]
                    }
                }
            }
        ]
        
    def process_message(self, user_text: str) -> str:
        messages = [
            {"role": "system", "content": "You are the Omnigent Broker. You manage a fleet of AI agents. When the user asks you to do something complex, use the `spawn_agent` tool to delegate it to a specialized agent. Do not do the work yourself."},
            {"role": "user", "content": user_text}
        ]
        
        try:
            # First call to the LLM
            response = litellm.completion(
                model=self.model,
                messages=messages,
                tools=self.tools
            )
            
            message = response.choices[0].message
            
            # Check if the model decided to call a function
            if message.tool_calls:
                messages.append(message) # Append the assistant's tool call message
                
                for tool_call in message.tool_calls:
                    if tool_call.function.name == 'spawn_agent':
                        args = json.loads(tool_call.function.arguments)
                        result_msg = spawn_agent(**args)
                        
                        # Provide the result back to the LLM
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": "spawn_agent",
                            "content": json.dumps({"result": result_msg})
                        })
                
                # Second call to get the final response based on tool output
                second_response = litellm.completion(
                    model=self.model,
                    messages=messages
                )
                return second_response.choices[0].message.content
            
            return message.content or ""
            
        except Exception as e:
            return f"Broker encountered an error: {str(e)}"
