"""empty message

Revision ID: f2ef34224a05
Revises: a941ad1345a2
Create Date: 2017-02-13 11:59:59.503765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2ef34224a05'
down_revision = 'a941ad1345a2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('last_edit_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'last_edit_date')
    # ### end Alembic commands ###
