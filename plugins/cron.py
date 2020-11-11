# This is a work-in-progress and doesn't do anything yet

from . import plugin
import threading

class CronPlugin(plugin.Plugin):
    def __init__(self):
        super().__init__()
        self._thread = threading.Thread(target=self._process_tick(), daemon=True)

    def _process_tick(self):
        return

    def receive(self, request):
        return []
