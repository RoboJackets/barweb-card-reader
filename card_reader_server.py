import sys
import argparse
from smartcard.util import *
from twisted.python import log
from twisted.internet import reactor
from smartcard.System import readers
from pynput.keyboard import Key, Controller
from smartcard.Exceptions import CardConnectionException
from smartcard.CardMonitoring import CardMonitor, CardObserver
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

VALID_CARD_READERS = ['ACS ACR122U']
connection = False
socket_enabled = False
keyboard_enabled = False
keyboard = False

class PrintObserver(CardObserver):
    def update(self, observable, cards):
        global connection
        global keyboard
        global keyboard_enabled
        global socket_enabled

        added_cards, removed_cards = cards

        if len(added_cards) > 0:
            # Connect to the reader
            connection.connect()

            try:
                # Disable the standard buzzer when a tag is detected. It sounds
                # immediately after placing a tag resulting in people lifting the tag off before
                # we've had a chance to read the data.
                # Note: this runs on the first card presentation, so that one will get two beeps.
                connection.transmit([0xFF, 0x00, 0x52, 0x00, 0x00])

                # App BBBBCD
                select_app_data = connection.transmit([0x90, 0x5a, 0x00, 0x00, 3, 0xcd, 0xbb, 0xbb, 0x00])

                # File 0x01
                read_file_data = connection.transmit([0x90, 0xbd, 0x00, 0x00, 0x07, 0x01, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00])[0]
                file_data_hex = toHexString(read_file_data)
                file_data_byte = bytearray.fromhex(file_data_hex).decode().split("=")
            except (IndexError, CardConnectionException):
                print("Error reading card")

                # TODO: Find a way to send this command without a transmit error since no card is present
                # Until this gets fixed, the LED turns off in error state without a beep

                # Beep twice and change LED to orange to indicate an error
                # p2 = int('11001111', 2)
                # connection.transmit([0xFF, 0x00, 0x40, p2, 0x04, 0x03, 0x00, 0x01, 0x00])
                return 0

            # Beep and change LED to green to signal user we've read the tag.
            # LED stays green until the card is removed
            # Manual Reference: Section 6.2 (Bi-color LED and Buzzer Control)
            p2 = int('10101010', 2)
            connection.transmit([0xFF, 0x00, 0x40, p2, 0x04, 0x02, 0x00, 0x01, 0x01])

            # Pipe card ID to the enabled output(s)
            if socket_enabled:
                WebSocket.broadcast_message(str(file_data_byte[0]))
            if keyboard_enabled:
                keyboard.type(str(file_data_byte[0]))
                keyboard.press(Key.enter)


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

def main():
    global connection
    global keyboard
    global socket_enabled
    global keyboard_enabled

    # Log to standard output
    log.startLogging(sys.stdout)

    # Parse arguments
    parser = argparse.ArgumentParser(description='Apiary NFC Card Reader Server')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-k', action='store_true', help='Keyboard Emulation Mode')
    group.add_argument('-s', action='store_true', help='WebSocket Mode')
    args = parser.parse_args()
    socket_enabled = args.s
    keyboard_enabled = args.k

    if socket_enabled:
        # Initialize web socket
        log.msg('Enabling WebSocket Mode (localhost:9000)')
        factory = WebSocketServerFactory(u'ws://localhost:9000')
        factory.protocol = WebSocket
        reactor.listenTCP(9000, factory)

    if keyboard_enabled:
        # Initialize keyboard emulation
        keyboard = Controller()

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

        reactor.run()
    else:
        print('No valid readers connected.')

if __name__ == '__main__':
    main()