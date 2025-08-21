#!/usr/bin/env python3
"""
Step 2: Generate a license using the keys from Step 1.

This script generates a license for the current machine using the
private key created in step1_generate_keys.py.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the licensing module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from licensing import LicenseGenerator


def main():
    print("=" * 60)
    print("STEP 2: GENERATING LICENSE")
    print("=" * 60)
    
    # Check if private key exists
    if not os.path.exists("private_key.txt"):
        print("Error: private_key.txt not found!")
        print("Please run: python examples/step1_generate_keys.py first")
        return
    
    # Load private key
    try:
        with open("private_key.txt", "r") as f:
            private_key = f.read().strip()
        print("✓ Loaded private key from private_key.txt")
    except Exception as e:
        print(f"Error loading private key: {e}")
        return
    
    # Load parameters from test_inputs.txt
    params = []
    try:
        with open("test_inputs.txt", "r") as f:
            params = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("Warning: test_inputs.txt not found, using defaults")
    
    # Extract parameters with defaults
    preseed = params[0] if len(params) > 0 else "my-secret-preseed-2024"
    days = int(params[1]) if len(params) > 1 else 365
    hw_choice = params[2] if len(params) > 2 else "5"
    app_name = params[3] if len(params) > 3 else "TestApp"
    app_version = params[4] if len(params) > 4 else "1.0"
    customer = params[5] if len(params) > 5 else "Test Customer"
    component_name = params[6] if len(params) > 6 else "CoreModule"
    
    print(f"✓ Using preseed: {preseed}")
    
    # Calculate expiry date
    expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    print(f"✓ License will expire on: {expiry_date} ({days} days)")
    
    # Set hardware fingerprint type
    hw_types = {"1": "mac", "2": "disk", "3": "cpu", "4": "system", "5": "composite"}
    fingerprint_type = hw_types.get(hw_choice, "composite")
    print(f"✓ Using fingerprint type: {fingerprint_type}")
    
    # Show application info
    print(f"✓ Application: {app_name} v{app_version}")
    print(f"✓ Customer: {customer}")
    print(f"✓ Component: {component_name}")
    
    print(f"\n{'='*60}")
    print("GENERATING LICENSE...")
    print("="*60)
    
    try:
        # Create license generator
        generator = LicenseGenerator(private_key, preseed)
        
        # Show current hardware fingerprint
        current_fp = generator.hw_fingerprint.get_fingerprint(fingerprint_type)
        print(f"Current hardware fingerprint ({fingerprint_type}): {current_fp[:16]}...")
        
        # Prepare additional data
        additional_data = {
            "app_name": app_name,
            "app_version": app_version,
            "customer": customer
        }
        
        # Generate license
        license_string = generator.generate_license(
            expiry_date=expiry_date,
            fingerprint_type=fingerprint_type,
            additional_data=additional_data,
            component_name=component_name
        )
        
        # Save license to file
        with open("license.txt", "w") as f:
            f.write(license_string)
        
        print("✓ License generated successfully!")
        print(f"✓ License saved to: license.txt")
        
        # Show license details
        license_info = generator.parse_license(license_string)
        print(f"\nLicense Details:")
        print(f"  Version: {license_info.get('version')}")
        print(f"  Hardware Type: {license_info.get('hw_type')}")
        print(f"  Hardware Info: {license_info.get('hw_info')[:50]}...")
        print(f"  Expires: {license_info.get('expiry')}")
        print(f"  Issued: {license_info.get('issued')}")
        print(f"  Component Name: {license_info.get('component_name')}")
        print(f"  App Name: {license_info.get('app_name')}")
        print(f"  App Version: {license_info.get('app_version')}")
        print(f"  Customer: {license_info.get('customer')}")
        print(f"  Preseed Hash: {license_info.get('preseed_hash')[:16]}...")
        
        print(f"\nLicense String (one line JSON):")
        print(f"{license_string}")
        
        print(f"\n{'='*60}")
        print("NEXT STEPS:")
        print("="*60)
        print("1. Run: python examples/step3_verify_license.py")
        print("2. Or use CLI: python licensing_cli.py verify-license -k public_key.txt -p 'your-preseed' -l license.txt")
        
    except Exception as e:
        print(f"Error generating license: {e}")
        return


if __name__ == "__main__":
    main()

