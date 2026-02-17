from setuptools import setup, find_packages

setup(
    name="cloudops",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.40.0",
        "boto3>=1.34.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "kubernetes>=29.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cloudops=cloudops.cli:main",
        ],
    },
    python_requires=">=3.9",
    author="CloudOps Team",
    description="AI-Assisted Cloud Operations Control Plane",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
