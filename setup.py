#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'pylive',
    version = '0.2.1',
    description = 'Python remote control of Ableton Live',
    long_description = open("README.md", "r").read(),
    long_description_content_type = "text/markdown",
    author = 'Daniel Jones',
    author_email = 'dan-pylive@erase.net',
    url = 'https://github.com/ideoforms/pylive',
    packages = ['live'],
    install_requires = ['cython', 'pyliblo >= 0.9.1'],
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
