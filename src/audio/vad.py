"""
Voice Activity Detection (VAD) para segmentação inteligente de áudio.
Implementa Silero VAD com fallback para WebRTC VAD e segmentação fixa.
"""

import logging
import numpy as np
from typing import List, Tuple, Optional
import torch

logger = logging.getLogger(__name__)

# Importação condicional do webrtcvad
try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    WEBRTCVAD_AVAILABLE = False
    logger.warning("webrtcvad não disponível. Usando apenas Silero VAD e segmentação fixa.")


class VADSegmenter:
    """Segmentador de áudio usando Voice Activity Detection."""
    
    def __init__(self, 
                 method: str = 'silero', 
                 aggressiveness: int = 1,
                 min_speech_duration: float = 0.5,
                 max_speech_duration: float = 30.0,
                 sample_rate: int = 16000):
        """
        Inicializa o segmentador VAD.
        
        Args:
            method: Método VAD ('silero', 'webrtc', 'fixed')
            aggressiveness: Nível de agressividade (0-3, apenas para WebRTC)
            min_speech_duration: Duração mínima do segmento em segundos
            max_speech_duration: Duração máxima do segmento em segundos
            sample_rate: Taxa de amostragem em Hz
        """
        self.method = method
        self.aggressiveness = aggressiveness
        self.min_speech_duration = min_speech_duration
        self.max_speech_duration = max_speech_duration
        self.sample_rate = sample_rate
        
        # Inicializa o modelo VAD
        self.vad_model = None
        self.webrtc_vad = None
        
        self._init_vad()
    
    def _init_vad(self) -> None:
        """Inicializa o modelo VAD baseado no método selecionado."""
        if self.method == 'silero':
            try:
                # Carrega modelo Silero VAD
                self.vad_model, _ = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False,
                    onnx=False
                )
                logger.info("Silero VAD carregado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao carregar Silero VAD: {e}")
                logger.info("Utilizando WebRTC VAD como fallback")
                self.method = 'webrtc'
                self._init_webrtc_vad()
        
        elif self.method == 'webrtc':
            self._init_webrtc_vad()
        
        elif self.method == 'fixed':
            logger.info("Usando segmentação fixa")
        
        else:
            raise ValueError(f"Método VAD inválido: {self.method}")
    
    def _init_webrtc_vad(self) -> None:
        """Inicializa WebRTC VAD."""
        if not WEBRTCVAD_AVAILABLE:
            logger.warning("WebRTC VAD não disponível. Usando segmentação fixa.")
            self.method = 'fixed'
            return
        
        try:
            self.webrtc_vad = webrtcvad.Vad(self.aggressiveness)
            logger.info("WebRTC VAD inicializado")
        except Exception as e:
            logger.warning(f"Erro ao inicializar WebRTC VAD: {e}")
            logger.info("Utilizando segmentação fixa como fallback")
            self.method = 'fixed'
    
    def segment_audio(self, audio_data: np.ndarray) -> List[Tuple[float, float]]:
        """
        Segmenta o áudio em intervalos de fala.
        
        Args:
            audio_data: Array de áudio normalizado
            
        Returns:
            Lista de tuplas (tempo_inicio, tempo_fim) em segundos
        """
        if self.method == 'silero':
            return self._segment_silero(audio_data)
        elif self.method == 'webrtc':
            return self._segment_webrtc(audio_data)
        else:
            return self._segment_fixed(audio_data)
    
    def _segment_silero(self, audio_data: np.ndarray) -> List[Tuple[float, float]]:
        """Segmenta usando Silero VAD."""
        try:
            # Converte para tensor
            audio_tensor = torch.from_numpy(audio_data).float()
            
            # Aplica VAD
            speech_timestamps = self.vad_model(
                audio_tensor, 
                self.sample_rate,
                return_seconds=True
            )
            
            # Converte para lista de tuplas
            segments = []
            for timestamp in speech_timestamps:
                start_time = timestamp['start']
                end_time = timestamp['end']
                
                # Aplica filtros de duração
                duration = end_time - start_time
                if duration >= self.min_speech_duration:
                    # Divide segmentos muito longos
                    if duration > self.max_speech_duration:
                        segments.extend(
                            self._split_long_segment(start_time, end_time)
                        )
                    else:
                        segments.append((start_time, end_time))
            
            return segments
            
        except Exception as e:
            logger.error(f"Erro no Silero VAD: {e}")
            return self._segment_fixed(audio_data)
    
    def _segment_webrtc(self, audio_data: np.ndarray) -> List[Tuple[float, float]]:
        """Segmenta usando WebRTC VAD."""
        if not WEBRTCVAD_AVAILABLE or self.webrtc_vad is None:
            logger.warning("WebRTC VAD não disponível, usando segmentação fixa")
            return self._segment_fixed(audio_data)
        
        try:
            # Converte para formato int16 para WebRTC
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Tamanho da janela em amostras (10, 20 ou 30ms)
            frame_duration = 30  # ms
            frame_size = int(self.sample_rate * frame_duration / 1000)
            
            segments = []
            current_start = None
            
            for i in range(0, len(audio_int16), frame_size):
                frame = audio_int16[i:i + frame_size]
                
                # Preenche frame se necessário
                if len(frame) < frame_size:
                    frame = np.pad(frame, (0, frame_size - len(frame)), 'constant')
                
                # Converte para bytes
                frame_bytes = frame.tobytes()
                
                # Detecta fala
                is_speech = self.webrtc_vad.is_speech(frame_bytes, self.sample_rate)
                
                current_time = i / self.sample_rate
                
                if is_speech and current_start is None:
                    current_start = current_time
                elif not is_speech and current_start is not None:
                    duration = current_time - current_start
                    if duration >= self.min_speech_duration:
                        segments.append((current_start, current_time))
                    current_start = None
            
            # Adiciona último segmento se necessário
            if current_start is not None:
                end_time = len(audio_int16) / self.sample_rate
                duration = end_time - current_start
                if duration >= self.min_speech_duration:
                    segments.append((current_start, end_time))
            
            return segments
            
        except Exception as e:
            logger.error(f"Erro no WebRTC VAD: {e}")
            return self._segment_fixed(audio_data)
    
    def _segment_fixed(self, audio_data: np.ndarray) -> List[Tuple[float, float]]:
        """Segmenta usando intervalos fixos."""
        duration = len(audio_data) / self.sample_rate
        segment_length = min(self.max_speech_duration, 10.0)  # 10s por padrão
        
        segments = []
        current_time = 0.0
        
        while current_time < duration:
            end_time = min(current_time + segment_length, duration)
            segments.append((current_time, end_time))
            current_time = end_time
        
        return segments
    
    def _split_long_segment(self, start_time: float, end_time: float) -> List[Tuple[float, float]]:
        """Divide segmentos muito longos em partes menores."""
        segments = []
        current_start = start_time
        
        while current_start < end_time:
            current_end = min(current_start + self.max_speech_duration, end_time)
            segments.append((current_start, current_end))
            current_start = current_end
        
        return segments
    
    def get_audio_segments(self, audio_data: np.ndarray) -> List[Tuple[np.ndarray, float, float]]:
        """
        Retorna segmentos de áudio com dados e timestamps.
        
        Args:
            audio_data: Array de áudio
            
        Returns:
            Lista de tuplas (segment_data, start_time, end_time)
        """
        segments = self.segment_audio(audio_data)
        audio_segments = []
        
        for start_time, end_time in segments:
            start_sample = int(start_time * self.sample_rate)
            end_sample = int(end_time * self.sample_rate)
            
            segment_data = audio_data[start_sample:end_sample]
            audio_segments.append((segment_data, start_time, end_time))
        
        return audio_segments 