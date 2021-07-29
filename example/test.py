import time
from petrel_tracing import trace, get_tracer


@trace  # 对 class 中所有非 __ 开头的函数进行trace
class A:
    @staticmethod
    def static_method():
        time.sleep(0.01)
        return 's_method'

    @trace  # 以 __ 开头的函数默认不被trace，需要单独添加
    def __dunder(self):
        time.sleep(0.01)
        pass

    def object_method(self):
        self.static_method()

        tracer = get_tracer()
        with tracer.start_active_span('span_in_object_method'):
            time.sleep(0.02)
            with tracer.start_active_span('another_span') as scope:
                scope.span.log_kv({'event': 'test message', 'life': 42})

        self.__dunder()
        return 'test'


class B:

    @trace  # 单独只对一个函数进行统计
    def test(self):
        pass


a = A()
b = B()

a.object_method()
b.test()

# 测试代码中主线程需要sleep，等待后台线程将数据发送到服务端
time.sleep(2)
