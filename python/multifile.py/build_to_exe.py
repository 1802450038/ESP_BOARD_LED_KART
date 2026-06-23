import os
import subprocess
import sys
import datetime

def main():
    print("="*50)
    print("  INICIANDO COMPILAÇÃO DO PAINEL PARA .EXE")
    print("="*50)
    
    print("\n[1/3] Verificando e instalando PyInstaller (caso não exista)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    except Exception as e:
        print(f"Erro ao instalar o PyInstaller: {e}")
        return
        
    # Como o script agora fica na própria pasta do python, o diretório base é o atual
    python_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(python_dir)
    
    print("\n[2/3] Configurando o destino na Área de Trabalho com data/hora...")
    
    # Gera a data e hora atual (Ex: 21-06-2026_19-45)
    agora = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    nome_executavel = f"Painel_KART_{agora}"
    
    # Descobre o caminho da Área de Trabalho do usuário
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    
    print(f" -> Nome do App: {nome_executavel}.exe")
    print(f" -> Destino final: {desktop_path}")
    
    print("\n[3/3] Empacotando o projeto (Isso vai levar alguns minutos)...")
    
    # Comando do PyInstaller configurado para jogar o .exe na Área de Trabalho com o nome exato
    comando = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--icon=kart_logo.ico",
        "--add-data=kart_logo.ico;.",
        # Força o empacotamento das bibliotecas críticas para não dar erro no .exe
        "--hidden-import=serial",
        "--hidden-import=serial.tools.list_ports",
        "--hidden-import=esptool",
        f"--name={nome_executavel}",
        f"--distpath={desktop_path}",
        "main.py"
    ]
    
    try:
        subprocess.run(comando, check=True)
        print("\n" + "="*50)
        print(" 🎉 BUILD CONCLUÍDO COM SUCESSO! 🎉")
        print(" O SEU EXECUTÁVEL ESTÁ PRONTO E SALVO NA SUA ÁREA DE TRABALHO:")
        print(f" -> {os.path.join(desktop_path, nome_executavel + '.exe')}")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Erro durante a compilação pelo PyInstaller: {e}")

if __name__ == "__main__":
    main()
