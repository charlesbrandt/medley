import json, re
from PySide import QtGui, QtCore

from medley.content import Content, Mark
from medley.playlist import Playlist

#from content_view import ContentWindow

class PlaylistModel(QtCore.QAbstractTableModel):
    """
    wrap a medley.playlist.Playlist object
    so that it is easily used in a TableView

    Shouldn't need a separate Playlist object beyond this.
    """
    def __init__(self, playlist, parent=None, key_order=None):
        super(PlaylistModel, self).__init__(parent)
        self.playlist = playlist

        #define the order that things are displayed
        if key_order is None:
            self.key_order = ['play', 'open', 'order', 'title', 'status', 'timestamp', 'tags', 'people', 'segments', 'marks', 'start', 'end', ]
        else:
            self.key_order = key_order
        
    def index(self, row, column, parent):
        """
        define how we retrieve a certain item in the list
        """
        if row < len(self.playlist):
            childItem = self.playlist[row]
            return self.createIndex(row, column, childItem)
        else:
            print "Row out of range! row: %s column: %s parent: %s" % (row, column, parent)
            return QtCore.QModelIndex()

        ## if childItem:
        ##     return self.createIndex(row, column, childItem)
        ## else:
        ##     return QtCore.QModelIndex()

    def rowCount(self, parent):
        ## if not parent.isValid():
        ##     parentNode = self.playlist
        ## else:
        ##     parentNode = parent.internalPointer()

        return len(self.playlist)

    def columnCount(self, index):
        """
        how many columns? (for table view only)
        """
        return len(self.key_order)
        #return 1
    
    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.key_order[col]
        return None

    def data(self, index, role):
        """
        this determines what is displayed in a View
        for a given item at index 'index'

        role determines which context the data is shown in
        """

        if not index.isValid():
            return None

        ## print index
        ## print dir(index)
        ## print index.row()
        ## print "index"
        ## print ""

        #content = self.playlist[index]
        content = index.internalPointer()
        #node = index.internalPointer()

        #print node.log()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:

            key = self.key_order[index.column()]

            #could check for special keys here:
            if key == 'order':
                return str(index.row())
            elif key == 'tags' or key == 'people':
                return ','.join(getattr(content, key))
            elif key == 'marks' or key == 'segments':
                return len(getattr(content, key))
            elif key == 'start' or key == "end":
                mark = getattr(content, key)
                if mark:
                    return mark.as_time()
                else:
                    return ''
            elif key == 'timestamp':
                ts = getattr(content, key)
                if ts:
                    return str(ts)
                else:
                    return ''
            elif key == 'play' or key == 'open':
                #TODO: check main playing status to see
                #if this is currently playing item
                #display play icon if so
                #otherwise, nothing:
                return ''
            else:
                return unicode(getattr(content, key))

            ## row = index.row()
            ## value = self.nodes[row]
            ## return value._name
            #if index.column() == 0:
            #    #return content.name()
            #    return str(content)

        ## elif role == QtCore.Qt.DecorationRole:
        ##     if index.column() == 0:
        ##         typeInfo = content.typeInfo()
                
        ##         if typeInfo == "LIGHT":
        ##             return QtGui.QIcon(QtGui.QPixmap(":/Light.png"))
                
        ##     #row = index.row()
        ##     #value = self.contents[row]

        ##     pixmap = QtGui.QPixmap(26, 26)
        ##     pixmap.fill('#000000')

        ##     icon = QtGui.QIcon(pixmap)
        ##     return icon

        elif role == QtCore.Qt.ToolTipRole:
            #return "Item details: %s" % content.name()
            return "%s" % (content.title)

        elif role == 0: 
            return index.internalPointer()
        else:
            return None


    def flags(self, index):
        """
        Valid items are selectable, editable, and drag and drop enabled.
        Invalid indices (open space in the view)
        are also drop enabled, so you can drop items onto the top level.
        """
        #print "flags called with index: %s" % index
        
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled

        #disable editing for title column
        elif ((self.key_order[index.column()] == 'open') or
              (self.key_order[index.column()] == 'marks') or
              (self.key_order[index.column()] == 'play') or
              (self.key_order[index.column()] == 'segments')):
              
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | \
                   QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable

        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | \
                   QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        this handles the new data once an edit is complete
        """
        if index.isValid():
            if role == QtCore.Qt.EditRole:
                
                content = index.internalPointer()
                key = self.key_order[index.column()]

                #could check for special keys here:
                if key == 'order':
                    #print "checking order move: %s, %s" % (value, index.row())
                    if int(value) != index.row():
                        self.beginRemoveRows( QtCore.QModelIndex(), index.row(), index.row() )
                        #print "len pre-pop: %s" % len(self.playlist)
                        self.playlist.pop(index.row())
                        #print "len post-pop: %s" % len(self.playlist)
                        self.endRemoveRows()
                        
                        self.beginInsertRows( QtCore.QModelIndex(), int(value), int(value) )
                        #print "len pre-insert: %s" % len(self.playlist)
                        self.playlist.insert(int(value), content)
                        #print "len pre-insert: %s" % len(self.playlist)
                        self.endInsertRows()
                        
                    #return str(index.row())

                elif key == 'tags' or key == 'people':
                    tags = value.split(',')
                    #this won't work for people
                    #content.tags = tags
                    setattr(content, key, tags)
                    content.save()

                elif key in ['title', 'status']:
                    setattr(content, key, value)
                    content.save()
                
                return True

        return False

    def insertRows(self, row, count, parentIndex=QtCore.QModelIndex()):
        """
        Add a number of rows to the model at the given row and parent.
        """
        #defaults parent to the root:
        #parentIndex = QtCore.QModelIndex()
        
        self.beginInsertRows( parentIndex, row, row+count-1 )

        success = False
        for i in range(count):
            content = Content()
            content.title = "New item: %s" % i
            self.playlist.append(content)
            success = True
            
        self.endInsertRows()
        return success
     
    def removeRows(self, row, count=1, parentIndex=QtCore.QModelIndex()):
        """
        Remove a number of rows from the model at the given row and parent.
        """
        self.beginRemoveRows( parentIndex, row, row+count-1 )

        success = False
        #parent = self.getNode(parentIndex)
        #parent = parentIndex.internalPointer()
        for i in range(row, row+count):
            self.playlist.pop(i)
            success = True
            #success = parent.removeChild(row)
            #value = self.nodes[row]
            #self.nodes.remove(value)
            
        self.endRemoveRows()
        return success


    def supportedDropActions(self):
        """
        Items can be moved and copied
        """
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction 

    def mimeTypes(self):
        """
        this is needed for drag and drop to make drop available (!!!)
        """
        return ['json/content']

    def mimeData(self, indices):
        """
        this recieves a separate index for every column that is selected...
        should check each index for a new row
        (we only want to move whole rows here)
        """
        mimedata = QtCore.QMimeData()
        #print len(indices)

        row_nums = []
        items = []
        for index in indices:
            if not index.row() in row_nums:
                row_nums.append(index.row())
                content = index.internalPointer()
                items.append(content.to_dict())
            else:
                pass
                #print "duplicate row: %s" % index.row()                
            
        #item = self.getNode( indices[0] )

        #mimedata.setData('text/xml', item)
        #print json.dumps(item)

        everything = {'row_nums':row_nums, 'items':items}
        
        #mimedata.setData('json/content', json.dumps(items))
        mimedata.setData('json/content', json.dumps(everything))
        return mimedata

    def dropMimeData(self, mimedata, action, row, column, parent):
        #TODO:
        #should pass in a parent id with mimedata
        #to enable removing from other PlaylistView objects
        
        print 'dropMimeData %s %s %s %s %s' % (mimedata.data('json/content'), action, row, column, parent)
        #print 'parent row: %s, column: %s' % (parent.row(), parent.column())
        
        everything = json.loads( str(mimedata.data('json/content')) )
        row_nums = everything['row_nums']
        items = everything['items']
        
        if action == QtCore.Qt.DropAction.MoveAction:
            #remove old row_nums first:
            row_nums.sort()
            row_nums.reverse()
            print "removing rows first: %s" % row_nums
            for row in row_nums:
                self.removeRows(row)

        start_pos = parent.row()

        self.beginInsertRows( QtCore.QModelIndex(), int(start_pos), int(len(items)+start_pos)-1 )
        print "len pre-insert: %s" % len(self.playlist)

        print "starting at row: %s" % start_pos
        position = start_pos
        for item in items:
            content = Content(content=item)
            self.playlist.insert(position, content)
            position += 1

        print "len pre-insert: %s" % len(self.playlist)
        self.endInsertRows()
            
        self.dataChanged.emit( parent, parent )
        return True        



class PlaylistView(QtGui.QTableView):
    """
    customizing TableView to handle drag and drop correctly:
    http://stackoverflow.com/questions/10264040/how-to-drag-and-drop-into-a-qtablewidget-pyqt
    """
    def __init__(self, parent=None):
        super(PlaylistView, self).__init__(parent)
        ## self.model = None
        ## self.last_folder = None

        #self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setAlternatingRowColors(True)
        #self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        #self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.doubleClicked.connect(self.check_click)
        #has no effect on trees, but might work in tables
        #self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        #what is currently selected.
        self.cur_index = QtCore.QModelIndex()
        self.cur_content = None

        self.content_view = None

        #this will get set once the PlaylistView has been assigned:
        self.player = None
        
    def setModel(self, model):
        super(PlaylistView, self).setModel(model)
        self.model = model

        #checking to see if the shortcut (following line) works instead of this:
        ## self.connect(self.selectionModel(),  
        ##              QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),  
        ##              self.store_current_selection)

        #this seems to perform the same function:
        #keeping both versions around, since legacy code uses SIGNAL
        #this is a good reminder/guide on how to convert them
        self.selectionModel().selectionChanged.connect(self.store_current_selection)

        play_index = self.model.key_order.index('play')
        open_index = self.model.key_order.index('open')
        order_index = self.model.key_order.index('order')
        title_index = self.model.key_order.index('title')
        status_index = self.model.key_order.index('status')
        start_index = self.model.key_order.index('start')
        self.resizeColumnToContents(play_index)
        self.resizeColumnToContents(open_index)
        self.resizeColumnToContents(order_index)
        self.resizeColumnToContents(title_index)
        self.resizeColumnToContents(status_index)
        self.resizeColumnToContents(start_index)


    def store_current_selection(self, newSelection, oldSelection):
        """
        update the currently selected Content item
        """
        self.cur_index = newSelection.indexes()[0]
        self.cur_content = self.cur_index.internalPointer()
        
    def check_click(self, index):
        """
        connect this with the doubleClicked signal
        to see what was clicked on
        """
        #print "DOUBLE CLICK: %s %s" % (index.row(), index.column())

        if self.model.key_order[index.column()] == 'open':
            if self.content_view is None:
                self.open_window()

            else:
                #even though actual window may have been deleted,
                #reference to it is kept around
                #we can check if the reference throws an error
                #in which case we can create a new window
                #seems a bit kludgey, but it works
                #(especially since ContentWindow.closeEvent didn't work)

                try:
                    self.content_view.window()
                except:
                    self.open_window()
                    
                ## print "CONTENT VIEW STATUS:"
                ## print self.content_view.destroyed
                ## print self.content_view.window()
                ## print self.content_view
                ## print dir(self.content_view)

            #update current content with selected content
            #do this if the window is new or old:
            self.content_view.update_view(self.cur_content)
            self.content_view.activateWindow()
            self.content_view.raise_() # just to be sure it's on top

        if self.model.key_order[index.column()] == 'play':
            #print "Play: %s" % self.cur_content.title
            #maybe it is better to pass self.model.playlist?
            self.model.playlist.set_current(self.cur_content)
            self.player.play(self.cur_content, self.model.playlist)

    
    def open_window(self):
        """
        http://stackoverflow.com/questions/8478210/how-to-create-a-new-window-button-pyside-pyqt
        """
        #self.content_view = QtGui.QMainWindow(self)
        self.content_view = ContentWindow(self.player, self)
        self.content_view.resize(1000, 400)
        self.content_view.show()


class MarksWidget(QtGui.QWidget):
    """
    combine the list view with a toolbar for different actions

    needs to be its own widget to be added to the splitter
    """
    def __init__(self, player, parent=None):
        super(MarksWidget, self).__init__(parent)

        self.player = player
        #set externally after content changes
        self.content = None

        self.layout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        self.marks = QtGui.QListWidget(self)
        #not sure that drag and drop is useful with marks...
        #auto-indexing by timestamp is more appropriate
        #self.marks.setDragDropMode(self.marks.InternalMove)
        self.marks.itemChanged.connect(self.on_changed)
        self.layout.addWidget(self.marks)

        self.track_prefix = QtGui.QLineEdit()
        self.layout.addWidget(self.track_prefix)

        marks_toolbar = QtGui.QToolBar()
        marks_toolbar.setIconSize(QtCore.QSize(16, 16))

        addAction = QtGui.QAction(QtGui.QIcon('images/target.png'), 'Add', self)
        #addAction.setShortcut('Ctrl+N')
        addAction.triggered.connect(self.add_mark)
        marks_toolbar.addAction(addAction)

        removeAction = QtGui.QAction(QtGui.QIcon('images/minus.png'), 'Remove', self)
        removeAction.triggered.connect(self.remove_mark)
        marks_toolbar.addAction(removeAction)

        openAction = QtGui.QAction(QtGui.QIcon('images/open.png'), 'Import from file', self)
        openAction.triggered.connect(self.open_marks)
        marks_toolbar.addAction(openAction)

        saveAction = QtGui.QAction(QtGui.QIcon('images/save.png'), 'Export to file', self)
        saveAction.triggered.connect(self.save_marks)
        marks_toolbar.addAction(saveAction)

        mergeAction = QtGui.QAction(QtGui.QIcon('images/merge.png'), 'Merge titles and marks', self)
        mergeAction.triggered.connect(self.merge_titles)
        marks_toolbar.addAction(mergeAction)

        #SPACER HERE
        #don't see any spacers for toolbars.
        

        self.layout.addWidget(marks_toolbar)

        self.setLayout(self.layout)

    ## def add_item(self, title='-'):
    ##     item = QtGui.QListWidgetItem(title, self.titles)
    ##     item.setFlags( QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | \
    ##                    QtCore.Qt.ItemIsDragEnabled | \
    ##                    QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable )
    ##     #print item.flags()
    ##     #self.titles.addItem(title)

    def sync(self):
        """
        synchronize the contents of content.marks
        with what is in QListWidget
        """
        #reorder list based on times
        self.content.marks.sort()
        self.marks.clear()
        for mark in self.content.marks:
            text = "%s - %s" % (mark.as_time(), mark.tag)
            item = QtGui.QListWidgetItem(text, self.marks)
            item.setFlags( QtCore.Qt.ItemIsEnabled | \
                           QtCore.Qt.ItemIsDropEnabled | \
                           QtCore.Qt.ItemIsDragEnabled | \
                           QtCore.Qt.ItemIsSelectable | \
                           QtCore.Qt.ItemIsEditable )
            
            #self.marks.addItem(text)

        self.track_prefix.setText(self.content.track_prefix)
        #can get the text with:
        #self.track_prefix.text()



    def add_mark(self, mark=''):
        #get current position from player (00:00 is ok)
        if self.player:
            time = self.player.currentTime()
            #display_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
            #hours = time / 3600000
            mark = Mark(mark, time)
            self.content.marks.append(mark)
            self.sync()
            #mark = "%s - %s" % (display_time.toString('h:mm:ss'), mark)
            #self.marks.addItem(mark)
        else:
            print "NO player object assigned to self: %s" % self.player
            #self.marks.addItem(mark)
            mark = Mark(mark, 0)
            self.content.marks.append(mark)
            self.sync()

    def remove_mark(self, row=None):
        if row is None:
            row = self.marks.currentRow()

        self.marks.takeItem(row)
        self.content.marks.pop(row)    

    def on_changed(self, item):
        row = self.marks.row(item)
        mark = self.content.marks[row]
        text = "%s - %s" % (mark.as_time(), mark.tag)
        if text != item.text():
            parts = item.text().split(' - ', 1)
            #print "PARTS: %s" % parts
            ts, tag = parts
            mark.from_time(ts)
            mark.tag = tag
            self.content.marks[row] = mark
            #print "Marks.on_change called: %s, %s" % (item.text(), text)
            self.sync()
        
    def open_marks(self):
        pass

    def save_marks(self):
        pass

    def merge_titles(self):
        new_prefix = self.track_prefix.text()
        self.content.track_prefix = new_prefix

        tracks = self.content.remainder['tracks']
        self.content.history.make("Merging titles with marks", ["merge"])
        self.content.marks.make_segments(self.content, titles=tracks)
        self.content.save()

        #matching titles/tracks should happen in make_segments() now:
        ## count = 0
        ## tracks = self.content.remainder['tracks']
        ## #tracks = self.content.tracks
        ## for cur_track in tracks:
        ##     if count < len(self.content.segments):
        ##         self.content.segments[count].title = cur_track
        ##     else:
        ##         print "%s tracks, %s segments" % (len(tracks), len(self.content.segments))
        ##         print "EXTRA track title: %s" % cur_track
        ##     count += 1

        ## if len(self.content.segments) > len(tracks):
        ##     print "WARNING: extra segments: %s tracks, %s segments" % (len(tracks), len(self.content.segments))

        #refresh ContentWindow with latest changes
        self.parent().parent().update_view(self.content)


class TitleList(QtGui.QListWidget):
    """
    ListWidget that allows custom drag and drop response:
    http://stackoverflow.com/questions/1224432/how-do-i-respond-to-an-internal-drag-and-drop-operation-using-a-qlistwidget    
    """
    def __init__(self, content, parent=None):
        QtGui.QListWidget.__init__(self, parent)
        self.content = content
        self.setDragDropMode(self.InternalMove)
        self.installEventFilter(self)

    def eventFilter(self, sender, event):
        if (event.type() == QtCore.QEvent.ChildRemoved):
            self.on_order_changed()
        return False # don't actually interrupt anything

    def on_order_changed(self):
        """
        just use the order of the ListWidget as authoritative
        """
        #print "Order change detected!!"
        if self.content and self.content.remainder.has_key('tracks'):
            new_order = []
            for row in range(self.count()):
                print self.item(row).text()
                new_order.append(self.item(row).text())
            self.content.remainder['tracks'] = new_order
            #self.content.remainder['tracks'].sort()
            #for title in self.content.remainder['tracks']:
        self.parent().sync()
        print
        
        
class TitlesWidget(QtGui.QWidget):
    """
    combine the list view with a toolbar for different actions

    needs to be its own widget to be added to the splitter
    """
    def __init__(self, parent=None, table=None):
        super(TitlesWidget, self).__init__(parent)

        #set externally after content changes
        self.content = None

        self.layout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        self.titles = QtGui.QListWidget(self)
        ## #might be better to subclass QListView and have model more in sync..
        ## #right now this will cause the item to be at the end of the list
        ## #self.titles.setDragDropMode(self.titles.InternalMove)

        #this still exhibits drop at end of list behavior,
        #but is much closer
        #self.titles = TitleList(self.content, self)

        self.titles.itemChanged.connect(self.on_changed)
        self.layout.addWidget(self.titles)

        titles_toolbar = QtGui.QToolBar()
        titles_toolbar.setIconSize(QtCore.QSize(16, 16))

        addAction = QtGui.QAction(QtGui.QIcon('images/plus.png'), 'Add', self)
        #addAction.setShortcut('Ctrl+N')
        addAction.triggered.connect(self.add_title)
        titles_toolbar.addAction(addAction)

        removeAction = QtGui.QAction(QtGui.QIcon('images/minus.png'), 'Remove', self)
        removeAction.triggered.connect(self.remove_title)
        titles_toolbar.addAction(removeAction)

        openAction = QtGui.QAction(QtGui.QIcon('images/open.png'), 'Import from file', self)
        openAction.triggered.connect(self.open_titles)
        titles_toolbar.addAction(openAction)

        saveAction = QtGui.QAction(QtGui.QIcon('images/save.png'), 'Export to file', self)
        saveAction.triggered.connect(self.save_titles)
        titles_toolbar.addAction(saveAction)

        detailsAction = QtGui.QAction(QtGui.QIcon('images/details.png'), 'Show details in console', self)
        detailsAction.triggered.connect(self.content_details)
        titles_toolbar.addAction(detailsAction)

        self.layout.addWidget(titles_toolbar)

        self.setLayout(self.layout)

    def on_changed(self, item):
        row = self.titles.row(item)
        if self.content.remainder.has_key('tracks'):
            tracks = self.content.remainder['tracks']
            if row < len(tracks):
                title = tracks[row]
                #title = self.content.titles[row]
                if title != item.text():
                    tracks[row] = item.text()
                    #print "Titles.on_change called: %s, %s" % (item.text(), title)
                    #be careful where sync is called...
                    #easy to get into an infinite loop with this
                    self.sync()
            else:
                #must have a new item... just append it:
                tracks.append(item.text())
                self.sync()

        
    def add_title(self, title='-'):
        item = QtGui.QListWidgetItem(title, self.titles)
        item.setFlags( QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | \
                       QtCore.Qt.ItemIsDragEnabled | \
                       QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable )
        #print item.flags()
        #self.titles.addItem(title)

    def sync(self):
        """
        synchronize the contents of content.titles
        with what is in QListWidget
        """
        #print content.to_dict()
        self.titles.clear()
        #self.titles.addItems(content.remainder['titles'])
        if self.content.remainder.has_key('tracks'):
            #self.content.remainder['tracks'].sort()
            re1='(\\d+)(\.)'	# Integer Number 1
            rg = re.compile(re1,re.IGNORECASE|re.DOTALL)

            tracks = self.content.remainder['tracks']
            #print "TRACKS: %s" % tracks

            sorting = []
            for title in tracks:
                m = rg.search(title)
                if m:
                    int1 = m.group(1)
                    #print "("+int1+")"+"\n"
                    sorting.append( (int(int1), title) )
                else:
                    sorting.append( (1000000, title) )
            sorting.sort()
            #print "SORTING: %s" % sorting
            
            updated = []
            for item in sorting:
                updated.append(item[1])
            #print "UPDATED: %s" % updated

            self.content.remainder['tracks'] = updated
            
            for title in updated:
                self.add_title(title)
            #self.titles.addItems(content.remainder['tracks'])


    def remove_title(self, row=None):
        if row is None:
            #take currently selected item instead
            row = self.titles.currentRow()

        self.titles.takeItem(row)
        self.content.titles.pop(row)    

    def open_titles(self):
        pass

    def save_titles(self):
        pass

    def content_details(self):
        """
        look in parent for currently selected content item
        then show the details (content.debug() and content.to_dict())
        in the console
        """
        if self.content:
            print self.content.to_dict()
            print self.content.debug()
        else:
            print "NO CONTENT assigned to self: %s" % self.content


class ContentWindow(QtGui.QMainWindow):
    def __init__(self, player, parent=None):
        super(ContentWindow, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('Content View')

        self.splitter = QtGui.QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)

        self.table = PlaylistView(self)
        self.splitter.addWidget(self.table)

        self.marks_col = MarksWidget(player, self)
        #self.splitter.addWidget(self.marks)
        self.splitter.addWidget(self.marks_col)

        self.titles_col = TitlesWidget(self)
        #self.splitter.addWidget(self.titles)
        self.splitter.addWidget(self.titles_col)

        #self.marks = QtGui.QListWidget(self)
        #self.splitter.addWidget(self.marks)

        self.splitter.setStretchFactor(0, 60)
        self.splitter.setStretchFactor(1, 20)
        self.splitter.setStretchFactor(2, 20)

        #self.setCentralWidget(self.table)
        self.setCentralWidget(self.splitter)

        self.content = None
        self.table.player = player

    def update_view(self, content):
        self.content = content

        self.setWindowTitle(content.title)
        playlist = Playlist(self.content.segments)

        key_order = ['play', 'open', 'order', 'start', 'tags', 'title', 'status', 'timestamp', 'people', 'segments', 'marks', 'end', ]

        subtree = PlaylistModel(playlist, key_order=key_order)

        self.table.setModel(subtree)

        self.titles_col.content = content
        self.titles_col.titles.content = content
        self.titles_col.sync()
        
        self.marks_col.content = content
        self.marks_col.sync()
        
        ## self.marks_col.marks.clear()
        ## for mark in content.marks:
        ##     text = "%s - %s" % (mark.as_time(), mark.tag)
        ##     self.marks_col.marks.addItem(text)

        #print content.to_dict()


    #this approach makes the program crash after a window close
    ## def closeEvent(self, event):
    ##     # make sure parent view does not reference old (destroyed) Window
    ##     self.parent().content_view = None

    ##     event.accept()
        
    ##     super(ContentWindow, self).closeEvent(event)