# -*- coding: utf-8 -
import logging
import threading
import time

from urllib3._collections import RecentlyUsedContainer

from socketclient.Connector import Connector
from socketclient.SocketPool import SocketPool
from socketclient.util import load_backend

logger = logging.getLogger()


class CustomRecentlyUsedContainer(RecentlyUsedContainer):
    def __iter__(self):
        super(CustomRecentlyUsedContainer, self).__iter__()

    def get(self, key):
        if key in self._container:
            return self._container[key]
        return None


class VerifyThread(threading.Thread):
    forceStop = False

    def __init__(self, func, interval_time=50):
        self.func = func
        self.interval_time = interval_time
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            time.sleep(self.interval_time)
            if self.forceStop:
                break
            self.func()


class SocketPoolManager(object):
    """Pool of socket manager"""

    def __init__(self, conn_factory, backend_mod=None, max_pool=10,
                 verify_interval_time=50):
        self.max_pool = max_pool
        self.pools = CustomRecentlyUsedContainer(max_pool, dispose_func=lambda p: p.invalidate_all())
        self.conn_factory = conn_factory
        if not backend_mod:
            backend_mod = load_backend("thread")
        self.backend_mod = backend_mod
        self.sem = self.backend_mod.Semaphore(1)

        self.run_func = None
        if verify_interval_time > 0:
            VerifyThread(self.verify_pools, verify_interval_time)

    @property
    def size(self):
        return self.pools.__len__()

    def clear_pools(self):
        self.pools.clear()

    def get_pool(self, host=None, port=80, full_init=True):
        pool = self.pools.get((host, port))
        if not pool:
            pool = self.init_pool(host, port, full_init=full_init)
        return pool

    def init_pool(self, host=None, port=80, active_count=3, max_count=10, full_init=False):
        with self.sem:
            if full_init is False and self.max_pool <= self.pools.__len__():
                return None
            pool = SocketPool(self.conn_factory, self.backend_mod, host, port, active_count, max_count)
            self.pools[(host, port)] = pool
            return pool

    def verify_pools(self):
        for key in self.pools.keys():
            pool = self.pools.get(key)
            if pool:
                if pool.size > 0:
                    pool.verify_all()

    def put_connect(self, conn: Connector):
        pool = self.get_pool(conn.host, conn.port, False)
        if pool:
            pool.put_connect(conn)
        else:
            # 释放该连接
            conn.invalidate()

    def connect_all(self):
        with self.sem:
            for key in self.pools.keys():
                pool = self.pools.get(key)
                if pool:
                    pool.connect_all()
