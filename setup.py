#!/usr/bin/env python

from setuptools import setup

#------------------------------------------------------------------------
# Generate a PyPI-friendly RST file from our markdown README.
#------------------------------------------------------------------------
try:
	import pypandoc
	long_description = pypandoc.convert('README.md', 'rst')
except:
	long_description = None

setup(
	name = 'pylive',
	version = '0.1.4',
	description = 'Python remote control of Ableton Live',
	long_description = long_description,
	author = 'Daniel Jones',
	author_email = 'dan-pylive@erase.net',
	url = 'https://github.com/ideoforms/pylive',
	packages = ['live'],
	install_requires = ['pyliblo >= 0.9.1'],
	keywords = ('sound', 'music', 'ableton', 'osc'),
	classifiers = [
		'Topic :: Multimedia :: Sound/Audio',
		'Topic :: Artistic Software',
		'Topic :: Communications',
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers'
	]
)
