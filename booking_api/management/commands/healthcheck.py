"""
Django management command for checking external service health.

This command verifies connectivity to Redis and other external services
before the application starts fully. Useful in Docker containers and
deployment pipelines.
"""

import sys

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check health of external services (Redis, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fail-fast",
            action="store_true",
            help="Exit with error code if any health check fails",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Only output errors (suppress success messages)",
        )

    def handle(self, *args, **options):
        fail_fast = options["fail_fast"]
        quiet = options["quiet"]
        all_passed = True

        if not quiet:
            self.stdout.write("Running health checks...")

        # Check Redis connection
        redis_ok = self.check_redis_connection(quiet)
        if not redis_ok:
            all_passed = False

        # Add more health checks here as needed
        # db_ok = self.check_database_connection(quiet)
        # twilio_ok = self.check_twilio_connection(quiet)

        # Final summary
        if all_passed:
            if not quiet:
                self.stdout.write(self.style.SUCCESS("\nAll health checks passed!"))
            sys.exit(0)
        else:
            self.stdout.write(
                self.style.ERROR("\nSome health checks failed. See errors above.")
            )
            if fail_fast:
                sys.exit(1)
            else:
                sys.exit(0)

    def check_redis_connection(self, quiet=False):
        """
        Check Redis cache connection.

        Args:
            quiet (bool): If True, suppress success messages

        Returns:
            bool: True if Redis connection is successful, False otherwise
        """
        try:
            # Test Redis by setting and getting a value
            test_key = "healthcheck_redis"
            test_value = "ok"

            cache.set(test_key, test_value, timeout=5)
            retrieved_value = cache.get(test_key)

            if retrieved_value == test_value:
                if not quiet:
                    self.stdout.write(self.style.SUCCESS("✓ Redis connection OK"))
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "✗ Redis connection test failed (value mismatch)"
                    )
                )
                return False

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Redis connection failed: {e}"))
            return False
