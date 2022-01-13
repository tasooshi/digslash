#!/usr/bin/env python

from distutils.core import setup

import digslash


setup(
    name=digslash.NAME,
    version=digslash.__version__,
    description='A site mapping and enumeration tool for Web applications analysis',
    author='tasooshi',
    author_email='tasooshi@pm.me',
    license='MIT License',
    url='https://github.com/tasooshi/digslash',
    packages=['digslash'],
    install_requires=(
        'aiohttp==3.8.1',
        'beautifulsoup4==4.10.0',
    ),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
    ]
)
