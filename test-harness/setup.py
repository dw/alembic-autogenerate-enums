
from __future__ import absolute_import

from setuptools import setup

setup(
    name='test-harness',
    description=(
        "Test harness for alembic-autogenerate-enums."
    ),
    version='0.0.1',
    author='Pierce Freeman',
    url='http://github.com/dw/alembic-autogenerate-enums/',
    py_modules=['test_harness'],
    classifiers=["Topic :: Database"],
    zip_safe=False,
    # requirements
    install_requires=[
        "alembic",
        "sqlalchemy",
        "psycopg2",
        "pytest",
    ]
)
