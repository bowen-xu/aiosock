import os
import pickle 
import asyncio

from socket import socketpair, socket
from typing import Any, Callable
from asyncio import StreamReader, StreamWriter, StreamReaderProtocol, BaseTransport


asyncio.set_event_loop(asyncio.SelectorEventLoop())


class AioSock:
    ''''''
    
    def __init__(self, callback: Callable=None, n_head=4) -> None:
        ''''''
        self.N_HEAD = n_head
        self.MAX_LEN = 2**(4*self.N_HEAD-1)-1
        self.MASK = 0x01<<(4*self.N_HEAD-1)

        rx, tx = socketpair()
        rx.setblocking(False)
        tx.setblocking(False)

        self.rx = rx
        self.tx = tx

        self.rx = AioSockReader(self.rx, callback, self.N_HEAD)
        self.tx = AioSockWriter(self.tx, self.N_HEAD)


    def reset_callback(self, callback: Callable):
        ''''''
        self.rx.reset_callback(callback)
        
        


    # def on_read(self):
    #     return self.rx.on_read()


    def write(self, content: Any):
        return self.tx.write(content)



class AioSockBase:
    def __init__(self, sock: socket, n_head=4) -> None:
        self.N_HEAD: int = n_head
        self.MAX_LEN: int = 2**(4*self.N_HEAD-1)-1
        self.MASK: int = 0x01<<(4*self.N_HEAD-1)

        self.sock = sock

    @property
    def loop(self):
        return asyncio.get_event_loop()
    


class AioSockReader(AioSockBase):
    def __init__(self, sock: socket, callback: Callable=None, n_head=4) -> None:
        super().__init__(sock, n_head)
        self.read_cache = bytearray()
        self.callback = callback
        if self.callback is not None:
            self.loop.add_reader(sock, self.on_read)


    def on_read(self):
        '''
        Read all the bytes in the socket buffer, and convert them to objects.
        '''
        N_HEAD = self.N_HEAD
        MASK = self.MASK

        sock: socket = self.sock
        data = self.read_cache
        is_obj_end = True
        while True:
            try:
                packet = sock.recv(N_HEAD)
            except:
                if not is_obj_end: self.read_cache = data
                else: self.read_cache = bytearray()
                break
            packet = int.from_bytes(packet, "big")
            is_obj_end = not (MASK&(packet))
            num_data = (~MASK)&(packet)
            packet = sock.recv(num_data)
            if is_obj_end:
                if len(data) > 0: data.extend(packet)
                else: data = packet
                obj = pickle.loads(data)
                self.loop.call_soon(self.callback, obj)
                data = bytearray()
            else:
                data.extend(packet)

    def reset_callback(self, callback: Callable):
        ''''''
        self.callback = callback
        self.loop.remove_reader(self.sock)
        self.loop.add_reader(self.sock, self.on_read)

class AioSockWriter(AioSockBase):
    def __init__(self, sock: socket, n_head=4) -> None:
        super().__init__(sock, n_head)
    #     self.loop.add_writer(sock, self.on_write)

    # def on_write(self, *args):
    #     print(f'[on write] {os.getpid()}')


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


class AioSockDuplex:

    def __init__(self, callback_a: Callable=None, callback_b: Callable=None, n_head=4) -> None:
        ''''''
        self.sock_a = AioSock(callback_a)
        self.sock_b = AioSock(callback_b)
        
    
    def write_a(self, content: Any):
        self.sock_a.write(content)


    def write_b(self, content: Any):
        self.sock_b.write(content)


    def set_callback_a(self, callback: Callable):
        self.sock_a.set_callback(callback)

    def set_callback_b(self, callback: Callable):
        self.sock_b.set_callback(callback)
