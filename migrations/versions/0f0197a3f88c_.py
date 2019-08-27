"""empty message

Revision ID: 0f0197a3f88c
Revises: 793f16379cef
Create Date: 2019-08-27 15:48:21.028725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f0197a3f88c'
down_revision = '793f16379cef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('SYS_DATA',
    sa.Column('ID', sa.String(length=64), nullable=False, comment='主键ID'),
    sa.Column('CREATE_BY', sa.String(length=64), nullable=True, comment='创建者'),
    sa.Column('UPDATE_BY', sa.String(length=64), nullable=True, comment='更新者'),
    sa.Column('CREATE_DATE', sa.DateTime(), nullable=True, comment='创建日期'),
    sa.Column('UPDATE_DATE', sa.DateTime(), nullable=True, comment='更新日期'),
    sa.Column('REMARKS', sa.Text(), nullable=True, comment='备注'),
    sa.Column('KEY', sa.String(length=64), nullable=False, comment='数据键值'),
    sa.Column('VALUE', sa.Text(), nullable=True, comment='数据值'),
    sa.Column('DESCRIPTION', sa.String(length=225), nullable=True, comment='描述'),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_index(op.f('ix_SYS_DATA_KEY'), 'SYS_DATA', ['KEY'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_SYS_DATA_KEY'), table_name='SYS_DATA')
    op.drop_table('SYS_DATA')
    # ### end Alembic commands ###