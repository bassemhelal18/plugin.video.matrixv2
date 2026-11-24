# -*- coding: utf-8 -*-


import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
from resources.lib import common
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


def _hdr_url(value):
    # Same quoting policy as _page: urllib sends headers as latin-1.
    return quote(value, safe="%/:?=&!+$,;@#[]()*'~-._")


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




def showHosters():
    # Diagnostic only. No additional requests or changed headers/cache settings.
    diag = dict(stage='start', choices=0, attempts=0, completed=0, html=0,
                empty_invalid=0, same_site=0, external=0, duplicate=0)
    statuses = {}
    try:
        # Download page -> /m/ redirect per server -> real external host page.
        hosters = []
        seen = set()
        url = ParameterHandler().getValue('sUrl')
        diag['stage'] = 'title'
        sHtmlContent = cRequestHandler(url).request()

        isactionurl, actionurl = cParser.parseSingleResult(sHtmlContent, '<a href="([^<]+)" class="btn download">')
        if isactionurl:
            actionurl = _http(url, actionurl)
            oRequestHandler = cRequestHandler(actionurl)
            oRequestHandler.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
            oRequestHandler.addHeaderEntry('referer', _hdr_url(URL_MAIN))
            diag['stage'] = 'download'
            sHtmlContent4 = oRequestHandler.request()
            Pattern = r'<a\s[^>]*?href="(?P<link>[^"]+)"[^>]*class="btn btn-down\s*"[^>]*>\s*<div class="icon">\s*<i[^>]*><\/i>\s*<\/div>\s*<div class="info\s*">\s*<span>(?P<name>[^<]+)<\/span>\s*<span>\s*<i[^>]*><\/i>\s*<span>(?P<quality>\d+)<\/span>'
            isMatch, aResult = cParser().parse(sHtmlContent4, Pattern)
            if isMatch:
                diag['choices'] = len(aResult)
                for link, name, quality in aResult:
                    link = _http(actionurl, link)
                    if not link:
                        continue
                    # caching=False: the cache path returns before the final URL is set.
                    oReq = cRequestHandler(link, caching=False)
                    oReq.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
                    oReq.addHeaderEntry('referer', _hdr_url(actionurl))
                    diag['stage'] = 'intermediary'
                    diag['attempts'] += 1
                    body = oReq.request()
                    diag['completed'] += 1
                    status = str(oReq.getStatus())
                    status = status if status.isdigit() and len(status) == 3 else 'unknown'
                    statuses[status] = statuses.get(status, 0) + 1
                    if isinstance(body, str) and ('<html' in body.lower() or '<!doctype html' in body.lower()):
                        diag['html'] += 1
                    final = oReq.getRealUrl()
                    # Keep only genuine external host pages: http(s), and not the site's own domain.
                    parts = urlsplit(final or '')
                    if parts.scheme not in ('http', 'https') or not parts.netloc:
                        diag['empty_invalid'] += 1
                        continue
                    if parts.netloc.lower().split(':')[0] == urlsplit(URL_MAIN).netloc.lower():
                        diag['same_site'] += 1
                        continue
                    diag['external'] += 1
                    if final in seen:
                        diag['duplicate'] += 1
                        continue
                    # Log the host only, final URLs can carry signed/session values.
                    # Diagnostic variant: no host names or final URLs in our output.
                    seen.add(final)
                    hosters.append({'link': final, 'name': name,
                                    'displayedName': name + ' ' + quality,
                                    'quality': quality})
        diag['stage'] = 'done'
        if hosters:
            hosters.append('getHosterUrl')
        else:
            cGui().showInfo()
        return hosters

    finally:
        logger.info('SHAHID_DIAG stage=%s choices=%d attempts=%d completed=%d handler_status=%s html=%d empty_invalid=%d same_site=%d external=%d duplicate=%d' % (
            diag['stage'], diag['choices'], diag['attempts'], diag['completed'],
            ','.join('%s:%d' % (key, statuses[key]) for key in sorted(statuses)) or 'none',
            diag['html'], diag['empty_invalid'], diag['same_site'], diag['external'], diag['duplicate']))


def getHosterUrl(sUrl=False):
    # Original pass-through contract: host URL is already in the host list.
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    text = cGui().showKeyBoard()
    if not text:
        return
    _search(False, text)


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)