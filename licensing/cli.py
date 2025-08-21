"""
Command Line Interface for the Licensing System.

This module provides a simple CLI for generating keys, creating licenses,
and verifying licenses using the Click library.
"""

import os
import json
import click
from datetime import datetime, timedelta
from typing import Optional

from .license_generator import LicenseGenerator
from .license_manager import LicenseManager
from .preseed_generator import PreseedGenerator
from .exceptions import LicenseError, LicenseExpiredError, LicenseInvalidError, HardwareMismatchError


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🔐 Offline Licensing System CLI
    
    A secure offline licensing solution using ECDSA signatures and hardware fingerprinting.
    """
    pass


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file to save keys (optional)')
@click.option('--format', 'output_format', type=click.Choice(['json', 'text']), default='text', 
              help='Output format for keys')
def generate_keys(output: Optional[str], output_format: str):
    """Generate a new ECDSA key pair for license signing."""
    click.echo("Generating ECDSA key pair...")
    
    try:
        private_key, public_key = LicenseGenerator.generate_key_pair()
        
        if output_format == 'json':
            keys_data = {
                "private_key": private_key,
                "public_key": public_key,
                "generated_at": datetime.now().isoformat(),
                "curve": "P-256"
            }
            
            if output:
                with open(output, 'w') as f:
                    json.dump(keys_data, f, indent=2)
                click.echo(f"Keys saved to {output}")
            else:
                click.echo(json.dumps(keys_data, indent=2))
        else:
            key_text = f"""
ECDSA Key Pair Generated
{'='*50}

PRIVATE KEY (Keep this secret!)
{private_key}

PUBLIC KEY (Distribute with your application)
{public_key}

IMPORTANT:
- Store the private key securely and never share it
- The public key should be distributed with your application
- You'll also need a preseed key for additional security

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Curve: P-256 (secp256r1)
"""
            
            if output:
                with open(output, 'w') as f:
                    f.write(key_text)
                click.echo(f"Keys saved to {output}")
            else:
                click.echo(key_text)
                
    except Exception as e:
        click.echo(f"Error generating keys: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--output', '-o', type=click.Path(), default='preseed.json', 
              help='Output file to save preseed (default: preseed.json)')
@click.option('--length', '-l', type=int, default=64, 
              help='Length of preseed key in characters (default: 64)')
@click.option('--project-name', help='Project name for metadata (optional)')
@click.option('--description', help='Description for metadata (optional)')
def generate_preseed(output: str, length: int, 
                    project_name: Optional[str], description: Optional[str]):
    """Generate a secure preseed file for license generation."""
    
    try:
        click.echo(f"Generating secure preseed ({length} characters)...")
        
        # Prepare metadata
        metadata = {}
        if project_name:
            metadata['project_name'] = project_name
        if description:
            metadata['description'] = description
        
        # Generate preseed file
        secret_content = PreseedGenerator.create_preseed_file(
            output_path=output,
            metadata=metadata,
            length=length
        )
        
        click.echo(f"✓ Preseed file generated: {output}")
        click.echo(f"✓ Secret length: {length} characters")
        if metadata:
            click.echo(f"✓ Metadata included: {list(metadata.keys())}")
        
        # Show file info
        info = PreseedGenerator.validate_preseed_file(output)
        click.echo(f"✓ File size: {info['file_size']} bytes")
        click.echo(f"✓ Generated at: {info['generated_at']}")
            
        click.echo(f"\n🔐 SECURITY NOTES:")
        click.echo(f"   • Keep {output} secure and confidential")
        click.echo(f"   • Do NOT commit {output} to version control")
        click.echo(f"   • Back up {output} safely")
        click.echo(f"   • The secret content will be hashed before use")
        
        click.echo(f"\n📋 Next steps:")
        click.echo(f"   1. Generate keys: licensing generate-keys")
        click.echo(f"   2. Generate license: licensing generate-license --preseed-file {output}")
        click.echo(f"   3. Verify license: licensing verify-license --preseed-file {output}")
        
    except Exception as e:
        click.echo(f"Error generating preseed: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--private-key', '-k', required=True, help='Private key (base64) or path to key file')
@click.option('--preseed-file', '-p', type=click.Path(exists=True), required=True, help='Path to preseed file')
@click.option('--expires', '-e', type=str, help='Expiry date (YYYY-MM-DD) or days from now (e.g., "30d")')
@click.option('--fingerprint-type', '-f', 
              type=click.Choice(['mac', 'disk', 'cpu', 'system', 'composite']),
              default='composite', help='Hardware fingerprint type')
@click.option('--target-hardware', '-t', type=click.Path(exists=True), 
              help='JSON file with target hardware info (for remote license generation)')
@click.option('--app-name', help='Application name to include in license')
@click.option('--version', help='Application version to include in license')
@click.option('--customer', help='Customer name to include in license')
@click.option('--component-name', '-c', help='Component/module name for additional security')
@click.option('--output', '-o', type=click.Path(), help='Output file to save license')
def generate_license(private_key: str, preseed_file: str, expires: Optional[str], 
                    fingerprint_type: str, target_hardware: Optional[str],
                    app_name: Optional[str], version: Optional[str], 
                    customer: Optional[str], component_name: Optional[str], output: Optional[str]):
    """Generate a license for the current or target machine."""
    
    try:
        # Load private key (from file or direct input)
        if os.path.isfile(private_key):
            with open(private_key, 'r') as f:
                content = f.read()
                try:
                    key_data = json.loads(content)
                    private_key_b64 = key_data['private_key']
                except json.JSONDecodeError:
                    # Assume it's a plain text key
                    private_key_b64 = content.strip()
        else:
            private_key_b64 = private_key
        
        # Load preseed from file
        try:
            preseed = PreseedGenerator.load_preseed_from_file(preseed_file)
            click.echo(f"✓ Loaded preseed from: {preseed_file}")
        except Exception as e:
            click.echo(f"Error loading preseed file: {e}", err=True)
            raise click.ClickException(str(e))
        
        # Parse expiry date
        if expires:
            if expires.endswith('d'):
                # Days from now
                days = int(expires[:-1])
                expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            else:
                # Assume YYYY-MM-DD format
                expiry_date = expires
                # Validate format
                datetime.strptime(expiry_date, "%Y-%m-%d")
        else:
            # Default to 1 year from now
            expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        click.echo(f"Generating license (expires: {expiry_date})...")
        
        # Create generator
        generator = LicenseGenerator(private_key_b64, preseed)
        
        # Prepare additional data
        additional_data = {}
        if app_name:
            additional_data['app_name'] = app_name
        if version:
            additional_data['app_version'] = version
        if customer:
            additional_data['customer'] = customer
        
        # Generate license
        if target_hardware:
            # Load target hardware info
            with open(target_hardware, 'r') as f:
                hw_info = json.load(f)
            
            license_string = generator.generate_license_for_target(
                target_hardware_info=hw_info,
                expiry_date=expiry_date,
                fingerprint_type=fingerprint_type,
                additional_data=additional_data if additional_data else None,
                component_name=component_name
            )
            click.echo(f"License generated for target hardware")
        else:
            # Generate for current machine
            license_string = generator.generate_license(
                expiry_date=expiry_date,
                fingerprint_type=fingerprint_type,
                additional_data=additional_data if additional_data else None,
                component_name=component_name
            )
            
            # Show current hardware fingerprint
            current_fp = generator.hw_fingerprint.get_fingerprint(fingerprint_type)
            click.echo(f"Hardware fingerprint ({fingerprint_type}): {current_fp[:16]}...")
        
        license_info = generator.parse_license(license_string)
        
        click.echo(f"\nLicense generated successfully!")
        click.echo(f"License Details:")
        click.echo(f"   Fingerprint Type: {license_info['hw_type']}")
        click.echo(f"   Expiry Date: {license_info['expiry']}")
        click.echo(f"   Issued Date: {license_info['issued']}")
        # Show component name if present
        if license_info.get('component_name'):
            click.echo(f"   Component Name: {license_info['component_name']}")
            
        # Additional data is merged directly into the license, so show app-specific fields
        app_fields = {k: v for k, v in license_info.items() 
                     if k not in ['version', 'hw_type', 'hw_info', 'expiry', 'issued', 'preseed_hash', 'signature', 'component_name']}
        if app_fields:
            click.echo(f"   Additional Data: {app_fields}")
        
        click.echo(f"\nLicense String:")
        
        if output:
            license_data = {
                "license": license_string,
                "info": license_info,
                "generated_at": datetime.now().isoformat()
            }
            with open(output, 'w') as f:
                json.dump(license_data, f, indent=2)
            click.echo(f"License saved to {output}")
        else:
            click.echo(license_string)
            
    except Exception as e:
        click.echo(f"Error generating license: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--public-key', '-k', required=True, help='Public key (base64) or path to key file')
@click.option('--preseed-file', '-p', type=click.Path(exists=True), required=True, help='Path to preseed file used during license generation')
@click.option('--license', '-l', required=True, help='License string or path to license file')
@click.option('--skip-hardware', is_flag=True, help='Skip hardware fingerprint verification')
@click.option('--skip-expiry', is_flag=True, help='Skip expiry date verification')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed verification information')
def verify_license(public_key: str, preseed_file: str, license: str, 
                  skip_hardware: bool, skip_expiry: bool, verbose: bool):
    """Verify a license on the current machine."""
    
    try:
        # Load public key (from file or direct input)
        if os.path.isfile(public_key):
            with open(public_key, 'r') as f:
                content = f.read()
                try:
                    key_data = json.loads(content)
                    public_key_b64 = key_data['public_key']
                except json.JSONDecodeError:
                    # Assume it's a plain text key
                    public_key_b64 = content.strip()
        else:
            public_key_b64 = public_key
        
        # Load preseed from file
        try:
            preseed = PreseedGenerator.load_preseed_from_file(preseed_file)
            click.echo(f"✓ Loaded preseed from: {preseed_file}")
        except Exception as e:
            click.echo(f"Error loading preseed file: {e}", err=True)
            raise click.ClickException(str(e))
        
        # Load license (from file or direct input)
        if os.path.isfile(license):
            with open(license, 'r') as f:
                content = f.read()
                try:
                    license_data = json.loads(content)
                    if 'license' in license_data:
                        license_string = license_data['license']
                    else:
                        # The file itself contains the license JSON
                        license_string = content.strip()
                except json.JSONDecodeError:
                    # Assume it's a plain text license
                    license_string = content.strip()
        else:
            license_string = license
        
        click.echo("Verifying license...")
        
        # Create license manager
        manager = LicenseManager(public_key_b64, preseed)
        
        # Get license info first
        try:
            license_info = manager.get_license_info(license_string)
            
            if verbose:
                click.echo(f"\nLicense Information:")
                for key, value in license_info.items():
                    if key == "signature":
                        click.echo(f"   {key}: {value[:32]}...")
                    elif key == "status":
                        click.echo(f"   {key}:")
                        for status_key, status_value in value.items():
                            status_icon = "PASS" if status_value else "FAIL"
                            click.echo(f"     {status_key}: {status_icon} {status_value}")
                    elif key == "additional_data":
                        click.echo(f"   {key}: {value}")
                    else:
                        click.echo(f"   {key}: {value}")
            
            # Show days until expiry
            days_until_expiry = manager.get_days_until_expiry(license_string)
            if days_until_expiry is not None:
                if days_until_expiry > 0:
                    click.echo(f"⏰ License expires in {days_until_expiry} days")
                elif days_until_expiry == 0:
                    click.echo(f"⚠️  License expires today")
                else:
                    click.echo(f"💀 License expired {abs(days_until_expiry)} days ago")
            
        except Exception as e:
            click.echo(f"Error reading license: {e}", err=True)
            return
        
        # Perform full verification
        click.echo(f"\n🔐 Full Verification:")
        
        try:
            verified_license = manager.verify_license(
                license_string, 
                check_hardware=not skip_hardware, 
                check_expiry=not skip_expiry
            )
            
            click.echo("LICENSE IS VALID AND ACTIVE")
            click.echo("Signature verification: PASSED")
            
            if not skip_hardware:
                click.echo("Hardware fingerprint: MATCHED")
            else:
                click.echo("Hardware fingerprint: SKIPPED")
            
            if not skip_expiry:
                click.echo("License expiry: NOT EXPIRED")
            else:
                click.echo("License expiry: SKIPPED")
            
            click.echo("Preseed verification: PASSED")
            
        except LicenseExpiredError as e:
            click.echo("LICENSE IS EXPIRED")
            click.echo(f"   {e}")
            
        except HardwareMismatchError as e:
            click.echo("HARDWARE FINGERPRINT MISMATCH")
            click.echo(f"   {e}")
            click.echo("   This license was generated for a different machine")
            
        except LicenseInvalidError as e:
            click.echo("LICENSE IS INVALID")
            click.echo(f"   {e}")
        
        if verbose:
            # Test individual components
            click.echo(f"\n🧪 Component Tests:")
            click.echo(f"   Signature only: {'VALID' if manager.is_valid(license_string, check_hardware=False, check_expiry=False) else 'INVALID'}")
            click.echo(f"   Signature + Hardware: {'VALID' if manager.is_valid(license_string, check_hardware=True, check_expiry=False) else 'INVALID'}")
            click.echo(f"   Signature + Expiry: {'VALID' if manager.is_valid(license_string, check_hardware=False, check_expiry=True) else 'INVALID'}")
            click.echo(f"   Full verification: {'VALID' if manager.is_valid(license_string, check_hardware=True, check_expiry=True) else 'INVALID'}")
            
    except Exception as e:
        click.echo(f"Error during verification: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--fingerprint-type', '-f', 
              type=click.Choice(['mac', 'disk', 'cpu', 'system', 'composite']),
              default='composite', help='Hardware fingerprint type')
@click.option('--output', '-o', type=click.Path(), help='Output file to save hardware info')
def get_hardware_info(fingerprint_type: str, output: Optional[str]):
    """Get current machine's hardware information for license generation."""
    
    try:
        click.echo(f"Collecting hardware information ({fingerprint_type})...")
        
        from .hardware_fingerprint import HardwareFingerprint
        hw_fingerprint = HardwareFingerprint()
        
        # Get fingerprint
        fingerprint = hw_fingerprint.get_fingerprint(fingerprint_type)
        
        # Get detailed hardware info
        if fingerprint_type == "mac":
            hw_data = {"mac_addresses": hw_fingerprint._get_mac_addresses()}
        elif fingerprint_type == "disk":
            hw_data = {"disk_info": hw_fingerprint._get_disk_info()}
        elif fingerprint_type == "cpu":
            hw_data = {"cpu_info": hw_fingerprint._get_cpu_info()}
        elif fingerprint_type == "system":
            hw_data = {"system_info": hw_fingerprint._get_system_info()}
        else:  # composite
            hw_data = hw_fingerprint._get_composite_info()
        
        result = {
            "hw_type": fingerprint_type,
            "fingerprint_hash": fingerprint,
            "hardware_data": hw_data,
            "collected_at": datetime.now().isoformat()
        }
        
        click.echo(f"Hardware fingerprint: {fingerprint}")
        
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            click.echo(f"Hardware info saved to {output}")
        else:
            click.echo(f"\nHardware Data:")
            click.echo(json.dumps(hw_data, indent=2))
            
    except Exception as e:
        click.echo(f"Error collecting hardware info: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
def demo():
    """Run a complete licensing workflow demonstration."""
    
    click.echo("Running complete licensing workflow demo...")
    click.echo("="*60)
    
    try:
        # Generate keys
        click.echo("\n1. Generating keys...")
        private_key, public_key = LicenseGenerator.generate_key_pair()
        click.echo(f"   Keys generated successfully")
        
        # Generate preseed file
        click.echo(f"\n2. Generating preseed file...")
        preseed = PreseedGenerator.create_preseed_file(
            output_path="demo_preseed.json",
            metadata={"project_name": "Demo", "description": "Demo preseed file"},
            length=64
        )
        
        # Load the hashed preseed from file
        preseed_hash = PreseedGenerator.load_preseed_from_file("demo_preseed.json")
        click.echo(f"   Preseed file generated: demo_preseed.json")
        
        # Generate license
        click.echo(f"\n3. Generating license...")
        expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        generator = LicenseGenerator(private_key, preseed_hash)
        license_string = generator.generate_license(
            expiry_date=expiry_date,
            fingerprint_type="composite",
            additional_data={"app_name": "DemoApp", "app_version": "1.0.0"},
            component_name="DemoComponent"
        )
        
        click.echo(f"   License generated (expires: {expiry_date})")
        
        # Verify license
        click.echo(f"\n4. Verifying license...")
        manager = LicenseManager(public_key, preseed_hash)
        
        verified_license = manager.verify_license(license_string)
        click.echo(f"   License verification passed")
        
        click.echo(f"\nDemo completed successfully!")
        click.echo(f"\nGenerated License:")
        click.echo(license_string)
        
        click.echo(f"\nTry these commands:")
        click.echo(f"   licensing verify-license -k '<public_key>' -p demo_preseed.json -l '<license>' -v")
        click.echo(f"   licensing generate-license -k '<private_key>' -p demo_preseed.json")
        
    except Exception as e:
        click.echo(f"Demo failed: {e}", err=True)
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()
