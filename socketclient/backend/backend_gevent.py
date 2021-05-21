# -*- coding: utf-8 -

import gevent
from gevent import select
from gevent import socket
from gevent import queue

try:
    from gevent import lock
except ImportError:
    #gevent < 1.0b2
    from gevent import coros as lock


sleep = gevent.sleep
Semaphore = lock.BoundedSemaphore
Socket = socket.socket
Select = select.select
