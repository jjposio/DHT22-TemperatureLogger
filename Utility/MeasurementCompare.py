import logging

# Utility.TemperatureConverter import TemperatureConverter

class MeasurementCompare():

	def __init__(self,configurations):
	
		self.logger = logging.getLogger(__name__)
		self.logger.info("MeasurementCompare instantiation started")

		self.fahrenheitConfig = configurations.get("useFahrenheitsConfig")
		self.sendWarning = False
		self.warningMsg = ""
		self.limitCheckWarningMsg = ""

		self.sensor = ""
		self.measuredTemperature = ""
		self.temperatureLowLimit = ""
		self.temperatureHighLimit = ""
		self.previousTemperature = ""
		self.measuredHumidity = ""
		self.humidityLowLimit = ""
		self.humidityHighLimit = ""
		self.temperatureThreshold = ""
		self.humidityThreshold = ""
		self.lastMeasuredHumidity = ""
		self.betweenLimits = True

		self.logger.info("Instantiation done")

	def setSensorData(self,sensor,sensorData):
		self.logger.info("Set sensor data to begin measurements")

		self.sensor = sensor
		self.measuredTemperature = sensorData.get('temperature')
		self.temperatureLowLimit = sensorData.get('temperatureLowLimit')
		self.temperatureHighLimit = sensorData.get('temperatureHighLimit')
		self.temperatureThreshold = sensorData.get('temperatureThreshold')
		self.previousTemperature = sensorData.get('lastMeasuredTemperature')
		self.measuredHumidity = sensorData.get('humidity')
		self.humidityLowLimit = sensorData.get('humidityLowLimit')
		self.humidityHighLimit = sensorData.get('humidityhighLimit')
		self.humidityThreshold = sensorData.get('humidityThreshold')
		self.previousHumidity = sensorData.get('lastMeasuredHumidity')
		self.warningMsg = "" 
		self.limitCheckWarningMsg = ""
		self.sendWarning = False
		self.betweenLimits = True
		
		self.logger.info("Data set")

	' Function for comparing measured temperature against limits set for the sensor in config.json. Data need to be set with setSensorData before calling this function '
	def checkTemperatureLimits(self):
		
		self.logger.info("Comparing measured temperature against set limit")

		# check temperature measurements against limits
		# If measured temperature is less than low limit -> set betweenlimits to False and warning gets sent
		if float(self.measuredTemperature) < float(self.temperatureLowLimit):
			self.limitCheckWarningMsg = "WARNING: Temperature low on sensor: {0}\nTemperature: {1}\nTemperature low limit: {2}\nhumidity: {3}\n".format(self.sensor,self.measuredTemperature,self.temperatureLowLimit,self.measuredHumidity)
			# This is True to begin with, changed to false if warning need to be sent
			self.betweenLimits = False
			self.logger.warning("Measured temperature is lower than set limit")

		# If measured temperature is greater than high limit -> set betweenlimits to False and warning gets sent
		elif float(self.measuredTemperature) > float(self.temperatureHighLimit):
			self.limitCheckWarningMsg = "WARNING: Temperature high on sensor: {0}\nTemperature: {1}\nTemperature high limit: {2}\nhumidity: {3}\n".format(self.sensor,self.measuredTemperature,self.temperatureHighLimit,self.measuredHumidity)
			# This is True to begin with, changed to false if warning need to be sent
			self.betweenLimits = False
			self.logger.warning("Measured temperature is higher than set limit")

		self.logger.info("Comparison done")
		return self.betweenLimits, self.limitCheckWarningMsg

	' Function for comparing measured humidity against limits set for the sensor in config.json. Data need to be set with setSensorData before calling this function '
	def checkHumidityLimits(self):

		self.logger.info("Comparing measured humidity against set limit")

		# check humidity measurements against limits
		# If measured humidity is less than low limit -> set betweenlimits to False and warning gets sent
		if float(self.measuredHumidity) < float(self.humidityLowLimit):
			self.limitCheckWarningMsg = self.limitCheckWarningMsg + "WARNING: Humidity low on sensor: {0}\nTemperature: {1}\nHumidity low limit: {2}\nHumidity: {3}\n".format(self.sensor,self.measuredTemperature,self.humidityLowLimit,self.measuredHumidity)
			self.betweenLimits = False
			self.logger.warning("Measured humidity is lower than set limit")

		# If measured humidity is greater than high limit -> set betweenlimits to False and warning gets sent
		elif float(self.measuredHumidity) > float(self.humidityHighLimit):
			self.limitCheckWarningMsg = self.limitCheckWarningMsg + "WARNING: Humidity high on sensor: {0}\nTemperature: {1}\nHumidity high limit: {2}\nHumidity: {3}\n".format(self.sensor,self.measuredTemperature,self.humidityHighLimit,self.measuredHumidity)
			self.betweenLimits = False
			self.logger.warning("Measured humidity is higher than set limit")

		self.logger.info("Comparison done")
		return self.betweenLimits, self.limitCheckWarningMsg

	' Function for checking temperature change. Compares current and last measurement agains set threshold  '
	def checkTemperatureChange(self):
		self.logger.info("Comparing temperature change against set threshold")

		# Set measurement unit as celsius degrees by default
		measurementUnit = "celsius degrees"

		# Check if fahrenheits is used
		if self.fahrenheitConfig.lower() == "y":
			self.logger.info("Fahrenheits enabled in configurations")
			# Set measurement unit as fahnrenheits
			measurementUnit = "fahrenheits"

		self.logger.info("Checking if previous temperature is available...")
		# check if previously measured humidity is castable to float, if not then measurement comparisons would fail
		if self._isFloat(self.previousTemperature):
			self.logger.info("Previous temperature is available, execute comparison")
			self.logger.info("Measured temperature = %s, previously measured temperature %s, temperature treshold %s",self.measuredTemperature,float(self.previousTemperature),self.temperatureThreshold)

			# Check if measured temperature is greater than previously measured temperature + allowed threshold
			if self.measuredTemperature > float(self.previousTemperature) + self.temperatureThreshold:
				# Set sendWarning flag to true to indicate that warning need to be sended
				self.sendWarning = True
				# Compose warning message to be sended out
				self.warningMsg = "WARNING: Temperature increased more than {0} {1} on sensor {2}\nMeasured temperature: {3} {1}\nPrevious temperature: {4} {1}".format(self.temperatureThreshold,measurementUnit,self.sensor,self.measuredTemperature,self.previousTemperature)
				self.logger.warning("Temperature has increased more than set threshold")

			# Check if measured temperature is less than previously measured temperature - allowed threshold
			if self.measuredTemperature < float(self.previousTemperature) - self.temperatureThreshold:
				# Set sendWarning flag to true to indicate that warning need to be sended
				self.sendWarning = True
				# Compose warning message to be sended out
				self.warningMsg = "WARNING: Temperature decreased more than {0} {1} on sensor {2}\nMeasured temperature: {3} {1}\nPrevious temperature: {4} {1}".format(self.temperatureThreshold,measurementUnit,self.sensor,self.measuredTemperature,self.previousTemperature)
				self.logger.warning("Temperature has decreased more than set threshold")
		else:
			self.logger.warning("...Previous temperature not available, nothing to compare to")
					
		self.logger.info("Comparison done")
		return self.sendWarning, self.warningMsg

	'  Function for checking humidity change. Compares current and last measurement agains set threshold '
	def checkHumidityChange(self):
		
		self.logger.info("Comparing humidity change against set threshold")

		self.logger.info("Checking if previous humidity value is available...")
		# check if previously measured humidity is castable to float, if not then measurement comparisons would fail
		if self._isFloat(self.previousHumidity):
			self.logger.info("Previous humidity is available, execute comparison")
			self.logger.info("Measured humidity = %s, previously measured humidity %s, humidity treshold %s",self.measuredHumidity,float(self.previousHumidity),self.humidityThreshold)

			# Check if measured humidity is greater than previously measured temperature + allowed threshold
			if self.measuredHumidity > float(self.previousHumidity) + self.humidityThreshold:
				# Set sendWarning flag to true to indicate that warning need to be sended
				self.sendWarning = True
				# Compose warning message to be sended out
				# Note that this will add new warningmessage after first in case that also temperature comparisons caused warning to be sent
				self.warningMsg = self.warningMsg + "WARNING: Humidity increased {0} percents on sensor {1}\nMeasured humidity: {2} \nPrevious humidity: {3}".format(self.humidityThreshold,self.sensor,self.measuredHumidity,self.previousHumidity)
				self.logger.warning("Humidity has increased more than set threshold")

			# Check if measured humidity is less than previously measured temperature - allowed threshold
			if self.measuredHumidity < float(self.previousHumidity) - self.humidityThreshold:
				# Set sendWarning flag to true to indicate that warning need to be sended
				self.sendWarning = True
				# Compose warning message to be sended out. 
				# Note that this will add new warningmessage after first in case that also temperature comparisons caused warning to be sent
				self.warningMsg = self.warningMsg + "WARNING: Humidity decreased {0} percents on sensor {1}\nMeasured humidity: {2} \nPrevious humidity: {3}".format(self.humidityThreshold,self.sensor,self.measuredHumidity,self.previousHumidity)
				self.logger.warning("Humidity has decreased more than set threshold")
		else:
			self.logger.warning("...Previous humidity value not available, nothing to compare to")

		self.logger.info("Comparison done")
		return self.sendWarning, self.warningMsg

	' Private function to check if value is float or not' 
	def _isFloat(self,valueToCheck):
		try:
			float(valueToCheck)
			return True
		except ValueError:
			return False
