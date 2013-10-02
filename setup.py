#!/usr/bin/env python

from setuptools import setup

setup(
	name = 'pylive',
	version = '0.1.1',
	description = 'Python remote control of Ableton Live',
	author = 'Daniel Jones',
	author_email = 'dan-pylive@erase.net',
	url = 'https://github.com/ideoforms/pylive',
	packages = ['live'],
	install_requires = ['pyOSC >= 0.3b0'],
	keywords = ('sound', 'music', 'ableton', 'osc'),
	classifiers = [
		'Topic :: Multimedia :: Sound/Audio',
		'Topic :: Artistic Software',
		'Topic :: Communications',
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers'
	]
)
