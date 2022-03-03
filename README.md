##  安装

```bash
pip install .
```

## 搭建 Jaeger 服务

在 docker 服务器上运行
```bash
docker run --rm -d -p5775:5775/udp -p6831:6831/udp -p6832:6832/udp -p5778:5778 -p16686:16686 -p14268:14268 -p9411:9411 jaegertracing/all-in-one:latest
```

或者，直接下载可执行文件 https://www.jaegertracing.io/download/#binaries 
，解压后运行 jaeger-all-in-one

## 测试
```bash
JAEGER_ENDPOINT=http://<docker-ip>:14268/api/traces python example/test.py 
```

## 查看结果
在浏览器访问
```text
http://<docker-ip>:16686/search
```

##  API
```python
def trace(target=None,                      # 被 trace 的方法或类
          *,
          operation_name=None,              # 默认使用方法的 qualname 作为 trace 结果中的 operation name，仅支持对方法进修饰
          span_name=None,                   # span 在被 trace 方法中的变量名
          span_from_flask_request=False,    # 从 flask request 中获取 span 相关信息
          ignore=False,                     # 忽略对该方法进行 trace
          method_list=None                  # 对类进行修饰时，指定需要 trace 的方法，默认对类中所有非 __ 开头的方法进行 trace
          )

def get_tracer() # 获取 tracer
```

## 使用方式
```python
@trace
class A:
    def foo(self):
        ...

    @trace(ignore=True) # 不对 bar 方法进行 trace
    def bar(self):
        ...

@trace(method_list=['foo']) # 仅对 foo 方法进行 trace
class B:
    def foo(self):
        ...

    def bar(self):
        ...

    @trace(span_name='span')
    def baz(self, span=None):
        ...
        if span:
            span.log_kv({'message': 'bomb'})


@trace
def foo():
    tracer = get_tracer()
    with tracer.start_active_span('span_in_foo'):
        ...
    with tracer.start_active_span('another_span_in_foo') as scope:
        scope.span.log_kv({'message': 'bomb'})
        ...

@trace(span_name='_bar')
def bar():
    ...

```

## 例子
- [基本用例](./example/test.py)
- [Flask用例](./example/flask_example.py)

## 更多信息

- [OpenTracing](https://opentracing.io/)
- [Jaeger - a Distributed Tracing System](https://github.com/jaegertracing/jaeger)
- [Jaeger Bindings for Python OpenTracing API](https://github.com/jaegertracing/jaeger-client-python)