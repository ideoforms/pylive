#!/usr/bin/env python3

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

    # TODO for me on windows 10 at least, in a fresh python 3.8 venv, i need
    # to pre install cython with: pip install cython
    # or else the `pip install ./` will fail even though 'cython' is also
    # in `install_requires`. test that `./setup.py install` behaves the same
    # way! + try to find workaround so cython gets installed first if not
    # fixable (or either way, really)

    # Since it seems it is not possible to specify "default" values for
    # the keys in "extras_require" (without hacks that would prevent this 
    # `setup.py` from being used to release wheels), I think the best option is
    # to always install pyliblo, even if it is not functional because there is
    # not a working installed liblo library. Then, we just need to make sure we
    # can detect either whether we have pythonosc, or whether the installed
    # pyliblo+liblo is actually working.

    # It does however seem that there is a fairly high bar for pyliblo's build
    # succeeding... I think I was only able to achieve this on MSYS2 on Windows,
    # with a bit of installation of dependencies required.
    install_requires = ['cython', 'pyliblo >= 0.9.1'],
    extras_require={
        'pythonosc': ['python-osc']
    },
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
