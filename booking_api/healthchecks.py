"""
Health check utilities for the booking API.

This module provides health check functions for external services
like Redis cache to ensure proper connectivity at startup.
"""

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def check_redis_connection():
    """
    Check Redis cache connection by performing a test set/get operation.

    Returns:
        bool: True if Redis connection is successful, False otherwise.

    Logs:
        - Info message on successful connection
        - Warning message on failed connection
    """
    try:
        cache.set("healthcheck_redis", "ok", timeout=5)
        value = cache.get("healthcheck_redis")
        if value == "ok":
            logger.info("Redis cache connection OK.")
            return True
        else:
            logger.warning("Redis cache connection test failed (no value).")
            return False
    except Exception as e:
        logger.error(f"Redis cache connection failed: {e}")
        return False


def run_startup_health_checks():
    """
    Run all startup health checks.

    This function is called during Django app initialization to verify
    that all external services are properly connected.
    """
    logger.info("Running startup health checks...")

    # Check Redis connection
    redis_ok = check_redis_connection()

    if not redis_ok:
        logger.warning(
            "Some health checks failed. Application may not function correctly."
        )
    else:
        logger.info("All startup health checks passed.")
