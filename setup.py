import os
import sys

from setuptools import setup
from setuptools import find_packages
from setuptools import Extension

PYPY = hasattr(sys, 'pypy_version_info')
PY312 = sys.version_info[:2] == (3, 12)

def read(fname, here=os.path.dirname(__file__)):
    with open(os.path.join(here, fname), encoding='utf-8') as f:
        return f.read()

README = read('README.rst')
CHANGES = read('CHANGES.rst')

tests_require = [
    'zope.testrunner',
    # nti.testing > ZODB > persistent -> cffi
    # CffI won't build on 3.13 yet; persistent is having trouble on PyPy
    'nti.testing; python_version != "3.13" and platform_python_implementation != "PyPy"',

    # transitive dep of nti.testing, which we don't always have, but need
    # for our emulation
    'zope.schema',
    'pyhamcrest >= 1.10',
    'pyperf',
]

###
# Cython
###

# Based on code from
# http://cython.readthedocs.io/en/latest/src/reference/compilation.html#distributing-cython-modules
def _dummy_cythonize(extensions, **_kwargs):
    for extension in extensions:
        sources = []
        for sfile in extension.sources:
            path, ext = os.path.splitext(sfile)
            if ext in ('.pyx', '.py'):
                ext = '.c'
                sfile = path + ext
            sources.append(sfile)
        extension.sources[:] = sources
    return extensions

try:
    from Cython.Build import cythonize
except ImportError:
    # The .c files had better already exist, as they should in
    # an sdist.
    cythonize = _dummy_cythonize

ext_modules = []

# Modules we want to compile with Cython. These *should* have a parallel
# .pxd file (with a leading _) defining cython attributes.
# They should also have a cython comment at the top giving options,
# and mention that they are compiled with cython on CPython.
# The bottom of the file must call import_c_accel.
# We use the support from Cython 28 to be able to parallel compile
# and cythonize modules to a different name with a leading _.
# This list is derived from the profile of bm_simple_iface
# https://github.com/NextThought/nti.externalization/commit/0bc4733aa8158acd0d23c14de2f9347fb698c040
if not PYPY:
    def _source(m, ext):
        # Yes, always /.
        m = m.replace('.', '/')
        return 'src/perfmetrics/' + m + '.' + ext
    def _py_source(m):
        return _source(m, 'py')
    def _pxd(m):
        return _source(m, 'pxd')
    def _c(m):
        return _source(m, 'c')
    # Each module should list the python name of the
    # modules it cimports from as deps. We'll generate the rest.
    # (Not that this actually appears to do anything right now.)

    for mod_name, deps in (
        ('metric', ()),
    ):
        deps = ([_py_source(mod) for mod in deps]
                + [_pxd(mod) for mod in deps]
                + [_c(mod) for mod in deps])

        source = _py_source(mod_name)
        # 'foo.bar' -> 'foo._bar'
        mod_name_parts = mod_name.rsplit('.', 1)
        mod_name_parts[-1] = '_' + mod_name_parts[-1]
        mod_name = '.'.join(mod_name_parts)


        ext_modules.append(
            Extension(
                'perfmetrics.' + mod_name,
                sources=[source],
                depends=deps,
                define_macros=[('CYTHON_TRACE', '0')],
            ))

    try:
        ext_modules = cythonize(
            ext_modules,
            annotate=True,
            compiler_directives={
                #'linetrace': True,
                'infer_types': True,
                'language_level': '3str',
                'always_allow_keywords': False,
                'nonecheck': False,
            },
        )
    except ValueError:
        # 'invalid literal for int() with base 10: '3str'
        # This is seen when an older version of Cython is installed.
        # It's a bit of a chicken-and-egg, though, because installing
        # from dev-requirements first scans this egg for its requirements
        # before doing any updates.
        import traceback
        traceback.print_exc()
        ext_modules = _dummy_cythonize(ext_modules)

setup(
    name='perfmetrics',
    version='4.1.0',
    author='Shane Hathaway',
    author_email='shane@hathawaymix.org',
    maintainer='Jason Madden',
    maintainer_email='jason@nextthought.com',
    description='Send performance metrics about Python code to Statsd',
    keywords="statsd metrics performance monitoring",
    long_description=README + '\n\n' + CHANGES,
    python_requires=">=3.7",
    # Get strings from https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
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
    ext_modules=ext_modules,
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
            'pyhamcrest',
            'sphinx_rtd_theme',
        ],
    },
    entry_points="""\
    [paste.filter_app_factory]
    statsd = perfmetrics:make_statsd_app
    """,
)
