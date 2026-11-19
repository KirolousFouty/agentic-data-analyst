import pytest

from backend.sql_security import SecureQueryExecutor, SQLSecurityError


@pytest.fixture
def guard():
    # Validation is deliberately unit-tested without needing a database driver or server.
    return SecureQueryExecutor(engine=object(), max_rows=10)  # type: ignore[arg-type]

@pytest.mark.parametrize("sql", [
    "DELETE FROM orders", "SELECT * FROM users", "SELECT * FROM orders; DELETE FROM orders",
    "SELECT * INTO backup FROM orders", "SELECT * FROM orders -- sneaky", "DROP TABLE products",
    "UPDATE orders SET status = 'x'", "SELECT pg_sleep(10)",
])
def test_rejects_unsafe_sql(guard, sql):
    with pytest.raises(SQLSecurityError): guard.validate(sql)

def test_canonicalizes_safe_select(guard):
    assert "orders" in guard.validate("select id, total_amount from orders limit 5").lower()


def test_allows_safe_division_expression(guard):
    sql = "SELECT 100.0 * COUNT(id) / NULLIF(COUNT(id), 0) AS rate FROM orders"
    assert "NULLIF" in guard.validate(sql)

def test_rejects_multiple_tables_not_allowlisted(guard):
    with pytest.raises(SQLSecurityError, match="unapproved"):
        guard.validate("SELECT * FROM information_schema.tables")
