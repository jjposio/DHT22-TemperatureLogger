from Utility.TimeFormatHelper import TimeFormat

import logging

class ConfigAdapter():
    'Adaptation class that can be used to get different adaptations from full configuration read from json.config.'

    def __init__(self,configurations):
        self.logger = logging.getLogger(__name__)
        self.logger.info("ConfigAdapter instantiation started")

        self.timeFormatHelper = TimeFormat()
        self.configuration = configurations

        self.logger.info("ConfigAdapter instantiated")

    def getAdaptedFullConfig(self):
        self.logger.info("Creating dictionary for full configurations")

        adaptation = dict(
            currentTime = self.timeFormatHelper.getDateTime(),
            currentTimeAsString = self.timeFormatHelper.getDateTimeAsString(),
            dayOfTheWeek = self.timeFormatHelper.getNumberOfTheDay(),
            dateAsString = self.timeFormatHelper.getTodayAsString(),
            sqlConfig = self.configuration["mysql"],
            sensorConfig = self.configuration["sensors"],
            mailConfig = self.configuration["mailInfo"],
            backupDumpConfig = self.configuration["sqlBackupDump"],
            averagesSendingConfig = self.configuration["weeklyAverages"],
            useFahrenheitsConfig = self.configuration["useFahrenheits"],
            mailSendingTimeout = self.configuration["mailSendingTimeoutInFullHours"],
            adafruitPathConfig = self.configuration["adafruitPath"])

        self.logger.info("Configuration dictionary created")

        return adaptation

    def getBackupDumpConfig(self):
        self.logger.info("Creating dictionary for backup dump configurations")

        adaptation = dict(
            backupDumpConfig = self.configuration["sqlBackupDump"],
            dayOfTheWeek = self.timeFormatHelper.getNumberOfTheDay(),
            currentTime = self.timeFormatHelper.getDateTime())

        self.logger.info("Configuration dictionary created")
        return adaptation
        
    def getAveragesSendingConfig(self):
        self.logger.info("Creating dictionary for backup dump configurations")
        
        adaptation = dict(
            averagesSendingConfig = self.configuration["weeklyAverages"],
            dayOfTheWeek = self.timeFormatHelper.getNumberOfTheDay(),
            currentTime = self.timeFormatHelper.getDateTime())

        self.logger.info("Configuration dictionary created")
        return adaptation



