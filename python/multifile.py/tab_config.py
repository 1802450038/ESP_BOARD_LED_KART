import tkinter as tk
from tkinter import ttk, messagebox
import json
import asyncio
import core

class TabConfig(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.construir_interface()
        self.atualizar_lista_placas()

    def atualizar_lista_placas(self):
        placas = sorted(list(core.clientes_conectados.keys()), key=lambda k: int(k) if str(k).isdigit() else k)
        self.combo_placas_ajustes['values'] = placas
        
        if placas and not self.combo_placas_ajustes.get():
            self.combo_placas_ajustes.current(0)
        elif not placas:
            self.combo_placas_ajustes.set('') 
            
        self.after(2000, self.atualizar_lista_placas)

    def enviar_config_placa(self):
        cliente_id = self.combo_placas_ajustes.get()
        
        if not cliente_id or cliente_id not in core.clientes_conectados:
            messagebox.showwarning("Atenção", "Selecione uma placa conectada primeiro!")
            return

        try:
            brilho_str = self.entry_brilho.get().strip()
            if brilho_str:
                brilho_val = int(brilho_str)
                if not (0 <= brilho_val <= 255): 
                    raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "O brilho deve ser um número inteiro entre 0 e 255.")
            return
            
        try:
            chain_str = self.combo_chain.get().strip()
            if chain_str:
                chain_val = int(chain_str)
                if chain_val < 1:
                    raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "A quantidade de painéis deve ser no mínimo 1.")
            return

        pacote = {"comando": "config"}
        if brilho_str:
            pacote["brilho"] = brilho_val
        if chain_str:
            pacote["chain"] = chain_val
            
        if "brilho" not in pacote and "chain" not in pacote:
            messagebox.showwarning("Atenção", "Preencha pelo menos um dos campos (Brilho ou Chain) para enviar a configuração.")
            return

        pacote_json = json.dumps(pacote)
        
        asyncio.run_coroutine_threadsafe(
            core.clientes_conectados[cliente_id].send(pacote_json), 
            core.async_loop
        )
        
        msg_sucesso = f"Configurações enviadas para a placa '{cliente_id}'!\n\n"
        if "brilho" in pacote: msg_sucesso += f"- Brilho: {brilho_val}\n"
        if "chain" in pacote: msg_sucesso += f"- Painéis (Chain): {chain_val}\n\n*A placa será reiniciada se o Chain tiver sido alterado."
        
        messagebox.showinfo("Sucesso", msg_sucesso)

    def construir_interface(self):
        f_ajustes = ttk.LabelFrame(self, text="Configuração Remota das Placas", padding=10)
        f_ajustes.pack(fill="x", padx=10, pady=15)

        ttk.Label(f_ajustes, text="Selecione a Placa Conectada:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_placas_ajustes = ttk.Combobox(f_ajustes, state="readonly", width=25)
        self.combo_placas_ajustes.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f_ajustes, text="Novo Brilho (0-255):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_brilho = ttk.Entry(f_ajustes, width=27)
        self.entry_brilho.insert(0, "") # Removido o default para poder enviar só o chain se quiser
        self.entry_brilho.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(f_ajustes, text="Quantidade de painéis por placa:").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_chain = ttk.Combobox(f_ajustes, state="readonly", width=24, values=[str(i) for i in range(1, 11)])
        self.combo_chain.set("")
        self.combo_chain.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(f_ajustes, text="▶ Enviar Configurações", command=self.enviar_config_placa).grid(row=3, column=0, columnspan=2, pady=15)