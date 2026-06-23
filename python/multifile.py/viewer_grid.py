import tkinter as tk
from tkinter import ttk
import os
import core

class DashboardApp(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Monitor Oficial - GRID ATUAL")
        self.geometry("1100x600")
        self.configure(bg="#050505")

        # --- Cabeçalho Superior ---
        frame_top = tk.Frame(self, bg="#050505", height=90)
        frame_top.pack(fill="x", pady=10, padx=20)
        
        # Lado Esquerdo do Cabeçalho
        frame_top_left = tk.Frame(frame_top, bg="#050505")
        frame_top_left.pack(side="left", fill="both", expand=True)

        self.lbl_title1 = tk.Label(frame_top_left, text="CORRIDA OFICIAL KARTMANIA", fg="#00ff00", bg="#050505", font=("Arial", 14, "bold"), anchor="w")
        self.lbl_title1.pack(fill="x")
        self.lbl_status = tk.Label(frame_top_left, text="Aguardando Dados do Banco...", fg="white", bg="#050505", font=("Arial", 12, "bold"), anchor="w")
        self.lbl_status.pack(fill="x")

        # Lado Direito do Cabeçalho (Logo)
        frame_top_right = tk.Frame(frame_top, bg="#050505")
        frame_top_right.pack(side="right")
        
        # Tempo Restante
        self.lbl_tempo = tk.Label(frame_top_right, text="TEMPO RESTANTE: 15:00", fg="#FFD700", bg="#050505", font=("Arial", 16, "bold"))
        self.lbl_tempo.pack(side="left", padx=20)
        
        self.logo_label = tk.Label(frame_top_right, bg="#050505")
        self.logo_label.pack(side="right")
        
        # Tentar carregar a logo
        try:
            base_path = os.path.dirname(__file__)
            # Procura primeiro o png, depois tenta o ico que você enviou
            logo_png = os.path.join(base_path, "kartmania.png")
            logo_ico = os.path.join(base_path, "kart_logo.ico")
            
            if os.path.exists(logo_png):
                self.logo_img = tk.PhotoImage(file=logo_png)
                self.logo_label.config(image=self.logo_img)
            elif os.path.exists(logo_ico):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(logo_ico)
                    # Usa thumbnail para não distorcer a imagem (mantém proporção original)
                    img.thumbnail((150, 80), Image.Resampling.LANCZOS)
                    self.logo_img = ImageTk.PhotoImage(img)
                    self.logo_label.config(image=self.logo_img)
                except ImportError:
                    self.logo_label.config(text="KARTMANIA\nRENTAL\n(Instale o Pillow para ver a logo .ico)", fg="red", font=("Arial", 12, "bold italic"))
            else:
                self.logo_label.config(text="KARTMANIA\nRENTAL", fg="red", font=("Arial", 22, "bold italic"), justify="center")
        except Exception as e:
            self.logo_label.config(text="KARTMANIA\nRENTAL", fg="red", font=("Arial", 22, "bold italic"), justify="center")

        # --- Tabela ---
        style = ttk.Style(self)
        style.theme_use("clam")
        
        # Configuração do Treeview e Scrollbar
        frame_tree = tk.Frame(self, bg="#050505")
        frame_tree.pack(fill="both", expand=True, padx=20, pady=5)
        
        style.configure("Treeview", 
                        background="black", 
                        foreground="white", 
                        fieldbackground="black", 
                        rowheight=45, 
                        font=("Arial", 13, "bold"),
                        borderwidth=0)
        
        style.map("Treeview", background=[('selected', '#222222')])
        
        style.configure("Treeview.Heading", 
                        background="#111111", 
                        foreground="#FFD700", 
                        font=("Arial", 11, "bold"),
                        borderwidth=0)

        # Colunas conforme a imagem
        cols = ("POS", "#", "NOME/PATROCINADOR", "M.V.", "T.M.V.", "D.A.", "T.U.V.", "VOLTAS", "CATEGORIA")
        self.tree = ttk.Treeview(frame_tree, columns=cols, show="headings")
        
        larguras = [50, 50, 320, 60, 100, 100, 100, 80, 100]
        alinhamento = ["center", "center", "w", "center", "center", "center", "center", "center", "center"]

        for i, col in enumerate(cols):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=larguras[i], anchor=alinhamento[i])
        
        self.tree.pack(side="left", fill="both", expand=True)

        # Tags de cor
        self.tree.tag_configure('podium1', foreground='#FFD700') # Gold
        self.tree.tag_configure('podium2', foreground='#C0C0C0') # Silver
        self.tree.tag_configure('podium3', foreground='#CD7F32') # Bronze
        self.tree.tag_configure('normal', foreground='white')

        # --- Rodapé ---
        frame_bottom = tk.Frame(self, bg="#050505", height=40)
        frame_bottom.pack(fill="x", pady=10, padx=20)
        
        lbl_rodape_esq = tk.Label(frame_bottom, text="CRONOMETRAGEM - WWW.KARTMANIA.COM.BR", fg="#00ff00", bg="#050505", font=("Arial", 12, "bold"))
        lbl_rodape_esq.pack(side="left")
        
        lbl_rodape_dir = tk.Label(frame_bottom, text="RESULTADOS EM TEMPO REAL", fg="#00ff00", bg="#050505", font=("Arial", 12, "bold"))
        lbl_rodape_dir.pack(side="right")

        # Inicia Loop Visual
        self.atualizar_grid()

    def atualizar_grid(self):
        # Para o loop se você fechar a janela
        if not self.winfo_exists():
            return

        try:
            # Tempo cronômetro
            if hasattr(core, 'em_corrida') and core.em_corrida:
                import time
                decorrido = time.time() - core.inicio_prova
                restante = max(0, core.duracao_prova - decorrido)
                minutos = int(restante // 60)
                segundos = int(restante % 60)
                self.lbl_tempo.config(text=f"TEMPO RESTANTE: {minutos:02d}:{segundos:02d}")
            else:
                self.lbl_tempo.config(text="TEMPO RESTANTE: --:--")

            # Atualiza os dados na tela caso existam dados formatados
            if hasattr(core, 'dados_grid_atual') and core.dados_grid_atual:
                
                # 1. Atualiza colunas se necessário
                if hasattr(core, 'cols_exibir_atual') and core.cols_exibir_atual:
                    cols_dinamicas = tuple(core.cols_exibir_atual)
                    if self.tree.cget("columns") != cols_dinamicas:
                        self.tree.config(columns=cols_dinamicas)
                        for col in cols_dinamicas:
                            self.tree.heading(col, text=col)
                            if "nome" in col.lower() or "piloto" in col.lower():
                                self.tree.column(col, width=320, anchor="w")
                            elif "numero" in col.lower() or "pos" in col.lower():
                                self.tree.column(col, width=60, anchor="center")
                            else:
                                self.tree.column(col, width=120, anchor="center")

                # Limpa a tabela
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                # Preenche com os dados que a aba Grid leu do banco
                for i, d in enumerate(core.dados_grid_atual):
                    # Puxa os dados baseados nas colunas ativas na arvore
                    valores = tuple(d.get(col, "") for col in self.tree.cget("columns"))
                    
                    # Cores para o top 3
                    tag = 'normal'
                    if i == 0: tag = 'podium1'
                    elif i == 1: tag = 'podium2'
                    elif i == 2: tag = 'podium3'
                    
                    self.tree.insert("", "end", values=valores, tags=(tag,))
                
                self.lbl_status.config(text=f"MONITOR ATIVO | Lendo do Banco Local | Última att: {core.ultima_att_grid}")

        except Exception as e:
            print(f"Erro GUI Viewer: {e}")
        
        finally:
            # Checa novamente em 200ms
            self.after(200, self.atualizar_grid)

# Função para chamar o painel de outro arquivo
def abrir_janela(parent):
    DashboardApp(parent)