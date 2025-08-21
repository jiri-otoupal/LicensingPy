"""
License generation module.

This module handles the creation of license strings with embedded
signatures and hardware fingerprints.
"""

import base64
import json
from datetime import datetime
from typing import Dict, Optional

from .crypto_utils import CryptoManager
from .hardware_fingerprint import HardwareFingerprint
from .exceptions import LicenseError


class LicenseGenerator:
    """
    Generates licenses with ECDSA signatures and hardware binding.
    
    License format (one-line JSON with clear key-value pairs):
    {
        "version": "1.0",
        "hw_type": "mac|disk|cpu|system|composite",
        "hw_info": "actual_hardware_data_or_hash",
        "expiry": "YYYY-MM-DD",
        "issued": "YYYY-MM-DD",
        "preseed_hash": "sha256_hash",
        "component_name": "component_or_module_name",
        "signature": "base64_ecdsa_signature"
    }
    """
    
    def __init__(self, private_key_b64: str, preseed: str):
        """
        Initialize the license generator.
        
        Args:
            private_key_b64: Base64 encoded private key for signing
            preseed: Developer's preseed key for additional security
        """
        self.private_key_b64 = private_key_b64
        self.preseed = preseed
        self.crypto = CryptoManager()
        self.hw_fingerprint = HardwareFingerprint()
    
    def generate_license(self, 
                        expiry_date: str,
                        fingerprint_type: str = "composite",
                        hardware_fingerprint: Optional[str] = None,
                        additional_data: Optional[Dict] = None,
                        component_name: Optional[str] = None) -> str:
        """
        Generate a license string.
        
        Args:
            expiry_date: License expiry date in YYYY-MM-DD format
            fingerprint_type: Type of hardware fingerprint to use
            hardware_fingerprint: Pre-computed hardware fingerprint (optional)
            additional_data: Additional data to include in license (optional)
            component_name: Component/module name for additional security (optional)
            
        Returns:
            Base64 encoded license string
            
        Raises:
            LicenseError: If license generation fails
            ValueError: If parameters are invalid
        """
        try:
            # Validate expiry date
            datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("expiry_date must be in YYYY-MM-DD format")
        
        if fingerprint_type not in self.hw_fingerprint.get_available_types():
            raise ValueError(f"Invalid fingerprint_type: {fingerprint_type}")
        
        try:
            # Get hardware fingerprint if not provided
            if hardware_fingerprint is None:
                hardware_fingerprint = self.hw_fingerprint.get_fingerprint(fingerprint_type)
            
            # Create current date
            issued_date = datetime.now().strftime("%Y-%m-%d")
            
            # Use component_name or default to empty string
            comp_name = component_name or ""
            
            # Create preseed hash including component_name
            preseed_hash = self.crypto.create_preseed_hash(
                self.preseed, hardware_fingerprint, fingerprint_type, expiry_date, comp_name
            )
            
            # Get actual hardware info for clear display
            if fingerprint_type == "mac":
                hw_info_display = ",".join(self.hw_fingerprint._get_mac_addresses())
            elif fingerprint_type == "disk":
                hw_info_display = ",".join(self.hw_fingerprint._get_disk_info())
            elif fingerprint_type == "cpu":
                cpu_info = self.hw_fingerprint._get_cpu_info()
                hw_info_display = f"CPU:{cpu_info.get('processor', 'unknown')}"
            elif fingerprint_type == "system":
                sys_info = self.hw_fingerprint._get_system_info()
                hw_info_display = f"System:{sys_info.get('system', 'unknown')}-{sys_info.get('node', 'unknown')}"
            else:  # composite
                hw_info_display = hardware_fingerprint  # Use hash for composite
            
            # Create license data structure with clear field names
            license_data = {
                "version": "1.0",
                "hw_type": fingerprint_type,
                "hw_info": hw_info_display,
                "expiry": expiry_date,
                "issued": issued_date,
                "preseed_hash": preseed_hash,
                "component_name": comp_name
            }
            
            # Add additional data if provided
            if additional_data:
                license_data.update(additional_data)  # Merge additional data into main structure
            
            # Create data to sign (everything except signature)
            data_to_sign = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
            
            # Sign the data
            signature = self.crypto.sign_data(data_to_sign, self.private_key_b64)
            
            # Add signature to license data
            license_data["signature"] = signature
            
            # Return as one-line JSON (no base64 encoding)
            license_json = json.dumps(license_data, separators=(',', ':'))
            
            return license_json
            
        except Exception as e:
            raise LicenseError(f"Failed to generate license: {str(e)}")
    
    def generate_license_for_target(self,
                                   target_hardware_info: Dict,
                                   expiry_date: str,
                                   fingerprint_type: str = "composite",
                                   additional_data: Optional[Dict] = None,
                                   component_name: Optional[str] = None) -> str:
        """
        Generate a license for specific target hardware.
        
        This method allows generating licenses for different machines
        by providing the target machine's hardware information.
        
        Args:
            target_hardware_info: Hardware info from target machine
            expiry_date: License expiry date in YYYY-MM-DD format
            fingerprint_type: Type of hardware fingerprint to use
            additional_data: Additional data to include in license
            component_name: Component/module name for additional security (optional)
            
        Returns:
            Base64 encoded license string
        """
        # Create hardware fingerprint from target info
        import hashlib
        fingerprint_data = str(target_hardware_info)
        hardware_fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        return self.generate_license(
            expiry_date=expiry_date,
            fingerprint_type=fingerprint_type,
            hardware_fingerprint=hardware_fingerprint,
            additional_data=additional_data,
            component_name=component_name
        )
    
    def get_hardware_info(self, fingerprint_type: str = "composite") -> Dict:
        """
        Get current machine's hardware information.
        
        This can be used to collect hardware info from a target machine
        for license generation.
        
        Args:
            fingerprint_type: Type of hardware fingerprint
            
        Returns:
            Dictionary containing hardware information
        """
        if fingerprint_type == "mac":
            return {"mac_addresses": self.hw_fingerprint._get_mac_addresses()}
        elif fingerprint_type == "disk":
            return {"disk_info": self.hw_fingerprint._get_disk_info()}
        elif fingerprint_type == "cpu":
            return {"cpu_info": self.hw_fingerprint._get_cpu_info()}
        elif fingerprint_type == "system":
            return {"system_info": self.hw_fingerprint._get_system_info()}
        elif fingerprint_type == "composite":
            return self.hw_fingerprint._get_composite_info()
        else:
            raise ValueError(f"Invalid fingerprint_type: {fingerprint_type}")
    
    @staticmethod
    def generate_key_pair() -> tuple[str, str]:
        """
        Generate a new ECDSA key pair for license signing.
        
        Returns:
            Tuple of (private_key_b64, public_key_b64)
        """
        crypto = CryptoManager()
        return crypto.generate_key_pair()
    
    def parse_license(self, license_string: str) -> Dict:
        """
        Parse a license string and return its components.
        
        Args:
            license_string: JSON license string
            
        Returns:
            Dictionary containing license data
            
        Raises:
            LicenseError: If license cannot be parsed
        """
        try:
            # Parse JSON directly (no base64 decoding needed)
            license_data = json.loads(license_string)
            
            return license_data
            
        except Exception as e:
            raise LicenseError(f"Failed to parse license: {str(e)}")
