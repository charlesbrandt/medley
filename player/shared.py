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
        #can go and remove once global approach is verified


"""
from medley.helpers import load_json, save_json

# simple place to keep track of all loaded content objects

all_contents = {}

# rather than pass this in everywhere, allow it to be imported
#since this is a widget, it probably needs to created like before
#main_player = None
#main_player = PlayerWidget(self)
#main_player = PlayerWidget(None)

config_source = 'configs.json'

class Configs(object):
    def __init__(self):
        global config_source
        self.configs = load_json(config_source, create=True)

        #aka drive_dir ??? (be consistent with content Object?)
        #maybe last_folder is a different configuration
        if self.configs.has_key('last_folder'):
            self.last_folder = self.config['last_folder']
        else:
            self.last_folder = '/'

    def get(self, key):
        """
        automatcially check if we have the key
        return blank if none exists
        """

        if self.configs.has_key(key):
            return self.configs[key]
        else:
            return ''

    def save_configs(self):
        """
        save self.configs to local 'configs.json' file
        """
        global config_source
        #save_json(self.config_source, self.configs)
        save_json(config_source, self.configs)
    
configs = Configs()
