"""Editable-install support for the loan_engine package.

The engine source lives in ``src/loan_engine``. With this file present you can run::

    .venv/Scripts/pip install -e .     # Windows
    pip install -e .                   # Linux/macOS

and then ``import loan_engine`` from anywhere. The venv already has the
package importable via PYTHONPATH=src, which the documented commands use.
"""

from setuptools import find_packages, setup

setup(
    name="loan-engine",
    version="0.1.0",
    description="India Personal Loan Eligibility & Recommendation Engine (rule-based, no ML)",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=[
        "pandas>=2.2,<3",
        "pydantic>=2.7,<3",
    ],
    extras_require={
        "ui": ["streamlit>=1.40,<2"],
        "dev": ["pytest>=8.0,<9"],
    },
)
