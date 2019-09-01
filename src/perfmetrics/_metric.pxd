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
    cpdef public bint metric_timing
    cpdef public bint metric_count
    cpdef public double metric_rate
    cdef  f
    cdef str timing_format
    cpdef public __wrapped__
    cdef dict __dict__

    cdef str _compute_stat(self, tuple args)


cdef class _GivenStatMetricImpl(_AbstractMetricImpl):
    cdef readonly str stat_name

cdef class _MethodMetricImpl(_AbstractMetricImpl):

    cdef klass_dict


cdef class Metric(object):
    cpdef public double rate
    cdef  double start
    cpdef public bint method
    cpdef public bint count
    cpdef public bint timing
    cpdef public str stat
    cpdef public str timing_format
    cdef random
    cdef dict __dict__
