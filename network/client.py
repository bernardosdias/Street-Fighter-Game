import socket
import threading
import queue
import time
from protocol import (
    Message,
    MessageType,
    NetworkProtocol,
    create_character_select_message,
    create_player_input_message,
    create_player_state_update_message,
    create_ping_message,
    DEFAULT_SERVER_PORT, BUFFER_SIZE
)


class GameClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.running = False

        # IDENTIFYING INFORMATION
        self.player_id = None
        self.player_name = "Player"

        # MESSAGE QUEUE
        self.incoming_messages = queue.Queue()
        self.ouytgoing_messages = queue.Queue()

        # MESSAGE THREAD
        self.receive_thread = None
        self.send_thread = None

        # LATENCY
        self.latency = 0
        self.last_ping_time = 0
