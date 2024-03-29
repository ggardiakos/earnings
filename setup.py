#!/usr/bin/env python
"""The setup script."""

from setuptools import setup, find_packages

requirements = []

test_requirements = [
    'pytest>=3',
]

setup(
    author="Or Shem Tov",
    author_email='or@quaniful.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description=
    "An options trading strategy that sells strangles before earnings announcements.",
    install_requires=requirements,
    license="MIT license",
    long_description=None,
    include_package_data=True,
    keywords='earnings',
    name='earnings',
    packages=find_packages(include=['earnings', 'earnings.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/oriesh/earnings',
    version='0.1.0',
    zip_safe=False,
)
