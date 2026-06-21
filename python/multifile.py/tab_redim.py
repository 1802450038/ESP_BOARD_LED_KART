import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageOps
import os

class TabRedim(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.caminho_imagem_redim = None
        self.cor_escolhida_redim = "#ffffff"
        self.construir_interface()

    def carregar_imagem_redim(self):
        self.caminho_imagem_redim = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if self.caminho_imagem_redim:
            self.lbl_arquivo_redim.config(text=os.path.basename(self.caminho_imagem_redim))

    def alternar_botao_cor_redim(self):
        if self.modo_mono_redim.get(): self.btn_cor_redim.config(state=tk.NORMAL)
        else: self.btn_cor_redim.config(state=tk.DISABLED)

    def escolher_cor_redim(self):
        cor = colorchooser.askcolor(title="Escolha a cor")[1]
        if cor:
            self.cor_escolhida_redim = cor
            self.btn_cor_redim.config(bg=cor)

    def processar_e_salvar_redim(self):
        if not self.caminho_imagem_redim:
            messagebox.showwarning("Atenção", "Selecione uma imagem primeiro!")
            return
            
        try:
            largura = int(self.entrada_w_redim.get())
            altura = int(self.entrada_h_redim.get())
        except ValueError:
            messagebox.showerror("Erro", "Por favor, digite números inteiros para largura e altura.")
            return

        try:
            img = Image.open(self.caminho_imagem_redim)
            img = img.resize((largura, altura), Image.Resampling.LANCZOS)

            if self.modo_mono_redim.get():
                img = img.convert("L") 
                img = ImageOps.colorize(img, black="black", white=self.cor_escolhida_redim)
            else:
                img = img.convert("RGB")

            caminho_salvar = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
            if caminho_salvar:
                img.save(caminho_salvar)
                messagebox.showinfo("Sucesso!", f"Imagem salva com sucesso em:\n{caminho_salvar}")

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao processar a imagem:\n{e}")

    def construir_interface(self):
        f1_redim = ttk.LabelFrame(self, text="1. Imagem Original", padding=10)
        f1_redim.pack(fill="x", padx=10, pady=5)
        tk.Button(f1_redim, text="Selecionar Arquivo", command=self.carregar_imagem_redim).pack(pady=5)
        self.lbl_arquivo_redim = tk.Label(f1_redim, text="Nenhuma imagem selecionada", fg="gray")
        self.lbl_arquivo_redim.pack()

        f2_redim = ttk.LabelFrame(self, text="2. Nova Resolução (Pixels)", padding=10)
        f2_redim.pack(fill="x", padx=10, pady=5)
        f2_sub = tk.Frame(f2_redim); f2_sub.pack()
        tk.Label(f2_sub, text="Largura:").grid(row=0, column=0, padx=5)
        self.entrada_w_redim = tk.Entry(f2_sub, width=8)
        self.entrada_w_redim.grid(row=0, column=1, padx=5)
        self.entrada_w_redim.insert(0, "128")
        tk.Label(f2_sub, text="Altura:").grid(row=0, column=2, padx=5)
        self.entrada_h_redim = tk.Entry(f2_sub, width=8)
        self.entrada_h_redim.grid(row=0, column=3, padx=5)
        self.entrada_h_redim.insert(0, "128")

        f3_redim = ttk.LabelFrame(self, text="3. Estilo e Filtro", padding=10)
        f3_redim.pack(fill="x", padx=10, pady=5)
        self.modo_mono_redim = tk.BooleanVar()
        tk.Checkbutton(f3_redim, text="Aplicar filtro monocromático (Cor Personalizada)", variable=self.modo_mono_redim, command=self.alternar_botao_cor_redim).pack(pady=5)
        self.btn_cor_redim = tk.Button(f3_redim, text="Escolher Cor do Filtro", command=self.escolher_cor_redim, state=tk.DISABLED, width=20)
        self.btn_cor_redim.pack(pady=5)

        f4_redim = ttk.Frame(self, padding=10)
        f4_redim.pack(fill="x", padx=10, pady=10)
        tk.Button(f4_redim, text="Processar e Salvar Imagem", command=self.processar_e_salvar_redim, bg="#0066cc", fg="white", font=("Arial", 11, "bold"), pady=5).pack()