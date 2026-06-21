import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import json
import os
import time
from threading import Thread
import asyncio
from PIL import Image
import core

class TabCarrossel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.is_running_carrossel = False
        self.lista_paths_imagens = []
        self.construir_interface()

    def log_car(self, msg): 
        self.txt_log_car.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log_car.see(tk.END)

    def adicionar_imagem(self):
        filepaths = filedialog.askopenfilenames(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")])
        for f in filepaths:
            if f not in self.lista_paths_imagens:
                self.lista_paths_imagens.append(f)
                self.listbox_img.insert(tk.END, os.path.basename(f))

    def remover_imagem(self):
        selecao = self.listbox_img.curselection()
        if selecao:
            idx = selecao[0]
            self.listbox_img.delete(idx)
            self.lista_paths_imagens.pop(idx)

    def salvar_perfil_carrossel(self):
        perfil = {"tempo": self.entry_tempo_car.get(), "imagens": self.lista_paths_imagens}
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Perfil Carrossel", "*.json")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f: json.dump(perfil, f, indent=4)
                messagebox.showinfo("Sucesso", "Perfil salvo com sucesso!")
            except Exception as e: messagebox.showerror("Erro", str(e))

    def carregar_perfil_carrossel(self):
        filepath = filedialog.askopenfilename(filetypes=[("Perfil Carrossel", "*.json")])
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f: perfil = json.load(f)
                self.entry_tempo_car.delete(0, tk.END)
                self.entry_tempo_car.insert(0, str(perfil.get("tempo", "5")))
                self.lista_paths_imagens.clear()
                self.listbox_img.delete(0, tk.END)
                for img in perfil.get("imagens", []):
                    if os.path.exists(img):
                        self.lista_paths_imagens.append(img)
                        self.listbox_img.insert(tk.END, os.path.basename(img))
                self.log_car("Perfil carregado!")
            except Exception as e: messagebox.showerror("Erro", str(e))

    def iniciar_carrossel(self):
        if not self.is_running_carrossel:
            self.is_running_carrossel = True
            self.btn_iniciar_car.config(state="disabled")
            self.btn_parar_car.config(state="normal")
            cfg = {"tempo": float(self.entry_tempo_car.get()), "imagens": self.lista_paths_imagens.copy()}
            Thread(target=self.loop_carrossel, args=(cfg,), daemon=True).start()

    def parar_carrossel(self):
        self.is_running_carrossel = False
        self.btn_iniciar_car.config(state="normal")
        self.btn_parar_car.config(state="disabled")
        self.log_car("Carrossel Parado.")

    def loop_carrossel(self, config):
        self.log_car("Iniciando Carrossel Binário...")
        imagens = config['imagens']
        if not imagens: 
            self.after(0, self.parar_carrossel)
            return
        
        idx = 0
        while self.is_running_carrossel:
            try:
                img_path = imagens[idx]
                placas_ativas = sorted(list(core.clientes_conectados.keys()), key=lambda k: int(k) if str(k).isdigit() else k)
                num_placas = len(placas_ativas)
                
                if num_placas > 0:
                    img = Image.open(img_path).convert("RGB")
                    img_resized = img.resize((128, 32 * num_placas), Image.Resampling.LANCZOS)
                    
                    for i, painel_id in enumerate(placas_ativas):
                        box = (0, i * 32, 128, (i + 1) * 32)
                        fatia = img_resized.crop(box)
                        payload = bytearray()
                        payload.append(ord('I'))
                        payload.append(128)
                        payload.append(32)
                        payload.extend(fatia.tobytes())
                        ws = core.clientes_conectados[painel_id]
                        asyncio.run_coroutine_threadsafe(ws.send(bytes(payload)), core.async_loop)
                        
                    self.log_car(f"Enviando Imagem {idx+1}/{len(imagens)}")
                idx = (idx + 1) % len(imagens)
                time.sleep(config['tempo'])
            except Exception as e:
                self.log_car(f"Erro ao processar imagem: {e}")
                time.sleep(2)

    def construir_interface(self):
        fc_cfg = ttk.LabelFrame(self, text="Imagens e Transição", padding=10)
        fc_cfg.pack(fill="x", padx=10, pady=5)
        tk.Button(fc_cfg, text="➕ Adicionar Imagens", bg="#007bff", fg="white", command=self.adicionar_imagem).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Button(fc_cfg, text="❌ Remover Selecionada", command=self.remover_imagem).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(fc_cfg, text="Tempo por imagem (seg):").grid(row=1, column=0, sticky="e", pady=10)
        self.entry_tempo_car = ttk.Entry(fc_cfg, width=10)
        self.entry_tempo_car.insert(0, "5.0")
        self.entry_tempo_car.grid(row=1, column=1, sticky="w", pady=10)
        self.listbox_img = tk.Listbox(fc_cfg, height=6)
        self.listbox_img.grid(row=2, column=0, columnspan=4, sticky="we", padx=5)
        f_btn_car = ttk.Frame(self, padding=5); f_btn_car.pack(fill="x", padx=10)
        self.btn_iniciar_car = ttk.Button(f_btn_car, text="▶ INICIAR CARROSSEL", command=self.iniciar_carrossel)
        self.btn_iniciar_car.pack(side="left", padx=5)
        self.btn_parar_car = ttk.Button(f_btn_car, text="⏹ PARAR", command=self.parar_carrossel, state="disabled")
        self.btn_parar_car.pack(side="left", padx=5)
        ttk.Button(f_btn_car, text="📂", command=self.carregar_perfil_carrossel, width=4).pack(side="right", padx=2)
        ttk.Button(f_btn_car, text="💾", command=self.salvar_perfil_carrossel, width=4).pack(side="right", padx=2)
        self.txt_log_car = scrolledtext.ScrolledText(self, height=10, bg='black', fg='#00FF00', font=("Consolas", 9))
        self.txt_log_car.pack(fill="both", expand=True, padx=10, pady=(5, 10))