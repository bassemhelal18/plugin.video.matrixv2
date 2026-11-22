# -*- coding: utf-8 -*-



import json
from bs4 import BeautifulSoup
import os
import re, requests
import xbmcaddon
from urllib.parse import unquote,quote,urljoin,urlsplit
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser, cUtil
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib import common
from six.moves import urllib_parse



SITE_IDENTIFIER = 'arabseed'
SITE_NAME = 'Arabseed'
SITE_ICON = 'arabseed.png'
PATH = xbmcaddon.Addon().getAddonInfo('path')
ART = os.path.join(PATH, 'resources', 'art')
#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'm.myseed.tv')
URL_MAIN = 'https://' + DOMAIN + '/'


URL_MOVIES_English = URL_MAIN + 'category/foreign-movies/'
URL_MOVIES_Arabic = URL_MAIN + 'category/arabic-movies/'
URL_SERIES_English = URL_MAIN + 'category/foreign-series/'
URL_SERIES_Arabic = URL_MAIN + 'category/arabic-series/'
URL_MOVIES_Kids = URL_MAIN + 'category/animation-movies/'
Ramadan = URL_MAIN + 'category/مسلسلات-رمضان/ramadan-series-2026/'
URL_SEARCH = URL_MAIN + 'find/?word=%s&type='

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


def showEntries(sUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    isTvshow = False
    if not sUrl: sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    
    
    oRequest.addHeaderEntry('Referer', quote(sUrl, safe='%/:?=&'))
    sHtmlContent = oRequest.request()
    
    pattern = '<div class="item__contents.*?<a href="(.*?)".*?data-src="(.*?)".*?alt="(.*?)"'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return
    itemList =[]
    total = len(aResult)
    for sUrl, sThumbnail,sName in aResult:
        isTvshow, aResult = cParser.parse(sName,'الحلقة')
        if not isTvshow:
           isTvshow, aResult = cParser.parse(sName,'مسلسل')
        sName = sName.replace('مترجمة','').replace('مترجم','').replace('فيلم','').replace('مسلسل','').replace('مشاهدة','').split('الموسم')[0].split('الحلقة')[0].strip()
        sYear = ''
        m = re.search(r'(?<!^)(?<!\d)(19|20)\d{2}\b', sName)
        if m:
            sYear = str(m.group(0))
            sName = sName.replace(sYear,'')
        if sSearchText and sSearchText.casefold() not in sName.casefold():
            continue
        
        if sName not in itemList:
            itemList.append(sName)
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
            if sYear:
             oGuiElement.setYear(sYear)
            params.setParam('sUrl', sUrl)
            params.setParam('sName', sName)
            params.setParam('sThumbnail', sThumbnail)
            oGui.addFolder(oGuiElement, params, isTvshow, total)
        
    if not sGui and not sSearchText:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent,'<a class="next page-numbers" href="(.*?)"')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            params.setParam('trumb', os.path.join(ART, 'Next.png'))
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()



def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sThumbnail = params.getValue('sThumbnail')
    sName = params.getValue('sName')
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    csrf__token = ''
    isMatch, token = cParser.parseSingleResult(sHtmlContent,'''['"]csrf__token['"]: ['"](.*?)["']''')
    if isMatch:
       csrf__token = token
    
    pattern = 'data-term="(.*?)".*?<span>(.*?)</span>'  # start element
    
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if  isMatch:
       
     total = len(aResult)
     for dataterm,sSeason in aResult:
        sSeason = sSeason.replace("مترجم","").replace("مترجمة","").replace(" الحادي عشر","11").replace(" الثاني عشر","12").replace(" الثالث عشر","13").replace(" الرابع عشر","14").replace(" الخامس عشر","15").replace(" السادس عشر","16").replace(" السابع عشر","17").replace(" الثامن عشر","18").replace(" التاسع عشر","19").replace(" العشرون","20").replace(" الحادي و العشرون","21").replace(" الثاني و العشرون","22").replace(" الثالث و العشرون","23").replace(" الرابع والعشرون","24").replace(" الخامس و العشرون","25").replace(" السادس والعشرون","26").replace(" السابع والعشرون","27").replace(" الثامن والعشرون","28").replace(" التاسع والعشرون","29").replace(" الثلاثون","30").replace(" الحادي و الثلاثون","31").replace(" الثاني والثلاثون","32").replace("الموسم الخامس","5").replace(" الاول","1").replace(" الثاني","2").replace(" الثانى","2").replace(" الثالث","3").replace(" الرابع","4").replace(" الخامس","5").replace(" السادس","6").replace(" السابع","7").replace(" الثامن","8").replace(" التاسع","9").replace(" العاشر","10").replace('الموسم','')
        oGuiElement = cGuiElement('Season'+' ' +sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('season')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('dataterm', dataterm)
        params.setParam('csrf__token', csrf__token)
        cGui().addFolder(oGuiElement, params, True, total)
    else:
        
        pattern = '<link rel="canonical" href="(.*?)".*?<title>(.*?)</title>'  # start element
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if  isMatch:
          total = len(aResult)
          for sUrl,sSeason in aResult:
            
            sSeason = sSeason.replace(sName,'').replace('مسلسل','').split('الحلقة')[0].replace("مترجم","").replace("مترجمة","").replace(" الحادي عشر","11").replace(" الثاني عشر","12").replace(" الثالث عشر","13").replace(" الرابع عشر","14").replace(" الخامس عشر","15").replace(" السادس عشر","16").replace(" السابع عشر","17").replace(" الثامن عشر","18").replace(" التاسع عشر","19").replace(" العشرون","20").replace(" الحادي و العشرون","21").replace(" الثاني و العشرون","22").replace(" الثالث و العشرون","23").replace(" الرابع والعشرون","24").replace(" الخامس و العشرون","25").replace(" السادس والعشرون","26").replace(" السابع والعشرون","27").replace(" الثامن والعشرون","28").replace(" التاسع والعشرون","29").replace(" الثلاثون","30").replace(" الحادي و الثلاثون","31").replace(" الثاني والثلاثون","32").replace("الموسم الخامس","5").replace(" الاول","1").replace(" الثاني","2").replace(" الثانى","2").replace(" الثالث","3").replace(" الرابع","4").replace(" الخامس","5").replace(" السادس","6").replace(" السابع","7").replace(" الثامن","8").replace(" التاسع","9").replace(" العاشر","10").replace("الموسم","").strip()
            isSeason,sSeason = cParser.parse(sSeason, '\d+')
            sSeason=str(sSeason).replace("['","").replace("']","")
            if not isSeason:
              sSeason='1'
            oGuiElement = cGuiElement('Season'+' '+sSeason, SITE_IDENTIFIER, 'showEpisodes')
            oGuiElement.setTVShowTitle(sName)
            oGuiElement.setSeason(sSeason)
            oGuiElement.setMediaType('season')
            params.setParam('sThumbnail', sThumbnail)
            params.setParam('sUrl', sUrl.strip())
            cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()

def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    sThumbnail = params.getValue('sThumbnail')
    sSeason = params.getValue('season')
    
    sShowName = params.getValue('sName')
    csrf__token = params.getValue('csrf__token')
    dataterm = params.getValue('dataterm')
    
    if dataterm:
     urlseason = URL_MAIN + 'season__episodes/'
     oRequestHandler = cRequestHandler(urlseason,'POST')
     oRequestHandler.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
     oRequestHandler.addHeaderEntry('referer',  urllib_parse.quote(sUrl, '%/:?=&!+'))
     oRequestHandler.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
     oRequestHandler.addParameters('season_id', dataterm)
     oRequestHandler.addParameters('csrf_token', csrf__token)
     sHtmlContent = oRequestHandler.request()
      
     try:
      sHtmlContent = json.loads(sHtmlContent).get('html', '')
     except (ValueError, TypeError, AttributeError):
      sHtmlContent = ''
     pattern = '<a href="(.*?)".*?class="epi__num">.*?<b>(.*?)</b>'  # start element
     isMatch, aResult = cParser.parse(sHtmlContent, pattern)
     if  isMatch: 
      total = len(aResult)
      for sUrl, sEpisode in aResult:
        
        oGuiElement = cGuiElement('Episode ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sShowName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        params.setParam('sUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    else:
       
       sStart = '<ul class="episodes__list boxs__wrapper d__flex flex__wrap">'
       sEnd = '<div class="break__line"></div>'
       sHtmlContent = cParser.abParse(sHtmlContent, sStart, sEnd)
       pattern = 'href="([^<]+)" class=.*?class="epi__num">الحلقة<b>(.*?)</b>'  # start element
       isMatch, aResult = cParser.parse(sHtmlContent, pattern)
       if  isMatch:
        total = len(aResult)
        for sUrl, sEpisode in aResult:
         oGuiElement = cGuiElement('Episode ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
         oGuiElement.setTVShowTitle(sShowName)
         oGuiElement.setSeason(sSeason)
         oGuiElement.setEpisode(sEpisode)
         oGuiElement.setMediaType('episode')
         params.setParam('sUrl', sUrl)
         cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('sUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
      # start element
    isactionurl, actionurl = cParser.parseSingleResult(sHtmlContent,'<a href="([^<]+)" class="btton watch__btn">' )
    if isactionurl:
        oRequestHandler = cRequestHandler(actionurl)
        oRequestHandler.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
        oRequestHandler.addHeaderEntry('referer', URL_MAIN)
        sHtmlContent4 = oRequestHandler.request()
        
        isMatch, token = cParser.parseSingleResult(sHtmlContent4,'''['"]csrf__token['"]: ['"](.*?)["']''')
        if isMatch:
         ispsot_id, psot_id = cParser.parseSingleResult(sHtmlContent4,'''['"]psot_id['"]: ['"](.*?)["']''' )
         if ispsot_id:
            sStart = 'class="qualities__list">'
            sEnd = '</ul>'
            sHtmlContent = cParser.abParse(sHtmlContent4, sStart, sEnd)
            pattern = '<div class="qu">(.+?)<'   # start element
    
            isMatch, aResult = cParser.parse(sHtmlContent, pattern)
            if not isMatch: return
            for sQual in aResult:
                oRequestHandler = cRequestHandler(URL_MAIN+'get__quality__servers/','POST')
                oRequestHandler.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
                oRequestHandler.addHeaderEntry('referer', actionurl)
                oRequestHandler.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
                oRequestHandler.addParameters('quality', sQual)
                oRequestHandler.addParameters('post_id', psot_id)
                oRequestHandler.addParameters('csrf_token', token)
                sHtmlContent41 = oRequestHandler.request()
                
                sHtmlContent2 = getlinks(str(sHtmlContent41),actionurl,token,psot_id)
                
                aResult = [item.rsplit(',', 1) for item in (sHtmlContent2 or [])]
                isMatch = bool(aResult)
     
                if isMatch:
                 for shost, sQuality in aResult :
        
                    sName = cParser.urlparse(shost)
        
                    if cConfig().isBlockedHoster(sName)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
                    if 'youtube' in shost:
                        continue
                    if 'Gamezone' in sName:
                       sName = 'Arabseed'
                    elif shost.startswith('//'):
                      shost = 'https:' + shost
                    hoster = {'link': shost, 'name': sName, 'displayedName':sName+' '+sQuality, 'quality': sQuality, 'resolveable': urlsplit(shost).netloc == urlsplit(URL_MAIN).netloc} # Qualität Anzeige aus Release Eintrag
                    hosters.append(hoster)
    
    
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    # Only unwrap this site's own current direct-player chain.
    if sUrl and urlsplit(sUrl).netloc == urlsplit(URL_MAIN).netloc and urlsplit(sUrl).path == '/vids.php':
        request = cRequestHandler(sUrl)
        request.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
        request.addHeaderEntry('Referer', URL_MAIN)
        page = request.request()
        frame = BeautifulSoup(page, 'html.parser').find('iframe', src=True)
        if frame:
            gateway = urljoin(sUrl, frame['src'])
            if urlsplit(gateway).netloc == 'd.myseed.tv' and urlsplit(gateway).path == '/player-gateway.php':
                request = cRequestHandler(gateway)
                request.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
                request.addHeaderEntry('Referer', URL_MAIN)
                page = request.request()
                source = BeautifulSoup(page, 'html.parser').select_one('video source[src]')
                if source and urlsplit(source['src']).scheme == 'https':
                    media = source['src'] + '|Referer=' + quote(gateway, safe='') + '&User-Agent=' + quote(common.IOS_USER_AGENT, safe='')
                    return [{'streamUrl': media, 'resolved': True}]
        return [{'streamUrl': '', 'resolved': True}]
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)

def getlinks(sHtmlContent,actionurl,token, psot_id):
    try:
     sHtmlContent = json.loads(sHtmlContent).get('html', '')
    except (ValueError, TypeError, AttributeError):
     return []
    listqual=[]
    pattern = '''data-server=['"]([^"]+)['"].*?qu=['"]([^"]+)['"]'''   # start element
    
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return []
    for server, sQual  in aResult:
       
       oRequestHandler = cRequestHandler(URL_MAIN+'get__watch__server/','POST')
       oRequestHandler.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
       oRequestHandler.addHeaderEntry('referer', quote(actionurl, '%/:?=&'))
       oRequestHandler.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
       oRequestHandler.addParameters('quality', sQual)
       oRequestHandler.addParameters('server', server)
       oRequestHandler.addParameters('csrf_token', token)
       oRequestHandler.addParameters('post_id', psot_id)
       sHtmlContent42 = oRequestHandler.request()
       try:
        serverUrl = json.loads(sHtmlContent42).get('server', '')
        if not serverUrl: continue
        sHosterUrl = urljoin(URL_MAIN, serverUrl)
       except (ValueError, TypeError, AttributeError):
        continue
       if not sHosterUrl or urlsplit(sHosterUrl).scheme not in ('https', 'http'): continue
          
       listqual.append(sHosterUrl+','+sQual)
        
    return listqual      
    