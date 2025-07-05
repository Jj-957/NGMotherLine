#!/usr/bin/env python3
"""
Pipeline principal do NGMotherLine
Coordena todo o fluxo de processamento
"""

import os
import sys
import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

# Importa componentes do pipeline
from ..audio.extractor import AudioExtractor
from ..audio.vad import VADSegmenter
from ..asr.whisper_engine import WhisperEngine, TranscriptionResult
from ..translation.translator import MotherLineTranslator
from ..subtitle.generator import SubtitleGenerator, SubtitleSegment

logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    """Configuração do pipeline NGMotherLine."""
    mode: str = "fast"
    source_language: str = "auto"
    target_language: Optional[str] = None
    output_formats: List[str] = field(default_factory=lambda: ["srt"])
    embed_subtitles: bool = False
    bilingual_subtitles: bool = False
    multilingual_detection: bool = False
    preserve_original_languages: bool = False
    add_language_labels: bool = False
    vad_method: str = "silero"
    device: str = "auto"
    cpu_threads: Optional[int] = None
    cache_dir: Optional[str] = None
    
    def __post_init__(self):
        """Validação e configuração automática."""
        if self.cache_dir is None:
            self.cache_dir = str(Path.home() / ".cache" / "motherline")
        
        # Configuração automática para modo multilíngue
        if self.multilingual_detection:
            if self.source_language == "auto":
                self.source_language = "multilingual"
            
            # Se não especificou idioma alvo, preserva originais
            if not self.target_language:
                self.preserve_original_languages = True

@dataclass
class ProcessingResult:
    """Resultado do processamento."""
    success: bool
    output_files: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    audio_duration: float = 0.0
    segments_count: int = 0
    detected_language: Optional[str] = None
    languages_found: List[str] = field(default_factory=list)
    multilingual_detected: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MotherLinePipeline:
    """Pipeline principal do NGMotherLine."""
    
    def __init__(self, config: PipelineConfig):
        """
        Inicializa o pipeline.
        
        Args:
            config: Configuração do pipeline
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Inicializa componentes
        self._initialize_components()
        
        # Estatísticas de processamento
        self.processing_stats = {}
        
        self.logger.info(f"Pipeline inicializado com configuração: {config}")
    
    def _initialize_components(self):
        """Inicializa todos os componentes do pipeline."""
        try:
            # Extrator de áudio
            self.audio_extractor = AudioExtractor()
            
            # VAD Segmenter
            self.vad_segmenter = VADSegmenter(
                method=self.config.vad_method,
                device=self.config.device
            )
            
            # Engine Whisper
            self.whisper_engine = WhisperEngine(
                mode=self.config.mode,
                device=self.config.device,
                cpu_threads=self.config.cpu_threads
            )
            
            # Tradutor (se necessário)
            self.translator = None
            if self.config.target_language:
                self.translator = MotherLineTranslator()
            
            # Gerador de legendas
            self.subtitle_generator = SubtitleGenerator()
            
            self.logger.info("Todos os componentes inicializados com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar componentes: {e}")
            raise RuntimeError(f"Falha na inicialização do pipeline: {e}")
    
    def process_file(self, input_file: str, output_dir: Optional[str] = None) -> ProcessingResult:
        """
        Processa um arquivo de mídia.
        
        Args:
            input_file: Caminho para o arquivo de entrada
            output_dir: Diretório de saída (opcional)
            
        Returns:
            Resultado do processamento
        """
        start_time = time.time()
        
        try:
            # Valida entrada
            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {input_file}")
            
            # Define diretório de saída
            if output_dir is None:
                output_dir = str(input_path.parent)
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Executa pipeline
            result = self._execute_pipeline(input_path, output_path)
            
            # Calcula tempo total
            result.processing_time = time.time() - start_time
            result.metadata['processing_stats'] = self.processing_stats
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processamento: {e}")
            
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def _execute_pipeline(self, input_path: Path, output_path: Path) -> ProcessingResult:
        """Executa o pipeline completo."""
        
        # Passo 1: Extrair áudio
        self.logger.info("Passo 1: Extraindo áudio...")
        step_start = time.time()
        
        audio_data, sample_rate = self.audio_extractor.extract_audio(str(input_path))
        audio_duration = len(audio_data) / sample_rate
        
        self.processing_stats['audio_extraction'] = time.time() - step_start
        self.logger.info(f"Áudio extraído: {audio_duration:.2f}s @ {sample_rate}Hz")
        
        # Passo 2: Segmentação VAD
        self.logger.info("Passo 2: Segmentando áudio...")
        step_start = time.time()
        
        segments = self.vad_segmenter.segment_audio(audio_data, sample_rate)
        
        self.processing_stats['vad_segmentation'] = time.time() - step_start
        self.logger.info(f"Segmentos encontrados: {len(segments)}")
        
        # Passo 3: Transcrição
        self.logger.info("Passo 3: Transcrevendo áudio...")
        step_start = time.time()
        
        if self.config.multilingual_detection:
            transcription_result = self.whisper_engine.transcribe_multilingual(audio_data, sample_rate)
        else:
            language = None if self.config.source_language == "auto" else self.config.source_language
            transcription_result = self.whisper_engine.transcribe_audio(
                audio_data, 
                sample_rate, 
                language=language
            )
        
        self.processing_stats['transcription'] = time.time() - step_start
        self.logger.info(f"Transcrição concluída: {len(transcription_result.segments)} segmentos")
        
        # Passo 4: Tradução (se necessário)
        translation_time = 0
        if self.config.target_language and self.translator:
            self.logger.info("Passo 4: Traduzindo texto...")
            step_start = time.time()
            
            transcription_result = self._translate_segments(transcription_result)
            
            translation_time = time.time() - step_start
            self.processing_stats['translation'] = translation_time
            self.logger.info("Tradução concluída")
        
        # Passo 5: Geração de legendas
        self.logger.info("Passo 5: Gerando legendas...")
        step_start = time.time()
        
        subtitle_segments = self._create_subtitle_segments(transcription_result)
        output_files = self._generate_subtitle_files(subtitle_segments, input_path, output_path)
        
        self.processing_stats['subtitle_generation'] = time.time() - step_start
        self.logger.info(f"Legendas geradas: {len(output_files)} arquivos")
        
        # Passo 6: Embed legendas (se necessário)
        if self.config.embed_subtitles:
            self.logger.info("Passo 6: Embedando legendas no vídeo...")
            step_start = time.time()
            
            embedded_file = self._embed_subtitles(input_path, output_path, output_files)
            if embedded_file:
                output_files.append(embedded_file)
            
            self.processing_stats['subtitle_embedding'] = time.time() - step_start
        
        # Retorna resultado
        return ProcessingResult(
            success=True,
            output_files=output_files,
            audio_duration=audio_duration,
            segments_count=len(transcription_result.segments),
            detected_language=transcription_result.detected_language,
            languages_found=transcription_result.languages_found or [],
            multilingual_detected=transcription_result.multilingual_detected,
            metadata={
                'transcription_info': {
                    'model_used': transcription_result.model_used,
                    'language_confidence': transcription_result.language_confidence,
                    'processing_time': transcription_result.processing_time
                }
            }
        )
    
    def _translate_segments(self, transcription_result: TranscriptionResult) -> TranscriptionResult:
        """Traduz segmentos conforme configuração."""
        if not self.translator:
            return transcription_result
        
        for segment in transcription_result.segments:
            # Determina idioma fonte
            source_lang = segment.language if self.config.multilingual_detection else transcription_result.detected_language
            
            # Traduz se necessário
            if source_lang != self.config.target_language:
                try:
                    translation = self.translator.translate_text(
                        segment.text, 
                        source_lang, 
                        self.config.target_language
                    )
                    
                    # Atualiza segmento baseado na configuração
                    if self.config.preserve_original_languages:
                        # Preserva texto original, adiciona tradução
                        segment.translated_text = translation.translated_text
                    else:
                        # Substitui texto original pela tradução
                        segment.text = translation.translated_text
                        segment.language = self.config.target_language
                        
                except Exception as e:
                    self.logger.warning(f"Erro ao traduzir segmento {segment.id}: {e}")
                    # Mantém texto original em caso de erro
                    if self.config.preserve_original_languages:
                        segment.translated_text = segment.text
            
            elif self.config.preserve_original_languages:
                # Mesmo idioma, mas preserva formato
                segment.translated_text = segment.text
        
        return transcription_result
    
    def _create_subtitle_segments(self, transcription_result: TranscriptionResult) -> List[SubtitleSegment]:
        """Cria segmentos de legenda a partir da transcrição."""
        subtitle_segments = []
        
        for segment in transcription_result.segments:
            # Determina textos a serem exibidos
            original_text = segment.text
            translated_text = getattr(segment, 'translated_text', None)
            
            # Adiciona rótulos de idioma se solicitado
            if self.config.add_language_labels and self.config.multilingual_detection:
                language_label = f"[{segment.language.upper()}] "
                original_text = language_label + original_text
                
                if translated_text and self.config.target_language:
                    target_label = f"[{self.config.target_language.upper()}] "
                    translated_text = target_label + translated_text
            
            # Cria segmento de legenda
            if self.config.bilingual_subtitles and translated_text:
                # Legendas bilíngues
                final_text = f"{original_text}\n{translated_text}"
            elif self.config.preserve_original_languages and translated_text:
                # Preserva original ou mostra tradução conforme idioma
                if segment.language == self.config.target_language:
                    final_text = original_text
                else:
                    final_text = translated_text
            else:
                # Texto simples
                final_text = original_text
            
            subtitle_segments.append(SubtitleSegment(
                id=segment.id,
                start=segment.start,
                end=segment.end,
                text=final_text,
                translated_text=translated_text
            ))
        
        return subtitle_segments
    
    def _generate_subtitle_files(self, segments: List[SubtitleSegment], 
                               input_path: Path, output_path: Path) -> List[str]:
        """Gera arquivos de legenda nos formatos solicitados."""
        output_files = []
        base_name = input_path.stem
        
        for format_type in self.config.output_formats:
            try:
                if format_type == "srt":
                    output_file = output_path / f"{base_name}.srt"
                    self.subtitle_generator.generate_srt(segments, str(output_file))
                    
                elif format_type == "vtt":
                    output_file = output_path / f"{base_name}.vtt"
                    self.subtitle_generator.generate_vtt(segments, str(output_file))
                    
                elif format_type == "ass":
                    output_file = output_path / f"{base_name}.ass"
                    self.subtitle_generator.generate_ass(segments, str(output_file))
                
                output_files.append(str(output_file))
                self.logger.info(f"Arquivo {format_type.upper()} gerado: {output_file}")
                
            except Exception as e:
                self.logger.error(f"Erro ao gerar arquivo {format_type}: {e}")
        
        # Gera arquivo de metadata se modo multilíngue
        if self.config.multilingual_detection:
            metadata_file = output_path / f"{base_name}_metadata.json"
            self._generate_metadata_file(segments, metadata_file)
            output_files.append(str(metadata_file))
        
        return output_files
    
    def _generate_metadata_file(self, segments: List[SubtitleSegment], output_file: Path):
        """Gera arquivo de metadata com informações dos idiomas."""
        metadata = {
            "total_segments": len(segments),
            "languages_detected": list(set(getattr(seg, 'language', 'unknown') for seg in segments)),
            "multilingual_mode": self.config.multilingual_detection,
            "preserve_original": self.config.preserve_original_languages,
            "language_labels": self.config.add_language_labels,
            "segments": [
                {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "language": getattr(seg, 'language', 'unknown'),
                    "text_length": len(seg.text),
                    "has_translation": hasattr(seg, 'translated_text') and seg.translated_text is not None
                }
                for seg in segments
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Arquivo de metadata gerado: {output_file}")
    
    def _embed_subtitles(self, input_path: Path, output_path: Path, 
                        subtitle_files: List[str]) -> Optional[str]:
        """Embeda legendas no vídeo usando FFmpeg."""
        if not subtitle_files:
            return None
        
        try:
            # Usa o primeiro arquivo SRT disponível
            srt_file = None
            for file in subtitle_files:
                if file.endswith('.srt'):
                    srt_file = file
                    break
            
            if not srt_file:
                self.logger.warning("Nenhum arquivo SRT encontrado para embedding")
                return None
            
            # Gera vídeo com legendas embedadas
            output_file = output_path / f"{input_path.stem}_with_subs{input_path.suffix}"
            
            success = self.subtitle_generator.embed_subtitles(
                str(input_path), 
                srt_file, 
                str(output_file)
            )
            
            if success:
                self.logger.info(f"Legendas embedadas com sucesso: {output_file}")
                return str(output_file)
            else:
                self.logger.error("Falha ao embedar legendas")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao embedar legendas: {e}")
            return None
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o pipeline."""
        return {
            "config": self.config,
            "components": {
                "audio_extractor": self.audio_extractor.__class__.__name__,
                "vad_segmenter": self.vad_segmenter.__class__.__name__,
                "whisper_engine": self.whisper_engine.__class__.__name__,
                "translator": self.translator.__class__.__name__ if self.translator else None,
                "subtitle_generator": self.subtitle_generator.__class__.__name__
            },
            "processing_stats": self.processing_stats
        }
    
    def cleanup(self):
        """Limpa recursos do pipeline."""
        try:
            if hasattr(self, 'whisper_engine'):
                self.whisper_engine.cleanup()
            
            if hasattr(self, 'translator') and self.translator:
                self.translator.cleanup()
                
            self.logger.info("Recursos do pipeline limpos")
            
        except Exception as e:
            self.logger.warning(f"Erro ao limpar recursos: {e}")
    
    def __enter__(self):
        """Context manager entrada."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager saída."""
        self.cleanup() 