import pytest

from agents.workflow import generate_sql
from backend.sql_security import SecureQueryExecutor


@pytest.mark.parametrize(
    ("question", "expected_fragment"),
    [
        ("Show revenue by region", "GROUP BY o.region"),
        ("Which categories have the highest return rates?", "ORDER BY return_rate_pct DESC"),
        ("What is the product with biggest on hand inventory?", "ORDER BY i.on_hand DESC LIMIT 1"),
        ("How much on hand inventory is there for product id 7?", "WHERE p.id = 7"),
        ("Compare customer retention across regions", "retention_pct"),
        ("Which products contributed most to declining margins?", "gross_margin"),
    ],
)
def test_core_questions_generate_valid_approved_sql(question, expected_fragment):
    sql = generate_sql({"question": question, "context": "", "plan": ""})["sql"]
    assert expected_fragment in sql
    # Templates must meet the same policy as model-generated SQL.
    assert SecureQueryExecutor(engine=object()).validate(sql)
