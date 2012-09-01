
from setuptools import setup, find_packages
import os
import sys

requires = ['setuptools']

if sys.version_info[:2] < (2, 7):
    requires.append('unittest2')

here = os.path.dirname(__file__)
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

setup(
    name='perfmetrics',
    version='0.9',
    author='Shane Hathaway',
    author_email='shane@hathawaymix.org',
    description='Send performance metrics about Python code to Statsd',
    long_description=README + '\n\n' + CHANGES,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    test_suite='perfmetrics',
    install_requires=requires)
