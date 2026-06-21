import tkinter as tk
from tkinter import ttk
import core

class DashboardApp(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Monitor Oficial - GRID ATUAL")
        self.geometry("1100x600")
        self.configure(bg="#1a1a1a")

        # --- Cabeçalho ---
        frame_top = tk.Frame(self, bg="#333", height=60)
        frame_top.pack(fill="x", pady=5)
        
        self.lbl_status = tk.Label(frame_top, text="Aguardando Dados do Banco...", fg="#00ff00", bg="#333", font=("Arial", 14, "bold"))
        self.lbl_status.pack(side="left", padx=20)

        # --- Tabela ---
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="black", 
                        foreground="#00FF00", 
                        fieldbackground="black", 
                        rowheight=45, 
                        font=("Arial", 12))
        
        style.configure("Treeview.Heading", 
                        background="#c0392b", 
                        foreground="white", 
                        font=("Arial", 13, "bold"))

        # Colunas Fixas
        cols = ("Pos", "Num", "Piloto", "Melhor Volta", "Volta", "Tempo Total", "Vlts", "Vel. Med", "Última Volta")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        
        larguras = [60, 60, 250, 130, 80, 130, 70, 100, 130]
        alinhamento = ["center", "center", "w", "center", "center", "center", "center", "center", "center"]

        for i, col in enumerate(cols):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=larguras[i], anchor=alinhamento[i])
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Tags de cor
        self.tree.tag_configure('podium1', foreground='gold') 
        self.tree.tag_configure('podium2', foreground='silver') 
        self.tree.tag_configure('podium3', foreground='#cd7f32') 

        # Inicia Loop Visual
        self.atualizar_grid()

    def atualizar_grid(self):
        # Para o loop se você fechar a janela
        if not self.winfo_exists():
            return

        try:
            # Atualiza os dados na tela caso existam dados formatados
            if hasattr(core, 'dados_grid_atual') and core.dados_grid_atual:
                # Limpa a tabela
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                # Preenche com os dados que a aba Grid leu do banco
                for i, d in enumerate(core.dados_grid_atual):
                    valores = (
                        d.get("Posicao", ""),
                        d.get("Numero", ""),
                        d.get("Piloto", ""),
                        d.get("TempoMelhorVolta", ""),
                        d.get("MelhorVoltanaVolta", ""),
                        d.get("TempoTotal", ""),
                        d.get("Voltas", ""),
                        d.get("VelMedia", ""),
                        d.get("UltimaVolta", "")
                    )
                    
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