"""
Setup configuration for the ArcGIS client package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
else:
    requirements = []

# Separate dev dependencies
dev_requirements = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.1",
    "pytest-asyncio>=0.21.1",
    "black>=23.7.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.5.0",
    "pylint>=2.17.5",
    "bandit>=1.7.5",
    "safety>=2.3.5",
    "pre-commit>=3.3.3",
]

setup(
    name="arcgis-client",
    version="1.0.0",
    author="GIS Development Team",
    author_email="dev@example.com",
    description="Production-grade ArcGIS Feature Service client with compliance checking and session management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/arcgis-client",
    packages=find_packages(include=["src", "src.*"]),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "arcgis-client=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
