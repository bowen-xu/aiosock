# aiosock -- Multiprocess communication sockets for asyncio

This package wraps the [`socket`](https://docs.python.org/3/library/socket.html) lib, so that it can be used as part of the non-blocking asyncio event loop. A goal scenario is multiprocess communication with the help of  coroutines, *i.e.*, combining [`multiprocessing`](https://docs.python.org/3/library/multiprocessing.html) and [`asyncio`](https://docs.python.org/3/library/asyncio.html). 

For example, there are two processes in a program: one is `Main_Process`, and the other is `IO_Process`. The two processes are running with respective event loops. The `Main_Process` is asynchronizedly reading messages from `IO_Process`, and once the `IO_Process` sends something to the `Main_Process`, the latter will call a `callback` function or continue executing a coroutine from the previous break point.

## Quick Start

First, install `aiosock`.

```
pip install aiosock
```

Second, import modules

```Python
import aiosock
import asyncio
```

Third, create aio-socket pair
```Python
sock1, sock2 = aiosocket.aiosockpair()
```

Forth, if you wish to use a callback function, initialize the aio-socket(s) with the function. The form of the function should be
```Python
def callback(obj_recv: Any, *args: Any): ...
```
The first argument is the object received from the other socket, and the remainder are arguments passed from where the socket is initialized. For example

```Python
def callback_print(obj_recv: Any, num: int): 
    print(f'{num}: {obj_recv}')

sock1.init((callback_print, 0))
```

Fifth, you may also use `await` to read something in an `async` function, rather than using a callback. For example

```Python
async def main():
    obj_recv = await sock1.read()
```
Sixth, you are able to set callbacks for both read and write. the read callback is executed whenever something is received, and the write callback is executed when it is available to write. For example

```Python
def callback_print(obj_recv: Any, num: int): 
    print(f'{num}: {obj_recv}')

def callback_writable():
    print('Now writable.')

sock1.init((callback_print, 0), callback_writable)
```

The defaut values of the callbacks are `None`.

Seventh, send any object you want, as long as the object is serializable.
```Python
sock2.send('Hello asyncio!')
```

You can call `sock2.send(...)` in another process and initialized the `sock2` in that process, so that multiple processes are able to communicate with each other.

Finally, don't forget to run the event loop, for example

```Python
asyncio.get_event_loop().run_forever()
```

Here is a complete demonstration below.


### Demo

Code:

``` Python
from multiprocessing import Process
import os
from typing import Any, Iterable, Mapping
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
        self.loop.create_task(self.read())
        self.loop.run_forever()


    def on_read(self, obj: Any, *args):
        ''''''
        print(obj)
        print(f'[io on_read] PID: {os.getpid()}')


    async def read(self):
        ''''''
        while True:
            obj = await self.sock.read()
            print(f'[io await read]{str(obj)}')
            print(f'[io await read] PID: {os.getpid()}')


async def main(sock: AioSock):
    ''''''
    sock1.write(f'[sock1 write] PID: {os.getpid()}')
    obj = await sock.read()
    print(obj)
    print(f'[main await read] PID: {os.getpid()}')


if __name__ == '__main__':    
    print('IO Process Read/Write, Main Process Write/Read.')  
    print(f'Main Process PID: {os.getpid()}')
    sock1, sock2 = aiosockpair()
    iop = IO_Process(sock2)
    sock1.init()
    iop.start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sock1))
```

Output:

```
Main Process PID: 15408
IO Process PID: 12324
[sock1 write] PID: 15408
[io on_read] PID: 12324
[io await read][sock1 write] PID: 15408
[io await read] PID: 12324
[sock2 write] PID: 12324
[main await read] PID: 15408
```