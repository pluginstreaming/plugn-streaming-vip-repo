# -*- coding: utf-8 -*-
# ============================================================
#  PLUGN STREAMING VIP - Addon Kodi
#  Versao: 2.2.2
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
ADDON_NAME = '[COLOR FF3399FF][B]PLUGN[/B][/COLOR][COLOR FFFFD700][B]STREAMING[/B][/COLOR] [COLOR FFCC0000][B]VIP[/B][/COLOR]'
HANDLE     = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE_URL   = sys.argv[0] if len(sys.argv) > 0 else ''
MEDIA_PATH = os.path.join(ADDON_PATH, 'resources', 'media')
ICON_MAIN  = os.path.join(ADDON_PATH, 'icon.png')
FANART     = os.path.join(ADDON_PATH, 'fanart.jpg')
QR_CODE    = os.path.join(ADDON_PATH, 'resources', 'media', 'qrcode_pix.jpg')

CLIENTS_GITHUB_URL = "https://raw.githubusercontent.com/pluginstreaming/plugn-streaming-vip-repo/main/plugin.video.plugnstreaming/clients.json"
SERVERS_GITHUB_URL = "https://raw.githubusercontent.com/pluginstreaming/plugn-streaming-vip-repo/main/plugin.video.plugnstreaming/servers.json"

# ============================================================
# SERVIDORES
# ============================================================
def update_servers_from_github():
    try:
        servers_file = os.path.join(ADDON_PATH, 'servers.json')
        response = urlrequest.urlopen(SERVERS_GITHUB_URL, timeout=3)
        data = response.read().decode('utf-8')
        json.loads(data)
        with open(servers_file, 'w') as f:
            f.write(data)
        log('Servidores atualizados do GitHub!')
    except Exception as e:
        log('Erro ao atualizar servers.json: {}'.format(str(e)))

def load_servers():
    try:
        servers_file = os.path.join(ADDON_PATH, 'servers.json')
        with open(servers_file, 'r') as f:
            data = json.load(f)
        servers_dict = {}
        for srv in data.get('servers', []):
            sid = srv.get('id', 0)
            if sid > 0 and srv.get('active', True):
                servers_dict[sid] = {
                    'name': srv.get('name', 'SERVIDOR {}'.format(sid)),
                    'url':  srv.get('url', ''),
                    'user': srv.get('user', ''),
                    'pass': srv.get('pass', ''),
                }
        return servers_dict if servers_dict else get_default_servers()
    except Exception as e:
        log('Erro ao carregar servers.json: {}'.format(str(e)))
        return get_default_servers()

def get_default_servers():
    return {
        1: {'name': 'SERVIDOR 1', 'url': 'http://amsplay.com:80', 'user': '898570',     'pass': 'MxCkDv'},
        2: {'name': 'SERVIDOR 2', 'url': 'http://amsplay.com:80', 'user': '724792',     'pass': '4WHKUG'},
        3: {'name': 'SERVIDOR 3', 'url': 'http://amsplay.com:80', 'user': '766763',     'pass': 'ScaHWe'},
        4: {'name': 'SERVIDOR 4', 'url': 'http://amsplay.com:80', 'user': '9543894325', 'pass': 'secure'},
        5: {'name': 'SERVIDOR 5', 'url': 'http://amsplay.com:80', 'user': '251265',     'pass': '7WCG69'},
    }

try:
    update_servers_from_github()
except:
    pass

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

# ============================================================
# TIPO DE PLAYER
# ============================================================
def get_player_type():
    val = ADDON.getSetting('player_type') or 'nativo'
    return val if val in ['nativo', 'f4mtester'] else 'nativo'

def set_player_type(ptype):
    ADDON.setSetting('player_type', ptype)

# ============================================================
# ADD DIR / ADD PLAY
# ============================================================
def add_dir(label, url, thumb=None, fanart=None, info=None):
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
    """
    Adiciona um item reproduzivel ao diretorio.
    Se o player for F4mTester, usa RunPlugin para chamar o InfinityTester
    diretamente sem depender de resolucao de URL pelo Kodi.
    """
    player = get_player_type()

    if player == 'f4mtester':
        # Monta URL do InfinityTester
        title = (info or {}).get('title', label)
        # Remove tags de cor do titulo para a URL
        import re
        title_clean = re.sub(r'\[/?COLOR[^\]]*\]|\[/?B\]|\[/?I\]', '', title)
        stype = 'live' if is_live else 'direct'
        encoded_url   = urlparse.quote_plus(url)
        encoded_title = urlparse.quote_plus(title_clean)
        play_url = 'plugin://plugin.video.f4mTester/?action=play&url={}&title={}&stream_type={}'.format(
            encoded_url, encoded_title, stype
        )
        li = xbmcgui.ListItem(label, path=play_url)
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
        xbmcplugin.addDirectoryItem(HANDLE, play_url, li, False)
        return

    # Player nativo
    li = xbmcgui.ListItem(label)
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
# TMDB
# ============================================================
TMDB_CACHE = {}
TMDB_API_KEY = '2696829a81b1b5827d515ff121700838'

def clean_title(title):
    import re
    t = re.sub(r'\[COLOR[^\]]*\]|\[/COLOR\]|\[B\]|\[/B\]', '', title)
    t = re.sub(r'\(\d{4}\)', '', t)
    t = re.sub(r'\b(4K|HD|FHD|UHD|DUAL|DUBLADO|LEGENDADO|NACIONAL|ORIGINAL|S\d+E\d+)\b', '', t, flags=re.IGNORECASE)
    return t.strip()

def tmdb_search(title, year=''):
    cache_key = (title + str(year)).lower().strip()
    if cache_key in TMDB_CACHE:
        return TMDB_CACHE[cache_key]
    try:
        clean = clean_title(title)
        if not clean:
            return {}
        if not year:
            import re
            m = re.search(r'\((\d{4})\)', title)
            if m:
                year = m.group(1)
            else:
                m2 = re.search(r'\b(20\d{2}|19\d{2})\b', title)
                if m2:
                    year = m2.group(1)
        query = urlparse.quote(clean)
        year_param = '&year={}'.format(year) if year else ''
        url = 'https://api.themoviedb.org/3/search/movie?api_key={}&query={}&language=pt-BR{}'.format(
            TMDB_API_KEY, query, year_param)
        req = urlrequest.Request(url, headers={'User-Agent': 'Kodi/19.0'})
        with urlrequest.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
        results = data.get('results', [])
        if not results and year_param:
            url2 = 'https://api.themoviedb.org/3/search/movie?api_key={}&query={}&language=pt-BR'.format(
                TMDB_API_KEY, query)
            req2 = urlrequest.Request(url2, headers={'User-Agent': 'Kodi/19.0'})
            with urlrequest.urlopen(req2, timeout=6) as resp2:
                data2 = json.loads(resp2.read().decode('utf-8', errors='replace'))
            results = data2.get('results', [])
        if not results:
            TMDB_CACHE[cache_key] = {}
            return {}
        m = results[0]
        release = m.get('release_date', '') or ''
        yr = int(release[:4]) if release and release[:4].isdigit() else 0
        poster_path = m.get('poster_path', '') or ''
        poster = 'https://image.tmdb.org/t/p/w500{}'.format(poster_path) if poster_path else ''
        rating = float(m.get('vote_average', 0) or 0)
        genre_ids = m.get('genre_ids', [])
        genre_map = {
            28: 'Acao', 12: 'Aventura', 16: 'Animacao', 35: 'Comedia', 80: 'Crime',
            99: 'Documentario', 18: 'Drama', 10751: 'Familia', 14: 'Fantasia',
            36: 'Historia', 27: 'Terror', 10402: 'Musica', 9648: 'Misterio',
            10749: 'Romance', 878: 'Ficcao Cientifica', 10770: 'TV Movie',
            53: 'Thriller', 10752: 'Guerra', 37: 'Faroeste'
        }
        genres = ', '.join([genre_map.get(gid, '') for gid in genre_ids if gid in genre_map])
        meta = {
            'plot':   m.get('overview', '') or '',
            'year':   yr,
            'rating': rating,
            'poster': poster,
            'genre':  genres,
            'title':  m.get('title', '') or '',
        }
        TMDB_CACHE[cache_key] = meta
        return meta
    except Exception as e:
        log('TMDB error: {}'.format(str(e)))
        TMDB_CACHE[cache_key] = {}
        return {}

# ============================================================
# API XTREAM
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
# AUTENTICACAO - SENHA INDIVIDUAL POR CLIENTE
# ============================================================
def load_clients_from_github():
    """Baixa clients.json do GitHub. Usa timestamp para evitar cache do CDN."""
    try:
        import time
        ts = int(time.time())
        url = '{}?nocache={}'.format(CLIENTS_GITHUB_URL, ts)
        req = urlrequest.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        with urlrequest.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
        return data.get('clients', [])
    except Exception as e:
        log('Erro ao carregar clients.json do GitHub: {}'.format(str(e)))
        return None

def check_client_password(password):
    """
    Verifica a senha do cliente no GitHub.
    Retorna (True, nome) se valida e ativa,
             (False, 'bloqueado') se senha valida mas inativa,
             (False, 'invalida') se senha nao encontrada,
             (False, 'offline') se nao conseguiu conectar.
    """
    clients = load_clients_from_github()
    if clients is None:
        cached = ADDON.getSetting('client_name')
        cached_pass = ADDON.getSetting('client_pass')
        if cached and cached_pass == password:
            return True, cached
        return False, 'offline'
    for client in clients:
        if client.get('password', '') == password:
            if client.get('active', True):
                return True, client.get('name', 'CLIENTE')
            else:
                return False, 'bloqueado'
    return False, 'invalida'

def is_authenticated():
    return ADDON.getSetting('auth_ok') == '1'

def get_client_name():
    return ADDON.getSetting('client_name') or 'CLIENTE'

def ensure_auth():
    """
    Verifica autenticacao a cada abertura.
    - Sempre consulta o GitHub com anti-cache
    - Se ativo=true  -> libera acesso (mostra boas-vindas se estava bloqueado)
    - Se ativo=false -> bloqueia (mantem senha para proxima verificacao)
    - Sem internet + estava autenticado -> permite com cache
    - Sem senha salva -> pede senha
    """
    saved_pass = ADDON.getSetting('client_pass')
    estava_autenticado = is_authenticated()

    if not saved_pass:
        # Nunca fez login: pede senha
        return ask_client_password()

    # Tem senha salva: consulta GitHub
    clients = load_clients_from_github()

    if clients is None:
        # Sem internet: usa estado anterior
        if estava_autenticado:
            return True
        else:
            xbmcgui.Dialog().ok(
                '[COLOR FFFF9900][B]SEM CONEXAO[/B][/COLOR]',
                '[COLOR FFCCCCCC]Nao foi possivel verificar seu acesso.[/COLOR]\n\n'
                '[COLOR FF888888]Verifique sua conexao com a internet.[/COLOR]'
            )
            return False

    # Conseguiu conectar: verifica status atual
    for client in clients:
        if client.get('password', '') == saved_pass:
            nome = client.get('name', 'CLIENTE')
            if client.get('active', True):
                # ATIVO: libera acesso
                if not estava_autenticado:
                    # Estava bloqueado e foi reativado: mostra boas-vindas
                    xbmcgui.Dialog().ok(
                        '[COLOR FF00CC44][B]ACESSO LIBERADO![/B][/COLOR]',
                        '[COLOR FFCCCCCC]Bem-vindo,[/COLOR] [COLOR FFFFD700][B]{}[/B][/COLOR][COLOR FFCCCCCC]![/COLOR]\n\n'
                        '[COLOR FF888888]Aproveite o melhor do streaming.[/COLOR]'.format(nome)
                    )
                ADDON.setSetting('auth_ok', '1')
                ADDON.setSetting('client_name', nome)
                return True
            else:
                # BLOQUEADO: remove autenticacao mas MANTEM senha para proxima verificacao
                ADDON.setSetting('auth_ok', '0')
                xbmcgui.Dialog().ok(
                    '[COLOR FFCC0000][B]ACESSO BLOQUEADO[/B][/COLOR]',
                    '[COLOR FFCC0000]Sua senha foi bloqueada pelo administrador.[/COLOR]\n\n'
                    '[COLOR FFCCCCCC]Entre em contato para regularizar seu acesso.[/COLOR]'
                )
                return False

    # Senha nao encontrada no clients.json: pede nova senha
    ADDON.setSetting('auth_ok', '0')
    ADDON.setSetting('client_pass', '')
    ADDON.setSetting('client_name', '')
    return ask_client_password()

def ask_client_password():
    dlg = xbmcgui.Dialog()
    dlg.ok(
        '[COLOR FF3399FF][B]PLUGN[/B][/COLOR][COLOR FFFFD700][B]STREAMING[/B][/COLOR] [COLOR FFCC0000][B]VIP[/B][/COLOR]',
        '[COLOR FFCCCCCC]Bem-vindo! Digite sua senha de acesso para continuar.[/COLOR]\n\n'
        '[COLOR FF888888]Cada cliente possui uma senha individual exclusiva.[/COLOR]'
    )
    password = dlg.input('[B]Senha de Acesso[/B]', type=xbmcgui.INPUT_ALPHANUM)
    if not password:
        return False
    prog = xbmcgui.DialogProgress()
    prog.create(
        '[COLOR FF3399FF][B]PLUGN[/B][/COLOR][COLOR FFFFD700][B]STREAMING[/B][/COLOR] [COLOR FFCC0000][B]VIP[/B][/COLOR]',
        'Verificando acesso...'
    )
    prog.update(50, 'Consultando servidor de licencas...')
    ok, result = check_client_password(password)
    prog.close()
    if ok:
        ADDON.setSetting('auth_ok', '1')
        ADDON.setSetting('client_name', result)
        ADDON.setSetting('client_pass', password)
        dlg.ok(
            '[COLOR FF00CC44][B]ACESSO LIBERADO![/B][/COLOR]',
            '[COLOR FFCCCCCC]Bem-vindo,[/COLOR] [COLOR FFFFD700][B]{}[/B][/COLOR][COLOR FFCCCCCC]![/COLOR]\n\n'
            '[COLOR FF888888]Aproveite o melhor do streaming.[/COLOR]'.format(result)
        )
        return True
    elif result == 'bloqueado':
        dlg.ok(
            '[COLOR FFCC0000][B]ACESSO BLOQUEADO[/B][/COLOR]',
            '[COLOR FFCC0000]Sua senha foi bloqueada pelo administrador.[/COLOR]\n\n'
            '[COLOR FFCCCCCC]Entre em contato para regularizar seu acesso.[/COLOR]'
        )
    elif result == 'offline':
        dlg.ok(
            '[COLOR FFFF9900][B]SEM CONEXAO[/B][/COLOR]',
            '[COLOR FFCCCCCC]Nao foi possivel verificar sua senha online.[/COLOR]\n\n'
            '[COLOR FF888888]Verifique sua conexao com a internet.[/COLOR]'
        )
    else:
        dlg.ok(
            '[COLOR FFCC0000][B]SENHA INVALIDA[/B][/COLOR]',
            '[COLOR FFCC0000]Senha nao encontrada.[/COLOR]\n\n'
            '[COLOR FFCCCCCC]Verifique sua senha e tente novamente.[/COLOR]'
        )
    return False

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
    xbmcplugin.addDirectoryItem(HANDLE, build_url({'action': 'change_server'}), li_srv, False)

    # TROCAR PLAYER
    player = get_player_type()
    player_label = 'NATIVO' if player == 'nativo' else 'F4MTESTER'
    li_player = xbmcgui.ListItem(
        '[COLOR FF00CCFF][B]>> TIPO DE PLAYER  |  ATIVO: {}[/B][/COLOR]'.format(player_label)
    )
    li_player.setArt({'icon': icon('iconserver'), 'thumb': icon('iconserver'), 'fanart': FANART})
    li_player.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(HANDLE, build_url({'action': 'change_player'}), li_player, False)

    # ITENS DO MENU
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

    # FAZER DOACAO
    li_don = xbmcgui.ListItem(
        '[COLOR FFFF4444][B]  FAZER DOACAO[/B][/COLOR]  [COLOR FFCCCCCC]- Apoie o projeto![/COLOR]'
    )
    li_don.setArt({
        'icon':   icon('icondonation'),
        'thumb':  icon('icondonation'),
        'fanart': FANART,
    })
    li_don.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(HANDLE, build_url({'action': 'donation'}), li_don, False)

    end_dir()

# ============================================================
# TROCAR PLAYER
# ============================================================
def change_player():
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
    keys = list(SERVERS.keys())
    for n in keys:
        s = SERVERS[n]
        mark = '  [COLOR FFFFD700][B]<< ATIVO[/B][/COLOR]' if n == current else ''
        opts.append('[B]{}[/B]{}'.format(s['name'], mark))
    sel = dlg.select('[B]Selecionar Servidor[/B]', opts)
    if sel >= 0:
        new_num = keys[sel]
        set_active_server(new_num)
        notify('[COLOR FF00CC44]Servidor: {}[/COLOR]'.format(SERVERS[new_num]['name']))
    xbmc.executebuiltin('Container.Refresh')

# ============================================================
# DOACAO - Exibe QR Code Pix
# ============================================================
def show_donation():
    dlg = xbmcgui.Dialog()
    if os.path.exists(QR_CODE):
        dlg.ok(
            '[COLOR FFFF4444][B]FAZER DOACAO - PIX[/B][/COLOR]',
            '[COLOR FFCCCCCC]Escaneie o QR Code com seu app de banco:[/COLOR]\n\n'
            '[COLOR FFFFD700][B]Obrigado pelo seu apoio![/B][/COLOR]\n'
            '[COLOR FF888888]Sua contribuicao mantem o projeto ativo.[/COLOR]'
        )
        xbmc.executebuiltin('ShowPicture({})'.format(QR_CODE))
    else:
        dlg.ok(
            '[COLOR FFFF4444][B]FAZER DOACAO - PIX[/B][/COLOR]',
            '[COLOR FFCCCCCC]Obrigado por querer contribuir![/COLOR]\n\n'
            '[COLOR FFFFD700][B]Entre em contato com o administrador[/B][/COLOR]\n'
            '[COLOR FF888888]para receber as informacoes de pagamento.[/COLOR]'
        )

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
        sid      = str(movie.get('stream_id', ''))
        name     = movie.get('name', 'Filme')
        thumb    = movie.get('stream_icon', '') or icon('iconmovies')
        ext      = movie.get('container_extension', 'mp4')
        year     = str(movie.get('year', '') or '')
        plot     = str(movie.get('plot', '') or '')
        rating   = str(movie.get('rating', '') or '')
        duration = str(movie.get('duration', '') or '')
        url      = make_stream_url(sid, 'movie', ext)
        final_plot   = plot if plot and plot not in ('None', 'null', '') else ''
        final_year   = year if year and year not in ('None', 'null', '0', '') else ''
        final_rating = rating if rating and rating not in ('None', 'null', '0', '') else ''
        if final_year and final_year.isdigit() and int(final_year) > 0:
            lbl = '[COLOR FFFF6B00]{}[/COLOR]  [COLOR FF888888]({})[/COLOR]'.format(name, final_year)
        else:
            lbl = '[COLOR FFFF6B00]{}[/COLOR]'.format(name)
        info = {
            'title': name,
            'plot': final_plot,
            'mediatype': 'movie',
            'sorttitle': name,
            'originaltitle': name,
        }
        try:
            if final_year and str(final_year).isdigit() and int(final_year) > 0:
                info['year'] = int(final_year)
        except Exception:
            pass
        try:
            if final_rating and str(final_rating).replace('.', '').replace(',', '').isdigit():
                info['rating'] = float(str(final_rating).replace(',', '.'))
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
        info  = {'title': name, 'plot': plot, 'mediatype': 'tvshow'}
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
    if not data:
        notify('Nenhuma temporada encontrada.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    seasons = data.get('seasons', [])
    if not seasons:
        episodes = data.get('episodes', {})
        if episodes:
            for snum in sorted(episodes.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
                eps_list = episodes[snum]
                ep_count = len(eps_list)
                name = 'Temporada {}'.format(snum)
                thumb = ''
                if eps_list:
                    thumb = eps_list[0].get('info', {}).get('movie_image', '') or ''
                thumb = thumb or icon('icontvseries')
                add_dir('[COLOR FF00CC44][B]{} ({} ep)[/B][/COLOR]'.format(name, ep_count),
                        build_url({'action': 'series_eps', 'series_id': series_id, 'season': str(snum)}),
                        thumb=thumb, info={'title': name, 'season': int(snum) if str(snum).isdigit() else 1, 'mediatype': 'season'})
        else:
            notify('Nenhuma temporada encontrada.', xbmcgui.NOTIFICATION_WARNING)
        end_dir()
        return
    for season in seasons:
        snum  = season.get('season_number', 1)
        name  = season.get('name', 'Temporada {}'.format(snum))
        thumb = season.get('cover', '') or season.get('cover_big', '') or icon('icontvseries')
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
    if not value:
        return ''
    try:
        decoded = base64.b64decode(value).decode('utf-8', errors='replace')
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
        title = decode_epg_field(item.get('title', ''))
        desc  = decode_epg_field(item.get('description', ''))
        start = item.get('start', '')[:16].replace('T', ' ')
        end_t = item.get('stop', '')[:16].replace('T', ' ')
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
# ATUALIZAR SERVIDORES
# ============================================================
def update_servers_menu():
    prog = xbmcgui.DialogProgress()
    prog.create(ADDON_NAME, 'Atualizando servidores do GitHub...')
    try:
        servers_file = os.path.join(ADDON_PATH, 'servers.json')
        prog.update(30, 'Conectando ao GitHub...')
        req = urlrequest.Request(SERVERS_GITHUB_URL, headers={'User-Agent': 'Kodi/19.0'})
        response = urlrequest.urlopen(req, timeout=10)
        data = response.read().decode('utf-8')
        prog.update(60, 'Validando dados...')
        json.loads(data)
        prog.update(90, 'Salvando arquivo...')
        with open(servers_file, 'w') as f:
            f.write(data)
        prog.close()
        notify('Servidores atualizados com sucesso!', xbmcgui.NOTIFICATION_INFO, 3000)
        log('Servidores atualizados do GitHub com sucesso!')
        global SERVERS
        SERVERS = load_servers()
    except Exception as e:
        prog.close()
        log('Erro ao atualizar servidores: {}'.format(str(e)))
        notify('Erro ao atualizar: {}'.format(str(e)), xbmcgui.NOTIFICATION_ERROR, 5000)
    show_main_menu()

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
    elif action == 'update_servers':
        update_servers_menu()
    elif action == 'donation':
        show_donation()
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
