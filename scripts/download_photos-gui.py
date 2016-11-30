#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2014.11.23 11:22:14 
# License: MIT 

# Requires:
# PySide, Medley

# Description:
#

"""

#import os, codecs, re, shutil
import os

from medley.scraper import download_images, download_image

from PySide import QtCore, QtGui

#for about:
import platform
import PySide
__version__ = '0.0.1'

class Grabber(QtGui.QWidget):
    """
    """
 
    def __init__(self, parent=None):
        """Constructor"""
        super(Grabber, self).__init__()
 
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)        

        #http://www.blog.pythonlibrary.org/2013/04/16/pyside-standard-dialogs-and-message-boxes/
        dirDialogBtn =  QtGui.QPushButton("Choose Directory")
        dirDialogBtn.clicked.connect(self.openDirectoryDialog)
        grid.addWidget(dirDialogBtn, 2, 0)

        #self.cur_dir = QtGui.QLabel("")

        #used for destination:
        self.cur_dir = QtGui.QLineEdit("")
        grid.addWidget(self.cur_dir, 2, 1)


        tags = []
        alternate_name = ''
        people = []

        tagsLabel = QtGui.QLabel("Tags:")        
        grid.addWidget(tagsLabel, 3, 0)
        self.tagsEdit = QtGui.QLineEdit()
        grid.addWidget(self.tagsEdit, 3, 1)

        prefixLabel = QtGui.QLabel("Alt file prefix:")        
        grid.addWidget(prefixLabel, 4, 0)
        self.prefixEdit = QtGui.QLineEdit()
        grid.addWidget(self.prefixEdit, 4, 1)

        peopleLabel = QtGui.QLabel("People:")        
        grid.addWidget(peopleLabel, 5, 0)
        self.peopleEdit = QtGui.QLineEdit()
        grid.addWidget(self.peopleEdit, 5, 1)


        urls = """
        """
        self.url_text = QtGui.QPlainTextEdit()
        self.url_text.setPlainText(urls)

        grid.addWidget(self.url_text, 6, 0, 1, 2)

         
        self.status = QtGui.QLabel("")
        grid.addWidget(self.status, 7, 0, 1, 2)
        #self.status_text = ''
        
        grab_button = QtGui.QPushButton('Grab em!', self)
        grab_button.clicked.connect(self.grab_em)
        grid.addWidget(grab_button, 8, 1)

        about_button = QtGui.QPushButton('About', self)
        about_button.clicked.connect(self.about)
        grid.addWidget(about_button, 8, 0)
        
        self.setLayout(grid)
 
    def openDirectoryDialog(self):
        """
        Opens a dialog to allow user to choose a directory
        """
        flags = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        d = directory = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", os.getcwd(), flags)
        self.cur_dir.setText(d)


    def grab_em(self):        
        button = self.sender()
        if isinstance(button, QtGui.QPushButton):
            #self.status.setText("You pressed %s!" % button.text())
            pass

        self.status.setText("... and we're off!")
                
        #print source directory:
        #print self.cur_dir.text()
        destination_path = self.cur_dir.text()

        tags_text = self.tagsEdit.text()
        tags = tags_text.split(',')

        alternate_name = self.prefixEdit.text()

        #print prefix:
        #print self.prefixEdit.text()
        people_text = self.peopleEdit.text()
        people = people_text.split(',')        

        self.destination_path = destination_path
        self.tags = tags
        self.alternate_name = alternate_name
        self.people = people
        
        #urls = urls.splitlines()

        #urls = []        
        #for line in self.url_text.toPlainText().splitlines():
        #    urls.append(line)

        self.urls = self.url_text.toPlainText().splitlines()

        QtCore.QTimer.singleShot(0, self.handle_download)

        #for loop will block gui updates:
        
        ## #count = 1
        ## #would be good to download one at a time and update status label
        ## for url in urls:
        ##     if url:
        ##         #cur_name = download_image(url, destination_path, tags, alternate_name, people)
        ##         self.url = url
        ##         QtCore.QTimer.singleShot(0, self.handle_download)
        ##         #hoping this will get picked up by timer?
        ##         #self.status_text = "Finished: %s" % cur_name
                
        ##         self.status_text = "Finished: %03d" % count
        ##         count += 1
                
        ##         #this won't get updated since the loop is blocking:
        ##         #self.status.setText("Finished: %s" % cur_name)

        ## #this will get set because it's the last call:
        ## #http://stackoverflow.com/questions/11836623/pyside-settext-not-updating-qlabel
        ## self.status.setText("All done!")
        ## print "All done!"

        #download_images(urls, destination, tags, alternate_name, people)
        #download_images(urls, destination_path, tags=[], alt_name="image", people=[], drive_dir=None, base_dir=None)

    def handle_download(self):
        """
        separate call so GUI gets updated in between
        """
        self.url = self.urls.pop()

        if self.url:
            cur_name = download_image(self.url, self.destination_path, self.tags, self.alternate_name, self.people)

        if len(self.urls):
            #self.status_text = "Finished: %s" % cur_name
            self.status.setText("Finished: %s" % cur_name)
            QtCore.QTimer.singleShot(0, self.handle_download)
        else:
            self.status.setText("All done!")
            print "All done!"
        

## class AppWindow(QtGui.QMainWindow):
##     def __init__(self, parent=None):
##         super(AppWindow, self).__init__(parent)

##         self.widget = Grabber(self)

##         self.setCentralWidget(self.widget)

##         aboutMenu = self.menuBar().addMenu("&About")

##         infoAction = QtGui.QAction('Info', self)
##         infoAction.setStatusTip('Information about Medley')        
##         infoAction.triggered.connect(self.about)
##         aboutMenu.addAction(infoAction)

##         self.setWindowTitle("Grab Images")

    def about(self):
        """
        Popup a box with about message.

        via:
        http://qt-project.org/wiki/PySideSimplicissimus_Module_3_AboutBox
        """
        QtGui.QMessageBox.about(self, "About Download Photos...",
                                """<b>Grabber!</b> v %s
                                <p>
                                <p>Python %s 
                                <p>PySide version %s
                                <p>Qt version %s on %s
                                """ % (__version__,
                                       platform.python_version(),
                                       PySide.__version__,
                                       PySide.QtCore.__version__,
                                       platform.system()))
    

 

                   
if __name__ == "__main__":
    app = QtGui.QApplication([])

    form = Grabber()
    form.setWindowTitle('Grabber')    
    form.resize(640, 450)

    form.show()

    #this is needed if you want a menu bar:
    ## window = AppWindow()
    ## window.show()

    app.exec_()
