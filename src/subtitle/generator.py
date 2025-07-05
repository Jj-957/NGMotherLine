"""
Gerador de legendas em múltiplos formatos.
Suporta SRT, VTT, ASS e embedding em vídeos.
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import timedelta
import srt
import ffmpeg
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SubtitleSegment:
    """Segmento de legenda."""
    index: int
    start: float
    end: float
    text: str
    translation: Optional[str] = None


class SubtitleGenerator:
    """Gerador de legendas em múltiplos formatos."""
    
    def __init__(self):
        """Inicializa o gerador de legendas."""
        self.supported_formats = ['srt', 'vtt', 'ass']
        logger.info("Gerador de legendas inicializado")
    
    def create_subtitle_segments(self, 
                                transcription_segments: List,
                                translation_results: Optional[List] = None) -> List[SubtitleSegment]:
        """
        Cria segmentos de legenda a partir da transcrição.
        
        Args:
            transcription_segments: Segmentos de transcrição
            translation_results: Resultados de tradução (opcional)
            
        Returns:
            Lista de segmentos de legenda
        """
        subtitle_segments = []
        
        for i, segment in enumerate(transcription_segments):
            # Texto da transcrição
            text = segment.text if hasattr(segment, 'text') else str(segment)
            
            # Texto traduzido (se disponível)
            translation = None
            if translation_results and i < len(translation_results):
                translation = translation_results[i].translated_text
            
            # Timestamps
            start_time = segment.start if hasattr(segment, 'start') else 0.0
            end_time = segment.end if hasattr(segment, 'end') else start_time + 3.0
            
            subtitle_segments.append(SubtitleSegment(
                index=i + 1,
                start=start_time,
                end=end_time,
                text=text.strip(),
                translation=translation
            ))
        
        return subtitle_segments
    
    def generate_srt(self, 
                    segments: List[SubtitleSegment],
                    output_path: str,
                    use_translation: bool = False) -> str:
        """
        Gera arquivo SRT.
        
        Args:
            segments: Segmentos de legenda
            output_path: Caminho do arquivo de saída
            use_translation: Se deve usar tradução ao invés do texto original
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            srt_subtitles = []
            
            for segment in segments:
                # Escolhe texto original ou tradução
                text = (segment.translation if use_translation and segment.translation 
                       else segment.text)
                
                if not text or not text.strip():
                    continue
                
                # Converte timestamps para timedelta
                start_time = timedelta(seconds=segment.start)
                end_time = timedelta(seconds=segment.end)
                
                # Cria subtitle
                subtitle = srt.Subtitle(
                    index=segment.index,
                    start=start_time,
                    end=end_time,
                    content=text.strip()
                )
                
                srt_subtitles.append(subtitle)
            
            # Gera conteúdo SRT
            srt_content = srt.compose(srt_subtitles)
            
            # Salva arquivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"Arquivo SRT gerado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar SRT: {e}")
            raise
    
    def generate_vtt(self, 
                    segments: List[SubtitleSegment],
                    output_path: str,
                    use_translation: bool = False) -> str:
        """
        Gera arquivo VTT (WebVTT).
        
        Args:
            segments: Segmentos de legenda
            output_path: Caminho do arquivo de saída
            use_translation: Se deve usar tradução ao invés do texto original
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            vtt_content = "WEBVTT\n\n"
            
            for segment in segments:
                # Escolhe texto original ou tradução
                text = (segment.translation if use_translation and segment.translation 
                       else segment.text)
                
                if not text or not text.strip():
                    continue
                
                # Formata timestamps para VTT
                start_time = self._format_vtt_time(segment.start)
                end_time = self._format_vtt_time(segment.end)
                
                # Adiciona segmento
                vtt_content += f"{start_time} --> {end_time}\n"
                vtt_content += f"{text.strip()}\n\n"
            
            # Salva arquivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(vtt_content)
            
            logger.info(f"Arquivo VTT gerado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar VTT: {e}")
            raise
    
    def generate_ass(self, 
                    segments: List[SubtitleSegment],
                    output_path: str,
                    use_translation: bool = False) -> str:
        """
        Gera arquivo ASS (Advanced SubStation Alpha).
        
        Args:
            segments: Segmentos de legenda
            output_path: Caminho do arquivo de saída
            use_translation: Se deve usar tradução ao invés do texto original
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            # Cabeçalho ASS
            ass_content = """[Script Info]
Title: MotherLine Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            
            for segment in segments:
                # Escolhe texto original ou tradução
                text = (segment.translation if use_translation and segment.translation 
                       else segment.text)
                
                if not text or not text.strip():
                    continue
                
                # Formata timestamps para ASS
                start_time = self._format_ass_time(segment.start)
                end_time = self._format_ass_time(segment.end)
                
                # Adiciona evento
                ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text.strip()}\n"
            
            # Salva arquivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            logger.info(f"Arquivo ASS gerado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar ASS: {e}")
            raise
    
    def generate_bilingual_srt(self, 
                              segments: List[SubtitleSegment],
                              output_path: str) -> str:
        """
        Gera arquivo SRT bilíngue (original + tradução).
        
        Args:
            segments: Segmentos de legenda
            output_path: Caminho do arquivo de saída
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            srt_subtitles = []
            
            for segment in segments:
                if not segment.text or not segment.text.strip():
                    continue
                
                # Texto bilíngue
                text_lines = [segment.text.strip()]
                if segment.translation and segment.translation.strip():
                    text_lines.append(segment.translation.strip())
                
                bilingual_text = "\n".join(text_lines)
                
                # Converte timestamps
                start_time = timedelta(seconds=segment.start)
                end_time = timedelta(seconds=segment.end)
                
                # Cria subtitle
                subtitle = srt.Subtitle(
                    index=segment.index,
                    start=start_time,
                    end=end_time,
                    content=bilingual_text
                )
                
                srt_subtitles.append(subtitle)
            
            # Gera conteúdo SRT
            srt_content = srt.compose(srt_subtitles)
            
            # Salva arquivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"Arquivo SRT bilíngue gerado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar SRT bilíngue: {e}")
            raise
    
    def embed_subtitles(self, 
                       video_path: str,
                       subtitle_path: str,
                       output_path: str,
                       subtitle_format: str = 'srt') -> str:
        """
        Embute legendas no vídeo.
        
        Args:
            video_path: Caminho do vídeo original
            subtitle_path: Caminho do arquivo de legenda
            output_path: Caminho do vídeo com legendas
            subtitle_format: Formato da legenda
            
        Returns:
            Caminho do vídeo gerado
        """
        try:
            logger.info(f"Embedando legendas no vídeo: {video_path}")
            
            # Configuração do filtro de legenda
            if subtitle_format.lower() == 'srt':
                subtitle_filter = f"subtitles={subtitle_path}:force_style='FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=1'"
            elif subtitle_format.lower() == 'ass':
                subtitle_filter = f"ass={subtitle_path}"
            else:
                subtitle_filter = f"subtitles={subtitle_path}"
            
            # Executa FFmpeg
            (
                ffmpeg
                .input(video_path)
                .output(
                    output_path,
                    vf=subtitle_filter,
                    vcodec='libx264',
                    acodec='copy',
                    crf=23,
                    preset='medium'
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"Vídeo com legendas gerado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao embedar legendas: {e}")
            raise
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Formata tempo para formato VTT."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def _format_ass_time(self, seconds: float) -> str:
        """Formata tempo para formato ASS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:01d}:{minutes:02d}:{secs:05.2f}"
    
    def get_supported_formats(self) -> List[str]:
        """Retorna lista de formatos suportados."""
        return self.supported_formats.copy()
    
    def validate_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """
        Valida e corrige segmentos de legenda.
        
        Args:
            segments: Segmentos para validar
            
        Returns:
            Segmentos validados
        """
        validated_segments = []
        
        for segment in segments:
            # Valida timestamps
            if segment.start < 0:
                segment.start = 0
            
            if segment.end <= segment.start:
                segment.end = segment.start + 1.0
            
            # Valida texto
            if not segment.text or not segment.text.strip():
                continue
            
            # Limita duração máxima
            max_duration = 10.0
            if segment.end - segment.start > max_duration:
                segment.end = segment.start + max_duration
            
            validated_segments.append(segment)
        
        return validated_segments 