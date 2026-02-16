# -*- coding: utf-8 -*-


import base64
import os
import re
import time
import xbmcaddon
from resources.lib import common
from urllib.parse import quote, unquote, urlparse
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'cimanow'
SITE_NAME = 'Cimanow'
SITE_ICON = 'cimanow.png'
PATH = xbmcaddon.Addon().getAddonInfo('path')
ART = os.path.join(PATH, 'resources', 'art')
#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'cimanow.cc')
URL_MAIN = 'https://' + DOMAIN + '/'


URL_MOVIES_English = URL_MAIN + 'category/افلام-اجنبية/'
URL_MOVIES_Arabic = URL_MAIN + 'category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9/'
URL_SERIES_English = URL_MAIN + 'category/%d8%a7%d9%84%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a%d8%a9/'
URL_SERIES_Arabic = URL_MAIN + 'category/%d8%a7%d9%84%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b9%d8%b1%d8%a8%d9%8a%d8%a9/'
URL_MOVIES_Kids = URL_MAIN + 'category/افلام-انيميشن/'
Ramadan = URL_MAIN + 'category/رمضان-2026/'
URL_SEARCH = URL_MAIN + '?s=%s'

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
    oRequest = cRequestHandler(sUrl)
    
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    
    sHtmlContent = oRequest.request()
    if 'cimanow_HTML_encoder' in sHtmlContent:
       sHtmlContent = prase_function(sHtmlContent)
       sHtmlContent =str(sHtmlContent.encode('latin-1'),'utf-8')
    pattern = '<article aria-label="post">.*?<a href="([^"]+).+?<li aria-label="year">(.+?)</li>.+?<li aria-label="title">([^<]+)<em>.+?data-src="(.+?)" width'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return
    itemList =[]
    total = len(aResult)
    for sUrl, sYear, sName, sThumbnail in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        if sName not in itemList:
            itemList.append(sName)
            
            isTvshow, aResult = cParser.parse(unquote(sUrl), 'مسلسل')
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
        isMatchNextPage,page = cParser().parse(sHtmlContent, r'<li class="active"><a\s*href="(.*?)">(.*?)</a>')
        if isMatchNextPage:
         sNextUrl=''
         for sUrl, sPage in page:
             sPage = int(sPage)+1
             if 'page/' in sUrl:
                 sUrl = sUrl.split('page')[0]
             sNextUrl = str(sUrl)+'/page/'+str(sPage)
             
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
    if 'cimanow_HTML_encoder' in sHtmlContent:
       sHtmlContent = prase_function(sHtmlContent)
       sHtmlContent =str(sHtmlContent.encode('latin-1'),'utf-8')
    
    pattern = r'<a\s*href="([^<]+)">([^<]+)<em>'  # start element
    
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if isMatch:
        
     total = len(aResult)
     for sUrl, sSeason in aResult:
        sSeason = sSeason.replace('الموسم','')
        oGuiElement = cGuiElement('Season'+ sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('season')
        params.setParam('sUrl', sUrl.strip())
        cGui().addFolder(oGuiElement, params, True, total)
    else:
        sSeason='1'
        oGuiElement = cGuiElement('Season'+' '+sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('season')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sUrl', sUrl.strip())
        cGui().addFolder(oGuiElement, params, True, 1)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()

def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sThumbnail = params.getValue('sThumbnail')
    sHtmlContent = cRequestHandler(sUrl).request()
    sSeason = params.getValue('season')
    sShowName = params.getValue('sName')
    if 'cimanow_HTML_encoder' in sHtmlContent:
       sHtmlContent = prase_function(sHtmlContent)
       sHtmlContent =str(sHtmlContent.encode('latin-1'),'utf-8')
    
    sStart = 'id="eps">'
    sEnd = '<footer>'
    sHtmlContent = cParser.abParse(sHtmlContent, sStart, sEnd)
    
    pattern = 'href="([^"]+)".*?<em>(.*?)</em>'  # start element
    
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
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
    oRequestHandler = cRequestHandler(sUrl+ 'watching/')
    oRequestHandler.addHeaderEntry('User-Agent', common.RAND_UA)
    oRequestHandler.addHeaderEntry('Referer', 'https://rm.freex2line.online/')
    sHtmlContent = oRequestHandler.request()
    if 'cimanow_HTML_encoder' in sHtmlContent:
       sHtmlContent = prase_function(sHtmlContent)
       sHtmlContent =str(sHtmlContent.encode('latin-1'),'utf-8')
    
    pattern = r'<li data-index="([^"]+)"[\s\S]*?data-id="([^"]+)"' 
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
     for sIndex ,sId in aResult:
            siteUrl = URL_MAIN + '/wp-content/themes/Cima%20Now%20New/core.php?action=switch&index='+sIndex+'&id='+sId
            oRequestHandler = cRequestHandler(siteUrl)
            oRequestHandler.addHeaderEntry('User-Agent', common.IOS_USER_AGENT)
            oRequestHandler.addHeaderEntry('referer', URL_MAIN)
            oRequestHandler.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
            oRequestHandler.addParameters('action','switch')
            oRequestHandler.addParameters('index',sIndex)
            oRequestHandler.addParameters('id',sId)
            sHtmlContent2 = oRequestHandler.request()
            
            sPattern =  '<iframe.+?src="([^"]+)"'
            isMatch, aResult = cParser().parse(sHtmlContent2,sPattern)
            if isMatch:
             for sUrl in aResult:
              if 'cimanowtv' in sUrl:
                  sUrl = sUrl +'$$'+URL_MAIN
              sName = cParser.urlparse(sUrl)
              try :
                  sName =  sName.split('.')[-2]
              except: sName = sName    
              if cConfig().isBlockedHoster(sName)[0]: continue 
              if 'youtube' in sUrl:
                continue
              elif sUrl.startswith('//'):
                sUrl = 'https:' + sUrl
              hoster = {'link': sUrl, 'name': sName, 'displayedName':sName} # Qualität Anzeige aus Release Eintrag
              hosters.append(hoster)
               
    
    sStart = '<ul class="tabcontent" id="download">'
    sEnd = '</section>'
    sHtmlContent0 = cParser.abParse(sHtmlContent, sStart, sEnd)
    pattern = r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)<\/a>'
    isMatch, aResult = cParser().parse(sHtmlContent0, pattern)

    if isMatch:
     for sUrl, sContent in aResult:
            
            oQuality = re.search(r'([0-9]{3,4}p)', sContent)
            sQuality = oQuality.group(1) if oQuality else ''
            
            if 'https://href.li' in sUrl:
                sUrl = sUrl.split('?')[-1]
            if 'youtube' in sUrl:
                continue
            
            if sUrl.startswith('//'):
                 sUrl = 'https:' + sUrl
            if  'filespayout' in sUrl: continue
            if 'frdl' in sUrl: continue
            if 'fredl' in sUrl: continue
            if 'jetload' in sUrl:
                sUrl = resolveJetload(sUrl)
            sName = cParser.urlparse(sUrl)
            if 'cimanowtv' in sUrl:
                sName = 'CimaNow'
                sUrl = sUrl +'|verifypeer=false&Referer='+URL_MAIN
                sUrl = quote(sUrl, '/:=&?|')
            
            hoster = {'link': sUrl, 'name': sName, 'displayedName':sName + ' ' + sQuality, 'quality': sQuality} # Qualität Anzeige aus Release Eintrag
            if 'verifypeer' in sUrl or 'jetload' in sUrl.lower():
                hoster.update({ 'resolved': True})
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):

    if 'verifypeer' in sUrl or 'jetload' in sUrl.lower():
        return [{'streamUrl': sUrl, 'resolved': True}] 
    return [{'streamUrl': sUrl, 'resolved': False}]

def showSearch():
    sSearchText = cGui().showKeyBoard()
    
    if not sSearchText: return
    
    _search(False, sSearchText)
    
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)

def prase_function(page): 
    if 'cimanow_HTML_encoder' in page:
     t_script = re.findall('<script.*?;.*?\'(.*?);', page, re.S)
     t_int = re.findall(r'/g.....(.*?)\)', page, re.S)
     if t_script and t_int:
         script = t_script[0].replace("'",'')
         script = script.replace("+",'')
         script = script.replace("\n",'')
         sc = script.split('.')
         
         for elm in sc:
             c_elm = base64.b64decode(elm+'==').decode()
             t_ch = re.findall(r'\d+', c_elm, re.S)
             if t_ch:
                nb = int(t_ch[0])+int(t_int[0])
                page = page + chr(nb)
    return page

def resolveJetload(sUrl):
    try:
        base_host = urlparse(sUrl).netloc
        jetload_base = f"https://{base_host}/Jetload3/"

        
        oReq = cRequestHandler(sUrl, caching=False)
        oReq.addHeaderEntry('Referer', URL_MAIN)
        sHtml = oReq.request()

        
        oReq2 = cRequestHandler(jetload_base, caching=False)
        oReq2.addHeaderEntry('Referer', oReq.getRealUrl())
        sHtml2 = oReq2.request()

        
        data_token = re.search(r'data-token="([^"]+)"', sHtml2)
        extra_token = re.search(r"window\.extraToken\s*=\s*'([^']+)'", sHtml2)
        countdown = re.search(r'id="countdown-number">(\d+)</span>', sHtml2)

        if not data_token or not extra_token:
            
            return False

        if countdown:
            time.sleep(int(countdown.group(1)))

        
        oReq3 = cRequestHandler(
            jetload_base + 'get-link.php?token=' + data_token.group(1),
            caching=False
        )
        
        oReq3.addHeaderEntry('Referer', jetload_base)
        oReq3.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
        
        intermediate = oReq3.request().strip().lstrip('\ufeff')
        
        if not intermediate:
            return False

        import requests
        html3 = requests.get(intermediate+'?t='+extra_token.group(1),
                            headers={"Referer": jetload_base},allow_redirects=False)

        url = html3.headers.get("Location")
        if url:
            final_url = url+'|Referer=' + jetload_base
            return final_url
        
    except Exception as e:
        logger.error(f"Error resolving Jetload URL: {e}")
        return False
        