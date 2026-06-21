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
            brilho_val = int(self.entry_brilho.get())
            if not (0 <= brilho_val <= 255): 
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "O brilho deve ser um número inteiro entre 0 e 255.")
            return

        # Envia APENAS o comando de brilho
        pacote = json.dumps({"comando": "config", "brilho": brilho_val})
        
        asyncio.run_coroutine_threadsafe(
            core.clientes_conectados[cliente_id].send(pacote), 
            core.async_loop
        )
        
        messagebox.showinfo("Sucesso", f"O brilho da placa '{cliente_id}' foi ajustado para {brilho_val} com sucesso!")

    def construir_interface(self):
        f_ajustes = ttk.LabelFrame(self, text="Configuração Remota das Placas", padding=10)
        f_ajustes.pack(fill="x", padx=10, pady=15)

        ttk.Label(f_ajustes, text="Selecione a Placa Conectada:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_placas_ajustes = ttk.Combobox(f_ajustes, state="readonly", width=25)
        self.combo_placas_ajustes.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f_ajustes, text="Novo Brilho (0-255):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_brilho = ttk.Entry(f_ajustes, width=27)
        self.entry_brilho.insert(0, "15")
        self.entry_brilho.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(f_ajustes, text="▶ Aplicar Brilho Imediatamente", command=self.enviar_config_placa).grid(row=2, column=0, columnspan=2, pady=15)