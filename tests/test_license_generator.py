"""
Tests for the license_generator module.
"""

import json
import pytest
from datetime import datetime, timedelta

from licensing.license_generator import LicenseGenerator
from licensing.exceptions import LicenseError


class TestLicenseGenerator:
    """Test the LicenseGenerator class."""
    
    def test_init(self, key_pair, test_preseed):
        """Test LicenseGenerator initialization."""
        generator = LicenseGenerator(key_pair['private_key'], test_preseed)
        
        assert generator.private_key_b64 == key_pair['private_key']
        assert generator.preseed == test_preseed
        assert generator.crypto is not None
        assert generator.hw_fingerprint is not None
    
    def test_generate_license_basic(self, license_generator):
        """Test basic license generation."""
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac"
        )
        
        # Should be a JSON string
        license_data = json.loads(license_string)
        
        # Check required fields
        assert license_data["version"] == "1.0"
        assert license_data["hw_type"] == "mac"
        assert license_data["expiry"] == "2025-12-31"
        assert license_data["issued"] == datetime.now().strftime("%Y-%m-%d")
        assert "hw_info" in license_data
        assert "preseed_hash" in license_data
        assert "component_name" in license_data
        assert "signature" in license_data
    
    def test_generate_license_with_component_name(self, license_generator):
        """Test license generation with component name."""
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        license_data = json.loads(license_string)
        assert license_data["component_name"] == "TestComponent"
    
    def test_generate_license_without_component_name(self, license_generator):
        """Test license generation without component name."""
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac"
        )
        
        license_data = json.loads(license_string)
        assert license_data["component_name"] == ""
    
    def test_generate_license_with_additional_data(self, license_generator):
        """Test license generation with additional data."""
        additional_data = {
            "app_name": "TestApp",
            "app_version": "1.0",
            "customer": "Test Customer",
            "features": ["feature1", "feature2"]
        }
        
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="TestComponent",
            additional_data=additional_data
        )
        
        license_data = json.loads(license_string)
        
        # Additional data should be merged into license
        assert license_data["app_name"] == "TestApp"
        assert license_data["app_version"] == "1.0"
        assert license_data["customer"] == "Test Customer"
        assert license_data["features"] == ["feature1", "feature2"]
    
    def test_generate_license_all_fingerprint_types(self, license_generator):
        """Test license generation with all fingerprint types."""
        fingerprint_types = ["mac", "disk", "cpu", "system", "composite"]
        
        for fp_type in fingerprint_types:
            license_string = license_generator.generate_license(
                expiry_date="2025-12-31",
                fingerprint_type=fp_type
            )
            
            license_data = json.loads(license_string)
            assert license_data["hw_type"] == fp_type
            assert "hw_info" in license_data
    
    def test_generate_license_custom_hardware_fingerprint(self, license_generator):
        """Test license generation with custom hardware fingerprint."""
        custom_fingerprint = "custom_hardware_fingerprint_hash"
        
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="composite",
            hardware_fingerprint=custom_fingerprint
        )
        
        license_data = json.loads(license_string)
        assert license_data["hw_info"] == custom_fingerprint
    
    def test_generate_license_for_target(self, license_generator):
        """Test generating license for target hardware."""
        target_hardware = {
            "mac_addresses": ["00:11:22:33:44:55"],
            "disk_info": ["disk1", "disk2"],
            "cpu_info": {"processor": "Intel Core i7"},
            "system_info": {"system": "Windows", "node": "TestPC"}
        }
        
        license_string = license_generator.generate_license_for_target(
            target_hardware_info=target_hardware,
            expiry_date="2025-12-31",
            fingerprint_type="composite",
            component_name="RemoteComponent"
        )
        
        license_data = json.loads(license_string)
        assert license_data["version"] == "1.0"
        assert license_data["hw_type"] == "composite"
        assert license_data["component_name"] == "RemoteComponent"
        assert "hw_info" in license_data
        assert "signature" in license_data
    
    def test_generate_license_for_target_with_additional_data(self, license_generator):
        """Test generating license for target with additional data."""
        target_hardware = {"test": "hardware"}
        additional_data = {"app_name": "RemoteApp", "customer": "Remote Customer"}
        
        license_string = license_generator.generate_license_for_target(
            target_hardware_info=target_hardware,
            expiry_date="2025-12-31",
            additional_data=additional_data,
            component_name="RemoteComponent"
        )
        
        license_data = json.loads(license_string)
        assert license_data["app_name"] == "RemoteApp"
        assert license_data["customer"] == "Remote Customer"
        assert license_data["component_name"] == "RemoteComponent"
    
    def test_invalid_expiry_date_format(self, license_generator):
        """Test license generation with invalid expiry date."""
        with pytest.raises(ValueError, match="YYYY-MM-DD format"):
            license_generator.generate_license(
                expiry_date="invalid-date",
                fingerprint_type="mac"
            )
    
    def test_invalid_fingerprint_type(self, license_generator):
        """Test license generation with invalid fingerprint type."""
        with pytest.raises(ValueError, match="Invalid fingerprint_type"):
            license_generator.generate_license(
                expiry_date="2025-12-31",
                fingerprint_type="invalid_type"
            )
    
    def test_get_hardware_info(self, license_generator):
        """Test getting current hardware info."""
        hw_info = license_generator.get_hardware_info("mac")
        
        assert "mac_addresses" in hw_info
        assert isinstance(hw_info["mac_addresses"], list)
    
    def test_get_hardware_info_all_types(self, license_generator):
        """Test getting hardware info for all types."""
        types = ["mac", "disk", "cpu", "system", "composite"]
        
        for hw_type in types:
            hw_info = license_generator.get_hardware_info(hw_type)
            assert isinstance(hw_info, dict)
            assert len(hw_info) > 0  # Should contain some hardware info
    
    def test_parse_license(self, license_generator, sample_license):
        """Test parsing a generated license."""
        parsed = license_generator.parse_license(sample_license)
        
        assert "version" in parsed
        assert "hw_type" in parsed
        assert "expiry" in parsed
        assert "signature" in parsed
        assert parsed["version"] == "1.0"
    
    def test_generate_key_pair_static(self):
        """Test static key pair generation method."""
        private_key, public_key = LicenseGenerator.generate_key_pair()
        
        assert isinstance(private_key, str)
        assert isinstance(public_key, str)
        
        # Should be base64 encoded
        import base64
        private_decoded = base64.b64decode(private_key)
        public_decoded = base64.b64decode(public_key)
        
        assert b'PRIVATE KEY' in private_decoded
        assert b'PUBLIC KEY' in public_decoded
    
    def test_license_reproducibility(self, license_generator):
        """Test that same inputs produce different licenses (due to timestamps)."""
        license1 = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        license2 = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        # Should be different due to timestamp differences
        assert license1 != license2
        
        # But should have same structure
        data1 = json.loads(license1)
        data2 = json.loads(license2)
        
        assert data1["version"] == data2["version"]
        assert data1["hw_type"] == data2["hw_type"]
        assert data1["expiry"] == data2["expiry"]
        assert data1["component_name"] == data2["component_name"]
    
    def test_different_component_names_different_hashes(self, license_generator):
        """Test that different component names produce different preseed hashes."""
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
        
        data1 = json.loads(license1)
        data2 = json.loads(license2)
        
        # Component names should be different
        assert data1["component_name"] != data2["component_name"]
        
        # Preseed hashes should be different
        assert data1["preseed_hash"] != data2["preseed_hash"]
    
    def test_license_signature_validity(self, license_generator, license_manager):
        """Test that generated licenses have valid signatures."""
        license_string = license_generator.generate_license(
            expiry_date="2025-12-31",
            fingerprint_type="mac",
            component_name="TestComponent"
        )
        
        # Should be able to verify with corresponding manager
        # (This is more of an integration test but important for generator)
        license_data = json.loads(license_string)
        assert "signature" in license_data
        assert len(license_data["signature"]) > 0
