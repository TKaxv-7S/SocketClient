# SocketClient
功能：支持多种参数配置，默认已实现TCP连接，可拓展其他连接如UDP等，支持批量创建连接，自动维护连接池，实现连接自动创建、保活、回收等功能，并支持http请求报文拼接与响应报文解析。

## 第三方库
- [gevent](http://www.gevent.org/)
- [urllib3](https://urllib3.readthedocs.io/)
- [Requests](http://docs.python-requests.org/en/master/)

#### 部分代码参考
- [SocketPool](https://github.com/benoitc/socketpool)
