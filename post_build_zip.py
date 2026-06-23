Import("env")
import os
import zipfile
from datetime import datetime

def post_build_action(source, target, env):
    build_dir = env.subst("$BUILD_DIR")
    
    firmware = os.path.join(build_dir, "firmware.bin")
    bootloader = os.path.join(build_dir, "bootloader.bin")
    partitions = os.path.join(build_dir, "partitions.bin")
    
    zip_path = os.path.join(build_dir, "pacote_firmware.zip")

    print("\n--- GERANDO PACOTE ZIP DO FIRMWARE ---")
    
    if os.path.exists(firmware):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.exists(bootloader):
                zipf.write(bootloader, "bootloader.bin")
                print(" -> bootloader.bin adicionado!")
            else:
                print(" -> AVISO: bootloader.bin não encontrado!")
                
            if os.path.exists(partitions):
                zipf.write(partitions, "partitions.bin")
                print(" -> partitions.bin adicionado!")
            else:
                print(" -> AVISO: partitions.bin não encontrado!")
                
            zipf.write(firmware, "firmware.bin")
            print(" -> firmware.bin adicionado!")
            
        print(f"✅ Pacote criado com sucesso em:\n{zip_path}")
        
        import shutil
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        dateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_arquivo = "pacote_firmware_" + dateTime + ".zip"
        destino_desktop = os.path.join(desktop_path, nome_arquivo)
        
        try:
            shutil.copy2(zip_path, destino_desktop)
            print(f"✅ Cópia salva na Área de Trabalho:\n{destino_desktop}")
        except Exception as e:
            print(f"⚠️ Erro ao copiar para a Área de Trabalho: {e}")
            
        print("--------------------------------------\n")

# Adiciona a ação para rodar logo após a criação do firmware.bin
env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", post_build_action)
