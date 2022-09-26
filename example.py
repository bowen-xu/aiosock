from multiprocessing import Process
import os
from typing import Any, Callable, Iterable, Mapping
from aiosock import aiosock
import asyncio

# class IOProcess(Process):
#     ''''''

# sock = aiosock()

# def IO_Process():
#     ''''''

class IO_Process(Process):
    ''''''
    def __init__(self, sock_tx: aiosock, group: None = None, name: 'str | None' = None, args: Iterable[Any] = (), kwargs: Mapping[str, Any] = {}, *, daemon: 'bool | None' = None) -> None:
        super().__init__(group, None, name, daemon=daemon)
        self.sock_tx = sock_tx

    def run(self):
        # display a message
        print('This is coming from another process')
        self.loop = asyncio.get_event_loop()
        self.loop.call_later(3, self.sock_tx.write, F'[run] This is IO Process. PID:{self.pid}.')
        self.loop.run_forever()

    def set_sock(self, sock: aiosock):
        ''''''
        self.sock2 = sock

    def on_read(self, obj: Any):
        ''''''
        print(f'[on_read] This is IO Process. PID: {self.pid}')
        print(obj)

def on_read(obj: Any):
    ''''''
    print(f'[main] This is Main Process. PID: {os.getpid()}')
    print(obj)
    
if __name__ == '__main__':

    sock1 = aiosock(on_read)
    iop = IO_Process(sock1)
    sock2 = aiosock(iop.on_read)
    # iop.set_sock(sock)
    iop.start()
    sock2.write(f'[main] sock2 write. {os.getpid()}')
    loop = asyncio.get_event_loop()
    loop.run_forever()