# -*- coding: utf-8 -*-
"""
perfmetrics is a library for sending software performance metrics
to statsd.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os


from .clientstack import statsd_client
from .clientstack import set_statsd_client
from .clientstack import client_stack as statsd_client_stack


from .statsd import statsd_client_from_uri
from .statsd import StatsdClient

from .metric import Metric
from .metric import MetricMod

from .pyramid import includeme
from .pyramid import tween
from .wsgi import make_statsd_app

__all__ = [
    'metric',
    'metricmethod',
    'Metric',
    'MetricMod',
    'StatsdClient',
    'set_statsd_client',
    'statsd_client',
    'statsd_client_from_uri',
    'statsd_client_stack',
    # Pyramid
    'includeme',
    'tween',
    # WSGI
    'make_statsd_app',
]

class _DisabledMetricDecorator(Metric):

    def __call__(self, f):
        return f

class _DisabledMetricModDecorator(MetricMod):

    def __call__(self, f):
        return f

if os.environ.get('PERFMETRICS_DISABLE_DECORATOR'):
    Metric = _DisabledMetricDecorator
    MetricMod = _DisabledMetricModDecorator

#: @metric:
metric = Metric()

#: @metricmethod:
metricmethod = Metric(method=True)


_uri = os.environ.get('STATSD_URI')
if _uri:
    set_statsd_client(_uri)  # pragma: no cover
