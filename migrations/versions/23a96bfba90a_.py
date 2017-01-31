"""empty message

Revision ID: 23a96bfba90a
Revises: b224c3fed517
Create Date: 2017-01-31 11:03:33.971425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23a96bfba90a'
down_revision = 'b224c3fed517'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('page',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=True),
    sa.Column('title', sa.String(length=50), nullable=True),
    sa.Column('content', sa.String(length=1000), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('page')
    # ### end Alembic commands ###
