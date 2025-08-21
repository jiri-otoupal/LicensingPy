"""
Cryptographic utilities for the licensing system.

This module handles ECDSA key generation, signing, and verification
using the pycryptodome library.
"""

import base64
import hashlib
from typing import Tuple, Union

from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256


class CryptoManager:
    """
    Manages cryptographic operations for the licensing system.
    
    Uses ECDSA with P-256 curve for digital signatures.
    """
    
    def __init__(self):
        self.curve = 'P-256'  # NIST P-256 curve (secp256r1)
    
    def generate_key_pair(self) -> Tuple[str, str]:
        """
        Generate a new ECDSA key pair.
        
        Returns:
            Tuple of (private_key_pem, public_key_pem) as base64 encoded strings
        """
        # Generate private key
        private_key = ECC.generate(curve=self.curve)
        public_key = private_key.public_key()
        
        # Export keys in PEM format
        private_pem = private_key.export_key(format='PEM')
        public_pem = public_key.export_key(format='PEM')
        
        # Encode to base64 for easier storage/transmission
        private_b64 = base64.b64encode(private_pem.encode()).decode()
        public_b64 = base64.b64encode(public_pem.encode()).decode()
        
        return private_b64, public_b64
    
    def load_private_key(self, private_key_b64: str) -> ECC.EccKey:
        """
        Load a private key from base64 encoded PEM.
        
        Args:
            private_key_b64: Base64 encoded private key in PEM format
            
        Returns:
            ECC private key object
        """
        private_pem = base64.b64decode(private_key_b64).decode()
        return ECC.import_key(private_pem)
    
    def load_public_key(self, public_key_b64: str) -> ECC.EccKey:
        """
        Load a public key from base64 encoded PEM.
        
        Args:
            public_key_b64: Base64 encoded public key in PEM format
            
        Returns:
            ECC public key object
        """
        public_pem = base64.b64decode(public_key_b64).decode()
        return ECC.import_key(public_pem)
    
    def sign_data(self, data: Union[str, bytes], private_key_b64: str) -> str:
        """
        Sign data using ECDSA with SHA256.
        
        Args:
            data: Data to sign (string or bytes)
            private_key_b64: Base64 encoded private key
            
        Returns:
            Base64 encoded signature
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Load private key
        private_key = self.load_private_key(private_key_b64)
        
        # Create hash of data
        hash_obj = SHA256.new(data)
        
        # Sign the hash
        signer = DSS.new(private_key, 'fips-186-3')
        signature = signer.sign(hash_obj)
        
        # Return base64 encoded signature
        return base64.b64encode(signature).decode()
    
    def verify_signature(self, data: Union[str, bytes], signature_b64: str, 
                        public_key_b64: str) -> bool:
        """
        Verify an ECDSA signature.
        
        Args:
            data: Original data that was signed
            signature_b64: Base64 encoded signature
            public_key_b64: Base64 encoded public key
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Load public key
            public_key = self.load_public_key(public_key_b64)
            
            # Decode signature
            signature = base64.b64decode(signature_b64)
            
            # Create hash of data
            hash_obj = SHA256.new(data)
            
            # Verify signature
            verifier = DSS.new(public_key, 'fips-186-3')
            verifier.verify(hash_obj, signature)
            
            return True
        except Exception:
            return False
    
    def hash_data(self, data: Union[str, bytes]) -> str:
        """
        Create SHA256 hash of data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hex string of the hash
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()
    
    def create_preseed_hash(self, preseed: str, hardware_fingerprint: str, 
                           fingerprint_type: str, expiry_date: str, component_name: str = "") -> str:
        """
        Create a deterministic hash from preseed and license components.
        
        Args:
            preseed: Developer's preseed key
            hardware_fingerprint: Hardware fingerprint
            fingerprint_type: Type of fingerprint used
            expiry_date: License expiry date (ISO format)
            component_name: Component/module name for additional security
            
        Returns:
            SHA256 hash of combined data
        """
        combined_data = f"{preseed}:{hardware_fingerprint}:{fingerprint_type}:{expiry_date}:{component_name}"
        return self.hash_data(combined_data)

