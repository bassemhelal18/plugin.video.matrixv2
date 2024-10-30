# -*- coding: utf-8 -*-


import os
import re
import requests
import xbmcaddon
from urllib.parse import quote, unquote
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from bs4 import BeautifulSoup


SITE_IDENTIFIER = 'uhdmovies'
SITE_NAME = 'UHDMovies'
SITE_ICON = 'uhdmovies.png'
PATH = xbmcaddon.Addon().getAddonInfo('path')
ART = os.path.join(PATH, 'resources', 'art')
#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'uhdmovies.icu')
URL_MAIN = 'https://' + DOMAIN + '/'


URL_MOVIES_English = URL_MAIN + 'movies/'
URL_SERIES_English = URL_MAIN + 'web-series/'

URL_SEARCH = URL_MAIN + 'search/%s'

#ToDo Serien auch auf reinen Filmseiten, prüfen ob Filterung möglich
def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES_English)
    params.setParam('trumb', os.path.join(ART, 'MoviesEnglish.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  
    params.setParam('sUrl', URL_SERIES_English)
    params.setParam('trumb', os.path.join(ART, 'TVShowsEnglish.png'))
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30514), SITE_IDENTIFIER, 'showEntries'), params) 
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
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    
    
    
    pattern = '<div class="entry-image">.*?<a href="(.*?)" title="Download (.*?) \((.*?)\).*?".*?src="(.*?)"'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return
    itemList =[]
    total = len(aResult)
    for sUrl, sName, sYear, sThumbnail  in aResult:
        sName = sName.strip()
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        if '-' in sYear:
           sYear = sYear.split('-')[0]
        if sName not in itemList:
            itemList.append(sName)
            
            isTvshow, aResult = cParser.parse(unquote(sUrl), 'season')
            if not isTvshow:
              isTvshow, aResult = cParser.parse(unquote(sUrl),'episode')
              if not isTvshow:
               isTvshow, aResult = cParser.parse(unquote(sUrl),'series')
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
            params.setParam('sUrl', sUrl)
            params.setParam('sName', sName)
            params.setParam('sThumbnail', sThumbnail)
            params.setParam('sYear', sYear)

            oGui.addFolder(oGuiElement, params, isTvshow, total)
        
    if not sGui and not sSearchText:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent,'''<a class="next page-numbers".*?href="(.*?)"''')
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
    
    isMatch, aResult = cParser.parse(sHtmlContent, '''<strong>Season (.*?)<''')
    if  isMatch:
      total = len(aResult)
      for sSeason in aResult:
        
        
        oGuiElement = cGuiElement('Season'+' ' +sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('season')
        params.setParam('sUrl', sUrl)
        cGui().addFolder(oGuiElement, params, True,total)
    else :
        sSeason = '1'
        oGuiElement = cGuiElement('Season'+' ' +sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('season')
        params.setParam('sUrl', sUrl)
        cGui().addFolder(oGuiElement, params, True)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()

def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    
    sHtmlContent = cRequestHandler(sUrl).request()
    sSeason = params.getValue('season')
    sSeasonprase = params.getValue('title')
    sShowName = params.getValue('sName')
    episodelist=[]
    
    
    sStart = f'<strong>{sSeasonprase}'
    sEnd = '<div class="mks_separator" style="border-bottom: 3px solid;"></div>'
    sHtmlContent0 = cParser.abParse(sHtmlContent, sStart, sEnd)
    
    if sStart in sHtmlContent0:
     
     
     pattern = '''Choose Episode Number to Download.*?href="(.*?)".*?<span class='mb-text'>(.*?)<'''  # start element
     isMatch, aResult = cParser.parse(sHtmlContent0, pattern)
     if not isMatch: return
     total = len(aResult)
     for sUrl, sEpisode in aResult:
        
        sEpisode = sEpisode.replace('Episode','').strip()
        if sEpisode not in episodelist:
         episodelist.append(sEpisode)
         dd = re.findall(f'''</div><p style="text-align: center;">.*?<span style="color: #.*?;">(.*?)<.*?href="(.*?)".*?<span class='mb-text'>Episode {sEpisode}<''',sHtmlContent0)
         
         oGuiElement = cGuiElement('Episode ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
         oGuiElement.setTVShowTitle(sShowName)
         oGuiElement.setSeason(sSeason)
         oGuiElement.setEpisode(sEpisode)
         oGuiElement.setMediaType('episode')
         params.setParam('html', dd)
         cGui().addFolder(oGuiElement, params, False, total)
        
    else:
        
        pattern = '''Choose Episode Number to Download.*?href="(.*?)".*?<span class='mb-text'>(.*?)<'''  # start element
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if not isMatch: return
        total = len(aResult)
        for sUrl, sEpisode in aResult:
        
         sEpisode = sEpisode.replace('Episode','').strip()
         if sEpisode not in episodelist:
          episodelist.append(sEpisode)
          dd = re.findall(f'''</div><p style="text-align: center;">.*?<span style="color: #.*?;">(.*?)<.*?href="(.*?)".*?<span class='mb-text'>Episode {sEpisode}<''',sHtmlContent)
          
          oGuiElement = cGuiElement('Episode ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
          oGuiElement.setTVShowTitle(sShowName)
          oGuiElement.setSeason(sSeason)
          oGuiElement.setEpisode(sEpisode)
          oGuiElement.setMediaType('episode')
          params.setParam('html', dd)
          cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()
    del episodelist[:]


def showHosters():
    hosters = []
    
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sType = params.getValue('mediaType')
    shtml2 = params.getValue('html')
    
    if sType == 'movie':
     sHtmlContent = cRequestHandler(sUrl).request()
     pattern = '<p style="text-align: center;">.*?<span style="color: #000000;">(.*?)<br />.*?href="(.*?)"'
     isMatch, aResult = cParser.parse(sHtmlContent, pattern)
     if not isMatch: return
    else:
      
      pattern = """'(.+?)', '(https.*?)'"""
      isMatch, aResult = cParser.parse(shtml2, pattern)
      if not isMatch: return
    for sName,slink in aResult:
        
        _wp_http = slink.split('?sid=')[1]
        action_url, _wp_http2, token = make_post_request(_wp_http)
        resp = get_pepe_url(action_url, _wp_http2, token)
        matches = get_match(resp)
        pepe_url = matches[0]
        cookies = {
            "__eoi": "ID=4a86dd07e2cfa744:T=1710970060:RT=1710970060:S=AA-AfjbVJgiJ3UbrHbBiGQPwwxlA",
            "__qca": "P0-1796148875-1710970059080"}


        if '?go=' in pepe_url:
           key = str(pepe_url.split('?go=')[1])
           cookies[key] = _wp_http2
        response = make_get_request(pepe_url, cookies, action_url)
        final_url = parse_redirect_page(response)
        file_id = get_zfile(final_url)
        res = get_mkv(file_id)
        if res is not None:
          hoster = {'link': quote(res,'/:=&?'), 'name': sName, 'displayedName':sName, 'resolveable': True} # Qualität Anzeige aus Release Eintrag
          hosters.append(hoster)
        
        res = get_mkv2(file_id)
        if res is not None:
            hoster = {'link': quote(res,'/:=&?'), 'name': sName, 'displayedName':sName, 'resolveable': True}
            hosters.append(hoster)
        
    if hosters:
           hosters.append('getHosterUrl')
    return hosters
        
    
def make_post_request(_wp_http):
        url = "https://tech.unblockedgames.world/"
        payload = {"_wp_http": _wp_http}
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "tech.unblockedgames.world",
            "Origin": "null",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Brave";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        response = requests.post(url, data=payload, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        form = soup.find('form', id='landing')
        action_url = form['action']
        _wp_http2 = form.find('input', {'name': '_wp_http2'})['value']
        token = form.find('input', {'name': 'token'})['value']
        return action_url, _wp_http2, token    

def get_pepe_url(action_url, _wp_http2, token):
        url = action_url
        payload = {"_wp_http2": _wp_http2, "token": token}
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "tech.unblockedgames.world",
            "Origin": "https://tech.unblockedgames.world",
            "Referer": "https://tech.unblockedgames.world/",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Brave";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        response = requests.post(url, data=payload, headers=headers)
        return response.text    

def get_match(resp):
        pattern = r'https://tech\.unblockedgames\.world/\?go=[^"]+'
        matches = re.findall(pattern, resp)
        return matches    

def make_get_request(url, cookies, ref):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.8",
            "Connection": "keep-alive",
            "Host": "tech.unblockedgames.world",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referrer": ref,
            "Cookie": "; ".join([f"{key}={value}" for key, value in cookies.items()]),
        }
        response = requests.get(url, headers=headers, allow_redirects=True)
        return response.text

def parse_redirect_page(html):
        pattern = r'<meta\s+http-equiv="refresh"\s+content="0;url=(.*?)"\s*/?>'
        match = re.search(pattern, html)
        if match:
            redirect_url = match.group(1)
            return redirect_url
        else:
            return None

def get_zfile(url):
  headers = {
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
      "Accept-Language": "en-GB,en;q=0.8",
      "Cache-Control": "max-age=0",
      "Connection": "keep-alive",
      "Content-Type": "application/x-www-form-urlencoded",
      "Host": "driveleech.org",
      "Origin": "https://driveleech.org",
      "Referer": "https://driveleech.org/",
      "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Brave";v="122"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": '"Windows"',
      "Sec-Fetch-Dest": "document",
      "Sec-Fetch-Mode": "navigate",
      "Sec-Fetch-Site": "same-origin",
      "Sec-Fetch-User": "?1",
      "Sec-GPC": "1",
      "Upgrade-Insecure-Requests": "1",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  }
  
  driveleech = requests.get(url, headers=headers, allow_redirects=True)
  pattern = r'/file/([a-zA-Z0-9]+)'
  matches = re.search(pattern, driveleech.text)

  if matches:
      file_id = matches.group(1)
      print("File ID:", file_id)
      return file_id
  else:
      print("File ID not found.")
      return None


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': True}]
    

def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % sSearchText, oGui, sSearchText)

def get_mkv(id):
  headers = {
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
      "Accept-Language": "en-GB,en;q=0.8",
      "Cache-Control": "max-age=0",
      "Connection": "keep-alive",
      "Content-Type": "application/x-www-form-urlencoded",
      "Host": "driveleech.org",
      "Origin": "https://driveleech.org",
      "Referer": "https://driveleech.org/",
      "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Brave";v="122"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": '"Windows"',
      "Sec-Fetch-Dest": "document",
      "Sec-Fetch-Mode": "navigate",
      "Sec-Fetch-Site": "same-origin",
      "Sec-Fetch-User": "?1",
      "Sec-GPC": "1",
      "Upgrade-Insecure-Requests": "1",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  }

  driveleech = requests.get(f"https://driveleech.org/zfile/{id}", headers=headers, allow_redirects=True)
  
  soup = BeautifulSoup(driveleech.text, 'html.parser')
  links = soup.find_all('a', href=True)
  
  for link in links:
      href_link = link['href']
      if href_link.endswith(".mkv"):
        return href_link

def get_mkv2(id):
  headers = {
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
      "Accept-Language": "en-GB,en;q=0.8",
      "Cache-Control": "max-age=0",
      "Connection": "keep-alive",
      "Content-Type": "text/html; charset=UTF-8",
      "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Brave";v="122"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": '"Windows"',
      "Sec-Fetch-Dest": "document",
      "Sec-Fetch-Mode": "navigate",
      "Sec-Fetch-Site": "none",
      "Sec-Fetch-User": "?1",
      "Upgrade-Insecure-Requests": "1",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  }

  driveleech = requests.get(f"https://driveleech.org/wfile/{id}", headers=headers, allow_redirects=True)
  
  pattern = '<a href="(/w.*?)" class="btn btn-outline-info"'
  isMatch, aResult = cParser.parse(driveleech.text, pattern)
  if not isMatch: return
  for link in aResult:
      driveleech = requests.get(f"https://driveleech.org{link}", headers=headers)
      soup = BeautifulSoup(driveleech.text, 'html.parser')
      links = soup.find_all('a', href=True)
      
      for link in links:
       href_link = link['href']
       if href_link.endswith(".mkv"):
           return href_link 


