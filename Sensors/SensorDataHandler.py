import logging
import sys

from Sensors.SensorReader import SensorReader
from Utility.MeasurementCompare import MeasurementCompare

class SensorDataHandler():
	' Class for handling Sensors and data gathered from sensors. Reads data, persists it to database and performs comparisons to see if temperature or humidity has changed more than set threshold allows'

	def __init__(self, configurations,dbControl,mailSender):
		self.logger = logging.getLogger(__name__)
		self.logger.info("SensorDataHandler instantiation started")

		# Set passed in data to variables for further usage
		self.dbControl = dbControl
		self.mailSender = mailSender
		self.configurations = configurations
		# Instantiate sensor reader
		self.sensorReader = SensorReader(self.configurations,self.dbControl)
		# Instantiate mesurement comparer
		self.compareMeasurements = MeasurementCompare(self.configurations)
		# Create empty list for readings
		self.readingsFromSensors = {}
		self.failedSensors = []

		self.logger.info("SensorDataHandler instantiated")

	def readAndStoreSensorReadings(self):
		# Store sensor temperature and humidity readings with other relevant data
		try:
			self.readingsFromSensors, self.failedSensors = self.sensorReader.getSensorReadings()
			self.logger.info('Successfully read: %s sensors. Failed to read: %s sensor(s)',len(self.readingsFromSensors),len(self.failedSensors))
		except Exception as e:
			self.logger.error("Sensor reading raised exception",exc_info=True)
			raise
		
		# Send warning to indicate that some of the configured sensors are not providing correct information
		try:
			# Check if all sensors failed to get readings. If so, no need to continue.
			if len(self.failedSensors) == len(self.configurations["sensorConfig"]):
				self.logger.error('Failed to get readings from any of the sensors. Execution terminated')
				try:
					self.logger.info('Send warning to indicate that none of the sensors provided data')			
					# Send warning email
					self.mailSender.sendWarningEmail('Failed to get readings from any of the sensors. Please check debug log and configurations from config.json')
					# There is no values to continue with, so it is good to terminate
					self.logger.warning('Warning mail sent, no measurement values to continue with...terminate')
					sys.exit(0)
				except Exception as e:
					self.logger.error('Warning mail sending failed',exc_info=True)
					raise
		except Exception as e:
			self.logger.error("Failed to check if all sensors failed to get readings",exc_info=True)
			raise
		
		try:
			# Check how many sensors failed. If there is more than 0, log and try to send warning mail
			if len(self.failedSensors) != 0:
				self.logger.warning('Failed to get readings from sensor(s): {0}'.format(', '.join(self.failedSensors)))
				msg = 'Failed to get readings from sensor(s): {0}.\nPlease check debug log from RPI for further info and double check your config.json'.format(', '.join(self.failedSensors))
				try:
					self.mailSender.sendWarningEmail(msg)
				except Exception as e:
					self.logger.error('Warning mail sending failed\n',exc_info=True)
					raise
		except Exception as e:
			self.logger.error("Failed to check how many sensors failed to provide readings",exc_info=True)
			raise
		
		# Persist read data to database
		try:
			self._persistSensorData()
		except:
			self.logger.error("Failed to persist read data to database",exc_info=True)
			raise

		# Compare measured value with previous measured value and set threshold. 
		# E.g. if config has threshold set to 5. Last measurement was 20 and now it is 30. Set threshold has been exceeded by 5 (30-20-5)
		# And it is time to send alarm
		try:
			self._measurementCompareAgainstSetThreshold()
		except:
			self.logger.error("Failed to perform comparison between measured data and set threshold",exc_info=True)
			raise

		# Check if measured values are beyond set limits
		try:
			self._compareReadValuesWithSetLimits()
		except:	
			self.logger.error("Failed to compare read value with set limits",exc_info=True)
			raise

		return

	' Private function for persisting sensor data to database'
	def _persistSensorData(self):
		# Check that there is values in readingsFromSensors collections and add into database
		for key, value in self.readingsFromSensors.iteritems():
			self.logger.info("Start persisting data for sensor %s",key)
			try:
				# Call setSensorTemperatureAndHumidityToDb from dbcontrol. Provide sensor name and value
				self.dbControl.setSensorTemperatureAndHumidityToDb(key,value)
			except:
				# Msg to separate variable, so that key can be added as well.
				msg = 'Failed to persist temperature and humidity readings to database. Sensor : %s', key
				self.logger.error(msg,exc_info=True)
				raise
			self.logger.info("Data persisting finished for sensor %s",key)
		self.logger.info("Data persisted")



	' Compare current and last measurement against set threshold. Note that this will ignore time when last one was sent, it will send mail always when set threshold is exceeded'
	def _measurementCompareAgainstSetThreshold(self):

		# Set send warning flag to false by default
		sendWarning = False

		# Start checking
		for key, value in self.readingsFromSensors.iteritems():
			self.logger.info('Starting measurement comparison against set threshold for sensor %s',key)

			# If there is no earlier temperature or humidity measurements available, skip this
			if (value['lastMeasuredTemperature'] != "") or (value['lastMeasuredHumidity'] != ""):
				self.logger.info('Last measured temperature to compare to: %s and Last measured humidity to compare to: %s',value['lastMeasuredTemperature'],value['lastMeasuredHumidity'])
				self.logger.info('Execute measurement compare against set threshold')
				try:
					# Set sensor data to comparer
					self.compareMeasurements.setSensorData(key,value)

					# First check if temperature has changed more than it is allowed in configuration threshold
					sendWarning, messageToSend = self.compareMeasurements.checkTemperatureChange()
					
					# Check also humidity for the same than temperature above. Append possible warnings to messagesToSend
					sendWarning, messageToSend = self.compareMeasurements.checkHumidityChange()
				except Exception as e:
					self.logger.error('Failed to compare sensor temperatures (last and current) against threshold limits:\n',exc_info=True)
					raise

				# Check if send warning flag is true after comparisons
				if sendWarning == True and self.mailSender is not None:
					try:
						self.logger.info('Send Sensor warning mail')			
						# Send sensor warning email
						self.mailSender.sendSensorWarningEmail(messageToSend,key,value)
					except Exception as e:
						self.logger.error('Warning mail sending failed\n',exc_info=True)
						raise
			else:
				self.logger.warning('There was no previous measurements for temperature or humidity. Nothing to compare to')
			self.logger.info('Threshold comparison done for sensor %s',key)


	' Compare measured temperature and humidity with set trigger limits '
	def _compareReadValuesWithSetLimits(self):

		for key, value in self.readingsFromSensors.iteritems():
			self.logger.info('Perform delta check compare against previously measured results for sensor %s',key)
			
			# Set flags to begin with
			betweenLimits = True
			mailSendingtimeOutPassed = False

			try:
				# Set sensor data to comparer
				self.compareMeasurements.setSensorData(key,value)

				# Compare measured temperature with set limits
				betweenLimits, messageToSend = self.compareMeasurements.checkTemperatureLimits()

				# Compare measured humidity with set limits
				betweenLimits, messageToSend = self.compareMeasurements.checkHumidityLimits()
			except Exception as e:
				msg = 'Failed to perform comparison for Sensor: %s',key
				self.logger.error(msg,exc_info=True)
				raise

			# If betweelimit flag was set to False during temperature or humidity check then start sending warning email
			if betweenLimits == False:
				# Check if lastMailSent is empty
				if not value['lastMailSent']:
					self.logger.warning('No value in lastMailSent. Send mail.')
					# If it is empty, no need to compare time to anything, just send mail
					mailSendingtimeOutPassed = True
				else:
					# Compare time delta between last mail sent and current time. If delta exceeds mailSendingTimeoutInFullHours value, return TRUE, otherwise FALSE
					self.logger.info('Delta check current time and last mail sent time.')
					try:
						mailSendingtimeOutPassed = self.mailSender.checkMailTimeout(value['lastMailSent'])
					except Exception as e:
						self.logger.error('Delta check failed\n',exc_info=True)
						raise

				# If time for last mail sending was found and it passed delta check and mailsender is available, send mail
				if mailSendingtimeOutPassed and self.mailSender is not None:
					try:
						self.logger.info('Send warning mail')
						self.mailSender.sendSensorWarningEmail(messageToSend,key,value)
					except Exception as e:
						self.logger.error('Warning mail sending failed\n',exc_info=True)
						raise
				self.logger.info('Delta check compare done for sensor %s',key)

