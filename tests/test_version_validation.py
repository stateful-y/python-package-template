"""Tests for version validation in copier.yml."""

import pytest


class TestVersionValidation:
    """Test that version validation works correctly."""

    @pytest.mark.parametrize(
        "version",
        [
            # Standard semantic versions
            "0.1.0",
            "1.0.0",
            "1.2.3",
            "10.20.30",
            "999.999.999",
            # Pre-release versions
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-beta.2",
            "1.0.0-rc.1",
            "1.0.0-0.3.7",
            "1.0.0-x.7.z.92",
            "2.0.0-alpha.beta",
            # Build metadata
            "1.0.0+build.1",
            "1.0.0+20130313144700",
            "1.0.0+exp.sha.5114f85",
            "1.0.0+21AF26D3----117B344092BD",
            # Pre-release + build metadata
            "1.0.0-beta+exp.sha.5114f85",
            "1.0.0-alpha.1+001",
            "2.0.0-rc.1+build.123",
        ],
    )
    def test_valid_versions_accepted(self, copie, version):
        """Test that valid semantic versions are accepted."""
        result = copie.copy(extra_answers={"version": version})
        assert result.exit_code == 0, f"Version {version!r} should be accepted but was rejected"

    @pytest.mark.parametrize(
        "version",
        [
            # Incomplete versions
            "1",
            "1.2",
            "1.2.3.4",
            # With prefix
            "v1.2.3",
            "V1.2.3",
            # Invalid characters
            "1.2.x",
            "1.x.3",
            "x.2.3",
            "1.2.3.beta",
            # Leading zeros (invalid in strict semver)
            "01.2.3",
            "1.02.3",
            "1.2.03",
            "001.002.003",
            # Empty or whitespace
            "",
            " ",
            "   ",
            # Trailing/leading characters
            "1.2.3-",
            "1.2.3+",
            "-1.2.3",
            "+1.2.3",
            " 1.2.3",
            "1.2.3 ",
            # Invalid format
            "abc",
            "alpha.beta.gamma",
            "1,2,3",
            "1_2_3",
        ],
    )
    def test_invalid_versions_rejected(self, copie, version):
        """Test that invalid versions are rejected."""
        with pytest.raises(ValueError) as exc_info:
            copie.copy(extra_answers={"version": version})

        # Check that error message mentions version validation
        error_msg = str(exc_info.value).lower()
        assert "version" in error_msg, f"Error message should mention version. Got: {exc_info.value}"


class TestVersionPropagation:
    """Test that version values propagate correctly to generated files."""

    @pytest.mark.parametrize(
        "version",
        [
            "0.1.0",
            "1.0.0",
            "2.3.4-alpha.1",
            "3.0.0+build.123",
        ],
    )
    def test_version_appears_in_changelog(self, copie, version):
        """Test that version appears in CHANGELOG.md."""
        result = copie.copy(extra_answers={"version": version})
        assert result.exit_code == 0

        changelog_path = result.project_dir / "CHANGELOG.md"
        assert changelog_path.is_file()

        content = changelog_path.read_text(encoding="utf-8")
        assert version in content, f"Version {version} not found in CHANGELOG.md"

    def test_pyproject_uses_dynamic_versioning(self, copie):
        """Test that pyproject.toml uses dynamic versioning via hatch-vcs."""
        result = copie.copy(extra_answers={"version": "1.2.3"})
        assert result.exit_code == 0

        pyproject_path = result.project_dir / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")

        # Should use dynamic versioning, not hardcoded version
        assert 'dynamic = ["version"]' in content
        assert "[tool.hatch.version]" in content
        assert 'source = "vcs"' in content
        # Version should NOT be hardcoded in project metadata
        assert 'version = "1.2.3"' not in content
