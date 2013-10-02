#!/usr/bin/env python

from distutils.core import setup

setup(
	name = 'pylive',
	version = '0.1.0',
	description = 'Python remote control of Ableton Live',
	author = 'Daniel Jones',
	author_email = 'dan-pylive@erase.net',
	url = 'https://github.com/ideoforms/pylive',
	packages = ['live'],
	requires = ['pyOSC (>=0.3)'],
	keywords = ('sound', 'music', 'ableton', 'osc'),
	classifiers = [
		'Topic :: Multimedia :: Sound/Audio',
		'Topic :: Artistic Software',
		'Topic :: Communications',
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers'
	]
)
