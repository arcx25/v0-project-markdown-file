"""Add vendor/buyer fields and subscription tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update user_role enum to use buyer/vendor instead of source/journalist
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('buyer', 'vendor', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_old")
    
    # Add subscription tier enum
    op.execute("CREATE TYPE subscription_tier AS ENUM ('free', 'freelancer', 'outlet', 'enterprise')")
    op.execute("CREATE TYPE subscription_status AS ENUM ('pending', 'active', 'expiring', 'grace_period', 'expired', 'cancelled')")
    op.execute("CREATE TYPE deposit_purpose AS ENUM ('subscription', 'support', 'escrow')")
    
    # Add vendor profile fields
    op.add_column('users', sa.Column('subscription_tier', sa.Enum('free', 'freelancer', 'outlet', 'enterprise', name='subscription_tier'), server_default='free'))
    op.add_column('users', sa.Column('subscription_expires_at', sa.DateTime(timezone=True)))
    op.add_column('users', sa.Column('is_subscribed', sa.Boolean, server_default='false'))
    op.add_column('users', sa.Column('proposals_this_month', sa.Integer, server_default='0'))
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tier', sa.Enum('free', 'freelancer', 'outlet', 'enterprise', name='subscription_tier'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'active', 'expiring', 'grace_period', 'expired', 'cancelled', name='subscription_status'), nullable=False, index=True),
        sa.Column('price_usd_cents', sa.Integer, nullable=False),
        sa.Column('price_xmr_atomic', sa.BigInteger, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('auto_renew', sa.Boolean, server_default='true'),
        sa.Column('payment_method', sa.String(20)),
        sa.Column('payment_reference', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # Create deposits table
    op.create_table(
        'deposits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('purpose', sa.Enum('subscription', 'support', 'escrow', name='deposit_purpose'), nullable=False),
        sa.Column('address', sa.String(106), nullable=False),
        sa.Column('payment_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('expected_amount_atomic', sa.BigInteger, nullable=False),
        sa.Column('received_amount_atomic', sa.BigInteger, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('reference_id', sa.String(200)),
        sa.Column('qr_code_base64', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # Add indexes for performance
    op.create_index('idx_subscriptions_user_status', 'subscriptions', ['user_id', 'status'])
    op.create_index('idx_deposits_status_created', 'deposits', ['status', 'created_at'])


def downgrade() -> None:
    # Drop new tables
    op.drop_table('deposits')
    op.drop_table('subscriptions')
    
    # Remove vendor profile fields
    op.drop_column('users', 'proposals_this_month')
    op.drop_column('users', 'is_subscribed')
    op.drop_column('users', 'subscription_expires_at')
    op.drop_column('users', 'subscription_tier')
    
    # Revert user_role enum
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('source', 'journalist', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_old")
    
    # Drop new enums
    op.execute('DROP TYPE deposit_purpose')
    op.execute('DROP TYPE subscription_status')
    op.execute('DROP TYPE subscription_tier')
