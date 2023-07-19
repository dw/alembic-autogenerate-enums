"""
Alembic extension to generate ALTER TYPE .. ADD VALUE statements to update
SQLAlchemy enums.

"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

import alembic
import alembic.autogenerate
import alembic.autogenerate.render
import alembic.operations.base
import alembic.operations.ops
import sqlalchemy


@dataclass
class EnumToTable:
    table_name: str
    column_name: str
    enum_name: str


@dataclass
class DeclaredEnumValues:
    # enum name -> frozenset of values
    enum_definitions: Dict[str, FrozenSet[str]]
    table_definitions: Optional[List[EnumToTable]] = None


def get_defined_enums(conn, schema):
    """
    Return a dict mapping PostgreSQL enumeration types to the set of their
    defined values.
    :param conn:
        SQLAlchemy connection instance.
    :param str schema:
        Schema name (e.g. "public").
    :returns DeclaredEnumValues:
        enum_definitions={
            "my_enum": frozenset(["a", "b", "c"]),
        }
    """
    sql = """
        SELECT
            pg_catalog.format_type(t.oid, NULL),
            ARRAY(SELECT enumlabel
                  FROM pg_catalog.pg_enum
                  WHERE enumtypid = t.oid)
        FROM pg_catalog.pg_type t
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
        WHERE
            t.typtype = 'e'
            AND n.nspname = :schema
    """
    return DeclaredEnumValues({
        r[0]: frozenset(r[1])
        for r in conn.execute(sqlalchemy.text(sql), dict(schema=schema))
    })


def is_enum_column_type(column_type):
    """
    Determines whether an column is a valid Enum type
    """
    if isinstance(column_type, sqlalchemy.TypeDecorator):
        column_type = column_type.impl

    if isinstance(column_type, sqlalchemy.Enum):
        return True
    return False


def get_declared_enums(metadata, schema, default):
    """
    Return a dict mapping SQLAlchemy enumeration types to the set of their
    declared values.
    :param metadata:
        ...
    :param str schema:
        Schema name (e.g. "public").
    :returns DeclaredEnumValues:
        enum_definitions: {
            "my_enum": frozenset(["a", "b", "c"]),
        },
        table_definitions: [
            EnumToTable(table_name="my_table", column_name="my_column", enum_name="my_enum"),
        ]
    """
    types = set()
    table_definitions = []

    for table in metadata.tables.values():
        for column in table.columns:
            if is_enum_column_type(column.type) and schema == (column.type.schema or default):
                types.add(column.type)
                table_definitions.append(
                    EnumToTable(table.name, column.name, column.type.name)
                )

    return DeclaredEnumValues(
        enum_definitions={
            t.name: frozenset(t.enums) for t in types
        },
        table_definitions=table_definitions,
    )


@contextmanager
def get_connection(operations) -> sqlalchemy.engine.Connection:
    """
    SQLAlchemy 2.0 changes the operation binding location; bridge function to support
    both 1.x and 2.x.

    """
    binding = operations.get_bind()
    if isinstance(binding, sqlalchemy.engine.Connection):
        yield binding
        return
    yield binding.connect()


@alembic.operations.base.Operations.register_operation("sync_enum_values")
class SyncEnumValuesOp(alembic.operations.ops.MigrateOperation):
    def __init__(
            self,
            schema: str,
            name: str,
            old_values: List[str],
            new_values: List[str],
            affected_columns: List[Tuple[str, str]],
            should_reverse: bool = False
        ):
        self.schema = schema
        self.name = name
        self.old_values = old_values
        self.new_values = new_values
        self.affected_columns = affected_columns
        self.should_reverse = should_reverse

    def reverse(self):
        """
        See MigrateOperation.reverse().
        """
        return SyncEnumValuesOp(
            self.schema,
            self.name,
            old_values=self.new_values,
            new_values=self.old_values,
            affected_columns=self.affected_columns,
            should_reverse=not self.should_reverse,
        )

    @classmethod
    def sync_enum_values(
        cls,
        operations,
        schema,
        name,
        old_values: List[str],
        new_values: List[str],
        affected_columns: List[Tuple[str, str]] = None,
        should_reverse: bool = False,
    ):
        """
        Define every enum value from `new_values` that is not present in
        `old_values`.
        :param operations:
            ...
        :param str schema:
            Schema name.
        :param name:
            Enumeration type name.
        :param list old_values:
            List of enumeration values that existed in the database before this
            migration executed.
        :param list new_values:
            List of enumeration values that should exist after this migration
            executes.

        Note that `should_reverse` defaults to False here to keep backwards compatibility
        with previous migrations. The old interface to `sync_enum_values` supported explicit
        enum values without a reverse state:
            schema,
            name,
            old_values: list[str]
            new_values: list[str]
        By defaulting this to False, we avoid performing our new backwards migration logic
        and will default to the stub implementation that was previously used (and only
        executable by superusers).

        """
        if should_reverse and affected_columns is not None:
            with get_connection(operations) as conn:
                all_values = ", ".join([
                    f"'{value}'"
                    for value in sorted(set(new_values))
                ])

                conn.execute(sqlalchemy.text(f"ALTER TYPE {schema}.{name} RENAME TO {name}_old"))
                conn.execute(sqlalchemy.text(f"CREATE TYPE {schema}.{name} AS ENUM({all_values})"))
                for table_name, column_name in affected_columns:
                    conn.execute(sqlalchemy.text(
                        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {schema}.{name} USING "
                        f"{column_name}::text::{schema}.{name}"
                    ))
                conn.execute(sqlalchemy.text(f"DROP TYPE {schema}.{name}_old"))
                return

        with get_connection(operations) as conn:
            conn.execute(sqlalchemy.text("COMMIT"))
            for value in set(new_values) - set(old_values):
                conn.execute(
                    sqlalchemy.text(
                        f"ALTER TYPE {schema}.{name} ADD VALUE '{value}'"
                    )
                )


@alembic.autogenerate.render.renderers.dispatch_for(SyncEnumValuesOp)
def render_sync_enum_value_op(autogen_context, op: SyncEnumValuesOp):
    return "op.sync_enum_values(%r, %r, %r, %r, %r, %r)" % (
        op.schema,
        op.name,
        sorted(op.old_values),
        sorted(op.new_values),
        op.affected_columns,
        op.should_reverse,
    )


@alembic.autogenerate.comparators.dispatch_for("schema")
def compare_enums(autogen_context, upgrade_ops, schema_names):
    """
    Walk the declared SQLAlchemy schema for every referenced Enum, walk the PG
    schema for every definde Enum, then generate SyncEnumValuesOp migrations
    for each defined enum that has grown new entries when compared to its
    declared version.
    Enums that don't exist in the database yet are ignored, since
    SQLAlchemy/Alembic will create them as part of the usual migration process.
    """
    to_add = set()
    for schema in schema_names:
        default = autogen_context.dialect.default_schema_name
        if schema is None:
            schema = default

        defined = get_defined_enums(autogen_context.connection, schema)
        declared = get_declared_enums(autogen_context.metadata, schema, default)
        for name, new_values in declared.enum_definitions.items():
            old_values = defined.enum_definitions.get(name)
            # Alembic will handle creation of the type in this migration, so
            # skip undefined names.
            if name in defined.enum_definitions and new_values != old_values:
                affected_columns = frozenset(
                    (table_definition.table_name, table_definition.column_name)
                    for table_definition in declared.table_definitions
                    if table_definition.enum_name == name
                )
                to_add.add((schema, name, old_values, new_values, affected_columns))

    for schema, name, old_values, new_values, affected_columns in sorted(to_add):
        op = SyncEnumValuesOp(schema, name, list(old_values), list(new_values), list(affected_columns))
        upgrade_ops.ops.append(op)
