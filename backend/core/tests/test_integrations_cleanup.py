"""
Tests for integrations cleanup — file-absence and symbol-absence.

Validates: Requirements 1.1, 2.1, 2.2
"""
import importlib
import os

import pytest

# Base path of the integrations package
INTEGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__),  # backend/core/tests/
    "..",                        # backend/core/
    "integrations",
)


class TestDeletedFilesAbsent:
    """Assert that the deleted module files no longer exist on the filesystem."""

    def test_pms_github_file_does_not_exist(self):
        """Requirement 1.1: pms_github.py must be absent."""
        path = os.path.abspath(os.path.join(INTEGRATIONS_DIR, "pms_github.py"))
        assert not os.path.exists(path), f"Expected {path} to be deleted, but it still exists."

    def test_vc_validator_file_does_not_exist(self):
        """Requirement 2.1: vc_validator.py must be absent."""
        path = os.path.abspath(os.path.join(INTEGRATIONS_DIR, "vc_validator.py"))
        assert not os.path.exists(path), f"Expected {path} to be deleted, but it still exists."


class TestValidateVcCredentialsNotImportable:
    """Assert that validate_vc_credentials cannot be imported from any package path."""

    def test_vc_validator_module_not_importable(self):
        """Requirement 2.1: the vc_validator module itself must not be importable."""
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("core.integrations.vc_validator")

    def test_validate_vc_credentials_not_in_integrations_init(self):
        """Requirement 2.2: validate_vc_credentials must not be accessible via core.integrations."""
        import core.integrations as pkg
        assert not hasattr(pkg, "validate_vc_credentials"), (
            "validate_vc_credentials should not be exported from core.integrations"
        )

    def test_validate_vc_credentials_not_importable_directly(self):
        """Requirement 2.2: direct import of validate_vc_credentials must fail."""
        with pytest.raises((ImportError, ModuleNotFoundError)):
            from core.integrations.vc_validator import validate_vc_credentials  # noqa: F401


class TestPreservedModulesImportable:
    """Assert that preserved modules remain importable after cleanup.

    Validates: Requirements 5.3, 5.4
    """

    def test_validate_github_token_importable(self):
        """Requirement 5.3: validate_github_token must be importable at its current dotted path."""
        from core.integrations.github_validator import validate_github_token  # noqa: F401
        assert callable(validate_github_token)

    def test_parse_url_schema_importable(self):
        """Requirement 5.4: custom_tool_parser must remain intact and parse_url_schema importable."""
        from core.integrations.custom_tool_parser import parse_url_schema  # noqa: F401
        assert callable(parse_url_schema)
