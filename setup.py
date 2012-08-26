
import sys
from setuptools import setup, find_packages

requires = ['setuptools',
            'decorator',
            ]

if sys.version_info[:2] < (2, 7):
    requires.append('unittest2')

setup(
    name='metrical',
    version='0.1',
    author='Shane Hathaway',
    author_email='shane@hathawaymix.org',
    description='A library for sending software performance metrics '
                'from Python libraries and apps to statsd.',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    test_suite='metrical',
    install_requires=requires)
