"""
adapted from:
http://stackoverflow.com/questions/4163740/qtreeview-with-drag-and-drop-support-in-pyqt?rq=1

and:
http://kylemr.blogspot.com/2013/04/pyqt-drag-and-drop-outliner-like.html

great video tutorials on Model View programming in Qt/PyQt/PySide:
http://www.yasinuludag.com/blog/?p=98

When searching for documentation on PySide, it's OK to look for PyQt too... they're mostly equivalent.

/c/alpha/pyside/drag_and_drop-tree.py


Medley

Tree of Lists


"""

import sys, os
import platform

import PySide
from PySide import QtGui, QtCore
from PySide.phonon import Phonon
    
from medley.helpers import load_json, save_json

#from content_view import ContentWindow
from playlists_view import PlaylistsTreeView, Node, TreeModel
from playlist_view import PlaylistView, PlaylistModel

__version__ = '0.0.1'


class PlayerWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(PlayerWidget, self).__init__(parent)

        self.audio = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.player = Phonon.MediaObject(self)
        Phonon.createPath(self.player, self.audio)

        self.player.setTickInterval(1000)
        self.connect(self.player, QtCore.SIGNAL("tick(qint64)"), self.tick)
    
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

        self.seek_bar = Phonon.SeekSlider(self.player, self)

        row2 = QtGui.QHBoxLayout()
        row2.addWidget(self.seek_bar)

        self.time_passed = QtGui.QLabel("00:00", self)
        self.time_remain = QtGui.QLabel("-00:00", self)

        row3 = QtGui.QHBoxLayout()
        row3.addWidget(self.time_passed)
        row3.addWidget(self.time_remain)
        row3.insertStretch(1, 50)

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


    def open_window(self):
        """
        opens the main video window
        """
        self.video_window = QtGui.QMainWindow(self)
        #self.video_window = ContentWindow(self)

        self.video = Phonon.VideoWidget(self.video_window)
        Phonon.createPath(self.player, self.video)

        self.video_window.resize(800, 400)
        self.video_window.show()

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

        if pressed is None:
            if self.play_state == "playing":
                self.pause()
                self.play_state = "paused"
                self.play_button.setDown(False)
            else:
                self.play()
                #self.play_state = "playing"
                #self.play_button.setDown(True)
                
        elif pressed:
            #source.setText("Pause")
            self.play_button.setIcon(QtGui.QIcon("images/pause.png"))
            self.play()
            #self.play_state = "playing"

        else:
            #source.setText("Play")
            self.play_button.setIcon(QtGui.QIcon("images/play.png"))
            self.pause()
            self.play_state = "paused"


    def play(self, content=None, playlist=None):
        #incase it was disabled:
        self.play_button.setEnabled(True)
        #incase play was not called by self.play_toggle()
        self.play_state = "playing"
        self.play_button.setDown(True)

        self.start = 0
        self.end = None
        if not content is None:
            self.cur_content = content
            #need milliseconds:
            self.start = content.start.total_seconds() * 1000
            if content.end:
                self.end = content.end.total_seconds() * 1000

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
            
        #look for cur_content: source file, start position, end position
        #print "PlayerWidget.play() called!"
        if self.cur_content:
            print "making path"
            path = os.path.join(self.cur_content.path, self.cur_content.filename)
            print "Playing: %s" % path

            player_path = self.player.currentSource().fileName()
            if path != player_path:
                #print "%s != %s" % (path, player_path)
                #get rid of everything already played:
                self.player.clear()
                self.player.setCurrentSource(Phonon.MediaSource(path))
            else:
                #no need to reset here, we're already playing the current item
                pass

            self.player.play()

            if self.start:
                #keep trying to update position until it works:
                start_text = 'a'
                cur_text = 'b'
                while start_text != cur_text:
                    time = self.player.currentTime()
                    cur_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
                    cur_text = cur_time.toString('mm:ss')

                    start_time = QtCore.QTime((self.start / 3600000), (self.start / 60000) % 60, (self.start / 1000) % 60)
                    start_text = start_time.toString('mm:ss')

                    #tried to trigger this
                    self.update_position()
            

            print "Playing: %s" % path
            print self.cur_content.title
            #print self.cur_content.to_dict()


        #this doesn't work after all
        #raise ValueError, "Raising error to prevent segfault. Ignore this one."


    def update_position(self):

        #might poll here for media to finish loading
        #before attempting to seek
        #print "Seekable?: %s" % self.player.isSeekable()

        if self.start:
            #print "Seeking to: %s" % self.start
            self.player.seek(self.start)
            #first time doesn't always get it...
            #trying twice:
            #makes it worse
            #self.player.seek(self.start)
        
            
    def pause(self):
        #pass it on
        self.player.pause()            

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
        time = self.player.currentTime()
        #go 5 seconds
        time += 5000
        self.player.seek(time)
        #print "Scan Forward"

    def back(self):
        time = self.player.currentTime()
        #go 5 seconds
        time -= 5000
        self.player.seek(time)
        #print "Scan Backward"

    def jumpf(self):
        time = self.player.currentTime()
        #go 60 seconds
        time += 60000
        self.player.seek(time)
        #print "Jump Forward"

    def jumpb(self):
        time = self.player.currentTime()
        #go 60 seconds
        time -= 60000
        self.player.seek(time)
        #print "Jump Backward"

    def tick(self, time):
        display_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
        hours = time / 3600000
        if hours:
            self.time_passed.setText(display_time.toString('h:mm:ss'))
        else:
            self.time_passed.setText(display_time.toString('mm:ss'))

        time = self.player.remainingTime()
        remain_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
        hours = time / 3600000
        if hours:
            self.time_remain.setText("-%s" % remain_time.toString('h:mm:ss'))
        else:
            self.time_remain.setText("-%s" % remain_time.toString('mm:ss'))
            


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
        """
        return self.player.currentTime()
    
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
        self.table = PlaylistView()
        self.addWidget(self.table)

        #http://srinikom.github.io/pyside-docs/PySide/QtGui/QSplitter.html#PySide.QtGui.PySide.QtGui.QSplitter.setSizes
        self.setStretchFactor(0, 25)
        self.setStretchFactor(1, 75)

        #pass self.table reference into self.left_nav.tree
        #for update after selection        
        #self.left_nav.table = self.table
        self.left_nav.set_table_view(self.table)
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

        fileMenu.addSeparator()

        openMediaAction = QtGui.QAction('Open Media', self)
        #openMediaAction.setShortcut('Ctrl+O')
        openMediaAction.setStatusTip('Add media to current playlist')        
        openMediaAction.triggered.connect(self.widget.table.add_content)
        fileMenu.addAction(openMediaAction)

        openFolderAction = QtGui.QAction('Open Folder', self)
        #openFolderAction.setShortcut('Ctrl+O')
        openFolderAction.setStatusTip('Add folder to current playlist')        
        openFolderAction.triggered.connect(self.widget.table.add_content)
        fileMenu.addAction(openFolderAction)



        playbackMenu = self.menuBar().addMenu("&Playback")

        playAction = QtGui.QAction('Play', self)
        playAction.setShortcut(' ')
        playAction.setStatusTip('Toggle Play / Pause of Player')        
        playAction.triggered.connect(self.widget.left_nav.player.toggle_play)
        playbackMenu.addAction(playAction)

        scanfAction = QtGui.QAction('Scan Forward', self)
        scanfAction.setShortcut('Alt+Right')
        scanfAction.setStatusTip('Seek Forward')        
        scanfAction.triggered.connect(self.widget.left_nav.player.forward)
        playbackMenu.addAction(scanfAction)

        scanbAction = QtGui.QAction('Scan Back', self)
        scanbAction.setShortcut('Alt+Left')
        scanbAction.setStatusTip('Seek Back')        
        scanbAction.triggered.connect(self.widget.left_nav.player.back)
        playbackMenu.addAction(scanbAction)

        #Meta seems to be equivalent to Ctrl on Mac
        jumpfAction = QtGui.QAction('Jump Forward', self)
        jumpfAction.setShortcut('Ctrl+Right')
        jumpfAction.setStatusTip('Jump Forward')        
        jumpfAction.triggered.connect(self.widget.left_nav.player.jumpf)
        playbackMenu.addAction(jumpfAction)

        jumpbAction = QtGui.QAction('Jump Back', self)
        jumpbAction.setShortcut('Ctrl+Left')
        jumpbAction.setStatusTip('Jump Back')        
        jumpbAction.triggered.connect(self.widget.left_nav.player.jumpb)
        playbackMenu.addAction(jumpbAction)

        nextAction = QtGui.QAction('Next', self)
        nextAction.setShortcut('Alt+Down')
        nextAction.setStatusTip('Next Track')        
        nextAction.triggered.connect(self.widget.left_nav.player.next)
        playbackMenu.addAction(nextAction)

        prevAction = QtGui.QAction('Previous', self)
        prevAction.setShortcut('Alt+Up')
        prevAction.setStatusTip('Previous Track')        
        prevAction.triggered.connect(self.widget.left_nav.player.previous)
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
    
        
def main():
    app = QtGui.QApplication(sys.argv)
    #this is needed for Phonon on Linux (DBUS):
    app.setApplicationName("Medley")
    window = AppWindow()
    window.resize(800, 600)
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
