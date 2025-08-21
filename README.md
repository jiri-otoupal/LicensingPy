# 🔐 Offline Licensing System for Python

A secure offline licensing solution using ECDSA signatures, hardware fingerprinting, and component-based security.

## ✨ Features

- 🔒 **ECDSA Digital Signatures** - Cryptographically secure license verification
- 🖥️ **Hardware Fingerprinting** - Bind licenses to specific machines
- 🧩 **Component-Based Licensing** - Separate licenses for different modules
- 📁 **Secure Preseed System** - File-based secret management with hashing
- 🌐 **Offline Operation** - No internet connection required
- 🛡️ **Tamper Resistant** - Licenses cannot be modified or forged
- ⚡ **Auto-Verification** - Automatic license discovery and validation
- 🖱️ **CLI Tools** - Complete command-line interface

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start Guide

### Step 1: Generate Preseed File

The preseed file contains secret content that secures your licenses:

```bash
python -m licensing.cli generate-preseed --project-name "MyAwesomeApp" --description "Production preseed for MyApp" --output my_app_preseed.json
```

**Output:**
```
✓ Preseed file generated: my_app_preseed.json
✓ Secret length: 64 characters
✓ File size: 285 bytes

🔐 SECURITY NOTES:
   • Keep my_app_preseed.json secure and confidential
   • Do NOT commit my_app_preseed.json to version control
   • Back up my_app_preseed.json safely
```

### Step 2: Generate Cryptographic Keys

```bash
python -m licensing.cli generate-keys --format json --output my_app_keys.json
```

**Output:**
```
✓ Key pair generated successfully
✓ Keys saved to my_app_keys.json

🔐 SECURITY NOTES:
- Keep the private key secure and confidential
- The public key can be distributed with your application
```

### Step 3: Generate a License

```bash
python -m licensing.cli generate-license --private-key my_app_keys.json --preseed-file my_app_preseed.json --app-name "MyAwesomeApp" --version "2.1.0" --component-name "CoreEngine" --customer "Acme Corporation" --expires "2025-12-31" --output customer_license.txt
```

**Output:**
```
✓ Loaded preseed from: my_app_preseed.json
Generating license (expires: 2025-12-31)...
Hardware fingerprint (composite): 4e120bb4a65e...

License generated successfully!
License Details:
   Fingerprint Type: composite
   Expiry Date: 2025-12-31
   Component Name: CoreEngine
   App Name: MyAwesomeApp
   App Version: 2.1.0
   Customer: Acme Corporation

✓ License saved to: customer_license.txt
```

### Step 4: Verify the License

```bash
python -m licensing.cli verify-license --public-key my_app_keys.json --preseed-file my_app_preseed.json --license customer_license.txt --verbose
```

**Output:**
```
✓ Loaded preseed from: my_app_preseed.json
✓ Loaded license from: customer_license.txt

LICENSE IS VALID AND ACTIVE
✓ Signature verification: PASSED
✓ Hardware fingerprint: MATCHED
✓ License expiry: NOT EXPIRED
✓ Component verification: PASSED
```

## 💻 Using in Your Python Code

### Basic License Verification

```python
from licensing import LicenseManager, PreseedGenerator

# Load your keys and preseed
def load_app_credentials():
    """Load your app's licensing credentials."""
    import json
    
    # Load public key
    with open('my_app_keys.json', 'r') as f:
        keys = json.load(f)
        public_key = keys['public_key']
    
    # Load and hash preseed
    preseed_hash = PreseedGenerator.load_preseed_from_file('my_app_preseed.json')
    
    return public_key, preseed_hash

# Verify a single license
def verify_license(license_string):
    """Verify a license string."""
    try:
        public_key, preseed_hash = load_app_credentials()
        manager = LicenseManager(public_key, preseed_hash)
        
        # Verify the license
        license_data = manager.verify_license(license_string)
        
        print("✅ License is valid!")
        print(f"App: {license_data.get('app_name')}")
        print(f"Component: {license_data.get('component_name')}")
        print(f"Customer: {license_data.get('customer')}")
        print(f"Expires: {license_data.get('expiry')}")
        
        return True
        
    except Exception as e:
        print(f"❌ License verification failed: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Load license from file
    with open('customer_license.txt', 'r') as f:
        license_string = f.read().strip()
    
    if verify_license(license_string):
        print("🎉 Application can start!")
    else:
        print("🚫 Application access denied!")
```

### Auto-Discovery License Verification

```python
from licensing import auto_verify_licenses

def check_all_licenses():
    """Automatically find and verify all licenses in current directory."""
    
    # Auto-discover and verify licenses
    results = auto_verify_licenses()
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return False
    
    summary = results['summary']
    print(f"📊 License Summary:")
    print(f"   Total found: {summary['total_licenses']}")
    print(f"   ✅ Valid: {summary['valid_count']}")
    print(f"   ❌ Invalid: {summary['invalid_count']}")
    print(f"   ⏰ Expired: {summary['expired_count']}")
    
    # Show valid licenses
    for license_data in results['valid_licenses']:
        print(f"\n📄 Valid License:")
        print(f"   App: {license_data.get('app_name', 'N/A')}")
        print(f"   Component: {license_data.get('component_name', 'N/A')}")
        print(f"   Customer: {license_data.get('customer', 'N/A')}")
        print(f"   Expires: {license_data.get('expiry', 'N/A')}")
    
    return summary['valid_count'] > 0

# Example usage
if __name__ == "__main__":
    if check_all_licenses():
        print("🎉 Valid licenses found - application authorized!")
    else:
        print("🚫 No valid licenses found - access denied!")
```

### Component-Specific License Checking

```python
from licensing import LicenseManager, PreseedGenerator

class ComponentLicenseManager:
    """Manage licenses for different application components."""
    
    def __init__(self, public_key_file, preseed_file):
        # Load credentials
        import json
        with open(public_key_file, 'r') as f:
            keys = json.load(f)
            self.public_key = keys['public_key']
        
        self.preseed_hash = PreseedGenerator.load_preseed_from_file(preseed_file)
        self.manager = LicenseManager(self.public_key, self.preseed_hash)
        
        # Cache for verified licenses
        self.verified_components = {}
    
    def verify_component_license(self, license_file, required_component):
        """Verify license for a specific component."""
        
        # Check cache first
        if required_component in self.verified_components:
            return self.verified_components[required_component]
        
        try:
            # Load license
            with open(license_file, 'r') as f:
                license_string = f.read().strip()
            
            # Verify license
            license_data = self.manager.verify_license(license_string)
            
            # Check component match
            license_component = license_data.get('component_name', '')
            if license_component != required_component:
                print(f"❌ Component mismatch: need '{required_component}', got '{license_component}'")
                return False
            
            # Cache successful verification
            self.verified_components[required_component] = license_data
            
            print(f"✅ Component '{required_component}' licensed to: {license_data.get('customer')}")
            return True
            
        except Exception as e:
            print(f"❌ Component '{required_component}' license verification failed: {e}")
            return False
    
    def require_license(self, component_name):
        """Decorator to require license for a component."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.verify_component_license('license.txt', component_name):
                    raise PermissionError(f"No valid license for component '{component_name}'")
                return func(*args, **kwargs)
            return wrapper
        return decorator

# Example usage
license_manager = ComponentLicenseManager('my_app_keys.json', 'my_app_preseed.json')

@license_manager.require_license('DatabaseEngine')
def access_database():
    """This function requires a valid DatabaseEngine license."""
    print("🗄️ Accessing database with licensed engine...")
    # Your database code here

@license_manager.require_license('ReportGenerator')  
def generate_reports():
    """This function requires a valid ReportGenerator license."""
    print("📊 Generating reports with licensed engine...")
    # Your reporting code here

# Use the licensed functions
try:
    access_database()      # Requires DatabaseEngine license
    generate_reports()     # Requires ReportGenerator license
except PermissionError as e:
    print(f"🚫 Access denied: {e}")
```

### Advanced License Validation

```python
from licensing import LicenseManager, PreseedGenerator
from datetime import datetime, timedelta

def advanced_license_check(license_file, preseed_file, public_key_file):
    """Advanced license validation with detailed reporting."""
    
    try:
        # Load credentials
        import json
        with open(public_key_file, 'r') as f:
            keys = json.load(f)
            public_key = keys['public_key']
        
        preseed_hash = PreseedGenerator.load_preseed_from_file(preseed_file)
        manager = LicenseManager(public_key, preseed_hash)
        
        # Load license
        with open(license_file, 'r') as f:
            license_string = f.read().strip()
        
        # Get license info without full validation
        license_info = manager.get_license_info(license_string)
        
        print("📋 License Information:")
        print(f"   App: {license_info.get('app_name', 'N/A')}")
        print(f"   Version: {license_info.get('app_version', 'N/A')}")
        print(f"   Component: {license_info.get('component_name', 'N/A')}")
        print(f"   Customer: {license_info.get('customer', 'N/A')}")
        print(f"   Issued: {license_info.get('issued', 'N/A')}")
        print(f"   Expires: {license_info.get('expiry', 'N/A')}")
        
        # Check expiry details
        days_left = manager.get_days_until_expiry(license_string)
        if days_left is not None:
            if days_left > 0:
                print(f"   ⏰ Days remaining: {days_left}")
                if days_left <= 30:
                    print("   ⚠️  License expiring soon!")
            else:
                print(f"   💀 License expired {abs(days_left)} days ago")
        
        # Show status details
        status = license_info.get('status', {})
        print(f"\n🔍 Verification Status:")
        print(f"   Signature: {'✅ VALID' if not status.get('signature_invalid') else '❌ INVALID'}")
        print(f"   Hardware: {'✅ MATCH' if status.get('hardware_matches') else '❌ MISMATCH'}")
        print(f"   Expiry: {'✅ ACTIVE' if not status.get('is_expired') else '❌ EXPIRED'}")
        print(f"   Preseed: {'✅ VALID' if status.get('preseed_valid') else '❌ INVALID'}")
        
        # Attempt full verification
        print(f"\n🛡️ Full Verification:")
        try:
            verified_license = manager.verify_license(license_string)
            print("✅ LICENSE IS FULLY VALID AND ACTIVE")
            return True
        except Exception as e:
            print(f"❌ Full verification failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ License check failed: {e}")
        return False

# Example usage
if __name__ == "__main__":
    is_valid = advanced_license_check(
        license_file='customer_license.txt',
        preseed_file='my_app_preseed.json', 
        public_key_file='my_app_keys.json'
    )
    
    if is_valid:
        print("\n🎉 Application startup authorized!")
    else:
        print("\n🚫 Application startup denied!")
```

## 🛠️ CLI Reference

### Generate Preseed File
```bash
python -m licensing.cli generate-preseed [OPTIONS]

Options:
  -o, --output PATH     Output file (default: preseed.json)
  -l, --length INTEGER  Secret length in characters (default: 64)
  --project-name TEXT   Project name for metadata
  --description TEXT    Description for metadata
```

### Generate Keys
```bash
python -m licensing.cli generate-keys [OPTIONS]

Options:
  -o, --output PATH           Output file for keys
  --format [json|text]        Output format (default: text)
```

### Generate License
```bash
python -m licensing.cli generate-license [OPTIONS]

Required:
  -k, --private-key PATH      Private key file
  -p, --preseed-file PATH     Preseed file

Options:
  -e, --expires TEXT          Expiry date (YYYY-MM-DD) or days (30d)
  -f, --fingerprint-type      Hardware fingerprint type
  -t, --target-hardware PATH  Generate for specific hardware
  --app-name TEXT             Application name
  --version TEXT              Application version  
  --customer TEXT             Customer name
  -c, --component-name TEXT   Component/module name
  -o, --output PATH           Output license file
```

### Verify License
```bash
python -m licensing.cli verify-license [OPTIONS]

Required:
  -k, --public-key PATH       Public key file
  -p, --preseed-file PATH     Preseed file
  -l, --license PATH          License file or string

Options:
  --skip-hardware             Skip hardware verification
  --skip-expiry               Skip expiry verification
  -v, --verbose               Show detailed information
```

### Demo Workflow
```bash
python -m licensing.cli demo
```

## 📁 File Structure

After following the quick start guide, you'll have:

```
your_project/
├── my_app_preseed.json     # Secret preseed file (keep secure!)
├── my_app_keys.json        # Public/private keys
├── customer_license.txt    # Generated license
└── your_application.py     # Your app with license verification
```

## 🔒 Security Best Practices

### 1. Preseed File Security
- ✅ **Keep preseed files secure** - treat like passwords
- ✅ **Never commit to version control** - add to .gitignore
- ✅ **Back up safely** - store in secure location
- ✅ **Use different preseeds** for different products/versions

### 2. Key Management
- ✅ **Private keys** - Keep secret, use for license generation only
- ✅ **Public keys** - Can be distributed with your application
- ✅ **Separate environments** - Different keys for dev/staging/prod

### 3. License Distribution
- ✅ **Unique licenses** - Generate separate license for each customer
- ✅ **Component isolation** - Use different component names for modules
- ✅ **Expiry dates** - Set appropriate expiration dates
- ✅ **Hardware binding** - Bind to customer's specific hardware

### 4. Application Integration
- ✅ **Fail securely** - Deny access if license verification fails
- ✅ **Cache verification** - Avoid re-verifying same license repeatedly
- ✅ **Component separation** - Check licenses for specific features
- ✅ **User feedback** - Provide clear messages for license issues

## 🆘 Troubleshooting

### License Verification Fails

**Hardware Mismatch:**
```bash
# Skip hardware check for testing
python -m licensing.cli verify-license --skip-hardware ...
```

**License Expired:**
```bash
# Check expiry date
python -m licensing.cli verify-license --verbose ...
```

**Invalid Signature:**
- Ensure you're using the correct preseed file
- Verify the public key matches the private key used for generation

### Auto-Discovery Issues

**No licenses found:**
- Ensure license files are in current directory
- Check file naming: `license.txt`, `*.license`, etc.

**No keys found:**
- Ensure key files are present: `keys.json`, `public_key.txt`, etc.

## 📞 Support

For issues and questions:
1. Check this README for common solutions
2. Review the example code above
3. Test with the demo command: `python -m licensing.cli demo`
4. Verify your file structure and permissions

## 🎯 Example Project Structure

```python
# main.py - Your application entry point
from licensing import LicenseManager, PreseedGenerator

def startup_license_check():
    """Check license before starting application."""
    try:
        # Load credentials
        import json
        with open('app_keys.json', 'r') as f:
            public_key = json.load(f)['public_key']
        
        preseed_hash = PreseedGenerator.load_preseed_from_file('app_preseed.json')
        manager = LicenseManager(public_key, preseed_hash)
        
        # Verify license
        with open('license.txt', 'r') as f:
            license_string = f.read().strip()
        
        license_data = manager.verify_license(license_string)
        
        print(f"✅ Licensed to: {license_data.get('customer')}")
        print(f"📱 App: {license_data.get('app_name')} v{license_data.get('app_version')}")
        print(f"🧩 Component: {license_data.get('component_name')}")
        
        return True
        
    except Exception as e:
        print(f"❌ License verification failed: {e}")
        return False

if __name__ == "__main__":
    if startup_license_check():
        print("🚀 Starting application...")
        # Your application code here
    else:
        print("🚫 Application startup denied - invalid license")
        exit(1)
```

---

**🎉 You're now ready to integrate secure offline licensing into your Python applications!**