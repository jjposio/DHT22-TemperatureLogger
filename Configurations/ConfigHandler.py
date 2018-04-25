import logging

from Configurations.ConfigReader import ConfigReader
from Configurations.ConfigAdapter import ConfigAdapter

class ConfigHandler():

    ' Class for handling configurations set in config.json '

    def __init__(self):
        self.logger = logging.getLogger(__name__)  
        self.logger.info("ConfigHandler instantiation started")

        # Instantiate config reader for reading config.json
        try:
            self.logger.info('Instantiate ConfigReader')
            self.configReader = ConfigReader()
        except Exception as e:
            self.logger.error('Instantiation failed')
            raise

        # Use getFullConfigurations method to fetch configuration set read during configreader instantiation
        try:
            self.logger.info('Read configurations')
            self.fullConfigurations = self.configReader.getFullConfigurations()
            self.logger.info('Configurations read succesfully')
        except Exception as e:
            self.logger.error("Configuration reading failed")
            raise

        # Check that configuration is not empty and instantiate configuration adapter with configuration data
        if self.fullConfigurations is None:
            raise Exception("Read configuration set is empty")
        try:
            self.ConfigAdapter = ConfigAdapter(self.fullConfigurations)
        except Exception as e:
            self.logger.error("Configuration adapter instantiation failed")
            raise

        self.logger.info("ConfigHandler instantiated")
 
    ' Get full configuration dictionary and return it to '
    def getFullConfiguration(self):
        self.logger.info("Get full configuration adaptation")
        try:
            return self.ConfigAdapter.getAdaptedFullConfig()
        except Exception as e:
            self.logger.error("Configuration adaptation failed\n")
            raise

    ' Check if backup dump is enabled in configurations and check if it is time to perform the dump '
    def isBackupDumpConfigEnabled(self):

        # Set exectue flag to false to begin with
        execute = False

        self.logger.info("Get configuration for backup dump")
        dumpConfig = self.ConfigAdapter.getBackupDumpConfig()

        # dumpConfigs to variables for better understandability
        dumpEnabled = dumpConfig["backupDumpConfig"][0]["backupDumpEnabled"]
        backupDay = dumpConfig["backupDumpConfig"][0]["backupDay"]
        backupHour = dumpConfig["backupDumpConfig"][0]["backupHour"]

        self.logger.info("Check if dump is enabled")
        if dumpEnabled.lower() == "y":
            self.logger.info("Yes")
            # Check if it is time to perform dump
            execute = self._isItTimeToperform(backupDay,backupHour,dumpConfig["dayOfTheWeek"],dumpConfig["currentTime"])
        else:
		 	self.logger.info("No")
        return execute
    
    ' Check if weekly averages sending is enabled '
    def isWeeklyAveragesConfigEnabled(self):
        
        # Flag to false
        execute = False

        self.logger.info("Get configuration for sending weekly average temperatures")
        averagesSendingConfig = self.ConfigAdapter.getAveragesSendingConfig()

        # Average configurations to variables for better understandability
        sendingEnabled = averagesSendingConfig["averagesSendingConfig"][0]["weeklyAverageSendingEnabled"]
        sendingDay = averagesSendingConfig["averagesSendingConfig"][0]["weekDayForSendingAverages"]
        sendingHour = averagesSendingConfig["averagesSendingConfig"][0]["hourOfTheDayForSendingAverages"]

        self.logger.info("Check if weekly averages sending is enabled")
        if sendingEnabled.lower() == "y":
            self.logger.info("Yes")
            # Check if it is time to perform averages sending
            execute = self._isItTimeToperform(sendingDay,sendingHour,averagesSendingConfig["dayOfTheWeek"],averagesSendingConfig["currentTime"])      
        else:
            self.logger.info("No")
        return execute

    ' Private function for comparing current date and time for configuration provided date and time '
    def _isItTimeToperform(self,setDay,setHour,currentDate,currentTime):
        self.logger.info("Is it time to perform requested action")

        if (str(setDay) == "0" or str(currentDate) == str(setDay)) and str(currentTime.hour) == str(setHour):
			self.logger.info("Yes")
			return True
        else:
            self.logger.info("No")
            return
