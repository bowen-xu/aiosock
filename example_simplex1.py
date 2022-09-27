from multiprocessing import Process
import os
import signal
from typing import Any, Callable, Iterable, Mapping
from aiosock import AioSock, aiosockpair
import asyncio


class IO_Process(Process):
    ''''''
    def __init__(self, sock: AioSock, group = None, name: 'str | None' = None, args: Iterable[Any] = (), kwargs: Mapping[str, Any] = {}, *, daemon: 'bool | None' = None) -> None:
        super().__init__(group, None, name, daemon=daemon)
        self.sock = sock


    def run(self):
        print(f'IO Process PID: {os.getpid()}')
        print('reset callback.')
        self.sock.init(self.on_read)
        print('reset callback done.')
        self.loop = asyncio.get_event_loop()
        self.loop.run_forever()


    def on_read(self, obj: Any):
        ''''''
        print(obj)
        print(f'[Sock on read] PID: {os.getpid()}')


def on_read(obj: Any):
    ''''''
    print(obj)
    print(f'[Main on read] PID: {os.getpid()}')


if __name__ == '__main__':  
    print('Main Process Write, IO Process Read.')  
    print(f'Main Process PID: {os.getpid()}')
    sock1, sock2 = aiosockpair()
    iop = IO_Process(sock2)
    iop.start()
    sock1.init()
    loop = asyncio.get_event_loop()
    loop.call_later(3, sock1.write, f'[Main sock writes] PID: {os.getpid()}')
    loop.call_later(4, sock1.write, f'[Main sock writes2] PID: {os.getpid()}')
    loop.run_forever()
    