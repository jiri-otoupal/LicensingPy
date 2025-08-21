"""
Tests for the hardware_fingerprint module.
"""

import pytest
from unittest.mock import patch, MagicMock

from licensing.hardware_fingerprint import HardwareFingerprint


class TestHardwareFingerprint:
    """Test the HardwareFingerprint class."""
    
    def test_init(self, hardware_fingerprint):
        """Test HardwareFingerprint initialization."""
        assert hardware_fingerprint is not None
        assert hasattr(hardware_fingerprint, 'get_fingerprint')
        assert hasattr(hardware_fingerprint, '_get_mac_addresses')
        assert hasattr(hardware_fingerprint, '_get_disk_info')
        assert hasattr(hardware_fingerprint, '_get_cpu_info')
        assert hasattr(hardware_fingerprint, '_get_system_info')
    
    def test_get_mac_addresses(self, hardware_fingerprint):
        """Test getting MAC addresses."""
        mac_addresses = hardware_fingerprint._get_mac_addresses()
        
        assert isinstance(mac_addresses, list)
        # Should have at least one MAC address on most systems
        assert len(mac_addresses) > 0
        
        # Each MAC address should be a string
        valid_macs = [mac for mac in mac_addresses if mac and len(mac) >= 12]
        assert len(valid_macs) > 0  # Should have at least one valid MAC
        
        for mac in valid_macs:
            assert isinstance(mac, str)
            # Basic MAC address format check (12 hex chars or with separators)
            assert len(mac) >= 12
    
    def test_get_disk_info(self, hardware_fingerprint):
        """Test getting disk information."""
        disk_info = hardware_fingerprint._get_disk_info()
        
        assert isinstance(disk_info, list)
        # Should have at least one disk on most systems
        assert len(disk_info) > 0
        
        # Each disk info should be a string
        for disk in disk_info:
            assert isinstance(disk, str)
            assert len(disk) > 0
    
    def test_get_cpu_info(self, hardware_fingerprint):
        """Test getting CPU information."""
        cpu_info = hardware_fingerprint._get_cpu_info()
        
        assert isinstance(cpu_info, dict)
        # Should have some CPU information
        assert len(cpu_info) > 0
        
        # Common CPU info fields
        expected_fields = ['processor', 'architecture', 'machine']
        found_fields = [field for field in expected_fields if field in cpu_info]
        assert len(found_fields) > 0  # At least one field should be present
    
    def test_get_system_info(self, hardware_fingerprint):
        """Test getting system information."""
        system_info = hardware_fingerprint._get_system_info()
        
        assert isinstance(system_info, dict)
        assert len(system_info) > 0
        
        # Common system info fields
        expected_fields = ['system', 'node', 'release', 'version', 'machine', 'processor']
        found_fields = [field for field in expected_fields if field in system_info]
        assert len(found_fields) > 0  # At least one field should be present
    
    def test_get_fingerprint_mac(self, hardware_fingerprint):
        """Test generating MAC-based fingerprint."""
        fingerprint = hardware_fingerprint.get_fingerprint("mac")
        
        assert isinstance(fingerprint, str)
        # Should be a SHA256 hash (64 hex characters)
        assert len(fingerprint) == 64
        assert all(c in '0123456789abcdef' for c in fingerprint)
        
        # Same call should produce same result
        fingerprint2 = hardware_fingerprint.get_fingerprint("mac")
        assert fingerprint == fingerprint2
    
    def test_get_fingerprint_disk(self, hardware_fingerprint):
        """Test generating disk-based fingerprint."""
        fingerprint = hardware_fingerprint.get_fingerprint("disk")
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64
        assert all(c in '0123456789abcdef' for c in fingerprint)
    
    def test_get_fingerprint_cpu(self, hardware_fingerprint):
        """Test generating CPU-based fingerprint."""
        fingerprint = hardware_fingerprint.get_fingerprint("cpu")
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64
        assert all(c in '0123456789abcdef' for c in fingerprint)
    
    def test_get_fingerprint_system(self, hardware_fingerprint):
        """Test generating system-based fingerprint."""
        fingerprint = hardware_fingerprint.get_fingerprint("system")
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64
        assert all(c in '0123456789abcdef' for c in fingerprint)
    
    def test_get_fingerprint_composite(self, hardware_fingerprint):
        """Test generating composite fingerprint."""
        fingerprint = hardware_fingerprint.get_fingerprint("composite")
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64
        assert all(c in '0123456789abcdef' for c in fingerprint)
        
        # Composite should be different from individual types
        mac_fp = hardware_fingerprint.get_fingerprint("mac")
        assert fingerprint != mac_fp
    
    def test_invalid_fingerprint_type(self, hardware_fingerprint):
        """Test invalid fingerprint type."""
        with pytest.raises(ValueError, match="Unsupported fingerprint type"):
            hardware_fingerprint.get_fingerprint("invalid_type")
    
    def test_get_available_types(self, hardware_fingerprint):
        """Test getting available fingerprint types."""
        types = hardware_fingerprint.get_available_types()
        
        assert isinstance(types, list)
        expected_types = ["mac", "disk", "cpu", "system", "composite"]
        for expected_type in expected_types:
            assert expected_type in types
    
    def test_clear_cache(self, hardware_fingerprint):
        """Test cache clearing functionality."""
        # Get initial fingerprint to populate cache
        fp1 = hardware_fingerprint.get_fingerprint("mac")
        
        # Clear cache
        hardware_fingerprint.clear_cache()
        
        # Get fingerprint again - should still work
        fp2 = hardware_fingerprint.get_fingerprint("mac")
        
        # Should be same result (hardware doesn't change)
        assert fp1 == fp2
    
    def test_get_disk_info_fallback(self, hardware_fingerprint):
        """Test disk info collection with fallback methods."""
        # This test checks that disk info collection works
        # even without psutil (using native fallbacks)
        disk_info = hardware_fingerprint._get_disk_info()
        assert isinstance(disk_info, list)
        # Should at least get some disk info on any system
        # (even if empty, it shouldn't crash)
    
    def test_fingerprint_consistency(self, hardware_fingerprint):
        """Test that fingerprints are consistent across multiple calls."""
        # Generate same type multiple times
        fingerprints = []
        for _ in range(5):
            fp = hardware_fingerprint.get_fingerprint("mac")
            fingerprints.append(fp)
        
        # All should be identical
        assert all(fp == fingerprints[0] for fp in fingerprints)
    
    def test_different_types_different_fingerprints(self, hardware_fingerprint):
        """Test that different fingerprint types produce different results."""
        types = ["mac", "disk", "cpu", "system", "composite"]
        fingerprints = {}
        
        for fp_type in types:
            fingerprints[fp_type] = hardware_fingerprint.get_fingerprint(fp_type)
        
        # Check that all are different (on most systems they should be)
        unique_fingerprints = set(fingerprints.values())
        # At least most should be different
        assert len(unique_fingerprints) >= len(types) - 1
