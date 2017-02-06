
from __future__ import absolute_import
from setuptools import setup

setup(
    name='alembic_autogenerate_enums',
    description=(
        "Alembic hook that causes --autogenerate to output PostgreSQL ALTER "
        "TYPE statements."
    ),
    version='0.0.2',
    author='David Wilson',
    url='http://github.com/dw/alembic-autogenerate-enums/',
    py_modules=['alembic_autogenerate_enums'],
    classifiers=["Topic :: Database"],
    zip_safe=False,
)
