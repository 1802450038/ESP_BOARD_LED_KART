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
from tab_config import TabConfig # <--- NOVO IMPORT

# Janela Principal
janela = tk.Tk()
janela.title("Painel Control Center - ESP32 HUB75 - Gabriel Bellagamba")
janela.geometry("850x760") 

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

# Inicia o Servidor em Background
Thread(target=core.iniciar_servidor_ws, daemon=True).start()

# Inicia a Interface
janela.mainloop()