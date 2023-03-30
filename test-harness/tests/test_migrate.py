from alembic.config import Config
from alembic import command
from test_harness.database import get_url
import sqlalchemy
from alembic.runtime import migration
from alembic.script import ScriptDirectory

def test_basic_migration(clear_db):
    config = Config("alembic.ini")
    config.set_main_option("script_location", "alembic")
    script = ScriptDirectory.from_config(config)

    engine = sqlalchemy.create_engine(get_url())
    with engine.begin() as conn:
        context = migration.MigrationContext.configure(conn)
        assert context.get_current_revision() is None
        assert script.get_current_head() is not None

    # Test the upgrade
    command.upgrade(config, "head")

    with engine.begin() as conn:
        context = migration.MigrationContext.configure(conn)
        assert context.get_current_revision() == script.get_current_head()

    # Test the full downgrade
    command.downgrade(config, "base")

    with engine.begin() as conn:
        context = migration.MigrationContext.configure(conn)
        assert context.get_current_revision() is None
        assert script.get_current_head() is not None
