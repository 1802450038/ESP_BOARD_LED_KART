import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import subprocess
import os
import time

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

class TabBoardControl(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.serial_conn = None
        self.is_reading = False
        self.read_thread = None
        self.bin_path = ""
        
        self.construir_interface()
        
    def log_serial(self, msg):
        self.txt_console.insert(tk.END, msg)
        self.txt_console.see(tk.END)
        
    def atualizar_portas(self):
        if not HAS_SERIAL:
            messagebox.showerror("Erro", "Biblioteca 'pyserial' não encontrada. Instale usando: pip install pyserial")
            return
            
        portas = [port.device for port in serial.tools.list_ports.comports()]
        self.cb_portas['values'] = portas
        if portas:
            self.cb_portas.set(portas[0])
            
    def buscar_zip(self):
        f = filedialog.askopenfilename(filetypes=[("Arquivo ZIP (Firmware)", "*.zip")])
        if f:
            self.bin_path = f
            self.lbl_bin_path.config(text=os.path.basename(f))
            
    def conectar_serial(self):
        if not HAS_SERIAL:
            return
            
        if self.serial_conn and self.serial_conn.is_open:
            self.desconectar_serial()
            return
            
        porta = self.cb_portas.get()
        if not porta:
            messagebox.showwarning("Atenção", "Selecione uma porta COM primeiro!")
            return
            
        try:
            baud = int(self.cb_baud.get())
            self.serial_conn = serial.Serial(porta, baud, timeout=1)
            self.is_reading = True
            self.btn_conectar.config(text="Desconectar", bg="#dc3545", fg="white")
            self.log_serial(f"\n--- Conectado em {porta} a {baud} bps ---\n")
            
            self.read_thread = threading.Thread(target=self.ler_serial, daemon=True)
            self.read_thread.start()
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar:\n{e}")
            
    def desconectar_serial(self):
        self.is_reading = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.btn_conectar.config(text="Conectar", bg="#28a745", fg="white")
        self.log_serial("\n--- Desconectado ---\n")
        
    def ler_serial(self):
        while self.is_reading and self.serial_conn and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting > 0:
                    linha = self.serial_conn.readline().decode('utf-8', errors='replace')
                    self.txt_console.after(0, self.log_serial, linha)
                else:
                    time.sleep(0.01)
            except Exception as e:
                self.is_reading = False
                self.txt_console.after(0, self.log_serial, f"\n[!] Erro na leitura: {e}\n")
                self.txt_console.after(0, self.desconectar_serial)
                break

    def limpar_console(self):
        self.txt_console.delete(1.0, tk.END)

    def enviar_firmware(self):
        porta = self.cb_portas.get()
        if not porta:
            messagebox.showwarning("Atenção", "Selecione uma porta COM!")
            return
        if not self.bin_path or not self.bin_path.endswith('.zip'):
            messagebox.showwarning("Atenção", "Selecione um arquivo .zip primeiro!")
            return
            
        if self.serial_conn and self.serial_conn.is_open:
            self.desconectar_serial()
            time.sleep(1)
            
        self.log_serial(f"\n--- Iniciando Upload do Firmware ---\nArquivo: {self.bin_path}\nPorta: {porta}\n")
        self.btn_upload.config(state="disabled")
        
        baud = self.cb_baud.get()
        # Iniciar thread para nao travar a UI
        threading.Thread(target=self.tarefa_upload, args=(porta, baud, self.bin_path), daemon=True).start()
        
    def tarefa_upload(self, porta, baud, zip_path):
        import sys
        import zipfile
        import tempfile
        import shutil
        
        # Cria pasta temporária
        temp_dir = tempfile.mkdtemp()
        
        try:
            self.txt_console.after(0, self.log_serial, f"\n[INFO] Descompactando {os.path.basename(zip_path)}...\n")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Procura os arquivos extraidos (podem estar na raiz ou dentro de alguma subpasta do zip)
            boot_path = None
            part_path = None
            firm_path = None
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    nome = file.lower()
                    if "bootloader.bin" in nome: boot_path = os.path.join(root, file)
                    elif "partitions.bin" in nome: part_path = os.path.join(root, file)
                    elif "firmware.bin" in nome: firm_path = os.path.join(root, file)
                    
            if not boot_path or not part_path or not firm_path:
                self.txt_console.after(0, self.log_serial, "\n[ERRO] O arquivo .zip não contém os 3 arquivos necessários (bootloader.bin, partitions.bin, firmware.bin)!\n")
                return

            flash_args = ["write-flash", "-z", "0x0", boot_path, "0x8000", part_path, "0x10000", firm_path]
            
            comando = [
                "--chip", "esp32s3", 
                "--port", porta, 
                "--baud", baud, 
                "--before", "default-reset", 
                "--after", "hard-reset"
            ] + flash_args
            
            # Usamos contextlib para redirecionar o stdout/stderr para a interface,
            # assim o app funciona perfeitamente ao ser compilado para .exe pelo PyInstaller
            import io
            import contextlib
            import esptool
            
            class Redirector(io.StringIO):
                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback
                def write(self, s):
                    self.callback(s)
                def flush(self):
                    pass
            
            redirector = Redirector(lambda s: self.txt_console.after(0, self.log_serial, s))
            
            try:
                with contextlib.redirect_stdout(redirector), contextlib.redirect_stderr(redirector):
                    esptool.main(comando)
                self.txt_console.after(0, self.log_serial, "\n--- Upload Concluído com Sucesso! ---\n")
            except SystemExit as e:
                if e.code == 0:
                    self.txt_console.after(0, self.log_serial, "\n--- Upload Concluído com Sucesso! ---\n")
                else:
                    self.txt_console.after(0, self.log_serial, f"\n--- Falha no Upload (Código {e.code}) ---\n")
                
        except Exception as e:
             self.txt_console.after(0, self.log_serial, f"\n[!] Erro na execução: {e}\n")
        finally:
            # Limpa o cache excluindo a pasta temporária
            try:
                shutil.rmtree(temp_dir)
                self.txt_console.after(0, self.log_serial, "\n[INFO] Arquivos temporários removidos com sucesso.\n")
            except:
                pass
            self.btn_upload.after(0, lambda: self.btn_upload.config(state="normal"))

    def construir_interface(self):
        # 1. Configurações de Conexão
        f_conn = ttk.LabelFrame(self, text="1. Conexão Serial (Monitor)", padding=10)
        f_conn.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(f_conn, text="Porta COM:").pack(side=tk.LEFT)
        self.cb_portas = ttk.Combobox(f_conn, width=15, state="readonly")
        self.cb_portas.pack(side=tk.LEFT, padx=5)
        
        btn_att = tk.Button(f_conn, text="🔄", command=self.atualizar_portas)
        btn_att.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(f_conn, text="Baud Rate:").pack(side=tk.LEFT, padx=(15, 0))
        self.cb_baud = ttk.Combobox(f_conn, width=10, state="readonly", values=["9600", "115200", "460800"])
        self.cb_baud.set("115200")
        self.cb_baud.pack(side=tk.LEFT, padx=5)
        
        self.btn_conectar = tk.Button(f_conn, text="Conectar", command=self.conectar_serial, bg="#28a745", fg="white", width=12)
        self.btn_conectar.pack(side=tk.LEFT, padx=15)
        
        # 2. Upload de Firmware
        f_upload = ttk.LabelFrame(self, text="2. Upload de Firmware (Pacote .zip)", padding=10)
        f_upload.pack(fill="x", padx=10, pady=5)
        
        btn_buscar = tk.Button(f_upload, text="Selecionar Pacote (.zip)", command=self.buscar_zip)
        btn_buscar.pack(side=tk.LEFT)
        
        self.lbl_bin_path = ttk.Label(f_upload, text="Nenhum arquivo selecionado", foreground="gray")
        self.lbl_bin_path.pack(side=tk.LEFT, padx=10)
        
        self.btn_upload = tk.Button(f_upload, text="Enviar para Placa (Upload)", command=self.enviar_firmware, bg="#007bff", fg="white", width=25)
        self.btn_upload.pack(side=tk.RIGHT, padx=5)
        
        # 3. Monitor Serial
        f_console = ttk.LabelFrame(self, text="3. Monitor Serial", padding=10)
        f_console.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.txt_console = scrolledtext.ScrolledText(f_console, bg="black", fg="#00FF00", font=("Consolas", 10))
        self.txt_console.pack(fill="both", expand=True, pady=(0, 5))
        
        btn_limpar = tk.Button(f_console, text="Limpar Console", command=self.limpar_console)
        btn_limpar.pack(side=tk.RIGHT)
        
        if not HAS_SERIAL:
            self.txt_console.insert(tk.END, "AVISO: A biblioteca 'pyserial' não foi encontrada.\nAbra o terminal e execute: pip install pyserial\nPara ativar as funções seriais.\n")
            
        self.atualizar_portas()
