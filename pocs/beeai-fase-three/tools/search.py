SEARCH_TOOL_SCHEMA = {
    "name": "search_web",
    "description": "Search the web for information about a topic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            }
        },
        "required": ["query"],
    },
}

_MOCK_SNIPPETS = [
    "According to multiple sources, this is a well-documented subject with broad consensus in the literature.",
    "A 2024 study found significant correlations, prompting renewed interest from researchers across disciplines.",
    "Experts remain divided on the long-term implications, though recent data suggests a clearer trend is emerging.",
    "Historical records indicate this phenomenon has been observed since at least the early 20th century.",
    "The latest figures put adoption at roughly 40% year-over-year growth, outpacing earlier projections.",
]


def search_web(query: str) -> dict:
    import random
    results = [
        {"title": f"Result {i+1} for '{query}'", "snippet": _MOCK_SNIPPETS[i % len(_MOCK_SNIPPETS)]}
        for i in range(3)
    ]
    return {
        "ok": True,
        "data": {"query": query, "results": results},
        "error": None,
    }
