from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models to register them with Base.metadata for Alembic discovery.
# This does not create any physical tables.
import app.models  # noqa: E402, F401
