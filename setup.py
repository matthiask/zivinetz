#!/usr/bin/env python

import os

from setuptools import find_packages, setup


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="zivinetz",
    version="0.1.0",
    description="App for managing civil service drudges.",
    long_description=read("README.rst"),
    author="Matthias Kestenholz",
    author_email="mk@406.ch",
    url="http://github.com/matthiask/zivinetz/",
    license="BSD License",
    platforms=["OS Independent"],
    packages=find_packages(exclude=[]),
    package_data={
        "": ["*.html", "*.txt"],
        "zivinetz": [
            "data/*.*",
            "locale/*/*/*.*",
            "static/zivinetz/*.*",
            "static/zivinetz/*/*.*",
            "templates/*.*",
            "templates/*/*.*",
            "templates/*/*/*.*",
            "templates/*/*/*/*.*",
        ],
    },
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    zip_safe=False,
    install_requires=[
        "schwifty",
        "Pillow",
        "pypdf>=3.0",
        "towel",
        "towel-foundation",
        "openpyxl>=3,<3.1",
    ],
)
