import os
from setuptools import setup, find_packages


def read(fname, here=os.path.dirname(__file__)):
    with open(os.path.join(here, fname)) as f:
        return f.read()

README = read('README.rst')
CHANGES = read('CHANGES.rst')

tests_require = [
    'zope.testrunner',
    'nti.testing',
    'pyhamcrest',
]

setup(
    name='perfmetrics',
    version='3.0.0.dev0',
    author='Shane Hathaway',
    author_email='shane@hathawaymix.org',
    description='Send performance metrics about Python code to Statsd',
    keywords="statsd metrics performance monitoring",
    long_description=README + '\n\n' + CHANGES,
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    # Get strings from https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
    project_urls={
        'Bug Tracker': 'https://github.com/zodb/perfmetrics/issues',
        'Source Code': 'https://github.com/zodb/perfmetrics/',
        'Documentation': 'https://perfmetrics.readthedocs.io',
    },
    license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=True,
    tests_require=tests_require,
    install_requires=[
        'setuptools',
    ],
    extras_require={
        'test': tests_require,
        'docs': [
            'Sphinx >= 2.1.2',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points="""\
    [paste.filter_app_factory]
    statsd = perfmetrics:make_statsd_app
    """,
)
