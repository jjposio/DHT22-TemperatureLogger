import logging

class TemperatureConverter():

    ' Used to do temperature convesions between celsius degrees to fahrenheits'

    def __init__(self):
	self.logger = logging.getLogger(__name__)
	self.logger.info("TemperatureConverter instantiated")
    
    ' Function for converting celsius degrees to fahrenheits'
    def celsiusToFahrenheits(self, temperatureInCelsius):
        self.logger.info("Converting temperature to fahrenheits")
        return float(temperatureInCelsius) * (9.0/5.0)+32

    ' Function for converting fahrenheits to celsius degrees'
    def FahrenheitToCelsius(self, temperatureInFahrenheits):
        self.logger.info("Converting temperature to celsius")
        return (float(temperatureInFahrenheits) - 32) / (9.0/5.0)