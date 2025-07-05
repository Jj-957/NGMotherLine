"""
Extrator de áudio usando FFmpeg para suporte a múltiplos formatos.
Otimizado para performance em hardware legado.
"""

import os
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple
import ffmpeg
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioExtractor:
    """Extrator de áudio com suporte a múltiplos formatos usando FFmpeg."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """
        Inicializa o extrator de áudio.
        
        Args:
            sample_rate: Taxa de amostragem em Hz (padrão: 16kHz para Whisper)
            channels: Número de canais (padrão: 1 para mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> None:
        """Verifica se o FFmpeg está disponível."""
        try:
            subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg não encontrado. Certifique-se de que está instalado e no PATH."
            )
    
    def extract_audio(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Extrai áudio do arquivo de mídia.
        
        Args:
            input_path: Caminho para o arquivo de entrada
            output_path: Caminho para salvar o áudio extraído (opcional)
            
        Returns:
            Caminho do arquivo de áudio extraído
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
        
        # Gera nome do arquivo de saída se não fornecido
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.wav')
        
        try:
            # Extrai áudio usando FFmpeg com otimizações
            (
                ffmpeg
                .input(str(input_path))
                .output(
                    output_path,
                    acodec='pcm_s16le',  # PCM 16-bit
                    ac=self.channels,    # Número de canais
                    ar=self.sample_rate, # Taxa de amostragem
                    loglevel='error'     # Reduz verbosidade
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"Áudio extraído: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = f"Erro ao extrair áudio: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_audio_info(self, input_path: str) -> dict:
        """
        Obtém informações sobre o arquivo de áudio/vídeo.
        
        Args:
            input_path: Caminho para o arquivo
            
        Returns:
            Dicionário com informações do áudio
        """
        try:
            probe = ffmpeg.probe(input_path)
            audio_streams = [
                stream for stream in probe['streams'] 
                if stream['codec_type'] == 'audio'
            ]
            
            if not audio_streams:
                raise ValueError("Nenhum stream de áudio encontrado")
            
            audio_stream = audio_streams[0]
            
            return {
                'duration': float(probe['format']['duration']),
                'sample_rate': int(audio_stream['sample_rate']),
                'channels': audio_stream['channels'],
                'codec': audio_stream['codec_name'],
                'bit_rate': audio_stream.get('bit_rate', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do áudio: {e}")
            raise
    
    def extract_audio_array(self, input_path: str) -> Tuple[np.ndarray, int]:
        """
        Extrai áudio como array NumPy.
        
        Args:
            input_path: Caminho para o arquivo de entrada
            
        Returns:
            Tuple com (array_audio, sample_rate)
        """
        temp_file = None
        try:
            # Extrai para arquivo temporário
            temp_file = self.extract_audio(input_path)
            
            # Carrega como array NumPy
            audio_data, sr = sf.read(temp_file, dtype='float32')
            
            # Garante que é mono
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            return audio_data, sr
            
        finally:
            # Limpa arquivo temporário
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
    
    def get_supported_formats(self) -> list:
        """
        Retorna lista de formatos suportados pelo FFmpeg.
        
        Returns:
            Lista de extensões de arquivo suportadas
        """
        return [
            # Vídeo
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
            '.3gp', '.mpg', '.mpeg', '.ts', '.mts', '.vob',
            # Áudio
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus',
            '.amr', '.aif', '.aiff', '.au', '.ra'
        ] 