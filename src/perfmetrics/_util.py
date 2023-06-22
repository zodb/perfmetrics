# -*- coding: utf-8 -*-
"""
Helper functions.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

PY3 = sys.version_info[0] >= 3
PYPY = hasattr(sys, 'pypy_version_info')
WIN = sys.platform.startswith("win")
LINUX = sys.platform.startswith('linux')
OSX = sys.platform == 'darwin'


PURE_PYTHON = PYPY or os.getenv('PURE_PYTHON') or os.getenv("PERFMETRICS_PURE_PYTHON")

def import_c_accel(globs, cname):
    """
    Import the C-accelerator for the __name__
    and copy its globals.
    """

    name = globs.get('__name__')

    if not name or name == cname:
        # Do nothing if we're being exec'd as a file (no name)
        # or we're running from the C extension
        return # pragma: no cover


    if not PURE_PYTHON: # pragma: no cover
        import importlib
        import warnings
        with warnings.catch_warnings():
            # Python 3.7 likes to produce
            # "ImportWarning: can't resolve
            #   package from __spec__ or __package__, falling back on
            #   __name__ and __path__"
            # when we load cython compiled files. This is probably a bug in
            # Cython, but it doesn't seem to have any consequences, it's
            # just annoying to see and can mess up our unittests.
            warnings.simplefilter('ignore', ImportWarning)
            mod = importlib.import_module(cname)

        # By adopting the entire __dict__, we get a more accurate
        # __file__ and module repr, plus we don't leak any imported
        # things we no longer need.
        globs.clear()
        globs.update(mod.__dict__)

    if 'import_c_accel' in globs:
        del globs['import_c_accel']
