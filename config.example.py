"""
Arquivo de configuração exemplo para NGMotherLine
Copie para config.py e configure conforme necessário
"""

import os
from pathlib import Path

# Configurações de Cache
CACHE_DIR = os.path.expandvars(r'%APPDATA%\MotherLine') if os.name == 'nt' else '~/.cache/motherline'
WHISPER_CACHE_DIR = os.path.join(CACHE_DIR, 'models')
ARGOS_CACHE_DIR = os.path.join(CACHE_DIR, 'translation')

# Configurações de Performance
MAX_THREADS = 4
DEFAULT_DEVICE = 'auto'  # 'auto', 'cpu', 'cuda'
MEMORY_LIMIT_MB = 8192

# Configurações de Logging
LOG_LEVEL = 'INFO'  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_FILE = os.path.join(CACHE_DIR, 'logs', 'motherline.log')

# Configurações de Rede
DOWNLOAD_TIMEOUT = 300
RETRY_COUNT = 3
PROXY_URL = None

# Configurações de Whisper
WHISPER_DEFAULT_MODEL = 'fast'  # 'fast', 'accurate', 'premium'
WHISPER_COMPUTE_TYPE = 'int8'   # 'int8', 'int16', 'float16', 'float32'
WHISPER_BEAM_SIZE = 5
WHISPER_BEST_OF = 5

# Configurações de Tradução
ARGOS_AUTO_DOWNLOAD = True
ARGOS_UPDATE_FREQUENCY = 'weekly'

# Configurações de Desenvolvimento
DEBUG = False
VERBOSE = False
PROFILE = False

# Configurações de Telemetria (desabilitado por padrão)
TELEMETRY_ENABLED = False
ANALYTICS_ENABLED = False

# Configurações de Interface
GUI_THEME = 'auto'  # 'auto', 'light', 'dark'
GUI_LANGUAGE = 'pt'  # 'pt', 'en', 'es', etc.
CLI_COLORS = True 