import os
import sys
import subprocess

def install_requirements():
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_file):
        print(f"[STOIQO-Comfyui-Nodes] Verifica e installazione dipendenze...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--prefer-binary", "-r", req_file
            ])
            print("[STOIQO-Comfyui-Nodes] Dipendenze verificate/installate con successo.")
        except subprocess.CalledProcessError as e:
            print(f"[STOIQO-Comfyui-Nodes] Errore durante l'installazione delle dipendenze: {e}")

if __name__ == "__main__":
    install_requirements()
