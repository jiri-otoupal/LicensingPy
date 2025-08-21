"""
Tests for the license_manager module.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
import pytest

from licensing.license_manager import LicenseManager
from licensing.exceptions import (
    LicenseError, LicenseExpiredError, 
    LicenseInvalidError, HardwareMismatchError
)


class TestLicenseManager:
    """Test the LicenseManager class."""
    
    def test_init(self, key_pair, test_preseed):
        """Test LicenseManager initialization."""
        manager = LicenseManager(key_pair['public_key'], test_preseed)
        
        assert manager.public_key_b64 == key_pair['public_key']
        assert manager.preseed == test_preseed
        assert manager.crypto is not None
        assert manager.hw_fingerprint is not None
    
    def test_verify_license_valid(self, license_manager, sample_license):
        """Test verification of valid license."""
        # Skip hardware check since we're using sample license from different machine
        license_data = license_manager.verify_license(
            sample_license, 
            check_hardware=False, 
            check_expiry=False
        )
        
        assert license_data["version"] == "1.0"
        assert "component_name" in license_data
        assert "app_name" in license_data
    
    def test_verify_license_with_hardware_and_expiry(self, license_generator, license_manager):
        """Test license verification with hardware and expiry checks."""
        # Generate license for current machine
        license_string = license_generator.generate_license(
            expiry_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        # Should verify successfully
        license_data = license_manager.verify_license(license_string)
        assert license_data["component_name"] == "TestComponent"
    
    def test_verify_expired_license(self, license_generator, license_manager):
        """Test verification of expired license."""
        # Generate expired license
        license_string = license_generator.generate_license(
            expiry_date="2020-01-01",  # Expired
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        # Should raise LicenseExpiredError
        with pytest.raises(LicenseExpiredError):
            license_manager.verify_license(license_string, check_hardware=False)
    
    def test_verify_license_skip_expiry(self, license_generator, license_manager):
        """Test verification skipping expiry check."""
        # Generate expired license
        license_string = license_generator.generate_license(
            expiry_date="2020-01-01",  # Expired
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        # Should succeed when skipping expiry
        license_data = license_manager.verify_license(
            license_string, 
            check_hardware=False, 
            check_expiry=False
        )
        assert license_data["component_name"] == "TestComponent"
    
    def test_verify_invalid_json(self, license_manager):
        """Test verification of invalid JSON license."""
        with pytest.raises(LicenseInvalidError, match="not valid JSON"):
            license_manager.verify_license("invalid json string")
    
    def test_verify_missing_required_fields(self, license_manager):
        """Test verification of license missing required fields."""
        incomplete_license = json.dumps({
            "version": "1.0",
            "hw_type": "mac"
            # Missing other required fields
        })
        
        with pytest.raises(LicenseInvalidError, match="Missing required field"):
            license_manager.verify_license(incomplete_license)
    
    def test_verify_unsupported_version(self, license_manager):
        """Test verification of license with unsupported version."""
        invalid_license = json.dumps({
            "version": "2.0",  # Unsupported version
            "hw_type": "mac",
            "hw_info": "test",
            "expiry": "2025-12-31",
            "issued": "2025-01-01",
            "preseed_hash": "test",
            "component_name": "test",
            "signature": "test"
        })
        
        with pytest.raises(LicenseInvalidError, match="Unsupported license version"):
            license_manager.verify_license(invalid_license)
    
    def test_verify_invalid_date_format(self, license_manager):
        """Test verification of license with invalid date format."""
        invalid_license = json.dumps({
            "version": "1.0",
            "hw_type": "mac",
            "hw_info": "test",
            "expiry": "invalid-date",  # Invalid format
            "issued": "2025-01-01",
            "preseed_hash": "test",
            "component_name": "test",
            "signature": "test"
        })
        
        with pytest.raises(LicenseInvalidError, match="Invalid date format"):
            license_manager.verify_license(invalid_license)
    
    def test_is_valid_method(self, license_manager, sample_license):
        """Test is_valid method."""
        # Should return True for valid license
        assert license_manager.is_valid(
            sample_license, 
            check_hardware=False, 
            check_expiry=False
        ) is True
        
        # Should return False for invalid license
        assert license_manager.is_valid("invalid license") is False
    
    def test_get_license_info(self, license_manager, sample_license):
        """Test getting license info without full validation."""
        info = license_manager.get_license_info(sample_license)
        
        assert "version" in info
        assert "hw_type" in info
        assert "component_name" in info
        assert "status" in info
        
        status = info["status"]
        assert "is_expired" in status
        assert "hardware_matches" in status
        assert "preseed_valid" in status
    
    def test_get_days_until_expiry(self, license_generator, license_manager):
        """Test getting days until license expiry."""
        # Future license
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        license_string = license_generator.generate_license(
            expiry_date=future_date,
            fingerprint_type="mac"
        )
        
        days = license_manager.get_days_until_expiry(license_string)
        assert days == 30
        
        # Expired license
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        expired_license = license_generator.generate_license(
            expiry_date=past_date,
            fingerprint_type="mac"
        )
        
        days = license_manager.get_days_until_expiry(expired_license)
        assert days == -10
    
    def test_get_days_until_expiry_invalid_license(self, license_manager):
        """Test getting days until expiry for invalid license."""
        days = license_manager.get_days_until_expiry("invalid license")
        assert days is None
    
    def test_get_hardware_fingerprint(self, license_manager):
        """Test getting current hardware fingerprint."""
        fingerprint = license_manager.get_hardware_fingerprint("mac")
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
        
        # Different types should return different fingerprints (usually)
        composite_fp = license_manager.get_hardware_fingerprint("composite")
        assert isinstance(composite_fp, str)
    
    def test_auto_verify_licenses_no_files(self, temp_dir):
        """Test auto verify when no license files exist."""
        results = LicenseManager.auto_verify_licenses(working_dir=str(temp_dir))
        
        assert "error" in results
        assert "No license files found" in results["error"]
    
    def test_auto_verify_licenses_no_keys(self, temp_dir):
        """Test auto verify when no key files exist."""
        # Create a license file but no key files
        license_file = temp_dir / "license.txt"
        license_file.write_text("dummy license content")
        
        results = LicenseManager.auto_verify_licenses(working_dir=str(temp_dir))
        
        assert "error" in results
        assert "No key files found" in results["error"]
    
    def test_auto_verify_licenses_success(self, temp_dir, license_generator, key_pair, preseed_file):
        """Test successful auto verification."""
        # Create license file
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="AutoTestComponent"
        )
        license_file = temp_dir / "license.txt"
        license_file.write_text(license_string)
        
        # Create key file
        key_file = temp_dir / "keys.json"
        preseed_hash = license_generator.preseed
        key_data = {
            "public_key": key_pair["public_key"],
            "preseed": preseed_hash
        }
        key_file.write_text(json.dumps(key_data))
        
        results = LicenseManager.auto_verify_licenses(
            working_dir=str(temp_dir),
            check_hardware=False,
            check_expiry=False
        )
        
        assert "error" not in results
        assert results["summary"]["total_licenses"] >= 1
        assert len(results["license_files_found"]) >= 1
        assert len(results["key_files_found"]) >= 1
    
    def test_auto_verify_multiple_licenses(self, temp_dir, license_generator, key_pair):
        """Test auto verification with multiple licenses in one file."""
        # Create multiple licenses
        license1 = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="Component1"
        )
        license2 = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="Component2"
        )
        
        # Write to file (one per line)
        license_file = temp_dir / "licenses.txt"
        license_file.write_text(f"{license1}\n{license2}")
        
        # Create key file
        key_file = temp_dir / "keys.json"
        key_data = {
            "public_key": key_pair["public_key"],
            "preseed": license_generator.preseed
        }
        key_file.write_text(json.dumps(key_data))
        
        results = LicenseManager.auto_verify_licenses(
            working_dir=str(temp_dir),
            check_hardware=False,
            check_expiry=False
        )
        
        assert results["summary"]["total_licenses"] == 2
    
    def test_verify_wrong_preseed(self, license_generator, key_pair):
        """Test verification with wrong preseed."""
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        # Create manager with wrong preseed
        wrong_manager = LicenseManager(key_pair['public_key'], "wrong-preseed")
        
        with pytest.raises(LicenseInvalidError, match="preseed hash is invalid"):
            wrong_manager.verify_license(
                license_string, 
                check_hardware=False, 
                check_expiry=False
            )
    
    def test_verify_wrong_public_key(self, license_generator, crypto_manager, test_preseed):
        """Test verification with wrong public key."""
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        # Generate different key pair
        wrong_private, wrong_public = crypto_manager.generate_key_pair()
        wrong_manager = LicenseManager(wrong_public, test_preseed)
        
        with pytest.raises(LicenseInvalidError, match="signature is invalid"):
            wrong_manager.verify_license(
                license_string, 
                check_hardware=False, 
                check_expiry=False
            )
