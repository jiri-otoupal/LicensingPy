#!/usr/bin/env python3
"""
Step 1: Generate ECDSA key pair for license signing.

This is the first step in the licensing workflow. Run this to generate
the private and public keys needed for license generation and verification.
"""

import sys
import os

# Add the parent directory to the path so we can import the licensing module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from licensing import LicenseGenerator


def main():
    print("=" * 60)
    print("STEP 1: GENERATING ECDSA KEY PAIR")
    print("=" * 60)
    
    print("\nThis will generate:")
    print("- private_key.txt (for license generation - keep secret!)")
    print("- public_key.txt (for license verification - distribute with app)")
    
    print("\nGenerating ECDSA key pair...")
    
    try:
        # Generate key pair
        private_key, public_key = LicenseGenerator.generate_key_pair()
        
        # Save private key
        with open("private_key.txt", "w") as f:
            f.write(private_key)
        
        # Save public key  
        with open("public_key.txt", "w") as f:
            f.write(public_key)
        
        print("✓ Keys generated successfully!")
        print("\nFiles created:")
        print(f"  private_key.txt ({len(private_key)} characters)")
        print(f"  public_key.txt ({len(public_key)} characters)")
        
        print("\n" + "=" * 60)
        print("IMPORTANT SECURITY NOTES:")
        print("=" * 60)
        print("- NEVER share private_key.txt with anyone")
        print("- Store private_key.txt in a secure location")
        print("- Back up private_key.txt safely")
        print("- Distribute public_key.txt with your application")
        print("- You'll also need a preseed key (secret string)")
        
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Run: python examples/step2_generate_license.py")
        print("2. Run: python examples/step3_verify_license.py")
        
    except Exception as e:
        print(f"Error generating keys: {e}")
        return


if __name__ == "__main__":
    main()

