# -*- coding: utf-8 -

import eventlet
from eventlet.green import select
from eventlet.green import socket
from eventlet import queue
from eventlet import event

sleep = eventlet.sleep
Socket = socket.socket
Select = select.select
Semaphore = eventlet.semaphore.BoundedSemaphore
Event = event.Event
