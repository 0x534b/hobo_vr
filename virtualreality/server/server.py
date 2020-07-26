"""Server loop that communicates between the driver and posers."""
import asyncio

from ..templates import PoserTemplate
from ..util import utilz as u

DOMAIN = (None, 6969)

class Server:
    def __init__(self):
        '''
        im not sure about this on chief,
        looks like a destructor to me
        '''
        self.conz = []
        self.debug = False

        self._driver_idz = [b'hello\n',]
        self._poser_idz = [b'holla\n',]
        self._terminator = b'\n'
        self._close_msg = b'CLOSE\n'

    def __repr__(self):
        '''do i need to explain this?'''
        return f'<{self.__class__.__module__}.{self.__class__.__name__} debug={self.debug} active_conz={len(self.conz)} object at {hex(id(self))}>'

    async def send_to_all(self, msg, me):
        '''send a message to all registered connections that are not self and have the corresponding id'''
        try:
            for i in self.conz:
                if i != me and (i[2] == me[2] or i[3]):
                    i[1].write(msg)
                    await i[1].drain()
        except Exception as e:
            print (f'message lost: {e}')


    async def __call__(self, reader, writer):
        '''this is will run for each incoming connection'''
        addr = writer.get_extra_info("peername")

        id_msg, first_msg = (await reader.read(50)).split(self._terminator)

        me = (addr, writer, id_msg in self._driver_idz or id_msg in self._poser_idz, id_msg in self._poser_idz, f'lol{len(self.conz)}')
        if me not in self.conz:
            print (f'new connection from {addr}')
            self.conz.append(me)

        if first_msg:
            await self.send_to_all(first_msg, me)

        while 1:
            try:
                # data = await u.read3(reader, read_len=256)
                data = await reader.read(300)

                if not data or self._close_msg in data:
                    break

                await self.send_to_all(data, me)

                if self.debug:
                    print (f'{repr(data)} from {addr}')

            except Exception as e:
                print (f'{addr} broke: {e}')
                break

        if me in self.conz:
            self.conz.remove(me)

        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print (f'failed to close {addr}: {e}')

        print (f'connection to {addr} closed')

def run_til_dead(poser: PoserTemplate = None, conn_handle=Server()):
    """Run the server until it dies."""
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(conn_handle, *DOMAIN, loop=loop)
    server = loop.run_until_complete(coro)

    if poser is not None:
        poser_result = asyncio.run_coroutine_threadsafe(poser.main(), loop)

    # Serve requests until Ctrl+C is pressed
    print("Serving on {}".format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
