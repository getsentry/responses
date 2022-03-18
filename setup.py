#!/usr/bin/env python
"""
responses
=========

A utility library for mocking out the `requests` Python library.

:copyright: (c) 2015 David Cramer
:license: Apache 2.0
"""

import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

setup_requires = []

if "test" in sys.argv:
    setup_requires.append("pytest")

install_requires = [
    "requests>=2.0,<3.0",
    "urllib3>=1.25.10",
]

tests_require = [
    "pytest>=7.0.0",
    "coverage >= 6.0.0",
    "pytest-cov",
    "pytest-asyncio",
    "pytest-localserver",
    "flake8",
    "types-mock",
    "types-requests",
    "mypy",
]

extras_require = {"tests": tests_require}


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["test_responses.py"]
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="responses",
    version="0.20.0",
    author="David Cramer",
    description=("A utility library for mocking out the `requests` Python library."),
    url="https://github.com/getsentry/responses",
    license="Apache 2.0",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    packages=["responses"],
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=tests_require,
    setup_requires=setup_requires,
    cmdclass={"test": PyTest},
    package_data={"responses": ["py.typed", "__init__.pyi"]},
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development",
    ],
)
