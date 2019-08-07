from setuptools import setup, find_packages
import os

requires = ['setuptools']

here = os.path.dirname(__file__)
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

setup(name='perfmetrics',
      version='2.0',
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
                   "License :: Repoze Public License",
                   "Topic :: System :: Monitoring",
                   ],
      url="https://github.com/hathawsh/perfmetrics",
      license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require=requires + ['nose'],
      test_suite="nose.collector",
      install_requires=requires,
      entry_points="""\
      [paste.filter_app_factory]
      statsd = perfmetrics:make_statsd_app
      """,
      )
