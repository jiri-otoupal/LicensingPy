"""
Command Line Interface for the Licensing System.

This module provides a beautiful CLI for generating keys, creating licenses,
and verifying licenses using the Click library with Rich styling.
"""

import os
import json
import click
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.syntax import Syntax
from rich.tree import Tree
from rich.prompt import Confirm
from rich import box
from rich.align import Align

from .license_generator import LicenseGenerator
from .license_manager import LicenseManager
from .preseed_generator import PreseedGenerator
from .exceptions import LicenseError, LicenseExpiredError, LicenseInvalidError, HardwareMismatchError

# Initialize Rich console
console = Console()

def print_success(message: str):
    """Print a success message with rich styling."""
    console.print(f"✅ {message}", style="bold green")

def print_error(message: str):
    """Print an error message with rich styling."""
    console.print(f"❌ {message}", style="bold red")

def print_warning(message: str):
    """Print a warning message with rich styling."""
    console.print(f"⚠️  {message}", style="bold yellow")

def print_info(message: str):
    """Print an info message with rich styling."""
    console.print(f"ℹ️  {message}", style="bold blue")

def print_header(title: str, subtitle: str = None):
    """Print a styled header."""
    if subtitle:
        text = Text()
        text.append(title, style="bold magenta")
        text.append(f"\n{subtitle}", style="dim")
        console.print(Panel(Align.center(text), box=box.DOUBLE))
    else:
        console.print(Panel(Align.center(Text(title, style="bold magenta")), box=box.DOUBLE))


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🔐 Offline Licensing System CLI
    
    A secure offline licensing solution using ECDSA signatures and hardware fingerprinting.
    """
    # Print beautiful welcome message
    console.print()
    print_header("🔐 Offline Licensing System", "Secure • Beautiful • Professional")
    console.print()


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file to save keys (optional)')
@click.option('--format', 'output_format', type=click.Choice(['json', 'text']), default='text', 
              help='Output format for keys')
def generate_keys(output: Optional[str], output_format: str):
    """Generate a new ECDSA key pair for license signing."""
    print_header("🔑 Key Generation", "Generating secure ECDSA key pair")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Generating ECDSA key pair...", total=None)
            private_key, public_key = LicenseGenerator.generate_key_pair()
            progress.update(task, completed=True)
        
        print_success("Key pair generated successfully!")
        
        # Create info table
        info_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        info_table.add_row("🔐 Algorithm", "ECDSA P-256 (secp256r1)")
        info_table.add_row("⏰ Generated", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info_table.add_row("📁 Format", output_format.upper())
        if output:
            info_table.add_row("💾 Output", output)
        
        console.print(Panel(info_table, title="[bold cyan]Key Information[/bold cyan]"))
        
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
                print_success(f"Keys saved to {output}")
            else:
                console.print("\n[bold cyan]Key Data (JSON):[/bold cyan]")
                console.print(Syntax(json.dumps(keys_data, indent=2), "json", theme="monokai"))
        else:
            # Display keys in a formatted table
            keys_table = Table(show_header=False, box=box.HEAVY_HEAD, border_style="green")
            keys_table.add_column("Type", style="bold cyan", width=15)
            keys_table.add_column("Key", style="dim", overflow="fold")
            
            keys_table.add_row("🔑 Private Key", f"[red]{private_key}[/red]")
            keys_table.add_row("🔓 Public Key", f"[green]{public_key}[/green]")
            
            console.print(Panel(keys_table, title="[bold green]Generated Keys[/bold green]"))
            
            # Security notice
            security_panel = Panel(
                "[red]⚠️  SECURITY IMPORTANT:[/red]\n"
                "• Store the [red]private key[/red] securely and never share it\n"
                "• The [green]public key[/green] should be distributed with your application\n"
                "• Generate a preseed file for additional security\n"
                "• Keep backups of both keys in a secure location",
                title="[bold red]🔒 Security Notice[/bold red]",
                border_style="red"
            )
            console.print(security_panel)
            
            if output:
                key_text = f"""ECDSA Key Pair Generated
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
                with open(output, 'w') as f:
                    f.write(key_text)
                print_success(f"Keys saved to {output}")
                
    except Exception as e:
        print_error(f"Key generation failed: {e}")
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
    print_header("🌱 Preseed Generation", f"Creating secure preseed file with {length} characters")
    
    try:
        # Prepare metadata
        metadata = {}
        if project_name:
            metadata['project_name'] = project_name
        if description:
            metadata['description'] = description
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Generating secure preseed...", total=None)
            secret_content = PreseedGenerator.create_preseed_file(
                output_path=output,
                metadata=metadata,
                length=length
            )
            progress.update(task, completed=True)
        
        print_success("Preseed file generated successfully!")
        
        # Show file info
        info = PreseedGenerator.validate_preseed_file(output)
        
        # Create info table
        info_table = Table(show_header=False, box=box.ROUNDED, border_style="green")
        info_table.add_row("📁 File", output)
        info_table.add_row("🔐 Secret Length", f"{length} characters")
        info_table.add_row("💾 File Size", f"{info['file_size']} bytes")
        info_table.add_row("⏰ Generated", info['generated_at'])
        
        if metadata:
            metadata_text = ", ".join(f"[cyan]{k}[/cyan]: {v}" for k, v in metadata.items())
            info_table.add_row("📋 Metadata", metadata_text)
        
        console.print(Panel(info_table, title="[bold green]Preseed Information[/bold green]"))
        
        # Security notice
        security_panel = Panel(
            "[red]🔐 SECURITY CRITICAL:[/red]\n"
            f"• Keep [cyan]{output}[/cyan] secure and confidential\n"
            f"• Do [red]NOT[/red] commit [cyan]{output}[/cyan] to version control\n"
            f"• Create secure backups of [cyan]{output}[/cyan]\n"
            "• The secret content will be hashed before use in licenses\n"
            "• Loss of this file means you cannot verify existing licenses",
            title="[bold red]🔒 Security Notice[/bold red]",
            border_style="red"
        )
        console.print(security_panel)
        
        # Next steps
        next_steps = Tree("📋 [bold cyan]Next Steps[/bold cyan]")
        next_steps.add("1. [green]Generate keys:[/green] [dim]licensing generate-keys[/dim]")
        next_steps.add(f"2. [green]Generate license:[/green] [dim]licensing generate-license --preseed-file {output}[/dim]")
        next_steps.add(f"3. [green]Verify license:[/green] [dim]licensing verify-license --preseed-file {output}[/dim]")
        
        console.print(Panel(next_steps, title="[bold blue]Workflow Guide[/bold blue]", border_style="blue"))
        
    except Exception as e:
        print_error(f"Preseed generation failed: {e}")
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
    target_mode = "Target Hardware" if target_hardware else "Current Machine"
    print_header("📄 License Generation", f"Creating license for {target_mode}")
    
    try:
        # Load private key (from file or direct input)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task1 = progress.add_task("Loading private key...", total=None)
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
            progress.update(task1, completed=True)
            
            # Load preseed from file
            task2 = progress.add_task("Loading preseed...", total=None)
            preseed = PreseedGenerator.load_preseed_from_file(preseed_file)
            progress.update(task2, completed=True)
        
        print_success(f"Loaded preseed from: {preseed_file}")
        
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Generating license...", total=None)
            
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
                print_success("License generated for target hardware")
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
                print_success("License generated for current machine")
                print_info(f"Hardware fingerprint ({fingerprint_type}): {current_fp[:16]}...")
            
            progress.update(task, completed=True)
        
        license_info = generator.parse_license(license_string)
        
        # Create license details table
        details_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        details_table.add_row("🆔 Fingerprint Type", license_info['hw_type'])
        details_table.add_row("⏳ Expiry Date", license_info['expiry'])
        details_table.add_row("📅 Issued Date", license_info['issued'])
        
        if license_info.get('component_name'):
            details_table.add_row("🧩 Component", license_info['component_name'])
        
        # Additional data is merged directly into the license, so show app-specific fields
        app_fields = {k: v for k, v in license_info.items() 
                     if k not in ['version', 'hw_type', 'hw_info', 'expiry', 'issued', 'preseed_hash', 'signature', 'component_name']}
        
        if app_fields:
            for key, value in app_fields.items():
                icon = "📱" if key == "app_name" else "🔖" if key == "app_version" else "👤" if key == "customer" else "📋"
                details_table.add_row(f"{icon} {key.replace('_', ' ').title()}", str(value))
        
        console.print(Panel(details_table, title="[bold cyan]License Details[/bold cyan]"))
        
        # Show license string
        license_panel = Panel(
            Syntax(license_string, "json", theme="monokai", word_wrap=True),
            title="[bold green]Generated License[/bold green]",
            border_style="green"
        )
        console.print(license_panel)
        
        if output:
            license_data = {
                "license": license_string,
                "info": license_info,
                "generated_at": datetime.now().isoformat()
            }
            with open(output, 'w') as f:
                json.dump(license_data, f, indent=2)
            print_success(f"License saved to {output}")
            
    except Exception as e:
        print_error(f"License generation failed: {e}")
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
    verification_mode = []
    if skip_hardware:
        verification_mode.append("Skip Hardware")
    if skip_expiry:
        verification_mode.append("Skip Expiry")
    mode_text = f" ({', '.join(verification_mode)})" if verification_mode else ""
    
    print_header("🔍 License Verification", f"Validating license authenticity{mode_text}")
    
    try:
        # Load components with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task1 = progress.add_task("Loading public key...", total=None)
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
            progress.update(task1, completed=True)
            
            task2 = progress.add_task("Loading preseed...", total=None)
            preseed = PreseedGenerator.load_preseed_from_file(preseed_file)
            progress.update(task2, completed=True)
            
            task3 = progress.add_task("Loading license...", total=None)
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
            progress.update(task3, completed=True)
        
        print_success(f"Loaded preseed from: {preseed_file}")
        
        # Create license manager
        manager = LicenseManager(public_key_b64, preseed)
        
        # Get license info first
        try:
            license_info = manager.get_license_info(license_string)
            
            # Create license info table
            info_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
            
            # Core license fields
            info_table.add_row("🆔 License Type", license_info.get('hw_type', 'Unknown'))
            info_table.add_row("📅 Issued", license_info.get('issued', 'Unknown'))
            info_table.add_row("⏳ Expires", license_info.get('expiry', 'Unknown'))
            
            if license_info.get('component_name'):
                info_table.add_row("🧩 Component", license_info['component_name'])
            
            # Additional data
            if license_info.get('app_name'):
                info_table.add_row("📱 Application", license_info['app_name'])
            if license_info.get('app_version'):
                info_table.add_row("🔖 Version", license_info['app_version'])
            if license_info.get('customer'):
                info_table.add_row("👤 Customer", license_info['customer'])
                
            console.print(Panel(info_table, title="[bold cyan]License Information[/bold cyan]"))
            
            # Show days until expiry with color coding
            days_until_expiry = manager.get_days_until_expiry(license_string)
            if days_until_expiry is not None:
                if days_until_expiry > 30:
                    print_success(f"License expires in {days_until_expiry} days")
                elif days_until_expiry > 7:
                    print_warning(f"License expires in {days_until_expiry} days")
                elif days_until_expiry > 0:
                    print_error(f"License expires in {days_until_expiry} days")
                elif days_until_expiry == 0:
                    print_error("License expires today")
                else:
                    print_error(f"License expired {abs(days_until_expiry)} days ago")
            
        except Exception as e:
            print_error(f"License parsing failed: {e}")
            return
        
        # Perform full verification with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Verifying license...", total=None)
            
            try:
                verified_license = manager.verify_license(
                    license_string, 
                    check_hardware=not skip_hardware, 
                    check_expiry=not skip_expiry
                )
                progress.update(task, completed=True)
                
                # Success - create verification results table
                results_table = Table(show_header=False, box=box.HEAVY_HEAD, border_style="green")
                results_table.add_column("Check", style="bold cyan", width=20)
                results_table.add_column("Status", style="bold green", width=15)
                results_table.add_column("Details", style="dim")
                
                results_table.add_row("🔐 Signature", "✅ PASSED", "Cryptographic signature is valid")
                
                if not skip_hardware:
                    results_table.add_row("🖥️  Hardware", "✅ MATCHED", "Fingerprint matches current machine")
                else:
                    results_table.add_row("🖥️  Hardware", "⏭️  SKIPPED", "Hardware check was bypassed")
                
                if not skip_expiry:
                    results_table.add_row("⏰ Expiry", "✅ VALID", "License has not expired")
                else:
                    results_table.add_row("⏰ Expiry", "⏭️  SKIPPED", "Expiry check was bypassed")
                
                results_table.add_row("🌱 Preseed", "✅ PASSED", "Preseed hash verification passed")
                
                console.print(Panel(results_table, title="[bold green]🎉 LICENSE IS VALID AND ACTIVE[/bold green]", border_style="green"))
                
            except LicenseExpiredError as e:
                progress.update(task, completed=True)
                error_panel = Panel(
                    f"[red]❌ LICENSE IS EXPIRED[/red]\n\n"
                    f"Details: {str(e)}\n\n"
                    f"The license has passed its expiration date and is no longer valid.",
                    title="[bold red]🚫 Verification Failed[/bold red]",
                    border_style="red"
                )
                console.print(error_panel)
                
            except HardwareMismatchError as e:
                progress.update(task, completed=True)
                error_panel = Panel(
                    f"[red]❌ HARDWARE FINGERPRINT MISMATCH[/red]\n\n"
                    f"Details: {str(e)}\n\n"
                    f"This license was generated for a different machine. The hardware "
                    f"fingerprint does not match the current system.",
                    title="[bold red]🚫 Verification Failed[/bold red]",
                    border_style="red"
                )
                console.print(error_panel)
                
            except LicenseInvalidError as e:
                progress.update(task, completed=True)
                error_panel = Panel(
                    f"[red]❌ LICENSE IS INVALID[/red]\n\n"
                    f"Details: {str(e)}\n\n"
                    f"The license structure or cryptographic signature is invalid.",
                    title="[bold red]🚫 Verification Failed[/bold red]",
                    border_style="red"
                )
                console.print(error_panel)
        
        if verbose:
            # Test individual components
            test_table = Table(show_header=True, box=box.ROUNDED, border_style="blue")
            test_table.add_column("Test", style="cyan")
            test_table.add_column("Result", style="bold")
            test_table.add_column("Description", style="dim")
            
            test_table.add_row(
                "Signature Only",
                "✅ VALID" if manager.is_valid(license_string, check_hardware=False, check_expiry=False) else "❌ INVALID",
                "Basic cryptographic verification"
            )
            test_table.add_row(
                "Signature + Hardware",
                "✅ VALID" if manager.is_valid(license_string, check_hardware=True, check_expiry=False) else "❌ INVALID", 
                "Signature plus hardware fingerprint"
            )
            test_table.add_row(
                "Signature + Expiry",
                "✅ VALID" if manager.is_valid(license_string, check_hardware=False, check_expiry=True) else "❌ INVALID",
                "Signature plus expiration check"
            )
            test_table.add_row(
                "Full Verification",
                "✅ VALID" if manager.is_valid(license_string, check_hardware=True, check_expiry=True) else "❌ INVALID",
                "Complete validation (recommended)"
            )
            
            console.print(Panel(test_table, title="[bold blue]🧪 Component Test Results[/bold blue]", border_style="blue"))
            
    except Exception as e:
        print_error(f"Verification failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--fingerprint-type', '-f', 
              type=click.Choice(['mac', 'disk', 'cpu', 'system', 'composite']),
              default='composite', help='Hardware fingerprint type')
@click.option('--output', '-o', type=click.Path(), help='Output file to save hardware info')
def get_hardware_info(fingerprint_type: str, output: Optional[str]):
    """Get current machine's hardware information for license generation."""
    print_header("🖥️  Hardware Analysis", f"Collecting {fingerprint_type} fingerprint information")
    
    try:
        from .hardware_fingerprint import HardwareFingerprint
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Analyzing hardware...", total=None)
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
            
            progress.update(task, completed=True)
        
        print_success("Hardware analysis completed!")
        
        # Create fingerprint info table
        fp_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        fp_table.add_row("🆔 Fingerprint Type", fingerprint_type.upper())
        fp_table.add_row("🔗 Hash", fingerprint)
        fp_table.add_row("⏰ Collected", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        console.print(Panel(fp_table, title="[bold cyan]Hardware Fingerprint[/bold cyan]"))
        
        # Create hardware details table
        details_table = Table(show_header=True, box=box.ROUNDED, border_style="green")
        details_table.add_column("Component", style="cyan")
        details_table.add_column("Value", style="green", overflow="fold")
        
        def format_hardware_data(data, parent_key=""):
            for key, value in data.items():
                display_key = f"{parent_key}.{key}" if parent_key else key
                if isinstance(value, dict):
                    format_hardware_data(value, display_key)
                elif isinstance(value, list):
                    if len(value) <= 3:
                        details_table.add_row(display_key, ", ".join(str(v) for v in value))
                    else:
                        details_table.add_row(display_key, f"{len(value)} items: {', '.join(str(v) for v in value[:3])}...")
                else:
                    details_table.add_row(display_key, str(value))
        
        format_hardware_data(hw_data)
        console.print(Panel(details_table, title="[bold green]Hardware Details[/bold green]"))
        
        result = {
            "hw_type": fingerprint_type,
            "fingerprint_hash": fingerprint,
            "hardware_data": hw_data,
            "collected_at": datetime.now().isoformat()
        }
        
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            print_success(f"Hardware info saved to {output}")
            
            # Show usage instructions
            usage_panel = Panel(
                f"[cyan]📋 Next Steps:[/cyan]\n\n"
                f"Use this file for remote license generation:\n"
                f"[dim]licensing generate-license --target-hardware {output} ...[/dim]\n\n"
                f"This allows generating licenses for machines without direct access.",
                title="[bold blue]Usage Instructions[/bold blue]",
                border_style="blue"
            )
            console.print(usage_panel)
        else:
            # Show raw data with syntax highlighting
            console.print("\n[bold cyan]Raw Hardware Data:[/bold cyan]")
            console.print(Syntax(json.dumps(hw_data, indent=2), "json", theme="monokai"))
            
    except Exception as e:
        print_error(f"Hardware analysis failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
def demo():
    """Run a complete licensing workflow demonstration."""
    print_header("🎭 Live Demo", "Complete licensing workflow demonstration")
    
    try:
        # Create a progress bar for the entire demo
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            console=console
        ) as progress:
            demo_task = progress.add_task("Demo Progress", total=4)
            
            # Step 1: Generate keys
            step_task = progress.add_task("1. Generating ECDSA key pair...", total=None)
            private_key, public_key = LicenseGenerator.generate_key_pair()
            progress.update(step_task, completed=True)
            progress.update(demo_task, advance=1)
            print_success("ECDSA key pair generated")
            
            # Step 2: Generate preseed file
            step_task = progress.add_task("2. Creating secure preseed...", total=None)
            preseed = PreseedGenerator.create_preseed_file(
                output_path="demo_preseed.json",
                metadata={"project_name": "Demo", "description": "Demo preseed file"},
                length=64
            )
            preseed_hash = PreseedGenerator.load_preseed_from_file("demo_preseed.json")
            progress.update(step_task, completed=True)
            progress.update(demo_task, advance=1)
            print_success("Preseed file created: demo_preseed.json")
            
            # Step 3: Generate license
            step_task = progress.add_task("3. Generating license...", total=None)
            expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            generator = LicenseGenerator(private_key, preseed_hash)
            license_string = generator.generate_license(
                expiry_date=expiry_date,
                fingerprint_type="composite",
                additional_data={"app_name": "DemoApp", "app_version": "1.0.0"},
                component_name="DemoComponent"
            )
            progress.update(step_task, completed=True)
            progress.update(demo_task, advance=1)
            print_success(f"License generated (expires: {expiry_date})")
            
            # Step 4: Verify license
            step_task = progress.add_task("4. Verifying license...", total=None)
            manager = LicenseManager(public_key, preseed_hash)
            verified_license = manager.verify_license(license_string)
            progress.update(step_task, completed=True)
            progress.update(demo_task, advance=1)
            print_success("License verification passed")
        
        # Demo results
        console.print("\n")
        
        # Create demo results table
        results_table = Table(show_header=False, box=box.HEAVY_HEAD, border_style="green")
        results_table.add_row("✅ Step 1", "ECDSA Key Pair", "P-256 curve keys generated")
        results_table.add_row("✅ Step 2", "Preseed File", "64-character secure seed created")
        results_table.add_row("✅ Step 3", "License Generation", f"Valid until {expiry_date}")
        results_table.add_row("✅ Step 4", "License Verification", "Signature and hardware validated")
        
        console.print(Panel(results_table, title="[bold green]🎉 Demo Completed Successfully![/bold green]", border_style="green"))
        
        # Show generated license
        license_panel = Panel(
            Syntax(license_string, "json", theme="monokai", word_wrap=True),
            title="[bold cyan]Generated Demo License[/bold cyan]",
            border_style="cyan"
        )
        console.print(license_panel)
        
        # Next steps tree
        next_steps = Tree("🚀 [bold magenta]Try These Commands[/bold magenta]")
        
        verify_branch = next_steps.add("🔍 [green]Verify License[/green]")
        verify_branch.add("[dim]licensing verify-license -k '<public_key>' -p demo_preseed.json -l '<license>' -v[/dim]")
        
        generate_branch = next_steps.add("📄 [green]Generate New License[/green]")
        generate_branch.add("[dim]licensing generate-license -k '<private_key>' -p demo_preseed.json[/dim]")
        
        hardware_branch = next_steps.add("🖥️  [green]Check Hardware[/green]")
        hardware_branch.add("[dim]licensing get-hardware-info -f composite[/dim]")
        
        console.print(Panel(next_steps, title="[bold blue]What's Next?[/bold blue]", border_style="blue"))
        
        # Pro tip
        tip_panel = Panel(
            "[yellow]💡 Pro Tip:[/yellow] Use [cyan]--verbose[/cyan] flag with verify-license for detailed analysis!\n"
            "[yellow]🔒 Security:[/yellow] In production, keep private keys and preseed files secure!",
            title="[bold yellow]Tips & Best Practices[/bold yellow]",
            border_style="yellow"
        )
        console.print(tip_panel)
        
    except Exception as e:
        print_error(f"Demo failed: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()
