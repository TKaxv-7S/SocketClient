import contextlib

from socketclient.Connector import TcpConnector
from socketclient.SocketPoolManager import SocketPoolManager
from socketclient.log import logger
from socketclient.util import load_backend


class SocketClient(object):

    def __init__(self, conn_factory=TcpConnector, backend="gevent", max_pool=10, retry_count=3,
                 verify_interval_time=50):
        # backend="gevent"
        # backend="thread"
        # backend="eventlet"
        if isinstance(backend, str):
            self.backend_mod = load_backend(backend)
            self.backend = backend
        else:
            self.backend_mod = backend
            self.backend = str(getattr(backend, '__name__', backend))
        self.pool_manager = SocketPoolManager(conn_factory, self.backend_mod, max_pool, verify_interval_time)
        self.retry_count = retry_count

    def init_pool(self, host=None, port=80, active_count=3, max_count=10):
        self.pool_manager.init_pool(host, port, active_count, max_count)

    @contextlib.contextmanager
    def get_connect(self, host=None, port=80):
        conn = None
        pool = self.pool_manager.get_pool(host, port)
        if pool:
            tries = 0
            while tries < self.retry_count:
                try:
                    conn = pool.get_connect(host, port)
                    break
                except Exception as e:
                    logger.error('获取连接异常，重试第：%s次，异常：%s', tries, e)
                tries += 1
        try:
            yield conn
        except Exception as e:
            conn.handle_exception(e)
        finally:
            self.pool_manager.put_connect(conn)

    # 修改为连接所有
    def connect(self, host=None, port=80):
        if host is not None and port is not None:
            pool = self.pool_manager.get_pool(host, port)
            if pool:
                pool.connect_all()
        else:
            self.pool_manager.connect_all()

    def send(self, host=None, port=80, byte_msg: bytes = b''):
        with self.get_connect(host, port) as conn:
            # 发送报文
            conn.send(byte_msg)
            # logger.debug('已发送')
        return conn

    def close_client(self):
        self.pool_manager.clear_pools()
