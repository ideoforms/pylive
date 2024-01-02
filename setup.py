#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name = 'pylive',
    version = '0.4.0',
    description = 'Python remote control of Ableton Live',
    long_description = open("README.md", "r").read(),
    long_description_content_type = "text/markdown",
    author = 'Daniel Jones',
    author_email = 'dan-pylive@erase.net',
    url = 'https://github.com/ideoforms/pylive',
    packages = find_packages(),
    install_requires = ['python-osc'],
    keywords = ('sound', 'music', 'ableton', 'osc'),
    classifiers = [
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Artistic Software',
        'Topic :: Communications',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers'
    ],
    setup_requires = ['pytest-runner'],
    tests_require = ['pytest', 'pytest-timeout']
)
