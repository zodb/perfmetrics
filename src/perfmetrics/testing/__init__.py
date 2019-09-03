#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for testing that code is instrumented as expected.
"""
from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

__all__ = [
    'FakeStatsDClient',
    'Observation',
    'OBSERVATION_KIND_COUNTER',
    'OBSERVATION_KIND_GAUGE',
    'OBSERVATION_KIND_SET',
    'OBSERVATION_KIND_TIMER',
]

from .client import FakeStatsDClient
from .observation import Observation
from .observation import OBSERVATION_KIND_COUNTER
from .observation import OBSERVATION_KIND_GAUGE
from .observation import OBSERVATION_KIND_SET
from .observation import OBSERVATION_KIND_TIMER
