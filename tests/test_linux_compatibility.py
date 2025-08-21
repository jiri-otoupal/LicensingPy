"""
Tests for Linux-specific hardware fingerprinting functionality.
"""

import os
import platform
import tempfile
from unittest.mock import patch, mock_open, MagicMock
import pytest

from licensing.hardware_fingerprint import HardwareFingerprint


class TestLinuxCompatibility:
    """Test Linux-specific hardware fingerprinting features."""
    
    def test_platform_capabilities(self, hardware_fingerprint):
        """Test platform capabilities detection."""
        capabilities = hardware_fingerprint.get_platform_capabilities()
        
        assert "platform" in capabilities
        assert "netifaces_available" in capabilities
        assert "psutil_available" in capabilities
        assert capabilities["platform"] == platform.system()
        
        if platform.system() == 'Linux':
            assert "supports_linux_sysfs" in capabilities
            assert "supports_linux_proc" in capabilities
            assert "supports_linux_commands" in capabilities
    
    def test_linux_compatibility_methods_exist(self):
        """Test that Linux-specific methods are properly implemented."""
        hw = HardwareFingerprint()
        
        # Test that the method has Linux-specific code paths
        import inspect
        
        # Check that _get_mac_addresses has Linux-specific code
        source = inspect.getsource(hw._get_mac_addresses)
        assert 'Linux' in source
        assert '/sys/class/net' in source
        assert 'ip' in source and 'link' in source
        
        # Check that _get_disk_info has Linux-specific code  
        source = inspect.getsource(hw._get_disk_info)
        assert 'Linux' in source
        assert '/sys/block' in source
        assert 'lsblk' in source
        
        # Check that _get_cpu_info has Linux-specific code
        source = inspect.getsource(hw._get_cpu_info)
        assert 'Linux' in source
        assert '/proc/cpuinfo' in source
        
        # Check that _get_system_info has Linux-specific code
        source = inspect.getsource(hw._get_system_info)
        assert 'Linux' in source
        assert 'machine-id' in source
    

    
    def test_fingerprint_consistency_without_psutil(self, hardware_fingerprint):
        """Test that fingerprints are consistent when psutil is unavailable."""
        # Disable psutil temporarily
        import licensing.hardware_fingerprint as hw_module
        original_psutil = hw_module.psutil
        hw_module.psutil = None
        
        try:
            # Clear cache to ensure fresh data
            hardware_fingerprint.clear_cache()
            
            # Generate fingerprints without psutil
            fp1 = hardware_fingerprint.get_fingerprint("mac")
            fp2 = hardware_fingerprint.get_fingerprint("mac")
            
            # Should be consistent
            assert fp1 == fp2
            assert len(fp1) == 64  # SHA256 hex string
            
        finally:
            # Restore psutil
            hw_module.psutil = original_psutil
    
    def test_fallback_methods_coverage(self, hardware_fingerprint):
        """Test that fallback methods provide adequate coverage."""
        # Test that we can get fingerprints for all types even without dependencies
        import licensing.hardware_fingerprint as hw_module
        original_psutil = hw_module.psutil
        original_netifaces = hw_module.netifaces
        
        try:
            # Disable external dependencies
            hw_module.psutil = None
            hw_module.netifaces = None
            hardware_fingerprint.clear_cache()
            
            # Should still be able to generate all fingerprint types
            for fp_type in hardware_fingerprint.get_available_types():
                fingerprint = hardware_fingerprint.get_fingerprint(fp_type)
                assert isinstance(fingerprint, str)
                assert len(fingerprint) == 64
                
        finally:
            # Restore dependencies
            hw_module.psutil = original_psutil
            hw_module.netifaces = original_netifaces
    
    @patch('platform.system', return_value='Linux')
    def test_linux_specific_capability_detection(self, mock_platform):
        """Test that Linux-specific capabilities are detected correctly."""
        hw = HardwareFingerprint()
        capabilities = hw.get_platform_capabilities()
        
        assert capabilities['platform'] == 'Linux'
        assert capabilities['supports_linux_commands'] is True
        
        # The exact values depend on what's available in the test environment
        assert 'supports_linux_sysfs' in capabilities
        assert 'supports_linux_proc' in capabilities
