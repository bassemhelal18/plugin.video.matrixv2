# -*- coding: utf-8 -*-
# Python 3

import xbmc
from resources.lib.gui.gui import cGui
from resources.lib.config import cConfig
from xbmc import LOGINFO as LOGNOTICE, LOGERROR, LOGWARNING, log, executebuiltin, getCondVisibility, getInfoLabel

LOGMESSAGE = cConfig().getLocalizedString(30166)


class Matrixv2Player(xbmc.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.streamFinished = False
        self.streamSuccess = True
        self.playedTime = 0
        self.totalTime = 999999
        self.from_global_search = False  # Track if started from Global Search
        log(cConfig().getLocalizedString(30166) + ' -> [player]: player instance created', LOGNOTICE)

    def onPlayBackStarted(self):
        log(cConfig().getLocalizedString(30166) + ' -> [player]: starting Playback', LOGNOTICE)
        try:
            self.totalTime = self.getTotalTime()
        except:
            self.totalTime = 999999

        # Detect if playback started from Global Search
        try:
            path = xbmc.getInfoLabel('Container.FolderPath')
            if path:
                low = path.lower()
                keywords = [
                    'function=globalsearch',
                    'site=globalsearch',
                    'function=searchalter',
                    'function=searchtmdb'
                ]
                if any(kw in low for kw in keywords):
                    self.from_global_search = True
                    log(cConfig().getLocalizedString(30166) + ' -> [player]: Detected Global Search context', LOGNOTICE)
        except:
            pass

    def onPlayBackStopped(self):
        log(LOGMESSAGE + ' -> [player]: Playback stopped', LOGNOTICE)
        if self.playedTime == 0 and self.totalTime == 999999:
            self.streamSuccess = False
            log(LOGMESSAGE + ' -> [player]: Kodi failed to open stream', LOGERROR)
        self.streamFinished = True
        # After playback ends, if we came from Global Search → return to main menu
        if self.from_global_search:
            try:
                xbmc.executebuiltin('Container.Update(plugin://plugin.video.matrixv2/)')
                log('Matrixv2 -> [player]: Returning to addon main menu after Global Search', LOGNOTICE)
            except Exception as e:
                log('Matrixv2 -> [player]: Failed to return to main menu: %s' % str(e), LOGERROR)


    def onPlayBackEnded(self):
        log(LOGMESSAGE + ' -> [player]: Playback completed', LOGNOTICE)
        self.onPlayBackStopped()


class cPlayer:
    def clearPlayList(self):
        oPlaylist = self.__getPlayList()
        oPlaylist.clear()

    def __getPlayList(self):
        return xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

    def addItemToPlaylist(self, oGuiElement):
        oListItem = cGui().createListItem(oGuiElement)
        self.__addItemToPlaylist(oGuiElement, oListItem)

    def __addItemToPlaylist(self, oGuiElement, oListItem):
        oPlaylist = self.__getPlayList()
        oPlaylist.add(oGuiElement.getMediaUrl(), oListItem)

    def startPlayer(self):
        log(LOGMESSAGE + ' -> [player]: start player', LOGNOTICE)
        xbmcPlayer = Matrixv2Player()
        monitor = xbmc.Monitor()
        while (not monitor.abortRequested()) & (not xbmcPlayer.streamFinished):
            if xbmcPlayer.isPlayingVideo():
                xbmcPlayer.playedTime = xbmcPlayer.getTime()
            monitor.waitForAbort(10)
        return xbmcPlayer.streamSuccess
