#!/usr/bin/env python3
"""
Script de instalação automática do NGMotherLine
Facilita o setup e verificação de dependências
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
from pathlib import Path
import shutil

def print_banner():
    """Mostra banner do NGMotherLine."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                    NGMotherLine v0.1.0                    ║
    ║        Engine de geração de legendas any-to-any          ║
    ║                                                           ║
    ║                   🎯 Instalador Automático               ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Verifica se a versão do Python é compatível."""
    print("🐍 Verificando versão do Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        print(f"   Versão atual: {sys.version}")
        print("   Baixe em: https://www.python.org/downloads/")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_ffmpeg():
    """Verifica se FFmpeg está instalado."""
    print("🎬 Verificando FFmpeg...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ {version}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ FFmpeg não encontrado")
    return False

def install_ffmpeg_windows():
    """Instala FFmpeg no Windows."""
    print("📥 Instalando FFmpeg para Windows...")
    
    # URL do FFmpeg para Windows
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        print("   Baixando FFmpeg...")
        
        # Diretório de instalação
        install_dir = Path.home() / "NGMotherLine" / "ffmpeg"
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Baixa o arquivo
        zip_path = install_dir / "ffmpeg.zip"
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        
        print("   Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        
        # Encontra o executável
        ffmpeg_exe = None
        for root, dirs, files in os.walk(install_dir):
            if 'ffmpeg.exe' in files:
                ffmpeg_exe = Path(root) / 'ffmpeg.exe'
                break
        
        if ffmpeg_exe:
            # Adiciona ao PATH temporariamente
            os.environ['PATH'] = str(ffmpeg_exe.parent) + os.pathsep + os.environ['PATH']
            
            print("✅ FFmpeg instalado com sucesso!")
            print(f"   Localização: {ffmpeg_exe}")
            print("   ⚠️  Adicione ao PATH do sistema para uso permanente:")
            print(f"   {ffmpeg_exe.parent}")
            
            return True
        else:
            print("❌ Erro ao encontrar executável do FFmpeg")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao instalar FFmpeg: {e}")
        return False
    
    finally:
        # Limpa arquivo temporário
        if zip_path.exists():
            zip_path.unlink()

def install_python_dependencies():
    """Instala dependências Python."""
    print("📦 Instalando dependências Python...")
    
    try:
        # Atualiza pip
        print("   Atualizando pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        
        # Instala dependências
        print("   Instalando requirements.txt...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        
        print("✅ Dependências instaladas com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def install_torch_cuda():
    """Instala PyTorch com suporte CUDA."""
    print("🚀 Deseja instalar PyTorch com suporte CUDA? (y/n): ", end='')
    
    response = input().lower()
    if response in ['y', 'yes', 's', 'sim']:
        print("   Instalando PyTorch com CUDA...")
        
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                'torch', 'torchvision', 'torchaudio', 
                '--index-url', 'https://download.pytorch.org/whl/cu118'
            ], check=True)
            
            print("✅ PyTorch com CUDA instalado!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar PyTorch CUDA: {e}")
            print("   Continuando com versão CPU...")
            return False
    
    return True

def create_desktop_shortcut():
    """Cria atalho na área de trabalho (Windows)."""
    if platform.system() != 'Windows':
        return
    
    print("🔗 Deseja criar atalho na área de trabalho? (y/n): ", end='')
    
    response = input().lower()
    if response in ['y', 'yes', 's', 'sim']:
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "NGMotherLine.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = str(Path.cwd() / "main.py")
            shortcut.WorkingDirectory = str(Path.cwd())
            shortcut.IconLocation = str(Path.cwd() / "assets" / "icon.ico")
            shortcut.save()
            
            print("✅ Atalho criado na área de trabalho!")
            
        except ImportError:
            print("   Instalando winshell...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'winshell', 'pywin32'], 
                          check=True)
            # Tenta novamente recursivamente
            create_desktop_shortcut()
            
        except Exception as e:
            print(f"❌ Erro ao criar atalho: {e}")

def run_tests():
    """Executa testes básicos."""
    print("🧪 Executando testes básicos...")
    
    try:
        result = subprocess.run([sys.executable, 'test_poc.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Todos os testes passaram!")
            return True
        else:
            print("❌ Alguns testes falharam:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return False

def show_usage_examples():
    """Mostra exemplos de uso."""
    print("""
    🎯 Exemplos de uso do NGMotherLine:
    
    # Processamento básico
    python main.py video.mp4
    
    # Com tradução
    python main.py video.mp4 --target-lang en
    
    # Modo preciso
    python main.py video.mp4 --mode accurate
    
    # Legendas bilíngues
    python main.py video.mp4 --target-lang en --bilingual
    
    # Ajuda completa
    python main.py --help
    """)

def main():
    """Função principal do instalador."""
    print_banner()
    
    # Lista de verificações
    checks = [
        ("Versão do Python", check_python_version),
        ("FFmpeg", check_ffmpeg),
    ]
    
    # Executa verificações
    all_passed = True
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
    
    # Instala dependências faltantes
    if not all_passed:
        print("\n🔧 Instalando dependências faltantes...")
        
        if platform.system() == 'Windows' and not check_ffmpeg():
            install_ffmpeg_windows()
    
    # Instala dependências Python
    if not install_python_dependencies():
        print("❌ Falha na instalação. Verifique os erros acima.")
        sys.exit(1)
    
    # Opções avançadas
    install_torch_cuda()
    create_desktop_shortcut()
    
    # Executa testes
    if not run_tests():
        print("\n⚠️  Instalação concluída com avisos.")
        print("   Alguns testes falharam, mas o sistema pode funcionar.")
    else:
        print("\n🎉 Instalação concluída com sucesso!")
    
    # Mostra exemplos
    show_usage_examples()
    
    print("\n📚 Documentação completa: README.md")
    print("🐛 Problemas ou dúvidas: https://github.com/ngmotherline/ngmotherline/issues")

if __name__ == '__main__':
    main() 