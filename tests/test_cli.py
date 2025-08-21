"""
Tests for the CLI module.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from click.testing import CliRunner

from licensing.cli import cli


class TestCLI:
    """Test the CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'generate-preseed' in result.output
        assert 'generate-keys' in result.output
        assert 'generate-license' in result.output
        assert 'verify-license' in result.output
    
    def test_generate_preseed_command(self):
        """Test generate-preseed command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_preseed.json")
            
            result = self.runner.invoke(cli, [
                'generate-preseed',
                '--output', output_file,
                '--length', '32',
                '--project-name', 'TestProject',
                '--description', 'Test preseed file'
            ])
            
            assert result.exit_code == 0
            assert 'Preseed file generated' in result.output
            assert os.path.exists(output_file)
            
            # Verify file contents
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert 'secret_content' in data
            assert 'generated_at' in data
            assert data['length'] == 32
            assert data['metadata']['project_name'] == 'TestProject'
            assert data['metadata']['description'] == 'Test preseed file'
    
    def test_generate_preseed_default_values(self):
        """Test generate-preseed with default values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "default_preseed.json")
            
            result = self.runner.invoke(cli, [
                'generate-preseed',
                '--output', output_file
            ])
            
            assert result.exit_code == 0
            assert os.path.exists(output_file)
            
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert data['length'] == 64  # Default length
    
    def test_generate_keys_text_format(self):
        """Test generate-keys command with text format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_keys.txt")
            
            result = self.runner.invoke(cli, [
                'generate-keys',
                '--format', 'text',
                '--output', output_file
            ])
            
            assert result.exit_code == 0
            assert 'Keys saved to' in result.output
            assert os.path.exists(output_file)
            
            # Verify file contents
            with open(output_file, 'r') as f:
                content = f.read()
            
            assert ('BEGIN PRIVATE KEY' in content or 'PRIVATE KEY' in content)
            assert ('BEGIN PUBLIC KEY' in content or 'PUBLIC KEY' in content)
    
    def test_generate_keys_json_format(self):
        """Test generate-keys command with JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_keys.json")
            
            result = self.runner.invoke(cli, [
                'generate-keys',
                '--format', 'json',
                '--output', output_file
            ])
            
            assert result.exit_code == 0
            assert os.path.exists(output_file)
            
            # Verify file contents
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert 'private_key' in data
            assert 'public_key' in data
            assert 'generated_at' in data
            assert 'curve' in data
    
    def test_generate_license_command(self):
        """Test generate-license command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create preseed file
            preseed_file = os.path.join(temp_dir, "test_preseed.json")
            self.runner.invoke(cli, [
                'generate-preseed',
                '--output', preseed_file,
                '--length', '32'
            ])
            
            # Create keys file
            keys_file = os.path.join(temp_dir, "test_keys.json")
            self.runner.invoke(cli, [
                'generate-keys',
                '--format', 'json',
                '--output', keys_file
            ])
            
            # Generate license
            license_file = os.path.join(temp_dir, "test_license.txt")
            result = self.runner.invoke(cli, [
                'generate-license',
                '--private-key', keys_file,
                '--preseed-file', preseed_file,
                '--app-name', 'TestApp',
                '--version', '1.0',
                '--component-name', 'TestComponent',
                '--customer', 'Test Customer',
                '--expires', '2025-12-31',
                '--output', license_file
            ])
            
            assert result.exit_code == 0
            assert 'License generated successfully' in result.output
            assert os.path.exists(license_file)
            
            # Verify license file
            with open(license_file, 'r') as f:
                license_content = f.read().strip()
            
            # Should be valid JSON
            license_data = json.loads(license_content)
            assert 'license' in license_data
            assert 'info' in license_data
    
    def test_generate_license_missing_preseed_file(self):
        """Test generate-license with missing preseed file."""
        result = self.runner.invoke(cli, [
            'generate-license',
            '--private-key', 'nonexistent.json',
            '--preseed-file', 'nonexistent.json',
            '--expires', '2025-12-31'
        ])
        
        assert result.exit_code != 0
        assert 'does not exist' in result.output
    
    def test_verify_license_command(self):
        """Test verify-license command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create preseed file
            preseed_file = os.path.join(temp_dir, "test_preseed.json")
            self.runner.invoke(cli, [
                'generate-preseed',
                '--output', preseed_file
            ])
            
            # Create keys file
            keys_file = os.path.join(temp_dir, "test_keys.json")
            self.runner.invoke(cli, [
                'generate-keys',
                '--format', 'json',
                '--output', keys_file
            ])
            
            # Generate license
            license_file = os.path.join(temp_dir, "test_license.txt")
            self.runner.invoke(cli, [
                'generate-license',
                '--private-key', keys_file,
                '--preseed-file', preseed_file,
                '--expires', '2025-12-31',
                '--output', license_file
            ])
            
            # Verify license
            result = self.runner.invoke(cli, [
                'verify-license',
                '--license', license_file,
                '--public-key', keys_file,
                '--preseed-file', preseed_file,
                '--skip-hardware'
            ])
            
            assert result.exit_code == 0
            assert 'VALID' in result.output
    
    def test_cli_version_info(self):
        """Test that CLI commands provide version info."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'generate-license' in result.output
        assert 'verify-license' in result.output
        assert 'generate-keys' in result.output
    
    def test_demo_command_basic(self):
        """Test demo command basic functionality."""
        # Just test that the demo command runs without changing directories
        # to avoid Windows file permission issues
        result = self.runner.invoke(cli, ['demo'])
        
        assert result.exit_code == 0
        assert 'demo' in result.output.lower()
    
    def test_generate_license_with_metadata(self):
        """Test generate-license with metadata fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create preseed and keys
            preseed_file = os.path.join(temp_dir, "test_preseed.json")
            keys_file = os.path.join(temp_dir, "test_keys.json")
            
            self.runner.invoke(cli, ['generate-preseed', '--output', preseed_file])
            self.runner.invoke(cli, ['generate-keys', '--format', 'json', '--output', keys_file])
            
            # Generate license with metadata
            license_file = os.path.join(temp_dir, "test_license.txt")
            result = self.runner.invoke(cli, [
                'generate-license',
                '--private-key', keys_file,
                '--preseed-file', preseed_file,
                '--app-name', 'TestApp',
                '--version', '2.0',
                '--component-name', 'CoreModule',
                '--customer', 'Test Corp',
                '--expires', '2025-12-31',
                '--output', license_file
            ])
            
            assert result.exit_code == 0
            
            # Verify metadata is in license
            with open(license_file, 'r') as f:
                license_content = json.loads(f.read().strip())
            
            license_data = json.loads(license_content['license'])
            assert license_data['app_name'] == 'TestApp'
            assert license_data['customer'] == 'Test Corp'
    
    def test_generate_license_target_hardware(self):
        """Test generate-license for target hardware."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create preseed and keys
            preseed_file = os.path.join(temp_dir, "test_preseed.json")
            keys_file = os.path.join(temp_dir, "test_keys.json")
            
            self.runner.invoke(cli, ['generate-preseed', '--output', preseed_file])
            self.runner.invoke(cli, ['generate-keys', '--format', 'json', '--output', keys_file])
            
            # Create target hardware file
            target_file = os.path.join(temp_dir, "target_hardware.json")
            target_data = {
                "mac_addresses": ["00:11:22:33:44:55"],
                "disk_info": ["disk1"],
                "cpu_info": {"processor": "Intel Core i7"},
                "system_info": {"system": "Windows", "node": "TargetPC"}
            }
            with open(target_file, 'w') as f:
                json.dump(target_data, f)
            
            # Generate license for target
            license_file = os.path.join(temp_dir, "target_license.txt")
            result = self.runner.invoke(cli, [
                'generate-license',
                '--private-key', keys_file,
                '--preseed-file', preseed_file,
                '--expires', '2025-12-31',
                '--target-hardware', target_file,
                '--output', license_file
            ])
            
            assert result.exit_code == 0
            assert os.path.exists(license_file)
    
    def test_invalid_date_format(self):
        """Test generate-license with invalid date format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            preseed_file = os.path.join(temp_dir, "test_preseed.json")
            keys_file = os.path.join(temp_dir, "test_keys.json")
            
            self.runner.invoke(cli, ['generate-preseed', '--output', preseed_file])
            self.runner.invoke(cli, ['generate-keys', '--format', 'json', '--output', keys_file])
            
            result = self.runner.invoke(cli, [
                'generate-license',
                '--private-key', keys_file,
                '--preseed-file', preseed_file,
                '--expires', 'invalid-date',
                '--output', 'test_license.txt'
            ])
            
            assert result.exit_code != 0
            assert ('date format' in result.output.lower() or 'does not match format' in result.output.lower())
    
    def test_generate_preseed_with_metadata(self):
        """Test generate-preseed with metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            preseed_file = os.path.join(temp_dir, "test_preseed.json")
            
            result = self.runner.invoke(cli, [
                'generate-preseed',
                '--output', preseed_file,
                '--project-name', 'TestProject',
                '--description', 'Test description'
            ])
            
            assert result.exit_code == 0
            assert os.path.exists(preseed_file)
            
            # Verify metadata was included
            with open(preseed_file, 'r') as f:
                data = json.load(f)
            assert data['metadata']['project_name'] == 'TestProject'
    
    def test_get_hardware_info_command(self):
        """Test get-hardware-info command."""
        result = self.runner.invoke(cli, [
            'get-hardware-info',
            '--fingerprint-type', 'mac'
        ])
        
        assert result.exit_code == 0
        assert 'hardware information' in result.output.lower()
