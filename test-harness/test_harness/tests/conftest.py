import pytest
import sqlalchemy
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic_autogenerate_enums import get_defined_enums
from sqlalchemy import create_engine, text

from test_harness.database import get_url
from test_harness.tests.fixtures import get_fixture_path


@pytest.fixture()
def clear_db():
    url = get_url()
    engine = create_engine(url)
    with engine.connect() as connection:
        # Drop the database tables
        from test_harness.models import Base, BaseV2
        base_classes = [Base, BaseV2]
        if sqlalchemy.__version__ > '2.0':
            from test_harness.models import BaseV3
            base_classes.append(BaseV3)

        for base_class in base_classes:
            for table in base_class.metadata.tables.values():
                connection.execute(text(f"DROP TABLE IF EXISTS {table.name} CASCADE"))

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


@pytest.fixture()
def alembic_config():
    config = Config(str(get_fixture_path("alembic.ini")))
    config.set_main_option("script_location", str(get_fixture_path("alembic")))
    return config


@pytest.fixture()
def alembic_script(alembic_config):
    script = ScriptDirectory.from_config(alembic_config)
    return script
