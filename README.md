
# alembic-autogenerate-enums

This package implements an Alembic hook that causes ``alembic revision
--autogenerate`` to output PostgreSQL ``ALTER TYPE .. ADD VALUE`` SQL
statements as part of new migrations.


## Usage

Add the line:

    import alembic_autogenerate_enums

To the top of your ``env.py``.


## Notes

Generated migrations only work in one direction, since without a superuser
account and a bunch of dangerous operations it isn't possible to remove
PostgreSQL ENUM values. Despite that, the generated migrations contain
downgrade code, just in case the implementation is improved (or e.g. extended
to work with other DBs) at some later date.

Since ``ALTER TYPE .. ADD VALUE`` cannot run transactionally, each
``op.sync_enum_values()`` call creates its own temporary private DB connection.
See https://bitbucket.org/zzzeek/alembic/issues/123/a-way-to-run-non-transactional-ddl
