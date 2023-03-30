
# alembic-autogenerate-enums

This package implements an Alembic hook that causes ``alembic revision
--autogenerate`` to output PostgreSQL ``ALTER TYPE .. ADD VALUE`` SQL
statements as part of new migrations.


## Usage

Add the line:

    import alembic_autogenerate_enums

To the top of your ``env.py``.


## Notes

Since ``ALTER TYPE .. ADD VALUE`` cannot run transactionally, each
``op.sync_enum_values()`` call creates its own temporary private DB connection.
See https://bitbucket.org/zzzeek/alembic/issues/123/a-way-to-run-non-transactional-ddl

## Tests

We have incredibly basic tests in a [sample project](./test-harness).

```
mkvirtualenv alembic-autogenerate
```

Install the main autogenerate package and then the test harness:

```
pip install -e .
pip install -e test-harness
```

```
createuser alembic-autogenerate
createdb -O alembic-autogenerate alembic-autogenerate_db
```

```
cd test-harness && pytest
```
