"""
Tests for the preseed_generator module.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from licensing.preseed_generator import PreseedGenerator


class TestPreseedGenerator:
    """Test the PreseedGenerator class."""
    
    def test_generate_preseed_default_length(self):
        """Test preseed generation with default length."""
        preseed = PreseedGenerator.generate_preseed()
        
        # Should be URL-safe base64 encoded, roughly 64 chars for 64 bytes
        assert isinstance(preseed, str)
        assert len(preseed) >= 60  # Account for base64 padding variations
    
    def test_generate_preseed_custom_length(self):
        """Test preseed generation with custom length."""
        length = 32
        preseed = PreseedGenerator.generate_preseed(length)
        
        assert isinstance(preseed, str)
        assert len(preseed) >= 30  # Account for base64 encoding
    
    def test_create_preseed_file(self, temp_dir):
        """Test creating a preseed file."""
        output_path = temp_dir / "test_preseed.json"
        metadata = {"project": "Test", "description": "Test preseed"}
        
        secret_content = PreseedGenerator.create_preseed_file(
            output_path=str(output_path),
            metadata=metadata,
            length=64
        )
        
        # Check that file was created
        assert output_path.exists()
        
        # Check file contents
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "secret_content" in data
        assert "generated_at" in data
        assert "length" in data
        assert "format_version" in data
        assert "metadata" in data
        
        assert data["secret_content"] == secret_content
        assert data["length"] == 64
        assert data["format_version"] == "1.0"
        assert data["metadata"] == metadata
    
    def test_create_preseed_file_no_metadata(self, temp_dir):
        """Test creating preseed file without metadata."""
        output_path = temp_dir / "test_preseed_no_meta.json"
        
        secret_content = PreseedGenerator.create_preseed_file(
            output_path=str(output_path),
            length=32
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "metadata" not in data
        assert data["length"] == 32
    
    def test_load_preseed_from_file(self, temp_dir):
        """Test loading preseed from file."""
        output_path = temp_dir / "test_preseed.json"
        metadata = {"project": "Test"}
        
        # Create preseed file
        secret_content = PreseedGenerator.create_preseed_file(
            output_path=str(output_path),
            metadata=metadata,
            length=64
        )
        
        # Load preseed hash
        preseed_hash = PreseedGenerator.load_preseed_from_file(str(output_path))
        
        # Should be a hash (64 char hex string)
        assert isinstance(preseed_hash, str)
        assert len(preseed_hash) == 64
        assert all(c in '0123456789abcdef' for c in preseed_hash)
        
        # Loading same file should give same hash
        preseed_hash2 = PreseedGenerator.load_preseed_from_file(str(output_path))
        assert preseed_hash == preseed_hash2
    
    def test_load_preseed_different_metadata_different_hash(self, temp_dir):
        """Test that different metadata produces different hashes."""
        # Create two files with same secret but different metadata
        path1 = temp_dir / "preseed1.json"
        path2 = temp_dir / "preseed2.json"
        
        # Manually create files with same secret but different metadata
        secret = "same_secret_content_for_both"
        
        data1 = {
            "secret_content": secret,
            "generated_at": "2025-01-01T00:00:00",
            "length": 64,
            "format_version": "1.0",
            "metadata": {"project": "Project1"}
        }
        
        data2 = {
            "secret_content": secret,
            "generated_at": "2025-01-01T00:00:00", 
            "length": 64,
            "format_version": "1.0",
            "metadata": {"project": "Project2"}
        }
        
        with open(path1, 'w') as f:
            json.dump(data1, f)
        
        with open(path2, 'w') as f:
            json.dump(data2, f)
        
        hash1 = PreseedGenerator.load_preseed_from_file(str(path1))
        hash2 = PreseedGenerator.load_preseed_from_file(str(path2))
        
        # Different metadata should produce different hashes
        assert hash1 != hash2
    
    def test_validate_preseed_file(self, temp_dir):
        """Test preseed file validation."""
        output_path = temp_dir / "test_preseed.json"
        metadata = {"project": "Test", "version": "1.0"}
        
        PreseedGenerator.create_preseed_file(
            output_path=str(output_path),
            metadata=metadata,
            length=64
        )
        
        info = PreseedGenerator.validate_preseed_file(str(output_path))
        
        assert "file_path" in info
        assert "generated_at" in info
        assert "length" in info
        assert "format_version" in info
        assert "has_metadata" in info
        assert "file_size" in info
        assert "metadata" in info
        
        assert info["length"] == 64
        assert info["format_version"] == "1.0"
        assert info["has_metadata"] is True
        assert info["metadata"] == metadata
        assert info["file_size"] > 0
    
    def test_validate_preseed_file_no_metadata(self, temp_dir):
        """Test validation of preseed file without metadata."""
        output_path = temp_dir / "test_preseed.json"
        
        PreseedGenerator.create_preseed_file(
            output_path=str(output_path),
            length=32
        )
        
        info = PreseedGenerator.validate_preseed_file(str(output_path))
        
        assert info["has_metadata"] is False
        assert "metadata" not in info
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            PreseedGenerator.load_preseed_from_file("nonexistent_file.json")
    
    def test_validate_nonexistent_file(self):
        """Test validating nonexistent file."""
        with pytest.raises(FileNotFoundError):
            PreseedGenerator.validate_preseed_file("nonexistent_file.json")
    
    def test_load_invalid_json_file(self, temp_dir):
        """Test loading invalid JSON file."""
        invalid_file = temp_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            PreseedGenerator.load_preseed_from_file(str(invalid_file))
    
    def test_load_missing_secret_content(self, temp_dir):
        """Test loading file missing secret_content field."""
        invalid_file = temp_dir / "missing_secret.json"
        data = {
            "generated_at": "2025-01-01T00:00:00",
            "length": 64,
            "format_version": "1.0"
        }
        
        with open(invalid_file, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError, match="missing 'secret_content'"):
            PreseedGenerator.load_preseed_from_file(str(invalid_file))
    
    def test_validate_missing_required_fields(self, temp_dir):
        """Test validation of file missing required fields."""
        invalid_file = temp_dir / "missing_fields.json"
        data = {
            "secret_content": "test",
            "generated_at": "2025-01-01T00:00:00"
            # Missing length and format_version
        }
        
        with open(invalid_file, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError, match="Missing required field"):
            PreseedGenerator.validate_preseed_file(str(invalid_file))
    
    def test_create_preseed_file_creates_directories(self, temp_dir):
        """Test that preseed file creation creates necessary directories."""
        nested_path = temp_dir / "nested" / "dir" / "preseed.json"
        
        PreseedGenerator.create_preseed_file(
            output_path=str(nested_path),
            length=64
        )
        
        assert nested_path.exists()
        assert nested_path.parent.exists()
