from multiprocessing import Process
import time
import requests
from flask import Flask

from petrel_tracing import trace, get_tracer, inject_header


@trace(span_name='span')  # trace 打开时，span 变量将传入到 调用函数
def do_request(path, span=None):
    headers = {}
    inject_header(headers)
    response = requests.get(
        f'http://localhost:8080/{path}', headers=headers)
    print('response:', response.content)

    if span:  # 不进行 trace 时， span 为 None
        span.log_kv({'path': path})  # 在 span 中添加 log 记录，该 log 将出现在 trace 结果中的 Logs 里


def main():
    app = Flask(__name__)

    @app.route("/hello_world")
    @trace(span_from_flask_request=True)
    def hello_world():
        time.sleep(0.01)
        return "Hello, World!"

    @app.route("/hello_world_again")
    @trace(span_from_flask_request=True)
    def hello_world_again():
        time.sleep(0.01)
        return "Hello, World!"

    server = Process(target=app.run, kwargs={'port': 8080})
    server.start()

    tracer = get_tracer()

    with tracer.start_active_span('span_of_do_reqeust'):
        do_request('hello_world')
        do_request('hello_world_again')

    time.sleep(2)  # 测试代码中主线程需要sleep，等待后台线程将数据发送到服务端

    server.terminate()
    server.join()


if __name__ == '__main__':
    main()
