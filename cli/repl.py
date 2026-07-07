import asyncio
import json
import websockets
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console

console = Console()

async def listen_to_broker(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            text = data.get("message", "")
            
            if msg_type in ["system", "event"]:
                # Print using rich. It will safely patch above the prompt bar.
                if text.startswith("Broker >"):
                    console.print(f"[bold cyan]{text}[/bold cyan]")
                elif text.startswith("You >"):
                    console.print(f"[dim]{text}[/dim]")
                else:
                    console.print(text)
    except websockets.exceptions.ConnectionClosed:
        console.print("[bold red]Connection to broker closed.[/bold red]")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        console.print(f"[bold red]Listener Error:[/] {e}")

async def run_repl():
    uri = "ws://localhost:8000/ws/broker/"
    session = PromptSession()
    
    console.print("[bold green]Starting Omnigent CLI...[/bold green]")
    
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            console.print("[bold green]Connected to Django WebSocket API![/bold green]")
            
            # Start the background listener task
            listener_task = asyncio.create_task(listen_to_broker(websocket))
            
            # Run the prompt loop
            with patch_stdout():
                while True:
                    try:
                        # Wait for user input asynchronously
                        user_input = await session.prompt_async("Omni > ")
                        
                        if not user_input.strip():
                            continue
                            
                        if user_input.strip().lower() in ["exit", "quit"]:
                            break
                            
                        # Handle local shell commands
                        if user_input.startswith("!"):
                            command = user_input[1:].strip()
                            console.print(f"[bold blue]Local Shell >[/bold blue] {command}")
                            try:
                                result = subprocess.run(
                                    command, shell=True, text=True, 
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                                )
                                output = result.stdout.strip()
                                if output:
                                    console.print(f"[dim]{output}[/dim]")
                                else:
                                    console.print("[dim](No output)[/dim]")
                            except Exception as e:
                                console.print(f"[bold red]Shell Error:[/] {e}")
                            continue

                        # Send normal message to broker
                        await websocket.send(json.dumps({
                            "message": user_input
                        }))
                        
                    except (EOFError, KeyboardInterrupt):
                        break
            
            listener_task.cancel()
            
    except ConnectionRefusedError:
        console.print("[bold red]Failed to connect to backend. Is Docker running?[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")

def main():
    try:
        asyncio.run(run_repl())
    except KeyboardInterrupt:
        pass
