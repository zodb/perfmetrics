=========
 Testing
=========

``perfmetrics.testing`` provides a testing client for verifying StatsD
metrics emitted by perfmetrics in the context of an instrumented
application.

It's easy to create a new client for use in testing:

.. code-block:: pycon

  >>> from perfmetrics.testing import FakeStatsDClient
  >>> test_client = FakeStatsDClient()

This client exposes the same public interface as
`perfmetrics.statsd.StatsdClient`. For example we can increment
counters, set gauges, etc:

.. code-block:: pycon

  >>> test_client.incr('request_c')
  >>> test_client.gauge('active_sessions', 320)

Unlike `perfmetrics.statsd.StatsdClient`, `~.FakeStatsDClient` simply
tracks the statsd packets that would be sent. This information is
exposed on our ``test_client`` both as the raw statsd packet, and for
convenience this information is also parsed and exposed as `~.Observation`
objects. For complete details see `~.FakeStatsDClient` and `~.Observation`.

.. code-block:: pycon

  >>> test_client.packets
  ['request_c:1|c', 'active_sessions:320|g']
  >>> test_client.observations
  [Observation(name='request_c', value='1', kind='c', sampling_rate=None), Observation(name='active_sessions', value='320', kind='g', sampling_rate=None)]

For validating metrics we provide a set of `PyHamcrest
<https://pypi.org/project/PyHamcrest/>`_ matchers for use in test
assertions:

.. code-block:: pycon

  >>> from hamcrest import assert_that
  >>> from hamcrest import contains_exactly as contains
  >>> from perfmetrics.testing.matchers import is_observation
  >>> from perfmetrics.testing.matchers import is_gauge

We can use both strings and numbers (or any matcher) for the value:

  >>> assert_that(test_client,
  ...     contains(is_observation('c', 'request_c', '1'),
  ...              is_gauge('active_sessions', 320)))
  >>> assert_that(test_client,
  ...     contains(is_observation('c', 'request_c', '1'),
  ...              is_gauge('active_sessions', '320')))
  >>> from hamcrest import is_
  >>> assert_that(test_client,
  ...     contains(is_observation('c', 'request_c', '1'),
  ...              is_gauge('active_sessions', is_('320'))))

If the matching fails, we get a descriptive error:

  >>> assert_that(test_client,
  ...     contains(is_gauge('request_c', '1'),
  ...              is_gauge('active_sessions', '320')))
  Traceback (most recent call last):
  ...
  AssertionError:
  Expected: a sequence containing [(an instance of Observation and (an object with a property 'kind' matching 'g' and an object with a property 'name' matching 'request_c' and an object with a property 'value' matching '1')), (an instance of Observation and (an object with a property 'kind' matching 'g' and an object with a property 'name' matching 'active_sessions' and an object with a property 'value' matching '320'))]
         but: item 0: was Observation(name='request_c', value='1', kind='c', sampling_rate=None)


Reference
=========

``perfmetrics.testing``
-----------------------
.. currentmodule:: perfmetrics.testing

.. automodule:: perfmetrics.testing.client
   :special-members: __len__, __iter___
.. automodule:: perfmetrics.testing.observation

``perfmetrics.testing.matchers``
--------------------------------
.. automodule:: perfmetrics.testing.matchers
