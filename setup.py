
from setuptools import setup, find_packages
import sys

requires = ['setuptools']

if sys.version_info[:2] < (2, 7):
    requires.append('unittest2')

setup(
    name='perfmetrics',
    version='0.9',
    author='Shane Hathaway',
    author_email='shane@hathawaymix.org',
    description='A library for sending software performance metrics '
                'from Python libraries and apps to statsd.',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    test_suite='perfmetrics',
    install_requires=requires)
