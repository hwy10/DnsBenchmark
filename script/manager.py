from multiprocessing.managers import SyncManager, ValueProxy, DictProxy
from Queue import Queue

class DnsBenchmarkManager(SyncManager):
    pass

class ReadyCount:
    count = 0

    ## to match the interface of ValueProxy

    def get(self):
        return self.count

    ## to match the interface of ValueProxy

    def set(self, value):
        self.count -= 1

    def init(self, value):
        self.count = value

task = {}
queue = Queue()
ready_count = ReadyCount()

DnsBenchmarkManager.register('get_task', callable=lambda: task, proxytype=DictProxy)
DnsBenchmarkManager.register('get_queue', callable=lambda: queue)
DnsBenchmarkManager.register('get_ready_count', callable=lambda: ready_count, proxytype=ValueProxy)
