#!/usr/bin/env python

# Copyright 2017 Martin Olejar
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import pyfdt
from setuptools import setup

if sys.version_info[0] == 2:
    sys.exit('Sorry, Python 2.x is not supported')

setup(
    name='pyfdt',
    version=pyfdt.__version__,
    license='Apache 2.0',
    author='Martin Olejar',
    author_email='martin.olejar@gmail.com',
    url='https://github.com/molejar/pyFDT',
    platforms="Mac OSX, Windows, Linux",
    description='Open Source library for manipulating with Device Tree image',
    install_requires=['click>=5.0'],
    packages=['pyfdt'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Utilities'
    ],
    entry_points={
        'console_scripts': [
            'pydtc = pyfdt.tool:main'
        ],
    }
)
