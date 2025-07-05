#!/usr/bin/env python3
"""
Interface de linha de comando para o NGMotherLine
"""

import sys
import os
import logging
from typing import Optional, List
from pathlib import Path
import click

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ..core.pipeline import MotherLinePipeline, PipelineConfig

@click.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option('--output-dir', '-o', 
              help='Diretório de saída (padrão: mesmo diretório do arquivo de entrada)')
@click.option('--mode', '-m', 
              type=click.Choice(['fast', 'accurate', 'premium']), 
              default='fast',
              help='Modo de processamento (padrão: fast)')
@click.option('--source-lang', '-s', 
              default='auto',
              help='Idioma do áudio (padrão: auto)')
@click.option('--target-lang', '-t', 
              help='Idioma para tradução (opcional)')
@click.option('--format', '-f', 
              'output_formats',
              multiple=True,
              type=click.Choice(['srt', 'vtt', 'ass']),
              default=['srt'],
              help='Formatos de saída (padrão: srt)')
@click.option('--embed', 
              is_flag=True,
              help='Embedar legendas no vídeo')
@click.option('--bilingual', 
              is_flag=True,
              help='Gerar legendas bilíngues')
@click.option('--multilingual', 
              is_flag=True,
              help='Detecção automática de múltiplos idiomas')
@click.option('--preserve-languages', 
              is_flag=True,
              help='Preservar idiomas originais nas legendas')
@click.option('--language-labels', 
              is_flag=True,
              help='Adicionar rótulos de idioma nas legendas')
@click.option('--vad-method', 
              type=click.Choice(['silero', 'webrtc', 'fixed']),
              default='silero',
              help='Método de detecção de voz (padrão: silero)')
@click.option('--device', 
              type=click.Choice(['auto', 'cpu', 'cuda']),
              default='auto',
              help='Dispositivo para processamento (padrão: auto)')
@click.option('--threads', 
              type=int,
              help='Número de threads CPU (padrão: auto)')
@click.option('--verbose', '-v', 
              is_flag=True,
              help='Saída detalhada')
@click.option('--quiet', '-q', 
              is_flag=True,
              help='Saída silenciosa')
@click.option('--info', 
              is_flag=True,
              help='Mostrar informações do sistema e sair')
def main(input_file: Optional[str],
         output_dir: Optional[str],
         mode: str,
         source_lang: str,
         target_lang: Optional[str],
         output_formats: List[str],
         embed: bool,
         bilingual: bool,
         multilingual: bool,
         preserve_languages: bool,
         language_labels: bool,
         vad_method: str,
         device: str,
         threads: Optional[int],
         verbose: bool,
         quiet: bool,
         info: bool):
    """
    NGMotherLine - Engine de geração de legendas any-to-any
    
    Gera legendas a partir de arquivos de áudio/vídeo com suporte a tradução
    e detecção automática de múltiplos idiomas.
    
    ARQUIVO: Caminho para o arquivo de áudio/vídeo
    
    \b
    Exemplos:
    
    \b
    # Processamento básico
    motherline video.mp4
    
    \b
    # Detecção automática de múltiplos idiomas
    motherline video.mp4 --multilingual
    
    \b
    # Preservar idiomas originais + traduzir
    motherline video.mp4 --multilingual --target-lang en --preserve-languages
    
    \b
    # Legendas com rótulos de idioma
    motherline video.mp4 --multilingual --language-labels
    
    \b
    # Com tradução para inglês
    motherline video.mp4 --target-lang en
    
    \b
    # Modo preciso com múltiplos formatos
    motherline video.mp4 --mode accurate --format srt --format vtt
    
    \b
    # Legendas bilíngues embedadas no vídeo
    motherline video.mp4 --target-lang en --bilingual --embed
    """
    
    # Configura logging
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # Mostra informações do sistema
    if info:
        show_system_info()
        return
    
    # Valida se arquivo foi fornecido
    if not input_file:
        click.echo("Erro: Arquivo de entrada é obrigatório", err=True)
        click.echo("Use --help para ver opções disponíveis")
        click.echo("\n💡 Exemplos:")
        click.echo("  python main.py video.mp4")
        click.echo("  python main.py video.mp4 --multilingual")
        click.echo("  python main.py video.mp4 --target-lang en")
        sys.exit(1)
    
    # Valida argumentos
    if bilingual and not target_lang:
        click.echo("Erro: --bilingual requer --target-lang", err=True)
        sys.exit(1)
    
    if preserve_languages and not multilingual:
        click.echo("Erro: --preserve-languages requer --multilingual", err=True)
        sys.exit(1)
    
    if language_labels and not multilingual:
        click.echo("Erro: --language-labels requer --multilingual", err=True)
        sys.exit(1)
    
    if not output_formats:
        output_formats = ['srt']
    
    # Configuração automática para modo multilíngue
    if multilingual:
        if source_lang == 'auto':
            source_lang = 'multilingual'
        click.echo("🌐 Modo multilíngue ativado - detectando idiomas automaticamente")
    
    # Cria configuração do pipeline
    config = PipelineConfig(
        mode=mode,
        source_language=source_lang,
        target_language=target_lang,
        output_formats=list(output_formats),
        embed_subtitles=embed,
        bilingual_subtitles=bilingual,
        multilingual_detection=multilingual,
        preserve_original_languages=preserve_languages,
        add_language_labels=language_labels,
        vad_method=vad_method,
        device=device,
        cpu_threads=threads
    )
    
    try:
        # Inicializa pipeline
        click.echo("🚀 Inicializando NGMotherLine...")
        pipeline = MotherLinePipeline(config)
        
        # Processa arquivo
        click.echo(f"📁 Processando: {input_file}")
        result = pipeline.process_file(input_file, output_dir)
        
        # Mostra resultados
        if result.success:
            click.echo(f"✅ Processamento concluído em {result.processing_time:.2f}s")
            click.echo(f"📊 Áudio: {result.audio_duration:.2f}s | Segmentos: {result.segments_count}")
            
            # Mostra informações de idiomas
            if result.detected_language:
                click.echo(f"🌐 Idioma detectado: {result.detected_language}")
            
            if hasattr(result, 'languages_found') and result.languages_found:
                if len(result.languages_found) > 1:
                    click.echo(f"🗣️  Idiomas encontrados: {', '.join(result.languages_found)}")
                    click.echo("🎯 Conteúdo multilíngue detectado!")
            
            click.echo(f"📄 Arquivos gerados: {len(result.output_files)}")
            
            for file_path in result.output_files:
                click.echo(f"  📄 {file_path}")
            
            # Mostra estatísticas detalhadas se verbose
            if verbose and result.metadata:
                click.echo("\n📈 Estatísticas de processamento:")
                stats = result.metadata.get('processing_stats', {})
                for step, time_taken in stats.items():
                    click.echo(f"  {step}: {time_taken:.2f}s")
        
        else:
            click.echo(f"❌ Erro no processamento: {result.error_message}", err=True)
            sys.exit(1)
    
    except KeyboardInterrupt:
        click.echo("\n⏹️  Processamento interrompido pelo usuário")
        sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Erro inesperado: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Limpa recursos
        if 'pipeline' in locals():
            pipeline.cleanup()


@click.command()
@click.option('--list-models', is_flag=True, help='Lista modelos disponíveis')
@click.option('--list-languages', is_flag=True, help='Lista idiomas suportados')
@click.option('--system-info', is_flag=True, help='Mostra informações do sistema')
def info(list_models: bool, list_languages: bool, system_info: bool):
    """Mostra informações sobre o NGMotherLine."""
    
    if list_models:
        click.echo("🤖 Modelos disponíveis:")
        from ..asr.whisper_engine import WhisperEngine
        models = WhisperEngine.get_available_models()
        for mode, config in models.items():
            click.echo(f"  {mode}:")
            click.echo(f"    Modelo: {config['model_size']}")
            click.echo(f"    Descrição: {config['description']}")
            click.echo(f"    WER esperado: {config['expected_wer']}%")
            click.echo(f"    Velocidade: {config['speed_factor']}x")
            click.echo(f"    Suporte multilíngue: {'✅' if config['language_detection'] else '❌'}")
            click.echo()
    
    if list_languages:
        click.echo("🌐 Idiomas suportados:")
        click.echo("\n📝 Para transcrição (Whisper):")
        from ..asr.whisper_engine import WhisperEngine
        whisper_langs = WhisperEngine.get_supported_languages()
        for i, lang in enumerate(whisper_langs):
            if i % 10 == 0:
                click.echo()
            click.echo(f"{lang:4}", nl=False)
        
        click.echo("\n\n🌐 Para tradução (Argos):")
        from ..translation.translator import MotherLineTranslator
        translator = MotherLineTranslator()
        translation_langs = translator.get_available_languages()
        
        for lang_code in sorted(translation_langs):
            lang_name = translator.get_language_name(lang_code)
            click.echo(f"  {lang_code}: {lang_name}")
    
    if system_info:
        show_system_info()


def show_system_info():
    """Mostra informações detalhadas do sistema."""
    import platform
    import psutil
    
    click.echo("SISTEMA - Informações do sistema:")
    click.echo(f"  SO: {platform.system()} {platform.release()}")
    click.echo(f"  CPU: {psutil.cpu_count(logical=False)} núcleos físicos, {psutil.cpu_count(logical=True)} lógicos")
    click.echo(f"  RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    
    # Verifica GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            click.echo(f"  GPU: {gpu_count} dispositivo(s) CUDA detectado(s)")
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                click.echo(f"    GPU {i}: {gpu_name}")
        else:
            click.echo("  GPU: Nenhum dispositivo CUDA detectado")
    except ImportError:
        click.echo("  GPU: PyTorch não instalado")
    
    # Verifica FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            click.echo(f"  FFmpeg: {version_line}")
        else:
            click.echo("  FFmpeg: Não encontrado")
    except FileNotFoundError:
        click.echo("  FFmpeg: Não encontrado")
    
    # Verifica recursos multilíngue
    click.echo("\n🌐 Recursos multilíngue:")
    try:
        from ..asr.whisper_engine import WhisperEngine
        engine = WhisperEngine()
        info = engine.get_model_info()
        click.echo(f"  Suporte multilíngue: {'✅' if info['multilingual_support'] else '❌'}")
        click.echo(f"  Detecção automática de idiomas: ✅")
        click.echo(f"  Threshold de confiança: {info['language_detection_threshold']}")
    except Exception as e:
        click.echo(f"  Erro ao verificar recursos: {e}")


@click.group()
@click.version_option(version='0.1.0', prog_name='NGMotherLine')
def cli():
    """NGMotherLine - Engine de geração de legendas any-to-any."""
    pass


# Adiciona comandos ao grupo
cli.add_command(main, name='process')
cli.add_command(info)

# Comando padrão (quando executado sem subcomando)
if __name__ == '__main__':
    # Se não há argumentos ou o primeiro não é um subcomando, executa 'process'
    import sys
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and not sys.argv[1] in ['process', 'info']):
        # Adiciona 'process' como primeiro argumento
        sys.argv.insert(1, 'process')
    
    cli()


# Função de entrada para setuptools
def entry_point():
    """Ponto de entrada para o executável."""
    main()


if __name__ == '__main__':
    entry_point() 