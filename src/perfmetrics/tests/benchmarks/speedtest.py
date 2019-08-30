
from perfmetrics import metric
from perfmetrics import set_statsd_client
from timeit import timeit


@metric
def func_with_metric():
    pass


def func_without_metric():
    pass


def main():
    t = timeit('f()', 'from __main__ import func_without_metric as f',
               number=1000)
    print('%f' % t)
    t = timeit('f()', 'from __main__ import func_with_metric as f',
               number=1000)
    print('%f' % t)

    set_statsd_client('statsd://localhost:8125')

    t = timeit('f()', 'from __main__ import func_with_metric as f',
               number=1000)
    print('%f' % t)

    from cProfile import runctx
    d = {'_range': range(10000), 'func_with_metric': func_with_metric}
    result = runctx('for _ in _range: func_with_metric()', d, d)
    print(result)


if __name__ == '__main__':
    main()
