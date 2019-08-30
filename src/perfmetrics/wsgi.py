# -*- coding: utf-8 -*-
"""
Optional WSGI integration.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .statsd import statsd_client_from_uri
from .clientstack import client_stack as statsd_client_stack
from .metric import Metric

def make_statsd_app(nextapp, _globals=None, statsd_uri=''):
    """
    Create a WSGI filter app that sets up Statsd for each request.

    If no *statsd_uri* is given, returns *nextapp* unchanged.

    .. versionchanged:: 3.0

       The returned app callable makes the statsd client that it
       uses available at the ``statsd_client`` attribute.
    """
    if not statsd_uri:
        # Disabled.
        return nextapp

    client = statsd_client_from_uri(statsd_uri)

    nextapp = Metric('perfmetrics.wsgi')(nextapp)
    def app(environ, start_response):
        statsd_client_stack.push(client)
        try:
            return nextapp(environ, start_response)
        finally:
            statsd_client_stack.pop()

    app.statsd_client = client

    return app
