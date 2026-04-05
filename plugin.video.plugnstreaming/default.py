# -*- coding: utf-8 -*-
# ============================================================
#  PLUGN STREAMING VIP - Addon Kodi
#  Versao: 2.0.0
# ============================================================
import sys
import os
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib.parse as urlparse
import urllib.request as urlrequest
import base64

ADDON      = xbmcaddon.Addon()
ADDON_ID   = ADDON.getAddonInfo('id')
ADDON_PATH = ADDON.getAddonInfo('path')
ADDON_NAME = 'PLUGN STREAMING VIP'
HANDLE     = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL   = sys.argv[0] if len(sys.argv) > 0 else ''
MEDIA_PATH = os.path.join(ADDON_PATH, 'resources', 'media')
ICON_MAIN  = os.path.join(ADDON_PATH, 'icon.png')
FANART     = os.path.join(ADDON_PATH, 'fanart.jpg')

ACCESS_PIN = '1056'

# ============================================================
# SERVIDORES - Carregados do servers.json
# ============================================================
def load_servers():
    """Carrega servidores do arquivo servers.json"""
    servers_file = os.path.join(ADDON_PATH, 'servers.json')
    try:
        with open(servers_file, 'r') as f:
            data = json.load(f)
        servers_dict = {}
        for srv in data.get('servers', []):
            sid = srv.get('id', 0)
            if sid > 0:
                servers_dict[sid] = {
                    'name': srv.get('name', f'SERVIDOR {sid}'),
                    'url': srv.get('url', ''),
                    'user': srv.get('user', ''),
                    'pass': srv.get('pass', ''),
                }
        return servers_dict if servers_dict else get_default_servers()
    except Exception as e:
        log(f'Erro ao carregar servers.json: {str(e)}')
        return get_default_servers()

def get_default_servers():
    """Retorna servidores padrão se servers.json não existir"""
    return {
        1: {'name': 'SERVIDOR 1',   'url': 'http://amsplay.com:80',    'user': '898570',   'pass': 'MxCkDv'},
        2: {'name': 'SERVIDOR 2',   'url': 'http://amsplay.com:80', 'user': '724792', 'pass': '4WHKUG'},
        3: {'name': 'SERVIDOR 3','url': 'http://amsplay.com:80',   'user': '766763','pass': 'ScaHWe'},
        4: {'name': 'SERVIDOR 4','url': 'http://amsplay.com:80',   'user': '9543894325','pass': 'secure'},
        5: {'name': 'SERVIDOR 5','url': 'http://amsplay.com:80',   'user': '251265','pass': '7WCG69'},
    }

SERVERS = load_servers()

# ============================================================
# HELPERS
# ============================================================
def build_url(params):
    return BASE_URL + '?' + urlparse.urlencode(params)

def get_params():
    if len(sys.argv) > 2 and sys.argv[2]:
        return dict(urlparse.parse_qsl(sys.argv[2][1:]))
    return {}

def icon(name):
    p = os.path.join(MEDIA_PATH, name + '.png')
    return p if os.path.exists(p) else ICON_MAIN

def get_active_server_num():
    try:
        n = int(ADDON.getSetting('active_server') or '1')
        if n in SERVERS:
            return n
    except Exception:
        pass
    return 1

def get_active_server():
    return SERVERS[get_active_server_num()]

def set_active_server(num):
    ADDON.setSetting('active_server', str(num))

def add_dir(label, url, thumb=None, fanart=None, info=None):
    """Adiciona item de diretorio (pasta)."""
    li = xbmcgui.ListItem(label)
    li.setArt({
        'icon':   thumb or ICON_MAIN,
        'thumb':  thumb or ICON_MAIN,
        'poster': thumb or ICON_MAIN,
        'fanart': fanart or FANART,
    })
    if info:
        li.setInfo('video', info)
    xbmcplugin.addDirectoryItem(HANDLE, url, li, True)

def add_play(label, url, thumb=None, info=None, is_live=False, poster=None, fanart_img=None):
    """Adiciona item reproduzivel com informações detalhadas."""
    li = xbmcgui.ListItem(label)
    
    # Configurar arte com poster se disponível
    art = {
        'icon':   thumb or ICON_MAIN,
        'thumb':  thumb or ICON_MAIN,
        'poster': poster or thumb or ICON_MAIN,
        'fanart': fanart_img or FANART,
    }
    li.setArt(art)
    
    if info:
        li.setInfo('video', info)
    
    li.setProperty('IsPlayable', 'true')
    
    # Para streams ao vivo: desabilita timeout e marca como live
    if is_live:
        li.setProperty('inputstream.adaptive.manifest_type', 'hls')
        li.setProperty('IsLive', 'true')
        li.setMimeType('video/ts')
        li.setContentLookup(False)
    
    xbmcplugin.addDirectoryItem(HANDLE, url, li, False)

def end_dir(sort=False):
    if sort:
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE)

def notify(msg, icon_type=xbmcgui.NOTIFICATION_INFO, time=3000):
    xbmcgui.Dialog().notification(ADDON_NAME, msg, icon_type, time)

def log(msg):
    xbmc.log('[PLUGN] ' + str(msg), xbmc.LOGINFO)

# ============================================================
# API XTREAM - usa urllib (sem dependencia externa)
# ============================================================
def api_call(action, extra=''):
    srv = get_active_server()
    url = '{}/player_api.php?username={}&password={}&action={}{}'.format(
        srv['url'].rstrip('/'), srv['user'], srv['pass'], action, extra
    )
    try:
        req = urlrequest.Request(url, headers={'User-Agent': 'Kodi/19.0'})
        with urlrequest.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            return json.loads(raw)
    except Exception as e:
        log('API error [{}]: {}'.format(action, str(e)))
        return None

def make_stream_url(stream_id, stype='live', ext='ts'):
    srv = get_active_server()
    base = srv['url'].rstrip('/')
    u = srv['user']
    p = srv['pass']
    if stype == 'live':
        return '{}/{}/{}/{}.{}'.format(base, u, p, stream_id, ext)
    elif stype == 'movie':
        return '{}/movie/{}/{}/{}.{}'.format(base, u, p, stream_id, ext)
    elif stype == 'series':
        return '{}/series/{}/{}/{}.{}'.format(base, u, p, stream_id, ext)
    return ''

# ============================================================
# AUTENTICACAO - PIN UNICO
# ============================================================
def check_pin_done():
    return ADDON.getSetting('pin_ok') == '1'

def ask_pin():
    dlg = xbmcgui.Dialog()
    dlg.ok(
        '[B][COLOR FF00AAFF]PLUGN STREAMING VIP[/COLOR][/B]',
        '[COLOR FFCCCCCC]Bem-vindo! Digite o PIN de acesso para continuar.[/COLOR]'
    )
    pin = dlg.input('[B]PIN de Acesso[/B]', type=xbmcgui.INPUT_NUMERIC)
    if pin == ACCESS_PIN:
        ADDON.setSetting('pin_ok', '1')
        notify('[COLOR FF00CC44]Acesso liberado! Bem-vindo![/COLOR]')
        return True
    elif pin:
        dlg.ok('[COLOR FFCC0000][B]ACESSO NEGADO[/B][/COLOR]',
               '[COLOR FFCC0000]PIN incorreto. Tente novamente.[/COLOR]')
    return False

def ensure_auth():
    if check_pin_done():
        return True
    return ask_pin()

# ============================================================
# MENU PRINCIPAL
# ============================================================
def show_main_menu():
    xbmcplugin.setPluginCategory(HANDLE, ADDON_NAME)
    xbmcplugin.setContent(HANDLE, 'files')

    srv = get_active_server()

    # TROCAR SERVIDOR
    li_srv = xbmcgui.ListItem(
        '[COLOR FFFFD700][B]>> TROCAR SERVIDOR  |  ATIVO: {}[/B][/COLOR]'.format(srv['name'])
    )
    li_srv.setArt({'icon': icon('iconserver'), 'thumb': icon('iconserver'), 'fanart': FANART})
    li_srv.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_url({'action': 'change_server'}),
        li_srv,
        False
    )

    # TROCAR PLAYER
    player = get_player_type()
    player_label = 'NATIVO' if player == 'nativo' else 'F4MTESTER'
    li_player = xbmcgui.ListItem(
        '[COLOR FF00CCFF][B]>> TIPO DE PLAYER  |  ATIVO: {}[/B][/COLOR]'.format(player_label)
    )
    li_player.setArt({'icon': icon('iconserver'), 'thumb': icon('iconserver'), 'fanart': FANART})
    li_player.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_url({'action': 'change_player'}),
        li_player,
        False
    )

    # MENU PRINCIPAL
    items = [
        ('[COLOR FF00AAFF][B]  TV AO VIVO[/B][/COLOR]',         'live_cats',   'iconlive'),
        ('[COLOR FFFF6B00][B]  FILMES[/B][/COLOR]',              'vod_cats',    'iconmovies'),
        ('[COLOR FF00CC44][B]  SERIES[/B][/COLOR]',              'series_cats', 'icontvseries'),
        ('[COLOR FFCC44FF][B]  GUIA DE PROGRAMACAO[/B][/COLOR]', 'epg_guide',   'iconguide'),
        ('[COLOR FFFF9900][B]  BUSCAR[/B][/COLOR]',              'search',      'iconsearch'),
        ('[COLOR FF00CCFF][B]  TESTE DE VELOCIDADE[/B][/COLOR]', 'speedtest',   'iconspeed'),
        ('[COLOR FFCCCCCC][B]  MINHA CONTA[/B][/COLOR]',         'account',     'iconaccount'),
        ('[COLOR FFFF4444][B]  LIMPAR CACHE[/B][/COLOR]',        'clear_cache', 'iconcache'),
    ]

    for label, action, ico in items:
        add_dir(label, build_url({'action': action}), thumb=icon(ico))

    end_dir()

# ============================================================
# TROCAR PLAYER (NATIVO / F4MTESTER)
# ============================================================
def get_player_type():
    """Retorna tipo de player salvo (nativo ou f4mtester)"""
    val = ADDON.getSetting('player_type') or 'nativo'
    return val if val in ['nativo', 'f4mtester'] else 'nativo'

def set_player_type(ptype):
    """Salva tipo de player"""
    ADDON.setSetting('player_type', ptype)

def change_player():
    """Menu para trocar tipo de player"""
    dlg = xbmcgui.Dialog()
    current = get_player_type()
    opts = [
        '[B]PLAYER NATIVO[/B]' + ('  [COLOR FFFFD700]<< ATIVO[/COLOR]' if current == 'nativo' else ''),
        '[B]F4MTESTER[/B]' + ('  [COLOR FFFFD700]<< ATIVO[/COLOR]' if current == 'f4mtester' else ''),
    ]
    sel = dlg.select('[B]Tipo de Player[/B]', opts)
    if sel == 0:
        set_player_type('nativo')
        notify('[COLOR FF00CC44]Player Nativo ativado![/COLOR]')
    elif sel == 1:
        set_player_type('f4mtester')
        notify('[COLOR FF00CC44]F4MTester ativado![/COLOR]')
    xbmc.executebuiltin('Container.Refresh')

# ============================================================
# TROCAR SERVIDOR
# ============================================================
def change_server():
    dlg = xbmcgui.Dialog()
    current = get_active_server_num()
    opts = []
    for n, s in SERVERS.items():
        mark = '  [COLOR FFFFD700][B]<< ATIVO[/B][/COLOR]' if n == current else ''
        opts.append('[B]{}[/B]{}'.format(s['name'], mark))
    sel = dlg.select('[B]Selecionar Servidor[/B]', opts)
    if sel >= 0:
        new_num = sel + 1
        set_active_server(new_num)
        notify('[COLOR FF00CC44]Servidor: {}[/COLOR]'.format(SERVERS[new_num]['name']))
    xbmc.executebuiltin('Container.Refresh')

# ============================================================
# TV AO VIVO
# ============================================================
def show_live_cats():
    xbmcplugin.setPluginCategory(HANDLE, 'TV AO VIVO')
    xbmcplugin.setContent(HANDLE, 'files')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando categorias...')
    data = api_call('get_live_categories')
    prog.close()
    if not data:
        notify('Erro ao carregar. Verifique o servidor.', xbmcgui.NOTIFICATION_ERROR, 4000)
        end_dir()
        return
    add_dir('[COLOR FFFFD700][B]>> TODOS OS CANAIS[/B][/COLOR]',
            build_url({'action': 'live_streams', 'cat_id': '-1'}), thumb=icon('iconlive'))
    for cat in data:
        add_dir('[COLOR FF00AAFF]{}[/COLOR]'.format(cat.get('category_name', 'Sem nome')),
                build_url({'action': 'live_streams', 'cat_id': str(cat.get('category_id', ''))}),
                thumb=icon('iconlive'))
    end_dir()

def show_live_streams(cat_id):
    xbmcplugin.setPluginCategory(HANDLE, 'TV AO VIVO')
    xbmcplugin.setContent(HANDLE, 'files')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando canais...')
    if cat_id == '-1':
        data = api_call('get_live_streams')
    else:
        data = api_call('get_live_streams', '&category_id={}'.format(cat_id))
    prog.close()
    if not data:
        notify('Nenhum canal encontrado.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    for ch in data:
        sid   = str(ch.get('stream_id', ''))
        name  = ch.get('name', 'Canal')
        thumb = ch.get('stream_icon', '') or icon('iconlive')
        url   = make_stream_url(sid, 'live', 'ts')
        add_play('[COLOR FF00AAFF]{}[/COLOR]'.format(name), url, thumb=thumb,
                 info={'title': name, 'mediatype': 'video'}, is_live=True)
    end_dir()

# ============================================================
# FILMES (VOD)
# ============================================================
def show_vod_cats():
    xbmcplugin.setPluginCategory(HANDLE, 'FILMES')
    xbmcplugin.setContent(HANDLE, 'files')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando categorias...')
    data = api_call('get_vod_categories')
    prog.close()
    if not data:
        notify('Erro ao carregar. Verifique o servidor.', xbmcgui.NOTIFICATION_ERROR, 4000)
        end_dir()
        return
    add_dir('[COLOR FFFFD700][B]>> TODOS OS FILMES[/B][/COLOR]',
            build_url({'action': 'vod_streams', 'cat_id': '-1'}), thumb=icon('iconmovies'))
    for cat in data:
        add_dir('[COLOR FFFF6B00]{}[/COLOR]'.format(cat.get('category_name', 'Sem nome')),
                build_url({'action': 'vod_streams', 'cat_id': str(cat.get('category_id', ''))}),
                thumb=icon('iconmovies'))
    end_dir()

def show_vod_streams(cat_id):
    xbmcplugin.setPluginCategory(HANDLE, 'FILMES')
    xbmcplugin.setContent(HANDLE, 'movies')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando filmes...')
    if cat_id == '-1':
        data = api_call('get_vod_streams')
    else:
        data = api_call('get_vod_streams', '&category_id={}'.format(cat_id))
    prog.close()
    if not data:
        notify('Nenhum filme encontrado.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    for movie in data:
        sid   = str(movie.get('stream_id', ''))
        name  = movie.get('name', 'Filme')
        thumb = movie.get('stream_icon', '') or icon('iconmovies')
        ext   = movie.get('container_extension', 'mp4')
        year  = str(movie.get('year', ''))
        plot  = str(movie.get('plot', ''))
        rating = str(movie.get('rating', ''))
        duration = str(movie.get('duration', ''))
        url   = make_stream_url(sid, 'movie', ext)
        lbl   = '[COLOR FFFF6B00]{}[/COLOR]  [COLOR FF888888]{}[/COLOR]'.format(name, year)
        info  = {'title': name, 'plot': plot, 'mediatype': 'movie'}
        try:
            if year and year.isdigit():
                info['year'] = int(year)
        except Exception:
            pass
        try:
            if rating and rating.replace('.', '').replace(',', '').isdigit():
                info['rating'] = float(rating.replace(',', '.'))
        except Exception:
            pass
        try:
            if duration and duration.isdigit():
                info['duration'] = int(duration)
        except Exception:
            pass
        add_play(lbl, url, thumb=thumb, poster=thumb, fanart_img=FANART, info=info)
    end_dir()

# ============================================================
# SERIES
# ============================================================
def show_series_cats():
    xbmcplugin.setPluginCategory(HANDLE, 'SERIES')
    xbmcplugin.setContent(HANDLE, 'files')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando categorias...')
    data = api_call('get_series_categories')
    prog.close()
    if not data:
        notify('Erro ao carregar. Verifique o servidor.', xbmcgui.NOTIFICATION_ERROR, 4000)
        end_dir()
        return
    for cat in data:
        add_dir('[COLOR FF00CC44]{}[/COLOR]'.format(cat.get('category_name', 'Sem nome')),
                build_url({'action': 'series_list', 'cat_id': str(cat.get('category_id', ''))}),
                thumb=icon('icontvseries'))
    end_dir()

def show_series_list(cat_id):
    xbmcplugin.setPluginCategory(HANDLE, 'SERIES')
    xbmcplugin.setContent(HANDLE, 'tvshows')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando series...')
    data = api_call('get_series', '&category_id={}'.format(cat_id))
    prog.close()
    if not data:
        notify('Nenhuma serie encontrada.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    for s in data:
        sid   = str(s.get('series_id', ''))
        name  = s.get('name', 'Serie')
        thumb = s.get('cover', '') or icon('icontvseries')
        plot  = s.get('plot', '')
        info = {'title': name, 'plot': plot, 'mediatype': 'tvshow'}
        try:
            year = str(s.get('year', ''))
            if year and year.isdigit():
                info['year'] = int(year)
        except:
            pass
        add_dir('[COLOR FF00CC44]{}[/COLOR]'.format(name),
                build_url({'action': 'series_seasons', 'series_id': sid}),
                thumb=thumb, info=info)
    end_dir()

def show_series_seasons(series_id):
    xbmcplugin.setPluginCategory(HANDLE, 'TEMPORADAS')
    xbmcplugin.setContent(HANDLE, 'seasons')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando temporadas...')
    data = api_call('get_series_info', '&series_id={}'.format(series_id))
    prog.close()
    if not data or 'seasons' not in data:
        notify('Nenhuma temporada encontrada.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    for season in data.get('seasons', []):
        snum  = season.get('season_number', 1)
        name  = season.get('name', 'Temporada {}'.format(snum))
        thumb = season.get('cover', '') or icon('icontvseries')
        add_dir('[COLOR FF00CC44][B]{}[/B][/COLOR]'.format(name),
                build_url({'action': 'series_eps', 'series_id': series_id, 'season': str(snum)}),
                thumb=thumb, info={'title': name, 'season': snum, 'mediatype': 'season'})
    end_dir()

def show_series_eps(series_id, season):
    xbmcplugin.setPluginCategory(HANDLE, 'EPISODIOS')
    xbmcplugin.setContent(HANDLE, 'episodes')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando episodios...')
    data = api_call('get_series_info', '&series_id={}'.format(series_id))
    prog.close()
    if not data or 'episodes' not in data:
        notify('Nenhum episodio encontrado.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    eps = data['episodes'].get(str(season), [])
    for ep in eps:
        eid   = str(ep.get('id', ''))
        title = ep.get('title', 'Episodio')
        epnum = ep.get('episode_num', '')
        thumb = ep.get('info', {}).get('movie_image', '') or icon('icontvseries')
        ext   = ep.get('container_extension', 'mp4')
        plot  = ep.get('info', {}).get('plot', '')
        url   = make_stream_url(eid, 'series', ext)
        lbl   = '[COLOR FF00CC44][B]{}.[/B] {}[/COLOR]'.format(epnum, title)
        info  = {'title': title, 'plot': plot, 'mediatype': 'episode'}
        try:
            info['episode'] = int(epnum)
            info['season']  = int(season)
        except Exception:
            pass
        add_play(lbl, url, thumb=thumb, poster=thumb, fanart_img=FANART, info=info)
    end_dir()

# ============================================================
# GUIA DE PROGRAMACAO (EPG)
# ============================================================
def show_epg_guide():
    xbmcplugin.setPluginCategory(HANDLE, 'GUIA DE PROGRAMACAO')
    xbmcplugin.setContent(HANDLE, 'files')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando canais para o guia...')
    data = api_call('get_live_streams')
    prog.close()
    if not data:
        notify('Erro ao carregar guia.', xbmcgui.NOTIFICATION_ERROR, 4000)
        end_dir()
        return
    for ch in data[:150]:
        name  = ch.get('name', 'Canal')
        sid   = str(ch.get('stream_id', ''))
        thumb = ch.get('stream_icon', '') or icon('iconguide')
        add_dir('[COLOR FFCC44FF]{}[/COLOR]'.format(name),
                build_url({'action': 'epg_channel', 'stream_id': sid, 'name': urlparse.quote(name)}),
                thumb=thumb)
    end_dir()

def decode_epg_field(value):
    """Decodifica campo EPG que pode estar em Base64."""
    if not value:
        return ''
    try:
        decoded = base64.b64decode(value).decode('utf-8', errors='replace')
        # Verifica se o resultado parece texto legivel (nao binario)
        if decoded and all(32 <= ord(c) < 127 or ord(c) > 159 for c in decoded[:20]):
            return decoded
    except Exception:
        pass
    return value

def show_epg_channel(stream_id, name):
    name = urlparse.unquote(name)
    xbmcplugin.setPluginCategory(HANDLE, 'EPG - {}'.format(name))
    xbmcplugin.setContent(HANDLE, 'files')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Carregando programacao...')
    data = api_call('get_short_epg', '&stream_id={}&limit=30'.format(stream_id))
    prog.close()
    if not data or 'epg_listings' not in data:
        notify('Sem programacao disponivel.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    for item in data['epg_listings']:
        # Titulos e descricoes vem em Base64 na API Xtream
        title = decode_epg_field(item.get('title', ''))
        desc  = decode_epg_field(item.get('description', ''))
        start = item.get('start', '')[:16].replace('T', ' ')
        end_t = item.get('stop', '')[:16].replace('T', ' ')
        # Formatar hora de forma legivel (YYYY-MM-DD HH:MM -> HH:MM)
        try:
            start_fmt = start[11:16] if len(start) >= 16 else start
            end_fmt   = end_t[11:16] if len(end_t) >= 16 else end_t
        except Exception:
            start_fmt = start
            end_fmt   = end_t
        lbl = '[COLOR FFCC44FF][B]{}[/B][/COLOR]  [COLOR FFFFD700]{} - {}[/COLOR]'.format(
            title or 'Sem titulo', start_fmt, end_fmt
        )
        li = xbmcgui.ListItem(lbl)
        li.setArt({'icon': icon('iconguide'), 'thumb': icon('iconguide'), 'fanart': FANART})
        li.setInfo('video', {'title': title, 'plot': desc or 'Sem descricao disponivel.'})
        xbmcplugin.addDirectoryItem(HANDLE, build_url({'action': 'none'}), li, False)
    end_dir()

# ============================================================
# BUSCA
# ============================================================
def show_search():
    kb = xbmc.Keyboard('', '[B]Buscar em PLUGN STREAMING[/B]')
    kb.doModal()
    if not kb.isConfirmed():
        return
    query = kb.getText().strip()
    if not query:
        return

    xbmcplugin.setPluginCategory(HANDLE, 'BUSCA: {}'.format(query))
    xbmcplugin.setContent(HANDLE, 'files')
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Buscando...')

    results = []
    prog.update(20, 'Buscando canais...')
    live = api_call('get_live_streams') or []
    for ch in live:
        if query.lower() in ch.get('name', '').lower():
            results.append(('live', ch))

    prog.update(60, 'Buscando filmes...')
    vod = api_call('get_vod_streams') or []
    for m in vod:
        if query.lower() in m.get('name', '').lower():
            results.append(('movie', m))

    prog.update(90, 'Buscando series...')
    series = api_call('get_series') or []
    for s in series:
        if query.lower() in s.get('name', '').lower():
            results.append(('series', s))

    prog.close()

    if not results:
        notify('Nenhum resultado para: {}'.format(query), xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return

    for rtype, item in results[:200]:
        if rtype == 'live':
            sid   = str(item.get('stream_id', ''))
            name  = '[COLOR FF00AAFF][TV][/COLOR] {}'.format(item.get('name', ''))
            thumb = item.get('stream_icon', '') or icon('iconlive')
            url   = make_stream_url(sid, 'live', 'ts')
            add_play(name, url, thumb=thumb, is_live=True)
        elif rtype == 'movie':
            sid   = str(item.get('stream_id', ''))
            name  = '[COLOR FFFF6B00][FILME][/COLOR] {}'.format(item.get('name', ''))
            thumb = item.get('stream_icon', '') or icon('iconmovies')
            ext   = item.get('container_extension', 'mp4')
            url   = make_stream_url(sid, 'movie', ext)
            add_play(name, url, thumb=thumb)
        elif rtype == 'series':
            sid   = str(item.get('series_id', ''))
            name  = '[COLOR FF00CC44][SERIE][/COLOR] {}'.format(item.get('name', ''))
            thumb = item.get('cover', '') or icon('icontvseries')
            add_dir(name, build_url({'action': 'series_seasons', 'series_id': sid}), thumb=thumb)

    end_dir()

# ============================================================
# MINHA CONTA
# ============================================================
def show_account():
    srv = get_active_server()
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Verificando conta...')
    url = '{}/player_api.php?username={}&password={}'.format(
        srv['url'].rstrip('/'), srv['user'], srv['pass']
    )
    try:
        req = urlrequest.Request(url, headers={'User-Agent': 'Kodi/19.0'})
        with urlrequest.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read().decode('utf-8', errors='replace'))
        prog.close()
        ui = d.get('user_info', {})
        si = d.get('server_info', {})
        import datetime
        exp_ts = ui.get('exp_date', '')
        try:
            exp_date = datetime.datetime.fromtimestamp(int(exp_ts)).strftime('%d/%m/%Y') if exp_ts else 'N/A'
        except Exception:
            exp_date = str(exp_ts)
        msg = (
            '[COLOR FF00AAFF][B]SERVIDOR:[/B][/COLOR] {}\n'
            '[COLOR FF00AAFF][B]URL:[/B][/COLOR] {}\n\n'
            '[COLOR FFFFD700][B]USUARIO:[/B][/COLOR] {}\n'
            '[COLOR FFFFD700][B]STATUS:[/B][/COLOR] [COLOR FF00CC44]{}[/COLOR]\n'
            '[COLOR FFFFD700][B]VALIDADE:[/B][/COLOR] [COLOR FFCC0000]{}[/COLOR]\n'
            '[COLOR FFFFD700][B]CONEXOES:[/B][/COLOR] {} / {}'
        ).format(
            srv['name'], srv['url'],
            ui.get('username', srv['user']),
            ui.get('status', 'N/A'),
            exp_date,
            ui.get('active_cons', '0'),
            ui.get('max_connections', '1'),
        )
        xbmcgui.Dialog().ok('[B]MINHA CONTA[/B]', msg)
    except Exception as e:
        prog.close()
        notify('Erro ao conectar: {}'.format(str(e)[:80]), xbmcgui.NOTIFICATION_ERROR, 5000)

# ============================================================
# TESTE DE VELOCIDADE
# ============================================================
def show_speedtest():
    import time
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Testando servidores...')
    results = []
    total = len(SERVERS)
    for i, (num, srv) in enumerate(SERVERS.items()):
        if prog.iscanceled():
            break
        prog.update(int((i / total) * 100), 'Testando {}...'.format(srv['name']))
        url = '{}/player_api.php?username={}&password={}'.format(
            srv['url'].rstrip('/'), srv['user'], srv['pass']
        )
        try:
            t0 = time.time()
            req = urlrequest.Request(url, headers={'User-Agent': 'Kodi/19.0'})
            with urlrequest.urlopen(req, timeout=10) as resp:
                resp.read()
            ping = int((time.time() - t0) * 1000)
            if ping < 300:
                quality = '[COLOR FF00CC44]OTIMO[/COLOR]'
            elif ping < 700:
                quality = '[COLOR FFFF9900]BOM[/COLOR]'
            else:
                quality = '[COLOR FFCC0000]LENTO[/COLOR]'
            results.append('[B]{}[/B]: {} ms  {}'.format(srv['name'], ping, quality))
        except Exception:
            results.append('[B]{}[/B]: [COLOR FFCC0000]OFFLINE / ERRO[/COLOR]'.format(srv['name']))
    prog.close()
    xbmcgui.Dialog().ok('[B]TESTE DE VELOCIDADE[/B]', '\n'.join(results))

# ============================================================
# LIMPAR CACHE
# ============================================================
def do_clear_cache():
    notify('[COLOR FF00CC44]Cache limpo com sucesso![/COLOR]')

# ============================================================
# ROTEADOR
# ============================================================
def router(params):
    action = params.get('action', '')
    log('action={}'.format(action))

    if action == 'change_server':
        change_server()
    elif action == 'change_player':
        change_player()
    elif action == 'live_cats':
        show_live_cats()
    elif action == 'live_streams':
        show_live_streams(params.get('cat_id', '-1'))
    elif action == 'vod_cats':
        show_vod_cats()
    elif action == 'vod_streams':
        show_vod_streams(params.get('cat_id', '-1'))
    elif action == 'series_cats':
        show_series_cats()
    elif action == 'series_list':
        show_series_list(params.get('cat_id', ''))
    elif action == 'series_seasons':
        show_series_seasons(params.get('series_id', ''))
    elif action == 'series_eps':
        show_series_eps(params.get('series_id', ''), params.get('season', '1'))
    elif action == 'epg_guide':
        show_epg_guide()
    elif action == 'epg_channel':
        show_epg_channel(params.get('stream_id', ''), params.get('name', ''))
    elif action == 'search':
        show_search()
    elif action == 'account':
        show_account()
    elif action == 'speedtest':
        show_speedtest()
    elif action == 'settings':
        ADDON.openSettings()
    elif action == 'clear_cache':
        do_clear_cache()
    elif action == 'none':
        pass
    else:
        show_main_menu()

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == '__main__':
    if not ensure_auth():
        sys.exit(0)
    params = get_params()
    router(params)
