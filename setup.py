from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in attendance_sync/__init__.py
from attendance_sync import __version__ as version

setup(
	name="attendance_sync",
	version=version,
	description="This is for syncing attendance.",
	author="Invento",
	author_email="hello@invento.com.bd",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
