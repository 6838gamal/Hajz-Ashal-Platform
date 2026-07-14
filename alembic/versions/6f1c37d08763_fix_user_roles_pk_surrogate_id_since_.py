"""fix user_roles pk: surrogate id since branch_id is nullable

Revision ID: 6f1c37d08763
Revises: fe6f3e916f72
Create Date: 2026-07-14 13:16:55.575018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f1c37d08763'
down_revision: Union[str, Sequence[str], None] = 'fe6f3e916f72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema. Manually adjusted: the old composite primary key
    (user_id, role_id, branch_id) implicitly forced branch_id NOT NULL, so
    it must be dropped before branch_id can become nullable and before the
    new surrogate `id` primary key is created."""
    op.drop_constraint('user_roles_pkey', 'user_roles', type_='primary')
    op.add_column('user_roles', sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')))
    op.alter_column('user_roles', 'branch_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.create_primary_key('user_roles_pkey', 'user_roles', ['id'])
    op.alter_column('user_roles', 'id', server_default=None)
    op.create_unique_constraint('uq_user_roles_natural_key', 'user_roles', ['user_id', 'role_id', 'branch_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_user_roles_natural_key', 'user_roles', type_='unique')
    op.drop_constraint('user_roles_pkey', 'user_roles', type_='primary')
    op.alter_column('user_roles', 'branch_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.drop_column('user_roles', 'id')
    op.create_primary_key('user_roles_pkey', 'user_roles', ['user_id', 'role_id', 'branch_id'])
    # ### end Alembic commands ###
