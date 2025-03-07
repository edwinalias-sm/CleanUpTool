#! python
""" Shim file for editable installs (with 'pip -e')

A pyproject.toml and setup.cfg is the standard for python packaging, so please go and edit those
rather than adding things to this file.

Please see https://packaging.python.org/tutorials/packaging-projects/ for more information.

This file is _only_ a shim.
"""
import setuptools

if __name__ == "__main__":
    setuptools.setup()
