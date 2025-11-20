#!/bin/bash

# SEC Filings Dashboard - Seed Data Script
# This script populates the database with sample test data

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Load environment variables
if [ -f .env ]; then
    source .env
else
    print_error ".env file not found!"
    exit 1
fi

# Set default values
POSTGRES_USER=${POSTGRES_USER:-secfilings}
POSTGRES_DB=${POSTGRES_DB:-secfilings}

print_header "Database Seed Utility"

# Check if PostgreSQL container is running
print_info "Checking PostgreSQL container..."

if ! docker-compose ps postgres | grep -q "Up"; then
    print_error "PostgreSQL container is not running!"
    print_info "Please start the services first: docker-compose up -d"
    exit 1
fi

print_success "PostgreSQL container is running"

# Create seed data SQL script
print_info "Creating seed data..."

SEED_SQL=$(cat << 'EOF'
-- Seed data for SEC Filings Dashboard
-- This creates sample companies and filings for testing

-- Insert sample companies
INSERT INTO companies (cik, name, ticker, sic_code, industry_description, fiscal_year_end, state_of_incorporation, created_at, updated_at, metadata) VALUES
('0000320193', 'Apple Inc.', 'AAPL', '3571', 'Electronic Computers', '0930', 'CA', NOW(), NOW(), '{"website": "https://www.apple.com"}'),
('0001018724', 'Amazon.com, Inc.', 'AMZN', '5961', 'Catalog & Mail-Order Houses', '1231', 'DE', NOW(), NOW(), '{"website": "https://www.amazon.com"}'),
('0001652044', 'Alphabet Inc.', 'GOOGL', '7370', 'Services-Computer Programming, Data Processing, Etc.', '1231', 'DE', NOW(), NOW(), '{"website": "https://www.google.com"}'),
('0001326801', 'Meta Platforms, Inc.', 'META', '7370', 'Services-Computer Programming, Data Processing, Etc.', '1231', 'DE', NOW(), NOW(), '{"website": "https://www.facebook.com"}'),
('0001318605', 'Tesla, Inc.', 'TSLA', '3711', 'Motor Vehicles & Passenger Car Bodies', '1231', 'DE', NOW(), NOW(), '{"website": "https://www.tesla.com"}'),
('0000789019', 'Microsoft Corporation', 'MSFT', '7372', 'Services-Prepackaged Software', '0630', 'WA', NOW(), NOW(), '{"website": "https://www.microsoft.com"}'),
('0001045810', 'NVIDIA Corporation', 'NVDA', '3674', 'Semiconductors & Related Devices', '0128', 'DE', NOW(), NOW(), '{"website": "https://www.nvidia.com"}'),
('0001467373', 'Netflix, Inc.', 'NFLX', '7841', 'Services-Video Tape Rental', '1231', 'DE', NOW(), NOW(), '{"website": "https://www.netflix.com"}'),
('0001065280', 'Salesforce, Inc.', 'CRM', '7372', 'Services-Prepackaged Software', '0131', 'DE', NOW(), NOW(), '{"website": "https://www.salesforce.com"}'),
('0001533932', 'Adobe Inc.', 'ADBE', '7372', 'Services-Prepackaged Software', '1130', 'DE', NOW(), NOW(), '{"website": "https://www.adobe.com"}')
ON CONFLICT (cik) DO NOTHING;

-- Insert sample filings for Apple
INSERT INTO filings (accession_number, company_cik, form_type, filing_date, period_of_report, accepted_datetime, description, document_count, file_url, indexed, created_at, metadata) VALUES
('0000320193-23-000077', '0000320193', '10-K', '2023-11-03', '2023-09-30', '2023-11-03 16:30:00', 'Annual Report', 120, 'https://www.sec.gov/Archives/edgar/data/320193/000032019323000077/0000320193-23-000077-index.htm', TRUE, NOW(), '{"fiscal_year": 2023}'),
('0000320193-23-000064', '0000320193', '10-Q', '2023-08-04', '2023-07-01', '2023-08-04 16:30:00', 'Quarterly Report', 85, 'https://www.sec.gov/Archives/edgar/data/320193/000032019323000064/0000320193-23-000064-index.htm', TRUE, NOW(), '{"fiscal_quarter": "Q3"}'),
('0000320193-23-000047', '0000320193', '10-Q', '2023-05-05', '2023-04-01', '2023-05-05 16:30:00', 'Quarterly Report', 82, 'https://www.sec.gov/Archives/edgar/data/320193/000032019323000047/0000320193-23-000047-index.htm', TRUE, NOW(), '{"fiscal_quarter": "Q2"}'),
('0000320193-23-000006', '0000320193', '8-K', '2023-01-06', '2023-01-05', '2023-01-06 08:30:00', 'Current Report', 15, 'https://www.sec.gov/Archives/edgar/data/320193/000032019323000006/0000320193-23-000006-index.htm', TRUE, NOW(), '{"event": "Earnings Release"}')
ON CONFLICT (accession_number) DO NOTHING;

-- Insert sample filings for Amazon
INSERT INTO filings (accession_number, company_cik, form_type, filing_date, period_of_report, accepted_datetime, description, document_count, file_url, indexed, created_at, metadata) VALUES
('0001018724-23-000004', '0001018724', '10-K', '2023-02-03', '2022-12-31', '2023-02-03 16:30:00', 'Annual Report', 145, 'https://www.sec.gov/Archives/edgar/data/1018724/000101872423000004/0001018724-23-000004-index.htm', TRUE, NOW(), '{"fiscal_year": 2022}'),
('0001018724-23-000013', '0001018724', '10-Q', '2023-05-05', '2023-03-31', '2023-05-05 16:30:00', 'Quarterly Report', 92, 'https://www.sec.gov/Archives/edgar/data/1018724/000101872423000013/0001018724-23-000013-index.htm', TRUE, NOW(), '{"fiscal_quarter": "Q1"}'),
('0001018724-23-000020', '0001018724', '8-K', '2023-04-27', '2023-04-27', '2023-04-27 16:30:00', 'Current Report', 18, 'https://www.sec.gov/Archives/edgar/data/1018724/000101872423000020/0001018724-23-000020-index.htm', TRUE, NOW(), '{"event": "Earnings Announcement"}')
ON CONFLICT (accession_number) DO NOTHING;

-- Insert sample filings for Alphabet
INSERT INTO filings (accession_number, company_cik, form_type, filing_date, period_of_report, accepted_datetime, description, document_count, file_url, indexed, created_at, metadata) VALUES
('0001652044-23-000008', '0001652044', '10-K', '2023-02-03', '2022-12-31', '2023-02-03 16:30:00', 'Annual Report', 132, 'https://www.sec.gov/Archives/edgar/data/1652044/000165204423000008/0001652044-23-000008-index.htm', TRUE, NOW(), '{"fiscal_year": 2022}'),
('0001652044-23-000016', '0001652044', '10-Q', '2023-04-26', '2023-03-31', '2023-04-26 16:30:00', 'Quarterly Report', 88, 'https://www.sec.gov/Archives/edgar/data/1652044/000165204423000016/0001652044-23-000016-index.htm', TRUE, NOW(), '{"fiscal_quarter": "Q1"}')
ON CONFLICT (accession_number) DO NOTHING;

-- Insert sample filings for Tesla
INSERT INTO filings (accession_number, company_cik, form_type, filing_date, period_of_report, accepted_datetime, description, document_count, file_url, indexed, created_at, metadata) VALUES
('0001318605-23-000012', '0001318605', '10-K', '2023-01-31', '2022-12-31', '2023-01-31 16:30:00', 'Annual Report', 156, 'https://www.sec.gov/Archives/edgar/data/1318605/000131860523000012/0001318605-23-000012-index.htm', TRUE, NOW(), '{"fiscal_year": 2022}'),
('0001318605-23-000034', '0001318605', '10-Q', '2023-04-24', '2023-03-31', '2023-04-24 16:30:00', 'Quarterly Report', 95, 'https://www.sec.gov/Archives/edgar/data/1318605/000131860523000034/0001318605-23-000034-index.htm', TRUE, NOW(), '{"fiscal_quarter": "Q1"}'),
('0001318605-23-000045', '0001318605', '8-K', '2023-07-19', '2023-07-19', '2023-07-19 16:30:00', 'Current Report', 22, 'https://www.sec.gov/Archives/edgar/data/1318605/000131860523000045/0001318605-23-000045-index.htm', TRUE, NOW(), '{"event": "Q2 2023 Earnings"}')
ON CONFLICT (accession_number) DO NOTHING;

-- Insert sample users
INSERT INTO users (id, email, oauth_provider, oauth_id, full_name, is_active, created_at, last_login_at) VALUES
(gen_random_uuid(), 'demo@example.com', 'google', 'demo_oauth_123', 'Demo User', TRUE, NOW(), NOW()),
(gen_random_uuid(), 'test@example.com', 'google', 'test_oauth_456', 'Test User', TRUE, NOW(), NOW()),
(gen_random_uuid(), 'analyst@example.com', 'google', 'analyst_oauth_789', 'Financial Analyst', TRUE, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- Create a demo alert for monitoring Apple 10-K filings
DO $$
DECLARE
    demo_user_id UUID;
BEGIN
    SELECT id INTO demo_user_id FROM users WHERE email = 'demo@example.com' LIMIT 1;

    IF demo_user_id IS NOT NULL THEN
        INSERT INTO user_alerts (id, user_id, name, conditions, notification_method, frequency, is_active, created_at, updated_at) VALUES
        (gen_random_uuid(), demo_user_id, 'Apple Annual Reports', '{"company_cik": "0000320193", "form_types": ["10-K"]}', 'email', 'immediate', TRUE, NOW(), NOW()),
        (gen_random_uuid(), demo_user_id, 'Tech Company 8-Ks', '{"company_ciks": ["0000320193", "0001018724", "0001652044"], "form_types": ["8-K"]}', 'email', 'daily', TRUE, NOW(), NOW())
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

EOF
)

# Execute seed data
print_info "Inserting seed data into database..."

echo "$SEED_SQL" | docker-compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

print_success "Seed data inserted"

# Summary
print_header "Seed Complete!"

print_success "Test data has been added to the database"
echo ""
print_info "Summary of seeded data:"
echo "  ✓ 10 public companies (Apple, Amazon, Google, Meta, Tesla, Microsoft, NVIDIA, Netflix, Salesforce, Adobe)"
echo "  ✓ 13 sample SEC filings (10-K, 10-Q, 8-K forms)"
echo "  ✓ 3 test user accounts"
echo "  ✓ 2 sample alerts"
echo ""
print_info "Test credentials:"
echo "  - demo@example.com (Demo User)"
echo "  - test@example.com (Test User)"
echo "  - analyst@example.com (Financial Analyst)"
echo ""
print_info "You can now:"
echo "  1. Start the API: docker-compose up api"
echo "  2. Query companies: GET http://localhost:8000/api/v1/companies"
echo "  3. Search filings: GET http://localhost:8000/api/v1/filings"
echo "  4. View API docs: http://localhost:8000/docs"
echo ""
