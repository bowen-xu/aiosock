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
        self.loop.call_later(self.sock_tx, F'This is IO Process. PID:{self.pid}.')
        self.loop.run_forever()

    # def set_sock(self, sock: aiosock):
    #     ''''''
    #     self.sock = sock

def on_read(obj: Any):
    ''''''
    print(f'This is Main Process. PID: {os.getpid() }')
    print(obj)
# io_process = Process(target=IO_Process, args=(write1,))
# writer_process.start()
if __name__ == '__main__':

    sock = aiosock(on_read)
    iop = IO_Process(sock.tx)
    # iop.set_sock(sock)
    iop.start()
    sock.write('Test')
    loop = asyncio.get_event_loop()
    loop.run_forever()