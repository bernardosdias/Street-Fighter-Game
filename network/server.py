"""
Server - Servidor de jogo que gerencia a conexao entre 2 jogadores
"""

import socket
import threading
import time
from network.protocol import (
    Message,
    MessageType,
    NetworkProtocol,
    create_error_message,
    create_game_state_update_message,
    create_map_selected_message,
    DEFAULT_SERVER_PORT,
    BUFFER_SIZE,
)


class GameServer:
    """Servidor de jogo para 2 jogadores"""

    def __init__(self, host="0.0.0.0", port=DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False

        self.players = {}
        self.player_count = 0
        self.max_players = 2
        self.game_started = False

        self.players_lock = threading.RLock()

        # Server-authoritative match state
        self.hit_cooldown_ms = 250
        self.round_reset_delay_ms = 2000
        self.last_hit_ms = {1: 0, 2: 0}
        self.match_state = {}
        self._reset_match_state()
        self.selected_map_id = "default"

    def _reset_match_state(self):
        self.match_state = {
            "player1_health": 100,
            "player2_health": 100,
            "score": [0, 0],
            "round_over": False,
            "round_winner": None,
            "round_over_time_ms": 0,
        }
        self.last_hit_ms = {1: 0, 2: 0}
        self.selected_map_id = "default"

    def _reset_round_state(self):
        self.match_state["player1_health"] = 100
        self.match_state["player2_health"] = 100
        self.match_state["round_over"] = False
        self.match_state["round_winner"] = None
        self.match_state["round_over_time_ms"] = 0
        self.last_hit_ms = {1: 0, 2: 0}

    def _update_player_count(self):
        self.player_count = len(self.players)

    def _next_available_player_id(self):
        for candidate in range(1, self.max_players + 1):
            if candidate not in self.players:
                return candidate
        return None

    def start(self):
        """Inicia o servidor"""
        try:
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)
            self.running = True

            print(f"Servidor iniciado em {self.host}:{self.port}")
            print(f"Aguardando jogadores... (0/{self.max_players})")

            accept_thread = threading.Thread(
                target=self._accept_connections, daemon=True)
            accept_thread.start()

            game_loop_thread = threading.Thread(
                target=self._game_loop, daemon=True)
            game_loop_thread.start()
            return True
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
            return False

    def _game_loop(self):
        while self.running:
            reset_round = False
            with self.players_lock:
                if self.game_started and self.match_state["round_over"]:
                    now_ms = int(time.time() * 1000)
                    if now_ms - self.match_state["round_over_time_ms"] >= self.round_reset_delay_ms:
                        self._reset_round_state()
                        reset_round = True

            if reset_round:
                self._broadcast_game_state(reset_round=True)

            time.sleep(0.05)

    def _accept_connections(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
            except Exception as e:
                if self.running:
                    print(f"Erro ao aceitar conexao: {e}")
                continue

            with self.players_lock:
                if len(self.players) >= self.max_players:
                    error_msg = create_error_message("Servidor cheio!")
                    try:
                        client_socket.send(
                            NetworkProtocol.encode_message(error_msg))
                    except Exception:
                        pass
                    client_socket.close()
                    continue

                player_id = self._next_available_player_id()
                if player_id is None:
                    client_socket.close()
                    continue

                self.players[player_id] = {
                    "socket": client_socket,
                    "address": address,
                    "name": f"Player{player_id}",
                    "character": None,
                    "ready": False,
                    "state": {},
                }
                self._update_player_count()

                print(f"Player {player_id} conectado de {address}")
                print(
                    f"Jogadores conectados: {self.player_count}/{self.max_players}")

                ack_msg = Message(
                    MessageType.CONNECT_ACK,
                    {"player_id": player_id,
                        "message": f"Conectado como Player {player_id}"},
                )
                try:
                    client_socket.send(NetworkProtocol.encode_message(ack_msg))
                except Exception:
                    self._remove_player(player_id)
                    continue

            client_thread = threading.Thread(
                target=self._handle_client,
                args=(player_id,),
                daemon=True,
            )
            client_thread.start()

    def _handle_client(self, player_id):
        buffer = b""

        with self.players_lock:
            player = self.players.get(player_id)
            if not player:
                return
            client_socket = player["socket"]

        try:
            while self.running:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                buffer += data
                while NetworkProtocol.DELIMITER in buffer:
                    message_data, buffer = buffer.split(
                        NetworkProtocol.DELIMITER, 1)
                    try:
                        message_str = message_data.decode("utf-8")
                        message = Message.from_json(message_str)
                    except Exception:
                        message = None

                    if message:
                        self._process_message(player_id, message)
        except Exception as e:
            if self.running:
                print(f"Erro na conexao com Player {player_id}: {e}")
        finally:
            self._remove_player(player_id)

    def _process_message(self, player_id, message):
        with self.players_lock:
            if player_id not in self.players:
                return

        if message.msg_type == MessageType.CHARACTER_SELECT:
            character = message.data.get("character")
            with self.players_lock:
                if player_id not in self.players:
                    return
                self.players[player_id]["character"] = character
                self.players[player_id]["ready"] = True
                others = [pid for pid in self.players.keys() if pid !=
                          player_id]
                both_ready = (
                    len(self.players) == self.max_players
                    and all(p["ready"] for p in self.players.values())
                )

            for other_player_id in others:
                notify_msg = Message(
                    MessageType.CHARACTER_SELECTED,
                    {"player_id": player_id, "character": character},
                )
                self._send_to_player(other_player_id, notify_msg)

            if both_ready:
                self._start_game()
            return

        if message.msg_type == MessageType.PLAYER_STATE_UPDATE:
            with self.players_lock:
                if player_id in self.players:
                    self.players[player_id]["state"] = message.data.get(
                        "state", {})
            self._send_to_other_player(
                player_id, message, include_player_id=False)
            return

        if message.msg_type == MessageType.HIT:
            self._handle_hit_message(player_id, message)
            return

        if message.msg_type == MessageType.MAP_SELECT:
            map_id = message.data.get("map_id", "default")
            with self.players_lock:
                # Host/player 1 escolhe o mapa para manter decisao unica.
                if player_id != 1 or not self.game_started:
                    return
                self.selected_map_id = map_id

            self._broadcast_message(create_map_selected_message(map_id))
            return

        if message.msg_type == MessageType.PLAYER_INPUT:
            self._send_to_other_player(
                player_id, message, include_player_id=True)
            return

        if message.msg_type == MessageType.ATTACK:
            self._broadcast_message(message, exclude_player=player_id)
            return

        if message.msg_type == MessageType.ROUND_OVER:
            return

        if message.msg_type == MessageType.PING:
            pong_msg = Message(MessageType.PONG, message.data)
            self._send_to_player(player_id, pong_msg)
            return

        if message.msg_type == MessageType.DISCONNECT:
            self._remove_player(player_id)

    def _handle_hit_message(self, sender_id, message):
        attacker_id = message.data.get("attacker_id")
        victim_id = message.data.get("victim_id")
        requested_damage = int(message.data.get("damage", 10))
        damage = max(1, min(requested_damage, 30))

        with self.players_lock:
            if not self.game_started:
                return
            if attacker_id != sender_id:
                return
            if attacker_id not in (1, 2) or victim_id not in (1, 2):
                return
            if attacker_id == victim_id:
                return
            if attacker_id not in self.players or victim_id not in self.players:
                return
            if self.match_state["round_over"]:
                return

            now_ms = int(time.time() * 1000)
            if now_ms - self.last_hit_ms.get(attacker_id, 0) < self.hit_cooldown_ms:
                return

            victim_state = self.players[victim_id].get("state", {})
            victim_defending = bool(victim_state.get("defending", False))
            applied_damage = 0 if victim_defending else damage

            if victim_id == 1:
                self.match_state["player1_health"] = max(
                    0, self.match_state["player1_health"] - applied_damage
                )
                victim_health = self.match_state["player1_health"]
            else:
                self.match_state["player2_health"] = max(
                    0, self.match_state["player2_health"] - applied_damage
                )
                victim_health = self.match_state["player2_health"]

            self.last_hit_ms[attacker_id] = now_ms

            if victim_health <= 0 and not self.match_state["round_over"]:
                self.match_state["round_over"] = True
                self.match_state["round_winner"] = attacker_id
                self.match_state["round_over_time_ms"] = now_ms
                if attacker_id == 1:
                    self.match_state["score"][0] += 1
                else:
                    self.match_state["score"][1] += 1

        self._broadcast_game_state()

    def _broadcast_game_state(self, reset_round=False):
        with self.players_lock:
            payload = {
                "player1_health": self.match_state["player1_health"],
                "player2_health": self.match_state["player2_health"],
                "score": list(self.match_state["score"]),
                "round_over": self.match_state["round_over"],
                "round_winner": self.match_state["round_winner"],
                "reset_round": reset_round,
            }
        self._broadcast_message(create_game_state_update_message(payload))

    def _send_to_other_player(self, player_id, message, include_player_id):
        with self.players_lock:
            other_players = [
                pid for pid in self.players.keys() if pid != player_id]

        if include_player_id:
            message.data["player_id"] = player_id

        for other_id in other_players:
            self._send_to_player(other_id, message)

    def _start_game(self):
        with self.players_lock:
            if self.game_started:
                return
            if 1 not in self.players or 2 not in self.players:
                return

            p1_character = self.players[1]["character"]
            p2_character = self.players[2]["character"]
            self._reset_match_state()
            self.game_started = True

        ready_msg = Message(
            MessageType.BOTH_READY,
            {"player1_character": p1_character, "player2_character": p2_character},
        )
        self._broadcast_message(ready_msg)
        self._broadcast_game_state(reset_round=True)

    def _send_to_player(self, player_id, message):
        with self.players_lock:
            player = self.players.get(player_id)
            if not player:
                return
            player_socket = player["socket"]

        try:
            encoded = NetworkProtocol.encode_message(message)
            player_socket.send(encoded)
        except Exception:
            self._remove_player(player_id)

    def _broadcast_message(self, message, exclude_player=None):
        with self.players_lock:
            player_ids = list(self.players.keys())

        for player_id in player_ids:
            if exclude_player is not None and player_id == exclude_player:
                continue
            self._send_to_player(player_id, message)

    def _remove_player(self, player_id):
        with self.players_lock:
            player = self.players.pop(player_id, None)
            if not player:
                return
            self._update_player_count()
            if self.player_count < self.max_players:
                self.game_started = False
                self._reset_match_state()

            try:
                player["socket"].close()
            except Exception:
                pass

            remaining_ids = list(self.players.keys())

        print(f"Player {player_id} removido")
        print(f"Jogadores conectados: {self.player_count}/{self.max_players}")

        disconnect_msg = Message(
            MessageType.DISCONNECT,
            {"player_id": player_id, "message": f"Player {player_id} desconectou"},
        )
        for other_player_id in remaining_ids:
            self._send_to_player(other_player_id, disconnect_msg)

    def stop(self):
        print("\nParando servidor...")
        self.running = False

        with self.players_lock:
            players = list(self.players.values())
            self.players.clear()
            self._update_player_count()
            self.game_started = False
            self._reset_match_state()

        for player in players:
            try:
                player["socket"].close()
            except Exception:
                pass

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

        print("Servidor parado")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"


def main():
    server = GameServer()

    if server.start():
        print(f"\n{'=' * 60}")
        print("SERVIDOR DE JOGO INICIADO")
        print(f"{'=' * 60}")
        print(f"IP Local: {server.get_local_ip()}:{server.port}")
        print(f"Localhost: 127.0.0.1:{server.port}")
        print(f"{'=' * 60}")
        print("\nPartilha o IP com o outro jogador!")
        print("Pressiona Ctrl+C para parar o servidor\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n")
            server.stop()


if __name__ == "__main__":
    main()
