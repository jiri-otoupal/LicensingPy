"""
Hardware fingerprinting module for license validation.

This module collects various hardware information to create a unique
fingerprint for license binding.
"""

import hashlib
import platform
import socket
import subprocess
import os
import re
from typing import Dict, List, Optional

try:
    import netifaces
except ImportError:
    netifaces = None

try:
    import psutil
except ImportError:
    psutil = None


class HardwareFingerprint:
    """
    Generates hardware fingerprints based on various system characteristics.
    
    Supports multiple fingerprint types:
    - mac: Primary network interface MAC address
    - disk: Disk serial numbers
    - cpu: CPU information
    - system: System UUID and motherboard info
    - composite: Combination of multiple hardware elements
    """
    
    FINGERPRINT_TYPES = ["mac", "disk", "cpu", "system", "composite"]
    
    def __init__(self):
        self._cache = {}
    
    def get_fingerprint(self, fingerprint_type: str = "composite") -> str:
        """
        Generate a hardware fingerprint of the specified type.
        
        Args:
            fingerprint_type: Type of fingerprint to generate
            
        Returns:
            SHA256 hash of the hardware fingerprint
            
        Raises:
            ValueError: If fingerprint_type is not supported
        """
        if fingerprint_type not in self.FINGERPRINT_TYPES:
            raise ValueError(f"Unsupported fingerprint type: {fingerprint_type}")
        
        if fingerprint_type in self._cache:
            return self._cache[fingerprint_type]
        
        if fingerprint_type == "mac":
            data = self._get_mac_addresses()
        elif fingerprint_type == "disk":
            data = self._get_disk_info()
        elif fingerprint_type == "cpu":
            data = self._get_cpu_info()
        elif fingerprint_type == "system":
            data = self._get_system_info()
        elif fingerprint_type == "composite":
            data = self._get_composite_info()
        
        # Create SHA256 hash of the collected data
        fingerprint = hashlib.sha256(str(data).encode('utf-8')).hexdigest()
        self._cache[fingerprint_type] = fingerprint
        
        return fingerprint
    
    def _get_mac_addresses(self) -> List[str]:
        """Get MAC addresses of network interfaces."""
        mac_addresses = []
        
        if netifaces:
            # Use netifaces for better cross-platform support
            for interface in netifaces.interfaces():
                try:
                    addr_info = netifaces.ifaddresses(interface)
                    if netifaces.AF_LINK in addr_info:
                        for link in addr_info[netifaces.AF_LINK]:
                            if 'addr' in link and link['addr'] != '00:00:00:00:00:00':
                                mac_addresses.append(link['addr'].upper())
                except Exception:
                    continue
        
        # Linux-specific fallback using /sys/class/net
        if not mac_addresses and platform.system() == 'Linux':
            try:
                net_dir = '/sys/class/net'
                if os.path.exists(net_dir):
                    for interface in os.listdir(net_dir):
                        if interface == 'lo':  # Skip loopback
                            continue
                        addr_file = os.path.join(net_dir, interface, 'address')
                        if os.path.exists(addr_file):
                            with open(addr_file, 'r') as f:
                                mac = f.read().strip().upper()
                                if mac and mac != '00:00:00:00:00:00':
                                    mac_addresses.append(mac)
            except Exception:
                pass
        
        # Linux command-line fallback
        if not mac_addresses and platform.system() == 'Linux':
            try:
                result = subprocess.run(['ip', 'link', 'show'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse ip link output for MAC addresses
                    for line in result.stdout.split('\n'):
                        if 'link/ether' in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                mac = parts[1].upper()
                                if mac and mac != '00:00:00:00:00:00':
                                    mac_addresses.append(mac)
            except Exception:
                pass
        
        # Fallback method using uuid (works on all platforms)
        if not mac_addresses:
            import uuid
            try:
                mac = hex(uuid.getnode())[2:].upper()
                if len(mac) == 12:
                    mac = ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
                    mac_addresses.append(mac)
            except Exception:
                pass
        
        # Remove duplicates and sort for consistency
        return sorted(list(set(mac_addresses)))
    
    def _get_disk_info(self) -> List[str]:
        """Get disk/storage device information."""
        disk_info = []
        
        if psutil:
            try:
                for partition in psutil.disk_partitions():
                    try:
                        # Get device info
                        device = partition.device
                        disk_info.append(device)
                    except Exception:
                        continue
            except Exception:
                pass
        
        # Add platform-specific disk info
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "diskdrive", "get", "serialnumber"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    for line in lines:
                        serial = line.strip()
                        if serial and serial != "SerialNumber":
                            disk_info.append(serial)
            elif platform.system() == "Linux":
                # Try multiple methods for Linux disk info
                try:
                    # Method 1: lsblk for serial numbers
                    result = subprocess.run(
                        ["lsblk", "-d", "-n", "-o", "SERIAL"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        serials = result.stdout.strip().split('\n')
                        disk_info.extend([s.strip() for s in serials if s.strip() and s.strip() != '-'])
                except Exception:
                    pass
                
                try:
                    # Method 2: Read from /sys/block for device info
                    block_dir = '/sys/block'
                    if os.path.exists(block_dir):
                        for device in os.listdir(block_dir):
                            if device.startswith(('sd', 'hd', 'nvme', 'vd')):  # Common disk prefixes
                                # Try to get serial from /sys/block/device/serial
                                serial_file = os.path.join(block_dir, device, 'serial')
                                if os.path.exists(serial_file):
                                    with open(serial_file, 'r') as f:
                                        serial = f.read().strip()
                                        if serial:
                                            disk_info.append(serial)
                                # Also get device name as fallback
                                disk_info.append(device)
                except Exception:
                    pass
                
                try:
                    # Method 3: hwinfo or lshw fallback (if available)
                    result = subprocess.run(
                        ["lshw", "-class", "disk", "-short"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if '/dev/' in line:
                                parts = line.split()
                                for part in parts:
                                    if part.startswith('/dev/'):
                                        disk_info.append(part.split('/')[-1])
                except Exception:
                    pass
        except Exception:
            pass
        
        return sorted(list(set(disk_info)))
    
    def _get_cpu_info(self) -> Dict[str, str]:
        """Get CPU information."""
        cpu_info = {
            "processor": platform.processor(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0]
        }
        
        if psutil:
            try:
                cpu_info["cpu_count"] = str(psutil.cpu_count(logical=False))
                cpu_info["cpu_count_logical"] = str(psutil.cpu_count(logical=True))
            except Exception:
                pass
        
        # Linux-specific CPU info from /proc/cpuinfo
        if platform.system() == 'Linux':
            try:
                if os.path.exists('/proc/cpuinfo'):
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                        
                    # Extract key CPU information
                    for line in cpuinfo.split('\n'):
                        if line.startswith('model name'):
                            cpu_info["model_name"] = line.split(':', 1)[1].strip()
                        elif line.startswith('cpu family'):
                            cpu_info["cpu_family"] = line.split(':', 1)[1].strip()
                        elif line.startswith('model'):
                            cpu_info["model"] = line.split(':', 1)[1].strip()
                        elif line.startswith('microcode'):
                            cpu_info["microcode"] = line.split(':', 1)[1].strip()
                        elif line.startswith('cpu cores'):
                            cpu_info["cpu_cores"] = line.split(':', 1)[1].strip()
                            
                    # Count processors if not already set
                    if "cpu_count" not in cpu_info:
                        processor_count = cpuinfo.count('processor')
                        if processor_count > 0:
                            cpu_info["cpu_count"] = str(processor_count)
            except Exception:
                pass
        
        # Fallback CPU count using os.cpu_count()
        if "cpu_count" not in cpu_info:
            try:
                cpu_info["cpu_count"] = str(os.cpu_count() or 1)
            except Exception:
                cpu_info["cpu_count"] = "1"
        
        return cpu_info
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system and motherboard information."""
        system_info = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform()
        }
        
        # Try to get system UUID (Windows/Linux)
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "csproduct", "get", "uuid"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        uuid = lines[1].strip()
                        if uuid and uuid != "UUID":
                            system_info["uuid"] = uuid
            elif platform.system() == "Linux":
                # Try multiple methods to get unique system identifiers
                try:
                    # Method 1: DMI product UUID
                    with open("/sys/class/dmi/id/product_uuid", "r") as f:
                        system_info["uuid"] = f.read().strip()
                except Exception:
                    pass
                    
                try:
                    # Method 2: Machine ID (systemd)
                    if os.path.exists("/etc/machine-id"):
                        with open("/etc/machine-id", "r") as f:
                            system_info["machine_id"] = f.read().strip()
                    elif os.path.exists("/var/lib/dbus/machine-id"):
                        with open("/var/lib/dbus/machine-id", "r") as f:
                            system_info["machine_id"] = f.read().strip()
                except Exception:
                    pass
                
                try:
                    # Method 3: DMI system information
                    dmi_fields = {
                        'sys_vendor': '/sys/class/dmi/id/sys_vendor',
                        'product_name': '/sys/class/dmi/id/product_name',
                        'product_version': '/sys/class/dmi/id/product_version',
                        'board_vendor': '/sys/class/dmi/id/board_vendor',
                        'board_name': '/sys/class/dmi/id/board_name',
                        'board_serial': '/sys/class/dmi/id/board_serial',
                        'chassis_serial': '/sys/class/dmi/id/chassis_serial'
                    }
                    
                    for key, path in dmi_fields.items():
                        if os.path.exists(path):
                            try:
                                with open(path, 'r') as f:
                                    value = f.read().strip()
                                    if value and value not in ['None', 'Not Specified', '']:
                                        system_info[key] = value
                            except Exception:
                                pass
                except Exception:
                    pass
                
                try:
                    # Method 4: Try dmidecode command (if available)
                    result = subprocess.run(
                        ["dmidecode", "-s", "system-uuid"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        uuid = result.stdout.strip()
                        if uuid and uuid not in ['Not Specified', 'Not Present']:
                            system_info["dmidecode_uuid"] = uuid
                except Exception:
                    pass
        except Exception:
            pass
        
        return system_info
    
    def _get_composite_info(self) -> Dict[str, any]:
        """Get a composite of all hardware information."""
        return {
            "mac": self._get_mac_addresses(),
            "disk": self._get_disk_info(),
            "cpu": self._get_cpu_info(),
            "system": self._get_system_info()
        }
    
    def get_available_types(self) -> List[str]:
        """Get list of available fingerprint types."""
        return self.FINGERPRINT_TYPES.copy()
    
    def clear_cache(self):
        """Clear the fingerprint cache."""
        self._cache.clear()
    
    def get_platform_capabilities(self) -> Dict[str, bool]:
        """
        Get information about platform-specific capabilities.
        
        Returns:
            Dictionary showing what methods are available on this platform
        """
        capabilities = {
            "platform": platform.system(),
            "netifaces_available": netifaces is not None,
            "psutil_available": psutil is not None,
            "supports_linux_sysfs": platform.system() == 'Linux' and os.path.exists('/sys'),
            "supports_linux_proc": platform.system() == 'Linux' and os.path.exists('/proc'),
            "supports_linux_commands": platform.system() == 'Linux',
            "supports_windows_wmic": platform.system() == 'Windows'
        }
        
        # Test command availability on Linux
        if platform.system() == 'Linux':
            for cmd in ['ip', 'lsblk', 'lshw', 'dmidecode']:
                try:
                    result = subprocess.run([cmd, '--version'], 
                                          capture_output=True, timeout=2)
                    capabilities[f"has_{cmd}_command"] = result.returncode == 0
                except Exception:
                    capabilities[f"has_{cmd}_command"] = False
        
        return capabilities
    
    def test_linux_fallbacks(self) -> Dict[str, str]:
        """
        Test Linux-specific fallback methods.
        Useful for debugging on Linux systems.
        
        Returns:
            Dictionary with test results for each Linux method
        """
        results = {}
        
        if platform.system() != 'Linux':
            return {"error": "This method only works on Linux systems"}
        
        # Test /sys/class/net MAC address reading
        try:
            net_dir = '/sys/class/net'
            if os.path.exists(net_dir):
                interfaces = [f for f in os.listdir(net_dir) if f != 'lo']
                results['sysfs_interfaces'] = f"Found {len(interfaces)} interfaces: {interfaces[:3]}"
            else:
                results['sysfs_interfaces'] = "Not available"
        except Exception as e:
            results['sysfs_interfaces'] = f"Error: {str(e)}"
        
        # Test /proc/cpuinfo reading
        try:
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    content = f.read()
                    cpu_count = content.count('processor')
                    results['proc_cpuinfo'] = f"Found {cpu_count} processors"
            else:
                results['proc_cpuinfo'] = "Not available"
        except Exception as e:
            results['proc_cpuinfo'] = f"Error: {str(e)}"
        
        # Test DMI information
        try:
            dmi_base = '/sys/class/dmi/id'
            if os.path.exists(dmi_base):
                dmi_files = os.listdir(dmi_base)
                results['dmi_info'] = f"Found {len(dmi_files)} DMI files"
            else:
                results['dmi_info'] = "Not available"
        except Exception as e:
            results['dmi_info'] = f"Error: {str(e)}"
        
        # Test command availability
        commands = ['ip', 'lsblk', 'lshw', 'dmidecode']
        available_commands = []
        for cmd in commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, timeout=2)
                if result.returncode == 0:
                    available_commands.append(cmd)
            except Exception:
                pass
        
        results['available_commands'] = f"Available: {available_commands}"
        
        return results

