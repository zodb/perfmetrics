import os
from setuptools import setup, find_packages

requires = ['setuptools']


def read(fname, here=os.path.dirname(__file__)):
    with open(os.path.join(here, fname)) as f:
        return f.read()

README = read('README.rst')
CHANGES = read('CHANGES.rst')

setup(name='perfmetrics',
      version='3.0.0.dev0',
      author='Shane Hathaway',
      author_email='shane@hathawaymix.org',
      description='Send performance metrics about Python code to Statsd',
      long_description=README + '\n\n' + CHANGES,
      python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
      # Get strings from https://pypi.org/pypi?%3Aaction=list_classifiers
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Developers",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: 3",
                   "Programming Language :: Python :: 3.5",
                   "Programming Language :: Python :: 3.6",
                   "Programming Language :: Python :: 3.7",
                   "Programming Language :: Python :: Implementation :: CPython",
                   "Programming Language :: Python :: Implementation :: PyPy",
                   "License :: Repoze Public License",
                   "Topic :: System :: Monitoring",
                   ],
      url="https://github.com/zodb/perfmetrics",
      license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=True,
      tests_require=requires + ['nose'],
      test_suite="nose.collector",
      install_requires=requires,
      entry_points="""\
      [paste.filter_app_factory]
      statsd = perfmetrics:make_statsd_app
      """,
      )
