from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box

console = Console()

AGENT_COLORS = {
    "Assistant": "blue",
    "Creative": "magenta",
    "Critic": "red",
}


def _color(name: str) -> str:
    return AGENT_COLORS.get(name, "white")


def print_welcome():
    console.print(
        Panel(
            "[bold]BeeAI Phase Three[/bold]\n"
            "Multi-personality agents · Tool use · Security testing",
            style="cyan",
            padding=(1, 4),
        )
    )


def print_agent_picker(agents: list[tuple[str, str]]):
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Agent")
    table.add_column("Description")
    for i, (name, desc) in enumerate(agents, 1):
        c = _color(name)
        table.add_row(str(i), f"[{c}]{name}[/{c}]", desc)
    console.print(table)


def print_user_message(text: str):
    console.print(f"\n[bold white]You:[/bold white] {text}")


def print_agent_message(agent_name: str, text: str):
    c = _color(agent_name)
    console.print(
        Panel(text, title=f"[bold {c}]{agent_name}[/bold {c}]", border_style=c, padding=(0, 1))
    )


def print_tool_call(tool_name: str, tool_input: dict):
    args = ", ".join(f"{k}={v!r}" for k, v in tool_input.items())
    console.print(f"  [dim]→ [italic]{tool_name}[/italic]({args})[/dim]")


def print_tool_result(tool_name: str, result: dict):
    if result["ok"]:
        console.print(f"  [dim]← {tool_name} returned[/dim]")
    else:
        console.print(f"  [dim red]← {tool_name} error: {result['error']}[/dim red]")


def print_history(agent_name: str, messages: list):
    c = _color(agent_name)
    console.print(Rule(f"[{c}]History · {agent_name}[/{c}]"))
    if not messages:
        console.print("[dim]  (no messages yet)[/dim]")
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            if isinstance(content, str):
                console.print(f"[bold white]You:[/bold white] {content}")
        elif role == "assistant":
            if isinstance(content, list):
                for block in content:
                    if hasattr(block, "text"):
                        console.print(f"[{c}]{agent_name}:[/{c}] {block.text}")
            elif isinstance(content, str):
                console.print(f"[{c}]{agent_name}:[/{c}] {content}")
    console.print(Rule())


def print_help():
    console.print(
        Panel(
            "/switch   — pick a different agent\n"
            "/history  — view conversation log for the active agent\n"
            "/quit     — exit",
            title="Commands",
            style="dim",
        )
    )
