import tkinter as tk
from tkinter import ttk, colorchooser
import asyncio
import textwrap
import core

class TabGlobal(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.cor_atual_hex_global = "#00FFFF"
        self.construir_interface()

    def enviar_mensagem_global(self):
        texto = self.txt_global.get("1.0", tk.END).strip()
        if not texto: return
        t = int(self.var_tamanho_global.get())
        c_linha, l_placa = (25, 4) if t == 1 else (12, 2)
        linhas = textwrap.wrap(texto, width=c_linha)
        placas_ativas = sorted(list(core.clientes_conectados.keys()), key=lambda k: int(k) if str(k).isdigit() else k)
        for i, p_id in enumerate(placas_ativas):
            chunk = [{"texto": tx, "cor": self.cor_atual_hex_global} for tx in linhas[i*l_placa:(i*l_placa)+l_placa]]
            if not chunk: chunk = [{"texto": " ", "cor": self.cor_atual_hex_global}]
            asyncio.run_coroutine_threadsafe(core.clientes_conectados[p_id].send(core.criar_pacote_json(chunk, t)), core.async_loop)

    def selecionar_cor_global(self):
        c = colorchooser.askcolor(color=self.cor_atual_hex_global)
        if c[1]: 
            self.cor_atual_hex_global = c[1]
            self.btn_cor_global.config(bg=self.cor_atual_hex_global)

    def construir_interface(self):
        f_gl = tk.Frame(self, padx=10, pady=10); f_gl.pack(fill=tk.X)
        tk.Label(f_gl, text="Tamanho:").pack(side=tk.LEFT)
        self.var_tamanho_global = tk.StringVar(value="2")
        ttk.Combobox(f_gl, textvariable=self.var_tamanho_global, values=["1", "2"], width=3, state="readonly").pack(side=tk.LEFT, padx=5)
        self.btn_cor_global = tk.Button(f_gl, text="      ", bg=self.cor_atual_hex_global, command=self.selecionar_cor_global)
        self.btn_cor_global.pack(side=tk.LEFT, padx=15)
        tk.Button(f_gl, text="Disparar", bg="#28a745", fg="white", command=self.enviar_mensagem_global).pack(side=tk.RIGHT, padx=10)
        self.txt_global = tk.Text(self, height=15, font=("Arial", 12))
        self.txt_global.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)