"""
Módulo de tradução usando Argos Translate.
Suporta tradução offline com cache de modelos.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import argostranslate.package
import argostranslate.translate
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Resultado da tradução."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 0.0


class MotherLineTranslator:
    """Tradutor offline usando Argos Translate."""
    
    # Mapeamento de códigos de idioma
    LANGUAGE_CODES = {
        'pt': 'Portuguese',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'ru': 'Russian',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'tr': 'Turkish',
        'nl': 'Dutch',
        'pl': 'Polish',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish',
        'cs': 'Czech',
        'hu': 'Hungarian',
        'ro': 'Romanian',
        'bg': 'Bulgarian',
        'hr': 'Croatian',
        'sk': 'Slovak',
        'sl': 'Slovenian',
        'et': 'Estonian',
        'lv': 'Latvian',
        'lt': 'Lithuanian',
        'mt': 'Maltese',
        'ga': 'Irish',
        'cy': 'Welsh'
    }
    
    def __init__(self, 
                 cache_dir: Optional[str] = None,
                 auto_download: bool = True):
        """
        Inicializa o tradutor.
        
        Args:
            cache_dir: Diretório para cache dos modelos
            auto_download: Se deve baixar modelos automaticamente
        """
        self.cache_dir = cache_dir or self._get_cache_dir()
        self.auto_download = auto_download
        self.installed_packages = set()
        
        # Configura diretório de dados do Argos
        os.environ['ARGOS_TRANSLATE_DATA_DIR'] = self.cache_dir
        
        # Atualiza lista de pacotes instalados
        self._update_installed_packages()
        
        logger.info(f"Tradutor inicializado:")
        logger.info(f"  Cache: {self.cache_dir}")
        logger.info(f"  Pacotes instalados: {len(self.installed_packages)}")
    
    def _get_cache_dir(self) -> str:
        """Retorna o diretório de cache dos modelos."""
        if os.name == 'nt':  # Windows
            cache_dir = os.path.expandvars(r'%APPDATA%\MotherLine\translation')
        else:  # Linux/Mac
            cache_dir = os.path.expanduser('~/.cache/motherline/translation')
        
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def _update_installed_packages(self) -> None:
        """Atualiza lista de pacotes instalados."""
        try:
            argostranslate.package.update_package_index()
            installed = argostranslate.package.get_installed_packages()
            
            self.installed_packages = set()
            for package in installed:
                self.installed_packages.add(f"{package.from_code}-{package.to_code}")
                
        except Exception as e:
            logger.warning(f"Erro ao atualizar pacotes: {e}")
            self.installed_packages = set()
    
    def _ensure_translation_package(self, from_code: str, to_code: str) -> bool:
        """
        Garante que o pacote de tradução está instalado.
        
        Args:
            from_code: Código do idioma de origem
            to_code: Código do idioma de destino
            
        Returns:
            True se o pacote está disponível
        """
        package_key = f"{from_code}-{to_code}"
        
        if package_key in self.installed_packages:
            return True
        
        if not self.auto_download:
            logger.warning(f"Pacote {package_key} não instalado e download automático desabilitado")
            return False
        
        try:
            logger.info(f"Baixando pacote de tradução {from_code} -> {to_code}...")
            
            # Busca pacote disponível
            available_packages = argostranslate.package.get_available_packages()
            target_package = None
            
            for package in available_packages:
                if package.from_code == from_code and package.to_code == to_code:
                    target_package = package
                    break
            
            if target_package is None:
                logger.error(f"Pacote {package_key} não encontrado")
                return False
            
            # Baixa e instala o pacote
            argostranslate.package.install_from_path(target_package.download())
            self.installed_packages.add(package_key)
            
            logger.info(f"Pacote {package_key} instalado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao instalar pacote {package_key}: {e}")
            return False
    
    def translate_text(self, 
                      text: str, 
                      source_lang: str, 
                      target_lang: str) -> TranslationResult:
        """
        Traduz texto entre idiomas.
        
        Args:
            text: Texto para traduzir
            source_lang: Código do idioma de origem
            target_lang: Código do idioma de destino
            
        Returns:
            Resultado da tradução
        """
        if not text or not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.0
            )
        
        # Normaliza códigos de idioma
        source_lang = source_lang.lower()
        target_lang = target_lang.lower()
        
        # Se idiomas são iguais, retorna original
        if source_lang == target_lang:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=1.0
            )
        
        # Garante que o pacote está instalado
        if not self._ensure_translation_package(source_lang, target_lang):
            # Tenta tradução via inglês como idioma intermediário
            if source_lang != 'en' and target_lang != 'en':
                return self._translate_via_english(text, source_lang, target_lang)
            else:
                # Se não conseguir, retorna original
                logger.warning(f"Tradução {source_lang} -> {target_lang} não disponível")
                return TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=0.0
                )
        
        try:
            # Executa tradução
            translated = argostranslate.translate.translate(
                text, 
                source_lang, 
                target_lang
            )
            
            return TranslationResult(
                original_text=text,
                translated_text=translated,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.8  # Confiança estimada
            )
            
        except Exception as e:
            logger.error(f"Erro na tradução: {e}")
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.0
            )
    
    def _translate_via_english(self, 
                              text: str, 
                              source_lang: str, 
                              target_lang: str) -> TranslationResult:
        """
        Traduz usando inglês como idioma intermediário.
        
        Args:
            text: Texto para traduzir
            source_lang: Idioma de origem
            target_lang: Idioma de destino
            
        Returns:
            Resultado da tradução
        """
        try:
            # Traduz para inglês
            if source_lang != 'en':
                if not self._ensure_translation_package(source_lang, 'en'):
                    raise Exception(f"Pacote {source_lang} -> en não disponível")
                
                english_text = argostranslate.translate.translate(
                    text, source_lang, 'en'
                )
            else:
                english_text = text
            
            # Traduz do inglês para o idioma alvo
            if target_lang != 'en':
                if not self._ensure_translation_package('en', target_lang):
                    raise Exception(f"Pacote en -> {target_lang} não disponível")
                
                final_text = argostranslate.translate.translate(
                    english_text, 'en', target_lang
                )
            else:
                final_text = english_text
            
            return TranslationResult(
                original_text=text,
                translated_text=final_text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.6  # Confiança menor por ser tradução indireta
            )
            
        except Exception as e:
            logger.error(f"Erro na tradução via inglês: {e}")
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.0
            )
    
    def translate_segments(self, 
                          segments: List[Dict], 
                          source_lang: str, 
                          target_lang: str) -> List[TranslationResult]:
        """
        Traduz múltiplos segmentos de texto.
        
        Args:
            segments: Lista de segmentos com texto
            source_lang: Idioma de origem
            target_lang: Idioma de destino
            
        Returns:
            Lista de resultados de tradução
        """
        results = []
        
        for i, segment in enumerate(segments):
            try:
                text = segment.get('text', '')
                result = self.translate_text(text, source_lang, target_lang)
                results.append(result)
                
                if (i + 1) % 10 == 0:  # Log progresso a cada 10 segmentos
                    logger.info(f"Traduzidos {i + 1}/{len(segments)} segmentos")
                    
            except Exception as e:
                logger.error(f"Erro ao traduzir segmento {i}: {e}")
                results.append(TranslationResult(
                    original_text=segment.get('text', ''),
                    translated_text=segment.get('text', ''),
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=0.0
                ))
        
        return results
    
    def get_available_languages(self) -> List[str]:
        """
        Retorna lista de idiomas disponíveis.
        
        Returns:
            Lista de códigos de idioma
        """
        return list(self.LANGUAGE_CODES.keys())
    
    def get_installed_packages(self) -> List[str]:
        """
        Retorna lista de pacotes de tradução instalados.
        
        Returns:
            Lista de pares de idiomas (from-to)
        """
        return list(self.installed_packages)
    
    def install_language_pack(self, from_code: str, to_code: str) -> bool:
        """
        Instala pacote de tradução específico.
        
        Args:
            from_code: Código do idioma de origem
            to_code: Código do idioma de destino
            
        Returns:
            True se instalado com sucesso
        """
        return self._ensure_translation_package(from_code, to_code)
    
    def get_language_name(self, code: str) -> str:
        """
        Retorna nome do idioma baseado no código.
        
        Args:
            code: Código do idioma
            
        Returns:
            Nome do idioma
        """
        return self.LANGUAGE_CODES.get(code.lower(), code.upper()) 