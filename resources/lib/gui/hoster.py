# -*- coding: utf-8 -*-
# Python 3
#
# 24.01.23 - Heptamer: Korrektur getpriorities (nun werden alle Hoster gelesen und sortiert)

from resources.lib.tmdb import cTMDB
import xbmc
import xbmcgui 
import xbmcplugin
import resolveurl as resolver
from infotagger.listitem import ListItemInfoTag
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui
from resources.lib.config import cConfig
from resources.lib.player import cPlayer
from resources.lib.tools import logger


class cHosterGui:
    SITE_NAME = 'cHosterGui'

    def __init__(self):
        self.maxHoster = int(cConfig().getSetting('maxHoster', 100))
        self.dialog = False

    # TODO: unify parts of play, download etc.
    def _getInfoAndResolve(self, siteResult):
        oGui = cGui()
        params = ParameterHandler()
        # get data
        mediaUrl = params.getValue('sMediaUrl')
        fileName = params.getValue('MovieTitle')
        
        if params.getValue('mediaType')=='episode':
         value = cTMDB().get_meta_episodes( params.getValue('mediaType'), name=params.getValue('TVShowTitle'), tmdb_id=params.getValue('tmdbID'), season=params.getValue('season'),episode=params.getValue('episode'), advanced='true')
        else:
         value = cTMDB().get_meta( params.getValue('mediaType'), name=fileName, tmdb_id=params.getValue('tmdbID'), advanced='true')

        try:
            try:
                import resolveurl as resolver
            except:
                import urlresolver as resolver
            # resolve
            if siteResult:
                mediaUrl = siteResult.get('streamUrl', False)
                mediaId = siteResult.get('streamID', False)
                if mediaUrl:
                    logger.info('-> [hoster]: resolve: ' + mediaUrl)
                    link = mediaUrl if siteResult['resolved'] else resolver.resolve(mediaUrl)
                elif mediaId:
                    logger.info('-> [hoster]: resolve: hoster: %s - mediaID: %s' % (siteResult['host'], mediaId))
                    link = resolver.HostedMediaFile(host=siteResult['host'].lower(), media_id=mediaId).resolve()
                else:
                    oGui.showError('Matrixv2', cConfig().getLocalizedString(30134), 5)
                    return False
            elif mediaUrl:
                logger.info('-> [hoster]: resolve: ' + mediaUrl)
                link = resolver.resolve(mediaUrl)
            else:
                oGui.showError('Matrixv2', cConfig().getLocalizedString(30134), 5)
                return False
        except resolver.resolver.ResolverError as e:
            logger.error('-> [hoster]: ResolverError: %s' % e)
            oGui.showError('Matrixv2', cConfig().getLocalizedString(30135), 7)
            return False
        # resolver response
        if link is not False:
            data = {'title': fileName, 'season': params.getValue('season'), 'episode': params.getValue('episode'), 'showTitle': params.getValue('TVShowTitle'), 'thumb': params.getValue('thumb'), 'link': link,'mediatype': params.getValue('mediaType'),'tmdb_id':params.getValue('tmdbID')}
            if value:
             data.update(value)
            return data
        return False

    def play(self, siteResult=False):
        data = self._getInfoAndResolve(siteResult)
        if not data:
            return False
        if self.dialog:
            try:
                self.dialog.close()
            except:
                pass

        logger.info('-> [hoster]: play file link: ' + str(data['link']))
        list_item = xbmcgui.ListItem(path=data['link'])
        videoInfoTag = list_item.getVideoInfoTag()
        videoInfoTag.setMediaType(data.get('mediatype', ""))
        videoInfoTag.setTvShowTitle(str(data.get('showTitle', "")))
        videoInfoTag.setTitle(data.get('title', ""))
        videoInfoTag.setOriginalTitle(data.get('originaltitle', ""))
        videoInfoTag.setUniqueIDs(data.get('tmdb_id', ""),'tmdb')
        videoInfoTag.setPlot(data.get('plot', ""))
        videoInfoTag.setPlotOutline(data.get('tagline', ""))
        videoInfoTag.setYear(int(data.get('year', 0)))
        videoInfoTag.setRating(float(data.get('rating', 0.0)))
        videoInfoTag.setMpaa(data.get('mpaa', ""))
        videoInfoTag.setDuration(int(data.get('duration', 0)))
        videoInfoTag.setPlaycount(int(data.get('playcount', 0)))
        videoInfoTag.setTrailer(data.get('trailer', ""))
        videoInfoTag.setTagLine(data.get('tagline', ""))
        videoInfoTag.setStudios(list(data.get('studio', '').split("/")))
        videoInfoTag.setWriters(list(data.get('writer', '').split("/")))
        videoInfoTag.setDirectors(list(data.get('director', '').split("/")))
        videoInfoTag.setGenres(''.join(data.get('genre', [""])).split('/'))
        videoInfoTag.setSeason(int(data.get('season', 0)))
        videoInfoTag.setEpisode(int(data.get('episode', 0)))
        videoInfoTag.setResumePoint(float(data.get('resumetime', 0.0)), float(data.get('totaltime', 0.0)))
        list_item.setArt({'poster': data.get('cover_url'),
                           'thumb': data.get('cover_url'),
                           'icon': data.get('cover_url'),
                          'fanart': data.get('backdrop_url')})
        list_item.setProperty('IsPlayable', 'true')
        if cGui().pluginHandle > 0:
            xbmcplugin.setResolvedUrl(cGui().pluginHandle, True, list_item)
        else:
            xbmc.Player().play(data['link'], list_item)
        return cPlayer().startPlayer()

    def addToPlaylist(self, siteResult=False):
        oGui = cGui()
        logger.info('-> [hoster]: attempt addToPlaylist')
        data = self._getInfoAndResolve(siteResult)
        if not data: return False
        logger.info('-> [hoster]: addToPlaylist file link: ' + str(data['link']))
        oGuiElement = cGuiElement()
        oGuiElement.setSiteName(self.SITE_NAME)
        oGuiElement.setMediaUrl(data['link'])
        oGuiElement.setTitle(data['title'])
        if data['thumb']:
            oGuiElement.setThumbnail(data['thumb'])
        if data['showTitle']:
            oGuiElement.setEpisode(data['episode'])
            oGuiElement.setSeason(data['season'])
            oGuiElement.setTVShowTitle(data['showTitle'])
        if self.dialog:
            self.dialog.close()
        oPlayer = cPlayer()
        oPlayer.addItemToPlaylist(oGuiElement)
        oGui.showInfo(cConfig().getLocalizedString(30136), cConfig().getLocalizedString(30137), 5)
        return True

    def download(self, siteResult=False):
        from resources.lib.download import cDownload
        logger.info('-> [hoster]: attempt download')
        data = self._getInfoAndResolve(siteResult)
        if not data: return False
        logger.info('-> [hoster]: download file link: ' + data['link'])
        if self.dialog:
            self.dialog.close()
        oDownload = cDownload()
        oDownload.download(data['link'], data['title'])
        return True

    def sendToPyLoad(self, siteResult=False):
        from resources.lib.handler.pyLoadHandler import cPyLoadHandler
        logger.info('-> [hoster]: attempt download with pyLoad')
        data = self._getInfoAndResolve(siteResult)
        if not data: return False
        cPyLoadHandler().sendToPyLoad(data['title'], data['link'])
        return True

    def sendToJDownloader(self, sMediaUrl=False):
        from resources.lib.handler.jdownloaderHandler import cJDownloaderHandler
        params = ParameterHandler()
        if not sMediaUrl:
            sMediaUrl = params.getValue('sMediaUrl')
        if self.dialog:
            self.dialog.close()
        logger.info('-> [hoster]: call send to JDownloader: ' + sMediaUrl)
        cJDownloaderHandler().sendToJDownloader(sMediaUrl)

    def sendToJDownloader2(self, sMediaUrl=False):
        from resources.lib.handler.jdownloader2Handler import cJDownloader2Handler
        params = ParameterHandler()
        if not sMediaUrl:
            sMediaUrl = params.getValue('sMediaUrl')
        if self.dialog:
            self.dialog.close()
        logger.info('-> [hoster]: call send to JDownloader2: ' + sMediaUrl)
        cJDownloader2Handler().sendToJDownloader2(sMediaUrl)

    def sendToMyJDownloader(self, sMediaUrl=False, sMovieTitle='Matrixv2'):
        from resources.lib.handler.myjdownloaderHandler import cMyJDownloaderHandler
        params = ParameterHandler()
        if not sMediaUrl:
            sMediaUrl = params.getValue('sMediaUrl')
        sMovieTitle = params.getValue('MovieTitle')
        if not sMovieTitle:
            sMovieTitle = params.getValue('Title')
        if not sMovieTitle:  # only temporary
            sMovieTitle = params.getValue('sMovieTitle')
        if not sMovieTitle:
            sMovieTitle = params.getValue('title')
        if self.dialog:
            self.dialog.close()
        logger.info('-> [hoster]: call send to My.JDownloader: ' + sMediaUrl)
        cMyJDownloaderHandler().sendToMyJDownloader(sMediaUrl, sMovieTitle)

    def __getPriorities(self, hosterList, filter=True):
        # Sort hosters based on their resolvers priority.
        ranking = []
        # handles multihosters but is about 10 times slower
        for hoster in hosterList:

            # we try to load resolveurl within the loop, making sure that the resolver loads new with every cycle
            try:
                import resolveurl as resolver
            except:
                import urlresolver as resolver
                 
            # accept hoster which is marked as resolveable by sitePlugin
            if hoster.get('resolveable', False):
                ranking.append([0, hoster])
                continue
             
            try:
                # serienstream VOE hoster = {'link': [sUrl, sName], aus array "[0]" True bzw. False
                link = hoster['link'][0] if isinstance(hoster['link'], list) else hoster['link']
                hmf = resolver.HostedMediaFile(url=link)
                #hmf = resolver.HostedMediaFile(url=hoster['link'])
            except:
                continue

            if not hmf.valid_url():
                hmf = resolver.HostedMediaFile(host=hoster['name'].lower(), media_id='dummy')

            if len(hmf.get_resolvers()):
                priority = False
                for resolver in hmf.get_resolvers():
                    # prefer individual priority
                    if not resolver.isUniversal():
                        priority = resolver._get_priority()
                        break
                    if not priority:
                        priority = resolver._get_priority()
                if priority:
                    ranking.append([priority, hoster])
            elif not filter:
                ranking.append([999, hoster])

            # Reset resolver so we have a fresh instance when loop starts again
            del(resolver) 

        if any('quality' in hoster[1] for hoster in ranking):
            try:
                # Sortiere Hoster nach Qualität (cConfig().getSetting('preferedQuality') == '5')
                pref_quali = cConfig().getSetting('preferedQuality')
                if pref_quali != '5' and any('quality' in hoster[1] and int(hoster[1]['quality']) == int(pref_quali) for hoster in ranking):
                    ranking = sorted(ranking, key=lambda hoster: int('quality' in hoster[1] and hoster[1]['quality']) == int(pref_quali), reverse=True)
                else:
                # Sortiere Hoster nach Priorität
                    ranking = sorted(ranking, key=lambda hoster: 'quality' in hoster[1] and int(hoster[1]['quality']), reverse=True)
            except:
                pass
        # After sorting Quality, we sort for Hoster-Priority :) -Hep 24.01.23
        # ranking = sorted(ranking, key=lambda ranking: ranking[0])
        
        # Sprache als Prio hinzugefügt DWH 07.02.23 THX Cubikon
        if ranking:
            if  "languageCode" in ranking[0][1]:
                ranking = sorted(ranking, key=lambda ranking: (ranking[1]["languageCode"],ranking[0]))
            else:
                ranking = sorted(ranking, key=lambda ranking: ranking[0])
        
        
        hosterQueue = []
        
        for i, hoster in ranking:
            hosterQueue.append(hoster)
        return hosterQueue

    def stream(self, playMode, siteName, function, url):
        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create('Matrixv2', cConfig().getLocalizedString(30138))
        # load site as plugin and run the function
        self.dialog.update(5, cConfig().getLocalizedString(30139))
        plugin = __import__(siteName, globals(), locals())
        function = getattr(plugin, function)
        self.dialog.update(10, cConfig().getLocalizedString(30140))
        if url:
            siteResult = function(url)
        else:
            siteResult = function()
        self.dialog.update(40)
        if not siteResult:
            self.dialog.close()
            cGui().showInfo('Matrixv2', cConfig().getLocalizedString(30141))
            return
        # if result is not a list, make in one
        if not type(siteResult) is list:
            temp = [siteResult]
            siteResult = temp
        # field "name" marks hosters
        if 'name' in siteResult[0]:
            functionName = siteResult[-1]
            del siteResult[-1]
            if not siteResult:
                self.dialog.close()
                cGui().showInfo('Matrixv2', cConfig().getLocalizedString(30142))
                return

            self.dialog.update(60, cConfig().getLocalizedString(30143))
            # Für Sitplugin einfach.to mit in automatische Abspielliste aufnehmen (Da Links bei der Überprüfung der Verfügbarkeit gekickt werden)
            # if (playMode != 'jd') and (playMode != 'jd2') and (playMode != 'pyload') and (cConfig().getSetting('presortHoster') == 'true') and (playMode != 'myjd'):
            if (siteName != 'einfach') and (playMode != 'jd') and (playMode != 'jd2') and (playMode != 'pyload') and (cConfig().getSetting('presortHoster') == 'true') and (playMode != 'myjd'):
                siteResult = self.__getPriorities(siteResult)
            if not siteResult:
                self.dialog.close()
                cGui().showInfo('Matrixv2', cConfig().getLocalizedString(30144))
                return False
            self.dialog.update(90)
            # self.dialog.close()
            if len(siteResult) > self.maxHoster:
                siteResult = siteResult[:self.maxHoster - 1]
            if cConfig().getSetting('hosterSelect') == 'List':
                self.showHosterFolder(siteResult, siteName, functionName)
                return
            if len(siteResult) > 1:
                # choose hoster
                siteResult = self._chooseHoster(siteResult)
                if not siteResult:
                    return
            else:
                siteResult = siteResult[0]
            # get stream links
            logger.info(siteResult['link'])
            function = getattr(plugin, functionName)
            siteResult = function(siteResult['link'])
            # if result is not a list, make in one
            if not type(siteResult) is list:
                temp = [siteResult]
                siteResult = temp
        # choose part
        if len(siteResult) > 1:
            siteResult = self._choosePart(siteResult)
            if not siteResult:
                logger.info('-> [hoster]: no part selected')
                return
        else:
            siteResult = siteResult[0]

        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create('Matrixv2', cConfig().getLocalizedString(30145))
        self.dialog.update(95, cConfig().getLocalizedString(30146))
        if playMode == 'play':
            self.play(siteResult)
        elif playMode == 'download':
            self.download(siteResult)
        elif playMode == 'enqueue':
            self.addToPlaylist(siteResult)
        elif playMode == 'jd':
            self.sendToJDownloader(siteResult['streamUrl'])
        elif playMode == 'jd2':
            self.sendToJDownloader2(siteResult['streamUrl'])
        elif playMode == 'myjd':
            self.sendToMyJDownloader(siteResult['streamUrl'])
        elif playMode == 'pyload':
            self.sendToPyLoad(siteResult)

    def streamAuto(self, playMode, siteName, function):
        logger.info('-> [hoster]: auto stream initiated')
        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create('Matrixv2', cConfig().getLocalizedString(30138))
        # load site as plugin and run the function
        self.dialog.update(5, cConfig().getLocalizedString(30139))
        plugin = __import__(siteName, globals(), locals())
        function = getattr(plugin, function)
        self.dialog.update(10, cConfig().getLocalizedString(30140))
        siteResult = function()
        if not siteResult:
            self.dialog.close()
            cGui().showInfo('Matrixv2', cConfig().getLocalizedString(30141))
            return False
        # if result is not a list, make in one
        if not type(siteResult) is list:
            temp = [siteResult]
            siteResult = temp
        # field "name" marks hosters
        if 'name' in siteResult[0]:
            self.dialog.update(90, cConfig().getLocalizedString(30143))
            functionName = siteResult[-1]
            del siteResult[-1]
            # Sitplugin einfach.to bei self.__getPriorities(siteResult) ausschliessen da sonst die Hoster gekickt werden.
            if siteName == 'einfach':
                hosters = siteResult
            else:
                hosters = self.__getPriorities(siteResult)
            #hosters = self.__getPriorities(siteResult)
            if not hosters:
                self.dialog.close()
                cGui().showInfo('Matrixv2', cConfig().getLocalizedString(30144))
                return False
            if len(siteResult) > self.maxHoster:
                siteResult = siteResult[:self.maxHoster - 1]
            check = False
            self.dialog.create('Matrixv2', cConfig().getLocalizedString(30147))
            total = len(hosters)
            for count, hoster in enumerate(hosters):
                if self.dialog.iscanceled() or xbmc.Monitor().abortRequested() or check: return
                percent = (count + 1) * 100 // total
                try:
                    logger.info('-> [hoster]: try hoster %s' % hoster['name'])
                    self.dialog.create('Matrixv2', cConfig().getLocalizedString(30147))
                    self.dialog.update(percent, cConfig().getLocalizedString(30147) + ' %s' % hoster['name'])
                    # get stream links
                    function = getattr(plugin, functionName)
                    siteResult = function(hoster['link'])
                    check = self.__autoEnqueue(siteResult, playMode)
                    if check:
                        return True
                except:
                    self.dialog.update(percent, cConfig().getLocalizedString(30148) % hoster['name'])
                    logger.error('-> [hoster]: playback with hoster %s failed' % hoster['name'])
        # field "resolved" marks streamlinks
        elif 'resolved' in siteResult[0]:
            for stream in siteResult:
                try:
                    if self.__autoEnqueue(siteResult, playMode):
                        self.dialog.close()
                        return True
                except:
                    pass

    def _chooseHoster(self, siteResult):
        dialog = xbmcgui.Dialog()
        titles = []
        for result in siteResult:
            if 'displayedName' in result:
                titles.append(str(result['displayedName']))
            else:
                titles.append(str(result['name']))
        index = dialog.select(cConfig().getLocalizedString(30149), titles)
        if index > -1:
            siteResult = siteResult[index]
            return siteResult
        else:
            logger.info('-> [hoster]: no hoster selected')
            return False

    def _choosePart(self, siteResult):
        self.dialog = xbmcgui.Dialog()
        titles = []
        for result in siteResult:
            titles.append(str(result['title']))
        index = self.dialog.select(cConfig().getLocalizedString(30150), titles)
        if index > -1:
            siteResult = siteResult[index]
            return siteResult
        else:
            return False

    def showHosterFolder(self, siteResult, siteName, functionName):
        oGui = cGui()
        total = len(siteResult)
        params = ParameterHandler()
        for hoster in siteResult:
            if 'displayedName' in hoster:
                name = hoster['displayedName']
            else:
                name = hoster['name']
            oGuiElement = cGuiElement(name, siteName, functionName)
            oGuiElement.setThumbnail(str(params.getValue('thumb')))
            params.setParam('url', hoster['link'])
            params.setParam('isHoster', 'true')
            oGui.addFolder(oGuiElement, params, iTotal=total, isHoster=True)
        oGui.setEndOfDirectory()

    def __autoEnqueue(self, partList, playMode):
        # choose part
        if not partList:
            return False
        for i in range(len(partList) - 1, -1, -1):
            try:
                if playMode == 'play' and i == 0:
                    if not self.play(partList[i]):
                        return False
                elif playMode == 'download':
                    self.download(partList[i])
                elif playMode == 'enqueue' or (playMode == 'play' and i > 0):
                    self.addToPlaylist(partList[i])
            except:
                return False
        logger.info('-> [hoster]: autoEnqueue successful')
        return True

    
class Hoster:
    def __init__(self, name, link):
        self.name = name
        self.link = link