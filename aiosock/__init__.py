from collections import deque
import pickle 
import asyncio

from socket import socketpair, socket
from typing import Any, Callable, Coroutine, Iterable, Tuple
from asyncio import BaseEventLoop, Event

# from .task import create_immediate_task, call_immediately

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
    ready.appendleft(ready.pop())

class AioSock:
    def __init__(self, sock: socket, n_head) -> None:
        self.N_HEAD: int = n_head
        self.MAX_LEN: int = 2**(4*self.N_HEAD-1)-1
        self.MASK: int = 0x01<<(4*self.N_HEAD-1)

        self.sock = sock

        self.read_cache = bytearray()

        self.callback_read = None
        self.callback_write = None

    @property
    def loop(self):
        return asyncio.get_event_loop()


    def init(self, 
        callback_read: 'Callable[[object, Any], None]|Tuple[Callable[[object, Any], None], Tuple]' = None, 
        callback_write: 'Callable[[Any], None]|Tuple[Callable[[Any], None], Tuple]'= None
        ):
        ''''''
        self._event_read = Event()
        self._event_read_incomplete = Event()

        self._event_read_incomplete.clear()

        args = ()
        if callback_read is not None:
            # add callback for reading avalability
            if not isinstance(callback_read, Callable):
                assert isinstance(callback_read, Iterable)
                callback, args = callback_read
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
                callback, args = callback_write
            else:
                callback = callback_write
            self.callback_write = callback
        self.loop.add_writer(self.sock, self.on_write_availabe, *args)


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
            except: packet = None
            if packet is None:
                if not is_obj_end: self.read_cache = data
                else: self.read_cache = bytearray()
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
                self._event_read.clear()

                # wait data to be read asynchronizedly.
                if self._event_read_incomplete.is_set():
                    await self._event_read_incomplete.wait()
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
        self._event_read_incomplete.set()
        if self.data_read is None:
            self._event_read.set()
            await self._event_read.wait()
        self._event_read_incomplete.set()
        obj, self.data_read = self.data_read, None
        return obj



# class AioSockReader(AioSockBase):
#     def __init__(self, sock: socket, callback: Callable=None, n_head=4) -> None:
#         super().__init__(sock, n_head)
#         self.read_cache = bytearray()
#         self.callback = callback
#         if self.callback is not None:
#             self.loop.add_reader(sock, self.on_read_availabe)


#     def on_read_availabe(self):
#         '''
#         Read all the bytes in the socket buffer, and convert them to objects.
#         '''
#         N_HEAD = self.N_HEAD
#         MASK = self.MASK

#         sock: socket = self.sock
#         data = self.read_cache
#         is_obj_end = True
#         while True:
#             try:
#                 packet = sock.recv(N_HEAD)
#             except:
#                 if not is_obj_end: self.read_cache = data
#                 else: self.read_cache = bytearray()
#                 break
#             packet = int.from_bytes(packet, "big")
#             is_obj_end = not (MASK&(packet))
#             num_data = (~MASK)&(packet)
#             packet = sock.recv(num_data)
#             if is_obj_end:
#                 if len(data) > 0: data.extend(packet)
#                 else: data = packet
#                 obj = pickle.loads(data)
#                 self.loop.call_soon(self.callback, obj)
#                 data = bytearray()
#             else:
#                 data.extend(packet)

#     def reset_callback(self, callback: Callable):
#         ''''''
#         self.callback = callback
#         self.loop.remove_reader(self.sock)
#         self.loop.add_reader(self.sock, self.on_read_availabe)

# class AioSockWriter(AioSockBase):
#     def __init__(self, sock: socket, callback: Callable=None, n_head=4) -> None:
#         super().__init__(sock, n_head)
#         self.loop.add_writer(self.sock, self.on_write_availabe)
#         self.callback = callback

#     def on_write_availabe(self):
#         self.loop.remove_writer(self.sock)
#         if self.callback is not None:
#             self.callback()
#         print(f'[on writable] {os.getpid()}')


#     def write(self, content: Any):
#         ''''''
#         N_HEAD = self.N_HEAD
#         MAX_LEN = self.MAX_LEN
#         MASK = self.MASK

#         writer: socket = self.sock

#         # pack
#         content = pickle.dumps(content)

#         #   get heads
#         len_content = len(content)
#         if len_content<=MAX_LEN:
#             heads = (len_content.to_bytes(N_HEAD, "big"),)
#         else:
#             heads = (*((MAX_LEN|MASK).to_bytes(N_HEAD, "big") for _ in range(len_content//MAX_LEN)), *(((len_content%MAX_LEN).to_bytes(N_HEAD, "big"),) if len_content%MAX_LEN>0 else ()))

        
#         content_pack = bytearray()
#         for i, head in enumerate(heads):
#             content_pack.extend(head)
#             content_pack.extend(content[MAX_LEN*i:MAX_LEN*(i+1)])
        
#         # send packed content
#         writer.send(content_pack)


# class AioSockDuplex:

#     def __init__(self, callback_a: Callable=None, callback_b: Callable=None, n_head=4) -> None:
#         ''''''
#         self.sock_a = AioSock(callback_a)
#         self.sock_b = AioSock(callback_b)
        
    
#     def write_a(self, content: Any):
#         self.sock_a.write(content)


#     def write_b(self, content: Any):
#         self.sock_b.write(content)


    def set_callback_a(self, callback: Callable):
        self.sock_a.set_callback(callback)

    def set_callback_b(self, callback: Callable):
        self.sock_b.set_callback(callback)
