# -*- coding: utf-8 -
import time

from socketclient.Connector import Connector
from socketclient.log import logger


class SocketPool(object):
    """Pool of socket connections"""

    def __init__(self, conn_factory, backend_mod=None,
                 host=None, port=80, active_count=3, max_count=10):

        self.conn_factory = conn_factory
        self.host = host
        self.port = port
        self.active_count = active_count
        self.max_count = max_count
        self.backend_mod = backend_mod
        self.import_queue = getattr(backend_mod, 'queue')

        self.pool = self.import_queue.Queue(max_count)

        for i in range(active_count):
            try:
                new_connect = conn_factory(host, port, backend_mod, True)
                if new_connect.is_connected():
                    self.pool.put_nowait(new_connect)
            except self.import_queue.Full:
                logger.error("队列已满")
                break
            except Exception as e:
                logger.error('新建连接异常，host：%s，port：%s，异常：%s', host, port, e)
        static_count = max_count - active_count
        if static_count > 0:
            for i in range(static_count):
                try:
                    new_connect = conn_factory(host, port, backend_mod)
                    self.pool.put_nowait(new_connect)
                except self.import_queue.Full:
                    logger.error("队列已满")
                    break
                except Exception as e:
                    logger.error('新建连接异常，host：%s，port：%s，异常：%s', host, port, e)

        self.sem = self.backend_mod.Semaphore(1)

    # 废弃逻辑
    # def is_valid_connect(self, conn: Connector, verify_time=time.time(), verify_interval_time=0):
    #     if conn.is_connected():
    #         if conn.is_connecting():
    #             interval_time = conn.connect_time() + self.life_time - verify_time
    #             if interval_time > 0:
    #                 if interval_time - verify_interval_time < 0:
    #                     conn.keep_connect(verify_time)
    #                 return True
    #             else:
    #                 return False
    #         else:
    #             return False
    #     return not conn.is_closed()

    @staticmethod
    def verify_connect(conn: Connector, verify_time=time.time()):
        if not conn:
            return False
        elif conn.is_valid(verify_time):
            return True
        else:
            conn.invalidate()
            return False

    def verify_all(self):
        active_count = 0
        now = time.time()
        for i in range(self.max_count):
            conn = None
            try:
                conn = self.pool.get_nowait()
                if self.verify_connect(conn, now):
                    if conn.is_connected():
                        active_count += 1
                    elif self.active_count > active_count:
                        # 根据active_count值保持活跃连接数
                        conn.connect()
                        active_count += 1
                    self.pool.put_nowait(conn)
            except self.import_queue.Empty:
                break
            except self.import_queue.Full:
                break
            except Exception as e:
                logger.error("异常信息：%s", e)
                if conn:
                    conn.invalidate()
        # 完成后需要保证队列中有max_count个连接，不够则创建
        left_count = self.max_count - self.pool.qsize()
        if active_count >= self.active_count:
            for i in range(left_count):
                try:
                    new_connect = self.conn_factory(self.host, self.port, self.backend_mod)
                    self.pool.put_nowait(new_connect)
                except self.import_queue.Full:
                    break
                except Exception as e:
                    logger.error('新建连接异常，host：%s，port：%s，异常：%s', self.host, self.port, e)
        else:
            left_active_count = self.active_count - active_count
            left_static_count = left_count - left_active_count
            # 剩余空间足够
            if left_static_count >= 0:
                for i in range(left_active_count):
                    try:
                        new_connect = self.conn_factory(self.host, self.port, self.backend_mod, True)
                        self.pool.put_nowait(new_connect)
                    except self.import_queue.Full:
                        break
                    except Exception as e:
                        logger.error('新建连接异常，host：%s，port：%s，异常：%s', self.host, self.port, e)
                for i in range(left_static_count):
                    try:
                        new_connect = self.conn_factory(self.host, self.port, self.backend_mod)
                        self.pool.put_nowait(new_connect)
                    except self.import_queue.Full:
                        break
                    except Exception as e:
                        logger.error('新建连接异常，host：%s，port：%s，异常：%s', self.host, self.port, e)
            # else:
                # 不应该会出现，否则打印错误日志
                # logger.error("队列中没有足够空间创建活动连接")

    @property
    def size(self):
        return self.pool.qsize()

    def invalidate_all(self):
        if self.pool.qsize():
            while True:
                try:
                    self.pool.get_nowait().invalidate()
                except self.import_queue.Empty:
                    break
                except Exception as e:
                    logger.error("异常信息：%s", e)
        logger.info("与主机[%s]端口[%s]连接已释放", self.host, self.port)

    def put_connect(self, conn: Connector):
        if conn.host != self.host or conn.port != self.port:
            conn.invalidate()
            return False
        with self.sem:
            if self.pool.qsize() < self.max_count:
                if self.verify_connect(conn):
                    try:
                        self.pool.put_nowait(conn)
                        return True
                    except self.import_queue.Full:
                        conn.invalidate()
                        return False
            else:
                conn.invalidate()
                return False

    def get_connect(self, host=None, port=80):
        size = self.pool.qsize()
        if size:
            now = time.time()
            while True:
                try:
                    conn = self.pool.get_nowait()
                    if self.verify_connect(conn, now):
                        return conn
                    else:
                        size -= 1
                        if size <= 0:
                            break
                except self.import_queue.Empty:
                    return None
                except Exception as e:
                    logger.error("异常信息：%s", e)
                    size -= 1
                    if size <= 0:
                        break
        try:
            new_item = self.conn_factory(host, port, self.backend_mod)
            new_item.connect()
            return new_item
        except Exception as e:
            logger.error("创建连接异常：%s", e)
            return None
        # else:
        #     # we should be connected now
        #     with self.sem:

    def connect_all(self):
        size = self.pool.qsize()
        if size:
            while True:
                try:
                    size -= 1
                    conn = self.pool.get_nowait()
                    if conn.is_valid():
                        conn.connect()
                        self.pool.put_nowait(conn)
                    else:
                        conn.invalidate()
                    if size <= 0:
                        break
                except self.import_queue.Full:
                    break
                except self.import_queue.Empty:
                    break
                except Exception as e:
                    logger.error("异常信息：%s", e)
        for i in range(self.max_count - self.pool.qsize()):
            new_connect = None
            try:
                new_connect = self.conn_factory(self.host, self.port, self.backend_mod, True)
                self.pool.put_nowait(new_connect)
            except self.import_queue.Full:
                if new_connect:
                    new_connect.invalidate()
                break
            except Exception as e:
                logger.error('新建连接异常：%s', e)
        logger.info("与主机[%s]端口[%s]新建[%s]个连接", self.host, self.port, self.pool.qsize())
