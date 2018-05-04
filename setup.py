#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from setuptools import setup
from setuptools import find_packages



project_name='hx_util'

def get_version(*file_paths):
    """Retrieves the version from [your_package]/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version(project_name, "__init__.py")


with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'bs4',
    'lxml',
    'pdfrw',
    'unicodecsv',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name=project_name,
    version=version,
    description="batch tools for edx course exports",
    long_description=readme,
    author="Colin Fredericks",
    author_email='colin_fredericks@harvard.edu',
    url='https://github.com/Colin_Fredericks/' + project_name,
    packages=find_packages(exclude=['tests*']),
    entry_points={
        'console_scripts': [
            '{}={}.HXLiveTools:main'.format(project_name, project_name),
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='hx edx course_export ' + project_name,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
