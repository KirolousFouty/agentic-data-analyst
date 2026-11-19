"""Initial schema migration.

Run with `python -m database.migrate`. The deterministic seed command recreates this
schema for development, while this migration is suitable for an empty database.
"""
from sqlalchemy.engine import Engine

from database.models import Base

revision = "001_initial"

def upgrade(engine: Engine) -> None:
    Base.metadata.create_all(engine)

def downgrade(engine: Engine) -> None:
    Base.metadata.drop_all(engine)
