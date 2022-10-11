import sys
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import *
from threading import Thread
from nv.main.conf import read_opts

#f"http://monkey:{pw}@192.168.2.22:6969/video"
class Window(QMainWindow):
	def __init__(self, url=None):
		if url is None:
			opts = read_opts
			url = opts['src']['url']
		super(Window,self).__init__()
		self.browser = QWebEngineView()
		camera_id = opts['camera_id']
		self.browser.setUrl(QUrl(url))
		self.setCentralWidget(self.browser)
		self.showMaximized()
		self.searchBar = QLineEdit()
		self.searchBar.returnPressed.connect(self.loadUrl)
	def home(self):
		self.browser.setUrl(QUrl(f"{opts['src']}"))
	def loadUrl(self):
		#fetching entered url from searchBar
		url = self.searchBar.text()
		self.browser.setUrl(QUrl(url))
	def updateUrl(self, url):
		self.searchBar.setText(url.toString())

def run_browser(opts=None):
	if opts is None:
		opts = read_opts(0)
	MyApp = QApplication(sys.argv)
	#setting application name
	QApplication.setApplicationName('NicVision MPJG Viewer')
	#creating window
	window = Window(opts)
	#executing created app
	MyApp.exec_()

def start_thread(opts=None):
	if opts is None:
		opts = read_opts(0)
	t = Thread(target=run_browser, args=(opts,))
	t.setDaemon(True)
	t.start()
if __name__ == "__main__":
	start_thread()
