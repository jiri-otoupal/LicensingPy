#!/usr/bin/env python3
"""
Setup script for the Offline Licensing System.
"""

from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="licensing-py",
    version="1.0.0",
    description="Secure offline licensing system using ECDSA signatures and hardware fingerprinting",
    author="Developer",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'licensing=licensing.cli:cli',
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

