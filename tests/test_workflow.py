from agents.workflow import classify


def test_write_request_is_rejected():
    answer=classify({"question":"drop all customer tables"})
    assert answer["intent"] == "reject"

def test_ambiguous_request_requests_clarification():
    assert classify({"question":"help"})["intent"] == "clarify"

def test_business_question_is_analyzed():
    assert classify({"question":"Compare revenue by region last month"})["intent"] == "analysis"
