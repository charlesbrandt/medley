"""
        all_contents is the global place to store all content objects
        if a requested content source is already loaded,
        use it instead of loading a new one

#TODO:
#consider a simpler global variable / object for all_contents
#rather than passing around everywhere...
#could then be imported by any other module that needs it

        #this is meant to be a global place
        #to store all loaded content objects
        #with the source path as the key
        #then when other playlists are loaded with the same content
        #they can reference the same object
        #self.all_contents = {}
        #moving this to a separate module so that it can be easily imported
        #anywhere that it is needed.
        #cumbersome to try to pass this around
        #TODO:
        #commented out all references to passed in 'all_contents'
        #can go and remove once global appraoch is verified


"""
# simple place to keep track of all loaded content objects

all_contents = {}


# rather than pass this in everywhere, allow it to be imported
#since this is a widget, it probably needs to created like before
#main_player = None
#main_player = PlayerWidget(self)
#main_player = PlayerWidget(None)

