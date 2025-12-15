"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE user_role AS ENUM ('source', 'journalist', 'admin')")
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'suspended', 'banned')")
    op.execute("CREATE TYPE lead_status AS ENUM ('draft', 'published', 'reviewing', 'matched', 'completed', 'archived')")
    op.execute("CREATE TYPE listing_status AS ENUM ('draft', 'active', 'paused', 'archived')")
    op.execute("CREATE TYPE payment_status AS ENUM ('pending', 'confirming', 'confirmed', 'completed', 'failed')")
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role', sa.Enum('source', 'journalist', 'admin', name='user_role'), nullable=False),
        sa.Column('pgp_fingerprint', sa.String(40), unique=True, nullable=False, index=True),
        sa.Column('pgp_public_key', sa.Text, nullable=False),
        sa.Column('display_name', sa.String(100)),
        sa.Column('bio', sa.Text),
        sa.Column('status', sa.Enum('active', 'suspended', 'banned', name='user_status'), 
                  default='active', nullable=False),
        sa.Column('verified_journalist', sa.Boolean, default=False),
        sa.Column('verification_details', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_seen', sa.DateTime(timezone=True)),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # Leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('tags', postgresql.ARRAY(sa.String)),
        sa.Column('status', sa.Enum('draft', 'published', 'reviewing', 'matched', 'completed', 'archived', 
                                    name='lead_status'), default='draft', nullable=False, index=True),
        sa.Column('matched_journalist_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # Lead Interest table (many-to-many)
    op.create_table(
        'lead_interests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('journalist_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('lead_id', 'journalist_id'),
    )
    
    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('encrypted_content', sa.Text, nullable=False),
        sa.Column('pgp_signature', sa.Text),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # Support Listings table
    op.create_table(
        'support_listings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('journalist_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('status', sa.Enum('draft', 'active', 'paused', 'archived', name='listing_status'), 
                  default='draft', nullable=False, index=True),
        sa.Column('total_raised_xmr', sa.Numeric(20, 12), default=0),
        sa.Column('total_raised_usd', sa.Numeric(12, 2), default=0),
        sa.Column('contributor_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # Support Tiers table
    op.create_table(
        'support_tiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('support_listings.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('amount_usd', sa.Numeric(12, 2), nullable=False),
        sa.Column('benefits', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    
    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('support_listings.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tier_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('support_tiers.id', ondelete='SET NULL')),
        sa.Column('amount_xmr', sa.Numeric(20, 12), nullable=False),
        sa.Column('amount_usd', sa.Numeric(12, 2), nullable=False),
        sa.Column('exchange_rate', sa.Numeric(12, 2)),
        sa.Column('monero_address', sa.String(95), nullable=False),
        sa.Column('integrated_address', sa.String(106)),
        sa.Column('payment_id', sa.String(64)),
        sa.Column('tx_hash', sa.String(64), index=True),
        sa.Column('confirmations', sa.Integer, default=0),
        sa.Column('status', sa.Enum('pending', 'confirming', 'confirmed', 'completed', 'failed', 
                                    name='payment_status'), default='pending', nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('metadata', postgresql.JSONB),
    )
    
    # Sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('circuit_id', sa.String(64), index=True),
        sa.Column('ip_hash', sa.String(64)),
        sa.Column('user_agent_hash', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_used', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('ip_hash', sa.String(64)),
        sa.Column('user_agent_hash', sa.String(64)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), index=True),
    )
    
    # Create indexes
    op.create_index('idx_leads_status_published', 'leads', ['status', 'published_at'])
    op.create_index('idx_messages_lead_created', 'messages', ['lead_id', 'created_at'])
    op.create_index('idx_payments_status_created', 'payments', ['status', 'created_at'])
    op.create_index('idx_sessions_expires', 'sessions', ['expires_at'])
    op.create_index('idx_audit_logs_created', 'audit_logs', ['created_at'])


def downgrade() -> None:
    # Drop all tables
    op.drop_table('audit_logs')
    op.drop_table('sessions')
    op.drop_table('payments')
    op.drop_table('support_tiers')
    op.drop_table('support_listings')
    op.drop_table('messages')
    op.drop_table('lead_interests')
    op.drop_table('leads')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute('DROP TYPE payment_status')
    op.execute('DROP TYPE listing_status')
    op.execute('DROP TYPE lead_status')
    op.execute('DROP TYPE user_status')
    op.execute('DROP TYPE user_role')
