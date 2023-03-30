import sqlalchemy
from alembic_autogenerate_enums import get_declared_enums, get_defined_enums

from alembic import command
from alembic.runtime import migration
from test_harness.database import get_url
from test_harness.models import SimpleEnum


def check_base(engine, script):
    """
    Check that the state of the database is at the base revision
    """
    with engine.begin() as conn:
        context = migration.MigrationContext.configure(conn)
        assert context.get_current_revision() is None
        assert script.get_current_head() is not None


def check_head(engine, script):
    """
    Check that the state of the database is at the head revision
    """
    with engine.begin() as conn:
        context = migration.MigrationContext.configure(conn)
        assert context.get_current_revision() == script.get_current_head()


def test_upgrade(clear_db, alembic_config, alembic_script):
    engine = sqlalchemy.create_engine(get_url())
    check_base(engine, alembic_script)
    command.upgrade(alembic_config, "head")
    check_head(engine, alembic_script)


def test_downgrade(clear_db, alembic_config, alembic_script):
    engine = sqlalchemy.create_engine(get_url())
    check_base(engine, alembic_script)
    command.upgrade(alembic_config, "head")
    check_head(engine, alembic_script)
    command.downgrade(alembic_config, "base")
    check_base(engine, alembic_script)


def test_enum_success(clear_db, alembic_config, alembic_script):
    """
    Test the enums that have been created by the end-to-end migration pipeline.
    These should be equal to the current enum definition.
    """
    engine = sqlalchemy.create_engine(get_url())
    command.upgrade(alembic_config, "head")

    with engine.begin() as conn:
        defined = get_defined_enums(conn, "public")

        assert set(defined.enum_definitions["simpleenum"]) == set([item.value for item in SimpleEnum])
