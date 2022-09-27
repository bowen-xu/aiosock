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
        self.loop.call_later(3, self.sock.write, f'[IO sock writes] PID: {os.getpid()}')
        self.loop.run_forever()


    def set_sock(self, sock: AioSock):
        self.sock2 = sock


def on_read(obj: Any):
    ''''''
    print(obj)
    print(f'[Main on read] PID: {os.getpid()}')


if __name__ == '__main__':    
    print('IO Process Write, Main Process Read.')  
    print(f'Main Process PID: {os.getpid()}')
    sock1, sock2 = aiosockpair()
    sock1.init(on_read)
    iop = IO_Process(sock2)
    iop.start()
    loop = asyncio.get_event_loop()
    loop.run_forever()