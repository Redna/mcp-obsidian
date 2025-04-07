import argparse
import json
import logging
import os

from typing import Literal
from collections.abc import Sequence
from dotenv import load_dotenv
from mcp.server import FastMCP
from pydantic import Field

from mcp.types import (
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from mcp_obsidian import obsidian

load_dotenv()

api_key = os.getenv("OBSIDIAN_API_KEY", "")
if api_key == "":
    raise ValueError(f"OBSIDIAN_API_KEY environment variable required. Working directory: {os.getcwd()}")


mcp = FastMCP(
    name="mcp-obsidian",
    instructions="Obsidian plugin for MCP",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-obsidian")


@mcp.tool(
    description="List all files and directories in the root directory of your Obsidian vault.",
)
def obsidian_list_files_in_vault() -> str:
    api = obsidian.Obsidian(api_key=api_key)

    files = api.list_files_in_vault()

    return [
        TextContent(
            type="text",
            text=json.dumps(files, indent=2)
        )
    ]


@mcp.tool(
    description="List all files and directories that exist in a specific Obsidian directory.",
)
def obsidian_list_files_in_dir(
    dirpath: str = Field(..., description="Path to list files from (relative to your vault root). Note that empty directories will not be returned.")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)

    files = api.list_files_in_dir(dirpath)

    return json.dumps(files, indent=2)

@mcp.tool(
    description="Return the content of a single file in your vault.",
)
def obsidian_get_file_contents(
    filepath: str = Field(..., description="Path to the relevant file (relative to your vault root).")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)

    content = api.get_file_contents(filepath)

    return json.dumps(content, indent=2)

@mcp.tool(
    description="Simple search for documents matching a specified text query across all files in the vault. Use this tool when you want to do a simple text search",
)
def obsidian_simple_search(
    query: str = Field(..., description="Text to a simple search for in the vault."),
    context_length: int = Field(100, description="How much context to return around the matching string (default: 100)")
) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    results = api.search(query, context_length)

    formatted_results = []
    for result in results:
        formatted_matches = []
        for match in result.get('matches', []):
            context = match.get('context', '')
            match_pos = match.get('match', {})
            start = match_pos.get('start', 0)
            end = match_pos.get('end', 0)

            formatted_matches.append({
                'context': context,
                'match_position': {'start': start, 'end': end}
            })

        formatted_results.append({
            'filename': result.get('filename', ''),
            'score': result.get('score', 0),
            'matches': formatted_matches
        })

    return json.dumps(formatted_results, indent=2)

@mcp.tool(
    description="Append content to a new or existing file in the vault.",
)
def obsidian_append_content(
    filepath: str = Field(..., description="Path to the relevant file (relative to your vault root)."),
    content: str = Field(..., description="Content to append to the file")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    api.append_content(filepath, content)

    return f"Successfully appended content to {filepath}"


@mcp.tool(
    description="Insert content into an existing note relative to a heading, block reference, or frontmatter field.",
)
def obsidian_patch_content(
    filepath: str = Field(..., description="Path to the relevant file (relative to your vault root)."),
    operation: Literal["append", "prepend", "replace"] = Field(..., description="Operation to perform (append, prepend, or replace)"),
    target_type: Literal["heading", "block", "frontmatter"] = Field(..., description="Operation to perform (append, prepend, or replace)"),
    target: str = Field(..., description="Target identifier (heading path, block reference, or frontmatter field)"),
    content: str = Field(..., description="Content to insert")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    api.patch_content(filepath, operation, target_type, target, content)

    return f"Successfully patched content in {filepath}"

@mcp.tool(
    description="Delete a file or directory from the vault.",
)
def obsidian_delete_file(
    filepath: str = Field(..., description="Path to the relevant file (relative to your vault root)."),
    confirm: bool = Field(..., description="Confirmation to delete the file (must be true)")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    api.delete_file(filepath)
    return f"Successfully deleted {filepath}"

@mcp.tool(
    description="Complex search for documents using a JsonLogic query. Supports standard JsonLogic operators plus 'glob' and 'regexp' for pattern matching. Results must be non-falsy.",
)
def obsidian_complex_search(
    query: dict = Field(..., description="JsonLogic query object. Example: {\"glob\": [\"*.md\", {\"var\": \"path\"}]} matches all markdown files")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    results = api.search_json(query)

    return json.dumps(results, indent=2)

@mcp.tool(
    description="Return the contents of multiple files in your vault, concatenated with headers.",
)
def obsidian_batch_get_file_contents(
    filepaths: list[str] = Field(..., description="List of file paths to read")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    content = api.get_batch_file_contents(filepaths)
    return content

@mcp.tool(
    description="Get current periodic note for the specified period.",
)
def obsidian_get_periodic_note(
    period: Literal["daily", "weekly", "monthly", "quarterly", "yearly"] = Field(..., description="The period type (daily, weekly, monthly, quarterly, yearly)")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    content = api.get_periodic_note(period)
    return content

@mcp.tool(
    description="Get most recent periodic notes for the specified period type.",
)
def obsidian_get_recent_periodic_notes(
    period: Literal["daily", "weekly", "monthly", "quarterly", "yearly"] = Field(..., description="The period type (daily, weekly, monthly, quarterly, yearly)"),
    limit: int = Field(5, description="Maximum number of notes to return (default: 5)", ge=1, le=50),
    include_content: bool = Field(False, description="Whether to include note content (default: false)")
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    results = api.get_recent_periodic_notes(period, limit, include_content)
    return json.dumps(results, indent=2)

@mcp.tool(
    description="Get recently modified files in the vault.",
)
def obsidian_get_recent_changes(
    limit: int = Field(10, description="Maximum number of files to return (default: 10)", ge=1, le=100),
    days: int = Field(90, description="Only include files modified within this many days (default: 90)", ge=1)
    ) -> str:
    api = obsidian.Obsidian(api_key=api_key)
    results = api.get_recent_changes(limit, days)
    return json.dumps(results, indent=2)

def main():
    """Main entry point for the server, handling argument parsing and server startup."""
    parser = argparse.ArgumentParser(description="Run the MCP Obsidian server.")
    parser.add_argument(
        '--transport',
        choices=['stdio', 'sse'],
        default='stdio',
        help='Transport protocol to use (stdio or sse). Default: stdio'
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host for SSE server.'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8001,
        help='Port for SSE server.'
    )


    args = parser.parse_args()

    mcp.settings.host = args.host
    mcp.settings.port = args.port

    logger.info(f"Starting server with {args.transport} transport...")

    mcp.run(args.transport)


if __name__ == "__main__":
    main()