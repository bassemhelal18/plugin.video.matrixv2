# -*- coding: utf-8 -*-


import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
import xbmcaddon
from six.moves.urllib.parse import unquote,quote
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui


SITE_IDENTIFIER = 'shahidu'
SITE_NAME = 'Shahid4u'
SITE_ICON = 'shahidu.png'
PATH = xbmcaddon.Addon().getAddonInfo('path')
ART = os.path.join(PATH, 'resources', 'art')
#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'shahed4u.here')
# Only the previous shipped default migrates; custom settings are preserved.
if DOMAIN == 'shaaheid4u.net':
    DOMAIN = 'shahed4u.here'
    cConfig().setSetting('plugin_'+ SITE_IDENTIFIER +'.domain', DOMAIN)
URL_MAIN = 'https://' + DOMAIN + '/'


URL_MOVIES_English = URL_MAIN + 'category/افلام-اجنبي'
URL_MOVIES_Arabic = URL_MAIN + 'category/افلام-عربي'
URL_SERIES_English = URL_MAIN + 'category/مسلسلات-اجنبي'
URL_SERIES_Arabic = URL_MAIN + 'category/مسلسلات-عربي'
URL_MOVIES_Kids = URL_MAIN + 'category/افلام-انمي'
Ramadan = URL_MAIN + 'category/مسلسلات-رمضان-2026'
URL_SEARCH = URL_MAIN + 'search?s=%s'

#ToDo Serien auch auf reinen Filmseiten, prüfen ob Filterung möglich
def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES_English)
    params.setParam('trumb', os.path.join(ART, 'MoviesEnglish.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  
    params.setParam('sUrl', URL_MOVIES_Arabic)
    params.setParam('trumb', os.path.join(ART, 'MoviesArabic.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30500), SITE_IDENTIFIER, 'showEntries'), params)  
    params.setParam('sUrl', URL_SERIES_English)
    params.setParam('trumb', os.path.join(ART, 'TVShowsEnglish.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30514), SITE_IDENTIFIER, 'showEntries'), params)  
    params.setParam('sUrl', URL_SERIES_Arabic)
    params.setParam('trumb', os.path.join(ART, 'TVShowsArabic.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  
    params.setParam('sUrl', URL_MOVIES_Kids)
    params.setParam('trumb', os.path.join(ART, 'Kids.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30503), SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', Ramadan)
    params.setParam('trumb', os.path.join(ART, 'Ramadan.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30501), SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('trumb', os.path.join(ART, 'search.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'),params) 
    cGui().setEndOfDirectory()


def _page(url, referer=None):
    request = cRequestHandler(url)
    # urllib serializes headers as latin-1. Quote Arabic URL characters once,
    # preserving existing percent escapes and URL delimiters.
    request.addHeaderEntry('Referer', quote(referer or URL_MAIN, safe="%/:?=&!+$,;@#[]()*'~-._"))
    return request, BeautifulSoup(request.request() or '', 'html.parser')


def _http(base, value):
    if not value:
        return ''
    url = urljoin(base, value)
    return url if urlsplit(url).scheme in ('http', 'https') else ''


def _title(value):
    value = re.sub(r'\b(?:19|20)\d{2}\b', '', value)
    for word in ('مشاهدة', 'مترجمة', 'مترجم', 'فيلم', 'مسلسل', 'اون لاين', 'أون لاين'):
        value = value.replace(word, '')
    return value.split('الموسم')[0].split('الحلقة')[0].strip()


def showEntries(sUrl=False, sGui=False, sSearchText=False):
    gui = sGui if sGui else cGui()
    params = ParameterHandler()
    listing = sUrl or params.getValue('sUrl') or URL_MAIN
    # Legacy navigation parameters must not replace an existing search query.
    page = str(params.getValue('page') or '')
    if page.isdigit() and int(page) > 1:
        parts = urlsplit(listing)
        query = dict(parse_qsl(parts.query))
        query['page'] = page
        listing = urlunsplit(parts._replace(query=urlencode(query)))
    request, doc = _page(listing)
    cards = doc.select('a.show-card[href]')
    seen = set()
    count = 0
    for card in cards:
        title = card.select_one('.title')
        if not title:
            continue
        raw = title.get_text(' ', strip=True)
        name = _title(raw)
        link = _http(listing, card.get('href'))
        is_series = any(x in urlsplit(link).path for x in ('/serie/', '/series/', '/season/', '/episode/'))
        identity = name if is_series else link
        if not name or not link or identity in seen:
            continue
        # The site's own search matches are retained, never compiled as regex.
        seen.add(identity)
        element = cGuiElement(name, SITE_IDENTIFIER, 'showSeasons' if is_series else 'showHosters')
        element.setMediaType('tvshow' if is_series else 'movie')
        year = re.search(r'\b(?:19|20)\d{2}\b', raw)
        if year:
            element.setYear(year.group())
        image = card.select_one('img')
        thumbnail = _http(listing, (image.get('data-src') or image.get('src')) if image else '')
        element.setThumbnail(thumbnail)
        item = ParameterHandler()
        item.setParam('sUrl', link)
        item.setParam('sName', name)
        item.setParam('sThumbnail', thumbnail)
        gui.addFolder(element, item, is_series, len(cards))
        count += 1
    if not count and not sGui:
        gui.showInfo()
    if not sGui:
        nxt = doc.select_one('a[rel="next"][href]')
        if nxt:
            next_url = _http(listing, nxt['href'])
            if urlsplit(next_url).netloc == urlsplit(listing).netloc:
                item = ParameterHandler()
                item.setParam('sUrl', next_url)
                item.setParam('page', 0)
                item.setParam('trumb', os.path.join(ART, 'Next.png'))
                gui.addNextPage(SITE_IDENTIFIER, 'showEntries', item)
        gui.setView('movies')
        gui.setEndOfDirectory()


def _number(anchor):
    spans = anchor.select('span')
    text = spans[-1].get_text(' ', strip=True) if spans else anchor.get_text(' ', strip=True)
    match = re.search(r'\d+', text)
    return match.group() if match else ''


def _parts(kind):
    params = ParameterHandler()
    url = params.getValue('sUrl')
    request, doc = _page(url)
    anchors = [a for a in doc.select('a.epss[href]') if '/' + kind + '/' in urlsplit(_http(url, a['href'])).path]
    return params, url, doc, anchors


def showSeasons():
    params, url, doc, anchors = _parts('season')
    if not anchors:
        # Series/episode pages without separate seasons may list episodes directly.
        showEpisodes()
        return
    seen = set()
    for anchor in anchors:
        link = _http(url, anchor['href'])
        number = _number(anchor)
        if link in seen or not number:
            continue
        seen.add(link)
        item = ParameterHandler()
        for key in ('sName', 'sThumbnail'):
            item.setParam(key, params.getValue(key) or '')
        item.setParam('sUrl', link)
        item.setParam('season', number)
        element = cGuiElement('Season ' + number, SITE_IDENTIFIER, 'showEpisodes')
        element.setTVShowTitle(params.getValue('sName') or '')
        element.setThumbnail(params.getValue('sThumbnail') or '')
        element.setSeason(number)
        element.setMediaType('season')
        cGui().addFolder(element, item, True, len(anchors))
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params, url, doc, anchors = _parts('episode')
    seen = set()
    for anchor in anchors:
        link = _http(url, anchor['href'])
        number = _number(anchor)
        if link in seen or not number:
            continue
        seen.add(link)
        item = ParameterHandler()
        item.setParam('sUrl', link)
        element = cGuiElement('Episode ' + number, SITE_IDENTIFIER, 'showHosters')
        element.setTVShowTitle(params.getValue('sName') or '')
        element.setThumbnail(params.getValue('sThumbnail') or '')
        if params.getValue('season'):
            element.setSeason(params.getValue('season'))
        element.setEpisode(number)
        element.setMediaType('episode')
        cGui().addFolder(element, item, False, len(anchors))
    if not anchors:
        cGui().showInfo()
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def _downloadPage(url):
    request, doc = _page(url)
    if '/download/' in urlsplit(url).path:
        return url, doc
    anchor = doc.select_one('a.btn.download[href]')
    if not anchor:
        return '', doc
    download = _http(url, anchor['href'])
    if urlsplit(download).netloc != urlsplit(url).netloc:
        return '', doc
    return download, _page(download, url)[1]


def _downloads(doc, base):
    result = []
    for anchor in doc.select('.down-container a.btn-down[href]'):
        if anchor.has_attr('data-honeytoken') or anchor.get('aria-hidden') == 'true':
            continue
        spans = anchor.select('.info > span')
        name = spans[0].get_text(' ', strip=True) if spans else ''
        quality = spans[1].get_text(' ', strip=True) if len(spans) > 1 else ''
        link = _http(base, anchor['href'])
        if name and link and not cConfig().isBlockedHoster(name.rstrip('.'))[0]:
            result.append((link, name, quality))
    return result


def showHosters():
    # Current watch servers require browser-generated interaction signals.
    # Do not invent those signals or mistake their JSON metadata for host URLs.
    url = ParameterHandler().getValue('sUrl')
    download, doc = _downloadPage(url)
    choices = _downloads(doc, download) if download else []
    hosters = []
    for index, (link, name, quality) in enumerate(choices):
        # Refresh short-lived wrapper URLs only when a server is selected.
        hosters.append({'link': download + '#matrixv2-server=' + urlencode({'name': name, 'quality': quality}),
                        'name': name, 'displayedName': name + ' ' + quality,
                        'quality': quality})
    if hosters:
        hosters.append('getHosterUrl')
    else:
        cGui().showInfo()
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl:
        return []
    parts = urlsplit(sUrl)
    if not parts.fragment.startswith('matrixv2-server='):
        return [{'streamUrl': sUrl, 'resolved': False}]
    try:
        selection = dict(parse_qsl(parts.fragment.split('=', 1)[1]))
        download = urlunsplit(parts._replace(fragment=''))
        request, doc = _page(download)
        choices = _downloads(doc, download)
        matches = [entry for entry in choices if entry[1] == selection.get('name') and entry[2] == selection.get('quality')]
        if not matches:
            return []
        wrapper = matches[0][0]
        if urlsplit(wrapper).netloc != urlsplit(download).netloc:
            return [{'streamUrl': wrapper, 'resolved': False}]
        if not urlsplit(wrapper).path.startswith('/m/'):
            return []
        request, doc = _page(wrapper, download)
        final = request.getRealUrl() or wrapper
        # Follow only an ordinary HTTP redirect. Never decode
        # protection tokens, run website JS, or return expired same-site wrappers.
        if urlsplit(final).netloc != urlsplit(download).netloc and _http(wrapper, final):
            return [{'streamUrl': final, 'resolved': False}]
    except (ValueError, TypeError, IndexError):
        pass
    logger.info(' -> [shahidu]: selected server unavailable or expired')
    cGui().showInfo()
    return []


def showSearch():
    text = cGui().showKeyBoard()
    if not text:
        return
    _search(False, text)


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)
