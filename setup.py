# openfisca-dash-ui -- User interface for OpenFisca
# By: Christophe Benz <christophe.benz@jailbreak.paris>
#
# Copyright (C) 2018 Christophe Benz
# https://github.com/cbenz/openfisca-dash-ui
#
# openfisca-dash-ui is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# openfisca-dash-ui is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Project properties and packaging infos.
"""

import codecs
from os import path

from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='OpenFisca-Dash-UI',
    version='0.1.0',

    description='OpenFisca user interface using Dash',
    long_description=LONG_DESCRIPTION,

    url='https://github.com/cbenz/openfisca-dash-ui',

    author='Christophe Benz',
    author_email='christophe.benz@jailbreak.paris',

    license='AGPLv3',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        'Environment :: Web Environment',
        'Operating System :: POSIX',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Affero General Public License v3',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
    ],

    # What does your project relate to?
    keywords='openfisca dash ui',

    packages=find_packages(),

    setup_requires=[
        'pytest-runner',
    ],

    tests_require=[
        'pytest',
    ],

    install_requires=[
        'dash',
        'dash_core_components',
        'dash_html_components',
        'dash-renderer',
        'plotly',
        'gunicorn',
        'ruamel.yaml',
        'OpenFisca-France >= 21.0, < 30.0',
        'toolz >= 0.9, < 0.10',
    ],

)
