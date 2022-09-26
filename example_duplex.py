from multiprocessing import Process
import os
from typing import Any, Callable, Iterable, Mapping
from aiosock import AioSock, AioSockDuplex
import asyncio


class IO_Process(Process):
    ''''''
    def __init__(self, sock: AioSockDuplex, group = None, name: 'str | None' = None, args: Iterable[Any] = (), kwargs: Mapping[str, Any] = {}, *, daemon: 'bool | None' = None) -> None:
        super().__init__(group, None, name, daemon=daemon)
        self.sock = sock

    def run(self):
        # display a message
        # print('This is coming from another process')
        self.loop = asyncio.get_event_loop()
        self.loop.call_later(3, self.sock.write_b, f'[write_b] PID: {os.getpid()}')
        # self.loop.call_soon(sock2.write, F'[run sock2] This is IO Process. PID:{os.getpid()}.')
        self.loop.run_forever()


    def on_read_a(self, obj: Any):
        ''''''
        print(obj)
        print(f'[on_read_a] PID: {os.getpid()}')

def on_read_b(obj: Any):
    ''''''
    print(obj)
    print(f'[on_read_b] PID: {os.getpid()}')


if __name__ == '__main__':    
    sock = AioSockDuplex()
    iop = IO_Process(sock)
    sock.set_callback_a(iop.on_read_a)
    sock.set_callback_b(on_read_b)
    iop.start()
    loop = asyncio.get_event_loop()
    loop.call_soon(sock.write_a, f'[write_a] PID: {os.getpid()}')
    loop.run_forever()