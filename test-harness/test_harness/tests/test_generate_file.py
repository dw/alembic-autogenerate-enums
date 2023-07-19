import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import PropertyMock, patch

import alembic.config
import pytest
from alembic.autogenerate.api import AutogenContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from test_harness.enums import sync_sqlalchemy
from test_harness.models import (Base, BaseV2, SimpleEnum, SimpleModel,
                                 SimpleModelMapped)
from test_harness.tests.fixtures import get_fixture_path


@pytest.mark.parametrize("model", [SimpleModel, SimpleModelMapped])
def test_migration_includes_sync_enum_values(clear_db, model: Base | BaseV2):
    # Set up temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    os.mkdir(temp_dir / "versions")

    shutil.copy(get_fixture_path("alembic.ini"), temp_dir)
    shutil.copy(get_fixture_path("alembic") / "env.py", temp_dir / "env.py")
    shutil.copy(get_fixture_path("alembic") / "script.py.mako", temp_dir / "script.py.mako")

    print(list(temp_dir.iterdir()))

    with patch.object(AutogenContext, 'metadata', new_callable=PropertyMock) as mock_metadata:
        # By default migrations are run in another context, which means that the harness won't see out
        # enum changes
        mock_metadata.return_value = model.metadata

        # Set up Alembic config
        config = alembic.config.Config(str(temp_dir / 'alembic.ini'))
        config.set_main_option("script_location", str(temp_dir))
        
        # Generate base migration that will create the enums in the first place
        alembic.command.revision(config, autogenerate=True, message="Initial migration")
        # Run the migration
        alembic.command.upgrade(config, "head")

        # Now manipulate the enum values by adding a new value
        assert "F" not in [value for value in SimpleEnum]
        SimpleEnum.add_member("F", "F")
        sync_sqlalchemy(model, SimpleEnum)

        # Generate the updated file
        alembic.command.revision(config, autogenerate=True, message="Test migration")

    # Downgrade for the next run
    SimpleEnum.remove_member("F")
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
