"""Deterministically create a realistic e-commerce dataset (default 50,000 orders)."""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.config import settings
from database.models import Base, Customer, Inventory, Order, OrderItem, Payment, Product, Return

SEED = 20241017
REGIONS = ["North", "South", "East", "West"]
CATEGORIES = {"Electronics": (45, 300, .11), "Home": (12, 150, .07), "Apparel": (8, 80, .18), "Sports": (15, 160, .09), "Beauty": (5, 60, .06)}

def money(v: float) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def seed(order_count: int = 50_000, url: str | None = None) -> None:
    rng = random.Random(SEED)
    engine = create_engine(url or settings.database_admin_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        customers = [Customer(email=f"customer{i}@example.test", region=REGIONS[i % 4], segment=["Consumer", "SMB", "Enterprise"][i % 3], created_at=datetime(2022, 1, 1).date() + timedelta(days=rng.randrange(1000))) for i in range(1, 10001)]
        db.add_all(customers)
        products: list[Product] = []
        for i in range(1, 251):
            category = list(CATEGORIES)[(i - 1) % len(CATEGORIES)]
            low, high, _ = CATEGORIES[category]
            cost = money(rng.uniform(low, high))
            products.append(Product(sku=f"SKU-{i:04d}", name=f"{category} Product {i:03d}", category=category, cost=cost, list_price=money(float(cost) * rng.uniform(1.35, 1.9))))
        db.add_all(products); db.flush()
        db.add_all([Inventory(product_id=p.id, warehouse=REGIONS[p.id % 4], on_hand=rng.randint(0, 500), reorder_point=rng.randint(15, 80)) for p in products])
        db.commit()
        start = datetime(2023, 1, 1)
        # Batch commits retain a modest memory footprint while remaining deterministic.
        for batch_start in range(0, order_count, 1000):
            for n in range(batch_start, min(batch_start + 1000, order_count)):
                # Seasonality: Q4 is proportionally denser; an intentional decline occurs in late 2024.
                day = rng.randrange(730); ordered = start + timedelta(days=day, hours=rng.randrange(24))
                customer = customers[rng.randrange(len(customers))]
                region = customer.region
                product = products[rng.randrange(len(products))]
                qty = rng.choices([1,2,3,4], [65,25,8,2])[0]
                seasonal = 0.90 if ordered.month in (1,2) else (1.15 if ordered.month in (11,12) else 1.0)
                price = money(float(product.list_price) * seasonal)
                discount_rate = rng.choice([0, .05, .10, .15])
                discount = money(float(price) * qty * discount_rate)
                total = money(float(price) * qty - float(discount))
                order = Order(customer_id=customer.id, ordered_at=ordered, status="completed", region=region, discount_amount=discount, total_amount=total)
                db.add(order); db.flush()
                item=OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=price, unit_cost=product.cost, discount_amount=discount)
                db.add(item); db.flush()
                db.add(Payment(order_id=order.id, method=rng.choice(["card", "wallet", "bank_transfer"]), amount=total, paid_at=ordered))
                _, _, return_rate = CATEGORIES[product.category]
                if rng.random() < return_rate:
                    db.add(Return(order_item_id=item.id, returned_at=ordered + timedelta(days=rng.randrange(3, 31)), reason=rng.choice(["Damaged", "Wrong size", "Changed mind", "Not as described"]), refund_amount=total))
            db.commit()
            print(f"seeded {min(batch_start + 1000, order_count)}/{order_count}")
    # Explicit grant protects databases initialized after tables were created.
    with engine.begin() as conn:
        conn.exec_driver_sql("GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_reader")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--orders", type=int, default=50_000); parser.add_argument("--url")
    seed(parser.parse_args().orders, parser.parse_args().url)
