"""
Server - Servidor de jogo que gerencia a conexão entre 2 jogadores
"""

import socket
import threading
import time
from network.protocol import (
    Message, MessageType, NetworkProtocol,
    create_connect_message, create_error_message,
    DEFAULT_SERVER_PORT, BUFFER_SIZE
)


class GameServer:
    """Servidor de jogo para 2 jogadores"""
    
    def __init__(self, host='0.0.0.0', port=DEFAULT_SERVER_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        # Jogadores conectados
        self.players = {}  # {player_id: {"socket": socket, "name": str, "character": str}}
        self.player_count = 0
        self.max_players = 2
        
        # Estado do jogo
        self.game_started = False
        self.both_characters_selected = False
        
        # Thread locks
        self.players_lock = threading.Lock()
        
    def start(self):
        """Inicia o servidor"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)
            self.running = True
            
            print(f"🎮 Servidor iniciado em {self.host}:{self.port}")
            print(f"📡 Aguardando jogadores... (0/{self.max_players})")
            
            # Thread para aceitar conexões
            accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            accept_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False
    
    def _accept_connections(self):
        """Thread que aceita novas conexões"""
        while self.running and self.player_count < self.max_players:
            try:
                client_socket, address = self.server_socket.accept()
                
                with self.players_lock:
                    if self.player_count >= self.max_players:
                        # Servidor cheio
                        error_msg = create_error_message("Servidor cheio!")
                        client_socket.send(NetworkProtocol.encode_message(error_msg))
                        client_socket.close()
                        continue
                    
                    # Adicionar jogador
                    self.player_count += 1
                    player_id = self.player_count
                    
                    self.players[player_id] = {
                        "socket": client_socket,
                        "address": address,
                        "name": f"Player{player_id}",
                        "character": None,
                        "ready": False
                    }
                    
                    print(f"✅ Player {player_id} conectado de {address}")
                    print(f"📡 Jogadores conectados: {self.player_count}/{self.max_players}")
                    
                    # Enviar confirmação de conexão
                    ack_msg = Message(MessageType.CONNECT_ACK, {
                        "player_id": player_id,
                        "message": f"Conectado como Player {player_id}"
                    })
                    client_socket.send(NetworkProtocol.encode_message(ack_msg))
                    
                    # Iniciar thread para lidar com este jogador
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(player_id,),
                        daemon=True
                    )
                    client_thread.start()
                    
                    # Se ambos conectaram, notificar
                    if self.player_count == self.max_players:
                        print("🎉 Ambos jogadores conectados! Aguardando seleção de personagens...")
                        
            except Exception as e:
                if self.running:
                    print(f"❌ Erro ao aceitar conexão: {e}")
    
    def _handle_client(self, player_id):
        """Thread que lida com mensagens de um cliente específico"""
        player = self.players[player_id]
        client_socket = player["socket"]
        buffer = b""
        
        try:
            while self.running:
                # Receber dados
                data = client_socket.recv(BUFFER_SIZE)
                
                if not data:
                    # Cliente desconectou
                    print(f"⚠️ Player {player_id} desconectou")
                    break
                
                buffer += data
                
                # Processar mensagens completas
                while NetworkProtocol.DELIMITER in buffer:
                    message_data, buffer = buffer.split(NetworkProtocol.DELIMITER, 1)
                    
                    # Decodificar mensagem
                    try:
                        message_str = message_data.decode('utf-8')
                        message = Message.from_json(message_str)
                        
                        if message:
                            self._process_message(player_id, message)
                    except Exception as e:
                        print(f"❌ Erro ao processar mensagem: {e}")
                        
        except Exception as e:
            print(f"❌ Erro na conexão com Player {player_id}: {e}")
        finally:
            self._remove_player(player_id)
    
    def _process_message(self, player_id, message):
        """Processa uma mensagem recebida de um jogador"""
        
        if message.msg_type == MessageType.CHARACTER_SELECT:
            # Jogador selecionou personagem
            character = message.data.get("character")
            self.players[player_id]["character"] = character
            self.players[player_id]["ready"] = True
            
            print(f"🎭 Player {player_id} selecionou: {character}")
            
            # Notificar o outro jogador
            other_player_id = 2 if player_id == 1 else 1
            if other_player_id in self.players:
                notify_msg = Message(MessageType.CHARACTER_SELECTED, {
                    "player_id": player_id,
                    "character": character
                })
                self._send_to_player(other_player_id, notify_msg)
            
            # Verificar se ambos selecionaram
            if all(p["ready"] for p in self.players.values()):
                self._start_game()
        
        elif message.msg_type == MessageType.PLAYER_INPUT:
            # Input do jogador - repassar para o outro jogador
            other_player_id = 2 if player_id == 1 else 1
            if other_player_id in self.players:
                # Adicionar player_id à mensagem
                message.data["player_id"] = player_id
                self._send_to_player(other_player_id, message)
        
        elif message.msg_type == MessageType.PLAYER_STATE:
            # Estado do jogador - repassar para o outro jogador
            other_player_id = 2 if player_id == 1 else 1
            if other_player_id in self.players:
                self._send_to_player(other_player_id, message)
        
        elif message.msg_type == MessageType.ATTACK:
            # Ataque - broadcast para todos
            self._broadcast_message(message, exclude_player=player_id)
        
        elif message.msg_type == MessageType.HIT:
            # Hit - broadcast para todos
            self._broadcast_message(message)
        
        elif message.msg_type == MessageType.ROUND_OVER:
            # Round over - broadcast para todos
            self._broadcast_message(message)
        
        elif message.msg_type == MessageType.PING:
            # Ping - responder com pong
            pong_msg = Message(MessageType.PONG, message.data)
            self._send_to_player(player_id, pong_msg)
        
        elif message.msg_type == MessageType.DISCONNECT:
            # Jogador quer desconectar
            print(f"👋 Player {player_id} desconectando...")
            self._remove_player(player_id)
    
    def _start_game(self):
        """Inicia o jogo quando ambos jogadores estão prontos"""
        if not self.game_started:
            self.game_started = True
            print("🎮 JOGO INICIADO!")
            
            # Enviar mensagem BOTH_READY para ambos jogadores
            ready_msg = Message(MessageType.BOTH_READY, {
                "player1_character": self.players[1]["character"],
                "player2_character": self.players[2]["character"]
            })
            
            self._broadcast_message(ready_msg)
    
    def _send_to_player(self, player_id, message):
        """Envia uma mensagem para um jogador específico"""
        if player_id in self.players:
            try:
                encoded = NetworkProtocol.encode_message(message)
                self.players[player_id]["socket"].send(encoded)
            except Exception as e:
                print(f"❌ Erro ao enviar para Player {player_id}: {e}")
    
    def _broadcast_message(self, message, exclude_player=None):
        """Envia uma mensagem para todos os jogadores"""
        for player_id in list(self.players.keys()):
            if exclude_player and player_id == exclude_player:
                continue
            self._send_to_player(player_id, message)
    
    def _remove_player(self, player_id):
        """Remove um jogador e notifica o outro"""
        with self.players_lock:
            if player_id in self.players:
                try:
                    self.players[player_id]["socket"].close()
                except:
                    pass
                
                del self.players[player_id]
                self.player_count -= 1
                
                print(f"❌ Player {player_id} removido")
                print(f"📡 Jogadores conectados: {self.player_count}/{self.max_players}")
                
                # Notificar o outro jogador
                other_player_id = 2 if player_id == 1 else 1
                if other_player_id in self.players:
                    disconnect_msg = Message(MessageType.DISCONNECT, {
                        "player_id": player_id,
                        "message": f"Player {player_id} desconectou"
                    })
                    self._send_to_player(other_player_id, disconnect_msg)
    
    def stop(self):
        """Para o servidor"""
        print("\n🛑 Parando servidor...")
        self.running = False
        
        # Fechar todas as conexões
        with self.players_lock:
            for player_id in list(self.players.keys()):
                try:
                    self.players[player_id]["socket"].close()
                except:
                    pass
        
        # Fechar socket do servidor
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("✅ Servidor parado")
    
    def get_local_ip(self):
        """Obtém o IP local da máquina"""
        try:
            # Truque: conecta a um endereço externo para descobrir o IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"


def main():
    """Função principal para testar o servidor"""
    server = GameServer()
    
    if server.start():
        print(f"\n{'='*60}")
        print(f"🎮 SERVIDOR DE JOGO INICIADO")
        print(f"{'='*60}")
        print(f"🌐 IP Local: {server.get_local_ip()}:{server.port}")
        print(f"🏠 Localhost: 127.0.0.1:{server.port}")
        print(f"{'='*60}")
        print(f"\n💡 Partilha o IP com o outro jogador!")
        print(f"⌨️  Pressiona Ctrl+C para parar o servidor\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n")
            server.stop()


if __name__ == "__main__":
    main()