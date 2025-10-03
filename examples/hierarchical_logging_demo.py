#!/usr/bin/env python3
"""
COMPREHENSIVE HIERARCHICAL LOGGING DEMO

This is the definitive demonstration of loguru's hierarchical logging extensions.
It showcases all implemented features with proper spacing and formatting.

FEATURES DEMONSTRATED:
✨ Hierarchical logging with Unicode box-drawing characters
✨ Rich contextual information with intelligent field prioritization
✨ Caught exceptions with hierarchical formatting
✨ Uncaught exceptions via global exception hook
✨ IDE-clickable file links in exception tracebacks
✨ Terminal-friendly color scheme (no black backgrounds)
✨ Proper spacing using format function approach
✨ Local variable extraction from exception frames
✨ Context-aware styling (URLs, IPs, emails, file paths)
✨ Performance optimization with intelligent caching

USAGE:
    python hierarchical_demo_final.py

This demo will:
1. Show regular hierarchical logging with various log levels
2. Demonstrate caught exception handling with rich context
3. Trigger an uncaught exception (terminates with beautiful formatting)
"""

import sys
import time
from pathlib import Path
from loguru import logger
from loguru._template_formatters import create_hierarchical_format_function
from loguru._exception_hook import install_exception_hook


def setup_hierarchical_logging():
    """
    Configure hierarchical logging with proper format function approach.
    
    CRITICAL: Always use create_hierarchical_format_function() for proper
    line ending control. This prevents the newline concatenation issue.
    """
    logger.remove()
    
    # Create hierarchical format function (NOT template formatter)
    format_func = create_hierarchical_format_function(
        format_string="{time:HH:mm:ss} | {level} | {name} | {message}",
        template="hierarchical"
    )
    
    logger.add(
        sys.stderr,
        format=format_func,  # Use format function directly
        colorize=True,
        level="DEBUG"
    )
    
    # Install hierarchical exception hook for uncaught exceptions
    hook = install_exception_hook(logger, "hierarchical")
    return hook


def demo_section(title: str, description: str):
    """Print a demo section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")
    print(f"{description}")
    print(f"{'=' * 80}")


def demo_basic_hierarchical_logging():
    """Demonstrate basic hierarchical logging across all levels."""
    demo_section(
        ">> BASIC HIERARCHICAL LOGGING", 
        "Shows hierarchical formatting with context across all log levels"
    )
    
    logger.debug("System initialization starting",
                 module="core_engine",
                 version="3.2.1",
                 build="release",
                 startup_time_ms=145,
                 memory_allocated_mb=256)
    
    time.sleep(0.3)
    
    logger.info("Database connections established",
               primary_db="postgresql://prod-db-01:5432/ecommerce",
               replica_db="postgresql://prod-db-02:5432/ecommerce", 
               connection_pool_size=25,
               response_time_ms=42,
               ssl_enabled=True,
               connection_timeout_seconds=30)
    
    time.sleep(0.3)
    
    logger.success("Authentication service ready",
                  service_url="https://auth.company.com/api/v2",
                  jwt_expiry_hours=24,
                  refresh_token_days=30,
                  supported_providers=["oauth2", "saml", "ldap"],
                  rate_limit_per_minute=1000)
    
    time.sleep(0.3)
    
    logger.warning("Memory usage approaching limits",
                  current_usage_percent=78.5,
                  warning_threshold_percent=75.0,
                  critical_threshold_percent=85.0,
                  available_memory_gb=3.2,
                  swap_usage_percent=12.1,
                  recommended_action="scale_horizontally")
    
    time.sleep(0.3)


def demo_rich_context_styling():
    """Demonstrate intelligent context styling for different data types."""
    demo_section(
        ">> INTELLIGENT CONTEXT STYLING", 
        "Shows automatic styling for URLs, IPs, emails, file paths, and more"
    )
    
    logger.info("Processing user authentication request",
               user_email="john.doe@enterprise.com",  # Email styling
               client_ip="192.168.1.100",             # IP styling  
               user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
               session_id="sess_abc123def456ghi789",
               login_url="https://app.company.com/auth/login",  # URL styling
               config_file="/etc/app/production.yml",          # File path styling
               request_time_ms=234,
               success_rate=99.7,
               is_premium_user=True,
               feature_flags=["dark_mode", "beta_features"])
    
    time.sleep(0.3)
    
    logger.info("File processing operation completed",
               source_file="C:\\Users\\admin\\Documents\\data\\customer_export.csv",
               destination_file="/var/uploads/processed/customers_2024.json",
               backup_location="s3://company-backups/daily/2024-08-27/",
               records_processed=15420,
               file_size_mb=234.7,
               processing_duration_seconds=45.3,
               compression_ratio=0.73,
               validation_errors=0)
    
    time.sleep(0.3)


def demo_performance_metrics():
    """Demonstrate logging with performance and business metrics."""
    demo_section(
        ">> PERFORMANCE & BUSINESS METRICS", 
        "Shows hierarchical logging for monitoring and business intelligence"
    )
    
    logger.info("API request processed successfully",
               endpoint="/api/v2/customers/search",
               method="POST",
               status_code=200,
               execution_time_seconds=0.245,
               database_query_time_ms=156,
               cache_hit_rate=0.87,
               response_size_kb=23.4,
               customer_count=1247,
               user_id="usr_enterprise_12345")
    
    time.sleep(0.3)
    
    logger.success("Payment transaction completed",
                  transaction_id="txn_prod_987654321",
                  amount_usd=1299.99,
                  payment_method="credit_card",
                  processor="stripe",
                  merchant_fee_usd=37.70,
                  processing_time_ms=892,
                  fraud_score=0.15,
                  risk_level="low",
                  customer_tier="gold")
    
    time.sleep(0.3)


def demo_caught_exception_with_context():
    """Demonstrate caught exception handling with rich hierarchical context."""
    demo_section(
        ">> CAUGHT EXCEPTION HANDLING", 
        "Shows logger.exception() with hierarchical formatting and rich context"
    )
    
    logger.info("Processing customer order validation workflow",
               order_id="ORD-2024-789123",
               customer_email="alice.johnson@enterprise.com",
               customer_tier="platinum",
               order_value_usd=2459.97,
               items_count=5,
               payment_method="corporate_card",
               shipping_method="express",
               expected_delivery_date="2024-08-30")
    
    time.sleep(0.3)
    
    try:
        # Simulate complex order processing that fails
        order_data = {
            "order_id": "ORD-2024-789123",
            "customer": {
                "email": "alice.johnson@enterprise.com",
                "tier": "platinum",
                "account_id": "acc_enterprise_456"
            },
            "items": [
                {"sku": "LAPTOP-DELL-XPS15", "quantity": 1, "price": 1899.99},
                {"sku": "MOUSE-WIRELESS", "quantity": 2, "price": 79.99},
                {"sku": "KEYBOARD-MECHANICAL", "quantity": 1, "price": 299.99},
                {"sku": "MONITOR-4K-27", "quantity": 1, "price": 399.99},
                {"sku": "WEBCAM-HD", "quantity": 1, "price": 129.99}
            ],
            "payment": {
                "method": "corporate_card",
                "card_last_four": "4567",
                "authorization": "auth_xyz789"
            },
            "totals": {
                "subtotal": 2389.95,
                "tax": 70.02,
                "total": 2459.97
            }
            # Missing required "shipping" section
        }
        
        # This will cause a KeyError with rich context available
        shipping_info = order_data["shipping"]  # KeyError!
        delivery_address = shipping_info["address"]
        logger.success(f"Order validated - shipping to {delivery_address}")
        
    except KeyError as e:
        logger.exception("Order validation failed due to incomplete data structure",
                        order_id="ORD-2024-789123",
                        customer_email="alice.johnson@enterprise.com", 
                        missing_section=str(e).strip("'\""),
                        error_category="data_validation",
                        severity_level="high",
                        business_impact="order_blocked",
                        auto_recovery_possible=False,
                        required_action="request_complete_order_data",
                        support_escalation_required=True,
                        estimated_resolution_minutes=15)
    
    time.sleep(0.5)


def demo_error_scenarios():
    """Demonstrate various error scenarios with hierarchical formatting."""
    demo_section(
        ">> ERROR SCENARIO HANDLING", 
        "Shows ERROR level logging with troubleshooting context"
    )
    
    logger.error("Database connection pool exhausted",
                connection_pool_size=25,
                active_connections=25,
                pending_requests=47,
                max_wait_time_seconds=30.0,
                database_host="prod-db-01.company.com",
                database_port=5432,
                last_successful_ping=1692.5,  # seconds ago
                error_type="connection_timeout",
                recommended_action="increase_pool_size_or_scale_read_replicas")
    
    time.sleep(0.3)
    
    logger.error("External API service unavailable",
                service_name="payment_processor_api",
                service_url="https://api.payments.com/v3/",
                http_status_code=503,
                response_time_ms=5000,
                retry_attempts=3,
                last_retry_at="2024-08-27T00:45:23Z",
                circuit_breaker_status="open",
                fallback_service_available=True,
                business_impact="payment_delays")
    
    time.sleep(0.3)


def trigger_uncaught_exception():
    """
    Trigger an uncaught exception to demonstrate global exception hook.
    
    This will terminate the program with beautiful hierarchical exception formatting.
    """
    demo_section(
        ">> UNCAUGHT EXCEPTION HANDLING", 
        "This will trigger an uncaught exception with hierarchical formatting"
    )
    
    logger.info("Initiating critical financial settlement process",
               settlement_batch_id="STL-BATCH-20240827-001",
               total_transactions=15420,
               total_amount_usd=2847392.50,
               settlement_bank="Wells Fargo Business",
               ach_routing_number="121000248",
               expected_settlement_date="2024-08-28",
               processing_fee_usd=1423.70,
               compliance_checks_passed=True)
    
    time.sleep(0.3)
    
    logger.info("Validating merchant account balances and limits",
               merchant_account_id="merch_enterprise_001",
               available_balance_usd=3240000.00,
               daily_limit_usd=5000000.00,
               monthly_volume_usd=24837291.20,
               risk_score=0.08,
               aml_status="compliant",
               sanctions_check="clear")
    
    time.sleep(0.3)
    
    # This will be an uncaught exception with beautiful hierarchical formatting!
    settlement_response = {
        "batch_id": "STL-BATCH-20240827-001",
        "bank": "wells_fargo",
        "transaction_count": 15420,
        "total_amount": 2847392.50,
        "processing_fee": 1423.70,
        "status": "processing",
        "created_at": "2024-08-27T00:47:15Z"
        # Missing required "settlement_reference" field that our code expects
    }
    
    # Accessing missing key - this will trigger beautiful hierarchical exception formatting!
    settlement_ref = settlement_response["settlement_reference"]  # KeyError - uncaught!
    logger.success(f"Settlement initiated successfully with reference: {settlement_ref}")


def main():
    """
    Main demonstration of all hierarchical logging features.
    
    This comprehensive demo shows every aspect of the hierarchical logging
    implementation, including the critical newline spacing fixes.
    """
    print("""
================================================================================
                    HIERARCHICAL LOGGING COMPREHENSIVE DEMO                   
================================================================================

This demo showcases the complete hierarchical logging implementation for loguru:

** KEY FEATURES:
   * Hierarchical Unicode box-drawing layouts
   * Rich contextual information with intelligent prioritization
   * Caught and uncaught exception handling
   * IDE-clickable file links in tracebacks
   * Context-aware styling (URLs, IPs, emails, paths)
   * Terminal-friendly color scheme
   * Performance-optimized with intelligent caching

** TECHNICAL HIGHLIGHTS:
   * Uses format function approach for proper line ending control
   * Solves newline concatenation issues (footer/header concatenation problem)
   * Integrates seamlessly with loguru's native systems
   * Maintains backward compatibility

** DEMO FLOW:
   1. Basic hierarchical logging (all levels)
   2. Intelligent context styling demonstration
   3. Performance and business metrics logging
   4. Caught exception with rich context
   5. Error scenario handling
   6. Uncaught exception (terminates with beautiful formatting)

Press Ctrl+C to exit early, or let it run to see the uncaught exception demo.
""")
    
    print("Starting demonstration in 3 seconds...")
    time.sleep(3)
    
    # Setup hierarchical logging with exception hook
    hook = setup_hierarchical_logging()
    
    try:
        # 1. Basic hierarchical logging demonstration
        demo_basic_hierarchical_logging()
        time.sleep(1)
        
        # 2. Rich context styling demonstration  
        demo_rich_context_styling()
        time.sleep(1)
        
        # 3. Performance metrics demonstration
        demo_performance_metrics()
        time.sleep(1)
        
        # 4. Caught exception demonstration
        demo_caught_exception_with_context()
        time.sleep(1)
        
        # 5. Error scenarios demonstration
        demo_error_scenarios()
        time.sleep(1)
        
        # 6. Uncaught exception demonstration (terminates program)
        print(f"\n{'>> WARNING'.center(80, '=')}")
        print("The next section will trigger an uncaught exception.")
        print("This is intentional and demonstrates the global exception hook.")
        print("The program will terminate with beautiful hierarchical formatting.")
        print("=" * 80)
        time.sleep(2)
        
        trigger_uncaught_exception()
        
        # This line will not be reached due to uncaught exception
        print("\n>> Demo completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n{'>> DEMO INTERRUPTED'.center(80, '=')}")
        print("Demo was interrupted by user (Ctrl+C)")
        print("=" * 80)
        # Cleanup hook on keyboard interrupt
        if 'hook' in locals():
            hook.uninstall()
    
    # NOTE: We don't uninstall the hook in a finally block because:
    # 1. For uncaught exceptions, the hook needs to remain active to handle them
    # 2. The program will terminate anyway after the uncaught exception
    # 3. Python will clean up automatically on program exit


if __name__ == "__main__":
    main()