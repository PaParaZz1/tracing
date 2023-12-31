import os
import multiprocessing
import threading
import time
import logging

from urllib.parse import urlparse
from functools import partial, wraps
import inspect

import opentracing
from opentracing.propagation import Format
from jaeger_client import Config

from grpc_opentracing import open_tracing_client_interceptor
from grpc_opentracing.grpcext import intercept_channel

lock = threading.Lock()
_tracer = opentracing.global_tracer()
_tracer.pid = None

enabled = False
tracer_interceptor = None

service = os.environ.get('JAEGER_SERVICE_NAME', 'petrel_tracing')


class FakeTracer(object):
    def __getattr__(self, name):
        return getattr(get_tracer(), name)


tracer = FakeTracer()
tracer_interceptor = open_tracing_client_interceptor(tracer)


def is_trace_enabled():
    return enabled


def get_tracer():
    if enabled:
        check_tracer()
    return _tracer


def check_tracer():
    current_pid = os.getpid()
    if _tracer.pid != current_pid:
        with lock:
            if _tracer.pid != current_pid:
                init_tracer()


def init_tracer():
    global _tracer, tracer_interceptor
    if not enabled:
        return
    # todo read from config file
    config = Config(
        config={  # usually read from some yaml config
            'sampler': {
                'type': 'const',
                'param': 1,
                # 'type': 'probabilistic',
                # 'param': 0.005,
            },
            'reporter_batch_size': 100,
            'reporter_queue_size': 100,
            # 'reporter_flush_interval': 1000,
            # 'sampling_refresh_interval': 1000
        },
        service_name=service,
    )
    _tracer = config.new_tracer()

    current_process = multiprocessing.current_process()
    # current_thread = threading.current_thread()
    _tracer.pid = current_process.ident

    opentracing.set_global_tracer(_tracer)
    opentracing.global_tracer = lambda: get_tracer()

    logging.debug(f'init trace in process: {current_process.name}')


def wrap_channel(channel):
    if tracer_interceptor:
        channel = intercept_channel(channel, tracer_interceptor)

    return channel


def inject_header(headers):
    _tracer = get_tracer()
    _tracer.inject(_tracer.active_span.context, Format.HTTP_HEADERS, headers)


def trace_callable(target, *, operation_name=None, span_name=None, span_from_flask_request=False, ignore=False, sleep_at_exit=False):
    if operation_name is None:
        operation_name = target.__qualname__

    if ignore:
        wrapped = target
    else:
        @wraps(target)
        def wrapped(*args, **kwargs):
            _tracer = get_tracer()
            parent_span = None
            if span_from_flask_request:
                from flask import request
                parent_span = _tracer.extract(
                    format=Format.HTTP_HEADERS, carrier=request.headers)
            try:
                with _tracer.start_active_span(operation_name, child_of=parent_span) as scope:
                    if span_name:
                        kwargs[span_name] = scope.span
                    return target(*args, **kwargs)
            finally:
                if sleep_at_exit:
                    time.sleep(2)

    setattr(wrapped, '__traced', True)
    return wrapped


def identity_wrapper(fn):
    return fn


def trace_class(cls, *, method_list=None, ignore=False, **kwargs):
    if not ignore:
        for attr, val in cls.__dict__.items():
            if (method_list and attr not in method_list) or attr.startswith('__'):
                continue

            if isinstance(val, staticmethod):
                fn_wrapper = staticmethod
                val = getattr(cls, attr)
            else:
                fn_wrapper = identity_wrapper

            if callable(val) and not getattr(val, '__traced', False):
                setattr(cls, attr, fn_wrapper(trace(val, **kwargs)))

    return cls


def trace(target=None, *,
          operation_name=None, span_name=None,
          span_from_flask_request=False, ignore=False,
          sleep_at_exit=False, method_list=None):
    args = locals()
    args.pop('target')

    if target is None:
        return partial(trace, **args)

    if not enabled:
        return target

    if inspect.isclass(target):
        if operation_name is not None:
            raise ValueError(
                'operation_name is not supported for class decoration')
        args.pop('operation_name')
        return trace_class(target, **args)
    elif callable(target):
        if method_list is not None:
            raise ValueError(
                'method_list is not supported for method decoration')
        args.pop('method_list')
        return trace_callable(target, **args)
    else:
        raise ValueError(f'can not set decorator on type {type(target)}')


endpoint = os.getenv('JAEGER_ENDPOINT')
if endpoint:
    result = urlparse(endpoint)
    if not result.hostname:
        raise ValueError(
            f'can not get hostname from JAEGER_ENDPOINT: {endpoint}')
    os.environ['JAEGER_AGENT_HOST'] = result.hostname

if os.getenv('JAEGER_AGENT_HOST'):
    print('JAEGER_AGENT_HOST:', os.getenv('JAEGER_AGENT_HOST'))
    enabled = True
    init_tracer()
