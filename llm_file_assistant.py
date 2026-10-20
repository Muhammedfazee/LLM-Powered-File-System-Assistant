"""Command-line LLM assistant that can call the file-system tools."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from fs_tools import list_files, read_file, search_in_file, write_file


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Extract text and metadata from a PDF, TXT, or DOCX file.",
            "parameters": {
                "type": "object",
                "properties": {"filepath": {"type": "string"}},
                "required": ["filepath"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory, optionally filtered by extension.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "extension": {"type": ["string", "null"]},
                },
                "required": ["directory", "extension"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file, creating parent directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["filepath", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search a supported document for a keyword, ignoring case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "keyword": {"type": "string"},
                },
                "required": ["filepath", "keyword"],
                "additionalProperties": False,
            },
        },
    },
]


def _workspace_path(workspace: Path, supplied_path: str) -> str:
    candidate = Path(supplied_path)
    resolved = (workspace / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if not resolved.is_relative_to(workspace):
        raise ValueError("Tool path must stay within the configured workspace.")
    return str(resolved)


def _execute_tool(
    name: str, arguments: dict[str, Any], workspace: Path
) -> dict[str, Any] | list[dict[str, Any]]:
    if name == "read_file":
        return read_file(_workspace_path(workspace, arguments["filepath"]))
    if name == "list_files":
        return list_files(
            _workspace_path(workspace, arguments["directory"]),
            arguments["extension"],
        )
    if name == "write_file":
        return write_file(
            _workspace_path(workspace, arguments["filepath"]),
            arguments["content"],
        )
    if name == "search_in_file":
        return search_in_file(
            _workspace_path(workspace, arguments["filepath"]),
            arguments["keyword"],
        )
    raise ValueError(f"Unknown tool requested: {name}")


def create_client() -> OpenAI:
    """Create an OpenRouter client using the project .env or environment key."""
    load_dotenv(Path(__file__).resolve().with_name(".env"))
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Set it in your environment before running."
        )
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def run_assistant(query: str, workspace: Path, model: str) -> str:
    """Run the LLM tool-call loop and return its final response."""
    client = create_client()
    workspace = workspace.resolve()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a file assistant. Use the provided tools for file operations. "
                "Tool paths are relative to the configured workspace; never invent "
                "file contents. Report tool errors clearly."
            ),
        },
        {"role": "user", "content": query},
    ]

    for _ in range(8):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content or ""

        messages.append(message)
        for tool_call in message.tool_calls:
            arguments = json.loads(tool_call.function.arguments)
            try:
                result = _execute_tool(
                    tool_call.function.name, arguments, workspace
                )
            except (KeyError, TypeError, ValueError) as exc:
                result = {"success": False, "error": str(exc)}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError("The assistant exceeded the maximum of 8 tool-call rounds.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="What you want the assistant to do")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).parent / "resumes",
        help="Directory that tool calls are allowed to access",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="OpenRouter model with tool-calling support (default: openrouter/free)",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        parser.error(f"Workspace directory does not exist: {workspace}")
    print(run_assistant(args.query, workspace, args.model))


if __name__ == "__main__":
    main()
