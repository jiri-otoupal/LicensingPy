#!/usr/bin/env python3
"""
Demo script for auto license verification functionality.

This script demonstrates how to use the auto_verify_licenses function
to automatically find and verify all licenses in the current directory.
"""

import json
from pprint import pprint
from licensing import auto_verify_licenses

def print_separator(title):
    """Print a formatted separator."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def main():
    print_separator("AUTO LICENSE VERIFICATION DEMO")
    
    print("Searching for license files and key files in current directory...")
    print("This will automatically:")
    print("  • Find license files (license.txt, licenses.txt, *.license, etc.)")
    print("  • Find key files (keys.json, public_key.txt, *.pub, etc.)")
    print("  • Load public key and preseed from key files")
    print("  • Verify each license found (one per line in files)")
    print("  • Provide detailed results and summary")
    
    try:
        # Run auto verification
        results = auto_verify_licenses()
        
        # Check for errors
        if "error" in results:
            print(f"\n❌ Error: {results['error']}")
            return
        
        print_separator("FILES FOUND")
        print(f"License files found: {len(results['license_files_found'])}")
        for file in results['license_files_found']:
            print(f"  • {file}")
        
        print(f"\nKey files found: {len(results['key_files_found'])}")
        for file in results['key_files_found']:
            print(f"  • {file}")
        
        print_separator("VERIFICATION SUMMARY")
        summary = results['summary']
        print(f"Total licenses processed: {summary['total_licenses']}")
        print(f"✅ Valid licenses: {summary['valid_count']}")
        print(f"❌ Invalid licenses: {summary['invalid_count']}")
        print(f"⏰ Expired licenses: {summary['expired_count']}")
        print(f"🖥️  Hardware mismatch: {summary['hardware_mismatch_count']}")
        
        if results['valid_licenses']:
            print_separator("VALID LICENSES")
            for i, license_data in enumerate(results['valid_licenses'], 1):
                metadata = license_data.get('_metadata', {})
                print(f"\n📄 License {i}:")
                print(f"   File: {metadata.get('file', 'Unknown')}")
                print(f"   Line: {metadata.get('line_number', 'Unknown')}")
                print(f"   App: {license_data.get('app_name', 'Not specified')}")
                print(f"   Expires: {license_data.get('expiry', 'Unknown')}")
                print(f"   Hardware Type: {license_data.get('hw_type', 'Unknown')}")
                print(f"   Issued: {license_data.get('issued', 'Unknown')}")
        
        if results['invalid_licenses']:
            print_separator("INVALID LICENSES")
            for i, invalid_license in enumerate(results['invalid_licenses'], 1):
                print(f"\n❌ Invalid License {i}:")
                print(f"   File: {invalid_license.get('file', 'Unknown')}")
                print(f"   Line: {invalid_license.get('line_number', 'Unknown')}")
                print(f"   Error Type: {invalid_license.get('error_type', 'Unknown')}")
                print(f"   Error: {invalid_license.get('error_message', 'Unknown')}")
        
        print_separator("VERIFICATION COMPLETE")
        
        # Save detailed results to file
        with open('license_verification_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("📁 Detailed results saved to: license_verification_results.json")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Make sure you have:")
        print("  • License files in the current directory")
        print("  • Key files (keys.json or public_key.txt) with valid keys")
        print("  • Proper preseed key (in key file or LICENSE_PRESEED env var)")

def demo_with_options():
    """Demo showing different verification options."""
    print_separator("VERIFICATION OPTIONS DEMO")
    
    print("1. Skip hardware verification (useful for testing on different machines):")
    results = auto_verify_licenses(check_hardware=False)
    if "error" not in results:
        print(f"   Valid licenses (no hardware check): {results['summary']['valid_count']}")
    
    print("\n2. Skip expiry verification (useful for testing with expired licenses):")
    results = auto_verify_licenses(check_expiry=False)
    if "error" not in results:
        print(f"   Valid licenses (no expiry check): {results['summary']['valid_count']}")
    
    print("\n3. Skip both hardware and expiry (signature only):")
    results = auto_verify_licenses(check_hardware=False, check_expiry=False)
    if "error" not in results:
        print(f"   Valid licenses (signature only): {results['summary']['valid_count']}")

if __name__ == "__main__":
    try:
        main()
        demo_with_options()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
