import pickle 
import asyncio

from socket import socketpair, socket
from typing import Any, Callable
from asyncio import StreamReader, StreamWriter, StreamReaderProtocol, BaseTransport


asyncio.set_event_loop(asyncio.SelectorEventLoop())

class aiosock:
    ''''''
    
    def __init__(self, callback_read: Callable, n_head=4) -> None:
        ''''''
        self.N_HEAD = n_head
        self.MAX_LEN = 2**(4*self.N_HEAD-1)-1
        self.MASK = 0x01<<(4*self.N_HEAD-1)

        self.loop = asyncio.get_event_loop()

        rx, tx = socketpair()
        rx.setblocking(False)
        tx.setblocking(False)
        self.loop.add_reader(rx, self.on_read)
        self.rx : socket = rx
        self.tx: socket = tx

        self.read_cache = bytearray()

        self.callback_read = callback_read



    def write(self, content: Any):
        ''''''
        N_HEAD = self.N_HEAD
        MAX_LEN = self.MAX_LEN
        MASK = self.MASK

        write: socket = self.tx

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
        write.send(content_pack)


    def on_read(self):
        '''
        Read all the bytes in the socket buffer, and convert them to objects.
        '''
        N_HEAD = self.N_HEAD
        MASK = self.MASK

        sock: socket = self.rx
        data = self.read_cache
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
                self.loop.call_soon(self.callback_read, obj)
                data = bytearray()
            else:
                data.extend(packet)

            

