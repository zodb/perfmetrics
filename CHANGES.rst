=========
 CHANGES
=========

4.1.0 (2024-06-11)
==================

- Add support for Python 3.13.
- Drop support for Python 3.7.
- Drop support for Manylinux 2010 wheels.

4.0.0 (2023-06-22)
==================

- Drop support for obsolete Python versions, including Python 2.7 and
  3.6.
- Add support for Python 3.12.


3.3.0 (2022-09-25)
==================

- Stop accidentally building manylinux wheels with unsafe math
  optimizations.
- Add support for Python 3.11.

NOTE: This will be the last major release to support legacy versions
of Python such as 2.7 and 3.6. Some such legacy versions may not have
binary wheels published for this release.


3.2.0.post0 (2021-09-28)
========================

- Add Windows wheels for 3.9 and 3.10.


3.2.0 (2021-09-28)
==================

- Add support for Python 3.10.

- Drop support for Python 3.5.

- Add aarch64 binary wheels.

3.1.0 (2021-02-04)
==================

- Add support for Python 3.8 and 3.9.
- Move to GitHub Actions from Travis CI.
- Support PyHamcrest 1.10 and later. See `issue 26
  <https://github.com/zodb/perfmetrics/issues/26>`_.
- The ``FakeStatsDClient`` for testing is now always true whether or
  not any observations have been seen, like the normal clients. See
  `issue <https://github.com/zodb/perfmetrics/issues/23>`_.
- Add support for `StatsD sets
  <https://github.com/statsd/statsd/blob/master/docs/metric_types.md#sets>`_,
  counters of unique events. See `PR 30 <https://github.com/zodb/perfmetrics/pull/30>`_.

3.0.0 (2019-09-03)
==================

- Drop support for EOL Python 2.6, 3.2, 3.3 and 3.4.

- Add support for Python 3.5, 3.6, and 3.7.

- Compile the performance-sensitive parts with Cython, leading to a
  10-30% speed improvement. See
  https://github.com/zodb/perfmetrics/issues/17.

- Caution: Metric names are enforced to be native strings (as a result
  of Cython compilation); they've always had to be ASCII-only but
  previously Unicode was allowed on Python 2. This is usually
  automatically the case when used as a decorator. On Python 2 using
  ``from __future__ import unicode_literals`` can cause problems
  (raising TypeError) when manually constructing ``Metric`` objects. A
  quick workaround is to set the environment variable
  ``PERFMETRICS_PURE_PYTHON`` before importing perfmetrics.

- Make decorated functions and methods configurable at runtime, not
  just compile time. See
  https://github.com/zodb/perfmetrics/issues/11.

- Include support for testing applications instrumented with
  perfmetrics in ``perfmetrics.testing``. This was previously released
  externally as ``nti.fakestatsd``. See https://github.com/zodb/perfmetrics/issues/9.

- Read the ``PERFMETRICS_DISABLE_DECORATOR`` environment variable when
  ``perfmetrics`` is imported, and if it is set, make the decorators ``@metric``,
  ``@metricmethod``, ``@Metric(...)`` and ``@MetricMod(...)`` return
  the function unchanged. This can be helpful for certain kinds of
  introspection tests. See https://github.com/zodb/perfmetrics/issues/15

2.0 (2013-12-10)
================

- Added the ``@MetricMod`` decorator, which changes the name of
  metrics in a given context. For example, ``@MetricMod('xyz.%s')``
  adds a prefix.

- Removed the "gauge suffix" feature. It was unnecessarily confusing.

- Timing metrics produced by ``@metric``, ``@metricmethod``, and
  ``@Metric`` now have a ".t" suffix by default to avoid naming
  conflicts.

1.0 (2012-10-09)
================

- Added 'perfmetrics.tween' and 'perfmetrics.wsgi' stats for measuring
  request timing and counts.

0.9.5 (2012-09-22)
==================

- Added an optional Pyramid tween and a similar WSGI filter app
  that sets up the Statsd client for each request.

0.9.4 (2012-09-08)
==================

- Optimized the use of reduced sample rates.

0.9.3 (2012-09-08)
==================

- Support the ``STATSD_URI`` environment variable.

0.9.2 (2012-09-01)
==================

- ``Metric`` can now be used as either a decorator or a context
  manager.

- Made the signature of StatsdClient more like James Socol's
  StatsClient.

0.9.1 (2012-09-01)
==================

- Fixed package metadata.

0.9 (2012-08-31)
================

- Initial release.
