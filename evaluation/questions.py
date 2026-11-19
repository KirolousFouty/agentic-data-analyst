"""100 deterministic evaluation cases. Expected SQL is executed against the seeded database."""
from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    expected_sql: str

BASE = [
    ("monthly revenue", "SELECT DATE_TRUNC('month', o.ordered_at) AS month, ROUND(SUM(oi.quantity * oi.unit_price - oi.discount_amount), 2) AS revenue FROM orders o JOIN order_items oi ON oi.order_id=o.id GROUP BY 1 ORDER BY 1"),
    ("return rates by category", "SELECT p.category, ROUND(100.0 * COUNT(r.id) / COUNT(oi.id), 2) AS return_rate_pct FROM order_items oi JOIN products p ON p.id=oi.product_id LEFT JOIN returns r ON r.order_item_id=oi.id GROUP BY p.category ORDER BY return_rate_pct DESC"),
    ("gross margin by product category", "SELECT p.category, ROUND(SUM(oi.quantity * (oi.unit_price-oi.unit_cost) - oi.discount_amount), 2) AS gross_margin FROM order_items oi JOIN products p ON p.id=oi.product_id GROUP BY p.category ORDER BY gross_margin DESC"),
    ("revenue by region", "SELECT o.region, ROUND(SUM(oi.quantity * oi.unit_price - oi.discount_amount), 2) AS revenue FROM orders o JOIN order_items oi ON oi.order_id=o.id GROUP BY o.region ORDER BY revenue DESC"),
    ("orders by payment method", "SELECT method, COUNT(*) AS orders FROM payments GROUP BY method ORDER BY orders DESC"),
]
CASES = tuple(EvaluationCase(f"Q{i:03d}", f"Show {label} (evaluation variant {i}).", sql) for i in range(1, 101) for label, sql in [BASE[(i-1) % len(BASE)]])
