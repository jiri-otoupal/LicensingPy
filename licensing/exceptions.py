"""
Custom exceptions for the licensing system.
"""


class LicenseError(Exception):
    """Base exception for licensing errors."""
    pass


class LicenseExpiredError(LicenseError):
    """Raised when a license has expired."""
    pass


class LicenseInvalidError(LicenseError):
    """Raised when a license is invalid or corrupted."""
    pass


class HardwareMismatchError(LicenseError):
    """Raised when hardware fingerprint doesn't match."""
    pass

