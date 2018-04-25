import os
import sys
import logging
import subprocess

class Logger:

    ' Logger class holds logger configurations'

    def __init__(self):

        print("Logger initialization started")
        
        # Path where log files are stored
        path = os.path.dirname(os.path.realpath(sys.argv[0])) + "/Debugger/Logs/"
        
        # Check if path has write permissions enabled
        print("Check if directory for storing logs is writeable")
        if not os.access(path,os.W_OK):
                # If write permission is not set, try adding with subprocess
                print("{0} not writeable. Try adding access rights with subprocess".format(path))
                try:
                        subprocess.call(['sudo','chmod','-R','777',path])
                except:
                        print("Failed to grant write permissions")
                        raise
                print("Access rights added successfully...")
        else:
            print("Directory is writeable")

        # Path and file where log files are stored
        LOG_FILE = path + "Debug.log"

        # Logger basic configurations
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(name)s %(message)s',datefmt='%d-%m-%y %H:%M:%S',filemode='a')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s',datefmt='%d-%m-%y %H:%M:%S')
        logger = logging.getLogger()
        handler = logging.handlers.RotatingFileHandler(LOG_FILE,maxBytes=50000,backupCount=5)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        print("Logger initialized")
        