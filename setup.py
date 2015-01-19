#!/usr/bin/env python
"""
responses
=========

A utility library for mocking out the `requests` Python library.

:copyright: (c) 2013 Dropbox, Inc.
"""

from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

setup_requires = []

if 'test' in sys.argv:
    setup_requires.append('pytest')

install_requires = [
    'requests',
    'cookies',
    'mock',
    'six',
]

tests_require = [
    'pytest',
    'pytest-cov',
    'flake8',
]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['test_responses.py']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='responses',
    version='0.3.1',
    author='David Cramer',
    description=(
        'A utility library for mocking out the `requests` Python library.'
    ),
    long_description=open('README.rst').read(),
    py_modules=['responses'],
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
    },
    tests_require=tests_require,
    setup_requires=setup_requires,
    cmdclass={'test': PyTest},
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
