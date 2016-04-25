# Copyright (c) 2015
# Author: Janne Posio

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

# This script is intended to use with Adafruit DHT22 temperature and humidity sensors
# and with sensor libraries that Adafruit provides for them. This script alone, without
# sensor/s to provide data for it doesn't really do anyting useful.
# For guidance how to create your own temperature logger that makes use of this script,
# Adafruit DHT22 sensors and raspberry pi, visit : 
# http://www.instructables.com/id/Raspberry-PI-and-DHT22-temperature-and-humidity-lo/

#!/usr/bin/python2
#coding=utf-8

import os
import re
import sys
import datetime
from datetime import timedelta
import json
import subprocess
import MySQLdb
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# function for reading DHT22 sensors
def sensorReadings(gpio, sensor):
	
	configurations = getConfigurations()	
	adafruit = configurations["adafruitpath"]

	sensorReadings = subprocess.check_output(['sudo',adafruit,sensor,gpio])

	try:
		# try to read neagtive numbers
		temperature = re.findall(r"Temp=(-\d+.\d+)", sensorReadings)[0]
	except: 
		# if negative numbers caused exception, they are supposed to be positive
		try:
			temperature = re.findall(r"Temp=(\d+.\d+)", sensorReadings)[0]
		except:
			pass
	humidity = re.findall(r"Humidity=(\d+.\d+)", sensorReadings)[0]
	intTemp = float(temperature)
	intHumidity = float(humidity)

	return intTemp, intHumidity

# function for getting weekly average temperatures.
def getWeeklyAverageTemp(sensor):

	weekAverageTemp = ""	
	
	date = 	datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	delta = (datetime.date.today() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")

    	try:
        	sqlCommand = "SELECT AVG(temperature) FROM temperaturedata WHERE dateandtime BETWEEN '%s' AND '%s' AND sensor='%s'" % (delta,date,sensor)
		data = databaseHelper(sqlCommand,"Select")
		weekAverageTemp = "%.2f" % data
   	except:
		pass
	
	return weekAverageTemp

# function that sends emails, either warning or weekly averages in order to see that pi is alive
def emailWarning(msg, msgType):
	
	configurations = getConfigurations()
	
	fromaddr = configurations["mailinfo"][0]["senderaddress"]
	toaddrs = configurations["mailinfo"][0]["receiveraddress"]
	username = configurations["mailinfo"][0]["username"]
	password = configurations["mailinfo"][0]["password"]
	subj = configurations["mailinfo"][0]["subjectwarning"]
		
	if msgType is 'Info':
		subj = configurations["mailinfo"][0]["subjectmessage"]
	
	# Message to be sended with subject field
	message = 'Subject: %s\n\n%s' % (subj,msg)

	# The actual mail sending
	server = smtplib.SMTP('smtp.gmail.com',587)
	server.starttls()
	server.login(username,password)
	server.sendmail(fromaddr, toaddrs, message)
	server.quit()

	return
	
# helper function for database actions. Handles select, insert and sqldumpings. Update te be added later
def databaseHelper(sqlCommand,sqloperation):

	configurations = getConfigurations()

	host = configurations["mysql"][0]["host"]
	user = configurations["mysql"][0]["user"]
	password = configurations["mysql"][0]["password"]
	database = configurations["mysql"][0]["database"]
	backuppath = configurations["sqlbackuppath"]
	
	data = ""
	
	db = MySQLdb.connect(host,user,password,database)
        cursor=db.cursor()

	if sqloperation == "Select":
		try:
			cursor.execute(sqlCommand)
			data = cursor.fetchone()
  		except:
			db.rollback()
	elif sqloperation == "Insert":
        	try:
			cursor.execute(sqlCommand)
                	db.commit()
        	except:
                	db.rollback()
                	emailWarning("Database insert failed", "")
			sys.exit(0)
    
	elif sqloperation == "Backup":	
		# Getting current datetime to create seprate backup folder like "12012013-071334".
		date = datetime.date.today().strftime("%Y-%m-%d")
		backupbathoftheday = backuppath + date

		# Checking if backup folder already exists or not. If not exists will create it.
		if not os.path.exists(backupbathoftheday):
			os.makedirs(backupbathoftheday)

		# Dump database
		db = database
		dumpcmd = "mysqldump -u " + user + " -p" + password + " " + db + " > " + backupbathoftheday + "/" + db + ".sql"
		os.system(dumpcmd)

	return data
	
# function for checking log that when last warning was sended, also inserts new entry to log if warning is sent
def checkWarningLog(sensor, sensortemp):

	currentTime = datetime.datetime.now()
	currentTimeAsString = datetime.datetime.strftime(currentTime,"%Y-%m-%d %H:%M:%S")
	lastLoggedTime = ""
	lastSensor = ""
	triggedLimit = ""
	lastTemperature = ""
	warning = ""
	okToUpdate = False
	# sql command for selecting last send time for sensor that trigged the warning

	sqlCommand = "select * from mailsendlog where triggedsensor='%s' and mailsendtime IN (SELECT max(mailsendtime)FROM mailsendlog where triggedsensor='%s')" % (sensor,sensor)
	data = databaseHelper(sqlCommand,"Select")

	# If there weren't any entries in database, then it is assumed that this is fresh database and first entry is needed
	if data == None:
	       	sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTimeAsString,sensor,"0.0",sensortemp)
		databaseHelper(sqlCommand,"Insert")
		lastLoggedTime = currentTimeAsString
		lastTemperature = sensortemp
		okToUpdate = True
	else:
		lastLoggedTime = data[0]
		lastSensor = data[1]
		triggedLimit = data[2]
		lastTemperature = data[3]

	# check that has couple of hours passed from the time that last warning was sended.
	# this check is done so you don't get warning everytime that sensor is trigged. E.g. sensor is checked every 5 minutes, temperature is lower than trigger -> you get warning every 5 minutes and mail is flooded.
	try:
		delta = currentTime - lastLoggedTime
		passedTime = (float(delta.seconds) // 3600)
	
		if passedTime > 2:
			okToUpdate = True
		else:
			pass
	except:
		pass

	# another check. If enough time were not passed, but if temperature has for some reason increased or dropped 5 degrees since last alarm, something might be wrong and warning mail is needed
	if okToUpdate == False:
		if "conchck" not in sensor:
			if sensortemp > float(lastTemperature) + 5.0:
				okToUpdate = True
				warning = "NOTE: Temperature increased 5 degrees"
			if sensortemp < float(lastTemperature) - 5.0:
				okToUpdate = True
				warning = "NOTE: Temperature decreased 5 degrees"

	return okToUpdate, warning

	# Function for checking limits. If temperature is lower or greater than limit -> do something
def checkLimits(sensor,sensorTemperature,sensorHumidity,sensorhighlimit,sensorlowlimit):
	
	check = True
	warningmsg = ""
	
	if float(sensorTemperature) < float(sensorlowlimit):
		warningmsg = "Temperature low on sensor: {0}\nReading: {1}\nLimit: {2}\nHumidity: {3}".format(sensor,sensorTemperature,sensorlowlimit,sensorHumidity)
		check = False
	elif float(sensorTemperature) > float(sensorhighlimit):
		warningmsg = "Temperature too high on sensor: {0}\nReading: {1}\nLimit: {2}\nHumidity: {3}".format(sensor,sensorTemperature,sensorhighlimit,sensorHumidity)
		check = False
	return check,warningmsg
	
	# helper function for getting configurations from config json file
def getConfigurations():

	path = os.path.dirname(os.path.realpath(sys.argv[0]))

	#get configs
	configurationFile = path + '/config.json'
	configurations = json.loads(open(configurationFile).read())

	return configurations

def main():

	currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	configurations = getConfigurations()

	# how many sensors there is 1 or 2
	sensorsToRead = configurations["sensoramount"]
		
	# Sensor names to add to database, e.g. carage, outside
	sensor1 = configurations["sensors"][0]["sensor1"]
	sensor2 = configurations["sensors"][0]["sensor2"]

	# limits for triggering alarms
	sensor1lowlimit = configurations["triggerlimits"][0]["sensor1lowlimit"]
	sensor2lowlimit = configurations["triggerlimits"][0]["sensor2lowlimit"]
	sensor1highlimit = configurations["triggerlimits"][0]["sensor1highlimit"]
	sensor2highlimit = configurations["triggerlimits"][0]["sensor2highlimit"]

	# Sensor gpios
	gpioForSensor1 = configurations["sensorgpios"][0]["gpiosensor1"]
	gpioForSensor2 = configurations["sensorgpios"][0]["gpiosensor2"]
	
	# Backup enabled
	backupEnabled = configurations["sqlBackupDump"][0]["backupDumpEnabled"]
	backupHour = configurations["sqlBackupDump"][0]["backupHour"]
	
	# Connection check enabled
	connectionCheckEnabled = configurations["connectionCheck"][0]["connectionCheckEnabled"]
	connectionCheckDay = configurations["connectionCheck"][0]["connectionCheckDay"]
	connectionCheckHour = configurations["connectionCheck"][0]["connectionCheckHour"]

	# type of the sensor used, e.g. DHT22 = 22
	sensorType = configurations["sensortype"]

	# Default value for message type, not configurable
	msgType = "Warning"

	d = datetime.date.weekday(datetime.datetime.now())
	h = datetime.datetime.now()

	# check if it is 5 o clock. If yes, take sql dump as backup
	if backupEnabled == "Y" or backupEnabled == "y":
		if h.hour == int(backupHour):
			databaseHelper("","Backup")

	# check if it is sunday, if yes send connection check on 23.00
	if connectionCheckEnabled == "Y" or connectionCheckEnabled == "y":
		okToUpdate = False
		if str(d) == str(connectionCheckDay) and str(h.hour) == str(connectionCheckHour):
			try:
				sensor1weeklyAverage = getWeeklyAverageTemp(sensor1)
				if sensor1weeklyAverage != None and sensor1weeklyAverage != '':
					checkSensor = sensor1+" conchck"
					okToUpdate, tempWarning = checkWarningLog(checkSensor,sensor1weeklyAverage)
					if okToUpdate == True:
						msgType = "Info"
						Message = "Connection check. Weekly average from {0} is {1}".format(sensor1,sensor1weeklyAverage)
						emailWarning(Message, msgType)
						sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTime,checkSensor,sensor1lowlimit,sensor1weeklyAverage)
						databaseHelper(sqlCommand,"Insert")
			except:
				emailWarning("Couldn't get average temperature to sensor: {0} from current week".format(sensor1),msgType)
				pass				

			if sensorsToRead != "1":
				okToUpdate = False
				try:
					sensor2weeklyAverage = getWeeklyAverageTemp(sensor2)
					if sensor2weeklyAverage != None and sensor2weeklyAverage != '':
						checkSensor = sensor2+" conchck"
						okToUpdate, tempWarning = checkWarningLog(checkSensor,sensor2weeklyAverage)
						if okToUpdate == True:
							msgType = "Info"	
							Message = "Connection check. Weekly average from {0} is {1}".format(sensor2,sensor2weeklyAverage)
							emailWarning(Message, msgType)
							sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTime,checkSensor,sensor2lowlimit,sensor2weeklyAverage)
							databaseHelper(sqlCommand,"Insert")
				except:
					emailWarning( "Couldn't get average temperature to sensor: {0} from current week".format(sensor2),msgType)
					pass			

	# default message type to send as email. DO NOT CHANGE
	msgType = "Warning"	

	sensor1error = 0
	okToUpdate = False
	# Sensor 1 readings and limit check
	try:
		sensor1temperature, sensor1humidity = sensorReadings(gpioForSensor1, sensorType)
		limitsOk,warningMessage = checkLimits(sensor1,sensor1temperature,sensor1humidity,sensor1highlimit,sensor1lowlimit)
	except:
		emailWarning("Failed to read {0} sensor".format(sensor1),msgType)
		sensor1error = 1
		pass

	if sensor1error == 0:
		try:
			# if limits were trigged
			if limitsOk == False:
				# check log when was last warning sended
				okToUpdate, tempWarning = checkWarningLog(sensor1,sensor1temperature)
		except: 
			# if limits were triggered but something caused error, send warning mail to indicate this
			emailWarning("Failed to check/insert log entry from mailsendlog. Sensor: {0}".format(sensor1),msgType)	
			sys.exit(0)

		if okToUpdate == True:
			# enough time has passed since last warning or temperature has increased/decreased by 5 degrees since last measurement
			warningMessage = warningMessage + "\n" + tempWarning
			# send warning
			emailWarning(warningMessage, msgType)
			try:
			# Insert line to database to indicate when warning was sent
				currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTime,sensor1,sensor1lowlimit,sensor1temperature)
				databaseHelper(sqlCommand,"Insert")
			except:
				# if database insert failed, send warning to indicate that there is some issues with database
				emailWarning("Failed to insert from {0} to mailsendlog".format(sensor1),msgType)	
	
	# sensor 2 readings and limit check
	sensor2error = 0
	okToUpdate = False
	
	if sensorsToRead != "1":
		try:
			sensor2temperature, sensor2humidity = sensorReadings(gpioForSensor2, sensorType)
			limitsOk,warningMessage = checkLimits(sensor2,sensor2temperature,sensor2humidity,sensor2highlimit,sensor2lowlimit)
		except:
			emailWarning("Failed to read {0} sensor".format(sensor2),msgType)
			sensor2error = 1
			pass

		if sensor2error == 0:
			try:		
				if limitsOk == False:
					okToUpdate, tempWarning = checkWarningLog(sensor2,sensor2temperature)	

			except:
				emailWarning("Failed to check/insert log entry from mailsendlog. Sensor: {0}".format(sensor2),msgType)	
				sys.exit(0)

			if okToUpdate == True:
				warningMessage = warningMessage + "\n" + tempWarning
				emailWarning(warningMessage, msgType)
				try:
					# Insert line to database to indicate when warning was sent
			       		sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTime,sensor2,sensor2lowlimit,sensor2temperature)
					databaseHelper(sqlCommand,"Insert")
				except:
					emailWarning("Failed to insert entry from {0} to mailsendlog".format(sensor1),msgType)	

	# insert values to db
	try:
		if sensor1error == 0:
			sqlCommand = "INSERT INTO temperaturedata SET dateandtime='%s', sensor='%s', temperature='%s', humidity='%s'" % (currentTime,sensor1,sensor1temperature,sensor1humidity)
			# This row below sets temperature as fahrenheit instead of celsius. Comment above line and uncomment one below to take changes into use
			#sqlCommand = "INSERT INTO temperaturedata SET dateandtime='%s', sensor='%s', temperature='%s', humidity='%s'" % (currentTime,sensor1,(sensor1temperature*(9.0/5.0)+32),sensor1humidity)
			databaseHelper(sqlCommand,"Insert")
		if sensorsToRead != "1" and sensor2error == 0:
			sqlCommand = "INSERT INTO temperaturedata SET dateandtime='%s', sensor='%s', temperature='%s', humidity='%s'" % (currentTime,sensor2,sensor2temperature,sensor2humidity)
			databaseHelper(sqlCommand,"Insert")
   	except:
		sys.exit(0)

if __name__ == "__main__":
	main()
