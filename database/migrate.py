from sqlalchemy import create_engine

from backend.config import settings


def main() -> None:
    # Migration package is intentionally simple for this one-revision portfolio project.
    from database.models import Base
    engine = create_engine(settings.database_admin_url)
    Base.metadata.create_all(engine)

if __name__ == "__main__": main()
