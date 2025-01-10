#!/usr/bin/env python
"""
responses
=========

A utility library for mocking out the `requests` Python library.

:copyright: (c) 2015 David Cramer
:license: Apache 2.0
"""

from setuptools import setup

install_requires = [
    "requests>=2.30.0,<3.0",
    "urllib3>=1.25.10,<3.0",
    "pyyaml",
]

tests_require = [
    "pytest>=7.0.0",
    "coverage >= 6.0.0",
    "pytest-cov",
    "pytest-asyncio",
    "pytest-httpserver",
    "flake8",
    "types-PyYAML",
    "types-requests",
    "mypy",
    # for check of different parsers in recorder
    "tomli; python_version < '3.11'",
    "tomli-w",
]

extras_require = {"tests": tests_require}

setup(
    name="responses",
    version="0.25.5",
    author="David Cramer",
    description="A utility library for mocking out the `requests` Python library.",
    url="https://github.com/getsentry/responses",
    project_urls={
        "Bug Tracker": "https://github.com/getsentry/responses/issues",
        "Changes": "https://github.com/getsentry/responses/blob/master/CHANGES",
        "Documentation": "https://github.com/getsentry/responses/blob/master/README.rst",
        "Source Code": "https://github.com/getsentry/responses",
    },
    license="Apache 2.0",
    long_description=open("README.rst", encoding="utf-8").read(),
    long_description_content_type="text/x-rst",
    packages=["responses"],
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development",
    ],
)
