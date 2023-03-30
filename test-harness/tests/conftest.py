import pytest
from test_harness.database import get_url
from sqlalchemy import create_engine, text
from alembic_autogenerate_enums import get_defined_enums

@pytest.fixture()
def clear_db():
    url = get_url()
    engine = create_engine(url)
    with engine.connect() as connection:
        # Drop the database tables
        from test_harness.models import Base
        Base.metadata.drop_all(bind=connection)

        # Drop the alembic specific tables
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))

        # Get all scheams in database
        defined = get_defined_enums(connection, "public")

        # Drop the enums
        # Run drop type for simpleenum
        for field_name in defined.enum_definitions:
            connection.execute(text(f"DROP TYPE {field_name}"))

        # Commit these changes
        connection.execute(text("COMMIT"))

    yield
