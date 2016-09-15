"""
Alembic extension to generate ALTER TYPE .. ADD VALUE statements to update
SQLAlchemy enums.
"""

from __future__ import absolute_import
import alembic
import alembic.autogenerate
import alembic.autogenerate.render
import alembic.operations.base
import alembic.operations.ops
import sqlalchemy


def get_defined_enums(conn, schema):
    """
    Return a dict mapping PostgreSQL enumeration types to the set of their
    defined values.

    :param conn:
        SQLAlchemy connection instance.

    :param str schema:
        Schema name (e.g. "public").

    :returns dict:
        {
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
            AND n.nspname = %s
    """
    return {r[0]: frozenset(r[1]) for r in conn.execute(sql, (schema,))}


def get_declared_enums(metadata, schema, default):
    """
    Return a dict mapping SQLAlchemy enumeration types to the set of their
    declared values.

    :param metadata:
        ...

    :param str schema:
        Schema name (e.g. "public").

    :returns dict:
        {
            "my_enum": frozenset(["a", "b", "c"]),
        }
    """
    types = set(column.type
                for table in metadata.tables.values()
                for column in table.columns
                if (isinstance(column.type, sqlalchemy.Enum) and
                    schema == (column.type.schema or default)))
    return {t.name: frozenset(t.enums) for t in types}


@alembic.operations.base.Operations.register_operation("sync_enum_values")
class SyncEnumValuesOp(alembic.operations.ops.MigrateOperation):
    """
    """
    def __init__(self, schema, name, old_values, new_values):
        self.schema = schema
        self.name = name
        self.old_values = old_values
        self.new_values = new_values

    def reverse(self):
        """
        See MigrateOperation.reverse().
        """
        return SyncEnumValuesOp(self.schema, self.name,
                                old_values=self.new_values,
                                new_values=self.old_values)

    @classmethod
    def sync_enum_values(cls, operations, schema, name, old_values, new_values):
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
        """
        with operations.get_bind().connect() as conn:
            conn.execute('COMMIT')
            for value in set(new_values) - set(old_values):
                conn.execute("ALTER TYPE %s.%s ADD VALUE '%s'" % (
                    schema,
                    name,
                    value
                ))


@alembic.autogenerate.render.renderers.dispatch_for(SyncEnumValuesOp)
def render_sync_enum_value_op(autogen_context, op):
    """
    """
    return 'op.sync_enum_values(%r, %r, %r, %r)' % (
        op.schema,
        op.name,
        sorted(op.old_values),
        sorted(op.new_values),
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
        for name, new_values in declared.items():
            old_values = defined.get(name)
            # Alembic will handle creation of the type in this migration, so
            # skip undefined names.
            if name in defined and new_values.difference(old_values):
                to_add.add((schema, name, old_values, new_values))

    for schema, name, old_values, new_values in sorted(to_add):
        op = SyncEnumValuesOp(schema, name, old_values, new_values)
        upgrade_ops.ops.append(op)
