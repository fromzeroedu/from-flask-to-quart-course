"""create relationship table

Revision ID: 7102c89a5021
Revises: 7c33d8dfbca6
Create Date: 2023-03-02 09:15:28.702252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7102c89a5021'
down_revision = '7c33d8dfbca6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('relationship',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fm_user_id', sa.Integer(), nullable=True),
    sa.Column('to_user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['fm_user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['to_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('relationship')
    # ### end Alembic commands ###