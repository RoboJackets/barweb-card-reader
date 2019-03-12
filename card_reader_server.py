import sys

from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import *
from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

VALID_CARD_READERS = ['ACS ACR122U']

class PrintObserver(CardObserver):
    def update(self, observable, cards):
        """
        Read data from present card, and pipe card ID to the web socket
        """
        added_cards, removed_cards = cards

        if len(added_cards) > 0:
            # Connect to the reader
            connection.connect()

            # App BBBBCD
            select_app_data = connection.transmit([0x90, 0x5a, 0x00, 0x00, 3, 0xcd, 0xbb, 0xbb, 0x00])

            # File 0x01
            read_file_data = connection.transmit([0x90, 0xbd, 0x00, 0x00, 0x07, 0x01, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00])[0]
            file_data_hex = toHexString(read_file_data)
            file_data_byte = bytearray.fromhex(file_data_hex).decode().split("=")

            # Pipe card ID to the web socket
            WebSocket.broadcast_message(str(file_data_byte))


class WebSocket(WebSocketServerProtocol):
    connections = list()

    def onConnect(self, request):
        """
        On connection. Add connection to list of connections
        """
        log.msg('Client connecting: %s' % request.peer)

        self.connections.append(self)

    def onOpen(self):
        """
        On client connection. Log
        """
        log.msg('WebSocket connection opened')

    def onMessage(self, payload, is_binary):
        """
        On message from client. Ignore
        """
        pass

    def onClose(self, was_clean, code, reason):
        """
        On disconnection. Remove connection from list of connections
        """
        log.msg('WebSocket connection closed: %s' % reason)

        self.connections.remove(self)

    @classmethod
    def broadcast_message(cls, data):
        """
        Send message to web socket
        """
        log.msg('Sending message to connections: %s' % data)

        payload = data.encode('utf8')

        # Send message through all connections
        for c in set(cls.connections):
            reactor.callFromThread(cls.sendMessage, c, payload)


# Log to standard output
log.startLogging(sys.stdout)

# The actual web socket
factory = WebSocketServerFactory(u'ws://localhost:9000')
factory.protocol = WebSocket

# Initialize readers
r = readers()
valid_reader_index = -1


# Check if any valid readers are connected
for i in range(len(r)):
    for valid_card_reader in VALID_CARD_READERS:
        if str(r[i]).find(valid_card_reader) > -1:
            valid_reader_index = i

            break

# Only start the server if any valid readers are connected
if valid_reader_index >= 0:
    # Create the connection the the reader
    connection = r[valid_reader_index].createConnection()

    # Variable for detecting presence of cards on the reader
    card_monitor = CardMonitor()
    card_observer = PrintObserver()

    card_monitor.addObserver(card_observer)

    # Run the web socket
    reactor.listenTCP(9000, factory)
    reactor.run()
else:
    print('No valid readers connected.')