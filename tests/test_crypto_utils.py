"""
Tests for the crypto_utils module.
"""

import base64
import pytest
from licensing.crypto_utils import CryptoManager
from licensing.exceptions import LicenseError


class TestCryptoManager:
    """Test the CryptoManager class."""
    
    def test_init(self, crypto_manager):
        """Test CryptoManager initialization."""
        assert crypto_manager.curve == 'P-256'
    
    def test_generate_key_pair(self, crypto_manager):
        """Test key pair generation."""
        private_key, public_key = crypto_manager.generate_key_pair()
        
        # Check that keys are base64 encoded strings
        assert isinstance(private_key, str)
        assert isinstance(public_key, str)
        
        # Check that they can be base64 decoded
        private_decoded = base64.b64decode(private_key)
        public_decoded = base64.b64decode(public_key)
        
        # Check PEM headers
        assert b'BEGIN PRIVATE KEY' in private_decoded
        assert b'BEGIN PUBLIC KEY' in public_decoded
    
    def test_load_private_key(self, crypto_manager, key_pair):
        """Test loading private key from base64."""
        private_key_obj = crypto_manager.load_private_key(key_pair['private_key'])
        
        # Check that we get an ECC key object
        assert hasattr(private_key_obj, 'curve')
        assert private_key_obj.curve == 'NIST P-256'
    
    def test_load_public_key(self, crypto_manager, key_pair):
        """Test loading public key from base64."""
        public_key_obj = crypto_manager.load_public_key(key_pair['public_key'])
        
        # Check that we get an ECC key object
        assert hasattr(public_key_obj, 'curve')
        assert public_key_obj.curve == 'NIST P-256'
    
    def test_sign_and_verify_data(self, crypto_manager, key_pair):
        """Test data signing and verification."""
        test_data = "This is test data for signing"
        
        # Sign the data
        signature = crypto_manager.sign_data(test_data, key_pair['private_key'])
        
        # Verify signature
        is_valid = crypto_manager.verify_signature(
            test_data, signature, key_pair['public_key']
        )
        
        assert is_valid is True
    
    def test_sign_and_verify_bytes(self, crypto_manager, key_pair):
        """Test signing and verifying byte data."""
        test_data = b"This is test byte data"
        
        # Sign the data
        signature = crypto_manager.sign_data(test_data, key_pair['private_key'])
        
        # Verify signature
        is_valid = crypto_manager.verify_signature(
            test_data, signature, key_pair['public_key']
        )
        
        assert is_valid is True
    
    def test_invalid_signature(self, crypto_manager, key_pair):
        """Test verification with invalid signature."""
        test_data = "This is test data"
        
        # Sign the data
        signature = crypto_manager.sign_data(test_data, key_pair['private_key'])
        
        # Verify with wrong data
        is_valid = crypto_manager.verify_signature(
            "Different data", signature, key_pair['public_key']
        )
        
        assert is_valid is False
    
    def test_wrong_key_signature(self, crypto_manager):
        """Test verification with wrong public key."""
        # Generate two key pairs
        private_key1, public_key1 = crypto_manager.generate_key_pair()
        private_key2, public_key2 = crypto_manager.generate_key_pair()
        
        test_data = "Test data"
        
        # Sign with first key
        signature = crypto_manager.sign_data(test_data, private_key1)
        
        # Try to verify with second public key
        is_valid = crypto_manager.verify_signature(test_data, signature, public_key2)
        
        assert is_valid is False
    
    def test_hash_data_string(self, crypto_manager):
        """Test hashing string data."""
        test_data = "test string"
        hash_result = crypto_manager.hash_data(test_data)
        
        # Should be a hex string
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 hex length
        
        # Same data should produce same hash
        hash_result2 = crypto_manager.hash_data(test_data)
        assert hash_result == hash_result2
    
    def test_hash_data_bytes(self, crypto_manager):
        """Test hashing byte data."""
        test_data = b"test bytes"
        hash_result = crypto_manager.hash_data(test_data)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
    
    def test_create_preseed_hash(self, crypto_manager):
        """Test preseed hash creation."""
        preseed = "test-preseed"
        hw_fingerprint = "test-hardware-fingerprint"
        fingerprint_type = "mac"
        expiry = "2025-12-31"
        component_name = "TestComponent"
        
        hash_result = crypto_manager.create_preseed_hash(
            preseed, hw_fingerprint, fingerprint_type, expiry, component_name
        )
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        
        # Same inputs should produce same hash
        hash_result2 = crypto_manager.create_preseed_hash(
            preseed, hw_fingerprint, fingerprint_type, expiry, component_name
        )
        assert hash_result == hash_result2
        
        # Different component name should produce different hash
        hash_result3 = crypto_manager.create_preseed_hash(
            preseed, hw_fingerprint, fingerprint_type, expiry, "DifferentComponent"
        )
        assert hash_result != hash_result3
    
    def test_create_preseed_hash_without_component(self, crypto_manager):
        """Test preseed hash creation without component name."""
        preseed = "test-preseed"
        hw_fingerprint = "test-hardware-fingerprint"
        fingerprint_type = "mac"
        expiry = "2025-12-31"
        
        hash_result = crypto_manager.create_preseed_hash(
            preseed, hw_fingerprint, fingerprint_type, expiry
        )
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
    
    def test_invalid_private_key(self, crypto_manager):
        """Test loading invalid private key."""
        with pytest.raises(Exception):
            crypto_manager.load_private_key("invalid_base64_key")
    
    def test_invalid_public_key(self, crypto_manager):
        """Test loading invalid public key."""
        with pytest.raises(Exception):
            crypto_manager.load_public_key("invalid_base64_key")
