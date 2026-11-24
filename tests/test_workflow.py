from agents.workflow import classify, respond
from backend.sql_security import QueryResult


def test_write_request_is_rejected():
    answer=classify({"question":"drop all customer tables"})
    assert answer["intent"] == "reject"

def test_ambiguous_request_requests_clarification():
    assert classify({"question":"help"})["intent"] == "clarify"

def test_business_question_is_analyzed():
    assert classify({"question":"Compare revenue by region last month"})["intent"] == "analysis"


def test_response_uses_requested_rank():
    result = QueryResult(
        columns=["category", "return_rate_pct"],
        rows=[
            {"category": "Apparel", "return_rate_pct": 17.53},
            {"category": "Electronics", "return_rate_pct": 10.64},
        ],
        sql="SELECT 1",
        truncated=False,
    )
    answer = respond({"question": "Which category is the second highest return rate?", "result": result})
    assert "Electronics" in answer["answer"]
