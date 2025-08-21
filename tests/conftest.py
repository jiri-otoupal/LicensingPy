"""
Pytest configuration and shared fixtures for the licensing system tests.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from licensing import LicenseGenerator, LicenseManager, PreseedGenerator
from licensing.crypto_utils import CryptoManager
from licensing.hardware_fingerprint import HardwareFingerprint


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def crypto_manager():
    """Create a CryptoManager instance."""
    return CryptoManager()


@pytest.fixture
def key_pair(crypto_manager):
    """Generate a test key pair."""
    private_key, public_key = crypto_manager.generate_key_pair()
    return {
        'private_key': private_key,
        'public_key': public_key
    }


@pytest.fixture
def test_preseed():
    """Standard test preseed."""
    return "test-preseed-for-pytest-2024"


@pytest.fixture
def preseed_file(temp_dir):
    """Create a test preseed file."""
    preseed_path = temp_dir / "test_preseed.json"
    PreseedGenerator.create_preseed_file(
        output_path=str(preseed_path),
        metadata={"project_name": "Test Project", "description": "Test preseed"},
        length=64
    )
    return preseed_path


@pytest.fixture
def preseed_hash(preseed_file):
    """Load preseed hash from test preseed file."""
    return PreseedGenerator.load_preseed_from_file(str(preseed_file))


@pytest.fixture
def license_generator(key_pair, preseed_hash):
    """Create a test license generator."""
    return LicenseGenerator(key_pair['private_key'], preseed_hash)


@pytest.fixture
def license_manager(key_pair, preseed_hash):
    """Create a test license manager."""
    return LicenseManager(key_pair['public_key'], preseed_hash)


@pytest.fixture
def sample_license(license_generator):
    """Generate a sample license for testing."""
    return license_generator.generate_license(
        expiry_date="2025-12-31",
        fingerprint_type="mac",
        component_name="TestComponent",
        additional_data={
            "app_name": "TestApp",
            "app_version": "1.0",
            "customer": "Test Customer"
        }
    )


@pytest.fixture
def hardware_fingerprint():
    """Create a hardware fingerprint instance."""
    return HardwareFingerprint()


@pytest.fixture(autouse=True)
def clean_test_files():
    """Automatically clean up test files after each test."""
    yield
    # Clean up any files that might have been created during tests
    test_files = [
        "test_license.txt",
        "test_keys.json", 
        "test_preseed.json",
        "demo_preseed.json",
        "license_verification_results.json"
    ]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
