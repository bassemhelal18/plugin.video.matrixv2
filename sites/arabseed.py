# -*- coding: utf-8 -*-



import json
import os
import re, requests
import xbmcaddon
from urllib.parse import unquote,quote
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
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'asd.rest')
URL_MAIN = 'https://' + DOMAIN + '/'


URL_MOVIES_English = URL_MAIN + 'category/foreign-movies/'
URL_MOVIES_Arabic = URL_MAIN + 'category/arabic-movies-5/'
URL_SERIES_English = URL_MAIN + 'category/foreign-series/'
URL_SERIES_Arabic = URL_MAIN + 'category/arabic-series/'
URL_MOVIES_Kids = URL_MAIN + 'category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%8a%d9%85%d9%8a%d8%b4%d9%86/'
Ramadan = URL_MAIN + 'category/مسلسلات-رمضان/ramadan-series-2025/'
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
    
    
    oRequest.addHeaderEntry('Referer', quote(sUrl))
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
        sName = sName.replace('مترجمة','').replace('مترجم','').replace('فيلم','').replace('مسلسل','').split('الموسم')[0].split('الحلقة')[0].strip()
        sYear = ''
        m = re.search(r'(?<!^)(?<!\d)(19|20)\d{2}\b', sName)
        if m:
            sYear = str(m.group(0))
            sName = sName.replace(sYear,'')
        if sSearchText and not cParser.search(sSearchText, sName):
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
        
        pattern = '<link rel="canonical" href="(.*?)".*?<meta property="og:title" content="(.*?)" />'  # start element
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
     headears = {'x-requested-with':'XMLHttpRequest',
                 'referer': urllib_parse.quote(sUrl, '%/:?=&!+')}
     data = {'season_id': dataterm,
                 'csrf_token': csrf__token}
     sHtmlContent = requests.post(urlseason,data=data,headers=headears).text
      
     sHtmlContent = str(json.loads(sHtmlContent))
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
       
       sStart = '<div class="ContainerEpisodesList"'
       sEnd = '<div style="clear: both;"></div>'
       sHtmlContent = cParser.abParse(sHtmlContent, sStart, sEnd)
       pattern = 'href="([^<]+)">.*?<em>([^<]+)</em>'  # start element
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
        headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1',
                   'referer': URL_MAIN}
        session = requests.Session()
        r = session.get(actionurl, headers=headers)
        sHtmlContent4 = r.text
        
        isMatch, token = cParser.parseSingleResult(sHtmlContent4,'''['"]csrf__token['"]: ['"](.*?)["']''')
        if isMatch:
            
            sHtmlContent2 = str(getlinks(token,actionurl,sUrl))
               
        
    
    sPattern = "(https.*?),(.*?)'"
    isMatch,aResult = cParser.parse(sHtmlContent2, sPattern)
     
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
        hoster = {'link': shost, 'name': sName, 'displayedName':sName+' '+sQuality, 'quality': sQuality} # Qualität Anzeige aus Release Eintrag
        hosters.append(hoster)
    
    
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)

def getlinks(token,actionurl,sUrl):
    
    listqual = []
    logger.info(actionurl)
    for sServer in ('0', '1', '2', '3', '4', '5','6', '7','8'):
        for sQual in ('1080', '720', '480', '360'):

          headers = {'accept':
'application/json, text/javascript, */*; q=0.01',
            'x-requested-with' : 'XMLHttpRequest',
            'origin':'https://m.gamehub.cam',
            'referer': actionurl,
            'sec-fetch-dest':'empty',
'sec-fetch-mode':'cors',
'sec-fetch-site':'same-origin',
'cookie':'cf_clearance=I9nx.yh3h6_Sg6RWEkolVwKWRntW1vL6eXEy8aT602Q-1743364415-1.2.1.1-8ASTk0GfGrFbG1qCOHFAb6r1Zl9m9.AViOtXMueCpWfyWo0N81r.0Kld1cJnyIOuBGF7baqn6tLQL0VbDwC5y1hQCHJYY.MPdYiG7RbGqEA_ZAFl4_JRl.O0.xS8MPYQ7Qr4izqGpOB6ZkOgvrSSYmmmLYeRL9gvB7ws30C84wU16nks6fOPvtjM9WUXMiRLnakvBLoPRnGoIysno1xd3rn8xmRq9dS3A_.M82nhYAIO3BCwWTqRBow7iDnOsqZQyny.CmLB5z4Jzuqx8Xrp5UdlXhwCEx6I1wbySX5p0szMt1sZZuWoHAXT1q7FX._6G_Wdbt1smGSpsViPaj8SkX_1iL.4qs8RL1J4HLLJvDkAJ_7xM4pACdGjfD1xWZc2rz36lnKC_SQCt16V2CuOaaMH7Bf61QecT1VXKciPtOQ; __eoi=ID=48ec88c4365a9b28:T=1743366976:RT=1743366976:S=AA-AfjZTNalKKKEAvXsyr1G8eV0b; _ga=GA1.1.211684426.1753959474; _ga_13FES6G8SF=GS2.1.s1756563641$o63$g1$t1756563668$j33$l0$h0; watch_servers_sid=3e6e864f1743194fb649b68a429df1a8; _ga_RLYB3E6BPM=GS2.1.s1756667413$o11$g1$t1756669183$j60$l0$h0'

            }
        
          payload= {'quality':sQual,
             'server':sServer,
             "csrf_token": token,
            }
        
          response = requests.post("https://m.gamehub.cam/get__watch__server/",data=payload,headers=headers)
          sHtmlContent = str(response.text).replace('\x00', '')
          
          sPattern = '"server":"([^"]+)"'
          aResult = cParser.parse(sHtmlContent, sPattern)
          if aResult[0]:
            for aEntry in aResult[1]:
        
                sHosterUrl = aEntry
                listqual.append(sHosterUrl+' ,'+sQual)
        
    return listqual