"""
Protocol for network communication in the Street Fighter game.
"""

import json
import time
from enum import Enum


class MessageType(Enum):
    # CONECTION
    CONNECT = "CONNECT"
    CONNECT_ACK = "CONNECT_ACK"
    DISCONNECT = "DISCONNECT"

    # CHARACTER SELECTION
    CHARACTER_SELECT = "CHARACTER_SELECT"
    CHARACTER_SELECTED = "CHARACTER_SELECTED"
    BOTH_READY = "BOTH_READY"

    # GAME STATE
    PLAYER_INPUT = "PLAYER_INPUT"
    GAME_STATE_UPDATE = "GAME_STATE_UPDATE"
    PLAYER_STATE_UPDATE = "PLAYER_STATE_UPDATE"

    # GAME EVENTS
    ATTACK = "ATTACK"
    HIT = "HIT"
    ROUND_OVER = "ROUND_OVER"
    GAME_OVER = "GAME_OVER"

    # CONTROL
    PING = "PING"
    PONG = "PONG"
    ERROR = "ERROR"


class Message:
    def __init__(self, msg_type, data=None):
        self.msg_type = msg_type
        self.data = data if data is not None else {}

    def to_json(self):
        return json.dumps({
            "type": self.msg_type.value if isinstance(self.msg_type, MessageType) else self.msg_type,
            "data": self.data
        })

    @staticmethod
    def from_json(json_str):
        try:
            obj = json.loads(json_str)
            msg_type = MessageType(obj["type"])
            return Message(msg_type, obj.get("data", {}))
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error decoding message: {e}")
            return None

    def __str__(self):
        return f"Message(type={self.msg_type}, data={self.data})"


class NetworkProtocol:

    DELIMITER = b'\n'

    MAX_MESSAGE_SIZE = 4 * 1024 * 1024

    @staticmethod
    def encode_message(message):
        json_str = message.to_json()
        return (json_str + '\n').encode('utf-8')

    @staticmethod
    def decode_message(data):
        messages = []
        if isinstance(data, bytes):
            text = data.decode('utf-8')
        else:
            text = str(data)

        lines = text.split('\n')

        for line in lines:
            if line.strip():
                msg = Message.from_json(line)
                if msg:
                    messages.append(msg)
        return messages


def create_connect_message(player_name):
    return Message(MessageType.CONNECT, {"player_name": player_name})


def create_character_select_message(character_name):
    return Message(MessageType.CHARACTER_SELECT, {"character": character_name})


def create_player_input_message(keys_pressed):
    return Message(MessageType.PLAYER_INPUT, {"keys_pressed": keys_pressed})


def create_player_state_update_message(player_id, state):
    return Message(MessageType.PLAYER_STATE_UPDATE,
                   {"player_id": player_id, "state": state})


def create_game_state_update_message(game_state):
    return Message(MessageType.GAME_STATE_UPDATE, game_state)


def create_attack_message(attacker_id, attack_type):
    return Message(MessageType.ATTACK, {"attacker_id": attacker_id, "attack_type": attack_type})


def create_hit_message(attacker_id, victim_id, damage):
    return Message(MessageType.HIT, {
        "attacker_id": attacker_id,
        "victim_id": victim_id,
        "damage": damage
    })


def create_round_over_message(winner_id):
    return Message(MessageType.ROUND_OVER, {"winner_id": winner_id})


def create_ping_message():
    return Message(MessageType.PING, {"timestamp": time.time()})


def create_pong_message(original_timestamp):
    return Message(MessageType.PONG, {"timestamp": time.time(), "original_timestamp": original_timestamp})


def create_error_message(error_message):
    return Message(MessageType.ERROR, {"error": error_message})


# CONSTANTS
DEFAULT_SERVER_PORT = 5555
BUFFER_SIZE = 4096
TICK_RATE = 60  # 60 updates per second
