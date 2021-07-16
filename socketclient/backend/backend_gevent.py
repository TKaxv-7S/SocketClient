# -*- coding: utf-8 -

import gevent
from gevent import select
from gevent import socket
from gevent import queue
from gevent import event

try:
    from gevent import lock
except ImportError:
    #gevent < 1.0b2
    from gevent import coros as lock


sleep = gevent.sleep
Socket = socket.socket
Select = select.select
Semaphore = lock.BoundedSemaphore
Event = event.Event
