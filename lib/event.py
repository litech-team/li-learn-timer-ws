import asyncio

class EventHandler:
    def __init__(self):
        self.listeners = []
    
    def add_listener(self, listener):
        self.listeners.append(listener)
        return self
    
    def remove_listener(self, listener):
        self.listeners.remove(listener)
        return self
    
    def fire(self, *args):
        for listener in self.listeners:
            if (asyncio.iscoroutinefunction(listener)):
                asyncio.ensure_future(listener(self, *args))
            else:
                listener(self, *args)