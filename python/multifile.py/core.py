import asyncio
import websockets
import socket
import json
from datetime import datetime

# Variáveis Globais
clientes_conectados = {}
async_loop = None

# Lista de funções que a interface pede para o core executar quando alguém conecta/desconecta
on_client_connect = []
on_client_disconnect = []


dados_grid_atual = []
cols_exibir_atual = []
ultima_att_grid = "Aguardando..."

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception: return "127.0.0.1"

def formatar_tempo(valor):
    if not valor: return "00:00:000"
    try:
        if isinstance(valor, datetime): return f"{valor.minute:02d}:{valor.second:02d}:{valor.microsecond // 1000:03d}"
        valor_str = str(valor)
        if " " in valor_str: valor_str = valor_str.split(" ")[1] 
        partes = valor_str.split(".")
        h, m, s = partes[0].split(":") 
        milissegundos = int((partes[1] + "000")[:3]) if len(partes) > 1 else 0
        return f"{int(m):02d}:{int(s):02d}:{milissegundos:03d}"
    except Exception: return str(valor)[:9]

def criar_pacote_json(linhas_dados, tamanho):
    return json.dumps({"linhas": linhas_dados, "tamanho": int(tamanho)})

async def gerenciar_conexao(websocket, *args):
    client_id_interno = None
    try:
        primeira_mensagem = await websocket.recv()
        client_id_interno = primeira_mensagem.decode('utf-8') if isinstance(primeira_mensagem, bytes) else primeira_mensagem
        print(f"[+] Placa conectada! ID: {client_id_interno}")
        clientes_conectados[client_id_interno] = websocket
        
        for cb in on_client_connect: cb(client_id_interno)
            
        async for mensagem in websocket: pass 
    except websockets.exceptions.ConnectionClosed: pass 
    except Exception as e: print(f"[!] Erro: {e}")
    finally:
        if client_id_interno:
            if client_id_interno in clientes_conectados: del clientes_conectados[client_id_interno]
            for cb in on_client_disconnect: cb(client_id_interno)

async def servidor_async():
    async with websockets.serve(gerenciar_conexao, "0.0.0.0", 8765, ping_interval=5, ping_timeout=15):
        await asyncio.Future()

def iniciar_servidor_ws():
    global async_loop
    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)
    async_loop.run_until_complete(servidor_async())