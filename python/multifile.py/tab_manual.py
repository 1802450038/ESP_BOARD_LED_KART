import tkinter as tk
from tkinter import ttk, colorchooser
import asyncio
import core

class TabManual(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.widgets_clientes = {}
        self.cor_atual_hex_manual = "#FFFFFF"
        self.construir_interface()
        
        # AQUI ESTAVA O ERRO! Agora os nomes estão iguaizinhos ao core.py
        core.on_client_connect.append(self.adicionar_cliente_gui)
        core.on_client_disconnect.append(self.remover_cliente_gui)

    def construir_interface(self):
        frame_estilo_manual = tk.Frame(self, padx=10, pady=10)
        frame_estilo_manual.pack(fill=tk.X)
        tk.Label(frame_estilo_manual, text="Tamanho do Texto:").pack(side=tk.LEFT)
        self.var_tamanho_manual = tk.StringVar(value="2")
        ttk.Combobox(frame_estilo_manual, textvariable=self.var_tamanho_manual, values=["1", "2"], width=3, state="readonly").pack(side=tk.LEFT, padx=5)
        tk.Label(frame_estilo_manual, text="Cor:").pack(side=tk.LEFT, padx=(15, 5))
        self.btn_cor_manual = tk.Button(frame_estilo_manual, text="      ", bg=self.cor_atual_hex_manual, relief=tk.RAISED, command=self.selecionar_cor_manual, cursor="hand2")
        self.btn_cor_manual.pack(side=tk.LEFT)
        self.frame_lista_manual = tk.Frame(self)
        self.frame_lista_manual.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def selecionar_cor_manual(self):
        cor = colorchooser.askcolor(title="Cor", color=self.cor_atual_hex_manual)
        if cor[1]: 
            self.cor_atual_hex_manual = cor[1]
            self.btn_cor_manual.config(bg=self.cor_atual_hex_manual)

    def enviar_mensagem_manual(self, client_id, entry_widget):
        msg = entry_widget.get()
        if not msg: return
        linhas_dados = [{"texto": t, "cor": self.cor_atual_hex_manual} for t in str(msg).split('\\n')]
        pacote = core.criar_pacote_json(linhas_dados, self.var_tamanho_manual.get())
        if client_id in core.clientes_conectados and core.async_loop:
            asyncio.run_coroutine_threadsafe(core.clientes_conectados[client_id].send(pacote), core.async_loop)
            entry_widget.delete(0, tk.END)

    def adicionar_cliente_gui(self, client_id):
        def _add():
            if client_id in self.widgets_clientes: return 
            f = tk.Frame(self.frame_lista_manual)
            f.pack(fill=tk.X, pady=5, padx=5)
            tk.Label(f, text=f"ID: {client_id}", width=10, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
            e = tk.Entry(f)
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            tk.Button(f, text="Enviar", bg="#007bff", fg="white", command=lambda: self.enviar_mensagem_manual(client_id, e)).pack(side=tk.RIGHT)
            self.widgets_clientes[client_id] = f
        self.after(0, _add)

    def remover_cliente_gui(self, client_id):
        def _rem():
            if client_id in self.widgets_clientes: 
                self.widgets_clientes[client_id].destroy()
                del self.widgets_clientes[client_id]
        self.after(0, _rem)