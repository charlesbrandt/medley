import os, json

from PySide import QtGui, QtCore

from medley.helpers import load_json, save_json
from medley.playlist import Playlist
from medley.content import Content

from shared import all_contents, configs
from playlist_view import PlaylistModel

def load_playlist(fname):
    """
    expects the playlist to hold:
       - the content source path
       - the segment id

    then loads the content from the source, and selects the correct segment
    """
    items = load_json(fname)
    #print items
    contents = []
    for item in items:
        #print item
        #print ""
        (json_source, segment_id) = item
        if all_contents.has_key(json_source):
            #print "Matched existing Content object with path: %s" % json_source
            content = all_contents[json_source]
        else:
            content = Content(json_source)
            all_contents[json_source] = content

        print json_source
        segment = content.get_segment(segment_id)
        #print segment.to_dict()
        #print ""
        #print ""
        contents.append(segment)
    return Playlist(contents)

class Node(object):
    """
    """
     
    def __init__( self, name, parent=None ):
        """
        Instantiates a new tree item

        #TODO:
        adapt to standard tree item interface for consistency
        """
        self._name = name
         
        self._parent = parent
        self.children = []

        self.source = ''
        self.content = Playlist()

        if parent is not None:
            parent.addChild(self)


    def __str__(self):
        return str(self._name)

    def __repr__(self):
        return str(self._name)
        #return self.log()

    def typeInfo(self):
        return "NODE"

    def addChild(self, child):
        self.children.append(child)
        child._parent = self
        return True

    def insertChild(self, position, child):
        
        if position < 0 or position > len(self.children):
            return False
        
        self.children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):
        
        if position < 0 or position > len(self.children):
            return False
        
        child = self.children.pop(position)
        child._parent = None

        return True

    def name(self):
        return self._name

    def setName(self, name):
        self._name = name

    def child(self, row):
        if row < len(self.children):
            return self.children[row]
        else:
            print "No child at row: %s" % row
            return None
    
    def childCount(self):
        return len(self.children)

    def parent(self):
        return self._parent
    
    def row(self):
        if self._parent is not None:
            return self._parent.children.index(self)



    def as_dict(self):
        """
        return a simple dictionary representation of the node
        (useful for serializing)
        """
        copy = {}
        
        copy['name'] = self.name()
        #assumes this is ok for JSON.dumps:
        #if it refers to a Playlist object, it probably is not OK
        #copy['content'] = self.content
        #TODO:
        #in that case, it's better to save the Playlist to self.source
        
        copy['source'] = self.source
        copy['children'] = []

        for child in self.children:
            copy['children'].append(child.as_dict())

        return copy
                
    def to_json(self):
        """
        json representation of object
        """
	return json.dumps(self.as_dict())

    def save_all(self):
        """
        recursively call save for all nodes
        """
        self.save()
        for child in self.children:
            child.save_all()

    def save(self):
        """
        save the current playlist

        different than to_json, which creates the whole structure,
        including children
        """
        if self.source:
            #content is really a Playlist object here
            #TODO:
            #refactor this to be less confusing.
            self.content.save(self.source)
        
    def from_json(self, data='', item={}):
        """
        load a previously serialized Node structure
        data assumed to be a json string
        item assumed to be a simple object (non Node)
        """

        #node = Node("temp")

        if data:
            simple = json.loads(data)
        elif item:
            simple = item
        else:
            raise ValueError, "No data to load from_json: %s" % data

        #print simple
        
        if simple.has_key('name'):
            self.setName(simple['name'])

        #ok to load it if it has it, but probably better to load source
        if simple.has_key('content'):
            self.content = simple['content']

        if simple.has_key('source'):
            self.source = simple['source']
            print "loading playlist: %s" % self.source
            if self.source:
                #load self.source into self.content here
                playlist = load_playlist(self.source)
                self.content = playlist
            else:
                #no source specified
                #create an empty Playlist here instead
                self.content = Playlist()
                #TODO:
                #should check if a Playlist has any changes before saving
                #also consider a setting an option to automatically
                #increment a date section of a filename if changes occur
                #(for automated file versions)

        if simple.has_key('children'):
            for item in simple['children']:
                child = Node('child')
                child.from_json(item=item)
                self.addChild(child)

    def log(self, tabLevel=-1):

        output     = ""
        tabLevel += 1
        
        for i in range(tabLevel):
            output += "\t"
        
        output += "|------" + self._name + "\n"
        
        for child in self.children:
            output += child.log(tabLevel)
        
        output += "\n"
        
        return output    
            
#other potential base classes
#QtCore.QAbstractListModel
#QtCore.QAbstractTableModel

class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, root, parent=None):
        super(TreeModel, self).__init__(parent)
        self.root = root
        
    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self.root
        else:
            parentNode = parent.internalPointer()

        return parentNode.childCount()

    def columnCount(self, index):
        """
        how many columns to show?
        """
        #return 2
        return 1
    
    def data(self, index, role):
        """
        this determines what is displayed in a View
        for a given item at index 'index'

        role determines which context the data is shown in
        """

        if not index.isValid():
            return None

        node = index.internalPointer()

        #print node.log()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            ## row = index.row()
            ## value = self.nodes[row]
            ## return value._name
            if index.column() == 0:
                return node.name()

        ## elif role == QtCore.Qt.DecorationRole:
        ##     if index.column() == 0:
        ##         typeInfo = node.typeInfo()
                
        ##         if typeInfo == "LIGHT":
        ##             return QtGui.QIcon(QtGui.QPixmap(":/Light.png"))
                
        ##     #row = index.row()
        ##     #value = self.nodes[row]

        ##     pixmap = QtGui.QPixmap(26, 26)
        ##     pixmap.fill('#000000')

        ##     icon = QtGui.QIcon(pixmap)
        ##     return icon

        ## elif role == QtCore.Qt.EditRole:
        ##     #what is shown when we're editing an item:
        ##     row = index.row()
        ##     value = self.nodes[row]
        ##     return value._name
        
        elif role == QtCore.Qt.ToolTipRole:
            return "Item details: %s" % node.name()

        elif role == 0: 
            return index.internalPointer()
        else:
            return None

    def headerData(self, section, orientation, role):

        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return "Content"
            else:
                #must be a row name (running vertically):
                return "Item %s" % (section)
                
    def flags(self, index):
        """
        Valid items are selectable, editable, and drag and drop enabled.
        Invalid indices (open space in the view)
        are also drop enabled, so you can drop items onto the top level.
        """
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled
         
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | \
               QtCore.Qt.ItemIsDragEnabled | \
               QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        this handles the new data once an edit is complete
        """
        if index.isValid():
            
            if role == QtCore.Qt.EditRole:
                
                node = index.internalPointer()
                node.setName(value)
                
                return True
        return False

     ## def setData(self, index, value, role = QtCore.Qt.EditRole):
     ##    """
     ##    this handles the new data once an edit is complete
     ##    """
     ##    if role == QtCore.Qt.EditRole:
     ##        row = index.row()
     ##        self.nodes[row]._name = value
     ##        #for alerting other views that the data has changed:
     ##        self.dataChanged.emit(index, index)
     ##        return True

    def insertRows(self, row, count, parentIndex=QtCore.QModelIndex()):
        """
        Add a number of rows to the model at the given row and parent.
        """
        #default parent to the root:
        #parentIndex = QtCore.QModelIndex()
        
        self.beginInsertRows( parentIndex, row, row+count-1 )

        parent = self.getNode(parentIndex)
        for i in range(count):
            childCount = parent.childCount()
            child = Node("untitled" + str(childCount))
            success = parent.insertChild(row, child)
            
        self.endInsertRows()
        return success
     
    def removeRows(self, row, count, parentIndex=QtCore.QModelIndex()):
        """
        Remove a number of rows from the model at the given row and parent.
        """
        self.beginRemoveRows( parentIndex, row, row+count-1 )

        parent = self.getNode(parentIndex)
        for i in range(count):
            success = parent.removeChild(row)
            #value = self.nodes[row]
            #self.nodes.remove(value)
            
        self.endRemoveRows()
        return success


    ## def index(self, row, column, parent):
    ##     return self.createIndex(row, column, self.nodes[row])

    def index(self, row, column, parent):
        """
        Needed for TreeViews specifically
        """
        
        parentNode = self.getNode(parent)

        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        """
        Needed for TreeViews specifically
        """
        node = index.internalPointer()
        parentNode = node.parent()

        if parentNode == self.root:
            return QtCore.QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)
        
    def getNode(self, index):
        """
        Returns the Node instance from a QModelIndex.
        """
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node
            
        return self.root

    def supportedDropActions(self):
        """
        Items can be moved and copied
        """
                
        #return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction         
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction 

    def mimeTypes(self):
        #return ['text/json']
        return ['json/content', 'text/json']

    def mimeData(self, indices):
        mimedata = QtCore.QMimeData()
        item = self.getNode( indices[0] )

        #mimedata.setData('text/xml', item)
        #print json.dumps(item)
        
        mimedata.setData('text/json', item.to_json())
        return mimedata

    def dropMimeData(self, mimedata, action, row, column, parent):
        #print dir(mimedata)
        #print mimedata.data.keys()
        print 'dropMimeData %s %s %s %s' % (mimedata.data('text/json'), action, row, parent)

        formats = mimedata.formats()
        print "formats: %s" % formats
        if 'text/json' in formats:
            item = Node('')
            item.from_json( str(mimedata.data('text/json')) )
            dropParent = self.getNode( parent )
            dropParent.addChild( item )
            #self.insertRows( dropParent.numChildren()-1, 1, parentIndex )
        elif 'json/content' in formats:
            print "Adding content to playlist"
            dropParent = self.getNode( parent )
            #self.cur_node = self.cur_index.internalPointer()
            print "using content: %s" % dropParent.content
            subtree = PlaylistModel(dropParent.content)
            subtree.dropMimeData(mimedata, action, row, column, parent)
            
        self.dataChanged.emit( parent, parent )
        
        return True        


class PlaylistsTreeView(QtGui.QTreeView):
    """
    customizing TreeView to handle selections appropriately:
    http://stackoverflow.com/questions/4160111/pyqt-qtreeview-trying-to-connect-to-the-selectionchanged-signal
    """
    def __init__(self, parent=None):
        """
        """
        super(PlaylistsTreeView, self).__init__(parent)
        
        self.model = None
        self.cur_item = None
        self.cur_index = QtCore.QModelIndex()
        self.cur_node = None
        self.last_folder = None

        root = Node("root")
        ## for i in range(4):
        ##     node = Node('node%s'%i)
        ##     node.addChild(Node('node%s%s'%(i, i)))
        ##     root.addChild(node)
        ## #self.nodes = [Node('node0'), Node('node1'), Node('node2')]
        self.playlists = TreeModel(root)
        #print root.log()

        
        previous = False

        previous_path = configs.get('previously')
        if previous_path and os.path.exists(previous_path):
            #try:
            self.load_lists(previous_path)
            previous = True
            #except:
            #    print "Error loading previous configuration: %s" % previous_path

        ## #old way, when loading configs locally here
        ## if self.configs.has_key('previously'):
        ##     if self.configs['previously']:
        ##         if os.path.exists(self.configs['previously']):
        ##             #try:
        ##             self.load_lists(self.configs['previously'])
        ##             previous = True
        ##             #except:
        ##             #    print "Error loading previous configuration: %s" % self.configs['previously']

        if not previous:
            print "Could not find a valid previous setup... starting blank"
            #self.playlists.root.from_json(item={})
            self.load_lists("blank.json")
                        

        #initialize data here:
        self.setModel(self.playlists)

        #we don't need the header here
        #self.tree_view.setHeaderHidden(True)
        self.setHeaderHidden(True)

        #this only allows moving... no copying:
        #self.tree_view.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        #self.tree_view.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)

        #this sets the default drag mode from Copy (default) to Move
        #move seems more consistent with other interface behavior
        #self.tree_view.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        
        #self.tree_view.setDragEnabled(True)
        #has no effect on trees, but might work in tables
        #self.tree_view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)


    def load_lists(self, fname):
        """
        for internal calls to load
        """
        items = load_json(fname)
        self.playlists.root.from_json(item=items)
        #for item in items:
        #    print type(item)


    def setModel(self, model):
        super(PlaylistsTreeView, self).setModel(model)
        self.model = model

        #checking to see if the shortcut (following line) works instead of this:
        ## self.connect(self.selectionModel(),  
        ##              QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),  
        ##              self.change_selection)

        #this seems to perform the same function:
        #keeping both versions around, since legacy code uses SIGNAL
        #this is a good reminder/guide on how to convert them
        #
        #also [2013.09.10 10:55:31]
        #both versions cause a segfault on linux with the following:
        #Python 2.7.4, Pyside 1.1.2, Qt 4.8.4
        #
        #this happens if nothing was loaded from a previous session
        #and will cause a "Segmentation fault (core dumped)"
        #
        #this one happens sooner since it is called immediately
        #
        #self.selectionModel().selectionChanged.connect(self.change_selection)
        
        sm = self.selectionModel()
        #this is needed to avoid SegFaults on Linux:
        #http://srinikom.github.io/pyside-bz-archive/1041.htlm
        #sm.setParent(None)
        
        sm.selectionChanged.connect(self.change_selection)

    def change_selection(self, newSelection, oldSelection):
        #print "changed"

        #this is *not* a QItemSelectionModel:
        #http://srinikom.github.io/pyside-docs/PySide/QtGui/QItemSelectionModel.html#PySide.QtGui.QItemSelectionModel
        #print newSelection.model()

        #this is a QItemSelection:
        #http://srinikom.github.io/pyside-docs/PySide/QtGui/QItemSelection.html#PySide.QtGui.QItemSelection
        #print newSelection.length()
        #print newSelection.indexes()[0].model().name()


        #there is only one TreeModel object:
        ## self.cur_item = newSelection.indexes()[0].model()
        ## print dir(self.cur_item)
        ## print type(self.cur_item)
        ## print "cur_item"

        # this is true!
        ## assert self.cur_item == self.model
        ## print ""
        
        #make sure we have something before trying to change:
        if newSelection and len(newSelection.indexes()):
            #these are equivalent:
            #print newSelection.indexes()[0].data()
            #and
            self.cur_index = newSelection.indexes()[0]
            #print self.cur_item.data(self.cur_index, QtCore.Qt.DisplayRole)
        
            #print dir(self.cur_index)
            #print type(self.cur_index)
            #print "cur_index"
            #print ""

            self.cur_node = self.cur_index.internalPointer()

            self.parent().change_selection(self.cur_node)

    def update_location(self, destination):
        print "UPDATE LOCATION CALLED: %s" % destination
        self.cur_node.source = destination
        self.cur_node.save()

    def open_list(self):
        """
        only open an individual list and append it to the current tree
        """
        #print "OOOOPEN!!!"

        if self.last_folder:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open Playlist',
                                                         self.last_folder)
        else:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open Playlist')


        #def insertRows(self, row, count, parentIndex=QtCore.QModelIndex()):
        
        parent = self.model.getNode(self.cur_index)
        #how many to insert:
        count = 1
        child_count = parent.childCount()

        self.model.beginInsertRows( self.cur_index, child_count, child_count+count-1 )

        for i in range(count):
            name_only = os.path.basename(fname)
            child = Node(name_only)
            child.source = fname

            #open fname here and assign Playlist object as child.content
            playlist = load_playlist(fname)
            child.content = playlist
            #add Node to tree of playlists:
            success = parent.insertChild(child_count, child)
            
        self.model.endInsertRows()
        return success

    def add(self):
        """
        add a new child node to the currently selected node
        """
        #print "ADDDDDD!!!"

        if self.cur_index:
            #parent = self.cur_index.parent()
            #row = self.cur_index.row()
            #self.model.insertRows(row, 1, parent)
            self.model.insertRows(0, 1, self.cur_index)
        else:
            self.model.insertRows(0, 1)
            

        #if self.cur_index:
        #    new_node = Node("New Node")
        #    self.cur_node.addChild(new_node)

        #print self.model.root.log()

    def remove(self):
        """
        removed the currently selected node
        (and all children?)
        """
        #print "REMOOOOOOVE!!!"

        parent = self.cur_index.parent()
        row = self.cur_index.row()
        self.model.removeRows(row, 1, parent)

        #this works, but something gets out of sync
        #parent = self.cur_node.parent()
        #parent.children.remove(self.cur_node)

        #these do not work:
        #parent.removeChild(self.cur_node)
        #del self.cur_node

        #print self.model.root.as_dict()
        #print self.model.root.log()

    def save_configs(self):
        """
        save self.configs to local 'configs.json' file
        """
        #save_json(self.config_source, self.configs)
        configs.save_configs()

    def open_lists(self):
        """
        generate a TreeModel based on a previously saved structure
        """
        #using self.last_folder to remember previously opened location
        if self.last_folder:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                         self.last_folder)
        else:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file')


        #print "OPEN LISTS CALLED: %s" % fname
        if fname:
            self.load_lists(fname)
            
    def save_lists(self):
        """
        convert the current TreeModel to a json file for later retrieval
        """
        #On OS X these both only flash the Dialog window
        #but never complete the process (until the application exits)
        #fname = QtGui.QFileDialog.getSaveFileName(self, 'Save file', '/')
        #fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', '/')

        #this at least throws an error (but still doesn't work)
        ## options = QtGui.QFileDialog.Options()
        ## if not self.native.isChecked():
        ##     options |= QtGui.QFileDialog.DontUseNativeDialog
        ## fileName, filtr = QtGui.QFileDialog.getSaveFileName(self,
        ##         "QFileDialog.getSaveFileName()",
        ##         self.saveFileNameLabel.text(),
        ##         "All Files (*);;Text Files (*.txt)", options)
        ## if fileName:
        ##     self.saveFileNameLabel.setText(fileName)


        #this thread mentioned a similar issue,
        #https://code.google.com/p/marave/issues/detail?id=91

        #http://srinikom.github.io/pyside-docs/PySide/QtGui/QFileDialog.html#PySide.QtGui.PySide.QtGui.QFileDialog.getOpenFileName

        #which they solved by manually instantiating a QFileDialog
        dlg = QtGui.QFileDialog(self.parent(), "Save as", self.last_folder)
        dlg.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dlg.setFileMode(QtGui.QFileDialog.AnyFile)
	dlg.exec_()

        fname = dlg.selectedFiles()[0]
        if fname:
            print "SAVE LISTS CALLED: %s" % fname

            self.last_folder = os.path.dirname(fname)

            tree = self.playlists.root.as_dict()
            save_json(fname, tree)

            self.playlists.root.save_all()

            #self.configs['previously'] = fname
            configs.configs['previously'] = fname
            self.save_configs()
            #print tree

