#!/usr/bin/env python
"""
originally adapted from:
http://stackoverflow.com/questions/4163740/qtreeview-with-drag-and-drop-support-in-pyqt?rq=1

and:
http://kylemr.blogspot.com/2013/04/pyqt-drag-and-drop-outliner-like.html

great video tutorials on Model View programming in Qt/PyQt/PySide:
http://www.yasinuludag.com/blog/?p=98

When searching for documentation on PySide, it's OK to look for PyQt too... they're mostly equivalent.

/c/alpha/pyside/drag_and_drop-tree.py


Medley

Tree of Lists

also [2014.10.08 12:34:24]
migrating this version to use VLC wrapper directly, rather than phonon layer.
difficulty getting phonon to use VLC back end.

"""

import sys, os
import platform

import PySide
from PySide import QtGui, QtCore
#from PySide.phonon import Phonon
import vlc
    
from medley.helpers import load_json, save_json

#from content_view import ContentWindow
#from playlists_view import PlaylistsTreeView, Node, TreeModel
from list_tree import PlaylistsTreeView, Node, TreeModel
#from playlist_view import PlaylistView, PlaylistModel
from playlist_view import PlaylistWidget, PlaylistModel

#from shared import main_player
from shared import cli_items

__version__ = '0.0.1'


#main window global:
main_window = None
main_player = None

class PlayerWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(PlayerWidget, self).__init__(parent)

        #a place to keep track of fullscreen status
        #should not start out in full
        self.fullscreen = False

        # creating a basic vlc instance
        self.Instance = vlc.Instance()
        # creating an empty vlc media player
        self.MediaPlayer = self.Instance.media_player_new()

        #self.audio = Phonon.AudioOutput(Phonon.MusicCategory, self)
        #self.player = Phonon.MediaObject(self)
        #Phonon.createPath(self.player, self.audio)

        #not sure if VLC library sends regular tick signals:
        #self.player.setTickInterval(1000)
        #self.connect(self.player, QtCore.SIGNAL("tick(qint64)"), self.tick)

        #so try this:
        #http://srinikom.github.io/pyside-docs/PySide/QtCore/QTimer.html#PySide.QtCore.QTimer
        ## timer = QtCore.QTimer(self)
        ## self.connect(timer, QtCore.SIGNAL("tick(qint64)"), self.tick)
        ## #check every second:
        ## timer.start(1000)

        #yup... this is how the sample does it too:
        self.Timer = QtCore.QTimer(self)
        self.Timer.setInterval(200)
        self.connect(self.Timer, QtCore.SIGNAL("timeout()"),
                     self.updateUI)

        
    
        #self.prev_button = QtGui.QPushButton("Prev", self)
        self.prev_button = QtGui.QPushButton("", self)
        self.prev_button.setIcon(QtGui.QIcon("images/prev.png"))
        self.prev_button.setIconSize(QtCore.QSize(20, 20))

        self.prev_button.clicked.connect(self.previous)

        #self.play_button = QtGui.QPushButton("Play", self)
        self.play_button = QtGui.QPushButton("", self)
        self.play_button.setCheckable(True)
        self.play_button.setIcon(QtGui.QIcon("images/play.png"))
        self.play_button.setIconSize(QtCore.QSize(40, 40))
        self.play_button.setEnabled(False)

        #self.connect(self.play_button, QtCore.SIGNAL("clicked()"), self.toggle_play)
        self.play_button.clicked[bool].connect(self.toggle_play)

        #self.pauseButton=QtGui.QPushButton("Pause")
        #self.pauseButton.setIcon(QtGui.QIcon("images/pause.png"))

        #self.stopButton=QtGui.QPushButton("Stop")
        #self.stopButton.setIcon(QtGui.QIcon("images/stop.png"))
        
        #self.next_button = QtGui.QPushButton("Next", self)
        self.next_button = QtGui.QPushButton("", self)
        self.next_button.setIcon(QtGui.QIcon("images/next.png"))
        self.next_button.setIconSize(QtCore.QSize(20, 20))

        self.next_button.clicked.connect(self.next)

        row1 = QtGui.QHBoxLayout()
        row1.addWidget(self.prev_button)
        row1.addWidget(self.play_button)
        row1.addWidget(self.next_button)

        #self.seek_bar = Phonon.SeekSlider(self.player, self)

        self.seek_bar = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.seek_bar.setToolTip("Position")
        self.seek_bar.setMaximum(1000)
        self.connect(self.seek_bar,
                     QtCore.SIGNAL("sliderMoved(int)"), self.setPosition)
        

        row2 = QtGui.QHBoxLayout()
        row2.addWidget(self.seek_bar)

        self.time_passed = QtGui.QLabel("00:00", self)
        self.time_remain = QtGui.QLabel("-00:00", self)

        #self.volume_slider = Phonon.VolumeSlider(self.audio, self)

        self.volume_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.MediaPlayer.audio_get_volume())
        self.volume_slider.setToolTip("Volume")
        self.connect(self.volume_slider,
                     QtCore.SIGNAL("valueChanged(int)"),self.set_volume)


        row3 = QtGui.QHBoxLayout()
        row3.addWidget(self.time_passed)
        row3.addWidget(self.volume_slider)
        row3.addWidget(self.time_remain)
        #row3.insertStretch(1, 50)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)

        self.setLayout(layout)
        self.seek_bar.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)

        #available once Seekable state changes:
        #http://srinikom.github.io/pyside-docs/PySide/phonon/Phonon.MediaObject.html
        #self.player.hasVideoChanged[bool].connect(self.update_position)
        #doesn't seem to call update_position for player
        #self.player.seekableChanged[bool].connect(self.update_position)


        self.video_window = None
        self.check_video()


        self.cur_content = None
        self.cur_playlist = None

        self.selected_content = None
        self.selected_playlist = None

        self.play_state = "paused"
        self.rate = 1.0


    def open_window(self):
        """
        opens the main video window
        """
        self.video_window = QtGui.QMainWindow(self)
        #self.video_window = ContentWindow(self)

        #self.widget = MainWidget(self)

        #self.setLayout(self.layout)


        #playbackMenu = self.video_window.menuBar().addMenu("&Playback")

        ## playAction = QtGui.QAction('Play', self.video_window)
        ## playAction.setShortcut(' ')
        ## playAction.setStatusTip('Toggle Play / Pause of Player')        
        ## playAction.triggered.connect(self.toggle_play)
        ## playAction.setIconVisibleInMenu(False)
        ## #playbackMenu.addAction(playAction)

        plays = QtGui.QShortcut(QtGui.QKeySequence(" "), self.video_window,
                               self.toggle_play)

        ## scanfAction = QtGui.QAction('Scan Forward', self.video_window)
        ## scanfAction.setShortcut('Alt+Right')
        ## scanfAction.setStatusTip('Seek Forward')        
        ## scanfAction.triggered.connect(self.forward)
        ## scanfAction.setIconVisibleInMenu(False)
        ## #playbackMenu.addAction(scanfAction)

        scanfs = QtGui.QShortcut(QtGui.QKeySequence('Alt+Right'),
                                self.video_window, self.forward)


        ## scanbAction = QtGui.QAction('Scan Back', self.video_window)
        ## scanbAction.setShortcut('Alt+Left')
        ## scanbAction.setStatusTip('Seek Back')        
        ## scanbAction.triggered.connect(self.back)
        ## scanbAction.setIconVisibleInMenu(False)
        ## #playbackMenu.addAction(scanbAction)

        scanbs = QtGui.QShortcut(QtGui.QKeySequence('Alt+Left'),
                                self.video_window, self.back)


        ## #Meta seems to be equivalent to Ctrl on Mac
        ## jumpfAction = QtGui.QAction('Jump Forward', self.video_window)
        ## jumpfAction.setShortcut('Ctrl+Right')
        ## jumpfAction.setStatusTip('Jump Forward')        
        ## jumpfAction.triggered.connect(self.jumpf)
        ## jumpfAction.setIconVisibleInMenu(False)
        ## #playbackMenu.addAction(jumpfAction)

        jumpfs = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Right'),
                                self.video_window, self.jumpf)

        ## jumpbAction = QtGui.QAction('Jump Back', self.video_window)
        ## jumpbAction.setShortcut('Ctrl+Left')
        ## jumpbAction.setStatusTip('Jump Back')        
        ## jumpbAction.triggered.connect(self.jumpb)
        ## jumpbAction.setIconVisibleInMenu(False)
        ## #playbackMenu.addAction(jumpbAction)

        jumpbs = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Left'),
                                self.video_window, self.jumpb)

        ## nextAction = QtGui.QAction('Next', self.video_window)
        ## nextAction.setShortcut('Alt+Down')
        ## nextAction.setStatusTip('Next Track')        
        ## nextAction.triggered.connect(self.next)
        ## nextAction.setIconVisibleInMenu(False)
        ## #playbackMenu.addAction(nextAction)

        slower = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+,'),
                                 self.video_window, self.slower)

        faster = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+.'),
                                 self.video_window, self.faster)


        nexts = QtGui.QShortcut(QtGui.QKeySequence('Alt+Down'),
                                self.video_window, self.next)
        nexts = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Down'),
                                self.video_window, self.next)

        fullscreen = QtGui.QShortcut(QtGui.QKeySequence('F'),
                                     self.video_window, self.toggle_full)


        ## prevAction = QtGui.QAction('Previous', self.video_window)
        ## prevAction.setShortcut('Alt+Up')
        ## prevAction.setStatusTip('Previous Track')        
        ## prevAction.triggered.connect(self.previous)
        ## prevAction.setIconVisibleInMenu(False)
        ## #playbackMenu.addAction(prevAction)

        prevs = QtGui.QShortcut(QtGui.QKeySequence('Alt+Up'),
                                self.video_window, self.previous)

        prevs2 = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Up'),
                                self.video_window, self.previous)



        #self.video = QtGui.QWidget(self)
        #self.setCentralWidget(self.Widget)

        self.VideoFrame = QtGui.QFrame()
        self.Palette = self.VideoFrame.palette()
        self.Palette.setColor (QtGui.QPalette.Window,
                               QtGui.QColor(0,0,0))
        self.VideoFrame.setPalette(self.Palette)
        self.VideoFrame.setAutoFillBackground(True)

        #self.VBoxLayout = QtGui.QVBoxLayout()
        #self.VBoxLayout.addWidget(self.VideoFrame)
        #self.video.setLayout(self.VBoxLayout)

        #self.video = Phonon.VideoWidget(self.video_window)
        #Phonon.createPath(self.player, self.video)

        #self.video_window.setCentralWidget(self.video)
        self.video_window.setCentralWidget(self.VideoFrame)

        #self.video_window.resize(840, 525)
        self.video_window.resize(960, 540)
        self.video_window.show()

    def toggle_full(self):
        if not self.fullscreen:
            #self.video_window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            self.video_window.showFullScreen()
            self.fullscreen = True
        else:
            self.video_window.showNormal()
            self.fullscreen = False
            
        

    def check_video(self):
        """
        make sure video window is open
        """

        if self.video_window is None:
            self.open_window()

        else:
            #even though actual window may have been deleted,
            #reference to it is kept around
            #we can check if the reference throws an error
            #in which case we can create a new window
            #seems a bit kludgey, but it works
            try:
                self.video_window.window()
            except:
                self.open_window()

        self.video_window.activateWindow()
        self.video_window.raise_() # just to be sure it's on top


    def toggle_play(self, pressed=None):
        """
        http://zetcode.com/gui/pysidetutorial/widgets/
        """
        #source = self.sender()

        if self.play_state == "playing":
            self.pause()
            self.play_state = "paused"
            self.play_button.setDown(False)

            #if pressed:
            self.play_button.setIcon(QtGui.QIcon("images/play.png"))
        else:
            self.play()
            #if pressed:
            #    #source.setText("Pause")
            self.play_button.setIcon(QtGui.QIcon("images/pause.png"))

            #self.play_state = "playing"
            #self.play_button.setDown(True)


        ## if pressed is None:
                
        ## elif pressed:
        ##     #source.setText("Pause")
        ##     self.play_button.setIcon(QtGui.QIcon("images/pause.png"))
        ##     self.play()
        ##     #self.play_state = "playing"

        ## else:
        ##     #source.setText("Play")
        ##     self.play_button.setIcon(QtGui.QIcon("images/play.png"))
        ##     self.pause()
        ##     self.play_state = "paused"


    def play(self, content=None, playlist=None, parent_content=None, loop=False, marks_col=None, titles_col=None):
    
        #usually this will not be set if just playing from main window:
        ## if marks_col:
        ##     make_mark = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+M'),
        ##                                 self.video_window, marks_col.add_mark)
        ## if titles_col:
        ##     make_title = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+N'),
        ##                                  self.video_window, titles_col.new_title)

        ## print "Play() called. Received:"
        ## print "Content: ", content
        ## print "Playlist: ", playlist
        ## print "Marks_col: ", marks_col
        ## print "Titles_col: ", titles_col
        

        #incase it was disabled:
        self.play_button.setEnabled(True)
        #incase play was not called by self.play_toggle()
        self.play_state = "playing"
        self.play_button.setDown(True)

        self.start = 0
        self.end = None
        self.loop = loop
        if not content is None:
            self.cur_content = content
            #need milliseconds:
            self.start = content.start.total_seconds() * 1000
            if content.end:
                self.end = content.end.total_seconds() * 1000

            #print "updating content with: ", content, " and start to: ", self.start

        self.parent_content = parent_content

        if not playlist is None:
            self.cur_playlist = playlist

        #figure out *what* to play
        if self.cur_content:
            #just play that!
            pass
        elif self.cur_playlist and len(self.cur_playlist):
            self.cur_content = self.cur_playlist.increment()
        elif self.selected_content:
            self.cur_content = self.selected_content
            self.cur_playlist = self.selected_playlist
        elif self.selected_playlist and len(self.selected_playlist):
            self.cur_playlist = self.selected_playlist
            self.cur_content = self.selected_playlist.increment()
        else:
            #couldn't find anything to play, (re)disable play button
            self.play_button.setEnabled(False)

        # look for the index of self.cur_content in self.cur_playlist
        # save the index for updating loop content
        self.cur_index = None
        ## if self.cur_playlist and self.cur_content:
        ##     self.cur_index = self.cur_playlist.index(self.cur_content)
        if self.parent_content and self.cur_content:
            self.cur_index = self.parent_content.segments.index(self.cur_content)
            print "Index found: %s" % self.cur_index
            
        #look for cur_content: source file, start position, end position
        #print "PlayerWidget.play() called!"
        if self.cur_content:
            title = "%s: %s" % (self.cur_content.filename, self.cur_content.title)

            global main_window
            #main_window.setWindowTitle(self.cur_content.filename)
            main_window.setWindowTitle(title)

            #this raises the video window every time a new segment starts:
            #self.check_video()
            #self.video_window.setWindowTitle(self.cur_content.filename)

            #this might not catch all instances when video window does not
            #exist, but better than nothing:
            if self.video_window:
                self.video_window.setWindowTitle(title)


            #print "making path"
            #print "Cur_content.path: ", self.cur_content.path
            #print "Cur_content.filename: ", self.cur_content.filename
            path = os.path.join(self.cur_content.path, self.cur_content.filename)
            print "Playing: %s" % path

            #player_path = self.player.currentSource().fileName()
            if hasattr(self, 'Media') and self.Media:
                player_path = self.Media.get_mrl()
                player_path = player_path.replace("file://", "")
            else:
                player_path = None
                
            if path != player_path:
                print "MEDIA PATH: %s != %s" % (path, player_path)
                #get rid of everything already played:
                #self.player.clear()
                #self.player.setCurrentSource(Phonon.MediaSource(path))

                self.Media = self.Instance.media_new(path)
                #print "Setting media for media player: %s" % (str(self.Media))
                # put the media in the media player
                self.MediaPlayer.set_media(self.Media)

                # parse the metadata of the file
                self.Media.parse()
                # set the title of the track as window title
                #self.setWindowTitle(self.Media.get_meta(0))

                # the media player has to be 'connected' to the QFrame
                # (otherwise a video would be displayed in it's own window)
                # this is platform specific!
                # you have to give the id of the QFrame (or similar object) to
                # vlc, different platforms have different functions for this
                if sys.platform == "linux2": # for Linux using the X Server
                    self.MediaPlayer.set_xwindow(self.VideoFrame.winId())
                elif sys.platform == "win32": # for Windows
                    self.MediaPlayer.set_hwnd(self.VideoFrame.winId())
                elif sys.platform == "darwin": # for MacOS
                    self.MediaPlayer.set_nsobject(self.VideoFrame.winId())

                
            else:
                #no need to reset here, we're already playing the current item
                pass


            #self.player.play()

            ## if self.MediaPlayer.is_playing():
            ##     self.MediaPlayer.pause()
            ##     self.PlayButton.setText("Play")
            ##     self.isPaused = True
            ## else:
            ##     if self.MediaPlayer.play() == -1:
            ##         self.OpenFile()
            ##         return

            self.rate = 1.0
            self.MediaPlayer.play()
            self.MediaPlayer.set_rate(self.rate)
            #self.PlayButton.setText("Pause")
            self.Timer.start()
            self.isPaused = False            

            if self.start:
                #keep trying to update position until it works:
                ## start_text = 'a'
                ## cur_text = 'b'
                ## while start_text != cur_text:

                #time = self.player.currentTime()
                time = self.MediaPlayer.get_position() * 1000
                cur_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
                cur_text = cur_time.toString('mm:ss')

                start_time = QtCore.QTime((self.start / 3600000), (self.start / 60000) % 60, (self.start / 1000) % 60)
                start_text = start_time.toString('mm:ss')

                #tried to trigger this
                #self.update_position()
                #print "start:", self.start, type(self.start)
                #length = self.MediaPlayer.get_length()
                
                self.seek(self.start)

            print "Playing: %s" % path
            print self.cur_content.title
            #print self.cur_content.to_dict()


        #this doesn't work after all
        #raise ValueError, "Raising error to prevent segfault. Ignore this one."

    def setPosition(self, Position):
        """Set the position
        """
        # setting the position to where the slider was dragged
        self.MediaPlayer.set_position(Position / 1000.0)
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)

    def seek(self, position):
        ratio = self.get_ratio(position)
        self.MediaPlayer.set_position(ratio)
        

    def update_position(self):

        #might poll here for media to finish loading
        #before attempting to seek
        #print "Seekable?: %s" % self.player.isSeekable()

        if self.start:
            #based on:
            #http://www.qtcentre.org/threads/55947-phonon-video-player-application-stopped-at-seeking-position
            #trying pause first.
            self.player.pause()
            #print "Seeking to: %s" % self.start
            self.player.seek(self.start)
            self.player.play()
            #first time doesn't always get it...
            #trying twice:
            #makes it worse
            #self.player.seek(self.start)
        
            
    def pause(self):
        #pass it on
        #self.player.pause()            

        if self.MediaPlayer.is_playing():
            self.MediaPlayer.pause()
            #self.PlayButton.setText("Play")
            self.isPaused = True

    def stop(self):
        """Stop player
        """
        print "Stopping"
        self.MediaPlayer.stop()
        #self.PlayButton.setText("Play")


    def next(self):
        if self.cur_playlist and len(self.cur_playlist):
            content = self.cur_playlist.increment()
            self.play(content)
        print "Go Next"

    def previous(self):
        if self.cur_playlist and len(self.cur_playlist):
            content = self.cur_playlist.decrement()
            self.play(content)
        print "Go Previous"

    def forward(self):
        #time = self.player.currentTime()
        time = self.get_position()
        #go 5 seconds
        time += 5000
        #self.player.seek(time)
        self.seek(time)
        #print "Scan Forward"

    def back(self):
        #time = self.player.currentTime()
        time = self.get_position()
        #go 5 seconds
        time -= 5000
        #self.player.seek(time)
        self.seek(time)
        #print "Scan Backward"

    def jumpf(self):
        #time = self.player.currentTime()
        time = self.get_position()
        #go 60 seconds
        time += 60000
        self.seek(time)
        #self.player.seek(time)
        #print "Jump Forward"

    def jumpb(self):
        #time = self.player.currentTime()
        time = self.get_position()
        #go 60 seconds
        time -= 60000
        #self.player.seek(time)
        self.seek(time)
        #print "Jump Backward"

    def slower(self):
        """Slow down playback rate
        """
        #print dir(self.MediaPlayer)
        if self.rate > .1:
            self.rate = self.rate - .1
        print self.rate
        self.MediaPlayer.set_rate(self.rate)

    def faster(self):
        """Speed up playback rate
        """
        #print dir(self.MediaPlayer)
        if self.rate > .1:
            self.rate = self.rate + .1
        print self.rate
        self.MediaPlayer.set_rate(self.rate)

    def set_volume(self, Volume):
        """Set the volume
        """
        self.MediaPlayer.audio_set_volume(Volume)

    def get_ratio(self, position):
        """
        position should be position in ms
        """
        length = self.Media.get_duration()
        #print "length:", length
        ratio = (position * 1.0) / length
        #print "ratio:", ratio
        return ratio

    def get_position(self):
        """
        helper to get current position
        """
        pos = self.MediaPlayer.get_position()

        length = self.Media.get_duration()

        time = length * pos

        #print "position: ", pos
        #print "time: ", time

        return time

    def get_remainder(self):
        time = self.get_position()
        length = self.Media.get_duration()
        remain = length - time
        return remain

    #def tick(self, time):
    def updateUI(self):
        """updates the user interface"""
        time = self.get_position()

        #in ms:
        remain = self.get_remainder()

        #check this at the beginning...
        #otherwise some calls (like next() )
        #may make it look like things have stopped, but they haven't
        if not self.MediaPlayer.is_playing():
            # no need to call this function if nothing is played
            self.Timer.stop()
            if not self.isPaused:
                # after the video finished, the play button stills shows
                # "Pause", not the desired behavior of a media player
                # this will fix it
                #
                # However, sometimes it takes time to start media playing
                # (especially under heavy load)
                # this can cause media to stop before it gets going.
                #
                # If this continues to be a problem,
                # should find a way to call stop toward the end of the media
                # right now it looks like we call next()
                #self.stop()
                pass


        
        #print "length:", length
        #ratio = (self.start * 1.0) / length
        #print "ratio:", ratio

        #self.MediaPlayer.set_position(ratio)

        #print "Updating UI: ", time
        
        # setting the slider to the desired position
        self.seek_bar.setValue(self.MediaPlayer.get_position() * 1000)

        #print remain

        if self.cur_content and self.cur_content.end and time >= self.cur_content.end.position:
            if self.loop:
                #this works, but does not update the content object
                #so new loop points are not used
                #self.seek(self.cur_content.start.total_seconds() * 1000)
                
                #not sure if this will get updated content object
                #doesn't update, and number of loops are limited
                #self.play(self.cur_content)

                #update the content object from playlist
                if (not self.cur_index is None) and self.parent_content:
                    self.cur_content = self.parent_content.segments[self.cur_index]
                    #self.cur_content = self.cur_playlist[self.cur_index]
                self.seek(self.cur_content.start.total_seconds() * 1000)

            else:
                print "AUTOMATICALLY MOVING TO NEXT TRACK IN PLAYLIST"
                self.next()

        #make sure we've actually loaded something here (time != 0)
        elif time and remain <= 2000:
            print "Reaching the end of a track, moving on."
            self.next()
            
        display_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
        hours = time / 3600000
        if hours:
            self.time_passed.setText(display_time.toString('h:mm:ss'))
        else:
            self.time_passed.setText(display_time.toString('mm:ss'))

        #time = self.player.remainingTime()
        #time = self.MediaPlayer.get_length() - (self.MediaPlayer.get_position() * 1000)
        time = remain
        remain_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
        hours = time / 3600000
        remain_string = ''
        if hours:
            remain_string = remain_time.toString('h:mm:ss')
        else:
            remain_string = remain_time.toString('mm:ss')
        self.time_remain.setText("-%s" % remain_string)

        ## if remain_string == "00:01" or remain_string == "00:00" and self.cur_content:
        ##     print "END OF TRACK: AUTOMATICALLY MOVING TO NEXT TRACK IN PLAYLIST"
        ##     self.next()


    def change_selection(self, playlist, content=None):
        """
        keep track of recent selections
        in case nothing is currently playing, but something was selected,
        and then play is pressed.
        in that case, we want to play the currently selected item.
        in all other cases, the currently playing item will take precedence
        (and be remembered) after a pause/resume
        updating the currently playing item will require double clicking the
        play column/option of the current selection.  
        """        
        #once something has been selected, we can enable the play button
        self.play_button.setEnabled(True)

        self.selected_playlist = playlist
        if content:
            self.selected_content = content

    def currentTime(self):
        """
        shortcut to self.player.currentTime()

        PlayerWidget is often named player externally
        so it seems like this should be possible

        this is also used by marks widget
        """
        #return self.player.currentTime()
        #return self.MediaPlayer.get_time() * 1000
        return self.get_position()

    
class LeftNavWidget(QtGui.QWidget):
    """
    combine the tree view with a toolbar for different actions
    """
    def __init__(self, parent=None, table=None):
        super(LeftNavWidget, self).__init__(parent)
        
        self.layout = QtGui.QGridLayout()
        #don't need a margin here:
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        ## print main_player
        ## global main_player
        ## main_player = PlayerWidget(self)
        #self.layout.addWidget(main_player)
        #print main_player
        self.player = PlayerWidget(self)
        self.layout.addWidget(self.player)


        #http://srinikom.github.io/pyside-docs/PySide/QtGui/QTreeView.html
        #self.tree_view = QtGui.QTreeView()
        self.tree_view = PlaylistsTreeView()

        self.layout.addWidget(self.tree_view)

        self.file_edit = QtGui.QLineEdit()
        #self.file_edit.textChanged.connect(self.tree_view.update_location)
        #self.file_edit.textEdited.connect(self.tree_view.update_location)
        #self.file_edit.editingFinished.connect( self.tree_view.update_location(self.file_edit.text()) )
        self.file_edit.editingFinished.connect( self.update_location )
        self.layout.addWidget(self.file_edit)


        #http://srinikom.github.io/pyside-docs/PySide/QtGui/QToolBar.html#PySide.QtGui.PySide.QtGui.QToolBar.addAction
        #http://zetcode.com/gui/pysidetutorial/menusandtoolbars/
        self.toolbar = QtGui.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(16, 16))

        addAction = QtGui.QAction(QtGui.QIcon('images/plus.png'), 'Add', self)
        addAction.setShortcut('Ctrl+N')
        addAction.triggered.connect(self.tree_view.add)
        #hehe... double addAction
        self.toolbar.addAction(addAction)

        removeAction = QtGui.QAction(QtGui.QIcon('images/minus.png'), 'Remove', self)
        removeAction.triggered.connect(self.tree_view.remove)
        self.toolbar.addAction(removeAction)

        openAction = QtGui.QAction(QtGui.QIcon('images/open.png'), 'Open', self)
        openAction.triggered.connect(self.tree_view.open_list)
        self.toolbar.addAction(openAction)

        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

        self.set_table_view(table)
        
    def set_table_view(self, table):
        """
        set the table view, and update its reference to our player

        this probably only happens during initialization
        but should serve as a reminder that new table views (in sub-windows)
        need to update their reference to self.player
        """

        #This is a reference to the currently selected playlist view
        #(which is a table view)
        #when the current selection is changed, this needs to be updated.
        #this must be passed in externally
        #either at time of initialization, or set manually after init
        self.table = table

        #this should not be necessary with global main_player in use
        if not self.table is None:
            self.table.player = self.player

    def update_location(self):
        self.tree_view.update_location(self.file_edit.text())        

    def change_selection(self, node):
        """
        this gets called by self.tree_view after a different node in the
        tree is selected.
        this updates other views as needed. 
        """
        self.file_edit.setText(node.source)
        #can get the text with:
        #self.file_edit.text()

        if not self.table is None:
            #node.content is a playlist in this case:
            subtree = PlaylistModel(node.content)

            #table was created in an external context:
            self.table.setModel(subtree)

        #node.content is a playlist in this case:
        self.player.change_selection(node.content)
        #main_player.change_selection(node.content)

#class MainWidget(QtGui.QWidget):
class MainWidget(QtGui.QSplitter):
    def __init__(self, parent):
        super(MainWidget, self).__init__(parent)

        self.setChildrenCollapsible(False)
        self.setHandleWidth(1)

        #self.layout = QtGui.QHBoxLayout()
        #self.layout = QtGui.QGridLayout()
        #self.layout = QtGui.QSplitter()

        self.left_nav = LeftNavWidget()
        self.addWidget(self.left_nav)

        #self.table = QtGui.QTableView()
        #self.table = PlaylistView()
        self.table = PlaylistWidget()
        self.addWidget(self.table)

        #window resizer:
        #this makes it show up, but the behavior is strange...
        #not recommended
        #resizer = QtGui.QSizeGrip(self)
        #self.addWidget(resizer)

        #http://srinikom.github.io/pyside-docs/PySide/QtGui/QSplitter.html#PySide.QtGui.PySide.QtGui.QSplitter.setSizes
        self.setStretchFactor(0, 25)
        self.setStretchFactor(1, 75)

        #pass self.table reference into self.left_nav.tree
        #for update after selection        
        #self.left_nav.table = self.table
        self.left_nav.set_table_view(self.table.playlist_view)
        #could also pass that in

        #self.layout.setColumnStretch(1, 1)

        #self.setLayout(self.layout)
        #self.setWidget(self.layout)


class AppWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(AppWindow, self).__init__(parent)

        self.widget = MainWidget(self)

        self.setCentralWidget(self.widget)

        fileMenu = self.menuBar().addMenu("&File")

        openAction = QtGui.QAction('Open State', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open playlist structure')        
        openAction.triggered.connect(self.widget.left_nav.tree_view.open_lists)
        fileMenu.addAction(openAction)

        saveAction = QtGui.QAction('Save State', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save playlist structure')        
        saveAction.triggered.connect(self.widget.left_nav.tree_view.save_lists)
        fileMenu.addAction(saveAction)

        importAction = QtGui.QAction('Import State', self)
        #importAction.setShortcut('Ctrl+S')
        importAction.setStatusTip('Import playlist structure')        
        importAction.triggered.connect(self.widget.left_nav.tree_view.import_lists)
        fileMenu.addAction(importAction)

        #metaMenu.addSeparator()

        #metaMenu = self.menuBar().addMenu("Me&ta")

        ## openFolderAction = QtGui.QAction('Open Folder', self)
        ## #openFolderAction.setShortcut('Ctrl+O')
        ## openFolderAction.setStatusTip('Add folder to current playlist')        
        ## openFolderAction.triggered.connect(self.widget.table.playlist_view.add_content)
        ## metaMenu.addAction(openFolderAction)


        mediaMenu = self.menuBar().addMenu("&Media")

        openMediaAction = QtGui.QAction('Add Media', self)
        #openMediaAction.setShortcut('Ctrl+O')
        openMediaAction.setStatusTip('Add media to current playlist')        
        openMediaAction.triggered.connect(self.widget.table.playlist_view.add_media_dialog)
        mediaMenu.addAction(openMediaAction)


        openFolderAction = QtGui.QAction('Add Folder', self)
        #openFolderAction.setShortcut('Ctrl+O')
        openFolderAction.setStatusTip('Add folder to current playlist')        
        openFolderAction.triggered.connect(self.widget.table.playlist_view.add_folder_dialog)
        mediaMenu.addAction(openFolderAction)

        openContentAction = QtGui.QAction('Add Content Json', self)
        #openContentAction.setShortcut('Ctrl+O')
        openContentAction.setStatusTip('Add content to current playlist')
        openContentAction.triggered.connect(self.widget.table.playlist_view.add_content_dialog)
        mediaMenu.addAction(openContentAction)

        openPlaylistAction = QtGui.QAction('Open Playlist', self)
        #openPlaylistAction.setShortcut('Ctrl+O')
        openPlaylistAction.setStatusTip('Open a single JSON or M3U playlist')
        openPlaylistAction.triggered.connect(self.widget.left_nav.tree_view.open_list)
        mediaMenu.addAction(openPlaylistAction)




        playbackMenu = self.menuBar().addMenu("&Playback")

        playAction = QtGui.QAction('Play', self)
        playAction.setShortcut(' ')
        playAction.setStatusTip('Toggle Play / Pause of Player')        
        playAction.triggered.connect(self.widget.left_nav.player.toggle_play)
        #playAction.triggered.connect(main_player.toggle_play)
        playbackMenu.addAction(playAction)

        scanfAction = QtGui.QAction('Scan Forward', self)
        scanfAction.setShortcut('Alt+Right')
        scanfAction.setStatusTip('Seek Forward')        
        scanfAction.triggered.connect(self.widget.left_nav.player.forward)
        #scanfAction.triggered.connect(main_player.forward)
        playbackMenu.addAction(scanfAction)

        scanbAction = QtGui.QAction('Scan Back', self)
        scanbAction.setShortcut('Alt+Left')
        scanbAction.setStatusTip('Seek Back')        
        scanbAction.triggered.connect(self.widget.left_nav.player.back)
        #scanbAction.triggered.connect(main_player.back)
        playbackMenu.addAction(scanbAction)

        #Meta seems to be equivalent to Ctrl on Mac
        jumpfAction = QtGui.QAction('Jump Forward', self)
        jumpfAction.setShortcut('Ctrl+Right')
        jumpfAction.setStatusTip('Jump Forward')        
        jumpfAction.triggered.connect(self.widget.left_nav.player.jumpf)
        #jumpfAction.triggered.connect(main_player.jumpf)
        playbackMenu.addAction(jumpfAction)

        jumpbAction = QtGui.QAction('Jump Back', self)
        jumpbAction.setShortcut('Ctrl+Left')
        jumpbAction.setStatusTip('Jump Back')        
        jumpbAction.triggered.connect(self.widget.left_nav.player.jumpb)
        #jumpbAction.triggered.connect(main_player.jumpb)
        playbackMenu.addAction(jumpbAction)

        slowerAction = QtGui.QAction('Slower', self)
        slowerAction.setShortcut('Ctrl+,')
        slowerAction.setStatusTip('Slow playback speed')        
        slowerAction.triggered.connect(self.widget.left_nav.player.slower)
        #slowerAction.triggered.connect(main_player.slower)
        playbackMenu.addAction(slowerAction)

        fasterAction = QtGui.QAction('Faster', self)
        fasterAction.setShortcut('Ctrl+.')
        fasterAction.setStatusTip('Increase playback speed')        
        fasterAction.triggered.connect(self.widget.left_nav.player.faster)
        #fasterAction.triggered.connect(main_player.faster)
        playbackMenu.addAction(fasterAction)



        nextAction = QtGui.QAction('Next', self)
        nextAction.setShortcut('Alt+Down')
        nextAction.setStatusTip('Next Track')        
        nextAction.triggered.connect(self.widget.left_nav.player.next)
        #nextAction.triggered.connect(main_player.next)
        playbackMenu.addAction(nextAction)

        prevAction = QtGui.QAction('Previous', self)
        prevAction.setShortcut('Alt+Up')
        prevAction.setStatusTip('Previous Track')        
        prevAction.triggered.connect(self.widget.left_nav.player.previous)
        #prevAction.triggered.connect(main_player.previous)
        playbackMenu.addAction(prevAction)


        aboutMenu = self.menuBar().addMenu("&About")

        infoAction = QtGui.QAction('Info', self)
        infoAction.setStatusTip('Information about Medley')        
        infoAction.triggered.connect(self.about)
        aboutMenu.addAction(infoAction)

    def about(self):
        """
        Popup a box with about message.

        via:
        http://qt-project.org/wiki/PySideSimplicissimus_Module_3_AboutBox
        """
        QtGui.QMessageBox.about(self, "About PySide, Platform, etc",
                                """<b>Medley</b> v %s
                                <p>
                                <p>Python %s 
                                <p>PySide version %s
                                <p>Qt version %s on %s
                                """ % (__version__,
                                       platform.python_version(),
                                       PySide.__version__,
                                       PySide.QtCore.__version__,
                                       platform.system()))
    
        
def usage():
    print __doc__
    
def main():
    source = None
    if len(sys.argv) > 1:
        helps = ['--help', 'help', '-h']
        for i in helps:
            if i in sys.argv:
                usage()
                exit()

        source = sys.argv[1]
        #could handle more than one here, if needed
        cli_items.append(source)

    #finding where playlists are initialized is always tricky...
    #AppWindow() -> MainWidget() -> LeftNavWidget()
    #this contains PlayerWidget() and list_tree.PlaylistsTreeView()
    #PlaylistsTreeView().__init__() calls load_lists(previous_path)
    
    global main_window
    app = QtGui.QApplication(sys.argv)
    #this is needed for Phonon on Linux (DBUS):
    app.setApplicationName("Medley")
    main_window = AppWindow()
    #main_window.resize(900, 600)
    main_window.resize(960, 350)
    main_window.show()
    app.exec_()

if __name__ == '__main__':
    main()
