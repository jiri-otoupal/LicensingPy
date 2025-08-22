"""
🔐 LicensingPy - Secure Offline Licensing System
================================================

A professional, secure offline licensing solution using ECDSA signatures and hardware fingerprinting.

Features:
    • 🔒 ECDSA P-256 cryptographic signatures
    • 🖥️  Hardware fingerprinting (MAC, disk, CPU, system, composite)
    • 🌱 Secure preseed-based additional authentication
    • 🎨 Beautiful Rich-powered CLI interface  
    • 🐧 Cross-platform support (Windows, Linux, macOS)
    • 📦 Zero external dependencies (with native fallbacks)
    • 🧪 Comprehensive test suite
    • 📚 Complete documentation

Basic Usage:
    >>> from licensing import LicenseGenerator, LicenseManager
    >>> 
    >>> # Generate key pair
    >>> private_key, public_key = LicenseGenerator.generate_key_pair()
    >>> 
    >>> # Generate license
    >>> generator = LicenseGenerator(private_key, "my-preseed")
    >>> license_string = generator.generate_license(
    ...     expiry_date="2025-12-31",
    ...     fingerprint_type="composite"
    ... )
    >>> 
    >>> # Verify license
    >>> manager = LicenseManager(public_key, "my-preseed")
    >>> license_data = manager.verify_license(license_string)
    >>> print(f"License expires: {license_data['expiry']}")

CLI Usage:
    $ licensingpy generate-keys --format json --output keys.json
    $ licensingpy generate-preseed --output preseed.json  # For license generation only
    $ licensingpy generate-license --private-key keys.json --preseed-file preseed.json
    $ licensingpy verify-license --public-key keys.json --preseed-file preseed.json --license license.txt
    $ licensingpy demo  # Interactive demonstration
    
Note: Preseed files are used for license generation via CLI. For production code verification, 
use hardcoded preseed strings instead of loading from files for security.

Author: LicensingPy Team
License: MIT
Homepage: https://github.com/jiri-otoupal/LicensingPy
"""

# Core imports
from .license_manager import LicenseManager
from .license_generator import LicenseGenerator
from .preseed_generator import PreseedGenerator
from .hardware_fingerprint import HardwareFingerprint
from .exceptions import LicenseError, LicenseExpiredError, LicenseInvalidError, HardwareMismatchError

# Package metadata
__version__ = "1.0.1"
__title__ = "licensingpy"
__description__ = "🔐 Secure offline licensing system with beautiful CLI, ECDSA signatures, and hardware fingerprinting"
__author__ = "LicensingPy Team"
__author_email__ = "licensing@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025 LicensingPy Team"
__url__ = "https://github.com/jiri-otoupal/LicensingPy"

# Public API
__all__ = [
    # Core classes
    "LicenseManager",
    "LicenseGenerator", 
    "PreseedGenerator",
    "HardwareFingerprint",
    
    # Exceptions
    "LicenseError",
    "LicenseExpiredError", 
    "LicenseInvalidError",
    "HardwareMismatchError",
    
    # Utility functions
    "verify_license_with_preseed",
    "auto_verify_licenses",
    
    # Package info
    "__version__",
    "__title__",
    "__description__",
    "__author__",
    "__license__",
    "__url__"
]

def verify_license_with_preseed(license_string, public_key, preseed, check_hardware=True, check_expiry=True):
    """
    Convenience function to verify a license with a hardcoded preseed string.
    
    This is the recommended approach for production applications where you want to
    ensure only licenses created with your specific preseed can be verified.
    The preseed should be hardcoded in your application, not loaded from a file.
    
    Args:
        license_string: The license string to verify
        public_key: Base64 encoded public key for verification
        preseed: Your secret preseed string (hardcoded, not from file)
        check_hardware: Whether to verify hardware fingerprint (default: True)
        check_expiry: Whether to check license expiry (default: True)
        
    Returns:
        Dictionary containing license information if valid
        
    Raises:
        LicenseInvalidError: If license is invalid or corrupted
        LicenseExpiredError: If license has expired
        HardwareMismatchError: If hardware doesn't match
        
    Example:
        >>> from licensing import verify_license_with_preseed
        >>> 
        >>> # Your application's hardcoded credentials
        >>> PUBLIC_KEY = "LS0tLS1CRUdJTi..."  # Your public key
        >>> APP_PRESEED = "my-secret-app-preseed-2024"  # Your secret preseed
        >>> 
        >>> # Verify a license
        >>> license_data = verify_license_with_preseed(
        ...     license_string=user_license,
        ...     public_key=PUBLIC_KEY,
        ...     preseed=APP_PRESEED
        ... )
        >>> print(f"License expires: {license_data['expiry']}")
    """
    manager = LicenseManager(public_key, preseed)
    return manager.verify_license(license_string, check_hardware, check_expiry)

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

