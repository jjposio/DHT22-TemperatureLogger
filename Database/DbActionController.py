import datetime
import logging

from datetime import timedelta
from DbActions import DbActions

class DbController():

	def __init__(self,configurations):

		self.logger = logging.getLogger(__name__)
		self.logger.info("DbController instantiation started")

		self.currentTimeAsString = configurations.get("currentTimeAsString")

		# Instantiate DbActions that handles CRUD operations
		self.dbActions = DbActions(configurations)

		self.logger.info("DbController instantiated")

	' Function for checking log that when last warning mail was sended for provided sensor '
	def getLastSensorMailSentTime(self,sensor):
		self.logger.info("getLastSensorMailSentTime")

		# Sql query to execute
		sqlQuery = "SELECT * FROM mailsendlog WHERE triggedsensor='%s' AND mailsendtime IN (SELECT max(mailsendtime)FROM mailsendlog WHERE triggedsensor='%s')" % (sensor,sensor)

		# Execute and return data
		data = self.dbActions.sqlSelect(sqlQuery)
		return data
	
	' Function for setting time when mail warning was sent for sensor '
	def setLastSensorMailSentTime(self,sensor,sendingTime,humidity,temperature):
		self.logger.info("setLastSensorMailSentTime")
		
		# Check if humidity was provided for the sensor, if not set it to zero
		if not humidity:
			self.logger.info("Humidity is Empty, set it to default 0.0")
			humidity = "0.0"

		# Check if current time was provided for the sensor, if not set it
		if not sendingTime:
			self.logger.info("sendingTime is empty, set it to current time %s",sendingTime)
			sendingTime = self.currentTimeAsString

		# SQL insert to execute
		sqlQuery = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (sendingTime,sensor,humidity,temperature)

		# Execute and return
		self.dbActions.sqlInsert(sqlQuery)
		return

	' Function for reading last time when mail was sended to spesific sensor '
	def getLastMailSentTime(self,action):
		self.logger.info("getLastMailSentTime")
		
		# Sql query to be executed
		sqlQuery = "SELECT MAX(mailsendtime) FROM mailsendlog WHERE triggedsensor ='%s'" % (action)

		# Execute and return data
		data = self.dbActions.sqlSelect(sqlQuery)
		return data

	' Function for setting time when last general mail was sended. Action is used to indicate what kind of action it was e.g. for averages sending it is Averages'
	def setLastMailSentTime(self,timestamp,action):
		self.logger.info("Set mail sent time to log")

		# Sql query to be executed
		sqlQuery = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (timestamp,action,"","")

		# Execute and return
		self.dbActions.sqlInsert(sqlQuery)
		return
		
	' Function for reading last persisted measurements sensor has provided' 
	def getLastSensorMeasurements(self,sensor):
		self.logger.info('Start reading last sensor measurements')

		# Sql query to be executed
		sqlQuery = "SELECT * FROM temperaturedata WHERE sensor='%s' and dateandtime IN (SELECT max(dateandtime) FROM temperaturedata WHERE sensor='%s')" % (sensor,sensor)

		# Execute and return data
		sensorData = self.dbActions.sqlSelect(sqlQuery)
		return sensorData
	
	' Function for fetching average of weekly temperatures persisted for the sensor'
	def getWeeklyAverageTemp(self,sensor):
			
		self.logger.info("Starting to read sensor weekly average temperatures")
		weekAverageTemp = ""	

		# Get delta between today and last week
		delta = (datetime.date.today() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")

		try:
			# Query to be executed
			sqlQuery = "SELECT AVG(temperature) FROM temperaturedata WHERE dateandtime BETWEEN '%s' AND '%s' AND sensor='%s'" % (delta,self.currentTimeAsString,sensor)

			# Execute
			data = self.dbActions.sqlSelect(sqlQuery)

			# Check if some reasonable data was returned and calculate average
			if data[0] is not None:
				self.logger.info("Calculating average temperature from returned data")
				weekAverageTemp = "%.2f" % data
			else:
				self.logger.warning("No temperature data found from database")
		except:
			raise
		
		# Return sensors weekly average
		return weekAverageTemp

	' Function for reading weekly average humidity persisted for the sensor'
	def getWeeklyAverageHumidity(self,sensor):
			
		self.logger.info("Starting to read sensor weekly average humidity")
		weekAverageHumidity = ""	
		
		delta = (datetime.date.today() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")

		try:
			# Query to be executed
			sqlQuery = "SELECT AVG(humidity) FROM temperaturedata WHERE dateandtime BETWEEN '%s' AND '%s' AND sensor='%s'" % (delta,self.currentTimeAsString,sensor)

			# Execute and calculate average
			data = self.dbActions.sqlSelect(sqlQuery)
			weekAverageHumidity = "%.2f" % data
		except:
			raise

		# Return sensors weekly average
		return weekAverageHumidity

	' Function for persisiting temperature and humidity for the sensor' 
	def setSensorTemperatureAndHumidityToDb(self,sensor,sensorData):
		
		self.logger.info("Starting to persist sensor readings to database")

		# Temperature and humidity to variables for better handling and undertanding
		temperature = sensorData['temperature']
		humidity = sensorData['humidity']
	
		try:
			# Query to be executed
			sqlQuery = "INSERT INTO temperaturedata SET dateandtime='%s', sensor='%s', temperature='%s', humidity='%s'" % (self.currentTimeAsString,sensor,temperature,humidity)
			
			# Execute
			self.dbActions.sqlInsert(sqlQuery)
	   	except:
			raise

	' Function for backup dump creation '
	def createSqlBackupDump(self):
		try:
			# Call dbactions sqlBackup function
			self.dbActions.sqlBackup()
		except:
			raise
