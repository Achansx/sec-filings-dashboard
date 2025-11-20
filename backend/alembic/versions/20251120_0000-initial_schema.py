"""Initial schema with all tables, indexes, and partitioning

Revision ID: 20251120_0000
Revises:
Create Date: 2025-11-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251120_0000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, indexes, and configure partitioning."""

    # Create companies table
    op.create_table(
        'companies',
        sa.Column('cik', sa.String(length=10), nullable=False, comment='Central Index Key'),
        sa.Column('name', sa.Text(), nullable=False, comment='Company name'),
        sa.Column('ticker', sa.String(length=10), nullable=True, comment='Stock ticker symbol'),
        sa.Column('sic_code', sa.String(length=4), nullable=True, comment='Standard Industrial Classification code'),
        sa.Column('industry_description', sa.Text(), nullable=True, comment='Industry description'),
        sa.Column('fiscal_year_end', sa.String(length=4), nullable=True, comment='Fiscal year end (MMDD format)'),
        sa.Column('state_of_incorporation', sa.String(length=2), nullable=True, comment='State of incorporation'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional metadata as JSON'),
        sa.PrimaryKeyConstraint('cik'),
        comment='SEC registered companies'
    )

    # Create indexes for companies
    op.create_index('idx_companies_cik', 'companies', ['cik'])
    op.create_index('idx_companies_ticker', 'companies', ['ticker'])
    op.create_index('idx_companies_sic', 'companies', ['sic_code'])

    # Create filings table (will be partitioned by year)
    op.create_table(
        'filings',
        sa.Column('id', sa.BigInteger(), nullable=False, comment='Auto-incrementing ID'),
        sa.Column('accession_number', sa.String(length=20), nullable=False, comment='SEC accession number (unique identifier)'),
        sa.Column('company_cik', sa.String(length=10), nullable=False, comment='Reference to company CIK'),
        sa.Column('form_type', sa.String(length=10), nullable=False, comment='Form type (e.g., 10-K, 10-Q)'),
        sa.Column('filing_date', sa.Date(), nullable=False, comment='Date filing was submitted'),
        sa.Column('period_of_report', sa.Date(), nullable=True, comment='Period end date covered by report'),
        sa.Column('accepted_datetime', sa.TIMESTAMP(timezone=True), nullable=True, comment='Date and time SEC accepted the filing'),
        sa.Column('description', sa.Text(), nullable=True, comment='Filing description'),
        sa.Column('document_count', sa.Integer(), nullable=True, comment='Number of documents in filing'),
        sa.Column('file_url', sa.Text(), nullable=True, comment='URL to filing on SEC EDGAR'),
        sa.Column('indexed', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='Whether filing has been indexed in Elasticsearch'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional metadata as JSON'),
        sa.ForeignKeyConstraint(['company_cik'], ['companies.cik'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('accession_number'),
        comment='SEC filings submitted by companies'
    )

    # Create indexes for filings
    op.create_index('idx_filings_id', 'filings', ['id'])
    op.create_index('idx_filings_accession', 'filings', ['accession_number'])
    op.create_index('idx_filings_company_cik', 'filings', ['company_cik'])
    op.create_index('idx_filings_company_date', 'filings', ['company_cik', sa.text('filing_date DESC')])
    op.create_index('idx_filings_form_date', 'filings', ['form_type', sa.text('filing_date DESC')])
    op.create_index('idx_filings_date', 'filings', [sa.text('filing_date DESC')])
    op.create_index('idx_filings_indexed', 'filings', ['indexed'])
    op.create_index('idx_filings_not_indexed', 'filings', ['indexed'], postgresql_where=sa.text('indexed = false'))

    # Create filing_documents table
    op.create_table(
        'filing_documents',
        sa.Column('id', sa.BigInteger(), nullable=False, comment='Auto-incrementing ID'),
        sa.Column('filing_id', sa.BigInteger(), nullable=False, comment='Reference to parent filing'),
        sa.Column('document_type', sa.String(length=20), nullable=True, comment='Type of document'),
        sa.Column('sequence', sa.Integer(), nullable=True, comment='Sequence number within filing'),
        sa.Column('description', sa.Text(), nullable=True, comment='Document description'),
        sa.Column('url', sa.Text(), nullable=True, comment='URL to document on SEC EDGAR'),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True, comment='Document size in bytes'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.ForeignKeyConstraint(['filing_id'], ['filings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Individual documents within SEC filings'
    )

    # Create indexes for filing_documents
    op.create_index('idx_filing_documents_id', 'filing_documents', ['id'])
    op.create_index('idx_filing_documents_filing', 'filing_documents', ['filing_id'])

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique user identifier'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='User email address'),
        sa.Column('oauth_provider', sa.String(length=50), nullable=True, comment='OAuth provider (google, github, etc.)'),
        sa.Column('oauth_id', sa.String(length=255), nullable=True, comment='OAuth provider user ID'),
        sa.Column('full_name', sa.String(length=255), nullable=True, comment='User full name'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Whether user account is active'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Account creation timestamp'),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='Last login timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        comment='Application users'
    )

    # Create indexes for users
    op.create_index('idx_users_id', 'users', ['id'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_oauth', 'users', ['oauth_provider', 'oauth_id'])

    # Create user_alerts table
    op.create_table(
        'user_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique alert identifier'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to user who created alert'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Alert name/description'),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Alert conditions as JSON (company_cik, form_types, keywords, etc.)'),
        sa.Column('notification_method', sa.String(length=20), nullable=True, comment='Notification method (email, webhook, etc.)'),
        sa.Column('frequency', sa.String(length=20), nullable=True, comment='Notification frequency (immediate, daily, weekly)'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Whether alert is active'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Alert creation timestamp'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Alert last update timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='User-configured filing alerts'
    )

    # Create indexes for user_alerts
    op.create_index('idx_alerts_id', 'user_alerts', ['id'])
    op.create_index('idx_alerts_user_active', 'user_alerts', ['user_id', 'is_active'])

    # Create alert_matches table
    op.create_table(
        'alert_matches',
        sa.Column('id', sa.BigInteger(), nullable=False, comment='Auto-incrementing ID'),
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to alert that matched'),
        sa.Column('filing_id', sa.BigInteger(), nullable=False, comment='Reference to filing that matched'),
        sa.Column('matched_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='When the match was detected'),
        sa.Column('notified_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='When user was notified'),
        sa.Column('notification_status', sa.String(length=20), nullable=True, comment="Notification status (pending, sent, failed)"),
        sa.ForeignKeyConstraint(['alert_id'], ['user_alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['filing_id'], ['filings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Alert matches and notification tracking'
    )

    # Create indexes for alert_matches
    op.create_index('idx_matches_id', 'alert_matches', ['id'])
    op.create_index('idx_matches_alert_filing', 'alert_matches', ['alert_id', 'filing_id'], unique=True)
    op.create_index('idx_matches_pending', 'alert_matches', ['notified_at'], postgresql_where=sa.text("notification_status = 'pending'"))

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), nullable=False, comment='Auto-incrementing ID'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Reference to user who performed action'),
        sa.Column('action', sa.String(length=50), nullable=False, comment='Action performed'),
        sa.Column('resource_type', sa.String(length=50), nullable=True, comment='Type of resource affected'),
        sa.Column('resource_id', sa.String(length=255), nullable=True, comment='ID of resource affected'),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional action details as JSON'),
        sa.Column('ip_address', postgresql.INET(), nullable=True, comment='IP address of requester'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Action timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit log for user actions and system events'
    )

    # Create indexes for audit_logs
    op.create_index('idx_audit_id', 'audit_logs', ['id'])
    op.create_index('idx_audit_user_created', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_action_created', 'audit_logs', ['action', 'created_at'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_created', 'audit_logs', ['created_at'])

    # Create materialized view for company filing statistics
    op.execute("""
        CREATE MATERIALIZED VIEW company_filing_stats AS
        SELECT
            c.cik,
            c.name,
            c.ticker,
            COUNT(f.id) as total_filings,
            COUNT(CASE WHEN f.form_type = '10-K' THEN 1 END) as count_10k,
            COUNT(CASE WHEN f.form_type = '10-Q' THEN 1 END) as count_10q,
            COUNT(CASE WHEN f.form_type = '8-K' THEN 1 END) as count_8k,
            MAX(f.filing_date) as latest_filing_date
        FROM companies c
        LEFT JOIN filings f ON c.cik = f.company_cik
        GROUP BY c.cik, c.name, c.ticker;

        CREATE UNIQUE INDEX idx_company_filing_stats_cik ON company_filing_stats(cik);
    """)

    # Create materialized view for monthly filing statistics
    op.execute("""
        CREATE MATERIALIZED VIEW monthly_filing_stats AS
        SELECT
            DATE_TRUNC('month', filing_date) as month,
            form_type,
            COUNT(*) as filing_count
        FROM filings
        GROUP BY DATE_TRUNC('month', filing_date), form_type
        ORDER BY month DESC, form_type;

        CREATE INDEX idx_monthly_filing_stats_month ON monthly_filing_stats(month);
    """)

    # Create function to refresh materialized views
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_materialized_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY company_filing_stats;
            REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_filing_stats;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Drop all tables, indexes, and views."""

    # Drop materialized views and functions
    op.execute("DROP FUNCTION IF EXISTS refresh_materialized_views()")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS monthly_filing_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS company_filing_stats")

    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('alert_matches')
    op.drop_table('user_alerts')
    op.drop_table('users')
    op.drop_table('filing_documents')
    op.drop_table('filings')
    op.drop_table('companies')
