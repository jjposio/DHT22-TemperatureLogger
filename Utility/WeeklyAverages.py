from Database.DbActionController import DbController

import logging

class WeeklyAverages():
    
    def __init__(self,configurations,dbControl,mailSender):
        self.logger = logging.getLogger(__name__)
        self.logger.info("WeeklyAverages instantiation started")

        self.sensorConfig = configurations.get("sensorConfig")
        self.dbController = dbControl
        self.mailSender = mailSender

        self.logger.info("WeeklyAverages instantiation finished")

    ' Function for performing weekly averages mail sending '
    def performWeeklyAverageMailSending(self):
        self.logger.info("Get weekly averages and check when last mail was sent")
        
        # Set mailSendingTimeoutPassed to false at first
        mailSendingtimeOutPassed = False

        # Get time when last mail was sended regarding this matter
        timeForLastAverageMail = self.dbController.getLastMailSentTime("Averages")
        
        self.logger.info('Delta check current time and last mail sent time. Last mail about average temperatures was sent out on: %s',timeForLastAverageMail)

        # Check if there is no time entry for last mail sending
        if timeForLastAverageMail[0] is None:
			self.logger.warning('No value in lastMailSent. Send mail.')
			mailSendingtimeOutPassed = True
        else:
            # Compare time when last mail was sent with mail sending timeout set in config
            try:
                self.logger.info('Time when last mail was sent: %s',timeForLastAverageMail)
                mailSendingtimeOutPassed = self.mailSender.checkMailTimeout(timeForLastAverageMail)
            except Exception as e:
                raise e

        # Check if mailsending timeout has passed, if yes start sending mail
        if mailSendingtimeOutPassed:
            mailToBeSended = "Weekly averages from sensors:\n"
            try:
                # Get weekly average temperature for each sensor and append results to the message going out
                for sensor in self.sensorConfig:
                    sensor = sensor[0]['name']
                    # Get weekly average temperature for the sensor and append it to mail that will be sent
                    sensorWeeklyAverageTemp = self.dbController.getWeeklyAverageTemp(sensor)
                    # If database contained any value for the sensor
                    if sensorWeeklyAverageTemp != "":
                        mailToBeSended = mailToBeSended + sensor + " : " + sensorWeeklyAverageTemp + "\n"
                    # If database didn't contain any value for the sensor
                    else:
                        mailToBeSended = mailToBeSended + sensor + " : N\A\n"
                
                # Send mail and set mailsentlog with 'Averages' as sensor name
                self.mailSender.sendInformationalEmail(mailToBeSended,"Averages")
                self.logger.info("Weekly averages email sent")
            except Exception as e:
                raise
        else:
            return
    