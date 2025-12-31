"""
Security Tests for File Upload Limits

Tests to ensure file upload size limits prevent DoS attacks and resource exhaustion.
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO

from gui.config import get_settings


@pytest.mark.security
class TestFileUploadSizeLimits:
    """Test file upload size limit enforcement."""

    def test_upload_limit_configured(self):
        """Test that upload size limit is properly configured."""
        settings = get_settings()

        assert settings.max_upload_size_mb > 0
        assert settings.max_upload_size_mb <=200  # Reasonable max
        assert settings.max_upload_size_bytes == settings.max_upload_size_mb * 1024 * 1024

    def test_upload_within_limit_succeeds(self, test_client):
        """Test that files within size limit can be uploaded."""
        settings = get_settings()

        # Create a small CSV file (well under limit)
        small_file = BytesIO(b"url\nhttps://example.com\n")
        small_file.name = "test.csv"

        response = test_client.post(
            "/api/upload/",
            files={"file": ("test.csv", small_file, "text/csv")}
        )

        # Should succeed (or fail for other reasons, but not size)
        assert response.status_code != 413

    def test_upload_exceeds_limit_rejected(self, test_client):
        """Test that files exceeding size limit are rejected."""
        settings = get_settings()

        # Create a file that's too large
        # Note: In real test, we'd mock this to avoid creating huge files
        large_size = settings.max_upload_size_bytes + 1024

        response = test_client.post(
            "/api/upload/",
            files={"file": ("large.csv", b"x" * 1024, "text/csv")},
            headers={"Content-Length": str(large_size)}
        )

        assert response.status_code == 413  # Payload Too Large
        assert "too large" in response.json()["detail"].lower()

    def test_upload_size_logged(self, test_client, caplog):
        """Test that upload attempts are logged."""
        import logging
        caplog.set_level(logging.INFO)

        small_file = BytesIO(b"url\nhttps://example.com\n")
        small_file.name = "test.csv"

        test_client.post(
            "/api/upload/",
            files={"file": ("test.csv", small_file, "text/csv")}
        )

        # Should log upload attempt
        assert any("upload" in record.message.lower() for record in caplog.records)


@pytest.mark.security
class TestFileUploadValidation:
    """Test file upload content type and extension validation."""

    def test_invalid_content_type_rejected(self, test_client):
        """Test that invalid content types are rejected."""
        # Try to upload an executable
        exe_file = BytesIO(b"MZ\x90\x00")  # PE header
        exe_file.name = "malware.exe"

        response = test_client.post(
            "/api/upload/",
            files={"file": ("malware.exe", exe_file, "application/x-msdownload")}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_invalid_extension_rejected(self, test_client):
        """Test that invalid file extensions are rejected."""
        # Try to upload with wrong extension
        bad_file = BytesIO(b"url\ntest")
        bad_file.name = "test.exe"

        response = test_client.post(
            "/api/upload/",
            files={"file": ("test.exe", bad_file, "text/csv")}
        )

        assert response.status_code == 400

    @pytest.mark.parametrize("allowed_ext", [".csv", ".xlsx", ".xls"])
    def test_allowed_extensions_accepted(self, test_client, allowed_ext):
        """Test that allowed extensions are accepted."""
        file_content = BytesIO(b"url\nhttps://example.com\n")
        filename = f"test{allowed_ext}"

        content_types = {
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel"
        }

        response = test_client.post(
            "/api/upload/",
            files={"file": (filename, file_content, content_types[allowed_ext])}
        )

        # Should not fail due to extension/content type
        assert response.status_code != 400 or "extension" not in response.json().get("detail", "").lower()


@pytest.mark.security
class TestUploadDosProtection:
    """Test protection against DoS attacks via uploads."""

    def test_multiple_large_uploads_prevented(self, test_client):
        """Test that multiple large upload attempts are prevented."""
        settings = get_settings()
        large_size = settings.max_upload_size_bytes + 1024

        # Try multiple large uploads
        for _ in range(3):
            response = test_client.post(
                "/api/upload/",
                files={"file": ("large.csv", b"x" * 1024, "text/csv")},
                headers={"Content-Length": str(large_size)}
            )

            assert response.status_code == 413

    def test_upload_middleware_rejects_early(self, test_client):
        """Test that middleware rejects oversized uploads before processing."""
        settings = get_settings()
        large_size = settings.max_upload_size_bytes + 1024

        # Middleware should reject based on Content-Length header
        response = test_client.post(
            "/api/upload/",
            files={"file": ("test.csv", b"data", "text/csv")},
            headers={"Content-Length": str(large_size)}
        )

        assert response.status_code == 413
