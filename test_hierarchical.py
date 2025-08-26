#!/usr/bin/env python3
"""
Simple test script to verify hierarchical formatting is working correctly.
"""

import sys
from loguru import logger
from loguru._template_formatters import create_template_formatter

# Remove default handler
logger.remove()

# Add hierarchical template formatter
formatter = create_template_formatter(
    format_string="{time:HH:mm:ss} | {level} | {message}",
    template="hierarchical"
)

logger.add(sys.stderr, format=formatter.format_map, colorize=True, level="INFO")

print("Testing Beautiful Hierarchical Formatting")
print("=" * 50)

# Test case 1: User authentication
logger.info(
    "User authentication successful",
    user_id="alice_cooper", 
    email="alice@company.com",
    session_id="sess_abc123",
    ip="192.168.1.100",
    duration=0.045,
    status_code=200,
    method="POST"
)

print()

# Test case 2: Payment processing  
logger.success(
    "Payment processed successfully",
    user_id="john_doe",
    amount=299.99,
    currency="USD", 
    payment_method="credit_card",
    transaction_id="txn_xyz789",
    execution_time_seconds=1.234
)

print()

# Test case 3: Database error
logger.error(
    "Database connection timeout",
    error_type="ConnectionTimeout",
    database="postgres_prod",
    retry_count=3,
    execution_time_seconds=5.0,
    host="db.company.com",
    port=5432
)

print()

# Test case 4: API call
logger.warning(
    "API rate limit exceeded for endpoint https://api.service.com/v1/users",
    endpoint="/v1/users",
    rate_limit=1000,
    current_usage=1001,
    reset_time="2024-01-15T10:30:00Z",
    user_agent="MyApp/1.0"
)

print("\nHierarchical formatting test complete!")