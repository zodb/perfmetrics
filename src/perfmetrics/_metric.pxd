# definitions for metric.py

import cython

cdef time
cdef MethodType
cdef WeakKeyDictionary
cdef functools
cdef stdrandom

cdef statsd_client
cdef statsd_client_stack
cdef StatsdClientMod
cdef null_client

cdef class _MethodLikeMixin(object):
    pass

cdef class _AbstractMetricImpl(_MethodLikeMixin):
    cdef public bint metric_timing
    cdef public bint metric_count
    cdef public double metric_rate
    cdef  f
    cdef str timing_format
    cdef public __wrapped__
    cdef dict __dict__

    cdef str _compute_stat(self, tuple args)


cdef class _GivenStatMetricImpl(_AbstractMetricImpl):
    cdef readonly str stat_name

cdef class _MethodMetricImpl(_AbstractMetricImpl):

    cdef klass_dict


cdef class Metric(object):
    cdef public double rate
    cdef double start
    cdef public bint method
    cdef public bint count
    cdef public bint timing
    cdef public str stat
    cdef public str timing_format
    cdef random
    cdef dict __dict__
