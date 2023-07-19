import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import PropertyMock, patch

import alembic.config
import pytest
import sqlalchemy
from alembic.autogenerate.api import AutogenContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from test_harness.enums import ModifiableEnum, sync_sqlalchemy
from test_harness.models import SimpleEnum, SimpleModel, SimpleModelCustomEnum
from test_harness.tests.fixtures import get_fixture_path


def modify_enum(model, enum: ModifiableEnum, add_values: list[str], remove_values: list[str]):
    # Now manipulate the enum values by adding a new value
    for value in add_values:
        assert value not in [value.value for value in enum]
        enum.add_member(value, value)
    for value in remove_values:
        assert value in [value.value for value in enum]
        enum.remove_member(value)

    sync_sqlalchemy(model, enum)

MODEL_DEFINITIONS = [SimpleModel, SimpleModelCustomEnum]

if sqlalchemy.__version__ > '2.0':
    from test_harness.models import SimpleModelMapped
    MODEL_DEFINITIONS.append(SimpleModelMapped)

@pytest.mark.parametrize(
        "model,add_values,remove_values",
        [
            (model, add_values, remove_values)
            for model in MODEL_DEFINITIONS
            for add_values, remove_values in [
                (["F"], []),
                ([], ["A"]),
            ]
        ]
    )
def test_migration_includes_sync_enum_values(
    clear_db,
    model,
    add_values: list[str],
    remove_values: list[str],
):
    # Set up temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    os.mkdir(temp_dir / "versions")

    shutil.copy(get_fixture_path("alembic.ini"), temp_dir)
    shutil.copy(get_fixture_path("alembic") / "env.py", temp_dir / "env.py")
    shutil.copy(get_fixture_path("alembic") / "script.py.mako", temp_dir / "script.py.mako")

    with patch.object(AutogenContext, 'metadata', new_callable=PropertyMock) as mock_metadata:
        # By default migrations are run in another context, which means that the harness won't see out
        # enum changes
        mock_metadata.return_value = model.metadata

        # Set up Alembic config
        config = alembic.config.Config(str(temp_dir / 'alembic.ini'))
        config.set_main_option("script_location", str(temp_dir))
        
        # Generate base migration that will create the enums in the first place
        # Then run it so we're current with the baseline enum value
        alembic.command.revision(config, autogenerate=True, message="Initial migration")
        alembic.command.upgrade(config, "head")

        # Now manipulate the enum values by adding a new value
        modify_enum(model, SimpleEnum, add_values, remove_values)

        # Generate the updated file
        alembic.command.revision(config, autogenerate=True, message="Test migration")

    # Revert to the default values for the next run by applying the inverse of our recent changes
    modify_enum(model, SimpleEnum, remove_values, add_values)

    sync_sqlalchemy(model, SimpleEnum)

    # Get the generated script
    script = ScriptDirectory.from_config(config)
    head_revision = script.get_current_head()
    head_script = script.get_revision(head_revision)

    # Read the script
    with open(head_script.path) as f:
        script_content = f.read()

    # Assert that sync_enum_values is included
    assert "op.sync_enum_values" in script_content
