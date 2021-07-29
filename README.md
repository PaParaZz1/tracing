##  安装

```bash
pip install .
```

## 搭建 Jaeger 服务

在 docker 服务器上运行
```bash
docker run --rm -d -p5775:5775/udp -p6831:6831/udp -p6832:6832/udp -p5778:5778 -p16686:16686 -p14268:14268 -p9411:9411 jaegertracing/all-in-one:latest
```

## 测试
```bash
JAEGER_ENDPOINT=http://<docker-ip>:14268/api/traces python example/test.py 
```

## 查看结果
在浏览器访问
```text
http://<docker-ip>:16686/search
```