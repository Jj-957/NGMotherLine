#!/usr/bin/env python3
"""
Script de instalação otimizado para Windows
Evita problemas de compilação C++ instalando apenas o necessário
"""

import sys
import subprocess
import platform
import logging

def setup_logging():
    """Configura logging básico."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')

def print_banner():
    """Mostra banner do NGMotherLine."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                NGMotherLine v0.1.0 - Windows             ║
    ║        Engine de geração de legendas any-to-any          ║
    ║                                                           ║
    ║               🛠️ Instalador Windows Otimizado            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

def check_system():
    """Verifica compatibilidade do sistema."""
    print("🔍 Verificando sistema...")
    
    # Verifica Python
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ necessário. Atual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Verifica Windows
    if platform.system() != 'Windows':
        print("⚠️  Este instalador é otimizado para Windows")
    
    return True

def install_core_packages():
    """Instala pacotes principais sem problemas de compilação."""
    print("\n📦 Instalando pacotes principais...")
    
    # Lista de pacotes que instalam sem problemas no Windows
    packages = [
        'click>=8.1.0',
        'numpy>=1.24.0', 
        'tqdm>=4.65.0',
        'psutil>=5.9.0',
        'requests>=2.31.0',
        'srt>=3.5.0',
        'ffmpeg-python>=0.2.0'
    ]
    
    for package in packages:
        try:
            print(f"   Instalando {package}...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], check=True, capture_output=True)
            print(f"   ✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erro ao instalar {package}")
            return False
    
    return True

def install_torch():
    """Instala PyTorch (versão CPU por padrão)."""
    print("\n🔥 Instalando PyTorch...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            'torch', 'transformers', '--index-url', 
            'https://download.pytorch.org/whl/cpu'
        ], check=True)
        print("✅ PyTorch instalado (versão CPU)")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar PyTorch")
        return False

def install_whisper():
    """Instala faster-whisper."""
    print("\n🎤 Instalando faster-whisper...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'faster-whisper'
        ], check=True, capture_output=True)
        print("✅ faster-whisper instalado")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar faster-whisper")
        return False

def install_translation():
    """Instala sistema de tradução."""
    print("\n🌐 Instalando sistema de tradução...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'argostranslate'
        ], check=True, capture_output=True)
        print("✅ argostranslate instalado")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar argostranslate")
        return False

def install_audio_packages():
    """Instala pacotes de áudio (tentativa com fallback)."""
    print("\n🎵 Instalando pacotes de áudio...")
    
    # Tenta instalar pacotes de áudio
    audio_packages = ['librosa', 'soundfile']
    
    for package in audio_packages:
        try:
            print(f"   Tentando instalar {package}...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], check=True, capture_output=True)
            print(f"   ✅ {package}")
        except subprocess.CalledProcessError:
            print(f"   ⚠️  {package} não pôde ser instalado (não crítico)")
    
    return True

def test_installation():
    """Testa se a instalação funcionou."""
    print("\n🧪 Testando instalação...")
    
    # Testa importações básicas
    test_imports = [
        ('click', 'Interface CLI'),
        ('numpy', 'Computação numérica'),
        ('torch', 'PyTorch'),
        ('faster_whisper', 'Reconhecimento de fala'),
        ('argostranslate', 'Tradução'),
        ('srt', 'Geração de legendas'),
        ('ffmpeg', 'Processamento de mídia')
    ]
    
    success_count = 0
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"   ✅ {description}")
            success_count += 1
        except ImportError:
            print(f"   ❌ {description}")
    
    print(f"\n📊 Resultado: {success_count}/{len(test_imports)} módulos funcionando")
    
    if success_count >= len(test_imports) - 2:  # Permite 2 falhas
        print("✅ Instalação suficiente para uso básico!")
        return True
    else:
        print("⚠️  Instalação parcial. Algumas funcionalidades podem não funcionar.")
        return False

def show_next_steps():
    """Mostra próximos passos."""
    print("""
    🎯 Próximos passos:
    
    1. Teste básico:
       python test_poc.py
    
    2. Processe um arquivo:
       python main.py seu_video.mp4
    
    3. Com tradução:
       python main.py video.mp4 --target-lang en
    
    4. Ajuda completa:
       python main.py --help
    
    📚 Documentação: README.md
    🐛 Problemas: Verifique os logs acima
    """)

def main():
    """Função principal."""
    setup_logging()
    print_banner()
    
    # Verificações básicas
    if not check_system():
        print("❌ Sistema incompatível")
        sys.exit(1)
    
    # Atualiza pip primeiro
    print("\n⬆️  Atualizando pip...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], check=True, capture_output=True)
        print("✅ pip atualizado")
    except:
        print("⚠️  Não foi possível atualizar pip (continuando...)")
    
    # Instalação em etapas
    steps = [
        ("Pacotes principais", install_core_packages),
        ("PyTorch", install_torch),
        ("faster-whisper", install_whisper),
        ("Sistema de tradução", install_translation),
        ("Pacotes de áudio", install_audio_packages),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ Falha em: {step_name}")
        else:
            print(f"✅ Concluído: {step_name}")
    
    # Testa instalação
    test_installation()
    
    # Resumo final
    if not failed_steps:
        print("\n🎉 Instalação concluída com sucesso!")
    else:
        print(f"\n⚠️  Instalação concluída com {len(failed_steps)} problemas:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nO sistema ainda pode funcionar com funcionalidades limitadas.")
    
    show_next_steps()

if __name__ == '__main__':
    main() 