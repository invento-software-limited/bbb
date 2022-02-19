from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in bbb/__init__.py
from bbb import __version__ as version

setup(
	name="bbb",
	version=version,
	description="bbb",
	author="invento software limited",
	author_email="munim@invento.com.bd",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
