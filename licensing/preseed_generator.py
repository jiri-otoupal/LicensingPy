"""
Preseed generation and management module.

This module handles the creation and loading of preseed files containing
secret content that gets hashed to create the actual preseed used in licensing.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class PreseedGenerator:
    """
    Manages preseed file generation and loading.
    
    Preseed files contain secret content that gets hashed to create
    the actual preseed key used in license generation and verification.
    """
    
    @staticmethod
    def generate_preseed(length: int = 64) -> str:
        """
        Generate a random preseed string.
        
        Args:
            length: Length of the preseed string
            
        Returns:
            Random preseed string
        """
        # Use cryptographically secure random generator
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def create_preseed_file(output_path: str, 
                           metadata: Optional[Dict] = None,
                           length: int = 64) -> str:
        """
        Create a preseed file with secret content and metadata.
        
        Args:
            output_path: Path where to save the preseed file
            metadata: Optional metadata to include in the file
            length: Length of the secret content
            
        Returns:
            The generated preseed content (before hashing)
            
        Raises:
            IOError: If file cannot be written
        """
        # Generate secret content
        secret_content = PreseedGenerator.generate_preseed(length)
        
        # Create preseed file structure
        preseed_data = {
            "secret_content": secret_content,
            "generated_at": datetime.now().isoformat(),
            "length": length,
            "format_version": "1.0"
        }
        
        # Add metadata if provided
        if metadata:
            preseed_data["metadata"] = metadata
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(preseed_data, f, indent=2)
        
        return secret_content
    
    @staticmethod
    def load_preseed_from_file(file_path: str) -> str:
        """
        Load preseed from a file and return the hashed preseed.
        
        Args:
            file_path: Path to the preseed file
            
        Returns:
            Hashed preseed string ready for use in licensing
            
        Raises:
            FileNotFoundError: If preseed file doesn't exist
            ValueError: If preseed file format is invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Preseed file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                preseed_data = json.load(f)
            
            # Validate file format
            if "secret_content" not in preseed_data:
                raise ValueError("Invalid preseed file: missing 'secret_content' field")
            
            if "format_version" not in preseed_data:
                raise ValueError("Invalid preseed file: missing 'format_version' field")
            
            # Get secret content
            secret_content = preseed_data["secret_content"]
            
            # Hash the secret content to create the actual preseed
            # Include file path and metadata in hash for additional uniqueness
            hash_input = secret_content
            
            # Add metadata to hash if present
            if "metadata" in preseed_data:
                metadata_str = json.dumps(preseed_data["metadata"], sort_keys=True)
                hash_input += ":" + metadata_str
            
            # Create SHA256 hash of the secret content
            preseed_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            
            return preseed_hash
            
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in preseed file: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading preseed file: {e}")
    
    @staticmethod
    def validate_preseed_file(file_path: str) -> Dict:
        """
        Validate a preseed file and return its information.
        
        Args:
            file_path: Path to the preseed file
            
        Returns:
            Dictionary with preseed file information
            
        Raises:
            FileNotFoundError: If preseed file doesn't exist
            ValueError: If preseed file format is invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Preseed file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                preseed_data = json.load(f)
            
            # Check required fields
            required_fields = ["secret_content", "generated_at", "length", "format_version"]
            for field in required_fields:
                if field not in preseed_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Return file information
            info = {
                "file_path": str(file_path),
                "generated_at": preseed_data["generated_at"],
                "length": preseed_data["length"],
                "format_version": preseed_data["format_version"],
                "has_metadata": "metadata" in preseed_data,
                "file_size": file_path.stat().st_size
            }
            
            if "metadata" in preseed_data:
                info["metadata"] = preseed_data["metadata"]
            
            return info
            
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in preseed file: {file_path}")
        except Exception as e:
            raise ValueError(f"Error validating preseed file: {e}")
