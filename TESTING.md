# ARCHITECT // VAULT - Testing Guide

## Running Tests

### Setup Test Environment

\`\`\`bash
# Install test dependencies
pip install -r requirements.txt

# Create test database
createdb vault_test
\`\`\`

### Run All Tests

\`\`\`bash
pytest
\`\`\`

### Run Specific Test Suites

\`\`\`bash
# Authentication tests
pytest tests/test_auth.py

# Lead management tests
pytest tests/test_leads.py

# With coverage
pytest --cov=app --cov-report=html
\`\`\`

## Test Structure

\`\`\`
tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── test_auth.py         # Authentication tests
├── test_leads.py        # Lead management tests
├── test_messages.py     # Messaging tests
├── test_listings.py     # Listing tests
└── test_payments.py     # Payment tests
\`\`\`

## Writing Tests

All tests should:
- Use async/await for database operations
- Clean up test data after execution
- Mock external services (Monero RPC, PGP operations)
- Test both success and failure scenarios

## Manual Testing

### Test PGP Authentication

1. Generate test PGP keys:
\`\`\`bash
gpg --batch --gen-key deploy/config/test_key_params
\`\`\`

2. Export public key:
\`\`\`bash
gpg --armor --export test@vault.local > test_key.asc
\`\`\`

3. Test registration:
\`\`\`bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d @test_user.json
\`\`\`

### Test Monero Integration

Requires running Monero stagenet node and wallet RPC.

## Performance Testing

Use Locust for load testing:

\`\`\`bash
locust -f tests/load_test.py --host=http://localhost:8000
