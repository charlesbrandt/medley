import json
from PySide import QtGui, QtCore

from medley.content import Content
from medley.playlist import Playlist

#from content_view import ContentWindow

class PlaylistModel(QtCore.QAbstractTableModel):
    """
    wrap a medley.playlist.Playlist object
    so that it is easily used in a TableView

    Shouldn't need a separate Playlist object beyond this.
    """
    def __init__(self, playlist, parent=None):
        super(PlaylistModel, self).__init__(parent)
        self.playlist = playlist

        #define the order that things are displayed
        self.key_order = ['play', 'open', 'order', 'title', 'status', 'timestamp', 'tags', 'people', 'segments', 'marks', 'start', 'end', ]
        
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
                    content.tags = tags
                
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
        self.resizeColumnToContents(play_index)
        self.resizeColumnToContents(open_index)
        self.resizeColumnToContents(order_index)
        self.resizeColumnToContents(title_index)
        self.resizeColumnToContents(status_index)


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
        self.content_view.resize(800, 400)
        self.content_view.show()



class ContentWindow(QtGui.QMainWindow):
    def __init__(self, player, parent=None):
        super(ContentWindow, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('Content View')

        self.table = PlaylistView(self)
        self.setCentralWidget(self.table)

        self.content = None
        self.table.player = player

    def update_view(self, content):
        self.content = content

        self.setWindowTitle(content.title)
        playlist = Playlist(self.content.segments)
        subtree = PlaylistModel(playlist)

        self.table.setModel(subtree)

    #this approach makes the program crash after a window close
    ## def closeEvent(self, event):
    ##     # make sure parent view does not reference old (destroyed) Window
    ##     self.parent().content_view = None

    ##     event.accept()
        
    ##     super(ContentWindow, self).closeEvent(event)
