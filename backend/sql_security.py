"""Defense-in-depth SQL validation; never trust model-produced SQL."""
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlglot import exp, parse
from sqlglot.errors import ParseError

from backend.config import settings

ALLOWED_TABLES = {"customers", "products", "orders", "order_items", "returns", "inventory", "payments"}
FORBIDDEN = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter, exp.Command, exp.Merge)
FORBIDDEN_FUNCTIONS = {"pg_sleep", "pg_read_file", "dblink", "lo_import", "lo_export", "set_config"}


class SQLSecurityError(ValueError):
    pass


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    sql: str
    truncated: bool


class SecureQueryExecutor:
    def __init__(self, engine: Engine | None = None, max_rows: int | None = None):
        self.engine = engine or create_engine(settings.database_url, pool_pre_ping=True)
        self.max_rows = max_rows or settings.sql_max_rows

    def validate(self, sql: str) -> str:
        if not sql or len(sql) > 20_000:
            raise SQLSecurityError("Query is empty or exceeds the size limit.")
        if re.search(r"(?:--|/\*|\*/|\x00)", sql):
            raise SQLSecurityError("Comments and control characters are not allowed.")
        try:
            statements = parse(sql, read="postgres")
        except ParseError as exc:
            raise SQLSecurityError("SQL could not be parsed.") from exc
        if len(statements) != 1:
            raise SQLSecurityError("Exactly one statement is required.")
        tree = statements[0]
        if not isinstance(tree, (exp.Select, exp.Union, exp.Subquery, exp.With)):
            raise SQLSecurityError("Only SELECT queries are permitted.")
        if any(isinstance(node, FORBIDDEN) for node in tree.walk()):
            raise SQLSecurityError("Write or administrative operations are forbidden.")
        tables = {t.name.lower() for t in tree.find_all(exp.Table)}
        cte_aliases = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
        unknown = tables - ALLOWED_TABLES - cte_aliases
        if unknown:
            raise SQLSecurityError(f"Access to unapproved table(s) denied: {', '.join(sorted(unknown))}.")
        if not tables:
            raise SQLSecurityError("A query must reference an approved table.")
        if tree.find(exp.Into):
            raise SQLSecurityError("SELECT INTO is forbidden.")
        if tree.find(exp.Lock):
            raise SQLSecurityError("Locking clauses are forbidden.")
        functions = {f.name.lower() for f in tree.find_all(exp.Func)}
        if functions & FORBIDDEN_FUNCTIONS:
            raise SQLSecurityError("Unsafe database function is forbidden.")
        return tree.sql(dialect="postgres")

    def execute(self, sql: str) -> QueryResult:
        canonical = self.validate(sql)
        capped = f"SELECT * FROM ({canonical}) AS guarded_query LIMIT {self.max_rows + 1}"
        with self.engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            conn.execute(text(f"SET LOCAL statement_timeout = '{settings.sql_statement_timeout_ms}ms'"))
            result = conn.execute(text(capped))
            rows = [dict(row) for row in result.mappings().all()]
        truncated = len(rows) > self.max_rows
        return QueryResult(list(rows[0].keys()) if rows else [], rows[: self.max_rows], canonical, truncated)
