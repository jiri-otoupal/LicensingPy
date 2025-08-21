#!/usr/bin/env python3
"""
Main CLI entry point for the Licensing System.

Usage:
    python licensing_cli.py --help
    python licensing_cli.py generate-keys
    python licensing_cli.py generate-license --help
    python licensing_cli.py verify-license --help
"""

if __name__ == '__main__':
    from licensing.cli import cli
    cli()

