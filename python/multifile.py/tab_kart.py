import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, scrolledtext, messagebox
from threading import Thread
import asyncio
import json
import pyodbc
import time
import os
from datetime import datetime
import core

class TabKart(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.is_running_kart = False
        self.thread_id_kart = 0  # <--- NOVA VARIÁVEL: Identificador único da Thread
        self.cor_atual_hex_kart = "#FFFF00"
        self.construir_interface()
        
    def log_kart(self, msg): 
        self.txt_log_kart.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log_kart.see(tk.END)

    def buscar_arquivo_db(self): 
        f = filedialog.askopenfilename(filetypes=[("Access DB", "*.accdb")])
        if f: 
            self.entry_db_kart.delete(0, tk.END)
            self.entry_db_kart.insert(0, f)

    def carregar_colunas_db(self):
        db_path = self.entry_db_kart.get()
        tabela = self.entry_tabela_kart.get()
        if not db_path or not tabela:
            messagebox.showwarning("Atenção", "Selecione o banco de dados e informe a tabela primeiro!")
            return
        try:
            conn_str = (r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};" f"DBQ={db_path};")
            conn = pyodbc.connect(conn_str, autocommit=True)
            c = conn.cursor()
            c.execute(f"SELECT TOP 1 * FROM {tabela}")
            colunas = [col[0] for col in c.description]
            conn.close()
            
            self.lb_disp.delete(0, tk.END)
            self.lb_sel.delete(0, tk.END)
            for col in colunas: self.lb_disp.insert(tk.END, col)
                
            self.cb_col_id['values'] = colunas
            self.cb_col_ordem['values'] = colunas
            
            if "Numero" in colunas: self.cb_col_id.set("Numero")
            if "Posicao" in colunas: self.cb_col_ordem.set("Posicao")
            
            self.log_kart(f"Sucesso: {len(colunas)} colunas carregadas.")
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível carregar as colunas:\n{e}")

    def mover_para_selecionadas(self):
        selecionados = self.lb_disp.curselection()
        for i in reversed(selecionados):
            self.lb_sel.insert(tk.END, self.lb_disp.get(i))
            self.lb_disp.delete(i)

    def mover_para_disponiveis(self):
        selecionados = self.lb_sel.curselection()
        for i in reversed(selecionados):
            self.lb_disp.insert(tk.END, self.lb_sel.get(i))
            self.lb_sel.delete(i)

    def mover_cima(self):
        selecionados = self.lb_sel.curselection()
        for pos in selecionados:
            if pos == 0: continue
            texto = self.lb_sel.get(pos)
            self.lb_sel.delete(pos)
            self.lb_sel.insert(pos - 1, texto)
            self.lb_sel.selection_set(pos - 1)

    def mover_baixo(self):
        selecionados = self.lb_sel.curselection()
        for pos in reversed(selecionados):
            if pos == self.lb_sel.size() - 1: continue
            texto = self.lb_sel.get(pos)
            self.lb_sel.delete(pos)
            self.lb_sel.insert(pos + 1, texto)
            self.lb_sel.selection_set(pos + 1)

    def selecionar_cor_kart(self):
        c = colorchooser.askcolor(color=self.cor_atual_hex_kart)
        if c[1]: 
            self.cor_atual_hex_kart = c[1]
            self.btn_cor_kart.config(bg=self.cor_atual_hex_kart)

    def salvar_perfil_kart(self):
        perfil = {
            "db": self.entry_db_kart.get(), "tab": self.entry_tabela_kart.get(), "int": self.entry_intervalo_kart.get(),
            "pilotos": self.entry_pilotos_kart.get(), "tamanho": self.var_tamanho_kart.get(), "cor": self.cor_atual_hex_kart,
            "modo_colorido": self.var_modo_colorido.get(),
            "col_id": self.cb_col_id.get(), "col_ordem": self.cb_col_ordem.get(), "ordem_dir": self.cb_ordem_dir.get(),
            "cols_exibicao": list(self.lb_sel.get(0, tk.END))
        }
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Perfil de Corrida", "*.json")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f: json.dump(perfil, f, indent=4)
                messagebox.showinfo("Sucesso", "Perfil salvo com sucesso!")
            except Exception as e: messagebox.showerror("Erro", str(e))

    def carregar_perfil_kart(self):
        filepath = filedialog.askopenfilename(filetypes=[("Perfil de Corrida", "*.json")])
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f: perfil = json.load(f)
                self.entry_db_kart.delete(0, tk.END); self.entry_db_kart.insert(0, perfil.get("db", ""))
                self.entry_tabela_kart.delete(0, tk.END); self.entry_tabela_kart.insert(0, perfil.get("tab", ""))
                self.entry_intervalo_kart.delete(0, tk.END); self.entry_intervalo_kart.insert(0, str(perfil.get("int", "2")))
                self.entry_pilotos_kart.delete(0, tk.END); self.entry_pilotos_kart.insert(0, perfil.get("pilotos", ""))
                self.var_tamanho_kart.set(str(perfil.get("tamanho", "1")))
                self.cor_atual_hex_kart = perfil.get("cor", "#FFFF00"); self.btn_cor_kart.config(bg=self.cor_atual_hex_kart)
                self.var_modo_colorido.set(perfil.get("modo_colorido", True))
                
                self.cb_col_id.set(perfil.get("col_id", ""))
                self.cb_col_ordem.set(perfil.get("col_ordem", ""))
                self.cb_ordem_dir.set(perfil.get("ordem_dir", "Crescente"))
                
                self.lb_sel.delete(0, tk.END)
                for col in perfil.get("cols_exibicao", []): self.lb_sel.insert(tk.END, col)
                self.log_kart(f"Perfil carregado: {os.path.basename(filepath)}")
            except Exception as e: messagebox.showerror("Erro", str(e))

    # --- FUNÇÃO NOVA: ABRIR PAINEL VISUAL ---
    def abrir_viewer(self):
        import viewer_grid
        viewer_grid.abrir_janela(self)

    def iniciar_kart(self):
        cols_para_exibir = list(self.lb_sel.get(0, tk.END))
        col_id = self.cb_col_id.get()
        col_ord = self.cb_col_ordem.get()
        
        if not cols_para_exibir or not col_id or not col_ord:
            messagebox.showerror("Erro", "Configure as colunas de ID, Ordenação e as Colunas de Exibição!")
            return

        if not self.is_running_kart:
            self.is_running_kart = True
            
            # --- PROTEÇÃO GHOST THREAD ---
            self.thread_id_kart = time.time() 
            
            self.btn_iniciar_kart.config(state="disabled")
            self.btn_parar_kart.config(state="normal")
            self.btn_abrir_viewer.config(state="normal") 
            c = {
                "db": self.entry_db_kart.get(), "tab": self.entry_tabela_kart.get(), "int": float(self.entry_intervalo_kart.get()), 
                "pilotos": self.entry_pilotos_kart.get(), "tamanho": int(self.var_tamanho_kart.get()),
                "cols_exibir": cols_para_exibir, "col_id": col_id, "col_ordem": col_ord, "ordem_dir": self.cb_ordem_dir.get(),
                "thread_id": self.thread_id_kart # Envia o ID para o Loop
            }
            Thread(target=self.loop_monitoramento, args=(c,), daemon=True).start()

    def parar_kart(self):
        self.is_running_kart = False
        self.btn_iniciar_kart.config(state="normal")
        self.btn_parar_kart.config(state="disabled")
        self.btn_abrir_viewer.config(state="disabled") 
        self.log_kart("Parado.")

    def loop_monitoramento(self, config):
        pilotos_raw = [x.strip() for x in config['pilotos'].split(',') if x.strip()]
        conn_str = (r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};" f"DBQ={config['db']};")
        
        col_id = config['col_id']
        col_ord = config['col_ordem']
        cols_exibir = config['cols_exibir']
        reverter_ordem = (config['ordem_dir'] == "Decrescente")

        # Laço de repetição bloqueado por ID único. Se você clicar Stop/Start, 
        # a thread velha morre aqui pois o self.thread_id_kart terá mudado!
        while self.is_running_kart and config.get('thread_id') == self.thread_id_kart:
            try:
                conn = pyodbc.connect(conn_str, autocommit=True)
                c = conn.cursor()
                grid_dados = []
                for num in pilotos_raw:
                    c.execute(f"SELECT TOP 1 * FROM {config['tab']} WHERE {col_id} = '{num}' ORDER BY Id DESC")
                    r = c.fetchone()
                    if r:
                        d = dict(zip([col[0] for col in c.description], r))
                        grid_dados.append(d)
                conn.close()
                
                if grid_dados:
                    # --- NOVA LÓGICA DE ORDENAÇÃO A PROVA DE FALHAS ---
                    def sort_key(x):
                        val = x.get(col_ord, "")
                        # Se o campo estiver em branco, joga pro fim da fila (-99 ou 99 garante que fique em último)
                        if val is None or str(val).strip() == "":
                            return (-99, "") if reverter_ordem else (99, "")
                        try:
                            # Se for número (ex: voltas ou milissegundos), classifica como número (0)
                            return (0, float(val))
                        except (ValueError, TypeError):
                            # Se for texto puro ou data formato estranho, classifica alfabeticamente (1)
                            return (1, str(val).lower())
                    
                    grid_dados.sort(key=sort_key, reverse=reverter_ordem)
                    
                    # --- ALIMENTA O DASHBOARD VISUAL NA MEMÓRIA COM AS COLUNAS FIXAS ---
                    dados_formatados_viewer = []
                    for p in grid_dados:
                        row_dict = {
                            "Posicao": p.get("Posicao", ""),
                            "Numero": str(p.get("Numero", "")).zfill(2) if str(p.get("Numero", "")).isdigit() else p.get("Numero", ""),
                            "Piloto": p.get("Piloto", ""),
                            "TempoMelhorVolta": core.formatar_tempo(p.get("TempoMelhorVolta", "")) if p.get("TempoMelhorVolta") else "",
                            "MelhorVoltanaVolta": p.get("MelhorVoltanaVolta", ""),
                            "TempoTotal": core.formatar_tempo(p.get("TempoTotal", "")) if p.get("TempoTotal") else "",
                            "Voltas": p.get("Voltas", ""),
                            "VelMedia": f"{p.get('VelMedia'):.2f}" if isinstance(p.get("VelMedia"), float) else p.get("VelMedia", ""),
                            "UltimaVolta": core.formatar_tempo(p.get("UltimaVolta", "")) if p.get("UltimaVolta") else ""
                        }
                        dados_formatados_viewer.append(row_dict)
                    
                    core.dados_grid_atual = dados_formatados_viewer
                    core.ultima_att_grid = datetime.now().strftime("%H:%M:%S")
                    # -------------------------------------------------------------------
                    
                    placas_ativas = sorted(list(core.clientes_conectados.keys()), key=lambda k: int(k) if str(k).isdigit() else k)
                    
                    if placas_ativas:
                        linhas_placa = 4 if config['tamanho'] == 1 else 2
                        for i, painel_id in enumerate(placas_ativas):
                            linhas_dados = []
                            for p in grid_dados[i*linhas_placa:(i*linhas_placa)+linhas_placa]:
                                cor = self.cor_atual_hex_kart
                                if self.var_modo_colorido.get():
                                    try:
                                        posicao_real_podio = grid_dados.index(p) + 1 
                                        if posicao_real_podio == 1: cor = "#00FF00"
                                        elif posicao_real_podio == 2: cor = "#FFFF00"
                                        elif posicao_real_podio == 3: cor = "#00BFFF"
                                    except: pass
                                
                                valores_finais = []
                                for col in cols_exibir:
                                    val = p.get(col, "")
                                    if "nome" in col.lower():
                                        val_str = str(val).strip()
                                        val = val_str[:8].ljust(8) # Corta só pra placa de LED
                                    elif "tempo" in col.lower() or isinstance(val, datetime):
                                        val = core.formatar_tempo(val)
                                    elif "numero" in col.lower() and str(val).isdigit():
                                        val = str(val).zfill(2) 
                                    elif isinstance(val, float):
                                        val = f"{val:.2f}"
                                    valores_finais.append(str(val))
                                    
                                texto_painel = "|".join(valores_finais)
                                linhas_dados.append({"texto": texto_painel, "cor": cor})
                                
                            if not linhas_dados: linhas_dados = [{"texto": " ", "cor": self.cor_atual_hex_kart}]
                            asyncio.run_coroutine_threadsafe(core.clientes_conectados[painel_id].send(core.criar_pacote_json(linhas_dados, config['tamanho'])), core.async_loop)
                        self.log_kart(f"Att: 1º Lugar ({grid_dados[0].get(col_id, '?')})")
                time.sleep(config['int'])
            except Exception as e: 
                self.log_kart(f"Erro no BD: {e}")
                time.sleep(2)

    def construir_interface(self):
        fk_db = ttk.LabelFrame(self, text="1. Conexão com Banco de Dados", padding=10)
        fk_db.pack(fill="x", padx=10, pady=5)
        ttk.Label(fk_db, text="Banco (.accdb):").grid(row=0, column=0, sticky="w")
        self.entry_db_kart = ttk.Entry(fk_db, width=45)
        self.entry_db_kart.grid(row=0, column=1, padx=5, pady=2, columnspan=2)
        ttk.Button(fk_db, text="...", command=self.buscar_arquivo_db, width=3).grid(row=0, column=3)
        ttk.Label(fk_db, text="Tabela:").grid(row=1, column=0, sticky="w")
        self.entry_tabela_kart = ttk.Entry(fk_db, width=20)
        self.entry_tabela_kart.insert(0, "webDisplayBateria")
        self.entry_tabela_kart.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        tk.Button(fk_db, text="🔄 Carregar Colunas", command=self.carregar_colunas_db, bg="#ffc107", font=("Arial", 8, "bold")).grid(row=1, column=2, padx=10, sticky="w")

        fk_dyn = ttk.LabelFrame(self, text="2. Construção Visual (Ordem da Esquerda para a Direita no LED)", padding=10)
        fk_dyn.pack(fill="x", padx=10, pady=5)
        f_map = ttk.Frame(fk_dyn); f_map.pack(fill="x", pady=(0, 10))
        ttk.Label(f_map, text="Filtrar por (Ex: ID):", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.cb_col_id = ttk.Combobox(f_map, width=12, state="readonly"); self.cb_col_id.pack(side=tk.LEFT, padx=5)
        ttk.Label(f_map, text="Ordenar por:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 0))
        self.cb_col_ordem = ttk.Combobox(f_map, width=15, state="readonly"); self.cb_col_ordem.pack(side=tk.LEFT, padx=5)
        ttk.Label(f_map, text="Ordem:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 0))
        self.cb_ordem_dir = ttk.Combobox(f_map, width=12, state="readonly", values=["Crescente", "Decrescente"])
        self.cb_ordem_dir.set("Crescente")
        self.cb_ordem_dir.pack(side=tk.LEFT, padx=5)

        f_listas = ttk.Frame(fk_dyn); f_listas.pack(fill="both", expand=True)
        ttk.Label(f_listas, text="Colunas Disponíveis:").grid(row=0, column=0, sticky="w")
        ttk.Label(f_listas, text="Colunas para Exibir no LED:").grid(row=0, column=2, sticky="w")
        self.lb_disp = tk.Listbox(f_listas, height=5, selectmode=tk.MULTIPLE, exportselection=False)
        self.lb_disp.grid(row=1, column=0, rowspan=4, padx=5, sticky="we")

        f_botoes = ttk.Frame(f_listas); f_botoes.grid(row=1, column=1, rowspan=4, padx=5)
        tk.Button(f_botoes, text="▶ Inserir", command=self.mover_para_selecionadas, bg="#28a745", fg="white").pack(pady=2, fill="x")
        tk.Button(f_botoes, text="◀ Remover", command=self.mover_para_disponiveis, bg="#dc3545", fg="white").pack(pady=2, fill="x")
        tk.Button(f_botoes, text="▲ Subir", command=self.mover_cima).pack(pady=2, fill="x")
        tk.Button(f_botoes, text="▼ Descer", command=self.mover_baixo).pack(pady=2, fill="x")

        self.lb_sel = tk.Listbox(f_listas, height=5, selectmode=tk.SINGLE, exportselection=False)
        self.lb_sel.grid(row=1, column=2, rowspan=4, padx=5, sticky="we")
        f_listas.columnconfigure(0, weight=1); f_listas.columnconfigure(2, weight=1)

        fk_params = ttk.LabelFrame(self, text="3. Parâmetros e Controle", padding=10)
        fk_params.pack(fill="x", padx=10, pady=5)
        ttk.Label(fk_params, text="Nº Pilotos na Corrida:").grid(row=0, column=0, sticky="w")
        self.entry_pilotos_kart = ttk.Entry(fk_params, width=30); self.entry_pilotos_kart.insert(0, "8,9,10,11,12,13,14,15"); self.entry_pilotos_kart.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(fk_params, text="Atualizar (Seg):").grid(row=0, column=2, sticky="e")
        self.entry_intervalo_kart = ttk.Entry(fk_params, width=6); self.entry_intervalo_kart.insert(0, "2"); self.entry_intervalo_kart.grid(row=0, column=3, sticky="w", padx=5)

        fe_k = ttk.Frame(fk_params); fe_k.grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Label(fe_k, text="Tamanho Fonte:").pack(side=tk.LEFT)
        self.var_tamanho_kart = tk.StringVar(value="1")
        ttk.Combobox(fe_k, textvariable=self.var_tamanho_kart, values=["1", "2"], width=3, state="readonly").pack(side=tk.LEFT, padx=5)
        self.btn_cor_kart = tk.Button(fe_k, text=" Cor Padrão ", bg=self.cor_atual_hex_kart, relief=tk.RAISED, command=self.selecionar_cor_kart)
        self.btn_cor_kart.pack(side=tk.LEFT, padx=10)
        self.var_modo_colorido = tk.BooleanVar(value=True)
        ttk.Checkbutton(fe_k, text="Aplicar Modo Pódio Colorido (1º, 2º e 3º)", variable=self.var_modo_colorido).pack(side=tk.LEFT, padx=(15, 5))

        fc_k = ttk.Frame(self, padding=5); fc_k.pack(fill="x", padx=10)
        self.btn_iniciar_kart = ttk.Button(fc_k, text="▶ INICIAR MONITORAMENTO", command=self.iniciar_kart)
        self.btn_iniciar_kart.pack(side="left", padx=5)
        self.btn_parar_kart = ttk.Button(fc_k, text="⏹ PARAR", command=self.parar_kart, state="disabled")
        self.btn_parar_kart.pack(side="left", padx=5)
        
        self.btn_abrir_viewer = ttk.Button(fc_k, text="📊 ABRIR PAINEL VISUAL", command=self.abrir_viewer, state="disabled")
        self.btn_abrir_viewer.pack(side="left", padx=5)
        
        ttk.Button(fc_k, text="📂", command=self.carregar_perfil_kart, width=4).pack(side="right", padx=2)
        ttk.Button(fc_k, text="💾", command=self.salvar_perfil_kart, width=4).pack(side="right", padx=2)

        self.txt_log_kart = scrolledtext.ScrolledText(self, height=6, bg='black', fg='#00FF00', font=("Consolas", 9))
        self.txt_log_kart.pack(fill="both", expand=True, padx=10, pady=(5, 10))