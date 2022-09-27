from multiprocessing import Process
import os
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
        self.loop = asyncio.get_event_loop()
        self.sock.init(self.on_read)
        self.loop.call_later(3, self.sock.write, f'[sock2 write] PID: {os.getpid()}')
        self.loop.run_forever()


    def on_read(self, obj: Any, *args):
        ''''''
        print(obj)
        print(f'[io on_read] PID: {os.getpid()}')


def on_read(obj: Any, *args):
    ''''''
    print(obj)
    print(f'[main on_read] PID: {os.getpid()}')


if __name__ == '__main__':    
    print('IO Process Read/Write, Main Process Write/Read.')  
    print(f'Main Process PID: {os.getpid()}')
    sock1, sock2 = aiosockpair()
    iop = IO_Process(sock2)
    sock1.init(on_read)
    iop.start()
    loop = asyncio.get_event_loop()
    loop.call_soon(sock1.write, f'[sock1 write] PID: {os.getpid()}')
    loop.run_forever()