# -*- coding: utf-8 -*-
"""
Benchmarks for metrics.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pyperf import Runner
from pyperf import perf_counter

from perfmetrics import metric
from perfmetrics import metricmethod
from perfmetrics import set_statsd_client
from perfmetrics import Metric
from perfmetrics.statsd import null_client

metricsampled_1 = Metric(rate=0.1)
metricsampled_9 = Metric(rate=0.999)

INNER_LOOPS = 1000

@metric
def func_with_metric():
    pass

@metricsampled_1
def func_with_metricsampled_1():
    pass

@metricsampled_9
def func_with_metricsampled_99():
    pass

def func_without_metric():
    pass

class AClass(object):

    @metricmethod
    def method_with_metric(self):
        pass

    def method_without_metric(self):
        pass


def _bench_call_func(loops, f):
    count = range(loops * INNER_LOOPS)
    t0 = perf_counter()
    for _ in count:
        f()
    t1 = perf_counter()
    return t1 - t0

##
# These four measure the overhead when there is no client installed
# First two are baselines.
##

def bench_a_call_func_without_metric(loops):
    return _bench_call_func(loops, func_without_metric)

def bench_a_call_method_without_metric(loops):
    return _bench_call_func(loops, AClass().method_without_metric)


def bench_call_func_with_metric(loops):
    return _bench_call_func(loops, func_with_metric)

def bench_call_method_with_metric(loops):
    return _bench_call_func(loops, AClass().method_with_metric)


##
# This measures the overhead of a trivial client
##

def _bench_call_func_with_client(loops,
                                 f=func_with_metric,
                                 client=null_client):
    set_statsd_client(client)
    result = _bench_call_func(loops, f)
    set_statsd_client(None)
    return result

def bench_call_func_with_null_client(loops):
    return _bench_call_func_with_client(loops)

##
# This measures the sampling overhead.
# It also uses a trivial client so we're not
# dependent on the order of tests.
##
def bench_call_sampled_1_func_with_null_client(loops):
    return _bench_call_func_with_client(loops, func_with_metricsampled_1, null_client)

def bench_call_sampled_99_func_with_null_client(loops):
    return _bench_call_func_with_client(loops, func_with_metricsampled_99, null_client)


##
# This measures actually sending the UDP packet
##
def bench_call_func_with_udp_client(loops):
    return _bench_call_func_with_client(
        loops,
        func_with_metric,
        'statsd://localhost:8125'
    )

def main():
    runner = Runner()
    for name, func in sorted([
            item for item in globals().items()
            if item[0].startswith('bench_')
    ]):
        runner.bench_time_func(name, func, inner_loops=INNER_LOOPS)


if __name__ == '__main__':
    main()
