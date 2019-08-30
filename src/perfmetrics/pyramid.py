# -*- coding: utf-8 -*-
"""
Optional pyramid integration.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .statsd import statsd_client_from_uri
from .clientstack import client_stack as statsd_client_stack
from .metric import Metric

logger = __import__('logging').getLogger(__name__)

def includeme(config):
    """Pyramid configuration hook: activate the perfmetrics tween.

    A statsd_uri should be in the settings.
    """
    if config.registry.settings.get('statsd_uri'):
        config.add_tween('perfmetrics.tween')


def tween(handler, registry):
    """Pyramid tween that sets up a Statsd client for each request.
    """
    uri = registry.settings['statsd_uri']
    client = statsd_client_from_uri(uri)

    handler = Metric('perfmetrics.tween')(handler)
    def handle(request):
        statsd_client_stack.push(client)
        try:
            return handler(request)
        finally:
            statsd_client_stack.pop()

    return handle
