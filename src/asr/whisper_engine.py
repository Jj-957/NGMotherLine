"""
Engine de reconhecimento de fala usando faster-whisper.
Suporta modos FAST e ACCURATE com otimizações para hardware legado.
"""

import os
import logging
import psutil
from typing import List, Dict, Optional, Tuple, Iterator, Any
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSegment:
    """Representa um segmento de transcrição."""
    id: int
    start: float
    end: float
    text: str
    confidence: float = 0.0
    language: str = "unknown"
    language_confidence: float = 0.0


@dataclass
class TranscriptionResult:
    """Resultado da transcrição."""
    segments: List[TranscriptionSegment]
    detected_language: str
    language_confidence: float
    processing_time: float
    model_used: str
    multilingual_detected: bool = False
    languages_found: List[str] = None


class WhisperEngine:
    """Engine de reconhecimento de fala usando faster-whisper."""
    
    # Configurações dos modelos
    MODEL_CONFIGS = {
        'fast': {
            'model_size': 'tiny',
            'compute_type': 'int8',
            'description': 'Modelo rápido para hardware legado (~39MB)',
            'expected_wer': 15.0,
            'speed_factor': 4.0,
            'language_detection': True
        },
        'accurate': {
            'model_size': 'medium',
            'compute_type': 'int8',
            'description': 'Modelo preciso para melhor qualidade (~769MB)',
            'expected_wer': 8.0,
            'speed_factor': 1.5,
            'language_detection': True
        },
        'premium': {
            'model_size': 'large-v3',
            'compute_type': 'int8',
            'description': 'Modelo premium para máxima qualidade (~1.5GB)',
            'expected_wer': 5.0,
            'speed_factor': 1.0,
            'language_detection': True
        }
    }
    
    def __init__(self, 
                 mode: str = 'fast',
                 language: str = 'auto',
                 device: str = 'auto',
                 cpu_threads: Optional[int] = None,
                 model_cache_dir: Optional[str] = None):
        """
        Inicializa o engine Whisper.
        
        Args:
            mode: Modo de operação ('fast', 'accurate', 'premium')
            language: Idioma do áudio ('auto' para detecção automática)
            device: Dispositivo ('auto', 'cpu', 'cuda')
            cpu_threads: Número de threads CPU (None para auto)
            model_cache_dir: Diretório para cache dos modelos
        """
        self.mode = mode
        self.language = language
        self.device = self._detect_device(device)
        self.cpu_threads = cpu_threads or self._get_optimal_threads()
        self.model_cache_dir = model_cache_dir or self._get_cache_dir()
        
        # Configuração do modelo
        self.model_config = self.MODEL_CONFIGS.get(mode, self.MODEL_CONFIGS['fast'])
        
        # Modelo carregado
        self.model = None
        self.model_loaded = False
        
        # Configurações para detecção multilíngue
        self.language_detection_threshold = 0.7
        self.segment_language_detection = True
        
        logger.info(f"Whisper Engine inicializado:")
        logger.info(f"  Modo: {mode}")
        logger.info(f"  Modelo: {self.model_config['model_size']}")
        logger.info(f"  Dispositivo: {self.device}")
        logger.info(f"  Threads: {self.cpu_threads}")
        logger.info(f"  Cache: {self.model_cache_dir}")
    
    def _detect_device(self, device: str) -> str:
        """Detecta o melhor dispositivo disponível."""
        if device == 'auto':
            try:
                import torch
                if torch.cuda.is_available():
                    return 'cuda'
                else:
                    return 'cpu'
            except ImportError:
                return 'cpu'
        return device
    
    def _get_optimal_threads(self) -> int:
        """Calcula o número ótimo de threads baseado no hardware."""
        cpu_count = psutil.cpu_count(logical=False)  # Núcleos físicos
        
        # Reserva 1 núcleo para o sistema
        optimal_threads = max(1, cpu_count - 1)
        
        # Limita baseado na memória disponível
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 4:
            optimal_threads = min(optimal_threads, 2)
        elif memory_gb < 8:
            optimal_threads = min(optimal_threads, 4)
        
        return optimal_threads
    
    def _get_cache_dir(self) -> str:
        """Retorna o diretório de cache dos modelos."""
        if os.name == 'nt':  # Windows
            cache_dir = os.path.expandvars(r'%APPDATA%\MotherLine\models')
        else:  # Linux/Mac
            cache_dir = os.path.expanduser('~/.cache/motherline/models')
        
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def load_model(self) -> bool:
        """Carrega o modelo Whisper."""
        if self.model_loaded:
            return True
        
        try:
            logger.info(f"Carregando modelo {self.model_config['model_size']}...")
            
            # Configurações do modelo
            model_kwargs = {
                'model_size_or_path': self.model_config['model_size'],
                'device': self.device,
                'compute_type': self.model_config['compute_type'],
                'download_root': self.model_cache_dir,
                'cpu_threads': self.cpu_threads if self.device == 'cpu' else None
            }
            
            # Remove argumentos None
            model_kwargs = {k: v for k, v in model_kwargs.items() if v is not None}
            
            self.model = WhisperModel(**model_kwargs)
            self.model_loaded = True
            
            logger.info("Modelo carregado com sucesso!")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False
    
    def transcribe_audio(self, 
                        audio_data: np.ndarray, 
                        sample_rate: int = 16000,
                        language: Optional[str] = None,
                        multilingual_mode: bool = False) -> TranscriptionResult:
        """
        Transcreve áudio para texto.
        
        Args:
            audio_data: Array de áudio
            sample_rate: Taxa de amostragem
            language: Idioma (None para usar o padrão)
            multilingual_mode: Se True, detecta idiomas por segmento
            
        Returns:
            Resultado da transcrição
        """
        if not self.model_loaded:
            self.load_model()
        
        # Usa idioma especificado ou padrão
        lang = language or self.language
        
        try:
            # Prepara parâmetros da transcrição
            transcribe_kwargs = {
                'audio': audio_data,
                'language': lang if lang != 'auto' else None,
                'task': 'transcribe',
                'vad_filter': True,
                'vad_parameters': {
                    'min_silence_duration_ms': 500,
                    'speech_pad_ms': 400
                }
            }
            
            # Executa transcrição
            segments, info = self.model.transcribe(**transcribe_kwargs)
            
            # Converte para nossa estrutura
            result_segments = []
            languages_found = set()
            
            for i, segment in enumerate(segments):
                # Detecta idioma do segmento se em modo multilíngue
                segment_language = info.language
                segment_lang_confidence = info.language_probability
                
                if multilingual_mode and self.segment_language_detection:
                    # Extrai áudio do segmento
                    start_sample = int(segment.start * sample_rate)
                    end_sample = int(segment.end * sample_rate)
                    segment_audio = audio_data[start_sample:end_sample]
                    
                    detected_lang = self.detect_segment_language(segment_audio, sample_rate)
                    if detected_lang != "unknown":
                        segment_language = detected_lang
                        segment_lang_confidence = 0.8  # Estimativa
                
                languages_found.add(segment_language)
                
                result_segments.append(
                    TranscriptionSegment(
                        id=i + 1,
                        start=segment.start,
                        end=segment.end,
                        text=segment.text.strip(),
                        confidence=getattr(segment, 'avg_logprob', 0.0),
                        language=segment_language,
                        language_confidence=segment_lang_confidence
                    )
                )
            
            logger.info(f"Transcrição concluída: {len(result_segments)} segmentos")
            
            processing_time = time.time() - start_time
            multilingual_detected = len(languages_found) > 1
            
            return TranscriptionResult(
                segments=result_segments,
                detected_language=info.language,
                language_confidence=info.language_probability,
                processing_time=processing_time,
                model_used=self.model_config['model_size'],
                multilingual_detected=multilingual_detected,
                languages_found=list(languages_found)
            )
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            raise RuntimeError(f"Falha na transcrição: {e}")
    
    def transcribe_segments(self, 
                           audio_segments: List[Tuple[np.ndarray, float, float]],
                           language: Optional[str] = None) -> List[TranscriptionSegment]:
        """
        Transcreve múltiplos segmentos de áudio.
        
        Args:
            audio_segments: Lista de (audio_data, start_time, end_time)
            language: Idioma (None para usar o padrão)
            
        Returns:
            Lista de segmentos transcritos
        """
        if not self.model_loaded:
            self.load_model()
        
        all_segments = []
        
        for i, (audio_data, start_time, end_time) in enumerate(audio_segments):
            try:
                logger.debug(f"Transcrevendo segmento {i+1}/{len(audio_segments)}")
                
                # Transcreve segmento individual
                segments = self.transcribe_audio(audio_data, language=language)
                
                # Ajusta timestamps para posição absoluta
                for segment in segments.segments:
                    segment.start += start_time
                    segment.end += start_time
                    all_segments.append(segment)
                    
            except Exception as e:
                logger.warning(f"Erro ao transcrever segmento {i+1}: {e}")
                # Cria segmento vazio para manter continuidade
                all_segments.append(
                    TranscriptionSegment(
                        id=i + 1,
                        start=start_time,
                        end=end_time,
                        text="[Erro na transcrição]",
                        confidence=0.0,
                        language="unknown",
                        language_confidence=0.0
                    )
                )
        
        return all_segments
    
    def detect_language(self, audio_data: np.ndarray) -> Tuple[str, float]:
        """
        Detecta o idioma do áudio.
        
        Args:
            audio_data: Array de áudio
            
        Returns:
            Tuple com (idioma, confiança)
        """
        if not self.model_loaded:
            self.load_model()
        
        try:
            # Usa apenas os primeiros 30 segundos para detecção
            sample_rate = 16000
            max_samples = 30 * sample_rate
            audio_sample = audio_data[:max_samples]
            
            # Detecta idioma
            segments, info = self.model.transcribe(
                audio_sample,
                language=None,  # Força detecção automática
                task='transcribe'
            )
            
            return info.language, info.language_probability
            
        except Exception as e:
            logger.error(f"Erro na detecção de idioma: {e}")
            return 'unknown', 0.0
    
    def detect_segment_language(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Detecta idioma de um segmento específico de áudio.
        
        Args:
            audio: Dados de áudio do segmento
            sample_rate: Taxa de amostragem
            
        Returns:
            Código do idioma detectado
        """
        if len(audio) < sample_rate * 2:  # Menos de 2 segundos
            return "unknown"
            
        try:
            if hasattr(self.model, 'detect_language'):
                language, confidence = self.model.detect_language(audio)
                if confidence > self.language_detection_threshold:
                    return language
                    
        except Exception as e:
            logger.debug(f"Erro na detecção de idioma do segmento: {e}")
            
        return "unknown"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo atual."""
        return {
            'mode': self.mode,
            'model_size': self.model_config['model_size'],
            'compute_type': self.model_config['compute_type'],
            'description': self.model_config['description'],
            'expected_wer': self.model_config['expected_wer'],
            'speed_factor': self.model_config['speed_factor'],
            'device': self.device,
            'cpu_threads': self.cpu_threads,
            'model_loaded': self.model_loaded,
            'multilingual_support': self.model_config['language_detection'],
            'language_detection_threshold': self.language_detection_threshold
        }
    
    def unload_model(self) -> None:
        """Descarrega o modelo da memória."""
        if self.model:
            del self.model
            self.model = None
            self.model_loaded = False
            logger.info("Modelo descarregado da memória")
    
    @staticmethod
    def get_available_models() -> Dict[str, Dict[str, Any]]:
        """Retorna informações sobre os modelos disponíveis."""
        return WhisperEngine.MODEL_CONFIGS.copy() 