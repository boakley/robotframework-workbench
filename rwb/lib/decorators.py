'''A collection of sometimes-useful decorators'''
def timeit(func):
    import time
    def _timeit(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        import sys; sys.stdout.flush()
        return res
    return _timeit

def cached_property(func):
    '''A cached property. 

    The original function will be evaluated only once, then
    the cached result will be returned on subsequent calls

    Example:

    class Foo(object):
        @cached_property
        def message(self):
            result = <some heavyweight calculation>
            return result
    '''
    attr_name = '__cached__' + func.__name__
    @property
    def _cached_property(self):
        try:
            return getattr(self, attr_name)
        except AttributeError:
            setattr(self, attr_name, func(self))
            return getattr(self, attr_name)
    return _cached_property


