"""current upgrade path

Revision ID: f609280185f5
Revises: 2635ee8b59d5
Create Date: 2023-03-30 15:12:50.387679

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f609280185f5'
down_revision = '2635ee8b59d5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.sync_enum_values('public', 'simpleenum', ['A', 'B', 'C', 'D'], ['A', 'B', 'C', 'D', 'E'], [('simple_model', 'enum_field')], False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.sync_enum_values('public', 'simpleenum', ['A', 'B', 'C', 'D', 'E'], ['A', 'B', 'C', 'D'], [('simple_model', 'enum_field')], True)
    # ### end Alembic commands ###
