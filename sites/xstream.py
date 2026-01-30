import json
from resources.lib import common
import xbmcgui
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser, cUtil
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
import base64
import os
import re
import xbmcaddon


SITE_IDENTIFIER = 'xstream'
SITE_NAME = 'XStream'
SITE_ICON = 'xstream.png'
PATH = xbmcaddon.Addon().getAddonInfo('path')
ART = os.path.join(PATH, 'resources', 'art')
# Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_' + SITE_IDENTIFIER + '.domain') # Domain Auswahl über die xStream Einstellungen möglich
STATUS = cConfig().getSetting('plugin_' + SITE_IDENTIFIER + '_status') # Status Code Abfrage der Domain
ACTIVE = cConfig().getSetting('plugin_' + SITE_IDENTIFIER) # Ob Plugin aktiviert ist oder nicht
username = cConfig().getSetting('xstream.user')    # Username
password = cConfig().getSetting('xstream.pass')    # Password
if username == '' or password == '':                # If no username and password were set, close the plugin!
    xbmcgui.Dialog().ok(cConfig().getLocalizedString(30241), cConfig().getLocalizedString(30263))   # Inf
URL_MAIN = 'https://' + DOMAIN

livetv = URL_MAIN + '/player_api.php?username=%s&password=%s&action=get_live' % (username, password)
series = URL_MAIN + '/player_api.php?username=%s&password=%s&action=get_series' % (username, password)
movies = URL_MAIN + '/player_api.php?username=%s&password=%s&action=get_vod' % (username, password)
URL_SEARCH = URL_MAIN + '/player_api.php?username=%s&password=%s&action=search&search=%s' % (username, password, '%s')

#

def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', livetv)
    params.setParam('trumb', os.path.join(ART, 'Live.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30505), SITE_IDENTIFIER, 'showcategories'), params)  
    params.setParam('sUrl', movies)
    params.setParam('trumb', os.path.join(ART, 'Movies.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showcategories'), params) 
    params.setParam('sUrl', series)
    params.setParam('trumb', os.path.join(ART, 'TVShows.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30507), SITE_IDENTIFIER, 'showcategories'), params)
    params.setParam('trumb', os.path.join(ART, 'search.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'),params)  
    cGui().setEndOfDirectory()


def showcategories():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl+'_categories')
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 24 # HTML Cache Zeit 1 Tag
    sHtmlContent = oRequest.request()
    jsHtmlContent = json.loads(sHtmlContent)
    if 'live' in sUrl or 'vod' in sUrl:
            sUrl = sUrl + '_streams'
    for cat in jsHtmlContent:
        sName = cat['category_name']
        sID = cat['category_id']
        params.setParam('sID', sID)
        
        params.setParam('sUrl', sUrl + '&category_id=' + str(sID))
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    if 'series' in entryUrl: isTvshow = True
    else: isTvshow = False
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 24 # HTML Cache Zeit 1 Tag
    oRequest.addHeaderEntry('user-agent',common.RAND_UA )
    sHtmlContent = oRequest.request()
    jsHtmlContent = json.loads(sHtmlContent)
    logger.info(jsHtmlContent)
    total = len(jsHtmlContent)
    for item in jsHtmlContent:
        sName = item['name'].strip()
        sID = item['stream_id'] if not isTvshow else item['series_id']
        sThumbnail =  item.get('stream_icon') or item.get('cover') or ''
        sYear = ''
        m = re.search(r'(?<!^)(?<!\d)(19|20)\d{2}\b', sName)
        if m:
            sYear = str(m.group(0)) 
            sName = sName.replace(sYear,'').strip()
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        if sYear:
            oGuiElement.setYear(sYear)
        params.setParam('sUrl', entryUrl + '&id=' + str(sID))
        params.setParam('sName', sName)
        params.setParam('sID', sID)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
        
    if not sGui and not sSearchText:
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sName = params.getValue('sName')
    series_id = params.getValue('sID')

    url = URL_MAIN + f'/player_api.php?username={username}&password={password}&action=get_series_info&series_id={series_id}'
    data = json.loads(cRequestHandler(url).request())

    seasons = data.get('episodes', {})
    for season, episodes in seasons.items():
        oGuiElement = cGuiElement(f'Season {season}', SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(season)
        oGuiElement.setMediaType('season')
        params.setParam('episodes', json.dumps(episodes))
        params.setParam('season', season)
        cGui().addFolder(oGuiElement, params)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()



def showEpisodes():
    params = ParameterHandler()
    episodes = json.loads(params.getValue('episodes'))
    sName = params.getValue('sName')
    sSeason = params.getValue('season')
    for ep in episodes:
        oGuiElement = cGuiElement('Episode ' + str(ep['episode_num']), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(ep['episode_num'])
        oGuiElement.setMediaType('episode')
        params.setParam('sID', ep['id'])
        params.setParam('ext', ep.get('container_extension', 'mp4'))
        params.setParam('sUrl', params.getValue('sUrl') + '&id=' + str(ep['id']))   
        cGui().addFolder(oGuiElement, params, False)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()



def showHosters():
    hosters = []
    params = ParameterHandler()
    sID = params.getValue('sID')
    sUrl = params.getValue('sUrl')  # contains action info

    ext = params.getValue('ext') or 'mp4'

    if 'get_live' in sUrl:
        playUrl = f'{URL_MAIN}/live/{username}/{password}/{sID}.ts'
    elif 'get_series' in sUrl:
        playUrl = f'{URL_MAIN}/series/{username}/{password}/{sID}.{ext}'
    else:
        playUrl = f'{URL_MAIN}/movie/{username}/{password}/{sID}.{ext}'
    hoster = {'link': playUrl, 'name': 'Direct', 'displayedName':'Direct', 'resolveable': True, 'resolved': True} # Qualität Anzeige aus Release Eintrag
    hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl):
    return [{'streamUrl': sUrl, 'resolved': True}]


def showSearch():
    sSearchText = cGui().showKeyBoard(
        sHeading=cConfig().getLocalizedString(30281)
    )
    if not sSearchText:
        return

    oGui = cGui()

    # search live
    _searchXtream(
        oGui,
        URL_MAIN + f'/player_api.php?username={username}&password={password}&action=get_live_streams',
        sSearchText
    )

    # search movies
    _searchXtream(
        oGui,
        URL_MAIN + f'/player_api.php?username={username}&password={password}&action=get_vod_streams',
        sSearchText
    )

    # search series
    _searchXtream(
        oGui,
        URL_MAIN + f'/player_api.php?username={username}&password={password}&action=get_series',
        sSearchText
    )

    oGui.setEndOfDirectory()

def _searchXtream(oGui, url, sSearchText):
    oRequest = cRequestHandler(url)
    data = json.loads(oRequest.request())

    if not isinstance(data, list):
        return

    sSearchText = sSearchText.lower()

    for item in data:
        title = item.get('name', '')
        if sSearchText not in title.lower():
            continue

        isSeries = 'series_id' in item
        isLive = 'get_live_streams' in url

        sID = item.get('series_id') if isSeries else item.get('stream_id')
        thumb = item.get('stream_icon') or item.get('cover', '')
        ext = item.get('container_extension', 'mp4')

        # Decide target function
        target = 'showSeasons' if isSeries else 'showHosters'

        oGuiElement = cGuiElement(title, SITE_IDENTIFIER, target)
        oGuiElement.setThumbnail(thumb)

        if isSeries:
            oGuiElement.setMediaType('tvshow')
        elif isLive:
            oGuiElement.setMediaType('video')
        else:
            oGuiElement.setMediaType('movie')

        params = ParameterHandler()
        params.setParam('sID', sID)
        params.setParam('sName', title)
        params.setParam('sUrl', url)
        params.setParam('ext', ext)

        oGui.addFolder(oGuiElement, params, isSeries)







