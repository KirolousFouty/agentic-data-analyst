"""Live, reproducible behavioral checks for core business questions.

Run inside the API container after seeding:
    python -m evaluation.regression
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class RegressionCase:
    name: str
    question: str
    answer_contains: str
    sql_contains: str | None = None
    expected_row: dict[str, Any] | None = None


CASES = (
    RegressionCase(
        "product-id inventory lookup",
        "How many on-hand inventory units are there for product id 7?",
        "on_hand=13",
        "WHERE p.id = 7",
        {"product_id": 7, "on_hand": 13},
    ),
    RegressionCase(
        "highest inventory product",
        "What is the product with the biggest on-hand inventory?",
        "Beauty Product 120",
        "ORDER BY i.on_hand DESC LIMIT 1",
        {"on_hand": 497},
    ),
    RegressionCase(
        "ordinal return-rate ranking",
        "Which category is the second highest return rate?",
        "Electronics",
        "ORDER BY return_rate_pct DESC",
        {"category": "Apparel", "return_rate_pct": 17.53},
    ),
    RegressionCase(
        "regional revenue",
        "Show revenue by region.",
        "region=South",
        "GROUP BY o.region",
        {"region": "South", "revenue": 2443638.7},
    ),
    RegressionCase(
        "regional retention",
        "Compare customer retention across regions.",
        "retention_pct=",
        "WITH monthly_customers",
    ),
    RegressionCase(
        "write rejection",
        "Delete all orders.",
        "read-only business analysis",
    ),
    RegressionCase(
        "ambiguous question",
        "Help.",
        "Please specify the business metric",
    ),
)


def run(base_url: str | None = None) -> list[dict[str, Any]]:
    url = (base_url or os.getenv("API_URL", "http://localhost:8000")).rstrip("/")
    outcomes: list[dict[str, Any]] = []
    with httpx.Client(timeout=180) as client:
        for case in CASES:
            response = client.post(f"{url}/ask", json={"question": case.question})
            response.raise_for_status()
            payload = response.json()
            valid = case.answer_contains.lower() in payload["answer"].lower()
            if case.sql_contains:
                valid = valid and case.sql_contains.lower() in (payload.get("sql") or "").lower()
            if case.expected_row:
                actual = (payload.get("rows") or [{}])[0]
                valid = valid and all(actual.get(key) == value for key, value in case.expected_row.items())
            outcomes.append({"name": case.name, "passed": valid, "answer": payload["answer"]})
    failures = [result["name"] for result in outcomes if not result["passed"]]
    if failures:
        raise AssertionError(f"Regression failures: {', '.join(failures)}")
    return outcomes


if __name__ == "__main__":
    for outcome in run():
        print(f"PASS: {outcome['name']}")
