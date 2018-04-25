import os
import sys
import json
import logging

class ConfigReader():

    def __init__(self):
        self.logger = logging.getLogger(__name__)  
        self.logger.info("ConfigReader instantiation started")

        # get path from where code was executed
        path = os.path.dirname(os.path.realpath(sys.argv[0]))

        # add /config.json to read path
        configurationFile = path + '/config.json'
        try:
            self.logger.info("Loading configurations from config.json")
            # Open up the config.json file and read configurations
            self.configurations = json.loads(open(configurationFile).read())
        except:
            raise
                
        self.logger.info("ConfigReader instantiated")
 
    # Get full configurations that was read during instantiation of ConfigReader
    def getFullConfigurations(self):    
        return self.configurations