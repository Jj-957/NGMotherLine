#!/usr/bin/env python3
"""
NGMotherLine - Engine de geração de legendas any-to-any
Ponto de entrada principal para execução via linha de comando.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path para importações
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.cli.main import main

if __name__ == '__main__':
    main() 