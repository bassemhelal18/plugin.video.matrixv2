# -*- coding: utf-8 -*-


import os
import json
import time
import re
import requests
import xbmcaddon
from urllib.parse import quote, unquote, urljoin, urlsplit
from resources.lib import common
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from bs4 import BeautifulSoup
from six.moves import urllib_parse

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
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'uhdmovies.ceo')
URL_MAIN = 'https://' + DOMAIN + '/'


URL_MOVIES_English = URL_MAIN + 'movies/'
URL_SERIES_English = URL_MAIN + 'web-series/'

URL_SEARCH = URL_MAIN + 'search/%s'

#ToDo Serien auch auf reinen Filmseiten, prüfen ob Filterung möglich
def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    params.setParam('trumb', os.path.join(ART, 'Recent.png'))
    cGui().addFolder(cGuiElement('Recent', SITE_IDENTIFIER, 'showEntries'), params)
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
    
    
    
    pattern = r'<div class="entry-image">.*?<a href="(.*?)" title="Download (.*?) \((.*?)\).*?".*?src="(.*?)"'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return
    itemList =[]
    total = len(aResult)
    for sUrl, sName, sYear, sThumbnail  in aResult:
        sName = sName.strip()
        if sSearchText and sSearchText.casefold() not in sName.casefold():
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
               if not isTvshow:
                isTvshow, aResult = cParser.parse(unquote(sUrl),'-s0')
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
    
    isMatch, aResult = cParser.parse(sHtmlContent, '''((?:<strong>|<b>)((?:Season|SEASON|season).*?)(?:</strong>|</b>))''')
    if  isMatch:
      total = len(aResult)
      for seasonprase,sSeason in aResult:
        
        sSeason = sSeason.lower().replace('season','').strip()
        oGuiElement = cGuiElement('Season'+' ' +sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('season')
        params.setParam('sUrl', sUrl)
        params.setParam('sSeasonprase', seasonprase)
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
    sSeasonprase = params.getValue('sSeasonprase')
    sShowName = params.getValue('sName')
    
    
    
    sStart = f'{sSeasonprase}<'
    sEnd = '<p style="text-align: center;"><div class="mks_separator" style="border-bottom: 5px solid;">'
    sHtmlContent0 = cParser.abParse(sHtmlContent, sStart, sEnd)
    
    if sStart in sHtmlContent0:
     if 'Choose Episode Number to Download' not in sHtmlContent0:
      sStart = f'{sSeasonprase}<'
      sEnd = '<div class="gridlove-author">'
      sHtmlContent0 = cParser.abParse(sHtmlContent, sStart, sEnd)
     s = BeautifulSoup(sHtmlContent0, 'html.parser')
     episode_links = {}
     for link in s.find_all('a', class_='maxbutton-gdrive-episode'):
       episode_number = link.find('span', class_='mb-text').text.strip()
       episode_url = link.get('href')
    
       if episode_number not in episode_links:
           episode_links[episode_number] = []
       episode_links[episode_number].append(episode_url)
     pattern = '''['"]Episode (.*?)['"]:.*?'(.*?)']'''  # start element
     isMatch, aResult = cParser.parse(str(episode_links), pattern)
     if not isMatch: return
     total = len(aResult)
     for sEpisode,sUrl in aResult:
        
         sEpisode = sEpisode.replace('Episode','').strip()
         
         oGuiElement = cGuiElement('Episode ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
         oGuiElement.setTVShowTitle(sShowName)
         oGuiElement.setSeason(sSeason)
         oGuiElement.setEpisode(sEpisode)
         oGuiElement.setMediaType('episode')
         params.setParam('sUrl', sUrl)
         cGui().addFolder(oGuiElement, params, False, total)
    else:
        
     s = BeautifulSoup(sHtmlContent, 'html.parser')
     episode_links = {}
     for link in s.find_all('a', class_='maxbutton-gdrive-episode'):
       episode_number = link.find('span', class_='mb-text').text.strip()
       episode_url = link.get('href')
    
       if episode_number not in episode_links:
           episode_links[episode_number] = []
       episode_links[episode_number].append(episode_url)
     pattern = '''['"]Episode (.*?)['"]:.*?'(.*?)']'''  # start element
     isMatch, aResult = cParser.parse(str(episode_links), pattern)
     if not isMatch: return
     total = len(aResult)
     for sEpisode,sUrl in aResult:
        
         sEpisode = sEpisode.replace('Episode','').strip()
         
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
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sType = params.getValue('mediaType')
    hosters = []
    if sType == 'movie':
        sHtmlContent = cRequestHandler(sUrl).request()
        soup = BeautifulSoup(sHtmlContent, 'html.parser')
        for link in soup.find_all('a', class_='maxbutton-download-g-drive', href=True):
            # Quality descriptions are strong/p blocks, not h3 headings.
            sRes = link.get_text(' ', strip=True)
            for heading in link.find_all_previous(['strong', 'p', 'h3', 'h4', 'h5']):
                label = heading.get_text(' ', strip=True)
                if re.search(r'\b(?:2160|1080|720|480)p\b|\b4K\b', label, re.I):
                    quality = re.search(r'\b(?:2160|1080|720|480)p\b|\b4K\b', label, re.I)
                    sRes = label[quality.start():]
                    break
            hosters.append({'link': link['href'], 'name': 'UHDMovies',
                            'displayedName': sRes, 'resolveable': True})
    elif sUrl:
        hosters.append({'link': sUrl, 'name': 'UHDMovies',
                        'displayedName': 'Episode', 'resolveable': True})
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getheader(url):
    sRefer = '{}'.format(cParser.urlparse(url))
    sRefer = sRefer.lower()
    headers = {'User-Agent': common.RAND_UA,
               'Referer': 'https://{0}/'.format(sRefer),
               'Origin': 'https://{0}'.format(sRefer)}
    
    return '|%s' % '&'.join(['%s=%s' % (key, urllib_parse.quote_plus(headers[key])) for key in headers])    

def make_post_request(_wp_http):
    # Keep the original helper chain, but use this link's current landing form.
    session = requests.Session()
    try:
        response = session.get(_wp_http, timeout=(5, 20))
        response.raise_for_status()
        origin = urlsplit(response.url).netloc
        if origin != 'en.thenaukriadda.in':
            raise ValueError('Unknown link intermediary')
        form = BeautifulSoup(response.text, 'html.parser').find('form', id='lp-land')
        action_url = urljoin(response.url, form['action'])
        if urlsplit(action_url).netloc != origin:
            raise ValueError('Unknown landing target')
        fields = {i['name']: i.get('value', '') for i in form.select('input[name]')}
        response = session.post(action_url, data=fields, headers={'Referer': response.url}, timeout=(5, 20))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', id='lp-s1-form')
        action_url = urljoin(response.url, form['action'])
        timer = int(soup.find(id='lp-timer-s1').get_text(strip=True))
        if urlsplit(action_url).netloc != origin or not 0 <= timer <= 30:
            raise ValueError('Changed continuation form')
        time.sleep(timer)
        fields = {i['name']: i.get('value', '') for i in form.select('input[name]')}
        token = {'session': session, 'fields': fields, 'referer': response.url, 'origin': origin}
        return action_url, fields.get('_lp_http2', ''), token
    except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError):
        session.close()
        return None, None, None


def get_pepe_url(action_url, _wp_http2, token):
    if not action_url or not token:
        return ''
    try:
        response = token['session'].post(action_url, data=token['fields'],
                                        headers={'Referer': token['referer']}, timeout=(5, 20))
        response.raise_for_status()
        duration = re.search(r'\bdur\s*=\s*(\d+)', response.text)
        cookie = re.search(r'\bsc\(("(?:[^"\\]|\\.)*"),("(?:[^"\\]|\\.)*"),60\)', response.text)
        if not duration or not cookie or not 0 <= int(duration.group(1)) <= 30:
            raise ValueError('Changed link generation')
        name, value = json.loads(cookie.group(1)), json.loads(cookie.group(2))
        if not re.fullmatch(r'lp-[a-zA-Z0-9]+', name):
            raise ValueError('Changed routing data')
        token['session'].cookies.set(name, value, domain=token['origin'], path='/')
        time.sleep(int(duration.group(1)))
        return response.text
    except (requests.RequestException, ValueError, TypeError, KeyError):
        token['session'].close()
        return ''


def get_match(resp):
    match = re.search(r"setAttribute\('href',\s*(\"(?:[^\"\\]|\\.)*\")\)", resp or '')
    if match:
        try:
            url = json.loads(match.group(1))
            if urlsplit(url).scheme == 'https' and urlsplit(url).netloc == 'en.thenaukriadda.in' and urlsplit(url).query.startswith('lp_go='):
                return [url]
        except ValueError:
            pass
    return []


def make_get_request(url, cookies, ref):
    if not cookies:
        return ''
    try:
        response = cookies['session'].get(url, headers={'Referer': ref}, timeout=(5, 20))
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ''
    finally:
        cookies['session'].close()


def parse_redirect_page(html):
    match = re.search(r'<meta\s+http-equiv="refresh"\s+content="0;url=(.*?)"\s*/?>', html or '')
    if match:
        url = match.group(1)
    else:
        match = re.search(r'window\.location\.replace\(("(?:[^"\\]|\\.)*")\);\},(\d+)\)', html or '')
        if not match or int(match.group(2)) > 30000:
            return None
        time.sleep(int(match.group(2)) / 1000.0)
        try:
            url = json.loads(match.group(1))
        except ValueError:
            return None
    if urlsplit(url).scheme == 'https' and urlsplit(url).netloc in ('driveseed.org', 'driveleech.org'):
        return url
    return None


def get_zfile(url):
  if not url: return None
  Request=cRequestHandler(url)
  Request.addHeaderEntry("Referer", "https://driveleech.org/")
  Request.addHeaderEntry("Origin", "https://driveleech.org")
  response = Request.request()
  
  pattern = r'/file/([a-zA-Z0-9]+)'
  matches = re.search(pattern, response)

  if matches:
      file_id = matches.group(1)
      print("File ID:", file_id)
      return file_id
  else:
      print("File ID not found.")
      return None


def getHosterUrl(sUrl=False):
    streams = []
    if not sUrl:
        return [{'streamUrl': '', 'resolved': True}]
    # Prepare only the chosen quality, then retain both original MKV branches.
    action_url, _wp_http2, token = make_post_request(sUrl)
    resp = get_pepe_url(action_url, _wp_http2, token)
    matches = get_match(resp)
    if matches:
        response = make_get_request(matches[0], token, action_url)
        final_url = parse_redirect_page(response)
        file_id = get_zfile(final_url)
        for extractor in (get_mkv, get_mkv2):
            res, sRes = extractor(file_id)
            if res is not None:
                streams.append({'streamUrl': urllib_parse.quote(res, '/:=&?') + getheader(res),
                                'resolved': True})
    elif token:
        token['session'].close()
    # The host framework indexes the result even when unavailable.
    return streams or [{'streamUrl': '', 'resolved': True}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % quote(sSearchText, safe=''), oGui, sSearchText)

def get_mkv(id):
  if not id: return None,None
  Request=cRequestHandler(f"https://driveseed.org/zfile/{id}")
  Request.addHeaderEntry("Referer", f"https://driveseed.org/file/{id}")
  Request.addHeaderEntry("Origin", "https://driveseed.org")
  response = Request.request()
       
  pattern = r'<meta property="og:title" content=".*?((?:2160p|1080p|720p).*?)\.mkv.*?"/>'
  isMatch, aResult = cParser.parse(response, pattern)
  if not isMatch: return None,None
  for sRes in aResult:
   sRes = sRes
  
  pattern = r'class="text-center">.*?<a href="([^"]+\.mkv)["]'
  isMatch, aResult = cParser.parse(response, pattern)
  if not isMatch:
    pattern = r'iframe id.*?src=".*?link=([^"]+\.mkv)"'
    isMatch, aResult = cParser.parse(response, pattern)
    if not isMatch: return None,None
  for link in aResult:
      href_link = link.strip()
      if href_link.endswith(".mkv"):
        href_link = href_link.replace(' ','.')
        return href_link,sRes
      else : return None, None
        

def get_mkv2(id):
  if not id: return None,None
  Request=cRequestHandler(f"https://driveseed.org/wfile/{id}")
  Request.addHeaderEntry("Referer", "https://driveseed.org/")
  Request.addHeaderEntry("Origin", "https://driveseed.org")
  response = Request.request()
  
  pattern = r'<meta property="og:title" content=".*?((?:2160p|1080p|720p).*?)\.mkv.*?"/>'
  isMatch, aResult = cParser.parse(response, pattern)
  if not isMatch: return None,None
  for sRes in aResult:
   sRes = sRes
  
  pattern = 'href="(/w.*?)" class="btn btn-outline-info"'
  isMatch, aResult = cParser.parse(response, pattern)
  if not isMatch: return None,None
  for link in aResult:
      
      Request=cRequestHandler(f"https://driveseed.org{link}")
      Request.addHeaderEntry("Referer", "https://driveseed.org/")
      Request.addHeaderEntry("Origin", "https://driveseed.org")
      response = Request.request()
      
   
  soup = BeautifulSoup(response, 'html.parser')
  links = soup.find_all('a',href =True)
  pattern = '''download.*?href=["'](https.*?.mkv)["']'''
  isMatch, aResult = cParser.parse(str(links), pattern)
  if not isMatch: return None,None
  for link in aResult:
    href_link = link.strip()
    if 'https://driveleech.org' in href_link:continue
    if href_link.endswith(".mkv"):
        href_link = href_link.replace(' ','.')
        return href_link,sRes
  else : return None, None

