#!/usr/bin/env python3
"""Interactive CLI for the building code assistant."""

import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from loguru import logger

from src.config import LLAMACPP_HOST, LOG_LEVEL
from src.agent.graph import build_agent


def _print_response(messages: list) -> None:
    """Print the final AI response and any tool calls that were made."""
    tool_calls_made: list[str] = []

    for msg in messages:
        if isinstance(msg, AIMessage):
            # Collect tool call names for the trace line
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_made.append(f"{tc['name']}({tc['args'].get('query') or tc['args'].get('reference', '')})")
            elif msg.content:
                # Final answer
                if tool_calls_made:
                    print(f"\n\033[2m[retrieved via: {' → '.join(tool_calls_made)}]\033[0m")
                print(f"\nAssistant: {msg.content}")


def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=LOG_LEVEL, colorize=True)

    print(f"Building code assistant (LLM: {LLAMACPP_HOST})")
    print("Loading models…")

    try:
        agent = build_agent()
    except Exception as exc:
        print(f"\nFailed to initialise agent: {exc}")
        print("Make sure Qdrant is running and the llama.cpp server is up at", LLAMACPP_HOST)
        sys.exit(1)

    print("Ready. Type your question, or 'exit' to quit.\n")

    conversation: list = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("Bye.")
            break

        conversation.append(HumanMessage(content=user_input))

        try:
            result = agent.invoke({"messages": conversation})
        except Exception as exc:
            print(f"\nError: {exc}")
            print("Is the llama.cpp server running at", LLAMACPP_HOST, "?")
            # Remove the message that failed so conversation stays consistent
            conversation.pop()
            continue

        conversation = result["messages"]
        _print_response(conversation)


if __name__ == "__main__":
    main()
