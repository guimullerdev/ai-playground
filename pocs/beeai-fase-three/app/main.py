import sys
import os
import json

# Make project root importable from anywhere
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_APP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _APP)

from anthropic import Anthropic

from agents.assistant import ASSISTANT_NAME, ASSISTANT_DESCRIPTION, ASSISTANT_SYSTEM_PROMPT
from agents.creative import CREATIVE_NAME, CREATIVE_DESCRIPTION, CREATIVE_SYSTEM_PROMPT
from agents.critic import CRITIC_NAME, CRITIC_DESCRIPTION, CRITIC_SYSTEM_PROMPT
from tools.weather import get_weather, WEATHER_TOOL_SCHEMA
from tools.search import search_web, SEARCH_TOOL_SCHEMA
from tools.calculator import calculate, CALCULATOR_TOOL_SCHEMA
from tools.summarizer import summarize_text, SUMMARIZER_TOOL_SCHEMA
from ui import (
    console,
    print_welcome,
    print_agent_picker,
    print_agent_message,
    print_tool_call,
    print_tool_result,
    print_history,
    print_help,
    _color,
)

AGENTS = [
    {"name": ASSISTANT_NAME, "description": ASSISTANT_DESCRIPTION, "system": ASSISTANT_SYSTEM_PROMPT},
    {"name": CREATIVE_NAME, "description": CREATIVE_DESCRIPTION, "system": CREATIVE_SYSTEM_PROMPT},
    {"name": CRITIC_NAME, "description": CRITIC_DESCRIPTION, "system": CRITIC_SYSTEM_PROMPT},
]

TOOLS = [WEATHER_TOOL_SCHEMA, SEARCH_TOOL_SCHEMA, CALCULATOR_TOOL_SCHEMA, SUMMARIZER_TOOL_SCHEMA]

TOOL_FNS = {
    "get_weather": get_weather,
    "search_web": search_web,
    "calculate": calculate,
    "summarize_text": summarize_text,
}


def pick_agent(prompt: str = "Choose an agent (1-3): ") -> dict:
    print_agent_picker([(a["name"], a["description"]) for a in AGENTS])
    while True:
        try:
            raw = console.input(f"\n[bold]{prompt}[/bold]").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(AGENTS):
                return AGENTS[idx]
        except (ValueError, KeyboardInterrupt):
            pass
        console.print("[red]Invalid choice, try again.[/red]")


def run_agent_turn(client: Anthropic, agent: dict, histories: dict) -> str:
    """Agentic loop: runs until the model stops calling tools and returns the final reply."""
    messages = histories[agent["name"]]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=agent["system"],
            tools=TOOLS,
            messages=messages,
        )

        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        if tool_calls:
            # Append the full assistant turn (may include text + tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tc in tool_calls:
                print_tool_call(tc.name, tc.input)
                fn = TOOL_FNS.get(tc.name)
                if fn:
                    result = fn(**tc.input)
                else:
                    result = {"ok": False, "data": None, "error": f"Unknown tool: {tc.name}"}
                print_tool_result(tc.name, result)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": json.dumps(result),
                    }
                )

            messages.append({"role": "user", "content": tool_results})
            continue  # get the model's reply after seeing tool results

        # Final text response — no more tool calls
        messages.append({"role": "assistant", "content": response.content})
        return "\n".join(text_parts)


def main():
    client = Anthropic()
    histories = {a["name"]: [] for a in AGENTS}

    print_welcome()
    current = pick_agent()
    c = _color(current["name"])
    console.print(
        f"\n[bold]Talking to [bold {c}]{current['name']}[/bold {c}].[/bold] "
        f"Type [dim]/help[/dim] for commands.\n"
    )

    while True:
        try:
            user_input = console.input("[bold white]You:[/bold white] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            console.print("[dim]Goodbye.[/dim]")
            break
        elif user_input == "/help":
            print_help()
            continue
        elif user_input == "/switch":
            current = pick_agent("Switch to agent (1-3): ")
            c = _color(current["name"])
            console.print(f"\n[bold]Switched to [bold {c}]{current['name']}[/bold {c}].[/bold]\n")
            continue
        elif user_input == "/history":
            print_history(current["name"], histories[current["name"]])
            continue

        histories[current["name"]].append({"role": "user", "content": user_input})

        with console.status(f"[dim]{current['name']} is thinking…[/dim]"):
            reply = run_agent_turn(client, current, histories)

        print_agent_message(current["name"], reply)


if __name__ == "__main__":
    main()
