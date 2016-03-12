#!/usr/bin/env python2.7

""""
Copyright 2016 Studentmediene i Trondheim AS

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""""

import sys

from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import *

from twisted.python import log
from twisted.internet import reactor

from autobahn.websocket import WebSocketServerProtocol, WebSocketServerFactory


VALID_CARD_READERS = ['ACS ACR122U 00 00']


class PrintObserver(CardObserver):
    def update(self, observable, cards):
        """
        Read data from present card, and pipe card ID to the web socket
        """
        added_cards, removed_cards = cards

        if len(added_cards) > 0:
            # Connect to the reader
            connection.connect()

            # Fetche card ID
            data = connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])[0]
            uid = toHexString(list(reversed(data))).replace(' ', '')
            card_number = int(uid, 16)

            # Pipe card ID to the web socket
            WebSocket.broadcast_message(str(card_number))


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
factory = WebSocketServerFactory(u'ws://localhost:9000', debug=False)
factory.protocol = WebSocket

# Initialize readers
r = readers()
valid_reader_index = -1


# Check if any valid readers are connected
for i in range(len(r)):
    if str(r[i]) in VALID_CARD_READERS:
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
