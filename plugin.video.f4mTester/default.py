# -*- coding: utf-8 -*-
# InfinityTester v2.0.1
# Player profissional para streams IPTV - PLUGN Team
# Codigo limpo, transparente e de codigo aberto

from __future__ import unicode_literals
import sys
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    from urllib.parse import urlencode, parse_qsl, unquote_plus
except ImportError:
    from urlparse import parse_qsl
    from urllib import urlencode, unquote_plus

# ============================================================
# CONSTANTES
# ============================================================
ADDON      = xbmcaddon.Addon()
ADDON_ID   = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VER  = ADDON.getAddonInfo('version')
ADDON_PATH = ADDON.getAddonInfo('path')
HANDLE     = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL   = sys.argv[0] if len(sys.argv) > 0 else ''

# ============================================================
# LOG
# ============================================================
def log(msg, level=xbmc.LOGINFO):
    xbmc.log('[InfinityTester] {}'.format(msg), level)

# ============================================================
# DETECCAO DE TIPO DE STREAM
# ============================================================
def detect_stream_type(url):
    """Detecta o tipo de stream pela URL."""
    url_lower = url.lower().split('?')[0]
    if url_lower.endswith('.m3u8') or '/hls/' in url_lower or 'manifest/hls' in url_lower:
        return 'hls'
    if url_lower.endswith('.mpd') or '/dash/' in url_lower or 'manifest/dash' in url_lower:
        return 'dash'
    if url_lower.endswith('.mp4') or url_lower.endswith('.mkv') or \
       url_lower.endswith('.avi') or url_lower.endswith('.mov'):
        return 'direct'
    if url_lower.endswith('.ts') or url_lower.endswith('.m2ts'):
        return 'ts'
    # Tenta detectar por conteudo da URL
    if 'iptv' in url_lower or 'live' in url_lower or 'stream' in url_lower:
        return 'live'
    return 'direct'

# ============================================================
# VERIFICACAO DE INPUTSTREAM
# ============================================================
def is_addon_enabled(addon_id):
    """Verifica se um addon esta instalado e habilitado."""
    try:
        xbmcaddon.Addon(addon_id)
        return True
    except Exception:
        return False

def has_ffmpegdirect():
    return is_addon_enabled('inputstream.ffmpegdirect')

def has_adaptive():
    return is_addon_enabled('inputstream.adaptive')

# ============================================================
# CONSTRUTOR DE LISTITEM
# ============================================================
def build_listitem(url, title='Stream', stream_type=None):
    """
    Constroi um ListItem otimizado para o tipo de stream.
    Tenta o melhor player disponivel com fallback automatico.
    """
    if stream_type is None:
        stream_type = detect_stream_type(url)

    li = xbmcgui.ListItem(title, path=url)
    li.setInfo('video', {'title': title, 'mediatype': 'video'})

    log('Reproduzindo: {} | Tipo: {} | URL: {}'.format(title, stream_type, url))

    # --- HLS ---
    if stream_type == 'hls':
        if has_ffmpegdirect():
            log('Usando inputstream.ffmpegdirect para HLS')
            li.setProperty('inputstream', 'inputstream.ffmpegdirect')
            li.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
            li.setProperty('inputstream.ffmpegdirect.open_mode', 'ffmpeg')
            li.setMimeType('application/x-mpegURL')
            li.setContentLookup(False)
        elif has_adaptive():
            log('Usando inputstream.adaptive para HLS')
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'hls')
            li.setMimeType('application/x-mpegURL')
            li.setContentLookup(False)
        else:
            log('Usando player nativo para HLS')
            li.setMimeType('application/x-mpegURL')
            li.setContentLookup(False)

    # --- DASH ---
    elif stream_type == 'dash':
        if has_adaptive():
            log('Usando inputstream.adaptive para DASH')
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setMimeType('application/dash+xml')
            li.setContentLookup(False)
        elif has_ffmpegdirect():
            log('Usando inputstream.ffmpegdirect para DASH')
            li.setProperty('inputstream', 'inputstream.ffmpegdirect')
            li.setProperty('inputstream.ffmpegdirect.manifest_type', 'mpd')
            li.setMimeType('application/dash+xml')
            li.setContentLookup(False)
        else:
            log('Sem inputstream para DASH - tentando player nativo')
            li.setMimeType('application/dash+xml')
            li.setContentLookup(False)

    # --- TS / LIVE ---
    elif stream_type in ('ts', 'live'):
        if has_ffmpegdirect():
            log('Usando inputstream.ffmpegdirect para TS/Live')
            li.setProperty('inputstream', 'inputstream.ffmpegdirect')
            li.setProperty('inputstream.ffmpegdirect.open_mode', 'ffmpeg')
            li.setMimeType('video/mp2t')
            li.setContentLookup(False)
        else:
            log('Usando player nativo para TS/Live')
            li.setMimeType('video/mp2t')
            li.setContentLookup(False)

    # --- DIRETO (MP4, MKV, etc.) ---
    else:
        log('Usando player nativo direto')
        li.setContentLookup(False)

    return li

# ============================================================
# REPRODUCAO PRINCIPAL
# ============================================================
def play_stream(url, title='Stream', stream_type=None):
    """
    Reproduz um stream com o melhor player disponivel.
    Funciona tanto quando chamado diretamente (HANDLE=-1)
    quanto quando chamado via plugin:// de outro addon (HANDLE>=0).
    """
    if not url:
        xbmcgui.Dialog().notification(
            'InfinityTester',
            'URL invalida ou vazia.',
            xbmcgui.NOTIFICATION_ERROR, 4000
        )
        return

    url = unquote_plus(url)

    # Se stream_type nao foi passado ou e 'direct', detecta pela URL
    if not stream_type or stream_type == 'direct':
        stream_type = detect_stream_type(url)

    li = build_listitem(url, title, stream_type)

    log('HANDLE={} | Iniciando reproducao'.format(HANDLE))

    # Sempre usa xbmc.Player().play() para garantir compatibilidade
    # quando chamado via plugin:// de outro addon
    xbmc.Player().play(url, li)

# ============================================================
# MENU PRINCIPAL
# ============================================================
def show_main_menu():
    """Exibe o menu principal do InfinityTester."""
    xbmcplugin.setPluginCategory(HANDLE, 'InfinityTester')
    xbmcplugin.setContent(HANDLE, 'videos')

    items = [
        {
            'label': '[COLOR cyan]Testar URL de Stream[/COLOR]',
            'action': 'test_url',
            'icon': 'DefaultVideo.png',
            'desc': 'Digite uma URL para testar a reproducao'
        },
        {
            'label': '[COLOR yellow]Informacoes do Player[/COLOR]',
            'action': 'player_info',
            'icon': 'DefaultAddonInfo.png',
            'desc': 'Versao e capacidades do InfinityTester'
        },
    ]

    for item in items:
        li = xbmcgui.ListItem(item['label'])
        li.setInfo('video', {'title': item['label'], 'plot': item['desc']})
        li.setArt({'icon': item['icon'], 'thumb': item['icon']})
        url = '{}?action={}'.format(BASE_URL, item['action'])
        xbmcplugin.addDirectoryItem(HANDLE, url, li, True)

    xbmcplugin.endOfDirectory(HANDLE)

# ============================================================
# TESTAR URL
# ============================================================
def test_url_dialog():
    """Abre dialogo para o usuario digitar uma URL e testar."""
    kb = xbmc.Keyboard('', 'Digite a URL do stream para testar')
    kb.doModal()
    if not kb.isConfirmed():
        return
    url = kb.getText().strip()
    if not url:
        xbmcgui.Dialog().notification(
            'InfinityTester', 'URL vazia.', xbmcgui.NOTIFICATION_WARNING, 3000
        )
        return

    stream_type = detect_stream_type(url)
    log('Testando URL: {} | Tipo detectado: {}'.format(url, stream_type))

    xbmcgui.Dialog().notification(
        'InfinityTester',
        'Iniciando: {} ({})'.format(url[:40] + '...' if len(url) > 40 else url, stream_type.upper()),
        xbmcgui.NOTIFICATION_INFO, 3000
    )

    li = build_listitem(url, 'Teste InfinityTester', stream_type)
    xbmc.Player().play(url, li)

# ============================================================
# INFORMACOES DO PLAYER
# ============================================================
def show_player_info():
    """Exibe informacoes sobre o player e capacidades."""
    ffmpeg   = 'Instalado' if has_ffmpegdirect() else 'NAO instalado'
    adaptive = 'Instalado' if has_adaptive() else 'NAO instalado'

    msg = (
        'InfinityTester v{}\n\n'
        'inputstream.ffmpegdirect: {}\n'
        'inputstream.adaptive: {}\n\n'
        'Formatos suportados:\n'
        '  HLS (.m3u8)\n'
        '  DASH (.mpd)\n'
        '  MP4, MKV, AVI\n'
        '  TS / IPTV Live\n\n'
        'Player: Fallback automatico\n'
        '(ffmpegdirect > adaptive > nativo)'
    ).format(ADDON_VER, ffmpeg, adaptive)

    xbmcgui.Dialog().ok('[COLOR blue]Infinity[/COLOR][COLOR white]Tester[/COLOR]', msg)

# ============================================================
# PARAMETROS
# ============================================================
def get_params():
    try:
        params = dict(parse_qsl(sys.argv[2][1:]))
    except Exception:
        params = {}
    return params

# ============================================================
# ROUTER
# ============================================================
def router(params):
    action = params.get('action', '')

    if action == 'play':
        url         = params.get('url', '')
        title       = params.get('title', 'Stream')
        stream_type = params.get('stream_type', None)
        play_stream(url, title, stream_type)

    elif action == 'test_url':
        test_url_dialog()

    elif action == 'player_info':
        show_player_info()

    else:
        show_main_menu()

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == '__main__':
    params = get_params()
    router(params)
