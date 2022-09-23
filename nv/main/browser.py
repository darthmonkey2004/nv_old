import sys
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import *
from threading import Thread
from nv.main.conf import read_opts

class Window(QMainWindow):
	def __init__(self, opts):
		super(Window,self).__init__()
		#---------------------adding browser-------------------
		self.browser = QWebEngineView()
		camera_id = opts['camera_id']
		self.browser.setUrl(QUrl(opts[camera_id]['url']))
		self.setCentralWidget(self.browser)
		#-------------------full screen mode------------------
		#to display browser in full screen mode, you may comment below line if you don't want to open your browser in full screen mode
		self.showMaximized()
		#----------------------navbar-------------------------
		#creating a navigation bar for the browser
		#navbar = QToolBar()
		#adding created navbar
		#self.addToolBar(navbar)
		#-----------------prev Button-----------------
		#creating prev button
		#prevBtn = QAction('Prev',self)
		#when triggered set connection 
		#prevBtn.triggered.connect(self.browser.back)
		# adding prev button to the navbar
		#navbar.addAction(prevBtn)
		#-----------------next Button---------------
		#nextBtn = QAction('Next',self)
		#nextBtn.triggered.connect(self.browser.forward)
		#navbar.addAction(nextBtn)
		#-----------refresh Button--------------------
		#refreshBtn = QAction('Refresh',self)
		#refreshBtn.triggered.connect(self.browser.reload)
		#navbar.addAction(refreshBtn)
		#-----------home button----------------------
		#homeBtn = QAction('Home',self)
		#when triggered call home method
		#homeBtn.triggered.connect(self.home)
		#navbar.addAction(homeBtn)
		#---------------------search bar---------------------------------
		#to maintain a single line
		self.searchBar = QLineEdit()
		#when someone presses return(enter) call loadUrl method
		self.searchBar.returnPressed.connect(self.loadUrl)
		#adding created seach bar to navbar
		#navbar.addWidget(self.searchBar)
		#if url in the searchBar is changed then call updateUrl method
		#self.browser.urlChanged.connect(self.updateUrl)
	#method to navigate back to home page
	def home(self):
		self.browser.setUrl(QUrl(f"{opts['src']}"))
	#method to load the required url
	def loadUrl(self):
		#fetching entered url from searchBar
		url = self.searchBar.text()
		#loading url
		self.browser.setUrl(QUrl(url))
	#method to update the url
	def updateUrl(self, url):
		#changing the content(text) of searchBar
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
