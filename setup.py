from setuptools import setup, find_packages

setup(
    name="documentcheckertool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gradio>=3.50.2",
        "pydantic>=2.5.2",
        "pytest>=8.0.0",
        "pytest-cov>=4.1.0",
        "pytest-asyncio>=0.23.5",
    ],
    python_requires=">=3.8",
) 