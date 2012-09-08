"""A multi-producer, multi-consumer queue."""

from collections import deque
from PyQt4 import QtCore

class Queue:
    """Create a queue object with a given maximum size.

    If maxsize is <= 0, the queue size is infinite.
    """
    def __init__(self, maxsize=0):
        self._init(maxsize)
        # mutex must be held whenever the queue is mutating.  All methods
        # that acquire mutex must release it before returning.  mutex
        # is shared between the two conditions, so acquiring and
        # releasing the conditions also acquires and releases mutex.
        self.mutex = QtCore.QMutex()
        # Notify not_empty whenever an item is added to the queue; a
        # thread waiting to get is notified then.
        self.not_empty = QtCore.QWaitCondition()
        # Notify not_full whenever an item is removed from the queue;
        # a thread waiting to put is notified then.
        self.not_full = QtCore.QWaitCondition()
        # Notify all_tasks_done whenever the number of unfinished tasks
        # drops to zero; thread waiting to join() is notified to resume
        self.all_tasks_done = QtCore.QWaitCondition()
        self.unfinished_tasks = 0

    def unlock(self):
        self.mutex.lock()
        self.maxsize = 0
        self.mutex.unlock()
        self.not_full.wakeAll()

    def qsize(self):
        """Return the approximate size of the queue (not reliable!)."""
        self.mutex.lock()
        n = self._qsize()
        self.mutex.unlock()
        return n

    def put(self, item):
        """Put an item into the queue."""
        self.mutex.lock()
        try:
            while self._full():
                self.not_full.wait(self.mutex)
            self._put(item)
            self.not_empty.wakeOne()
        finally:
            self.mutex.unlock()

    def remove(self,item):
        """Remove an item into the queue."""
        self.mutex.lock()
        try:
            self._remove(item)
            self.not_full.wakeOne()
        finally:
            self.mutex.unlock()

    def get(self):
        """Remove and return an item from the queue."""
        self.mutex.lock()
        try:
            while self._empty():
                self.not_empty.wait(self.mutex)
            item = self._get()
            self.not_full.wakeOne()
            return item
        finally:
            self.mutex.unlock()

    # Initialize the queue representation
    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = deque()

    def _qsize(self):
        return len(self.queue)

    # Check whether the queue is empty
    def _empty(self):
        return not self.queue

    # Check whether the queue is full
    def _full(self):
        return self.maxsize > 0 and len(self.queue) == self.maxsize

    # Put a new item in the queue
    def _put(self, item):
        self.queue.append(item)

    # Remove an item from the queue
    def _remove(self, item):
        if item in self.queue:
            try:
                # remove is only availible in python 2.5
                self.queue.remove(item)
            except AttributeError:
                # remove items this way in older versions of python.
                for i in range(0, len(self.queue)):
                    if self.queue[i] == item:
                        self.queue.rotate(-i)
                        self.queue.popleft()
                        self.queue.rotate(i)
                        break

    # Get an item from the queue
    def _get(self):
        return self.queue.popleft()
