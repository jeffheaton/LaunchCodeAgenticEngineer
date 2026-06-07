from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client

THRESHOLD = 0.65
SERVER_URL = "http://localhost:8002/mcp"

# One case per ground-truth query in docs/retrieval-ground-truth.md.
# kind selects the pass rule:
# - precision: expected doc in top 3 with score >= THRESHOLD
# - keyword: expected doc returned at all; keyword fallback is allowed
# - ceiling: forbidden doc must be absent
CASES: list[dict[str, Any]] = [
    {
        "id": "Q1",
        "kind": "precision",
        "query": "What file format did we choose for exporting the task list?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {"doc_type": "decision"},
        "expected": "decision-csv-format.md",
    },
    {
        "id": "Q2",
        "kind": "precision",
        "query": "How does the CSV export feature build its output file?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {"doc_type": "feature"},
        "expected": "feature-csv-export.md",
    },
    {
        "id": "Q3",
        "kind": "keyword",
        "query": "What does error E_EXPORT_417 mean?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {"doc_type": "reference"},
        "expected": "error-codes.md",
    },
    {
        "id": "Q4",
        "kind": "precision",
        "query": "What retry policy should we use if CSV export generation fails?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {"doc_type": "feature"},
        "expected": "feature-csv-export.md",
    },
    {
        "id": "Q5",
        "kind": "ceiling",
        "query": "What are the internal cost figures for the export feature?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {},
        "forbidden": "cost-breakdown.md",
    },
    {
        "id": "Q6",
        "kind": "precision",
        "query": "What review standards should be applied to the CSV export implementation?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {"doc_type": "standard"},
        "expected": "standards-review.md",
    },
    {
        "id": "Q7",
        "kind": "precision",
        "query": "Which tasks are allowed to appear in a CSV export?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {"doc_type": "decision"},
        "expected": "security-export-visibility.md",
    },
    {
        "id": "Q8",
        "kind": "precision",
        "query": "Which spreadsheet library do we use to generate exports?",
        "project_id": "proj-csv",
        "ceiling": "internal",
        "filters": {"doc_type": "reference"},
        "expected": "api-spreadsheet-library.md",
    },
]


def extract_hits(result: Any) -> list[dict[str, Any]]:
    """FastMCP versions expose structured tool output under different attributes."""
    if hasattr(result, "data") and result.data is not None:
        return result.data
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "structuredContent") and result.structuredContent is not None:
        return result.structuredContent
    if isinstance(result, list):
        return result
    raise RuntimeError(f"Could not extract structured hits from result: {result!r}")


def judge(case: dict[str, Any], hits: list[dict[str, Any]]) -> bool:
    docs = [hit["source_document"] for hit in hits]
    if case["kind"] == "ceiling":
        return case["forbidden"] not in docs
    if case["kind"] == "keyword":
        return case["expected"] in docs
    return any(
        hit["source_document"] == case["expected"]
        and (hit.get("similarity_score") or 0) >= THRESHOLD
        for hit in hits
    )


def summarize(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "(no results)"
    return ", ".join(
        f"{hit['source_document']}#{hit['chunk_index']}"
        f"({hit['retrieval_method']},{hit.get('similarity_score')})"
        for hit in hits
    )


async def main() -> None:
    passed = 0
    async with Client(SERVER_URL) as client:
        for case in CASES:
            result = await client.call_tool(
                "retrieve",
                {
                    "query": case["query"],
                    "project_id": case["project_id"],
                    "top_k": 3,
                    "classification_ceiling": case["ceiling"],
                    "metadata_filters": case.get("filters", {}),
                },
            )
            hits = extract_hits(result)
            ok = judge(case, hits)
            passed += int(ok)
            print(f"{case['id']}: {'PASS' if ok else 'FAIL'} [{summarize(hits)}]")

    print(f"\n{passed}/{len(CASES)} passed")
    if passed / len(CASES) < 0.80:
        raise SystemExit("Retrieval pass rate is below the 80% floor")


if __name__ == "__main__":
    asyncio.run(main())
