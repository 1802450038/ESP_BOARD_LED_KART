import tkinter as tk
from tkinter import ttk
from threading import Thread
import core

# Importação de todas as abas
from tab_manual import TabManual
from tab_kart import TabKart
from tab_global import TabGlobal
from tab_carrossel import TabCarrossel
from tab_redim import TabRedim
from tab_config import TabConfig
from board_software_control import TabBoardControl # <--- NOVO IMPORT

import os
import sys

# Função para carregar recursos no executável (PyInstaller)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Janela Principal
janela = tk.Tk()
janela.title("Painel Control Center - ESP32 HUB75 - Gabriel Bellagamba")
janela.geometry("850x760") 

try:
    janela.iconbitmap(resource_path("kart_logo.ico"))
except Exception as e:
    pass

lbl_ip = tk.Label(janela, text=f"Servidor WS Rodando em: ws://{core.obter_ip_local()}:8765", font=("Arial", 11, "bold"), fg="#d9534f")
lbl_ip.pack(pady=10)

notebook = ttk.Notebook(janela)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

aba_manual = TabManual(notebook)
notebook.add(aba_manual, text="Controle Manual")

aba_kart = TabKart(notebook)
notebook.add(aba_kart, text="Grid de Corrida")

aba_global = TabGlobal(notebook)
notebook.add(aba_global, text="Mensagem Global")

aba_carrossel = TabCarrossel(notebook)
notebook.add(aba_carrossel, text="Videowall (Carrossel)")

aba_redim = TabRedim(notebook)
notebook.add(aba_redim, text="Ferramentas (Imagens)")

# ---> NOVA ABA ADICIONADA AQUI <---
aba_config = TabConfig(notebook)
notebook.add(aba_config, text="Ajustes (Placas)")

aba_board = TabBoardControl(notebook)
notebook.add(aba_board, text="Gravar Placa (Firmware)")

# Inicia o Servidor em Background
Thread(target=core.iniciar_servidor_ws, daemon=True).start()

# Inicia a Interface
janela.mainloop()

# Compilar projeto
# python -m PyInstaller --noconsole --onefile --icon="C:\Users\gabri\Desktop\ESP_MESH\python\multifile\meu_icone.ico" main.py