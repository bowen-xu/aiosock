from collections import deque
import pickle 
import asyncio

from socket import socketpair, socket
from typing import Any, Callable, Coroutine, Iterable, Tuple
from asyncio import BaseEventLoop, Event


asyncio.set_event_loop(asyncio.SelectorEventLoop())


def aiosockpair(n_head=4):
    ''''''
    N_HEAD = n_head
    MAX_LEN = 2**(4*N_HEAD-1)-1
    MASK = 0x01<<(4*N_HEAD-1)

    s1, s2 = socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    return AioSock(s1, N_HEAD), AioSock(s2, N_HEAD)


def create_immediate_task(loop: BaseEventLoop, func: Coroutine, *args):
    ''''''
    loop.create_task(func(*args))
    ready: deque = loop._ready
    if len(ready) > 0:
        ready.appendleft(ready.pop())


class AioSock:
    def __init__(self, sock: socket, n_head) -> None:
        self.N_HEAD: int = n_head
        self.MAX_LEN: int = 2**(4*self.N_HEAD-1)-1
        self.MASK: int = 0x01<<(4*self.N_HEAD-1)

        self.sock = sock
        self.sock.setblocking(False)

        self.read_cache = bytearray()

        self.callback_read = None
        self.callback_write = None

        self.data_read = None

    @property
    def loop(self):
        return asyncio.get_event_loop()


    def init(self, 
        callback_read: 'Callable[[object, Any], None]|Tuple[Callable[[object, Any], None], Tuple]' = None, 
        callback_write: 'Callable[[Any], None]|Tuple[Callable[[Any], None], Tuple]'= None
        ):
        ''''''
        self._event_read = Event()
        self._event_read_complete = Event()

        self._event_read_complete.set()

        args = ()
        if callback_read is not None:
            # add callback for reading avalability
            if not isinstance(callback_read, Callable):
                assert isinstance(callback_read, Iterable)
                callback_read = tuple(callback_read)
                callback, args = callback_read[0], callback_read[1:]
            else:
                callback = callback_read
            self.callback_read = callback
        # to ensure that the asynchronized funtion `self.on_read_availabe` is handled with the highest priority
        self.loop.add_reader(self.sock, create_immediate_task, self.loop, self.on_read_availabe, *args)
        

        args = ()
        if callback_write is not None: 
            # add callback for writing avalability
            if not isinstance(callback_write, Callable):
                assert isinstance(callback_write, Iterable)
                callback_write = tuple(callback_write)
                callback, args = callback_write[0], callback_write[1:]
            else:
                callback = callback_write
            self.callback_write = callback
        self.loop.add_writer(self.sock, self.on_write_availabe, *args)


    def close_socket(self):
        self.sock.close()
        try:
            self.loop.remove_reader(self.sock)
            self.loop.remove_writer(self.sock)
        except: pass

    async def on_read_availabe(self, *args):
        '''
        Read all the bytes in the socket buffer, and convert them to objects.
        '''
        N_HEAD = self.N_HEAD
        MASK = self.MASK

        sock: socket = self.sock
        data = self.read_cache
        is_obj_end = True
        while True:
            # get head
            try: packet = sock.recv(N_HEAD) # packet may be None if nothing to receive
            except BlockingIOError: packet = None
            except ConnectionResetError:
                self.close_socket()
                break
        
            if packet is None or len(packet) == 0:
                if not is_obj_end: self.read_cache = data
                else: self.read_cache = bytearray()
                if packet == b'':
                    self.close_socket()
                break
            # now packet is not None

            # convert head
            packet = int.from_bytes(packet, "big")
            is_obj_end = not (MASK&(packet))
            num_data = (~MASK)&(packet)
            # get data
            packet = sock.recv(num_data)
            if is_obj_end:
                if len(data) > 0: data.extend(packet)
                else: data = packet
                obj = pickle.loads(data)
                self.data_read = obj
                if self.callback_read is not None:
                    self.loop.call_soon(self.callback_read, obj, *args)
                self._event_read.set()

                # wait data to be read asynchronizedly.
                if not self._event_read_complete.is_set():
                    await self._event_read_complete.wait()
                data = bytearray()
            else:
                data.extend(packet)


    def on_write_availabe(self, *args):
        self.loop.remove_writer(self.sock)
        if self.callback_write is not None:
            self.callback_write(*args)


    def write(self, content: Any):
        ''''''
        N_HEAD = self.N_HEAD
        MAX_LEN = self.MAX_LEN
        MASK = self.MASK

        writer: socket = self.sock

        # pack
        content = pickle.dumps(content)

        #   get heads
        len_content = len(content)
        if len_content<=MAX_LEN:
            heads = (len_content.to_bytes(N_HEAD, "big"),)
        else:
            heads = (*((MAX_LEN|MASK).to_bytes(N_HEAD, "big") for _ in range(len_content//MAX_LEN)), *(((len_content%MAX_LEN).to_bytes(N_HEAD, "big"),) if len_content%MAX_LEN>0 else ()))

        
        content_pack = bytearray()
        for i, head in enumerate(heads):
            content_pack.extend(head)
            content_pack.extend(content[MAX_LEN*i:MAX_LEN*(i+1)])
        
        # send packed content
        writer.send(content_pack)
    
    
    async def read(self) -> Any:
        ''''''
        # the reading process is not completed
        self._event_read_complete.clear()
        # nothing read
        if self.data_read is None:
            self._event_read.clear()
            # wait until something is read
            await self._event_read.wait()
        # now the reading process is completed
        self._event_read_complete.set()
        # clear the cache
        obj, self.data_read = self.data_read, None
        return obj
