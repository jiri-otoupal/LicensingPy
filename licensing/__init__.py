"""
Offline Licensing System for Python

A secure offline licensing solution using ECDSA signatures and hardware fingerprinting.
"""

from .license_manager import LicenseManager
from .license_generator import LicenseGenerator
from .preseed_generator import PreseedGenerator
from .hardware_fingerprint import HardwareFingerprint
from .exceptions import LicenseError, LicenseExpiredError, LicenseInvalidError

__version__ = "1.0.0"
__all__ = [
    "LicenseManager",
    "LicenseGenerator",
    "PreseedGenerator",
    "HardwareFingerprint",
    "LicenseError",
    "LicenseExpiredError",
    "LicenseInvalidError",
    "auto_verify_licenses"
]

def auto_verify_licenses(working_dir=None, check_hardware=True, check_expiry=True):
    """
    Convenience function to automatically find and verify all licenses in the current directory.
    
    This function searches for license files and key files in the specified directory
    (or current working directory if not specified), then verifies all licenses found.
    Each line in a license file is treated as a separate license.
    
    Args:
        working_dir: Directory to search in (defaults to current working directory)
        check_hardware: Whether to verify hardware fingerprint (default: True)
        check_expiry: Whether to check license expiry (default: True)
        
    Returns:
        Dictionary with verification results containing:
        - valid_licenses: List of valid license data
        - invalid_licenses: List of invalid license info with errors
        - license_files_found: List of license file paths found
        - key_files_found: List of key file paths found
        - summary: Dictionary with counts of total, valid, invalid, expired, hardware mismatch
        
    Example:
        >>> from licensing import auto_verify_licenses
        >>> results = auto_verify_licenses()
        >>> print(f"Found {results['summary']['valid_count']} valid licenses")
        >>> for license_data in results['valid_licenses']:
        ...     print(f"License expires: {license_data['expiry']}")
    """
    return LicenseManager.auto_verify_licenses(working_dir, check_hardware, check_expiry)

