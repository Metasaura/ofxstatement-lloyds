#!/usr/bin/python3
"""Setup
"""
from setuptools import find_packages
from distutils.core import setup

version = "0.9.4"

with open("README.rst") as f:
    long_description = f.read()

setup(
    name="ofxstatement-lloyds",
    version=version,
    author="Victoria Lebedeva",
    author_email="victoria@lebedev.lt",
    url="https://github.com/Metasaura/ofxstatement-lloyds",
    description=("Plugin for reading statements of Lloyds UK bank"),
    long_description=long_description,
    license="MIT",
    keywords=["ofx", "banking", "statement", "lloyds"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Utilities",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={
        "ofxstatement": ["lloyds = ofxstatement_lloyds.plugin:LloydsPlugin"]
    },
    install_requires=["ofxstatement"],
    include_package_data=True,
    zip_safe=True,
)
