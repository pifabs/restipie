# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in restipie/__init__.py
from restipie import __version__ as version

setup(
	name='restipie',
	version=version,
	description='Create ReSTful apis on top of frappe',
	author='palanskiheji',
	author_email='hejipalanski@yahoo.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
