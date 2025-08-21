"""
License verification and management module.

This module handles license validation, expiry checking, and hardware verification.
"""

import json
import base64
import os
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple

from .crypto_utils import CryptoManager
from .hardware_fingerprint import HardwareFingerprint
from .exceptions import (
    LicenseError, 
    LicenseExpiredError, 
    LicenseInvalidError, 
    HardwareMismatchError
)


class LicenseManager:
    """
    Manages license verification and validation.
    
    This class provides methods to verify license authenticity,
    check expiration, and validate hardware binding.
    """
    
    def __init__(self, public_key_b64: str, preseed: str):
        """
        Initialize the license manager.
        
        Args:
            public_key_b64: Base64 encoded public key for verification
            preseed: Developer's preseed key (must match generator's preseed)
        """
        self.public_key_b64 = public_key_b64
        self.preseed = preseed
        self.crypto = CryptoManager()
        self.hw_fingerprint = HardwareFingerprint()
    
    def verify_license(self, 
                      license_string: str,
                      check_hardware: bool = True,
                      check_expiry: bool = True) -> Dict:
        """
        Verify a license string completely.
        
        Args:
            license_string: JSON license string
            check_hardware: Whether to verify hardware fingerprint
            check_expiry: Whether to check license expiry
            
        Returns:
            Dictionary containing license information if valid
            
        Raises:
            LicenseInvalidError: If license is invalid or corrupted
            LicenseExpiredError: If license has expired
            HardwareMismatchError: If hardware doesn't match
        """
        # Parse the license
        license_data = self._parse_license(license_string)
        
        # Verify signature
        if not self._verify_signature(license_data):
            raise LicenseInvalidError("License signature is invalid")
        
        # Verify preseed hash
        if not self._verify_preseed_hash(license_data):
            raise LicenseInvalidError("License preseed hash is invalid")
        
        # Check expiry if requested
        if check_expiry and self._is_expired(license_data):
            raise LicenseExpiredError(f"License expired on {license_data['expiry']}")
        
        # Check hardware if requested
        if check_hardware and not self._verify_hardware(license_data):
            raise HardwareMismatchError("Hardware fingerprint does not match")
        
        return license_data
    
    def is_valid(self, 
                license_string: str,
                check_hardware: bool = True,
                check_expiry: bool = True) -> bool:
        """
        Check if a license is valid without raising exceptions.
        
        Args:
            license_string: JSON license string
            check_hardware: Whether to verify hardware fingerprint
            check_expiry: Whether to check license expiry
            
        Returns:
            True if license is valid, False otherwise
        """
        try:
            self.verify_license(license_string, check_hardware, check_expiry)
            return True
        except Exception:
            return False
    
    def get_license_info(self, license_string: str) -> Dict:
        """
        Get license information without full validation.
        
        This method only verifies the license structure and signature,
        but does not check expiry or hardware binding.
        
        Args:
            license_string: JSON license string
            
        Returns:
            Dictionary containing license information
            
        Raises:
            LicenseInvalidError: If license structure or signature is invalid
        """
        license_data = self._parse_license(license_string)
        
        if not self._verify_signature(license_data):
            raise LicenseInvalidError("License signature is invalid")
        
        # Add status information
        license_data["status"] = {
            "is_expired": self._is_expired(license_data),
            "hardware_matches": self._verify_hardware(license_data),
            "preseed_valid": self._verify_preseed_hash(license_data)
        }
        
        return license_data
    
    def _parse_license(self, license_string: str) -> Dict:
        """Parse and validate license structure."""
        try:
            # Parse JSON directly (no base64 decoding needed)
            license_data = json.loads(license_string)
            
            # Validate required fields with new field names
            required_fields = [
                "version", "hw_type", "hw_info",
                "expiry", "issued", "preseed_hash", "signature", "component_name"
            ]
            
            for field in required_fields:
                if field not in license_data:
                    raise LicenseInvalidError(f"Missing required field: {field}")
            
            # Validate version
            if license_data["version"] != "1.0":
                raise LicenseInvalidError(f"Unsupported license version: {license_data['version']}")
            
            # Validate dates
            try:
                datetime.strptime(license_data["expiry"], "%Y-%m-%d")
                datetime.strptime(license_data["issued"], "%Y-%m-%d")
            except ValueError:
                raise LicenseInvalidError("Invalid date format in license")
            
            return license_data
            
        except json.JSONDecodeError:
            raise LicenseInvalidError("License is not valid JSON")
        except Exception as e:
            if isinstance(e, LicenseError):
                raise
            raise LicenseInvalidError(f"Failed to parse license: {str(e)}")
    
    def _verify_signature(self, license_data: Dict) -> bool:
        """Verify the ECDSA signature of the license."""
        try:
            # Create data that was signed (everything except signature)
            signature = license_data.pop("signature")
            data_to_verify = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
            
            # Verify signature
            is_valid = self.crypto.verify_signature(
                data_to_verify, signature, self.public_key_b64
            )
            
            # Restore signature to license data
            license_data["signature"] = signature
            
            return is_valid
            
        except Exception:
            return False
    
    def _verify_preseed_hash(self, license_data: Dict) -> bool:
        """Verify the preseed hash in the license."""
        try:
            # For the new format, we need to reconstruct the hardware fingerprint hash
            # from the actual hardware info if it's not composite
            hw_type = license_data["hw_type"]
            if hw_type == "composite":
                hardware_fingerprint = license_data["hw_info"]
            else:
                # Generate hash from current hardware for verification
                hardware_fingerprint = self.hw_fingerprint.get_fingerprint(hw_type)
            
            expected_hash = self.crypto.create_preseed_hash(
                self.preseed,
                hardware_fingerprint,
                hw_type,
                license_data["expiry"],
                license_data.get("component_name", "")
            )
            
            return expected_hash == license_data["preseed_hash"]
            
        except Exception:
            return False
    
    def _is_expired(self, license_data: Dict) -> bool:
        """Check if the license has expired."""
        try:
            expiry_date = datetime.strptime(license_data["expiry"], "%Y-%m-%d").date()
            current_date = datetime.now().date()
            
            return current_date > expiry_date
            
        except Exception:
            return True  # If we can't parse date, consider it expired
    
    def _verify_hardware(self, license_data: Dict) -> bool:
        """Verify that current hardware matches license."""
        try:
            hw_type = license_data["hw_type"]
            expected_hw_info = license_data["hw_info"]
            
            # Get current hardware info
            if hw_type == "mac":
                current_hw_info = ",".join(self.hw_fingerprint._get_mac_addresses())
            elif hw_type == "disk":
                current_hw_info = ",".join(self.hw_fingerprint._get_disk_info())
            elif hw_type == "cpu":
                cpu_info = self.hw_fingerprint._get_cpu_info()
                current_hw_info = f"CPU:{cpu_info.get('processor', 'unknown')}"
            elif hw_type == "system":
                sys_info = self.hw_fingerprint._get_system_info()
                current_hw_info = f"System:{sys_info.get('system', 'unknown')}-{sys_info.get('node', 'unknown')}"
            else:  # composite
                # For composite, compare hash
                current_hw_info = self.hw_fingerprint.get_fingerprint(hw_type)
            
            return current_hw_info == expected_hw_info
            
        except Exception:
            return False
    
    def get_days_until_expiry(self, license_string: str) -> Optional[int]:
        """
        Get number of days until license expires.
        
        Args:
            license_string: JSON license string
            
        Returns:
            Number of days until expiry, None if license is invalid,
            negative number if already expired
        """
        try:
            license_data = self._parse_license(license_string)
            
            expiry_date = datetime.strptime(license_data["expiry"], "%Y-%m-%d").date()
            current_date = datetime.now().date()
            
            delta = expiry_date - current_date
            return delta.days
            
        except Exception:
            return None
    
    def get_hardware_fingerprint(self, fingerprint_type: str = "composite") -> str:
        """
        Get current machine's hardware fingerprint.
        
        Args:
            fingerprint_type: Type of fingerprint to generate
            
        Returns:
            Hardware fingerprint hash
        """
        return self.hw_fingerprint.get_fingerprint(fingerprint_type)

    @classmethod
    def auto_verify_licenses(cls, 
                           working_dir: Optional[str] = None,
                           check_hardware: bool = True,
                           check_expiry: bool = True) -> Dict[str, List[Dict]]:
        """
        Automatically find and verify all licenses in the current working directory.
        
        This function searches for license files and key files in the specified directory
        (or current working directory if not specified), then verifies all licenses found.
        
        Args:
            working_dir: Directory to search in (defaults to current working directory)
            check_hardware: Whether to verify hardware fingerprint
            check_expiry: Whether to check license expiry
            
        Returns:
            Dictionary with results:
            {
                "valid_licenses": [list of valid license data],
                "invalid_licenses": [list of invalid license info with errors],
                "license_files_found": [list of license file paths],
                "key_files_found": [list of key file paths],
                "summary": {
                    "total_licenses": int,
                    "valid_count": int,
                    "invalid_count": int,
                    "expired_count": int,
                    "hardware_mismatch_count": int
                }
            }
        """
        if working_dir is None:
            working_dir = os.getcwd()
        
        working_dir = Path(working_dir)
        
        # Find license files (common patterns)
        license_patterns = [
            "license.txt", "license.json", "*.license", 
            "licenses.txt", "licenses.json", "license_*"
        ]
        
        license_files = []
        for pattern in license_patterns:
            license_files.extend(glob.glob(str(working_dir / pattern)))
        
        # Find key files
        key_patterns = [
            "keys.json", "public_key.txt", "*.pub", 
            "key.json", "*key*"
        ]
        
        key_files = []
        for pattern in key_patterns:
            key_files.extend(glob.glob(str(working_dir / pattern)))
        
        # Remove duplicates, filter out result files, and sort  
        license_files = sorted(list(set(license_files)))
        license_files = [f for f in license_files if not f.endswith('_results.json') and not f.endswith('_verification.json')]
        key_files = sorted(list(set(key_files)))
        
        results = {
            "valid_licenses": [],
            "invalid_licenses": [],
            "license_files_found": license_files,
            "key_files_found": key_files,
            "summary": {
                "total_licenses": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "expired_count": 0,
                "hardware_mismatch_count": 0
            }
        }
        
        if not license_files:
            results["error"] = "No license files found in the working directory"
            return results
        
        if not key_files:
            results["error"] = "No key files found in the working directory"
            return results
        
        # Try to load keys and preseed
        public_key_b64 = None
        preseed = None
        
        for key_file in key_files:
            try:
                with open(key_file, 'r') as f:
                    content = f.read().strip()
                    
                    # Try to parse as JSON first
                    try:
                        key_data = json.loads(content)
                        if 'public_key' in key_data:
                            public_key_b64 = key_data['public_key']
                        if 'preseed' in key_data:
                            preseed = key_data['preseed']
                    except json.JSONDecodeError:
                        # Try as plain text public key
                        if content.startswith('LS0tLS1CRUdJTiBQVUJMSUM') or 'PUBLIC KEY' in content:
                            public_key_b64 = content
                
                # Break if we found both
                if public_key_b64 and preseed:
                    break
                    
            except Exception:
                continue
        
        # If we still don't have preseed, use a default or look for it in environment
        if not preseed:
            preseed = os.environ.get('LICENSE_PRESEED', 'my-secret-preseed-2024')
        
        if not public_key_b64:
            results["error"] = "Could not find valid public key in any key file"
            return results
        
        # Create license manager
        try:
            license_manager = cls(public_key_b64, preseed)
        except Exception as e:
            results["error"] = f"Failed to initialize license manager: {str(e)}"
            return results
        
        # Process each license file
        for license_file in license_files:
            try:
                with open(license_file, 'r') as f:
                    content = f.read().strip()
                    
                    # Split by lines to handle multiple licenses per file
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    
                    for line_num, line in enumerate(lines, 1):
                        results["summary"]["total_licenses"] += 1
                        
                        try:
                            # Try to verify the license
                            license_data = license_manager.verify_license(
                                line, 
                                check_hardware=check_hardware,
                                check_expiry=check_expiry
                            )
                            
                            # Add metadata
                            license_data["_metadata"] = {
                                "file": license_file,
                                "line_number": line_num,
                                "verification_time": datetime.now().isoformat()
                            }
                            
                            results["valid_licenses"].append(license_data)
                            results["summary"]["valid_count"] += 1
                            
                        except LicenseExpiredError as e:
                            results["invalid_licenses"].append({
                                "file": license_file,
                                "line_number": line_num,
                                "license_string": line,
                                "error_type": "expired",
                                "error_message": str(e),
                                "verification_time": datetime.now().isoformat()
                            })
                            results["summary"]["invalid_count"] += 1
                            results["summary"]["expired_count"] += 1
                            
                        except HardwareMismatchError as e:
                            results["invalid_licenses"].append({
                                "file": license_file,
                                "line_number": line_num,
                                "license_string": line,
                                "error_type": "hardware_mismatch",
                                "error_message": str(e),
                                "verification_time": datetime.now().isoformat()
                            })
                            results["summary"]["invalid_count"] += 1
                            results["summary"]["hardware_mismatch_count"] += 1
                            
                        except LicenseInvalidError as e:
                            results["invalid_licenses"].append({
                                "file": license_file,
                                "line_number": line_num,
                                "license_string": line,
                                "error_type": "invalid",
                                "error_message": str(e),
                                "verification_time": datetime.now().isoformat()
                            })
                            results["summary"]["invalid_count"] += 1
                            
                        except Exception as e:
                            results["invalid_licenses"].append({
                                "file": license_file,
                                "line_number": line_num,
                                "license_string": line,
                                "error_type": "unknown",
                                "error_message": str(e),
                                "verification_time": datetime.now().isoformat()
                            })
                            results["summary"]["invalid_count"] += 1
                            
            except Exception as e:
                results["invalid_licenses"].append({
                    "file": license_file,
                    "line_number": None,
                    "license_string": None,
                    "error_type": "file_error",
                    "error_message": f"Could not read file: {str(e)}",
                    "verification_time": datetime.now().isoformat()
                })
        
        return results
