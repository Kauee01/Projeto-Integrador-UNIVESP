"""Migração inicial com a coluna descricao em Categoria

Revision ID: f1fe05526d6b
Revises: 
Create Date: 2025-04-05 15:26:17.190455

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1fe05526d6b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categoria',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nome', sa.String(length=255), nullable=False),
    sa.Column('descricao', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nome')
    )
    op.create_table('tipo_pagamento',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nome', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nome')
    )
    op.create_table('tipo_produto',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nome', sa.String(length=255), nullable=False),
    sa.Column('categoria_id', sa.Integer(), nullable=False),
    sa.Column('preco', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['categoria_id'], ['categoria.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nome')
    )
    op.create_table('venda',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('data', sa.DateTime(), nullable=True),
    sa.Column('tipo_pagamento_id', sa.Integer(), nullable=False),
    sa.Column('valor_total', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['tipo_pagamento_id'], ['tipo_pagamento.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('item_venda',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('venda_id', sa.Integer(), nullable=False),
    sa.Column('tipo_produto_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Integer(), nullable=False),
    sa.Column('valor_produtos', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['tipo_produto_id'], ['tipo_produto.id'], ),
    sa.ForeignKeyConstraint(['venda_id'], ['venda.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('produto',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tipo_produto_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['tipo_produto_id'], ['tipo_produto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('produto')
    op.drop_table('item_venda')
    op.drop_table('venda')
    op.drop_table('tipo_produto')
    op.drop_table('tipo_pagamento')
    op.drop_table('categoria')
    # ### end Alembic commands ###
