class BaseHandler(object):
	"""For using this class in order to build a handler check the documentation
	to learn how to deploy a new handler"""
	
	def __init__(self):
		#this list will hold all the collected results from job executions
		self.__results = []
	
	def __save(self, name, data, description, group):
		"""
		These are the basic fields of all the JobAttributes
		name: name of the attribute eg EVENT_LOOP
		data: the actual data of the attribute eg : 1701
		description: an optional field, to document with a short description the saved attribute
		group: an optional field in case you want to group your attributes, specify a group eg "Timing"
		"""
		dataDict = {
				'name' : name,
				'data' : data,
				'description' : description,
				'group' : group,
					}
		return dataDict
	
	def saveInt(self,name,data,description="",group=""):
		if name == '' or data == '':
			return False
		
		dataDict = self.__save(name, data, description, group)
		dataDict['type'] = 'Integer'
		
		self.__results.append(dataDict)
	
	def saveFloat(self,name,data,description="",group=""):
		if name == '' or data == '':
			return False
		
		dataDict = self.__save(name, data, description, group)
		dataDict['type'] = 'Float'
		
		self.__results.append(dataDict)
	
	def saveString(self,name,data,description="",group=""):
		if name == '' or data == '':
			return False
		
		dataDict = self.__save(name, data, description, group)
		dataDict['type'] = 'String'
		
		self.__results.append(dataDict)
	
	def saveFile(self,name,filename,description="",group=""):
		"""
		This method is used to save files
		name: provide the name you want your saved file to have
		filename: in this parameter provide the actual path to the file you want to file
		eg saveFile("Gauss-histogram.root", "/afs/cern.ch/user/.../tests/Gauss-30000000-100ev-20130425-histos.root")
		"""
		if name == '' or filename == '':
			return False
		
		dataDict = {
				'name' : name,
				'filename' : filename,
				'description' : description,
				'group' : group,
				'type' : 'File'
					}
		
		self.__results.append(dataDict)
		
	def getResults(self):
		return self.__results
	
	def collectResults(self, directory='.'):
		return NotImplementedError()
		
		
	
	 