from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in attendance/__init__.py
from attendance import __version__ as version

setup(
	name="attendance",
	version=version,
	description="This app wiil provide the attendance moddule.",
	author="Invento",
	author_email="hell0@invento.com.bd",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
