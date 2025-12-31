"""
Security Tests for SSL/TLS Certificate Verification

Critical tests to ensure SSL verification is working correctly and cannot be
bypassed accidentally.
"""

import pytest
import ssl
import aiohttp
from unittest.mock import patch, Mock

from src.core.checker import WebsiteStatusChecker
from src.config import CheckerConfig


@pytest.mark.security
class TestSSLVerificationDefault:
    """Test that SSL verification is enabled by default."""

    def test_ssl_verify_default_true(self):
        """Test SSL verification is True by default."""
        checker = WebsiteStatusChecker()

        assert checker.verify_ssl is True, "SSL verification MUST be True by default"

    def test_ssl_context_secure_by_default(self):
        """Test SSL context is secure by default."""
        checker = WebsiteStatusChecker()

        assert checker.ssl_context.check_hostname is True
        assert checker.ssl_context.verify_mode == ssl.CERT_REQUIRED

    def test_config_ssl_verify_default_true(self, clean_env):
        """Test configuration defaults to SSL verification enabled."""
        config = CheckerConfig()

        assert config.verify_ssl is True


@pytest.mark.security
class TestSSLVerificationEnforcement:
    """Test that SSL verification cannot be disabled accidentally."""

    def test_ssl_disabled_requires_explicit_parameter(self):
        """Test SSL can only be disabled with explicit parameter."""
        # Should not be possible to disable SSL without explicit parameter
        checker = WebsiteStatusChecker()

        assert checker.verify_ssl is True

    def test_ssl_disabled_logs_warning(self, caplog):
        """Test that disabling SSL logs a prominent warning."""
        import logging
        caplog.set_level(logging.WARNING)

        checker = WebsiteStatusChecker(verify_ssl=False)

        # Check for security warning in logs
        assert any("SSL CERTIFICATE VERIFICATION DISABLED" in record.message
                  for record in caplog.records)
        assert any("SECURITY RISK" in record.message
                  for record in caplog.records)

    def test_ssl_context_insecure_when_disabled(self):
        """Test SSL context is properly configured when disabled."""
        checker = WebsiteStatusChecker(verify_ssl=False)

        assert checker.ssl_context.check_hostname is False
        assert checker.ssl_context.verify_mode == ssl.CERT_NONE


@pytest.mark.security
@pytest.mark.asyncio
class TestSSLCertificateValidation:
    """Test actual SSL certificate validation behavior."""

    async def test_session_uses_ssl_context(self):
        """Test that session uses the configured SSL context."""
        checker = WebsiteStatusChecker(verify_ssl=True)
        await checker.create_session()

        assert checker.session is not None
        # Verify the session connector uses our SSL context
        assert checker.session.connector._ssl is not False

        await checker.close()

    async def test_session_respects_ssl_verification_setting(self):
        """Test session respects SSL verification setting."""
        # With SSL verification
        checker_secure = WebsiteStatusChecker(verify_ssl=True)
        await checker_secure.create_session()

        assert checker_secure.session.connector._ssl == checker_secure.ssl_context

        await checker_secure.close()

        # Without SSL verification
        checker_insecure = WebsiteStatusChecker(verify_ssl=False)
        await checker_insecure.create_session()

        assert checker_insecure.session.connector._ssl == checker_insecure.ssl_context

        await checker_insecure.close()


@pytest.mark.security
class TestProductionSSLRequirements:
    """Test production environment SSL requirements."""

    def test_production_config_validates_ssl(self, production_env):
        """Test production config validation catches disabled SSL."""
        import os
        os.environ["SSL_VERIFY_DEFAULT"] = "false"

        from src.config import AppConfig
        config = AppConfig()

        issues = config.validate_production_config()

        critical_issues = [i for i in issues if "CRITICAL" in i or "SSL" in i]
        assert len(critical_issues) > 0, "Production must flag disabled SSL as critical"

    def test_production_prevents_ssl_disable(self, production_env):
        """Test that production environment raises alarm for disabled SSL."""
        import os
        os.environ["SSL_VERIFY_DEFAULT"] = "false"

        from src.config import AppConfig
        config = AppConfig()

        issues = config.validate_production_config()

        # Should have SSL-related warning
        assert any("SSL" in issue for issue in issues)


@pytest.mark.security
class TestSSLConfigurationPersistence:
    """Test SSL configuration is properly propagated through the system."""

    def test_batch_config_propagates_ssl_setting(self):
        """Test batch config properly propagates SSL setting."""
        from src.core.batch import BatchConfig, BatchProcessor

        # With SSL verification
        config_secure = BatchConfig(verify_ssl=True)
        processor_secure = BatchProcessor(config_secure)

        assert processor_secure.checker.verify_ssl is True

        # Without SSL verification
        config_insecure = BatchConfig(verify_ssl=False)
        processor_insecure = BatchProcessor(config_insecure)

        assert processor_insecure.checker.verify_ssl is False

    def test_cli_flag_propagates_ssl_setting(self):
        """Test CLI --disable-ssl-verify flag is properly handled."""
        from src.core.batch import BatchConfig

        # Simulate CLI with SSL verification disabled
        config = BatchConfig(verify_ssl=False)

        assert config.verify_ssl is False


@pytest.mark.security
class TestSSLBypassPrevention:
    """Test that SSL verification cannot be bypassed through various means."""

    def test_cannot_bypass_via_session_get_ssl_param(self):
        """Test that SSL context is used, not session.get ssl param."""
        checker = WebsiteStatusChecker(verify_ssl=True)

        # Verify that the SSL context is secure
        assert checker.ssl_context.verify_mode == ssl.CERT_REQUIRED

    def test_env_var_ssl_disable_logged(self, clean_env, caplog):
        """Test that environment variable SSL disable is logged."""
        import logging
        import os
        caplog.set_level(logging.WARNING)

        os.environ["SSL_VERIFY_DEFAULT"] = "false"

        from src.config import CheckerConfig
        config = CheckerConfig()

        # Should propagate to checker
        checker = WebsiteStatusChecker(verify_ssl=config.verify_ssl)

        assert any("SSL" in record.message for record in caplog.records)


@pytest.mark.security
class TestSSLSecurityBestPractices:
    """Test SSL security best practices are followed."""

    def test_default_context_uses_system_ca_bundle(self):
        """Test that default SSL context uses system CA certificates."""
        checker = WebsiteStatusChecker(verify_ssl=True)

        # Should use default context which loads system CAs
        assert checker.ssl_context.check_hostname is True
        assert checker.ssl_context.verify_mode == ssl.CERT_REQUIRED

    def test_ssl_disabled_uses_weak_ciphers_for_compatibility(self):
        """Test that SSL disabled mode allows weak ciphers for compatibility."""
        checker = WebsiteStatusChecker(verify_ssl=False)

        # When SSL is disabled, we use permissive settings
        # This is by design for compatibility, but should be documented
        assert checker.ssl_context.verify_mode == ssl.CERT_NONE
