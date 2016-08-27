import json, re, os
from PySide import QtGui, QtCore

from shared import all_contents, configs
#from shared import main_player

from medley.content import Content, Mark, import_content
from medley.playlist import Playlist
from medley.helpers import find_json, load_json
#from medley.helpers import find_json, make_json_path, load_json

from moments.path import Path
from moments.launch import file_browse

re1='(\\d+)(\.)'	# Integer Number 1
find_number = re.compile(re1,re.IGNORECASE|re.DOTALL)

def make_media_file_list(media):
    """
    accepts a list of media options from a content object
    converts it to just a list of files
    """
    
    items = []

    for item in media:
        if isinstance(item, list):
            #print item[0]
            fname = os.path.basename(item[0])
            #print fname
            items.append(fname)
        else:
            fname = os.path.basename(item)
            #print fname
            items.append(fname)
            
    return items

def find_contents(fname):
    """
    helper to take a path (fname)
    look for the corresponding json file
    (create one if none exists)
    and load the Content(s)
    returns a list of all contents found

    utilized the all_contents global dictionary
    """
    contents = []
    options = []
    if fname:
        print "Loading: %s" % fname
        p = Path(fname)
        if p.type() == "Directory":
            d = p.load()
            d.scan_filetypes()
            options.extend(d.movies)
            options.extend(d.sounds)
        else:
            #name = p.name
            #must be some other file type... load the parent directory:
            #parent = p.parent()
            #d = parent.load()
            options.append(p)

        drive_dir = configs.get('default_drive_dir')            
        for option in options:
            print "Adding: %s" % unicode(option)
            content = import_content(unicode(option), all_contents, drive_dir)
            contents.append(content)
    else:
        print "No file selected: %s" % fname

    return contents

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
            #different options available
            #self.key_order = ['up', 'play', 'open', 'order', 'title', 'status', 'timestamp', 'tags', 'people', 'segments', 'marks', 'start', 'end', ]
            #self.key_order = ['up', 'play', 'open', 'order', 'people', 'filename', 'tags', 'status', 'timestamp', 'title', 'segments', 'marks', 'start', 'end', ]
            #self.key_order = ['up', 'open', 'play', 'status', 'tags', 'start', 'order', 'title', 'filename', 'people', 'timestamp', 'segments', 'marks', 'end', ]
            self.key_order = ['open', 'play', 'media', 'status', 'tags', 'start', 'order', 'title', 'people', 'timestamp', 'segments', 'marks', 'end', 'up', 'loop', ]
            #see also ContentWindow for other common key_order 

        else:
            self.key_order = key_order

    def add_contents(self, contents):
        """
        originally in PlaylistView
        but it was making many calls to PlaylistModel...
        just do it all here
        this will also help to add contents from other places

        (targeting list_tree.PlaylistsTreeView specifically)
        """
        count = len(contents)
        total_rows = self.rowCount(None)

        #not sure if this will work here... 
        cur_index = QtCore.QModelIndex()

        self.beginInsertRows( cur_index, total_rows, total_rows+count-1 )

        #for i in range(count):
        for content in contents:
            self.playlist.append(content)
            ## name_only = os.path.basename(fname)
            ## child = Node(name_only)
            ## child.source = fname

            ## #open fname here and assign Playlist object as child.content
            ## playlist = load_playlist(fname)
            ## child.content = playlist
            ## #add Node to tree of playlists:
            ## success = parent.insertChild(child_count, child)
            
        self.endInsertRows()
        #print self.playlist

        return "success"
        
        
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
            #print key

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
            ## elif key == 'media':
            ##     #just return this one the way it is
            ##     return getattr(content, key)                
            elif key == 'media':
                 #just return this one the way it is
                 return json.dumps(getattr(content, key))
            elif key == 'play' or key == 'open' or key == 'up' or key == 'loop':
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
              (self.key_order[index.column()] == 'up') or
              (self.key_order[index.column()] == 'marks') or
              (self.key_order[index.column()] == 'play') or
              (self.key_order[index.column()] == 'loop') or
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

                elif key in ['media']:
                    #content = index.internalPointer()

                    #key = self.key_order[index.column()]
                    #could check for special keys here:
                    #assert key == 'media'
                    items = make_media_file_list(content.media)        

                    ## print items
                    ## print "filename pre:", content.filename
                    ## print value
                    new_name = items[value]
                    
                    setattr(content, 'filename', new_name)
                    if hasattr(content, 'segments'):
                        for segment in content.segments:
                            setattr(segment, 'filename', new_name)
                            
                    setattr(content, 'filename', new_name)
                    content.save()
                    #print "filename post:", content.filename
                    
                
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
                json_path = os.path.join(content.path, content.json_source)
                items.append( [json_path, content.segment_id] )
            else:
                pass
                #print "duplicate row: %s" % index.row()                
            
        #item = self.getNode( indices[0] )

        #mimedata.setData('text/xml', item)
        print json.dumps(items)

        #everything = {'row_nums':row_nums, 'items':items}
        everything = {'items':items}
        
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
        #row_nums = everything['row_nums']
        items = everything['items']
        
        if action == QtCore.Qt.DropAction.MoveAction:
            # old way using row numbers:
            #
            ## #remove old row_nums first:
            ## row_nums.sort()
            ## row_nums.reverse()
            ## print "removing rows first: %s" % row_nums
            ## for row in row_nums:
            ##     self.removeRows(row)


            #try to remove the sent items from self,
            #but if items are from a different PlaylistView, they won't exist...
            #removing from source is a trickier task...
            
            for item in items:
                (path, segment_id) = item
                #it really should, unless it is a locally created Content obj
                if all_contents.has_key(path):
                    content = all_contents[path]
                    segment = content.get_segment(segment_id)
                    if segment in self.playlist:
                        row = self.playlist.index(segment)
                        
                        self.beginRemoveRows( QtCore.QModelIndex(), row, row )
                        self.playlist.remove(segment)
                        self.endRemoveRows()


        start_pos = parent.row()

        self.beginInsertRows( QtCore.QModelIndex(), int(start_pos), int(len(items)+start_pos)-1 )
        print "len pre-insert: %s" % len(self.playlist)

        print "starting at row: %s" % start_pos
        position = start_pos
        for item in items:
            (path, segment_id) = item
            #it really should, unless it is a locally created Content obj
            if all_contents.has_key(path):
                content = all_contents[path]
                segment = content.get_segment(segment_id)
                #content = Content(content=item)
                self.playlist.insert(position, segment)
                position += 1
            else:
                print "COULDN'T FIND CONTENT: %s, %s" % (path, segment_id)

        print "len pre-insert: %s" % len(self.playlist)
        self.endInsertRows()
            
        self.dataChanged.emit( parent, parent )
        return True        


#http://stackoverflow.com/questions/17615997/pyqt-how-to-set-qcombobox-in-a-table-view-using-qitemdelegate
class MediaComboDelegate(QtGui.QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
        
    def createEditor(self, parent, option, index):
        self.combo = QtGui.QComboBox(parent)

        media_json = index.model().data(index, QtCore.Qt.EditRole)
        media = json.loads(media_json)
        #print media

        self.items = make_media_file_list(media)        
            
        self.combo.addItems(self.items)

        self.connect(self.combo, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        return self.combo
        
    def setEditorData(self, editor, index):
        content = index.internalPointer()
        cur_index = 0
        if content.filename in self.items:
            cur_index = self.items.index(content.filename)
            
        #print content
        #index.model().key_order.index('media')
        editor.blockSignals(True)
        #print self.items[int(index)]
        #editor.setCurrentIndex(int(index.model().data(index)))
        editor.setCurrentIndex(cur_index)
        #print "editor index: ", editor.currentIndex()
        editor.blockSignals(False)
        
    def setModelData(self, editor, model, index):
        ## content = index.internalPointer()

        ## #key = self.key_order[index.column()]
        ## #could check for special keys here:
        ## #assert key == 'media'

        ## print self.items
        ## print "filename pre:", content.filename
        ## print editor.currentIndex()
        ## setattr(content, 'filename', self.items[editor.currentIndex()])
        ## content.save()
        ## print "filename post:", content.filename

        
        model.setData(index, editor.currentIndex())

        ## print "Editor:"
        ## print dir(editor)
        ## print type(editor)
        ## print editor
        ## print

        ## print "Model:"
        ## print dir(model)
        ## print type(model)
        ## print model
        ## print

        ## print "Index:"
        ## print dir(index)
        ## print type(index)
        ## print index
        ## print

        
    @QtCore.Slot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())


class PlaylistView(QtGui.QTableView):
    """
    customizing TableView to handle drag and drop correctly:
    http://stackoverflow.com/questions/10264040/how-to-drag-and-drop-into-a-qtablewidget-pyqt
    """
    def __init__(self, parent=None, marks_col=None, titles_col=None):
        super(PlaylistView, self).__init__(parent)
        ## self.model = None
        ## self.last_folder = None

        self.marks_col = marks_col
        self.titles_col = titles_col

        #self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setAlternatingRowColors(True)
        #self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        #self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        #this is what allows drag and drop from one position to another:
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

        #until something else gets set:
        blank_list = PlaylistModel(Playlist())
        self.setModel(blank_list)

    def dragEnterEvent(self, evt):
        #This works, but the drop does not...
        #not sure why!
        mime_data = evt.mimeData()
        print "DRAAAG!"
        #print dir(mime_data)
        #print mime_data.data
        #print mime_data.property
        if mime_data.hasUrls():
            self.dropFile = mime_data.urls()[0].toLocalFile()
            print self.dropFile
            #ideally this would happen in actual drop:
            self.add_media(self.dropFile)
            evt.acceptProposedAction()
            #evt.accept()

    def dropEvent(self, evt):
        mime_data = evt.mimeData()
        print "DROPP!"
        print self.dropFile
        #print dir(mime_data)
        evt.acceptProposedAction()
        
    def setModel(self, model):
        super(PlaylistView, self).setModel(model)
        #self.model = model

        #checking to see if the shortcut (following line) works instead of this:
        ## self.connect(self.selectionModel(),  
        ##              QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),  
        ##              self.store_current_selection)

        #this seems to perform the same function:
        #keeping both versions around, since legacy code uses SIGNAL
        #this is a good reminder/guide on how to convert them
        #self.selectionModel().selectionChanged.connect(self.store_current_selection)

        sm = self.selectionModel()
        #this is needed to avoid SegFaults on Linux:
        #http://srinikom.github.io/pyside-bz-archive/1041.htlm
        #sm.setParent(None)

        sm.selectionChanged.connect(self.store_current_selection)

        loop_index = self.model().key_order.index('loop')
        play_index = self.model().key_order.index('play')
        open_index = self.model().key_order.index('open')
        up_index = self.model().key_order.index('up')
        order_index = self.model().key_order.index('order')
        title_index = self.model().key_order.index('title')
        status_index = self.model().key_order.index('status')
        start_index = self.model().key_order.index('start')

        self.setColumnWidth(loop_index, 25)
        self.resizeColumnToContents(play_index)
        self.resizeColumnToContents(open_index)
        self.resizeColumnToContents(up_index)
        self.resizeColumnToContents(order_index)
        #self.resizeColumnToContents(title_index)
        self.resizeColumnToContents(status_index)
        self.resizeColumnToContents(start_index)

        if 'media' in self.model().key_order:
            media_index = self.model().key_order.index('media')
            print media_index
            self.setItemDelegateForColumn(self.model().key_order.index('media'), MediaComboDelegate(self))
            for row in range(0, self.model().rowCount(self)):
                self.openPersistentEditor(self.model().index(row, media_index, self))
                

    def store_current_selection(self, newSelection, oldSelection):
        """
        update the currently selected Content item
        """
        if len(newSelection.indexes()):
            self.cur_index = newSelection.indexes()[0]
            self.cur_content = self.cur_index.internalPointer()
        
    def check_click(self, index):
        """
        connect this with the doubleClicked signal
        to see what was clicked on
        """
        #print "DOUBLE CLICK: %s %s" % (index.row(), index.column())

        if self.model().key_order[index.column()] == 'open' or self.model().key_order[index.column()] == 'up':
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

            if self.model().key_order[index.column()] == 'up':
                #TODO:
                #find parent content of self.cur_content
                #set self.cur_content to that
                self.content_view.update_view(self.cur_content.parent)
            else:
                #update current content with selected content
                #do this if the window is new or old:
                self.content_view.update_view(self.cur_content)
            self.content_view.activateWindow()
            self.content_view.raise_() # just to be sure it's on top


        if self.model().key_order[index.column()] == 'loop':
            #print "Loop: %s" % self.cur_content.title
            self.model().playlist.set_current(self.cur_content)

            #self.marks_col and self.titles_col both have
            #a main content object associated with them
            #this is the item that gets updated
            #and eventually synchronized with self.model().playlist
            #will try to access it directly
            #self.player.play(self.cur_content, self.model().playlist, self.marks_col, self.titles_col, loop=True)
            self.player.play(self.cur_content, self.model().playlist, parent_content=self.marks_col.content, loop=True)


        if self.model().key_order[index.column()] == 'play':
            #print "Play: %s" % self.cur_content.title
            #maybe it is better to pass self.model().playlist?
            #print self.cur_content.to_dict()
            self.model().playlist.set_current(self.cur_content)
            #self.player.play(self.cur_content, self.model().playlist, self.marks_col, self.titles_col)

            #in a window with only a playlist_view, may not be a marks_col...
            #no easy access to parent content in that case
            if self.marks_col:
                self.player.play(self.cur_content, self.model().playlist, parent_content=self.marks_col.content, loop=False)
            else:
                self.player.play(self.cur_content, self.model().playlist)
            
            #print main_player
            #main_player.play(self.cur_content, self.model().playlist, self.marks_col, self.titles_col)

    
    def open_window(self):
        """
        http://stackoverflow.com/questions/8478210/how-to-create-a-new-window-button-pyside-pyqt
        """
        #self.content_view = QtGui.QMainWindow(self)
        self.content_view = ContentWindow(self.player, self)
        #self.content_view = ContentWindow(self)
        #self.content_view.resize(840, 400)
        #self.content_view.resize(640, 250)
        self.content_view.resize(960, 300)
        self.content_view.show()

    def add_contents(self, contents):
        """
        helper for add_media to do the actual update of View Model

        #TODO:
        working on migrating this functionality to PlaylistModel.add_contents.
        """

        ## parent = self.model().getNode(self.cur_index)
        ## child_count = parent.childCount()

        #how many to insert:
        #count = 1
        count = len(contents)
        total_rows = self.model().rowCount(None)

        self.model().beginInsertRows( self.cur_index, total_rows, total_rows+count-1 )

        #for i in range(count):
        for content in contents:
            self.model().playlist.append(content)
            ## name_only = os.path.basename(fname)
            ## child = Node(name_only)
            ## child.source = fname

            ## #open fname here and assign Playlist object as child.content
            ## playlist = load_playlist(fname)
            ## child.content = playlist
            ## #add Node to tree of playlists:
            ## success = parent.insertChild(child_count, child)
            
        self.model().endInsertRows()
        #print self.model().playlist

        return "success"
    
    def add_media(self, fname):
        all_results = True
        contents = []

        contents = find_contents(fname)
        
        print "CONTENTS DURING LOAD: %s" % contents
        result = self.add_contents(contents)
            
        if not result:
            all_results = False
        
        return all_results

    def add_content_dialog(self):
        """
        open a open dialog to select the json source of a Content object
        load the Content object
        then append it to self.model().playlist
        """
        #can implement this later if it would be helpful:
        self.last_folder = None
        
        if self.last_folder:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open Content',
                                                         self.last_folder)
        else:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open Content')

        content = Content(fname)

        result = self.add_contents([content])
        
        return result

    def add_media_dialog(self):
        """
        open a open dialog to select a media file
        check if there is an associated Content object (load it if so)

        if not, create a new Content object
        then append it to self.model().playlist
        """
        #can implement this later if it would be helpful:
        self.last_folder = None
        
        if self.last_folder:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open Media',
                                                         self.last_folder)
        else:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open Media')

        result = self.add_media(fname)
        return result

    def add_folder_dialog(self):
        """
        open a open dialog to select a media file
        check if there is an associated Content object (load it if so)

        if not, create a new Content object
        then append it to self.model().playlist
        """
        #can implement this later if it would be helpful:
        self.last_folder = None
        
        if self.last_folder:
            fname = QtGui.QFileDialog.getExistingDirectory(self, 'Open Directory',
                                                              self.last_folder)
        else:
            fname = QtGui.QFileDialog.getExistingDirectory(self, 'Open Directory')

        result = self.add_media(fname)
        return result

class PlaylistWidget(QtGui.QWidget):
    """
    combine PlaylistView with a toolbar to facilitate deleting and adding items
    """
    def __init__(self, parent=None, table=None, marks_col=None, titles_col=None):
        super(PlaylistWidget, self).__init__(parent)
        
        #should work the same:
        #self.layout = QtGui.QGridLayout()
        self.layout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        self.playlist_view = PlaylistView(self, marks_col=marks_col, titles_col=titles_col)
        self.layout.addWidget(self.playlist_view)

        playlist_toolbar = QtGui.QToolBar()
        playlist_toolbar.setIconSize(QtCore.QSize(16, 16))

        #TODO:
        #action is not yet implemented
        #
        ## addAction = QtGui.QAction(QtGui.QIcon('images/plus.png'), 'Add', self)
        ## #addAction.setShortcut('Ctrl+N')
        ## addAction.triggered.connect(self.add_item)
        ## playlist_toolbar.addAction(addAction)

        removeAction = QtGui.QAction(QtGui.QIcon('images/minus.png'), 'Remove', self)
        removeAction.triggered.connect(self.remove_item)
        playlist_toolbar.addAction(removeAction)


        folderAction = QtGui.QAction(QtGui.QIcon('images/folder-o.png'), 'Folder', self)
        folderAction.triggered.connect(self.launch_finder)
        playlist_toolbar.addAction(folderAction)


        self.row = QtGui.QHBoxLayout()
        self.row.addWidget(playlist_toolbar)

        ## self.row.addWidget(self.player.time_passed)
        ## self.row.addWidget(self.player.time_remain)
        ## self.row.insertStretch(2, 50)

        #self.layout.addWidget(playlist_toolbar)
        self.layout.addLayout(self.row)

        self.setLayout(self.layout)


    def add_item(self, name=''):
        print "ADD ITEM from PlaylistWidget"
        
    def remove_item(self, row=None):
        if row is None:
            row = self.playlist_view.cur_index.row()

        self.playlist_view.model().removeRows(row)

    def launch_finder(self, row=None):
        if row is None:
            row = self.playlist_view.cur_index.row()

        content = self.playlist_view.model().playlist[row]
        print content.path
        file_browse(content.path)

class MarksWidget(QtGui.QWidget):
    """
    combine the list view with a toolbar for different actions

    needs to be its own widget to be added to the splitter
    """
    def __init__(self, player, parent=None):
    #def __init__(self, parent=None):
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

        snapshotAction = QtGui.QAction(QtGui.QIcon('images/camera.png'), 'Take Snapshot', self)
        snapshotAction.triggered.connect(self.take_snapshot)
        marks_toolbar.addAction(snapshotAction)

        removeAction = QtGui.QAction(QtGui.QIcon('images/minus.png'), 'Remove', self)
        removeAction.triggered.connect(self.remove_mark)
        marks_toolbar.addAction(removeAction)

        ## openAction = QtGui.QAction(QtGui.QIcon('images/open.png'), 'Import from file', self)
        ## openAction.triggered.connect(self.open_marks)
        ## marks_toolbar.addAction(openAction)

        ## saveAction = QtGui.QAction(QtGui.QIcon('images/save.png'), 'Export to file', self)
        ## saveAction.triggered.connect(self.save_marks)
        ## marks_toolbar.addAction(saveAction)

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

        (updates the view)
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



    def add_mark(self, tag=''):
        #get current position from player (00:00 is ok)
        if self.player:
        #if main_player:
            time = self.player.currentTime()
            #time = main_player.currentTime()
            
            #display_time = QtCore.QTime((time / 3600000), (time / 60000) % 60, (time / 1000) % 60)
            #hours = time / 3600000
            mark = Mark(tag, time)
            self.content.marks.append(mark)
            self.sync()
            #mark = "%s - %s" % (display_time.toString('h:mm:ss'), mark)
            #self.marks.addItem(mark)
        else:
            print "NO player object assigned to self: %s" % self.player
            #print "NO shared player object available: %s" % main_player
            #self.marks.addItem(mark)
            mark = Mark(mark, 0)
            self.content.marks.append(mark)
            self.sync()

        return mark
    
    def remove_mark(self, row=None):
        if row is None:
            row = self.marks.currentRow()

        self.marks.takeItem(row)
        self.content.marks.pop(row)    

    def on_changed(self, item):
        """
        handle a manual edit of a mark after change accepted
        
        occasionally crashes with following traceback:

Traceback (most recent call last):
  File "/c/medley/player/playlist_view.py", line 736, in on_changed
    row = self.marks.row(item)
TypeError: 'PySide.QtGui.QListWidget.row' called with wrong argument types:
  PySide.QtGui.QListWidget.row(PySide.QtGui.QItemSelectionModel)
Supported signatures:
  PySide.QtGui.QListWidget.row(PySide.QtGui.QListWidgetItem)
Segmentation fault: 11        
        """

        if isinstance(item, QtGui.QListWidgetItem):
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

        else:
            print dir(item)
            print "Item: %s" % item
            raise TypeError, "WRONG TYPE SENT: %s" % type(item)
            
    def open_marks(self):
        pass

    def save_marks(self):
        pass

    def merge_titles(self):
        new_prefix = self.track_prefix.text()
        self.content.track_prefix = new_prefix

        #if not self.content.remainder.has_key("tracks"):
        #    self.content.remainder['tracks'] = [ "1. " ]
        #if not len(self.content.titles):
        #    self.titles.append("1. ")
        
        #tracks = self.content.remainder['tracks']
        #self.content.marks.make_segments(self.content, titles=tracks)
        self.content.marks.make_segments(self.content)
        self.content.history.make("Merging titles with marks", ["merge"])
        self.content.save()

        #refresh ContentWindow with latest changes
        self.parent().parent().update_view(self.content)

    def add_mark_and_title(self, title='', add_index=True):
        """
        similar to add_mark
        but also add a title
        and shift any following title numbers accordingly

        if add_index is True,
        will look for the index at the current mark position
        add that index to the current title
        then increment all subsequent titles

        this may not be necessary if the new mark is not meant
        to designate a new segment (just a note)

        but in this case, isn't easier to just use the mark.title
        to keep everything in the right place?
        """

        if self.player:
            time = self.player.currentTime()
            mark = Mark(mark, time)

            self.content.marks.sort()
            index = 0
            found = False
            new_pos = None
            for existing in self.content.marks:
                if not found and (existing.position > mark.position):
                    found = True
                    new_pos = index
                index += 1

            if len(self.content.titles) > new_pos:
                new_pos_number = None

                for item in self.content.titles[new_pos:]:
                    #go through and increment all subsequent titles
                    #then create a new title
                    item = self.content.titles[new_pos]
                    m = find_number.search(title)
                    if m:
                        number = int(m.group(1))
                        #print "("+int1+")"+"\n"
                        #sorting.append( (int(int1), title) )

            #self.content.marks.append(mark)
            self.sync()
            #mark = "%s - %s" % (display_time.toString('h:mm:ss'), mark)

        else:
            #nothing to get a time from
            pass

    def take_snapshot(self):
        """
        add a new mark with a corresponding title
        """
        for existing in self.content.marks:
            if existing.tag == "snapshot, default":
                existing.tag = "snapshot"
                                
        mark = self.add_mark('snapshot, default')

        #this always returns null image:
        #seems to be a known bug:
        #http://qt-project.org/forums/viewthread/2487
        #image = self.player.video.snapshot()

        #this will include any windows that are over the video window
        image = QtGui.QPixmap.grabWindow(self.player.video_window.winId())
        
        options = os.listdir(self.content.path)
        #print self.content.path
        #print options
        destination = os.path.join(self.content.path, "1.jpg")
        if os.path.exists(destination):
            index = 2
            available = None
            while not available:
                name = "%s.jpg" % index
                option = os.path.join(self.content.path, name)
                if not os.path.exists(option):
                    available = option
                index += 1
            #move the existing 1.jpg to the new available option:
            os.rename(destination, available)

        result = image.save(destination, "JPEG", quality=100)
        print "Image Saved: %s" % destination
        #print "Null?: %s" % image.isNull()
        #print image.size()
        #print result

        #format is not a method of QPixmap
        #print image.format()
        
        
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
        #if self.content and self.content.remainder.has_key('tracks'):
        if self.content:
            new_order = []
            for row in range(self.count()):
                print self.item(row).text()
                new_order.append(self.item(row).text())
            #self.content.remainder['tracks'] = new_order
            self.content.titles = new_order
            #self.content.remainder['tracks'].sort()
            #for title in self.content.remainder['tracks']:
        self.parent().sync()

class EditTitlesDialog(QtGui.QDialog):
    """
    subclass QDialog:
    http://srinikom.github.io/pyside-docs/PySide/QtGui/QDialog.html#PySide.QtGui.QDialog
    """
    def __init__(self, parent=None, contents="test test test\nabcd"):
        super(EditTitlesDialog, self).__init__(parent)
        self.setWindowTitle("Bulk edit titles...")
        self.setModal(True)
        self.layout = QtGui.QVBoxLayout()
        self.text = QtGui.QPlainTextEdit()
        self.text.setPlainText(contents)
        self.layout.addWidget(self.text)

        self.row = QtGui.QHBoxLayout()

        cancel_button = QtGui.QPushButton("Cancel")
        self.row.addWidget(cancel_button)
        ok_button = QtGui.QPushButton("OK")
        self.row.addWidget(ok_button)

        self.layout.addLayout(self.row)

        self.setLayout(self.layout)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        
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
        #addAction.triggered.connect(self.add_title)
        addAction.triggered.connect(self.new_title)
        titles_toolbar.addAction(addAction)

        removeAction = QtGui.QAction(QtGui.QIcon('images/minus.png'), 'Remove', self)
        removeAction.triggered.connect(self.remove_title)
        titles_toolbar.addAction(removeAction)

        ## openAction = QtGui.QAction(QtGui.QIcon('images/open.png'), 'Import from file', self)
        ## openAction.triggered.connect(self.open_titles)
        ## titles_toolbar.addAction(openAction)

        ## saveAction = QtGui.QAction(QtGui.QIcon('images/save.png'), 'Export to file', self)
        ## saveAction.triggered.connect(self.save_titles)
        ## titles_toolbar.addAction(saveAction)

        detailsAction = QtGui.QAction(QtGui.QIcon('images/details.png'), 'Show details in console', self)
        detailsAction.triggered.connect(self.content_details)
        titles_toolbar.addAction(detailsAction)

        editAction = QtGui.QAction(QtGui.QIcon('images/edit.png'), 'Show edit in console', self)
        editAction.triggered.connect(self.bulk_edit_titles)
        titles_toolbar.addAction(editAction)

        self.layout.addWidget(titles_toolbar)

        self.setLayout(self.layout)

    def bulk_edit_titles(self):
        if self.content:
            #merge all titles into lines of text
            combined = ''
            for title in self.content.titles:
                combined += title + '\n'
            #print combined
            
            #show those in an edit dialog 
            edit = EditTitlesDialog(self, combined)
            #edit.show()
            #make it blocking:
            edit.exec_()

            #print "Result = ", edit.text.toPlainText()
            #print text
            #print ok
            #on close, split them back up into separate titles

            updated = []
            for line in edit.text.toPlainText().splitlines():
                updated.append(line)

            self.content.titles = updated
            self.sync()

        else:
            print "NO CONTENT assigned to self: %s" % self.content
            print "no titles to edit?"
            print
            
    def on_changed(self, item):
        row = self.titles.row(item)
        #if self.content.remainder.has_key('tracks'):
            #tracks = self.content.remainder['tracks']

        if row < len(self.content.titles):
            title = self.content.titles[row]
            #title = self.content.titles[row]
            if title != item.text():
                self.content.titles[row] = item.text()
                #print "Titles.on_change called: %s, %s" % (item.text(), title)
                #be careful where sync is called...
                #easy to get into an infinite loop with this
                self.sync()
        else:
            #must have a new item... just append it:
            self.content.titles.append(item.text())
            self.sync()


    def new_title(self, title='-'):        
        #if title == '-' and self.content.remainder.has_key('tracks'):
        if title == '-':
            #passed the default...
            #try to find the next number to add automatically

            #self.content.remainder['tracks'].sort()

            #tracks = self.content.remainder['tracks']
            #tracks = self.content.titles
            #print "TRACKS: %s" % tracks

            sorting = []
            #for title in tracks:
            for title in self.content.titles:
                #m = rg.search(title)
                m = find_number.search(title)
                if m:
                    int1 = m.group(1)
                    #print "("+int1+")"+"\n"
                    sorting.append( (int(int1), title) )
            sorting.sort()
            if len(sorting):
                number = sorting[-1][0]
                plus = number + 1
                title = "%s. " % plus
            else:
                title = "1. "

        item = self.add_title(title)

        #on_changed will recreate the list, so item will not be the same
        #get the row, then we can get the new item by row
        row = self.titles.row(item)
        
        #sync back up with model:
        self.on_changed(item)

        item = self.titles.item(row)
        self.titles.editItem(item)
        
        #print item.flags()
        #self.titles.addItem(title)

    def add_title(self, title):

        #don't insert to list right away... we want to keep a reference around
        #item = QtGui.QListWidgetItem(title, self.titles)
        item = QtGui.QListWidgetItem(title)
        item.setFlags( QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | \
                       QtCore.Qt.ItemIsDragEnabled | \
                       QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable )
        #self.titles.insertItem(-1, item)
        self.titles.addItem(item)

        return item
    
    def sync(self):
        """
        synchronize the contents of content.titles
        with what is in QListWidget
        """
        #print content.to_dict()
        self.titles.clear()
        #self.titles.addItems(content.remainder['titles'])
        #if self.content.remainder.has_key('tracks'):

        #self.content.remainder['tracks'].sort()
        #re1='(\\d+)(\.)'	# Integer Number 1
        #rg = re.compile(re1,re.IGNORECASE|re.DOTALL)

        #tracks = self.content.remainder['tracks']
        #print "TRACKS: %s" % tracks

        sorting = []
        for title in self.content.titles:
            #m = rg.search(title)
            m = find_number.search(title)
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

        #self.content.remainder['tracks'] = updated
        self.content.titles = updated

        for title in updated:
            self.add_title(title)
        #self.titles.addItems(content.remainder['tracks'])


    def remove_title(self, row=None):
        if row is None:
            #take currently selected item instead
            row = self.titles.currentRow()

        self.titles.takeItem(row)
        #this might be unnecessary after self.titles runs sync
        #seems very necessary
        #self.content.remainder['tracks'].pop(row)    
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
            #printing json instead of dict()...
            #just incase something isn't working as expected...
            #this can salvage changes
            print json.dumps(self.content.to_dict())
            print self.content.debug()
        else:
            print "NO CONTENT assigned to self: %s" % self.content


class ContentWindow(QtGui.QMainWindow):
    def __init__(self, player, parent=None):
    #def __init__(self, parent=None):
        super(ContentWindow, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('Content View')

        self.splitter = QtGui.QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)

        self.marks_col = MarksWidget(player, self)
        #self.marks_col = MarksWidget(self)

        self.titles_col = TitlesWidget(self)
        #self.splitter.addWidget(self.titles)

        #self.table = PlaylistView(self)
        self.table = PlaylistWidget(self, marks_col=self.marks_col, titles_col=self.titles_col)
        self.splitter.addWidget(self.table)

        #self.splitter.addWidget(self.marks)
        self.splitter.addWidget(self.marks_col)

        self.splitter.addWidget(self.titles_col)

        #self.marks = QtGui.QListWidget(self)
        #self.splitter.addWidget(self.marks)

        self.splitter.setStretchFactor(0, 60)
        self.splitter.setStretchFactor(1, 20)
        self.splitter.setStretchFactor(2, 20)

        #self.setCentralWidget(self.table)
        self.setCentralWidget(self.splitter)

        make_mark = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+M'),
                                    self, self.marks_col.add_mark)

        make_title = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+N'),
                                    self, self.titles_col.new_title)

        make_segments = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+S'),
                                        self, self.marks_col.merge_titles)

        screen_capture = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+B'),
                                         self, self.marks_col.take_snapshot)

        plays = QtGui.QShortcut(QtGui.QKeySequence(" "), self,
                                player.toggle_play)

        scanfs = QtGui.QShortcut(QtGui.QKeySequence('Alt+Right'),
                                self, player.forward)

        scanbs = QtGui.QShortcut(QtGui.QKeySequence('Alt+Left'),
                                self, player.back)

        jumpfs = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Right'),
                                self, player.jumpf)

        jumpbs = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Left'),
                                self, player.jumpb)

        nexts = QtGui.QShortcut(QtGui.QKeySequence('Alt+Down'),
                                self, player.next)
        nexts = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Down'),
                                self, player.next)

        prevs = QtGui.QShortcut(QtGui.QKeySequence('Alt+Up'),
                                self, player.previous)
        prevs2 = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Up'),
                                self, player.previous)

        faster = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+,'),
                                self, player.slower)
        slower = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+.'),
                                self, player.faster)



        self.content = None
        self.table.playlist_view.player = player

        #this removes the time widgets from the main player
        #then when window is closed, they get deleted.
        #that makes things unhappy.
        #self.table.row.addWidget(player.time_passed)
        #self.table.row.addWidget(player.time_remain)
        #self.table.row.insertStretch(2, 50)

    def update_view(self, content):
        self.content = content

        #self.setWindowTitle(content.title)
        self.setWindowTitle(content.filename)
        playlist = Playlist(self.content.segments)

        #key_order = ['open', 'order', 'tags', 'start', 'play', 'title', 'status', 'timestamp', 'people', 'segments', 'marks', 'end', 'up', ]
        key_order = ['loop', 'open', 'play', 'start', 'title', 'filename', 'people', 'tags', 'timestamp', 'segments', 'marks', 'end', 'order', 'status', 'up', ]
        #key_order = None
        
        subtree = PlaylistModel(playlist, key_order=key_order)

        self.table.playlist_view.setModel(subtree)

        #only want to expand here:
        title_index = self.table.playlist_view.model().key_order.index('title')
        self.table.playlist_view.resizeColumnToContents(title_index)
        

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

