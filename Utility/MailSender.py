from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from datetime import datetime

from TimeFormatHelper import TimeFormat

import smtplib
import logging

class MailSender():
	' Sends emails. Either warning or weekly averages in order to see that pi is alive. Currently supports only gmail '

	def __init__(self,configurations,dbController):
		self.logger = logging.getLogger(__name__)
		self.logger.info("MailSender instantiation started")

		# Passed in dbController to variable
		self.dbController = dbController

		# Configurations to variables for easier use
		self.username = configurations.get('mailConfig')[0]['username']
		self.password = configurations.get('mailConfig')[0]['password']
		self.sender = configurations.get('mailConfig')[0]['senderaddress']
		self.receiver = configurations.get('mailConfig')[0]['receiveraddress']
		self.warningSubject = configurations.get('mailConfig')[0]['subjectwarning']
		self.messageSubject = configurations.get('mailConfig')[0]['subjectmessage']
		self.currentTimeAsString = configurations.get("currentTimeAsString")
		self.currentTime = configurations.get("currentTime")
		self.mailSendingTimeout = configurations.get("mailSendingTimeout")
		
		# Instantiate TimeFormatHelper
		self.timeFormatHelper = TimeFormat()

		self.logger.info("MailSender instantiation finished")


	' Function for sending informational mail e.g. weekly averages. Pass in trigger to indicate what was trigger event e.g. Averages when weekly averages are being sent'
	def sendInformationalEmail(self, msgContent,trigger):
		self.logger.info("sendInformationalEmail called for: %s",trigger)

		# Message to be sended with subject field
		messageOut = 'Subject: %s\n\n%s' % (self.messageSubject ,msgContent)
		try:
			# Send mail
			self._sendMail(messageOut)
		except:
			self.logger.error('Failed to send mail\n',exc_info=True)
			raise

		try:
			# Get time when mail was sent out
			timeSent = self._getDateTimeString()
			# Persist mail sending time to mailsendlog. Use trigger to indicate event - it is set to triggedsensor
			self.dbController.setLastMailSentTime(timeSent,trigger)
		except:
			self.logger.error('Failed to set mail sent time to database\n',exc_info=True)
			raise
	
	' Function for sending warning email '
	def sendWarningEmail(self, msgContent):
		self.logger.info("sendWarningEmail called")
		
		# Message to be sended with subject field
		messageOut = 'Subject: %s\n\n%s' % (self.warningSubject ,msgContent)
		
		try:
			# Send mail
			self._sendMail(messageOut)
		except:
			self.logger.error('Failed to send mail\n',exc_info=True)
			raise

	' Function for sending SENSOR warning email '
	def sendSensorWarningEmail(self, msgContent,sensor,sensorData):
		self.logger.info("sendSensorWarningEmail called")

		# Message to be sended with subject field
		messageOut = 'Subject: %s\n\n%s' % (self.warningSubject ,msgContent)

		try:
			# Send mail
			self._sendMail(messageOut)
		except:
			self.logger.error('Failed to send mail\n',exc_info=True)
			raise

		# Persist mailsending time to database
		try:
			# Get time when mail was sent out
			sendTime = self._getDateTimeString()
			
			# Call setLastSensorMailSentTime function and provide needed data
			self.dbController.setLastSensorMailSentTime(sensor,sendTime,sensorData['temperature'],sensorData['humidity'])
		except:
			self.logger.error('Failed to set mail sent time to database\n',exc_info=True)
			raise
		
	' Private function for sending emails '
	def _sendMail(self, message):
		self.logger.info("_sendMail called. Sending mail...")

		# The actual mail sending
		server = smtplib.SMTP('smtp.gmail.com',587)
		server.starttls()
		server.login(self.username,self.password)
		server.sendmail(self.sender,self.receiver, message)
		server.quit()

		self.logger.info("Mail sent")

		return True

	' Function for checking if mail sending is on timeout. Means that enough time has not passed sice last mail was sent. Check json.config mailSendingTimeoutInFullHours '
	def checkMailTimeout(self, lastMailSentTime):

		self.logger.info("checkMailTimeout called.")

		# check that has the set time passed from the time that last warning was sended.
		# this check is done so you don't get warning everytime that sensor is trigged. E.g. sensor is checked every 5 minutes, temperature is lower than trigger -> you get warning every 5 minutes and mail is flooded.
		if float(self.mailSendingTimeout) != 0.0:
			try:
				# Calculate how many seconds have passed since last mail was sended
				delta = (self.currentTime - lastMailSentTime[0]).total_seconds()
				self.logger.info('Time delta in seconds between current time and time when last mail was sended: %s',delta)

				# Divide delta with seconds to get passed time in full hours
				passedTime = delta // 3600
				self.logger.info('Hours passed since current time and time when last mail was sended: %s',passedTime)
			
				self.logger.info('Comparing passed time with set timeout: %s h',float(self.mailSendingTimeout))
				# Compare passed time for timeout value to see if enough full hours have passed
				if passedTime >= float(self.mailSendingTimeout):
					self.logger.info("Timeout passed, send mail.")
					return True
				else:
					self.logger.info("Still on timeout, mail sending not allowed.")
					return False
			except:
				raise
		else:
			self.logger.warning("Timeout set to 0, mail is sent every time.")
			return True

	' Private function used for getting date time in required form '
	def _getDateTimeString(self):
		try:
			return self.timeFormatHelper.getDateTimeStringFromDateTimeObject(datetime.now(),"%Y-%m-%d %H:%M:%S")
		except:
			self.logger.error('Failed to convert mail sending time DateTime Object to string\n',exc_info=True)
			raise