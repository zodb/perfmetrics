
from perfmetrics import Metric
from perfmetrics import set_statsd_client


@Metric(rate=0.001)
def myfunction():
    """Do something that might be expensive"""


class MyClass(object):
    @Metric(rate=0.001, method=True)
    def mymethod(self):
        """Do some other possibly expensive thing"""


try:
    xrange
except NameError:
    xrange = range  # Python 3


set_statsd_client('statsd://localhost:8125')
for i in xrange(1000000):
    myfunction()
    MyClass().mymethod()
