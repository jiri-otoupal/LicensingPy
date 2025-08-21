#!/usr/bin/env python3
"""
Step 3: Verify a license using the keys from Step 1.

This script verifies the license created in step2_generate_license.py
using the public key.
"""

import sys
import os

# Add the parent directory to the path so we can import the licensing module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from licensing import LicenseManager
from licensing.exceptions import LicenseExpiredError, LicenseInvalidError, HardwareMismatchError


def main():
    print("=" * 60)
    print("STEP 3: VERIFYING LICENSE")
    print("=" * 60)
    
    # Check if public key exists
    if not os.path.exists("public_key.txt"):
        print("Error: public_key.txt not found!")
        print("Please run: python examples/step1_generate_keys.py first")
        return
    
    # Load public key
    try:
        with open("public_key.txt", "r") as f:
            public_key = f.read().strip()
        print("✓ Loaded public key from public_key.txt")
    except Exception as e:
        print(f"Error loading public key: {e}")
        return
    
    # Load parameters from test_inputs.txt
    params = []
    try:
        with open("test_inputs.txt", "r") as f:
            params = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("Warning: test_inputs.txt not found, using defaults")
    
    # Get preseed from parameters (must match the one used for generation)
    preseed = params[0] if len(params) > 0 else "my-secret-preseed-2024"
    print(f"✓ Using preseed: {preseed}")
    
    # Load license from license.txt automatically
    if not os.path.exists("license.txt"):
        print("Error: license.txt not found!")
        print("Please run: python examples/step2_generate_license.py first")
        return
    
    try:
        with open("license.txt", "r") as f:
            license_string = f.read().strip()
        print("✓ Loaded license from license.txt")
    except Exception as e:
        print(f"Error loading license: {e}")
        return
    
    print(f"\n{'='*60}")
    print("VERIFYING LICENSE...")
    print("="*60)
    
    try:
        # Create license manager
        manager = LicenseManager(public_key, preseed)
        
        # Get license info first (without full validation)
        try:
            license_info = manager.get_license_info(license_string)
            
            print("License Information:")
            for key, value in license_info.items():
                if key == "signature":
                    print(f"  {key}: {value[:32]}...")
                elif key == "status":
                    print(f"  {key}:")
                    for status_key, status_value in value.items():
                        status_icon = "PASS" if status_value else "FAIL"
                        print(f"    {status_key}: {status_icon}")
                elif key == "hw_info" and len(str(value)) > 50:
                    print(f"  {key}: {str(value)[:50]}...")
                else:
                    print(f"  {key}: {value}")
            
            # Get days until expiry
            days_until_expiry = manager.get_days_until_expiry(license_string)
            if days_until_expiry is not None:
                if days_until_expiry > 0:
                    print(f"\n⏰ License expires in {days_until_expiry} days")
                elif days_until_expiry == 0:
                    print(f"\n⚠️  License expires today")
                else:
                    print(f"\n💀 License expired {abs(days_until_expiry)} days ago")
            
        except Exception as e:
            print(f"Error reading license info: {e}")
            return
        
        print(f"\n{'='*40}")
        print("FULL VERIFICATION")
        print("="*40)
        
        # Perform full verification
        try:
            verified_license = manager.verify_license(license_string)
            print("✓ LICENSE IS VALID AND ACTIVE")
            print("✓ Signature verification: PASSED")
            print("✓ Hardware fingerprint: MATCHED")
            print("✓ License expiry: NOT EXPIRED")
            print("✓ Preseed verification: PASSED")
            
            print(f"\n{'='*60}")
            print("SUCCESS! License verification completed.")
            print("="*60)
            
        except LicenseExpiredError as e:
            print("✗ LICENSE IS EXPIRED")
            print(f"   {e}")
            
        except HardwareMismatchError as e:
            print("✗ HARDWARE FINGERPRINT MISMATCH")
            print(f"   {e}")
            print("   This license was generated for a different machine")
            
        except LicenseInvalidError as e:
            print("✗ LICENSE IS INVALID")
            print(f"   {e}")
        
        # Test individual components
        print(f"\n{'='*40}")
        print("COMPONENT VERIFICATION")
        print("="*40)
        
        print(f"Signature only: {'VALID' if manager.is_valid(license_string, check_hardware=False, check_expiry=False) else 'INVALID'}")
        print(f"Signature + Hardware: {'VALID' if manager.is_valid(license_string, check_hardware=True, check_expiry=False) else 'INVALID'}")
        print(f"Signature + Expiry: {'VALID' if manager.is_valid(license_string, check_hardware=False, check_expiry=True) else 'INVALID'}")
        print(f"Full verification: {'VALID' if manager.is_valid(license_string, check_hardware=True, check_expiry=True) else 'INVALID'}")
        
        print(f"\n{'='*60}")
        print("VERIFICATION COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"Error during verification: {e}")


if __name__ == "__main__":
    main()

