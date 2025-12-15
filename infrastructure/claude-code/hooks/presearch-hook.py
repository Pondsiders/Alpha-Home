#!/usr/bin/env python3
"""
Presearch Hook

A UserPromptSubmit hook that automatically searches Pond based on the user's
prompt BEFORE Alpha sees it. Injects relevant memories as additionalContext.

Uses Haiku to extract search queries from natural language prompts.
Skips trivial prompts (greetings, short affirmations, etc.).

Location: Alpha-Home/infrastructure/claude-code/hooks/
"""

import json
import subprocess
import sys
import urllib.request

# Pond API config
POND_API_URL = "http://raspberrypi:8000/api/v1/search"
POND_API_KEY = "pond_sk_e3U_rmqjoyEHobkgWI8llY4XGoeI91qYwCtTjg7RIvA"

# Haiku prompt for query extraction
HAIKU_SYSTEM_PROMPT = """You extract search queries from user prompts for a semantic memory system.

Given a user's message to an AI assistant, output ONLY:
- A search query (keywords/concepts to search for), OR
- The word SKIP if the prompt doesn't need memory context

SKIP for: greetings, short affirmations ("yes", "ok", "thanks"), meta-commands,
trivial chitchat, or anything where past memories wouldn't help.

Extract search terms for: questions about past events, references to previous work,
topics that might have history, people, projects, technical concepts.

Output ONLY the query or SKIP. No explanation. No punctuation unless part of the query."""


def extract_query_with_haiku(prompt: str) -> str | None:
    """Use Haiku to extract a search query from the prompt."""
    try:
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--model", "haiku",
                "--setting-sources", "",  # Bypass all config
                "--no-session-persistence",
                "--system-prompt", HAIKU_SYSTEM_PROMPT,
                "--tools", "",  # Pure inference, no tools
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=10,
        )

        query = result.stdout.strip()

        if query.upper() == "SKIP" or not query:
            return None

        return query

    except Exception as e:
        # On any error, just skip presearch
        return None


def search_pond(query: str, limit: int = 3) -> list[dict]:
    """Search Pond via REST API."""
    try:
        data = json.dumps({"query": query, "limit": limit}).encode('utf-8')

        req = urllib.request.Request(
            POND_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": POND_API_KEY,
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("memories", [])

    except Exception as e:
        return []


def format_memory(memory: dict) -> str:
    """Format a single memory for display."""
    content = memory.get("content", "")
    # Truncate long memories
    if len(content) > 500:
        content = content[:500] + "..."
    return content


def build_context(prompt: str, query: str | None, memories: list[dict]) -> str:
    """Build the additionalContext string with debugging info."""
    parts = []

    parts.append("**🔍 Presearch Debug:**")

    # Show truncated prompt
    prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
    prompt_preview = prompt_preview.replace('\n', ' ')
    parts.append(f"- Prompt: \"{prompt_preview}\"")

    # Show Haiku's decision
    if query is None:
        parts.append("- Haiku: SKIP")
        return "\n".join(parts)

    parts.append(f"- Haiku query: \"{query}\"")
    parts.append(f"- Pond returned: {len(memories)} memories")

    if memories:
        parts.append("")
        parts.append("**📚 Relevant memories:**")
        for i, mem in enumerate(memories, 1):
            parts.append(f"\n**[{i}]**")
            parts.append(format_memory(mem))

    return "\n".join(parts)


def main():
    # Read hook input
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    # Get the user's prompt
    prompt = input_data.get("prompt", "")

    if not prompt:
        # No prompt, nothing to do
        print(json.dumps({}))
        sys.exit(0)

    # Extract search query with Haiku
    query = extract_query_with_haiku(prompt)

    # Search Pond if we have a query
    memories = []
    if query:
        memories = search_pond(query, limit=3)

    # Build context (always include debug info for now)
    additional_context = build_context(prompt, query, memories)

    # Output
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
