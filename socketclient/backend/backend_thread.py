# -*- coding: utf-8 -

import select
import socket
import threading
import time

try:
    import Queue as queue
except ImportError:  # py3
    import queue

sleep = time.sleep
Select = select.select
Socket = socket.socket
Semaphore = threading.BoundedSemaphore
Event = threading.Event
