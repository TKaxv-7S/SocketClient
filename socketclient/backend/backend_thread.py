# -*- coding: utf-8 -

import select
import socket
import threading
import time

try:
    import Queue as queue
except ImportError:  # py3
    import queue

Select = select.select
Socket = socket.socket
sleep = time.sleep
Semaphore = threading.BoundedSemaphore
