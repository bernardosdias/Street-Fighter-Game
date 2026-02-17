"""
Client - Cliente de rede para conectar ao servidor de jogo
"""

import socket
import threading
import queue
import time
from network.protocol import (
    Message, MessageType, NetworkProtocol,
    create_character_select_message, create_player_input_message,
    create_player_state_update_message, create_ping_message,
    DEFAULT_SERVER_PORT, BUFFER_SIZE
)


class GameClient:
    """Cliente de rede para jogo multiplayer"""

    def __init__(self):
        self.socket = None
        self.connected = False
        self.running = False

        # Identificação
        self.player_id = None
        self.player_name = "Player"

        # Filas de mensagens
        self.incoming_messages = queue.Queue()
        self.outgoing_messages = queue.Queue()

        # Thread para receber mensagens
        self.receive_thread = None
        self.send_thread = None

        # Latência
        self.latency = 0
        self.last_ping_time = 0

    def connect(self, host, port=DEFAULT_SERVER_PORT):
        """
        Conecta ao servidor de jogo

        Args:
            host (str): IP ou hostname do servidor
            port (int): Porta do servidor

        Returns:
            bool: True se conectou com sucesso
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            self.running = True

            print(f"✅ Conectado ao servidor {host}:{port}")

            # Iniciar threads
            self.receive_thread = threading.Thread(
                target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            self.send_thread = threading.Thread(
                target=self._send_loop, daemon=True)
            self.send_thread.start()

            # Aguardar mensagem de ACK com player_id
            timeout = 5.0  # 5 segundos
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    msg = self.incoming_messages.get(timeout=0.1)
                    if msg.msg_type == MessageType.CONNECT_ACK:
                        self.player_id = msg.data.get("player_id")
                        print(f"🎮 {msg.data.get('message', '')}")
                        print(f"🆔 Você é o Player {self.player_id}")
                        return True
                except queue.Empty:
                    continue

            print("❌ Timeout esperando confirmação do servidor")
            self.disconnect()
            return False

        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            self.connected = False
            return False

    def _receive_loop(self):
        """Thread que recebe mensagens do servidor"""
        buffer = b""

        try:
            while self.running and self.connected:
                try:
                    data = self.socket.recv(BUFFER_SIZE)

                    if not data:
                        # Servidor desconectou
                        print("⚠️ Servidor desconectou")
                        self.connected = False
                        break

                    buffer += data

                    # Processar mensagens completas
                    while NetworkProtocol.DELIMITER in buffer:
                        message_data, buffer = buffer.split(
                            NetworkProtocol.DELIMITER, 1)

                        try:
                            message_str = message_data.decode('utf-8')
                            message = Message.from_json(message_str)

                            if message:
                                # Processar ping/pong localmente
                                if message.msg_type == MessageType.PONG:
                                    self._handle_pong(message)
                                else:
                                    # Adicionar à fila para processamento
                                    self.incoming_messages.put(message)
                        except Exception as e:
                            print(f"❌ Erro ao processar mensagem: {e}")

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"❌ Erro ao receber dados: {e}")
                    break

        except Exception as e:
            print(f"❌ Erro no receive loop: {e}")
        finally:
            self.connected = False

    def _send_loop(self):
        """Thread que envia mensagens ao servidor"""
        try:
            while self.running and self.connected:
                try:
                    # Pegar mensagem da fila (com timeout)
                    message = self.outgoing_messages.get(timeout=0.1)

                    # Enviar mensagem
                    encoded = NetworkProtocol.encode_message(message)
                    self.socket.send(encoded)

                except queue.Empty:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"❌ Erro ao enviar mensagem: {e}")
                    break

        except Exception as e:
            print(f"❌ Erro no send loop: {e}")
        finally:
            self.connected = False

    def send_message(self, message):
        """
        Envia uma mensagem ao servidor

        Args:
            message (Message): Mensagem a enviar
        """
        if self.connected:
            self.outgoing_messages.put(message)
        else:
            print("⚠️ Não conectado ao servidor")

    def get_message(self, timeout=None):
        """
        Obtém uma mensagem da fila de mensagens recebidas

        Args:
            timeout (float): Tempo máximo de espera (None = não bloqueia)

        Returns:
            Message ou None
        """
        try:
            if timeout is None:
                return self.incoming_messages.get_nowait()
            else:
                return self.incoming_messages.get(timeout=timeout)
        except queue.Empty:
            return None

    def has_messages(self):
        """Verifica se há mensagens na fila"""
        return not self.incoming_messages.empty()

    def select_character(self, character_name):
        """
        Envia seleção de personagem ao servidor

        Args:
            character_name (str): Nome da personagem selecionada
        """
        msg = create_character_select_message(character_name)
        self.send_message(msg)
        print(f"🎭 Selecionou personagem: {character_name}")

    def send_player_input(self, keys_pressed):
        """
        Envia input do jogador ao servidor

        Args:
            keys_pressed (dict): Dicionário com teclas pressionadas
        """
        msg = create_player_input_message(keys_pressed)
        self.send_message(msg)

    def send_player_state(self, state):
        """
        Envia estado do jogador ao servidor

        Args:
            state (dict): Estado do jogador
        """
        msg = create_player_state_update_message(self.player_id, state)
        self.send_message(msg)

    def ping(self):
        """Envia ping ao servidor para medir latência"""
        self.last_ping_time = time.time()
        msg = create_ping_message()
        self.send_message(msg)

    def _handle_pong(self, message):
        """Processa resposta de pong e calcula latência"""
        if self.last_ping_time > 0:
            self.latency = (time.time() - self.last_ping_time) * 1000  # em ms
            # print(f"🏓 Latência: {self.latency:.1f}ms")

    def disconnect(self):
        """Desconecta do servidor"""
        print("👋 Desconectando...")

        # Enviar mensagem de disconnect
        if self.connected:
            try:
                msg = Message(MessageType.DISCONNECT, {})
                encoded = NetworkProtocol.encode_message(msg)
                self.socket.send(encoded)
            except:
                pass

        self.running = False
        self.connected = False

        # Fechar socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        print("✅ Desconectado")

    def is_connected(self):
        """Verifica se está conectado"""
        return self.connected

    def get_latency(self):
        """Retorna a latência atual em ms"""
        return self.latency


def main():
    """Função de teste do cliente"""
    print("🎮 CLIENTE DE TESTE")
    print("=" * 60)

    # Pedir IP do servidor
    host = input("Digite o IP do servidor (ou Enter para localhost): ").strip()
    if not host:
        host = "127.0.0.1"

    port_str = input(
        f"Digite a porta (Enter para {DEFAULT_SERVER_PORT}): ").strip()
    port = int(port_str) if port_str else DEFAULT_SERVER_PORT

    # Criar e conectar cliente
    client = GameClient()

    if not client.connect(host, port):
        print("❌ Falha ao conectar")
        return

    print("\n✅ Conectado com sucesso!")
    print("💡 Digite 'quit' para sair\n")

    # Loop de teste simples
    try:
        while client.is_connected():
            # Verificar mensagens recebidas
            while client.has_messages():
                msg = client.get_message()
                print(f"📨 Recebido: {msg}")

            # Pedir input do usuário
            try:
                user_input = input("> ")

                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'ping':
                    client.ping()
                elif user_input.lower().startswith('char '):
                    char_name = user_input.split(' ', 1)[1]
                    client.select_character(char_name)
                else:
                    print("Comandos: ping, char <nome>, quit")

            except EOFError:
                break

    except KeyboardInterrupt:
        print("\n")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
