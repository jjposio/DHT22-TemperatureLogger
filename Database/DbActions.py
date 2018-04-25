import MySQLdb
import os
import logging
import subprocess

# TODO MySqldb.connect is done separately in each function. Check if reasonable to do once in init

class DbActions():
	' Helper function for database actions. Handles select, insert and sql dump '

	
	def __init__(self, configurations):
		self.logger = logging.getLogger(__name__)
		self.logger.info("DBActions instantiation started")

		# Set configuration data for variables for easier usage
		self.host = configurations.get('sqlConfig')[0]['host']
		self.user = configurations.get('sqlConfig')[0]['user']
		self.password = configurations.get('sqlConfig')[0]['password']
		self.database = configurations.get('sqlConfig')[0]['database']
		self.backupDumpConfig = configurations.get('backupDumpConfig')
		self.timeAsString = configurations.get('currentTimeAsString')
		self.dateAsString = configurations.get('dateAsString')

		self.logger.info("DBActions instantiated")

	' Select function '
	def sqlSelect(self,sqlQuery):
		self.logger.info('Executing Sql SELECT')

		# Connect to db
		db = MySQLdb.connect(self.host,self.user,self.password,self.database)
		cursor=db.cursor()

		try:
			# Execute passed in query
			cursor.execute(sqlQuery)
			data = cursor.fetchone()
		except:
			self.logger.error("Executing Sql SELECT failed")
			raise

		self.logger.info("Executing Sql SELECT finished")
		return data

	' Insert function '
	def sqlInsert(self,sqlQuery):
		self.logger.info('Executing Sql INSERT')
		
		# Connect to db
		db = MySQLdb.connect(self.host,self.user,self.password,self.database)
		cursor=db.cursor()

		try:
			# Execute passed in query
			cursor.execute(sqlQuery)
			db.commit()
		except:
			self.logger.error("Executing Sql INSERT failed")
			db.rollback()
			raise

		self.logger.info("Executing Sql INSERT finished")

	' Function for sql backup '
	def sqlBackup(self):
		self.logger.info("Sql backup dump execution started")

		# Set dumpPath to variable for easier reference
		dumpPath = self.backupDumpConfig[0]['backupDumpPath']

		# Getting current datetime to create seprate backup folder like "12012013-071334".
		backupPathWithDate = dumpPath + self.dateAsString

		self.logger.info("Folder to create for backup:%s",backupPathWithDate)
		# Checking if backup folder already exists or not. If not exists will create it.
		if not os.path.exists(backupPathWithDate):
			self.logger.info("Dated backup folder doesn't exist. Creating one...")
			try:
				self.logger.info("Checking if backup dump folder is writeable")
				# Check if path has write permissions enabled
				if not os.access(dumpPath,os.W_OK):
				# If write permission is not set, try adding with subprocess
					self.logger.warning("{0} not writeable. Try adding access rights".format(dumpPath))
					try:
						# Start subprocess and execute sudo chmod -R 777 to folder where dumps are going. This allows writing to the folder.
						subprocess.call(['sudo','chmod','-R','777',dumpPath])
					except:
						self.logger.error("Failed to grant write permissions to dump path with subprocess")
						raise
					self.logger.info("Access rights added successfully, create dated folder...")
				else:
					self.logger.warning("Dump folder is writeable, continue")
				os.makedirs(backupPathWithDate)

			except IOError:
				self.logger.error("Failed to create backup folder")
				raise
			self.logger.info("Backup folder created")

			try:
				# Dump command
				dumpCmd = "mysqldump -u {0} -p{1} {2} > {3}/{4}.sql".format(self.user,self.password,self.database,backupPathWithDate,self.database)
				self.logger.info("Starting dump")

				# Execute dump command
				os.system(dumpCmd)
			
				self.logger.info("Sql backup dump done")
			except:
				self.logger.error("SQL Backup dump failed")
				raise
		else:
			self.logger.warning("Sql backup dumped already for today")

		return
