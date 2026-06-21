import json
import asyncio
import websockets
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Log, Static, Input
from textual.containers import Horizontal, Vertical
from textual import work

class OmnigentApp(App):
    """A Textual app to manage the Omnigent AI fleet via WebSockets."""

    CSS = """
    Screen { layout: vertical; }
    #main_container { height: 1fr; }
    #sidebar { width: 30; dock: left; border: solid green; }
    #agent_list { height: 2fr; border: solid blue; }
    #event_log { height: 1fr; border: solid cyan; }
    #command_input { dock: bottom; margin: 1; }
    """

    def __init__(self):
        super().__init__()
        self.websocket = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("Inbox:\n- 0 messages", id="sidebar"),
            Vertical(
                DataTable(id="agent_list"),
                Log(id="event_log"),
                id="main_container"
            )
        )
        yield Input(placeholder="Ask the Broker to spawn an agent or analyze something...", id="command_input")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Status", "Scope", "Last Update")
        
        log = self.query_one(Log)
        log.write_line("Omnigent TUI initialized.")
        
        # Start the background websocket listener
        self.connect_to_broker()

    @work(exclusive=True)
    async def connect_to_broker(self) -> None:
        log = self.query_one(Log)
        uri = "ws://localhost:8000/ws/broker/"
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                log.write_line("[bold green]Connected to Django WebSocket API![/]")
                
                # Listen for messages forever
                async for message in websocket:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    text = data.get("message", "")
                    
                    if msg_type in ["system", "event"]:
                        # Since we are updating UI from a worker, we must use call_from_thread
                        self.call_from_thread(log.write_line, text)
                        
                        # In the future, parse AgentCreated events to update DataTable here
                        
        except Exception as e:
            self.call_from_thread(log.write_line, f"[bold red]Connection error:[/] {e}")

    @work
    async def send_message_to_broker(self, message_text: str) -> None:
        if self.websocket and self.websocket.open:
            await self.websocket.send(json.dumps({
                "message": message_text
            }))
        else:
            log = self.query_one(Log)
            self.call_from_thread(log.write_line, "[bold red]Cannot send: Not connected to broker.[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value
        if message.strip():
            self.send_message_to_broker(message)
        event.input.value = ""

if __name__ == "__main__":
    app = OmnigentApp()
    app.run()
