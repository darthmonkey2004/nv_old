import pickle
import logging
import datetime
import os



global conf, LOGFILE, CONFFILE
home = os.path.expanduser("~")
user = home.split('/')[2]
from nv import DATA_DIR
from nv.main.conf import readConf, writeConf
LOGFILE = f"{DATA_DIR}/nv.log"
CONFFILE = f"{DATA_DIR}{os.path.sep}nv.conf"






class nv_logger():
	def __init__(self):
		self.logfile = LOGFILE
		lvl_debug = getattr(logging, 'DEBUG', None)
		lvl_critical = getattr(logging, 'CRITICAL', None)
		lvl_error = getattr(logging, 'ERROR', None)
		lvl_fatal = getattr(logging, 'FATAL', None)
		lvl_fatal = getattr(logging, 'INFO', None)
		lvl_warning = getattr(logging, 'WARNING', None)
		self.conf = readConf()
		self.log_type = 'debug'
		self.log_level = getattr(logging, self.log_type.upper(), None)
		logging.basicConfig(filename=self.logfile, level=self.log_level)
		self.msg = None
		if self.conf['debug'] == None:
			self.conf = np.initConf()
			np.writeConf(self.conf)
			np.log(f"Over wrote conf file (empty debug string. Data: {self.conf}", 'warning')
		try:
			self.debug = self.conf['debug']
		except Exception as e:
			print (f"Error in log.py: debug setting not in conf: {e}")
	def log_msg(self, *args):
		#print (self.msg)
		pos = -1
		t = datetime.datetime.now()
		ts = (str(t.day) + "-" + str(t.month) + "-" + str(t.year) + " " + str(t.hour) + ":" + str(t.minute) + ":" + str(t.second) + ":" + str(t.microsecond))
		for arg in args:
			pos = pos + 1
			if pos == 0:
				self.msg = (ts + "--" + str(arg))
			elif pos == 1:
				self.log_type = arg
				self.log_level = getattr(logging, self.log_type.upper(), None)
				logging.basicConfig(filename=self.logfile, level=self.log_level)
		if not isinstance(self.log_level, int):
			raise ValueError('Invalid log level: %s' % self.log_type)
			return
		if self.msg == None:
			raise ValueError('No message data provided!')
		if self.debug == True:
			print ("DEBUG MESSAGE:", self.msg)
		if self.log_level == 10:#debug level
			logging.debug(self.msg)
		elif self.log_level == 20:
			logging.info(self.msg)
		elif self.log_level == 30:
			logging.warning(self.msg)
		elif self.log_level == 40:
			logging.error(self.msg)
			try:
				print("NicVision logged an error:", self.msg)
			except Exception as e:
				ouch=("Unable to print error message, background process(?)", self.msg, e)
				logging.error(ouch)
				raise RuntimeError(ouch) from e
				print (f"Log class exiting with errors: {e}")
				return
		return
