
from Cython.Distutils import build_ext
from setuptools.extension import Extension
from setuptools import setup, find_packages
import sys

requires = ['setuptools',
            'decorator',
            ]

ext_modules = [Extension('metrical._cimpl', ['src/metrical/_cimpl.pyx'])]

if sys.version_info[:2] < (2, 7):
    requires.append('unittest2')

setup(
    name='metrical',
    version='0.1',
    author='Shane Hathaway',
    author_email='shane@hathawaymix.org',
    cmdclass={'build_ext': build_ext},
    description='A library for sending software performance metrics '
                'from Python libraries and apps to statsd.',
    ext_modules = ext_modules,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    test_suite='metrical',
    install_requires=requires)
