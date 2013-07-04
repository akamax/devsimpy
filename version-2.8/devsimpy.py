#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# main.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2013
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 2.7.1                                      last modified:  08/01/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# strong depends: wxPython, wxversion
# light depends : NumPy for spectrum analysis, mathplotlib for graph display
# remarque; attention, la construction de l'arbre des librairies (ou domain) est fait par la classe TreeListLib.
# De plus, cette construction necessite la présence obligatoire du fichier __init__.py dans chaque sous domain d'un domaine repertorié dans le repertoire Domain (voir methode recursive GetSubDomain).
# L'utilisateur doit donc ecrire se fichier en sautant les lignes dans le __all__ = []. Si le fichier n'existe pas le prog le cree.
# Pour importer une lib: 1/ faire un rep MyLib dans Domain avec les fichier Message.py, DomainBehavior.py et DomaineStrucutre.py
#                                               2/ stocker tout les autre .py dans un sous rep contenant également un fichier __init__ dans lequel son ecris les fichier a importer.
#                                               3/ les fichier .cmd issu de l'environnement peuvent etre stocké nimport ou il seron pris en compte en tant que model couplé.
#                                               4/ les fichier init doivent respecter le format de saus de ligne pour une bonne importation.
#                                               5/ tout fichier .py qui ne se trouve pas dans init n'est ps importé
#                                               6/ lors de l'import des .py (DnD) attention, il faut aussi que les parametres du constructeurs aient des valeurs par defaut.
#                                               7/ le nom des modeles atomiques dans le GUI necessite l'implémentation de la méthode __str__ dans les classes (sinon il note les modèles AM)
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### at the beginning to prevent with statement for python vetrsion <=2.5
from __future__ import with_statement

__authors__  = "Laurent Capocchi <capocchi@univ-corse.fr, lcapocchi@gmail.com>, TIC project team <santucci@univ-coorse.fr>" # ajouter les noms et les mails associés aux autres auteurs
__date__    = "05 Feb 2012, 17:07 GMT"
__version__ = '2.8'
__docformat__ = 'epytext'

import copy
import os
import sys
import time
import gettext
import __builtin__
import webbrowser
import platform
import threading
import inspect
import httplib
import urlparse
import cPickle
import zipfile

from tempfile import gettempdir

try:
	import hotshot
	import hotshot.stats
except ImportError:
	sys.stdout.write("Hotshot module not found. If you want to perform profiling simulation, install it !")

from urllib import urlopen

__min_wx_version__ = ['2.8','2.7','2.6','2.5']

__wxpython_url__ = 'http://wxpython.org'
__get__wxpython__ = 'Get it from %s'%__wxpython_url__

try:

	if not hasattr(sys, 'frozen'):
		import wxversion as wxv

		if wxv.checkInstalled(__min_wx_version__):
			wxv.select(__min_wx_version__)
		else:
			import wx
			app = wx.PySimpleApp()
			wx.MessageBox("The requested version of wxPython is not installed.\nPlease install version %s" %__min_wx_version__, "wxPython Version Error")
			app.MainLoop()
			webbrowser.open(__wxpython_url__)
			sys.exit()

	import wx

except ImportError:
	## wxversion not installed
	try:
		import wx
		if wx.VERSION_STRING < __min_wx_version__:
			sys.stdout.write("You need to updgarde wxPython to v%s (or higer) to run DEVSimPy\n"%__min_wx_version__)
			sys.stdout.write(__get_wxpython__)
			sys.exit()
	except ImportError:
			sys.stderr.write("Error: DEVSimPy requires wxPython, which doesn't seem to be installed\n")
			sys.stdout.write(__get__wxpython__)
			sys.exit()
	sys.stdout.write("Warning: the package python-wxversion was not found, please install it.\n")
	sys.stdout.write("DEVSimPy will continue anyway, but not all features might work.\n")

sys.stdout.write("Importing wxPython %s for python %s on %s (%s) platform \n"%(wx.__version__, platform.python_version(), platform.system(), platform.version()))

import wx.aui
import wx.py as py
import wx.lib.dialogs
import wx.html

try:
	from wx.lib.agw import advancedsplash
	AdvancedSplash = advancedsplash.AdvancedSplash
	old = False
except ImportError:
	AdvancedSplash = wx.SplashScreen
	old = True

# to send event
if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher as pub
else:
	from wx.lib.pubsub import setuparg1
	from wx.lib.pubsub import pub


### here berfore the __main__ function
if len(sys.argv) >= 2 and sys.argv[1] in ('-ng, -nogui, -js, -javascript'):
	__builtin__.__dict__['GUI_FLAG'] = False
	from SimulationNoGUI import makeSimulation, makeJS
else:
	__builtin__.__dict__['GUI_FLAG'] = True

### import Container much faster loading than from Container import ... for os windows only
import Container
import Menu

from DomainInterface.DomainBehavior import DomainBehavior
from Patterns.Observer import Observer
from ImportLibrary import ImportLibrary
from Reporter import ExceptionHook
from ConnectionThread import UpgradeLibThread
from PreferencesGUI import PreferencesGUI
from pluginmanager import load_plugins
from PrintOut import Printable
from which import which
from Utilities import GetMails, replaceAll, getFileListFromInit, path_to_module, IsAllDigits
from ReloadModule import recompile
from Decorators import redirectStdout, BuzyCursorNotification
from ZipManager import Zip, getPythonModelFileName
from Components import BlockFactory, DEVSComponent, GetClass
from DetachedFrame import DetachedFrame


ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

### specific builtin variables. (dont modify the defautls value. If you want to change it, go tot the PreferencesGUI from devsimpy interface.)
builtin_dict = {'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'bitmaps', 'splash.png'),
				'DEVSIMPY_PNG': 'iconDEVSimPy.png',	# png file for devsimpy icon
				'HOME_PATH': ABS_HOME_PATH,
				'ICON_PATH': os.path.join(ABS_HOME_PATH, 'icons'),
				'ICON_PATH_16_16': os.path.join(ABS_HOME_PATH, 'icons', '16x16'),
				'SIMULATION_SUCCESS_WAV_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Success.wav'),
				'SIMULATION_ERROR_WAV_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Error.wav'),
				'DOMAIN_PATH': os.path.join(ABS_HOME_PATH, 'Domain'), # path of local lib directory
				'NB_OPENED_FILE': 5, # number of recent files
				'NB_HISTORY_UNDO': 5, # number of undo
				'OUT_DIR': 'out', # name of local output directory (composed by all .dat, .txt files)
				'PLUGINS_DIR': 'plugins', # general plugins directory
				#'PLUGINS_FILENAME': 'plugins', # model plugins file name
				'FONT_SIZE': 12, # Block font size
				'LOCAL_EDITOR': True, # for the use of local editor
				'LOG_FILE': os.devnull, # log file (null by default)
				'DEFAULT_SIM_STRATEGY': 'SimStrategy2', #choose the default simulation strategy
				'SIM_STRATEGY_LIST' : ['SimStrategy1', 'SimStrategy2', 'SimStrategy3'], # list of available simulation strategy
				'HELP_PATH' : os.path.join('doc', 'html'), # path of help directory
				'NTL' : False, # No Time Limit for the simulation
				'TRANSPARENCY' : True, # Transparancy for DetachedFrame
				'DEFAULT_PLOT_DYN_FREQ' : 100 # frequence of dynamic plot of QuickScope (to avoid overhead)
				}

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
__builtin__.__dict__.update(builtin_dict)

#-------------------------------------------------------------------
def getIcon(img_file):
	path = os.path.join(ICON_PATH_16_16, img_file)
	icon = wx.EmptyIcon()
	#if os.path.exists(path):
	bmp = wx.Image(path).ConvertToBitmap()
	bmp.SetMask(wx.Mask(bmp, wx.WHITE))
	icon.CopyFromBitmap(bmp)
	#else:
		#ABS_HOME_PATH = os.getcwd()

	return icon

#-------------------------------------------------------------------
def DefineScreenSize(percentscreen = None, size = None):
	"""Returns a tuple to define the size of the window
		percentscreen = float
	"""
	if not size and not percentscreen:
		percentscreen = 0.8
	if size:
		l, h = size
	elif percentscreen:
		x1, x2, l, h = wx.Display().GetClientArea()
		#print "ClientArea = ", l, h
		l, h = percentscreen * l, percentscreen * h
	return l, h

#----------------------------------------------------------------------------------------------------
class LibraryTree(wx.TreeCtrl):
	"""	Class of libraries tree of devsimpy model and python files.

		EXT_LIB_FILE = tuple of considered devsimpy file extention.
		EXT_LIB_PYTHON_FLAG = flag to used model from python file instanciation.
		EXCLUDE_DOMAIN = List of exclude directory
	"""

	### type of considered files
	EXT_LIB_FILE = ('.cmd', '.amd')
	### if True, python files are visible in the tree
	EXT_LIB_PYTHON_FLAG = True
	### exclude rep present into Domain
	EXCLUDE_DOMAIN = ['Basic', '.svn']

	def __init__(self, *args, **kwargs):
		""" Constructor
		"""

		wx.TreeCtrl.__init__(self, *args, **kwargs)

		# correspondance entre path (cle) et item du Tree (valeur)
		self.ItemDico = {}

		isz = (16,16)
		il = wx.ImageList(isz[0], isz[1])
		self.fldridx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
		self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz))
		self.fileidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
		self.atomicidx = il.Add(wx.Image(os.path.join(ICON_PATH_16_16, 'atomic3.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.coupledidx = il.Add(wx.Image(os.path.join(ICON_PATH_16_16, 'coupled3.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.pythonfileidx = il.Add(wx.Image(os.path.join(ICON_PATH_16_16, 'pythonFile.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.not_importedidx = il.Add(wx.Image(os.path.join(ICON_PATH_16_16, 'no_ok.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.SetImageList(il)
		self.il = il

		self.root = self.AddRoot(os.path.basename(DOMAIN_PATH))
		self.SetItemBold(self.root)

		self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightItemClick)
		self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
		self.Bind(wx.EVT_TREE_ITEM_MIDDLE_CLICK, self.OnMiddleClick)

		self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClick)
		self.Bind(wx.EVT_MOTION, self.OnMotion)


	def Populate(self, chargedDomainList = []):
		""" Populate the Tree from a list of domain path.
		"""

		assert self.root != None, _("Missing root")

		for absdName in chargedDomainList:
			self.InsertNewDomain(absdName, self.root, self.GetSubDomain(absdName, self.GetDomainList(absdName)).values()[0])

		self.UnselectAll()
		self.SortChildren(self.root)

	def OnMotion(self, evt):
		""" Motion engine over item.
		"""
		item, flags = self.HitTest(evt.GetPosition())

		if item and self.IsSelected(item) and (flags & wx.TREE_HITTEST_ONITEMLABEL) and not evt.LeftIsDown():

			path = self.GetItemPyData(item)

			if os.path.isdir(path):
				model_list = self.GetModelList(path)
				domain_list = self.GetDomainList(path)
				if domain_list != []:
					tip = '\n'.join(domain_list)
				elif model_list != []:
					tip = '\n'.join(model_list)
				else:
					tip = ""
			### is last item
			else:
				module = BlockFactory.GetModule(path)
				info = Container.CheckClass(path)

				if isinstance(info, tuple):
					doc = str(info)
				elif isinstance(module, tuple):
					doc = str(module)
				else:
					doc = inspect.getdoc(module)

				tip = doc if doc is not None else _("No documentation for selected model.")

			self.SetToolTipString(tip.decode('utf-8'))

		else:
			self.SetToolTip(None)

		### else the drag and drop dont run
		evt.Skip()

	def OnLeftClick(self, evt):
		"""
		"""

		self.UnselectAll()
		mainW = wx.GetApp().GetTopWindow()
		mainW.statusbar.SetStatusText('', 0)
		mainW.statusbar.SetStatusText('', 1)
		self.SetFocus()
		evt.Skip()

	def OnMiddleClick(self, evt):
		"""
		"""
		item_selected = evt.GetItem()
		if not self.ItemHasChildren(item_selected):
			path = self.GetItemPyData(item_selected)
			mainW = wx.GetApp().GetTopWindow()
			nb2 = mainW.nb2
			canvas = nb2.GetPage(nb2.GetSelection())
			### define path for python and model component

			if path.endswith('.py'):
				### create component
				m = GetBlockModel(	canvas = canvas,
									x = 40,
									y = 40,
									label = self.GetItemText(item_selected),
									id = 0,
									inputs = 1,
									outputs = 1,
									python_file = path,
									model_file = "")
				if m:

					# Adding graphical model to diagram
					canvas.AddShape(m)

					sys.stdout.write(_("Adding DEVSimPy model: \n").encode('utf-8'))
					sys.stdout.write(repr(m))

					# focus
					#canvas.SetFocus()

			else:
				sys.stdout.write(_("This option has not been implemented yet. \n"))
	###
	def OnRightClick(self, evt):
		""" Right click has been clicked.
		"""

		# si pas d'item selectionnner, le evt.Skip à la fin propage l'evenement vers OnRightItemClick
		if self.GetSelections() == []:
			self.PopupMenu(Menu.LibraryPopupMenu(self), evt.GetPosition())
		else:
			evt.Skip()

	###
	def OnRightItemClick(self, evt):
		"""
		"""
		self.PopupMenu(Menu.ItemLibraryPopupMenu(self), evt.GetPoint())
		evt.Skip()

	###
	def OnDelete(self, evt):
		""" Delete the item from Tree
		"""

		self.RemoveItem(self.GetSelection())

	def OnNewModel(self, evt):
		Container.ShapeCanvas.StartWizard(self)

	###
	def GetDomainList(self, dName):
		""" Get the list of sub-directory of dName directory
		"""

		if dName.startswith('http'):
			o = urlparse(dName)
			if dName.startswith('https'):
				c = httplib.HTTPSConnection(o.netloc)
			else:
				c = httplib.HTTPConnection(o.netloc)
			c.request('GET', o.path+'/__init__.py')

			r = c.getresponse()

			code = r.read()
			if r.status == 200:
				exec code
				#return filter(lambda d: d not in LibraryTree.EXCLUDE_DOMAIN, __all__)
				return __all__
			else:
				return []

		else:
			return [f for f in os.listdir(dName) if os.path.isdir(os.path.join(dName, f)) and f not in LibraryTree.EXCLUDE_DOMAIN] if os.path.isdir(dName) else []

	###
	def GetItemChildren(self, item, recursively = False):
		""" Return the children of item as a list. This method is not )
		part of the API of any tree control, but very convenient to
		have available.
		"""

		children = []
		child, cookie = self.GetFirstChild(item)
		while child:
			children.append(child)
			if recursively:
				children.extend(self.GetItemChildren(child, True))
			child, cookie = self.GetNextChild(item, cookie)
		return children

	###
	def GetModelList(self, dName):
		""" Get the list of files from dName directory.
		"""

		### list of py file from __init__.py
		if LibraryTree.EXT_LIB_PYTHON_FLAG:

			### lsit of py file from url
			if dName.startswith('http'):

				o = urlparse(dName)
				c = httplib.HTTPConnection(o.netloc)
				c.request('GET', o.path+'/__init__.py')

				r = c.getresponse()
				code = r.read()

				if r.status == 200:
					exec code
					tmp = filter(lambda s: s.replace('\n','').replace('\t','').replace(',','').replace('"',"").replace('\'',"").strip(), __all__)
					### test if the content of __init__.py file is python file (isfile equivalent)
					py_file_list = [s for s in tmp if 'python' in urlopen(dName+'/'+s+'.py').info().type]

				else:
					py_file_list = []

				return py_file_list
			else:
				try:
					name_list = getFileListFromInit(os.path.join(dName,'__init__.py'))
					py_file_list = []
					for s in name_list:
						python_file = os.path.join(dName,s+'.py')
						### test if tmp is only composed by python file (case of the user write into the __init__.py file directory name is possible ! then we delete the directory names)
						if os.path.isfile(python_file):

							cls = GetClass(python_file)

							if cls is not None and not isinstance(cls, tuple):
								### only model that herite from DomainBehavior is shown in lib
								if issubclass(cls, DomainBehavior):
									py_file_list.append(s)

							### If cls is tuple, there is an error but we load the model to correct it.
							### If its not DEVS model, the Dnd don't allows the instantiation and when the error is corrected, it don't appear before a update.
							else:

								py_file_list.append(s)

				except Exception:
					py_file_list = []
					# if dName contains a python file, __init__.py is forced
					for f in os.listdir(dName):
						if f.endswith('.py'):
							#sys.stderr.write(_("%s not imported : %s \n"%(dName,info)))
							break
		else:
			py_file_list = []

		# list of amd and cmd files
		devsimpy_file_list = [f for f in os.listdir(dName) if os.path.isfile(os.path.join(dName, f)) and (f[:2] != '__') and (f.endswith(LibraryTree.EXT_LIB_FILE))]

		return py_file_list + devsimpy_file_list

	###
	def InsertNewDomain(self, dName, parent, L = []):
		""" Recurcive function that insert new Domain on library panel.
		"""

		### au depard seulement pour le parent de plus haut niveau (comme PowerSystem)
		if dName not in self.ItemDico.keys():
			label = os.path.basename(dName) if not dName.startswith('http') else filter(lambda a: a!='', dName.split('/'))[-1]
			id = self.InsertItemBefore(parent, 0, label)
			self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
			self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)
			self.SetItemBold(id)
			self.ItemDico.update({dName:id})
			self.SetPyData(id,dName)

		### fin de la recursion
		if L == []:
			return
		else:
			item = L.pop(0)
			assert not isinstance(item,unicode), _("Warning unicode item !")
			### element à faire remonter dans la liste
			D = []
			### si le fils est un modèle construit dans DEVSimPy
			if isinstance(item, str):

				### le parent est récupére dans le Dico
				parent = self.ItemDico[dName]
				assert parent != None

				### path correspondant au parent
				parentPath = self.GetPyData(parent)

				### remplacement des espaces
				item = item.strip()

				come_from_net = parentPath.startswith('http')

				### suppression de l'extention su .cmd (model atomic lue a partir de __init__ donc pas d'extention)
				if item.endswith('.cmd'):
					### gestion de l'importation de module (.py) associé au .cmd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
					if not come_from_net:
						path = os.path.join(parentPath, item)
						zf = Zip(path)
						module = zf.GetModule()
						image_file = zf.GetImage()
					else:
						path = parentPath+'/'+item+'.py'
						module = load_module_from_net(path)

					### check error
					error = isinstance(module, Exception)

					### change icon depending on the error and the presence of image in amd
					if error:
						img = self.not_importedidx
					elif image_file is not None:
						img = self.il.Add(image_file.ConvertToBitmap())
					else:
						img = self.coupledidx

					### insertion dans le tree
					id = self.InsertItemBefore(parent, 0, os.path.splitext(item)[0], img, img)
					self.SetPyData(id, path)

				elif item.endswith('.amd'):
					### gestion de l'importation de module (.py) associé au .amd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
					if not come_from_net:
						path = os.path.join(parentPath, item)
						zf = Zip(path)
						module = zf.GetModule()
						image_file = zf.GetImage()
					else:
						path = parentPath+'/'+item+'.py'
						module = load_module_from_net(path)

					### check error
					error = isinstance(module, Exception)

					### change icon depending on the error and the presence of image in amd
					if error:
						img = self.not_importedidx
					elif image_file is not None:
						img = self.il.Add(image_file.ConvertToBitmap())
					else:
						img = self.atomicidx

					### insertion dans le tree
					id = self.InsertItemBefore(parent, 0, os.path.splitext(item)[0], img, img)
					self.SetPyData(id, path)

				else:

					path = os.path.join(parentPath, item+'.py') if not parentPath.startswith('http') else parentPath+'/'+item+'.py'

					info = Container.CheckClass(path)

					error = isinstance(info, tuple)
					img = self.not_importedidx if error else self.pythonfileidx
					### insertion dans le tree
					id = self.InsertItemBefore(parent, 0, item, img, img)
					self.SetPyData(id, path)

				### error info back propagation
				if error:
					while(parent):
						self.SetItemImage(parent, self.not_importedidx, wx.TreeItemIcon_Normal)
						### next parent item
						parent = self.GetItemParent(parent)

				### insertion des donnees dans l'item et gestion du ItemDico
				self.ItemDico.update({os.path.join(parentPath,item,):id})

			### si le fils est un sous repertoire contenant au moins un fichier (all dans __init__.py different de [])
			elif isinstance(item, dict) and item.values() != [[]]:

				### nom a inserer dans l'arbe
				dName = os.path.basename(item.keys()[0])

				### nouveau parent
				parent = self.ItemDico[os.path.dirname(item.keys()[0])] if not dName.startswith('http') else self.ItemDico[item.keys()[0].replace('/'+dName,'')]

				assert(parent!=None)
				### insertion de fName sous parent
				id = self.InsertItemBefore(parent, 0, dName)

				self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
				self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)
				### stockage du parent avec pour cle le chemin complet avec extention (pour l'import du moule dans le Dnd)
				self.ItemDico.update({item.keys()[0]:id})
				self.SetPyData(id,item.keys()[0])
				### pour les fils du sous domain
				for elem in item.values()[0]:
					# si elem simple (modèle couple ou atomic)
					if isinstance(elem,str):
						### remplacement des espaces
						elem = elem.strip() #replace(' ','')
						### parent provisoir
						p = self.ItemDico[item.keys()[0]]
						assert(p!=None)
						come_from_net = item.keys()[0].startswith('http')
						### si model atomic
						if elem.endswith('.cmd'):
							### gestion de l'importation de module (.py) associé au .amd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
							if not come_from_net:
								path = os.path.join(item.keys()[0], elem)
								zf = Zip(path)
								module = zf.GetModule()
								image_file = zf.GetImage()
							else:
								path = item.keys()[0]+'/'+elem+'.py'
								module = load_module_from_net(path)

							### check error
							error = isinstance(module, Exception)

							### change icon depending on the error and the presence of image in amd
							if error:
								img = self.not_importedidx
							elif image_file is not None:
								img = self.il.Add(image_file.ConvertToBitmap())
							else:
								img = self.coupledidx

							### insertion dans le tree
							id = self.InsertItemBefore(p, 0, os.path.splitext(elem)[0], img, img)
							self.SetPyData(id, path)
						elif elem.endswith('.amd'):
							### gestion de l'importation de module (.py) associé au .amd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
							if not come_from_net:
								path = os.path.join(item.keys()[0], elem)
								zf = Zip(path)
								module = zf.GetModule()
								image_file = zf.GetImage()
							else:
								path = item.keys()[0]+'/'+elem+'.py'
								module = load_module_from_net(path)

							### check error
							error = isinstance(module, Exception)

							### change icon depending on the error and the presence of image in amd
							if error:
								img = self.not_importedidx
							elif image_file is not None:
								img = self.il.Add(image_file.ConvertToBitmap())
							else:
								img = self.atomicidx

							### insertion dans le tree
							id = self.InsertItemBefore(p, 0, os.path.splitext(elem)[0], img, img)
							self.SetPyData(id, path)
						else:

							path = os.path.join(item.keys()[0],elem+'.py') if not item.keys()[0].startswith('http') else item.keys()[0]+'/'+elem+'.py'
							info = Container.CheckClass(path)

							error = isinstance(info, tuple)
							img = self.not_importedidx if error else self.pythonfileidx

							### insertion dans le tree
							id = self.InsertItemBefore(p, 0, elem, img, img)
							self.SetPyData(id, path)

						### error info back propagation
						if error:
							### insert error to the doc field
							while(p):
								self.SetItemImage(p, self.not_importedidx, wx.TreeItemIcon_Normal)
								### next parent item
								p = self.GetItemParent(p)

						self.ItemDico.update({os.path.join(item.keys()[0], os.path.splitext(elem)[0]):id})

					else:
						### pour faire remonter l'info dans la liste
						D.append(elem)

				### mise a jour avec le nom complet
				dName = item.keys()[0]

			### for spash screen
			try:
				### format the string depending the nature of the item
				if isinstance(item, dict):
					item = "%s from %s"%(os.path.basename(item.keys()[0]), os.path.basename(os.path.dirname(item.keys()[0])))
				else:
					item = "%s from %s"%(item, os.path.basename(dName))

				pub.sendMessage('object.added', 'Loading %s domain...'%item)
			except:
				pass

			### gestion de la recursion
			if D != []:
				return self.InsertNewDomain(dName,parent, L+D)
			else:
				return self.InsertNewDomain(dName,parent, L)

    ###
	def GetSubDomain(self, dName, domainSubList = []):
		""" Get the dico composed by all of the sub domain of dName (like{'../Domain/PowerSystem': ['PSDomainStructure', 'PSDomainBehavior', 'Object', 'PSSDB', {'../Domain/PowerSystem/Rt': []}, {'../Domain/PowerSystem/PowerMachine': ['toto.cmd', 'Integrator.cmd', 'titi.cmd', 'Mymodel.cmd', {'../Domain/PowerSystem/PowerMachine/TOTO': []}]}, {'../Domain/PowerSystem/Sources': ['StepGen', 'SinGen', 'CosGen', 'RampGen', 'PWMGen', 'PulseGen', 'TriphaseGen', 'ConstGen']}, {'../Domain/PowerSystem/Sinks': ['To_Disk', 'QuickScope']}, {'../Domain/PowerSystem/MyLib': ['', 'model.cmd']}, {'../Domain/PowerSystem/Hybrid': []}, {'../Domain/PowerSystem/Continuous': ['WSum', 'Integrator', 'Gain', 'Gain2', 'NLFunction']}]}
	)
		"""

		if domainSubList == []:
			### attention il faut que le fichier __init__.py respecte une certain ecriture
			return {dName:self.GetModelList(dName)}
		else:
			### on comptabilise les fichiers si il y en a dans le rep courant (la recusion s'occupe des sous domaines)
			D = {dName: self.GetModelList(dName)}
			### on lance la recursion sur les repertoires fils
			for d in domainSubList:
				p = os.path.join(dName,d)
				D[dName].append(self.GetSubDomain(p,self.GetDomainList(p)))
			return D

	###
	def GetChildRoot(self):
		""" Return the list compsed by the childs of the Root
		"""
		return map(lambda s: str(self.GetItemText(s)), self.GetItemChildren(self.root))

	###
	def IsChildRoot(self, dName):
		"""
		"""
		return (dName in self.GetChildRoot())

	def HasString(self, s = ""):
		"""
		"""
		return s in map(lambda item: str(self.GetItemText(item)), self.ItemDico.values())

	def CheckItem(self, path):
		"""
		"""

		item = self.ItemDico[path]
		file_path = "%s.py"%path

		info = Container.CheckClass(file_path)
		### there is error in file
		if isinstance(info, tuple):
			### Until it has parent, we redifine icon to inform user
			while(item):
				### change image
				self.SetItemImage(item, self.not_importedidx, wx.TreeItemIcon_Normal)
				### next parent item
				item = self.GetItemParent(item)
		else:
			### recompile if no error
			info = recompile(path_to_module(file_path))

			### if not error
			if not isinstance(info, (Exception,str)):
				### change image
				self.SetItemImage(item, self.pythonfileidx, wx.TreeItemIcon_Normal)

				#### Until it has parent, we redifine icon to inform user
				#while(item):
					#if self.IsExpanded(item):
						#### change image
						#self.SetItemImage(item, self.fldropenidx, wx.TreeItemIcon_Normal)
					#else:
						#self.SetItemImage(item, self.fldridx, wx.TreeItemIcon_Normal)

					#### next parent item
					#item = self.GetItemParent(item)
	###
	def UpdateDomain(self, path):
		""" Update the Tree Library with new path of the corresponding domain
		"""

		### only of the path is in the tree
		if self.HasString(os.path.basename(path)):
			dName = path

			### try to find focused item from dName
			try:
				item = self.ItemDico[dName]
			### if dName is not present in ItemDico but exist and represent the same directory, we find the path strored in ItemDico
			except KeyError:
				for p in self.ItemDico:
					if p.endswith(os.path.basename(dName)):
						item = self.ItemDico[p]

			### save parent before deleting item
			parent = self.GetItemParent(item)

			### save expanded info before deleting item
			expanded = self.IsExpanded(item)

			### remove for create udpated new item
			self.RemoveItem(item)

			### insertion du nouveau domain
			self.InsertNewDomain(dName, parent, self.GetSubDomain(dName, self.GetDomainList(dName)).values()[0])

			### module checking
			for d in self.GetSubDomain(dName, self.GetDomainList(dName)).values()[0]:
				if isinstance(d, dict):
					name_list =  d.values()[0]
					if name_list != []:
						path = d.keys()[0]
						for name in filter(lambda a: not isinstance(a, dict) and not a.endswith(('.cmd','.amd')), name_list):
							self.CheckItem(os.path.join(path, name))

			### extend item if it was extended
			if expanded:
				self.Expand(self.ItemDico[dName])

	@BuzyCursorNotification
	def OnUpdateAll(self, event):
		self.UpdateAll()

	def UpdateAll(self):
		"""
		"""

		### for expand the updated domain
		#expanded = [it for it in self.ItemDico if self.IsExpanded(self.ItemDico[it])]

		### update all Domain
		for item in self.GetItemChildren(self.GetRootItem()):
			self.UpdateDomain(self.GetPyData(item))

		### to sort domain
		self.SortChildren(self.root)

		#for it in expanded:
			#self.Expand(self.ItemDico[it])

	def UpgradeAll(self, evt):
		"""
		"""
		progress_dlg = wx.ProgressDialog(_("DEVSimPy upgrade libraries"),
								_("Connecting to %s ...")%"code.google.com", parent=self,
								style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
		progress_dlg.Pulse()

		thread = UpgradeLibThread(progress_dlg)

		while thread.isAlive():
			time.sleep(0.3)
			progress_dlg.Pulse()

		progress_dlg.Destroy()
		wx.SafeYield()

		return thread.finish()

	def RemoveItem(self, item):
		""" Remove item from Tree and also the corresponding elements of ItemDico
		"""

		### suppression des reference dans le ItemDico
		for key in copy.copy(self.ItemDico):
			if os.path.basename(self.GetPyData(item)) in key.split(os.sep):
				del self.ItemDico[key]

		self.Delete(item)

	def OnItemRefresh(self, evt):
		item = self.GetSelection()
		path = self.GetItemPyData(item)

		self.CheckItem(os.path.splitext(path)[0])

	def OnItemEdit(self, evt):
		item = self.GetSelection()
		path = self.GetItemPyData(item)

		### virtual DEVS component just for edition
		devscomp = DEVSComponent()

		### path depends on the nature of droped component
		### if pure python path
		if path.endswith('.py'):
			devscomp.setDEVSPythonPath(path)
		### if devsimpy model
		elif zipfile.is_zipfile(path):
			#zf = Zip(path)
			devscomp.setDEVSPythonPath(os.path.join(path, getPythonModelFileName(path)))
			devscomp.model_path = path
		else:
			sys.stdout.write(_('The code of this type of model is not editable'))
			return

		### call frame editor
		DEVSComponent.OnEditor(devscomp, evt)

	def OnItemRename(self, evt):
		item = self.GetSelection()
		path = self.GetItemPyData(item)

		bn = os.path.basename(path)
		dn = os.path.dirname(path)
		name, ext = os.path.splitext(bn)

		d = wx.TextEntryDialog(self,_('New file name'), defaultValue = name, style=wx.OK)
		d.ShowModal()

		### new label
		new_label = d.GetValue()
		os.rename(path, os.path.join(dn, new_label)+ext)
		replaceAll(os.path.join(dn,'__init__.py'), os.path.splitext(bn)[0], new_label)

		self.UpdateAll()

	def OnItemDocumentation(self, evt):
		""" Display the item's documentation on miniFrame.
		"""

		item = self.GetSelection()
		path = self.GetItemPyData(item)
		name = self.GetItemText(item)

		module = BlockFactory.GetModule(path)
		info = Container.CheckClass(path)

		if isinstance(info, tuple):
			doc = str(info)
		elif isinstance(module, tuple):
			doc = str(module)
		else:
			doc = inspect.getdoc(module)

		if doc:
			dlg = wx.lib.dialogs.ScrolledMessageDialog(self, doc, name)
			dlg.CenterOnParent(wx.BOTH)
			dlg.ShowModal()
		else:
			wx.MessageBox(_('No documentation for %s')%name, 'Info', wx.OK)

	def OnInfo(self, event):
		"""
		"""
		wx.MessageBox(_('Libraries Import Manager.\nYou can import, refresh or upgrade librairies by using right options.\nDefault libraries directory is %s.')%(DOMAIN_PATH))

#-----------------------------------------------------------------------
class SearchLib(wx.SearchCtrl):
	"""
	"""
	def __init__(self, *args, **kwargs):
		"""
		"""
		wx.SearchCtrl.__init__(self, *args, **kwargs)

		self.treeChildren = []
		self.treeCopy = None
		self.ShowCancelButton( True)
		self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
		self.Bind(wx.EVT_TEXT, self.OnSearch)

		self.SetToolTipString(_("Find model in the library depending its name."))

	def OnCancel(self, evt):
		"""
		"""
		self.Clear()

	def OnSearch(self, evt):
		"""
		"""
		mainW = evt.GetEventObject().GetTopLevelParent()
		mainW.OnSearch(evt)

#-------------------------------------------------------------------
class LeftNotebook(wx.Notebook, Observer):
	"""
	"""

	def __init__(self, *args, **kwargs):
		"""
		Notebook class that allows overriding and adding methods for the left pane of DEVSimPy

		@param parent: parent windows
		@param id: id
		@param pos: windows position
		@param size: windows size
		@param style: windows style
		@param name: windows name
		"""

		wx.Notebook.__init__(self, *args, **kwargs)

		### Define drop source
		#DropTarget.SOURCE = self

		### Add pages
		self.libPanel = wx.Panel(self, wx.ID_ANY)
		self.propPanel = wx.Panel(self, wx.ID_ANY)

		### selected model for libPanel managing
		self.selected_model = None

		### Creation de l'arbre des librairies
		self.tree = LibraryTree(self.libPanel, wx.ID_ANY, wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

		mainW = self.GetTopLevelParent()

		### lecture de ChargedDomainList dans .devsimpy
		cfg_domain_list = mainW.cfg.Read('ChargedDomainList')
		chargedDomainList = eval(cfg_domain_list) if cfg_domain_list else []

		self.tree.Populate(chargedDomainList)

		### Creation de l'arbre de recherche hide au depart (voir __do_layout)
		self.searchTree = LibraryTree(self.libPanel, wx.ID_ANY, wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_MULTIPLE|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

		### Creation de l'option de recherche dans tree
		self.search = SearchLib(self.libPanel, size=(200,-1), style = wx.TE_PROCESS_ENTER)

		self.tree.UpdateAll()

		self.__set_properties()
		self.__do_layout()
		self.__set_tips()

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__PageChanged)

	def __set_properties(self):
		"""
		"""
		imgList = wx.ImageList(16, 16)
		for img in [os.path.join(ICON_PATH_16_16,'db.png'), os.path.join(ICON_PATH_16_16,'properties.png'), os.path.join(ICON_PATH_16_16,'simulation.png')]:
			imgList.Add(wx.Image(img, wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.AssignImageList(imgList)

		self.libPanel.SetBackgroundColour(wx.WHITE)
		self.propPanel.SetBackgroundColour(wx.WHITE)
		self.searchTree.Hide()

	def GetTree(self):
		return self.tree

	def GetSearchTree(self):
		return self.searchTree

	def __set_tips(self):
		"""
		"""

		self.propToolTip =[_("No model selected.\nChoose a model to show in this panel its properties"),_("You can change the properties by editing the cellule")]
		self.propPanel.SetToolTipString(self.propToolTip[0])

	def __do_layout(self):
		"""
		"""
		libSizer = wx.BoxSizer(wx.VERTICAL)
		libSizer.Add(self.tree, 1 ,wx.EXPAND)
		libSizer.Add(self.searchTree, 1 ,wx.EXPAND)
		libSizer.Add(self.search, 0 ,wx.BOTTOM|wx.EXPAND)

		propSizer = wx.BoxSizer(wx.VERTICAL)
		propSizer.Add(self.defaultPropertiesPage(), 0, wx.ALL, 10)

		self.AddPage(self.libPanel, _("Library"), imageId=0)
		self.AddPage(self.propPanel, _("Properties"), imageId=1)

		self.libPanel.SetSizer(libSizer)
		self.libPanel.SetAutoLayout(True)

		self.propPanel.SetSizer(propSizer)
		self.propPanel.Layout()

	def __PageChanged(self, evt):
		"""
		"""
		if evt.GetSelection() == 1:
			pass
		evt.Skip()

	def Update(self, concret_subject=None):
		""" Update method that manages the panel propertie depending of the selected model in the canvas
		"""

		state = concret_subject.GetState()
		canvas = state['canvas']
		model = state['model']

		if self.GetSelection() == 1:
			if model:
				if model != self.selected_model:
					newContent = Container.AttributeEditor(self.propPanel, wx.ID_ANY, model, canvas)
					self.UpdatePropertiesPage(newContent)
					self.selected_model = model
					self.propPanel.SetToolTipString(self.propToolTip[1])
			else:
				self.UpdatePropertiesPage(self.defaultPropertiesPage())
				self.selected_model = None
				self.propPanel.SetToolTipString(self.propToolTip[0])

	def defaultPropertiesPage(self):
		"""
		"""

		propContent = wx.StaticText(self.propPanel, wx.ID_ANY, _("Properties panel"))
		sum_font = propContent.GetFont()
		sum_font.SetWeight(wx.BOLD)
		propContent.SetFont(sum_font)

		return propContent

	def UpdatePropertiesPage(self, panel=None):
		"""	Update the propPanel with teh new panel param of the model
		"""
		sizer = self.propPanel.GetSizer()
		sizer.DeleteWindows()
		sizer.Add(panel, 1, wx.EXPAND|wx.ALL)
		sizer.Layout()

#-------------------------------------------------------------------
class DiagramNotebook(wx.Notebook, Printable):
	"""
	"""

	def __init__(self, *args, **kwargs):
		"""
		Notebook class that allows overriding and adding methods.

		@param parent: parent windows
		@param id: id
		@param pos: windows position
		@param size: windows size
		@param style: windows style
		@param name: windows name
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Loading notebook diagram...\n')

		wx.Notebook.__init__(self, *args, **kwargs)
		Printable.__init__(self)

		# local copy
		self.parent = args[0]
		self.pages = []			# keeps track of pages

		### to propagate the dsp file path in __setstate__ of Block object
		self.current_dsp_file_path = ""
		
		#icon under tab
		imgList = wx.ImageList(16, 16)
		for img in [os.path.join(ICON_PATH_16_16,'network.png')]:
			imgList.Add(wx.Image(img, wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.AssignImageList(imgList)

		### binding
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__PageChanged)
		#self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.__OnPageChanging)
		self.Bind(wx.EVT_RIGHT_DOWN, self.__ShowMenu)
		self.Bind(wx.EVT_LEFT_DCLICK, self.__AddPage)

	def GetPages(self):
		return self.pages

	def __AddPage(self, event):
		self.AddEditPage(_("Diagram%d")%len(self.pages))

	def AddEditPage(self, title, defaultDiagram = None):
		"""
		Adds a new page for editing to the notebook and keeps track of it.

		@type title: string
		@param title: Title for a new page
		"""

		### title page list
		title_pages = map(lambda p: p.name, self.pages)

		### occurence of title in existing title pages
		c = title_pages.count(title)

		title = title+"(%d)"%c if c != 0 else title

		### new page
		newPage = Container.ShapeCanvas(self, wx.NewId(), name=title)

		### new diagram
		d = defaultDiagram or Container.Diagram()
		d.SetParent(newPage)

		### diagram and background newpage setting
		newPage.SetDiagram(d)

		### print canvas variable setting
		self.print_canvas = newPage
		self.print_size = self.GetSize()

		self.pages.append(newPage)
		self.AddPage(newPage, title, imageId=0)
		self.SetSelection(self.GetPageCount()-1)

	def GetPageByName(self, name = ''):
		"""
		"""
		for i in xrange(len(self.pages)):
			if name == self.GetPageText(i):
				return self.GetPage(i)
		return None

	#def __OnPageChanging(self, evt):
		#"""
		#"""
		#canvas = self.GetPage(evt.GetSelection())
		##canvas = self.GetPage(self.GetSelection())
		#### update the path of current dsp file
		#self.current_dsp_file_path = canvas.GetDiagram().last_name_saved
			
	def __PageChanged(self, evt):
		"""
		"""

		try:
			canvas = self.GetPage(self.GetSelection())
			self.print_canvas = canvas
			self.print_size = self.GetSize()

			### permet d'activer les redo et undo pour chaque page
			self.parent.tb.EnableTool(wx.ID_UNDO, not len(canvas.stockUndo) == 0)
			self.parent.tb.EnableTool(wx.ID_REDO, not len(canvas.stockRedo) == 0)

			canvas.deselect()
			canvas.Refresh()
			
		except Exception:
			pass
		evt.Skip()

	def __ShowMenu(self, evt):
		"""	Callback for the right click on a tab. Displays the menu.

			@type   evt: event
			@param  evt: Event Objet, None by default
		"""

		### mouse position
		pos = evt.GetPosition()
		### pointed page and flag
		page,flag = self.HitTest(pos)

		### if no where click
		if flag == wx.BK_HITTEST_NOWHERE:
			self.PopupMenu(Menu.DiagramNoTabPopupMenu(self), pos)
		### if tab has been clicked
		elif flag == wx.BK_HITTEST_ONLABEL:
			self.PopupMenu(Menu.DiagramTabPopupMenu(self), pos)
		else:
			pass

	def OnClearPage(self, evt):
		""" Clear page.

			@type evt: event
			@param  evt: Event Objet, None by default
		"""
		if self.GetPageCount() > 0:
			canvas = self.GetPage(self.GetSelection())
			diagram = canvas.diagram

			diagram.DeleteAllShapes()
			diagram.modified = True

			canvas.deselect()
			canvas.Refresh()

	def OnClosePage(self, evt):
		""" Close current page.

			@type evt: event
			@param  evt: Event Objet, None by default
		"""

		if self.GetPageCount() > 0:

			id = self.GetSelection()
			title = self.GetPageText(id)
			canvas = self.GetPage(id)
			diagram = canvas.GetDiagram()

			mainW =  self.GetTopLevelParent()

			if diagram.modify:
				dlg = wx.MessageDialog(self, _('%s\nSave changes to the current diagram ?')%(title), _('Save'), wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL |wx.ICON_QUESTION)
				val = dlg.ShowModal()
				if val == wx.ID_YES:
					mainW.OnSaveFile(evt)
				elif val == wx.ID_NO:
					self.DeleteBuiltinConstants()
					self.pages.remove(canvas)
					if not self.DeletePage(id):
						sys.stdout.write(_(" %s not deleted ! \n"%(title)))
				else:
					dlg.Destroy()
					return False

				dlg.Destroy()

			else:

				self.DeleteBuiltinConstants()
				self.pages.remove(canvas)

				if not self.DeletePage(id):
					sys.stdout.write(_("%s not deleted ! \n"%(title)))

			### effacement du notebook "property"
			nb1 = mainW.nb1
			activePage = nb1.GetSelection()
			### si la page active est celle de "properties" alors la met a jour et on reste dessus
			if activePage == 1:
				nb1.UpdatePropertiesPage(nb1.defaultPropertiesPage())

			return True

	def OnRenamePage(self, evt):
		"""Rename the title of notebook page.

		@type evt: event
		@param  evt: Event Objet, None by default
		"""
		selection = self.GetSelection()
		dlg = wx.TextEntryDialog(self, _("Enter a new name:"), _("Diagram Manager"))
		dlg.SetValue(self.GetPageText(selection))

		if dlg.ShowModal() == wx.ID_OK:
			txt = dlg.GetValue()
			self.SetPageText(selection,txt)

		dlg.Destroy()

	def OnDetachPage(self, evt):
		"""
		Detach the notebook page on frame.

		@type evt: event
		@param  evt: Event Objet, None by default
		"""

		mainW = self.GetTopLevelParent()
		selection = self.GetSelection()
		canvas = self.GetPage(selection)
		title = self.GetPageText(selection)

		frame = DetachedFrame(canvas, wx.ID_ANY, title, canvas.GetDiagram())
		frame.SetIcon(mainW.icon)
		frame.SetFocus()
		frame.Show()

	def DeleteBuiltinConstants(self):
		""" Delete builtin constants for the diagram.
		"""
		try:
			name = self.GetPageText(self.GetSelection())
			del __builtin__.__dict__[str(os.path.splitext(name)[0])]
		except Exception:
			pass
			#print "Constants builtin not delete for %s : %s"%(name, info)

# -------------------------------------------------------------------
class MainApplication(wx.Frame):
	""" DEVSimPy main application.
	"""

	def __init__(self, parent, id, title):
		""" Constructor.
		"""

		## Create Config file -------------------------------------------------------
		self.cfg = self.GetConfig()
		self.SetConfig(self.cfg)

		## Set i18n locales --------------------------------------------------------
		self.Seti18n()

		wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = DefineScreenSize(), style = wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)

		self.window = None
		self.otherWin = None
		self.replace = False
		self.stdioWin = None

		# icon setting
		self.icon = getIcon(DEVSIMPY_PNG)
		self.SetIcon(self.icon)

		# tell FrameManager to manage this frame
		self._mgr = wx.aui.AuiManager()
		self._mgr.SetManagedWindow(self)

		# Prevent TreeCtrl from displaying all items after destruction when True
		self.dying = False

		if 0:
			# This is another way to set Accelerators, in addition to
			# using the '\t<key>' syntax in the menu items.
			aTable = wx.AcceleratorTable([(wx.ACCEL_ALT,  ord('X'), exitID), (wx.ACCEL_CTRL, ord('H'), helpID),(wx.ACCEL_CTRL, ord('F'), findID),(wx.ACCEL_NORMAL, WXK_F3, findnextID)])
			self.SetAcceleratorTable(aTable)


		# for spash screen
		pub.sendMessage('object.added', 'Loading tree library...\n')
		pub.sendMessage('object.added', 'Loading search tree library...\n')

		# NoteBook
		self.nb1 = LeftNotebook(self, wx.ID_ANY, style = wx.CLIP_CHILDREN)
		self.tree = self.nb1.GetTree()
		self.searchTree = self.nb1.GetSearchTree()
		self.search = self.nb1.search

		self._mgr.AddPane(self.nb1, wx.aui.AuiPaneInfo().Name("nb1").Hide().Caption("Control").
                          FloatingSize(wx.Size(280, 400)).CloseButton(True).MaximizeButton(True))

		#------------------------------------------------------------------------------------------
		# Create a Notebook 2
		self.nb2 = DiagramNotebook(self, wx.ID_ANY, style = wx.CLIP_CHILDREN)

		### load .dsp or empty on empty diagram
		if len(sys.argv) >= 2:
			for arg in map(os.path.abspath, filter(lambda a :a.endswith('.dsp'), sys.argv[1:])):
				diagram = Container.Diagram()
				#diagram.last_name_saved = arg
				name = os.path.basename(arg)
				if not isinstance(diagram.LoadFile(arg), Exception):
					self.nb2.AddEditPage(os.path.splitext(name)[0], diagram)
		else:
			self.nb2.AddEditPage(_("Diagram%d"%Container.ShapeCanvas.ID))

		self._mgr.AddPane(self.nb2, wx.aui.AuiPaneInfo().Name("nb2").CenterPane().Hide())

		# Simulation panel
		self.panel3 = wx.Panel(self.nb1, wx.ID_ANY, style = wx.WANTS_CHARS)
		self.panel3.SetBackgroundColour(wx.NullColour)
		self.panel3.Hide()

		#status bar avant simulation :-)
		self.MakeStatusBar()

		# Shell panel
		self.panel4 = wx.Panel(self, wx.ID_ANY, style=wx.WANTS_CHARS)
		sizer4 = wx.BoxSizer(wx.VERTICAL)
		sizer4.Add(py.shell.Shell(self.panel4, introText=_("Welcome to DEVSimPy: The GUI Python DEVS Simulator")), 1, wx.EXPAND)
		self.panel4.SetSizer(sizer4)
		self.panel4.SetAutoLayout(True)

		self._mgr.AddPane(self.panel4, wx.aui.AuiPaneInfo().Name("shell").Hide().Caption("Shell").
										FloatingSize(wx.Size(280, 400)).CloseButton(True).MaximizeButton(True))

		self._mgr.GetPane("nb1").Show().Left().Layer(0).Row(0).Position(0).BestSize(wx.Size(280,-1)).MinSize(wx.Size(250,-1))
		self._mgr.GetPane("nb2").Show().Center().Layer(0).Row(1).Position(0)
		self._mgr.GetPane("shell").Bottom().Layer(0).Row(0).Position(0).BestSize(wx.Size(-1,100)).MinSize(wx.Size(-1,120))

		# "commit" all changes made to FrameManager (warning always before the MakeMenu)
		self._mgr.Update()

		self.MakeMenu()
		self.MakeToolBar()

		self.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)
		self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnDragInit, id = self.tree.GetId())
		#self.Bind(wx.EVT_TREE_END_DRAG, self.OnDragEnd, id = self.tree.GetId())
		self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnDragInit, id = self.searchTree.GetId())
		self.Bind(wx.EVT_IDLE, self.OnIdle)
		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

		self.Centre(wx.BOTH)
		self.Show()

	def GetVersion(self):
		return __version__

	def GetUserConfigDir(self):
		""" Return the standard location on this platform for application data.
		"""
		sp = wx.StandardPaths.Get()
		return sp.GetUserConfigDir()

	def GetConfig(self):
		""" Reads the config file for the application if it exists and return a configfile object for use later.
		"""
		return wx.FileConfig(localFilename = os.path.join(self.GetUserConfigDir(),'.devsimpy'))

	def WriteDefaultConfigFile(self, cfg):
		""" Write config file
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Writing .devsimpy settings file...\n')

		sys.stdout.write("Writing default .devsimpy settings file on %s directory..."%self.GetUserConfigDir())

		self.exportPathsList = []					# export path list
		self.openFileList = ['']*NB_OPENED_FILE		#number of last opened files
		self.language = 'default'						# default language
		self.perspectives = {}

		# verison of the main (fo compatibility of DEVSimPy)
		cfg.Write('version', str(__version__))
		# list des chemins des librairies à importer
		cfg.Write('exportPathsList', str([]))
		# list de l'unique domain par defaut: Basic
		cfg.Write('ChargedDomainList', str([]))
		# list des 5 derniers fichier ouvert
		cfg.Write('openFileList', str(eval("self.openFileList")))
		cfg.Write('language', "'%s'"%str(eval("self.language")))
		cfg.Write('plugins', str("[]"))
		cfg.Write('perspectives', str(eval("self.perspectives")))
		cfg.Write('builtin_dict', str(eval("__builtin__.__dict__")))

		sys.stdout.write("OK \n")

	def SetConfig(self, cfg):
		""" Set all config entry like language, external importpath, recent files...
		"""

		self.cfg = cfg

		### if .devsimpy config file already exist, load it
		if self.cfg.Exists('version'):

			### rewrite old configuration file
			rewrite = float(self.cfg.Read("version")) < float(self.GetVersion())

			if not rewrite:

				### for spash screen
				pub.sendMessage('object.added', 'Loading .devsimpy settings file...\n')

				sys.stdout.write("Load .devsimpy %s settings file from %s directory ... \n"%(self.GetVersion(),self.GetUserConfigDir()))
				### load external import path
				self.exportPathsList = filter(lambda path: os.path.isdir(path), eval(self.cfg.Read("exportPathsList")))
				### append external path to the sys module to futur import
				sys.path.extend(self.exportPathsList)

				### load recent files list
				self.openFileList = eval(self.cfg.Read("openFileList"))
				### update chargedDomainList
				chargedDomainList = filter(lambda path: path.startswith('http') or os.path.isdir(path), eval(self.cfg.Read('ChargedDomainList')))

				self.cfg.DeleteEntry('ChargedDomainList')
				self.cfg.Write('ChargedDomainList', str(eval('chargedDomainList')))
				### load language
				self.language = eval(self.cfg.Read("language"))
				### load any plugins from the list
				for plugin in eval(self.cfg.Read("plugins")):
					load_plugins(plugin)

				### load perspective profile
				self.perspectives = eval(self.cfg.Read("perspectives"))

				### restore the builtin dict (just for )
				try:
					D = eval(self.cfg.Read("builtin_dict"))
				except SyntaxError:
					sys.stdout.write('Error trying to read the builtin dictionary from config file. So, we load the default builtin \n')
					D = builtin_dict

				__builtin__.__dict__.update(D)

				sys.stdout.write("DEVSimPy is ready. \n")

			else:
				self.WriteDefaultConfigFile(self.cfg)

		### create a new defaut .devsimpy config file
		else:
			self.WriteDefaultConfigFile(self.cfg)


	def Seti18n(self):
		""" Set local setting.
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Loading locale configuration...\n')

		localedir = os.path.join(HOME_PATH, "locale")
		langid = wx.LANGUAGE_DEFAULT    # use OS default; or use LANGUAGE_FRENCH, etc.
		domain = "DEVSimPy"             # the translation file is messages.mo

		# Set locale for wxWidgets
		mylocale = wx.Locale(langid)
		mylocale.AddCatalogLookupPathPrefix(localedir)
		mylocale.AddCatalog(domain)

		# language config from .devsimpy file
		if self.language == 'en':
			translation = gettext.translation(domain, localedir, languages=['en']) # English
		elif self.language =='fr':
			translation = gettext.translation(domain, localedir, languages=['fr']) # French
		else:
			#installing os language by default
			translation = gettext.translation(domain, localedir, [mylocale.GetCanonicalName()], fallback = True)

		translation.install(unicode = True)


	def MakeStatusBar(self):
		""" Make status bar.
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Making status bar...\n')

		self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-5, -2, -1])

	def MakeMenu(self):
		""" Make main menu.
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Making Menu ...\n')

		self.menuBar = Menu.MainMenuBar(self)
		self.SetMenuBar(self.menuBar)

		### bind menu that require update on open and close event (forced to implement the binding here !)
		for menu,title in filter(lambda c : c[-1] in ('File', 'Fichier', 'Options'), self.menuBar.GetMenus()):
			self.Bind(wx.EVT_MENU_OPEN, self.menuBar.OnOpenMenu)
			#self.Bind(wx.EVT_MENU_CLOSE, self.menuBar.OnCloseMenu)

	def MakeToolBar(self):
		""" Make main tools bar.
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Making tools bar ...\n')

		self.tb = self.CreateToolBar( style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT, name = 'tb')
		self.tb.SetToolBitmapSize((25,25)) # juste for windows

		self.toggle_list = [wx.NewId(), wx.NewId(), wx.NewId()]

		currentPage = self.nb2.GetCurrentPage()

		### Tools List - IDs come from Menu.py file
		self.tools = [	self.tb.AddTool(wx.ID_NEW, wx.Bitmap(os.path.join(ICON_PATH,'new.png')), shortHelpString=_('New diagram (Ctrl+N)'),longHelpString=_('Create a new diagram in tab')),
						self.tb.AddTool(wx.ID_OPEN, wx.Bitmap(os.path.join(ICON_PATH,'open.png')), shortHelpString=_('Open File (Ctrl+O)'), longHelpString=_('Open an existing diagram')),
						self.tb.AddTool(wx.ID_PREVIEW_PRINT, wx.Bitmap(os.path.join(ICON_PATH,'print-preview.png')), shortHelpString=_('Print Preview (Ctrl+P)'), longHelpString=_('Print preview of current diagram')),
						self.tb.AddTool(wx.ID_SAVE, wx.Bitmap(os.path.join(ICON_PATH,'save.png')), shortHelpString=_('Save File (Ctrl+S)') , longHelpString=_('Save the current diagram'), clientData=currentPage),
						self.tb.AddTool(wx.ID_SAVEAS, wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')), shortHelpString=_('Save file as'), longHelpString=_('Save the diagram with an another name'), clientData=currentPage),
						self.tb.AddTool(wx.ID_UNDO, wx.Bitmap(os.path.join(ICON_PATH,'undo.png')),shortHelpString= _('Undo'), longHelpString=_('Click to glongHelpString=o back, hold to see history'), clientData=currentPage),
						self.tb.AddTool(wx.ID_REDO, wx.Bitmap(os.path.join(ICON_PATH,'redo.png')), shortHelpString=_('Redo'), longHelpString=_('Click to go forward, hold to see history'), clientData=currentPage),
						self.tb.AddTool(Menu.ID_ZOOMIN_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')), shortHelpString=_('Zoom'),longHelpString=_('Zoom +'), clientData=currentPage),
						self.tb.AddTool(Menu.ID_ZOOMOUT_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')), shortHelpString=_('UnZoom'),longHelpString=_('Zoom -'), clientData=currentPage),
						self.tb.AddTool(Menu.ID_UNZOOM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')), shortHelpString=_('AnnuleZoom'), longHelpString=_('Normal size'), clientData=currentPage),
						self.tb.AddTool(Menu.ID_PRIORITY_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'priority.png')), shortHelpString=_('Priority (F3)'),longHelpString= _('Define model activation priority')),
						self.tb.AddTool(Menu.ID_CHECK_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'check_master.png')), shortHelpString=_('Debugger (F4)'),longHelpString= _('Check devs models')),
						self.tb.AddTool(Menu.ID_SIM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')), shortHelpString=_('Simulation (F5)'), longHelpString=_('Simulate the diagram')),
						self.tb.AddTool(self.toggle_list[0], wx.Bitmap(os.path.join(ICON_PATH,'direct_connector.png')),shortHelpString= _('Direct'),longHelpString=_('Direct connector'), isToggle=True),
						self.tb.AddTool(self.toggle_list[1], wx.Bitmap(os.path.join(ICON_PATH,'square_connector.png')), shortHelpString=_('Square'), longHelpString=_('Square connector'), isToggle=True),
						self.tb.AddTool(self.toggle_list[2], wx.Bitmap(os.path.join(ICON_PATH,'linear_connector.png')), shortHelpString=_('Linear'), longHelpString=_('Linear connector'), isToggle=True)
					]

		self.tb.InsertSeparator(3)
		self.tb.InsertSeparator(8)
		self.tb.InsertSeparator(12)
		self.tb.InsertSeparator(16)

		### undo and redo button desabled
		self.tb.EnableTool(wx.ID_UNDO, False)
		self.tb.EnableTool(wx.ID_REDO, False)

		### default direct connector toogled
		self.tb.ToggleTool(self.toggle_list[0],1)

		### Binding
		self.Bind(wx.EVT_TOOL, self.OnNew, self.tools[0])
		self.Bind(wx.EVT_TOOL, self.OnOpenFile, self.tools[1])
		self.Bind(wx.EVT_TOOL, self.OnPrintPreview, self.tools[2])
		self.Bind(wx.EVT_TOOL, self.OnSaveFile, self.tools[3])
		self.Bind(wx.EVT_TOOL, self.OnSaveAsFile, self.tools[4])
		self.Bind(wx.EVT_TOOL, self.OnUndo, self.tools[5])
		self.Bind(wx.EVT_TOOL, self.OnRedo, self.tools[6])
		self.Bind(wx.EVT_TOOL, self.OnZoom, self.tools[7])
		self.Bind(wx.EVT_TOOL, self.OnUnZoom, self.tools[8])
		self.Bind(wx.EVT_TOOL, self.AnnuleZoom, self.tools[9])
		self.Bind(wx.EVT_TOOL, self.OnPriorityGUI, self.tools[10])
		self.Bind(wx.EVT_TOOL, self.OnCheck, self.tools[11])
		self.Bind(wx.EVT_TOOL, self.OnSimulation, self.tools[12])
		self.Bind(wx.EVT_TOOL, self.OnDirectConnector, self.tools[13])
		self.Bind(wx.EVT_TOOL, self.OnSquareConnector, self.tools[14])
		self.Bind(wx.EVT_TOOL, self.OnLinearConnector, self.tools[15])

		self.tb.Realize()

	def OnDirectConnector(self, event):
		"""
		"""
		toolbar = event.GetEventObject()
		Container.ShapeCanvas.CONNECTOR_TYPE = 'direct'
		for id in self.toggle_list:
			toolbar.ToggleTool(id,0)
		toolbar.ToggleTool(event.GetId(),1)

	def OnSquareConnector(self, event):
		"""
		"""
		toolbar = event.GetEventObject()
		Container.ShapeCanvas.CONNECTOR_TYPE = 'square'
		for id in self.toggle_list:
			toolbar.ToggleTool(id,0)
		toolbar.ToggleTool(event.GetId(),1)

	def OnLinearConnector(self, event):
		"""
		"""
		toolbar = event.GetEventObject()
		Container.ShapeCanvas.CONNECTOR_TYPE = 'linear'
		for id in self.toggle_list:
			toolbar.ToggleTool(id,0)
		toolbar.ToggleTool(event.GetId(),1)

	def OnPaneClose(self, event):
		""" Close pane has been invoked.
		"""
		caption = event.GetPane().caption
		if caption in ["Control"]:
			msg = _("You realy want close this pane?")
			dlg = wx.MessageDialog(self, msg, _("Question"),
									wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

			if dlg.ShowModal() in [wx.ID_NO, wx.ID_CANCEL]:
				event.Veto()
			dlg.Destroy()

	###
	def OnOpenRecentFile(self, event):
		""" Recent file has been invoked.
		"""

		id = event.GetId()
		#menu=event.GetEventObject()
		##on Linux, event.GetEventObject() returns a reference to the menu item,
		##while on Windows, event.GetEventObject() returns a reference to the main frame.
		menu = self.GetMenuBar().FindItemById(id).GetMenu()
		menuItem = menu.FindItemById(id)
		path = menuItem.GetItemLabel()
		name = os.path.basename(path)

		diagram = Container.Diagram()
		#diagram.last_name_saved = path
		open_file_result = diagram.LoadFile(path)

		if isinstance(open_file_result, Exception):
			wx.MessageBox(_('Error opening file.\nInfo : %s')%str(open_file_result), _('Error'), wx.OK | wx.ICON_ERROR)
		else:
			self.nb2.AddEditPage(os.path.splitext(name)[0], diagram)

	def OnDeleteRecentFiles(self, event):
		""" Delete the recent files list
		"""

		# update config file
		self.openFileList = ['']*NB_OPENED_FILE
		self.cfg.Write("openFileList", str(eval("self.openFileList")))
		self.cfg.Flush()

	def OnCreatePerspective(self, event):
		"""
		"""
		dlg = wx.TextEntryDialog(self, _("Enter a new name:"), _("Perspective Manager"), _("Perspective %d")%(len(self.perspectives)))
		if dlg.ShowModal() == wx.ID_OK:
			txt = dlg.GetValue()

			if len(self.perspectives) == 0:
				self.perspectivesmenu.AppendSeparator()

			self.perspectivesmenu.Append(wx.NewId(), txt)
			self.perspectives[txt] = self._mgr.SavePerspective()

	def OnRestorePerspective(self, event):
		"""
		"""
		id = event.GetId()
		item = self.GetMenuBar().FindItemById(id)
		self._mgr.LoadPerspective(self.perspectives[item.GetText()])

	def OnDeletePerspective(self, event):
		"""
		"""
		# delete all path items
		L = list(self.perspectivesmenu.GetMenuItems())
		for item in L[4:]:
			self.perspectivesmenu.RemoveItem(item)

		# update config file
		self.perspectives = {_("Default Startup"):self._mgr.SavePerspective()}
		self.cfg.Write("perspectives", str(eval("self.perspectives")))
		self.cfg.Flush()

	###
	def OnDragInit(self, event):

		# version avec arbre
		item = event.GetItem()
		tree = event.GetEventObject()

		### in posix-based we drag only item (in window is automatic)
		platform_sys = os.name
		flag = True
		if platform_sys == 'posix':
			flag = tree.IsSelected(item)

		# Dnd uniquement sur les derniers fils de l'arbre
		if not tree.ItemHasChildren(item) and flag:
			text = tree.GetItemPyData(event.GetItem())
			try:
				tdo = wx.PyTextDataObject(text)
				#tdo = wx.TextDataObject(text)
				tds = wx.DropSource(tree)
				tds.SetData(tdo)
				tds.DoDragDrop(True)
			except:
				sys.stderr.write(_("OnDragInit avorting \n"))

	###
	def OnIdle(self, event):
		if self.otherWin:
			self.otherWin.Raise()
			self.otherWin = None

	###
	def SaveLibraryProfile(self):
		""" Update config file with the librairies opened during the last use of DEVSimPy.
		"""
		# save in config file the opened last library directory
		L = self.tree.GetItemChildren(self.tree.root)
		self.cfg.Write("ChargedDomainList", str(filter(lambda k: self.tree.ItemDico[k] in L ,self.tree.ItemDico)))
		self.cfg.Flush()

		# save in config file the charged last external library directory
		#self.cfg.Write('exportPathsList', str(filter(lambda a: os.path.isdir(a), self.exportPathsList)))

	def SavePerspectiveProfile(self):
		""" Update the config file with the profile that are enabled during the last use of DEVSimPy
		"""
		# save in config file the last activated perspective
		self.cfg.Write("perspectives", str(self.perspectives))
		self.cfg.Flush()

	def SaveBuiltinDict(self):
		""" Save the specific builtin variable into the config file
		"""
		self.cfg.Write("builtin_dict", str(eval('dict((k, __builtin__.__dict__[k]) for k in builtin_dict)')))
		self.cfg.Flush()

	###
	def OnCloseWindow(self, event):
		""" Close icon has been pressed. Closing DEVSimPy.
		"""

		exit = False
		### for all pages, we invoke their OnClosePage function
		for i in xrange(self.nb2.GetPageCount()):
			self.nb2.ChangeSelection(0)
			if not self.nb2.OnClosePage(event):
				exit = True
				break

		if not exit:
			### Save process
			self.SaveLibraryProfile()
			self.SavePerspectiveProfile()
			self.SaveBuiltinDict()
			self._mgr.UnInit()
			del self._mgr
			self.Destroy()

			#win = wx.Window_FindFocus()
			#if win != None:
				## Note: you really have to use wx.wxEVT_KILL_FOCUS
				## instead of wx.EVT_KILL_FOCUS here:
				#win.Disconnect(-1, -1, wx.wxEVT_KILL_FOCUS)
			#self.Destroy()

	###
	def OnZoom(self, event):
		""" Zoom in icon has been pressed. Zoom in the current diagram.
		"""
		obj = event.GetEventObject()
		currentPage = obj.GetToolClientData(event.GetId()) if isinstance(obj.GetTopLevelParent(), DetachedFrame) else self.nb2.GetCurrentPage()
		currentPage.scalex=max(currentPage.scalex+.05,.3)
		currentPage.scaley=max(currentPage.scaley+.05,.3)
		currentPage.Refresh()

		self.statusbar.SetStatusText(_('Zoom In'))

	###
	def OnUnZoom(self, event):
		""" Zoom out icon has been pressed. Zoom out the current diagram.
		"""
		obj = event.GetEventObject()

		currentPage = obj.GetToolClientData(event.GetId()) if isinstance(obj.GetTopLevelParent(), DetachedFrame) else self.nb2.GetCurrentPage()
		currentPage.scalex=currentPage.scalex-.05
		currentPage.scaley=currentPage.scaley-.05
		currentPage.Refresh()

		self.statusbar.SetStatusText(_('Zoom Out'))

	###
	def AnnuleZoom(self, event):
		"""
		"""
		obj = event.GetEventObject()

		currentPage = obj.GetToolClientData(event.GetId()) if isinstance(obj.GetTopLevelParent(), DetachedFrame) else self.nb2.GetCurrentPage()
		currentPage.scalex = 1.0
		currentPage.scaley = 1.0
		currentPage.Refresh()

		self.statusbar.SetStatusText(_('No Zoom'))

	###
	def OnNew(self, event):
		""" New diagram has been invocked.
		"""
		self.nb2.AddEditPage("Diagram%d"%Container.ShapeCanvas.ID)
		return self.nb2.GetCurrentPage()

	###
	def OnOpenFile(self, event):
		""" Open file button has been pressed.
		"""

		wcd = _("DEVSimPy files (*.dsp)|*.dsp|YAML files (*.yaml)|*.yaml|All files (*)|*")
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH
		open_dlg = wx.FileDialog(self, message = _('Choose a file'), defaultDir = home, defaultFile = "", wildcard = wcd, style = wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)

		### path,diagram dictionary
		new_paths = {}

		# get the new path from open file dialogue
		if open_dlg.ShowModal() == wx.ID_OK:

			### for selected paths
			for path in open_dlg.GetPaths():
				diagram = Container.Diagram()
				#diagram.last_name_saved = path

				### adding path with assocaited diagram
				new_paths[os.path.normpath(path)] = diagram

				open_dlg.Destroy()

		# load the new_path file with ConnectionThread function
		if new_paths != {}:

			for path,diagram in new_paths.items():

				fileName = os.path.basename(path)
				open_file_result = diagram.LoadFile(path)

				if isinstance(open_file_result, Exception):
					wx.MessageBox(_('Error opening file : %s')%str(open_file_result), 'Error', wx.OK | wx.ICON_ERROR)
				else:
					self.nb2.AddEditPage(os.path.splitext(fileName)[0], diagram)

					# ajout dans la liste des derniers fichier ouvert (avec gestion de la suppression du dernier inserer)
					if path not in self.openFileList:
						self.openFileList.insert(0, path)
						del self.openFileList[-1]
						self.cfg.Write("openFileList", str(eval("self.openFileList")))
						self.cfg.Flush()

	###
	def OnPrint(self, event):
		""" Print current diagram
		"""
		self.nb2.print_canvas = self.nb2.GetCurrentPage()
		self.nb2.print_size = self.nb2.GetSize()
		self.nb2.PrintButton(event)

	def OnPrintPreview(self, event):
		""" Print preview of current diagram
		"""

		self.nb2.print_canvas = self.nb2.GetCurrentPage()
		self.nb2.print_size = self.nb2.GetSize()
		self.nb2.PrintPreview(event)

	def OnScreenCapture(self, event):
		""" Print preview of current diagram
		"""

		try:
			import gtk.gdk
		except ImportError:
			id = event.GetId()
			menu = self.GetMenuBar().FindItemById(id).GetMenu()
			menuItem = menu.FindItemById(id)
			### enable the menu
			menuItem.Enable(False)
			sys.stdout.write(_("Unable to import gtk module.\n"))
		else:
			### dfault filename
			fn = "screenshot.png"

			#### filename dialog request
			dlg = wx.TextEntryDialog(self, _('Enter a new name:'),_('ScreenShot Filename'), fn)
			if dlg.ShowModal() == wx.ID_OK:
				fn = dlg.GetValue()
			dlg.Destroy()

			### screenshot
			w = gtk.gdk.get_default_root_window()
			sz = w.get_size()
			### "The size of the window is %d x %d" % sz
			pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, sz[0], sz[1])
			pb = pb.get_from_drawable(w,w.get_colormap(), 0, 0, 0, 0, sz[0], sz[1])
			### saving
			if (pb != None):
				ext = os.path.splitext(fn)[-1][1:]
				pb.save(fn, ext)
				wx.MessageBox(_("Screenshot saved in %s.")%fn, _("Success"), wx.OK|wx.ICON_INFORMATION)
			else:
				wx.MessageBox(_("Unable to get the screenshot."), _("Error"), wx.OK|wx.ICON_ERROR)

	def OnUndo(self, event):
		""" Undo the diagram
		"""
		### get toolbar and clientData defined in AddTool
		toolbar = event.GetEventObject()
		currentPage = toolbar.GetToolClientData(event.GetId()) if isinstance(toolbar.GetParent(), DetachedFrame) else self.nb2.GetCurrentPage()

		### append the stockredo and active it
		currentPage.stockRedo.append(cPickle.dumps(obj=currentPage.GetDiagram(),protocol=0))
		toolbar.EnableTool(wx.ID_REDO, True)

		### change the current diagram with the last undo
		new_diagram = cPickle.loads(currentPage.stockUndo.pop())
		new_diagram.parent = currentPage
		currentPage.DiagramReplace(new_diagram)
		original_diagram = currentPage.GetDiagram()

		## if model is containerBlock, the grand parent is DetachedFrame and we could update the diagram withou update the original canvas
		if isinstance(original_diagram.GetGrandParent(), DetachedFrame):
			## update of all shapes in the original diagram
			original_diagram.shapes = new_diagram.shapes
		else:
			## refresh original canvas with new diagram
			original_canvas = original_diagram.parent
			original_canvas.DiagramReplace(new_diagram)

		### desable undo btn if the stockUndo list is empty
		toolbar.EnableTool(wx.ID_UNDO, not currentPage.stockUndo == [])

	def OnRedo(self, event):
		""" Redo the diagram
		"""

		toolbar = event.GetEventObject()
		currentPage = toolbar.GetToolClientData(event.GetId()) if isinstance(toolbar.GetParent(), DetachedFrame) else self.nb2.GetCurrentPage()

		### append the stockundo and active it
		currentPage.stockUndo.append(cPickle.dumps(obj=currentPage.GetDiagram(), protocol=0))
		toolbar.EnableTool(wx.ID_UNDO, True)

		### change the current canvas with the last undo
		new_diagram = cPickle.loads(currentPage.stockRedo.pop())
		new_diagram.parent = currentPage
		currentPage.DiagramReplace(new_diagram)
		original_diagram = currentPage.GetDiagram()

		## if model is containerBlock, the grand parent is DetachedFrame and we could update the diagram withou update the original canvas
		if isinstance(original_diagram.GetGrandParent(), DetachedFrame):
			## update of all shapes in the original diagram
			original_diagram.shapes = new_diagram.shapes
		else:
			## refresh original canvas with new diagram
			original_canvas = original_diagram.parent
			original_canvas.DiagramReplace(new_diagram)

		### desable undo btn if the stockRedo list is empty
		toolbar.EnableTool(wx.ID_REDO, not currentPage.stockRedo == [])

	###
	def OnSaveFile(self, event):
		""" Save file button has been pressed.
		"""

		obj = event.GetEventObject()

		if isinstance(obj, wx.ToolBar) and isinstance(obj.GetParent(), DetachedFrame):
			currentPage = obj.GetToolClientData(event.GetId())
		else:
			currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = currentPage.GetDiagram()

		### diagram preparation
		diagram.modify = False

		if diagram.last_name_saved:

			assert(os.path.isabs(diagram.last_name_saved))

			if Container.Diagram.SaveFile(diagram, diagram.last_name_saved):
				# Refresh canvas
				currentPage.Refresh()

				### enable save button on status bar
				self.tb.EnableTool(Menu.ID_SAVE, diagram.modify)

				#self.statusbar.SetStatusText(_('%s saved')%diagram.last_name_saved)
			else:
				wx.MessageBox( _('Error saving file.') ,_('Error'), wx.OK | wx.ICON_ERROR)
		else:
			self.OnSaveAsFile(event)

	###
	def OnSaveAsFile(self, event):
		""" Save file menu as has been selected.
		"""

		obj = event.GetEventObject()
		if isinstance(obj, wx.ToolBar) and isinstance(obj.GetParent(), DetachedFrame):
			currentPage = obj.GetToolClientData(event.GetId())
		else:
			currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = copy.deepcopy(currentPage.GetDiagram())

		### options building
		msg = "DEVSimPy files (*.dsp)|*.dsp|"
		if __builtin__.__dict__['YAML_IMPORT']:
			msg+="YAML files (*.yaml)|*.yaml|"
		msg+="XML files (*.xml)|*.xml|All files (*)|*)"

		wcd = _(msg)
		home = os.path.dirname(diagram.last_name_saved) or HOME_PATH
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)


		if save_dlg.ShowModal() == wx.ID_OK:
			path = os.path.normpath(save_dlg.GetPath())
			ext = os.path.splitext(path)[-1]
			file_name = save_dlg.GetFilename()
			wcd_i = save_dlg.GetFilterIndex()

			#ajoute de l'extention si abscente en fonction du wcd choisi (par defaut .dsp)
			if ext == '':
				if wcd_i == 0:
					path=''.join([path,'.dsp'])
				elif __builtin__.__dict__['YAML_IMPORT']:
					if wcd_i == 1:
						path=''.join([path,'.yaml'])
					elif wcd_i == 2:
						path=''.join([path,'.xml'])
				elif wcd_i == 1:
					path=''.join([path,'.xml'])

			### diagram preparation
			label = os.path.splitext(file_name)[0]
			diagram.LoadConstants(label)
			diagram.last_name_saved = path
			diagram.modify = False

			#sauvegarde dans le nouveau fichier
			if Container.Diagram.SaveFile(diagram, path):

				### if OnSaveAs invocked from DetahcedFrame, we update the title
				df = self.GetWindowByEvent(event)
				if isinstance(df, DetachedFrame):
					df.SetTitle(label)

				if diagram.last_name_saved == '':
					self.nb2.SetPageText(self.nb2.GetSelection(), label)
					currentPage.SetDiagram(diagram)
				else:
					self.nb2.AddEditPage(label, diagram)

				### enable save button on status bar
				self.tb.EnableTool(Menu.ID_SAVE, diagram.modify)
			else:
				wx.MessageBox(_('Error saving file.'), _('Error'), wx.OK | wx.ICON_ERROR)

		save_dlg.Destroy()

	def OnNewLib(self, event):
		dlg1 = wx.TextEntryDialog(self, _('Enter new directory name'), _('New Library'), _("New_lib"))
		if dlg1.ShowModal() == wx.ID_OK:
			dName = dlg1.GetValue()
			directory = os.path.join(DOMAIN_PATH, dName)
			if not os.path.exists(directory):
				os.makedirs(directory)
				f = open(os.path.join(directory,'__init__.py'),'w')
				f.write("__all__=[\n]")
				f.close()

				dlg2 = wx.MessageDialog(self, _('Do you want to import it?'), 'Question', wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
				if dlg2.ShowModal() == wx.ID_YES:

					progress_dlg = wx.ProgressDialog(_('Importing library'), _("Loading %s ...")%dName, parent=self, style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
					progress_dlg.Pulse()

					### ajout dans le sys.path si pas deja fait
					if directory not in sys.path:
						sys.path.append(directory)

					self.tree.InsertNewDomain(directory, self.tree.GetRootItem(), self.tree.GetSubDomain(directory, self.tree.GetDomainList(directory)).values()[0])

					progress_dlg.Destroy()
					wx.SafeYield()

					self.tree.SortChildren(self.tree.GetRootItem())

				dlg2.Destroy()

			else:
				wx.MessageBox(_('Directory already exist.\nChoose another name.'), _('Information'), wx.OK | wx.ICON_INFORMATION)

		dlg1.Destroy()

	###
	def OnImport(self, event):
		""" Import DEVSimPy library from Domain directory.
		"""

		# dialog pour l'importation de lib DEVSimPy (dans Domain) et le local
		dlg = ImportLibrary(self, wx.ID_ANY, _('Import Library'), size=(550,400))

		if (dlg.ShowModal() == wx.ID_OK):

			num = dlg._cb.GetItemCount()
			for index in xrange(num):
				label = dlg._cb.GetItemText(index)

				### met a jour le dico des elements selectionnes
				if dlg._cb.IsChecked(index) and not dlg._selectedItem.has_key(label):
					dlg._selectedItem.update({str(label):index})
				elif not dlg._cb.IsChecked(index) and dlg._selectedItem.has_key(label):
					del dlg._selectedItem[str(label)]

			for s in dlg._selectedItem:

				absdName = str(os.path.join(DOMAIN_PATH, s)) if s not in dlg._d else str(dlg._d[s])
				progress_dlg = wx.ProgressDialog(_('Importing library'),_("Loading %s ...")%s, parent=self, style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
				progress_dlg.Pulse()

				### ajout dans le sys.path si pas deja fait
				if absdName not in sys.path:
					sys.path.append(absdName)

				self.tree.InsertNewDomain(absdName, self.tree.GetRootItem(), self.tree.GetSubDomain(absdName, self.tree.GetDomainList(absdName)).values()[0])

				progress_dlg.Destroy()
				wx.SafeYield()

			self.tree.SortChildren(self.tree.GetRootItem())

		dlg.Destroy()

	###
	def OnSearch(self,evt):
		"""
		"""

		# text taper par l'utilisateur
		text = self.search.GetValue()

		if text != '':

			#list des mots trouves
			L = []

			#pour tout les parents qui n'ont pas de fils (bout de branche)
			for item in filter(lambda elem: not self.tree.ItemHasChildren(elem), self.tree.ItemDico.values()):
				path = self.tree.GetPyData(item)
				dirName = os.path.basename(path)

				### plus propre que la deuxieme solution (a tester dans le temps)
				if dirName.startswith(text):
					L.append(path)

			#masque l'arbre
			self.tree.Show(False)

			# Liste des domaines concernes
			if L != []:

				### on supprime l'ancien searchTree
				for item in self.searchTree.GetItemChildren(self.searchTree.GetRootItem()):
					self.searchTree.RemoveItem(item)

				### uniquify the list
				L = set(map(os.path.dirname, L))

				### construction du nouveau
				self.searchTree.Populate(L)

				### effacement des items qui ne correspondent pas
				for item in filter(lambda elem: not self.searchTree.ItemHasChildren(elem), copy.copy(self.searchTree.ItemDico).values()):
					path = self.searchTree.GetPyData(item)

					### si les path ne commence pas par le text entre par l'utilsiateur, on les supprime
					if not os.path.basename(path).startswith(text):
						self.searchTree.RemoveItem(item)

				self.searchTree.Show(True)
				self.nb1.libPanel.GetSizer().Layout()
				self.searchTree.ExpandAll()

			else:
				self.searchTree.Show(False)
		else:
			self.tree.Show(True)

	###
	def GetDiagramByWindow(self,window):
		""" Method that give the diagram present into the windows
		"""

		# la fenetre par laquelle a été invoqué l'action peut être principale (wx.App) ou detachée (DetachedFrame)
		if isinstance(window, DetachedFrame):
			return window.GetCanvas().GetDiagram()
		else:
			activePage = window.nb2.GetSelection()
			return window.nb2.GetPage(activePage).GetDiagram()
	###
	def GetWindowByEvent(self, event):
		""" Method that give the window instance from the event
		"""

		obj = event.GetEventObject()

		# si invocation de l'action depuis une ToolBar
		if isinstance(obj, (wx.ToolBar,wx.Frame)):
			window = obj.GetTopLevelParent()
		# si invocation depuis une Menu (pour le Show dans l'application principale)
		elif isinstance(obj, wx.Menu):
			window = wx.GetApp().GetTopWindow()
		else:
			sys.stdout.write(_("This option has not been implemented yet."))
			return False

		return window

	###
	def OnConstantsLoading(self, event):
		""" Method calling the AddConstants windows.
		"""

		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		diagram.OnAddConstants(event)


		###
	def OnInfoGUI(self, event):
		""" Method calling the PriorityGui.
		"""

		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		diagram.OnInformation(parent)

	###
	def OnPriorityGUI(self, event):
		""" Method calling the PriorityGui.
		"""

		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		diagram.OnPriority(parent)

	def OnCheck(self, event):
		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		return diagram.OnCheck(event)

	###
	def OnSimulation(self, event):
		""" Method calling the simulationGUI.
		"""

		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		return diagram.OnSimulation(event)

	##----------------------------------------------
	#def AdjustTab(self, evt):
		## clic sur simulation
		#if evt.GetSelection() == 2:
			#self.FindWindowByName("splitter").SetSashPosition(350)
		#elif evt.GetSelection() == 1:
		## clic sur property
			#self.FindWindowByName("splitter").SetSashPosition(350)
		## clic sur library
		#else:
			#self.FindWindowByName("splitter").SetSashPosition(350)
		#evt.Skip()

	###
	def OnShowControl(self, evt):
		""" Shell view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		if menu.IsChecked():
			self._mgr.GetPane("nb1").Show()
		else:
			self._mgr.GetPane("nb1").Hide()
		self._mgr.Update()

	###
	def OnShowShell(self, evt):
		""" Shell view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		if menu.IsChecked():
			self._mgr.GetPane("shell").Show()
		else:
			self._mgr.GetPane("shell").Hide()
		self._mgr.Update()

	###
	def OnShowSimulation(self, evt):
		""" Simulation view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		if menu.IsChecked():
			menu.Check(self.OnSimulation(evt))
		else:
			self.nb1.DeletePage(2)

	###
	def OnShowToolBar(self, evt):
		self.tb.Show(not self.tb.IsShown())

	###
	def OnFrench(self, event):
		self.cfg.Write("language", "'fr'")
		if wx.Platform == '__WXGTK__':
			dlg = wx.MessageDialog(self, _('You need to restart DEVSimPy to take effect.\n\nDo you want to restart now ?'), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_YES:
				wx.CallAfter(self.OnRestart())
		else:
			wx.MessageBox(_('You need to restart DEVSimPy to take effect.'), _('Info'), wx.OK|wx.ICON_INFORMATION)
	###
	def OnEnglish(self, event):
		self.cfg.Write("language", "'en'")

		if wx.Platform == '__WXGTK__':
			dlg = wx.MessageDialog(self, _('You need to restart DEVSimPy to take effect.\n\nDo you want to restart now ?'), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_YES:
				wx.CallAfter(self.OnRestart())
		else:
			wx.MessageBox(_('You need to restart DEVSimPy to take effect.'), _('Info'), wx.OK|wx.ICON_INFORMATION)
	###
	def OnAdvancedSettings(self, event):
		frame = PreferencesGUI(self,_("Preferences Manager"))
		frame.Show()
	###
	@BuzyCursorNotification
	def OnProfiling(self, event):
		""" Simulation profiling for fn file
		"""

		### find the prof file name
		i = event.GetId()
		menu = event.GetEventObject()
		fn = menu.FindItemById(i).GetLabel()
		prof_file_path = os.path.join(gettempdir(),fn)

		### list of item in single choice dialogue
		choices = [_('Embedded in DEVSimPy')]

		### editor of profiling software
		try :
			kcachegrind = which('kcachegrind')
			choices.append('kcachegrind')
		except Exception:
			kcachegrind = False
		try:
			kprof = which('kprof')
			choices.append('kprof')
		except Exception:
			kprof = False
		try:
			converter = which('hotshot2calltree')
		except Exception:
			converter = False

		choices.append(_('Other...'))

		dlg = wx.SingleChoiceDialog(self, _('What profiling software are you using?'), _('Single Choice'), choices)
		if dlg.ShowModal() == wx.ID_OK:
			response = dlg.GetStringSelection()
			if response == 'kcachegrind':
				dlg.Destroy()

				if converter:
					### cache grind file name that will be generated
					cachegrind_fn = os.path.join(gettempdir(), "%s%s"%(fn[:-len('.prof')],'.cachegrind'))
					### transform profile file for cachegrind
					os.system("%s %s %s %s"%(converter,"-o", cachegrind_fn, prof_file_path))

					self.LoadCachegrindFile(cachegrind_fn)
				else:
					wx.MessageBox(_("Hotshot converter (hotshot2calltree) not found"), _('Error'), wx.OK|wx.ICON_ERROR)

			elif response == 'kprof':
				dlg.Destroy()
				self.LoadProfFileFromKProf(prof_file_path)
			elif response == _('Embedded in DEVSimPy'):
				dlg.Destroy()
				output = self.LoadProfFile(prof_file_path)
				d = wx.lib.dialogs.ScrolledMessageDialog(self, output, _("Statistic of profiling"))
				d.CenterOnParent(wx.BOTH)
				d.ShowModal()
			else:
				pass

	@staticmethod
	def LoadCachegrindFile(cachegrind_fn):
		### lauch  kcachegrid
		os.system("%s %s %s"%('kcachegrind',cachegrind_fn,"&"))

	@staticmethod
	def LoadProfFileFromKProf(prof_file_path):
		### lauch  kprof
		os.system("%s %s %s"%('kprof',prof_file_path,"&"))

	@staticmethod
	@redirectStdout
	def LoadProfFile(prof_file_path):
		### lauch embedded prof editor
		stats = hotshot.stats.load(prof_file_path)
		stats.strip_dirs()
		stats.sort_stats('time', 'calls')
		text = stats.print_stats(100)

	def OnDeleteProfiles(self, event):
		dlg = wx.MessageDialog(self, _('Do you realy want to delete all files ?'), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			tmp_dir = gettempdir()
			for fn in filter(lambda f: f.endswith(('.prof','.cachegrind')), os.listdir(tmp_dir)):
				os.remove(os.path.join(tmp_dir,fn))

	###
	def OnRestart(self):
		""" Restart application.
		"""

		# permanently writes all changes (otherwise, they’re only written from object’s destructor)
		self.cfg.Flush()

		# restart application on the same process (erase)
		program = "python"
		arguments = ["devsimpy.py"]
		os.execvp(program, (program,) +  tuple(arguments))

	def OnHelp(self, event):
		""" Shows the DEVSimPy help file. """

		## language config from .devsimpy file
		if self.language == 'default':
			lang = 'en'
		else:
			lang = eval('self.language')

		filename = os.path.join('doc','html', lang, 'Help.zip')

		wx.FileSystem.AddHandler(wx.ZipFSHandler())     # add the Zip filesystem (only before HtmlHelpControler instance)

		self.help = wx.html.HtmlHelpController()

		if not self.help.AddBook(filename, True):
			wx.MessageBox(_("Unable to open: %s")%filename, _("Error"), wx.OK|wx.ICON_ERROR)
		else:
			self.help.Display(os.path.join('html','toc.html'))

	def OnAPI(self, event):
		""" Shows the DEVSimPy API help file. """

		#webbrowser.open_new(opj(self.installDir + "/docs/api/index.html"))
		wx.MessageBox(_("This option has not been implemented yet."), _('Info'), wx.OK|wx.ICON_INFORMATION)

	@BuzyCursorNotification
	def OnAbout(self, event):
		""" About menu has been pressed.
		"""

		description = _("""DEVSimPy is an advanced wxPython framework for the modeling and simulation of systems based on the DEVS formalism.
Features include powerful built-in editor, advanced modeling approach, powerful discrete event simulation algorithm,
import/export DEVS components library and more.""")

		licence =_( """DEVSimPy is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later version.

DEVSimPy is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. You should have received a copy of
the GNU General Public License along with File Hunter; if not, write to
the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA""")

		info = wx.AboutDialogInfo()

		info.SetIcon(getIcon(SPLASH_PNG))
		info.SetName('DEVSimPy')
		info.SetVersion(self.GetVersion())
		info.SetDescription(description)
		info.SetCopyright(_('(C) 2011 oct SPE Laboratory'))
		info.SetWebSite('http://www.spe.univ-corse.fr')
		info.SetLicence(licence)
		info.AddDeveloper(_('L. Capocchi and SPE team.'))
		info.AddDocWriter(_('L. Capocchi and SPE team.'))
		info.AddArtist(_('L. Capocchi and SPE team.'))
		info.AddTranslator(_('L. Capocchi and SPE team.'))

		wx.AboutBox(info)

	@BuzyCursorNotification
	def OnContact(self, event):
		""" Launches the mail program to contact the DEVSimPy author. """

		mails_list = GetMails(__authors__)
		cc = ""
		mailto = mails_list[0]

		for mail in mails_list[1:]:
			cc+=',%s'%mail

		webbrowser.open_new("mailto:%s?subject=%s&cc=%s"%(mailto,_("Comments On DEVSimPy"),cc))

##-------------------------------------------------------------------
class AdvancedSplashScreen(AdvancedSplash):
	""" A splash screen class, with a shaped frame.
	"""

	# # These Are Used To Declare If The AdvancedSplash Should Be Destroyed After The
	# # Timeout Or Not
	AS_TIMEOUT = 1
	AS_NOTIMEOUT = 2
	#
	# # These Flags Are Used To Position AdvancedSplash Correctly On Screen
	AS_CENTER_ON_SCREEN = 4
	AS_CENTER_ON_PARENT = 8
	AS_NO_CENTER = 16
	#
	# # This Option Allow To Mask A Colour In The Input Bitmap
	AS_SHADOW_BITMAP = 32

	###
	def __init__(self, app):
		""" A splash screen constructor

		**Parameters:**

		* `app`: the current wxPython app.
		"""

		splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
		splashBmp = wx.Image(SPLASH_PNG).ConvertToBitmap()
		splashDuration = 2000

		if old:
			AdvancedSplash.__init__(self, splashBmp, splashStyle, splashDuration, None)
			self.CreateStatusBar()
		else:
			style=wx.NO_BORDER|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP|wx.FRAME_SHAPED
			extrastyle = AdvancedSplashScreen.AS_TIMEOUT|AdvancedSplashScreen.AS_CENTER_ON_SCREEN #| AdvancedSplashScreen.AS_SHADOW_BITMAP
			shadow = wx.WHITE

			### TODO: test sous ex de l'extrastyle
			if wx.Platform == '__WXMAC__':
				AdvancedSplash.__init__(self, bitmap=splashBmp, timeout=splashDuration, style=style, shadowcolour=wx.WHITE, parent=None)
			else:
				if wx.VERSION_STRING >= '2.8.11':
					AdvancedSplash.__init__(self, bitmap=splashBmp, timeout=splashDuration, style=style, agwStyle=extrastyle, shadowcolour=shadow, parent=None)
				else:
					AdvancedSplash.__init__(self, bitmap=splashBmp, timeout=splashDuration, style=style, extrastyle=extrastyle, shadowcolour=shadow, parent=None)

			w = splashBmp.GetWidth()
			h = splashBmp.GetHeight()

			# Set The AdvancedSplash Size To The Bitmap Size
			self.SetSize((w, h))

			self.SetTextPosition((30, h-20))
			self.SetTextFont(wx.Font(9, wx.SWISS, wx.ITALIC, wx.NORMAL, False))
			self.SetTextColour("#797373")

		wx.EVT_CLOSE(self, self.OnClose)
		self.fc = wx.FutureCall(500, self.ShowMain)
		self.app = app

		# for splash info
		try:
			pub.subscribe(self.OnObjectAdded, 'object.added')
		except TypeError:
			pub.subscribe(self.OnObjectAdded, data='object.added')

	def OnObjectAdded(self, message):
		# data passed with your message is put in message.data.
		# Any object can be passed to subscribers this way.

		data = message.data

		try:
			self.SetText(data)
		### wx <= 2.8
		except AttributeError:
			self.PushStatusText(data)

		with open(LOG_FILE, 'a') as f:
			f.write("%s - %s"%(time.strftime("%Y-%m-%d %H:%M:%S"), data))

	def OnClose(self, event):
		""" Handles the wx.EVT_CLOSE event for SplashScreen. """

		# Make sure the default handler runs too so this window gets
		# destroyed
		event.Skip()
		self.Hide()

		# if the timer is still running then go ahead and show the
		# main frame now
		if self.fc.IsRunning():
		# Stop the wx.FutureCall timer
			self.fc.Stop()
			self.ShowMain()


	def ShowMain(self):
		""" Shows the main application (DEVSimPy). """

		self.app.frame = MainApplication(None, wx.ID_ANY, 'DEVSimPy - Version %s'%__version__)

		# recuperation dans un attribut de stdio qui est invisible pour l'instant
		self.app.frame.stdioWin = self.app.stdioWin
		wx.App.SetTopWindow(self.app, self.app.frame)

		if self.fc.IsRunning():
		# Stop the splash screen timer and close it
			self.Raise()

#------------------------------------------------------------------------
class LogFrame(wx.Frame):
	""" Log Frame class
	"""

	def __init__(self, parent, id, title, position, size):
		""" constructor
		"""

		wx.Frame.__init__(self, parent, id, title, position, size, style=wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP)
		self.Bind(wx.EVT_CLOSE, self.OnClose)


	def OnClose(self, event):
		"""	Handles the wx.EVT_CLOSE event
		"""
		self.Show(False)

#------------------------------------------------------------------------------
class PyOnDemandOutputWindow(threading.Thread):
	"""
	A class that can be used for redirecting Python's stdout and
	stderr streams.  It will do nothing until something is wrriten to
	the stream at which point it will create a Frame with a text area
	and write the text there.
	"""
	def __init__(self, title = "wxPython: stdout/stderr"):
		threading.Thread.__init__(self)
		self.frame  = None
		self.title  = title
		self.pos    = wx.DefaultPosition
		self.size   = (450, 300)
		self.parent = None
		self.st = None

	def SetParent(self, parent):
		"""Set the window to be used as the popup Frame's parent."""
		self.parent = parent

	def CreateOutputWindow(self, st):
		self.st = st
		self.start()
		#self.frame.Show(True)

	def run(self):
		self.frame = LogFrame(self.parent, wx.ID_ANY, self.title, self.pos, self.size)
		self.text  = wx.TextCtrl(self.frame, wx.ID_ANY, "", style = wx.TE_MULTILINE|wx.HSCROLL)
		self.text.AppendText(self.st)

	# These methods provide the file-like output behaviour.
	def write(self, text):
		"""
		If not called in the context of the gui thread then uses
		CallAfter to do the work there.
		"""
		if self.frame is None:
			if not wx.Thread_IsMain():
				wx.CallAfter(self.CreateOutputWindow, text)
			else:
				self.CreateOutputWindow(text)
		else:
			if not wx.Thread_IsMain():
				wx.CallAfter(self.text.AppendText, text)
			else:
				self.text.AppendText(text)

	def close(self):
		if self.frame is not None:
			wx.CallAfter(self.frame.Close)

	def flush(self):
		pass

#-------------------------------------------------------------------
class DEVSimPyApp(wx.App):

	outputWindowClass = PyOnDemandOutputWindow

	def __init__(self, redirect=False, filename=None):
		wx.App.__init__(self,redirect, filename)

		# make sure we can create a GUI
		if not self.IsDisplayAvailable():

			if wx.Platform == '__WXMAC__':
				msg = """This program needs access to the screen.
				Please run with 'pythonw', not 'python', and only when you are logged
				in on the main display of your Mac."""

			elif wx.Platform == '__WXGTK__':
				msg ="Unable to access the X Display, is $DISPLAY set properly?"

			else:
				msg = 'Unable to create GUI'
				# TODO: more description is needed for wxMSW...

			raise SystemExit(msg)

		# Save and redirect the stdio to a window?
		self.stdioWin = None
		self.saveStdio = (sys.stdout, sys.stderr)
		if redirect:
			self.RedirectStdio(filename)

	def SetTopWindow(self, frame):
		"""Set the \"main\" top level window"""
		if self.stdioWin:
			self.stdioWin.SetParent(frame)
		wx.App.SetTopWindow(self, frame)

	def RedirectStdio(self, filename=None):
		"""Redirect sys.stdout and sys.stderr to a file or a popup window."""
		if filename:
			sys.stdout = sys.stderr = open(filename, 'a')
		else:
			# ici on cree la fenetre !
			DEVSimPyApp.outputWindowClass.parent=self
			self.stdioWin = DEVSimPyApp.outputWindowClass('DEVSimPy Output')
			sys.stdout = sys.stderr = self.stdioWin

	def RestoreStdio(self):
		try:
			sys.stdout, sys.stderr = self.saveStdio
		except:
			pass

	def MainLoop(self):
		"""Execute the main GUI event loop"""
		wx.App.MainLoop(self)
		self.RestoreStdio()

	def Destroy(self):
		self.this.own(False)
		wx.App.Destroy(self)

	def __del__(self, destroy = wx.App.__del__):
		self.RestoreStdio()  # Just in case the MainLoop was overridden
		destroy(self)

	def SetOutputWindowAttributes(self, title=None, pos=None, size=None):
		"""
		Set the title, position and/or size of the output window if
		the stdio has been redirected.  This should be called before
		any output would cause the output window to be created.
		"""
		if self.stdioWin:
			if title is not None:
				self.stdioWin.title = title
			if pos is not None:
				self.stdioWin.pos = pos
			if size is not None:
				self.stdioWin.size = size

	def OnInit(self):
		"""
		Create and show the splash screen.  It will then create and show
		the main frame when it is time to do so.
		"""

		#wx.InitAllImageHandlers()

		# Set up the exception handler...
		sys.excepthook = ExceptionHook

		# start our application with splash
		splash = AdvancedSplashScreen(self)
		splash.Show()

		return True

#-------------------------------------------------------------------
if __name__ == '__main__':

	### python devsimpy.py -c|-clean in order to delete the config file
	if len(sys.argv) >= 2 and sys.argv[1] in ('-c, -clean'):
		sp = wx.StandardPaths.Get()
		config_file = os.path.join(sp.GetUserConfigDir(),'.devsimpy')
		r = raw_input('Are you sure to delete DEVSimPy config file ? (Y,N):')
		if r in ('Y','y','yes','Yes' ):
			os.remove(config_file)
			sys.stdout.write('%s has been deleted !\n'%config_file)

		elif r in ('N','n','no', 'No'):
			pass
		else:
			pass
		sys.exit()
	elif len(sys.argv) >= 2 and sys.argv[1] in ('-m'):
		##########################################
		import compileall
		import re

		compileall.compile_dir('.', maxlevels=20, rx=re.compile(r'/\.svn'))
		###########################################
		sys.stdout.write('all pyc has been deleted !\n')

	### python devsimpy.py -d|-debug in order to define log file
	elif len(sys.argv) >= 2 and sys.argv[1] in ('-d, -debug'):
		LOG_FILE='log.txt'
		sys.stdout.write('Writing %s file. \n'%LOG_FILE)
	### python devsimpy.py -h|-help in order to invoke command hepler
	elif len(sys.argv) >= 2 and sys.argv[1] in ('-h, -help'):
		sys.stdout.write('Welcome to the DEVsimpy helper. \n')
		sys.stdout.write('\t To execute DEVSimPy GUI: python devsimpy.py \n')
		sys.stdout.write('\t To execute DEVSimPy cleaner: python devsimpy.py -c|-clean\n')
		sys.stdout.write('\t To execute DEVSimPy writing log.txt file: python devsimpy.py -d|-debug\n')
		sys.stdout.write('\t To execute DEVSimPy in no GUI mode: python devsimpy.py -ng|-nogui\n')
		sys.stdout.write('Authors: L. capocchi (capocchi@univ-corse.fr)\n')
		sys.exit()
	### python devsimpy.py -ng|-nogui yourfile.dsp -> sans interface graphique
	elif not __builtin__.__dict__['GUI_FLAG']:

		if sys.argv[1] == '-ng' or sys.argv[1] == '-nogui':
			if len(sys.argv) == 3:

				### check dsp filename
				filename = sys.argv[2]
				if not os.path.exists(filename):
					sys.stderr.write('Error : .dsp not exist !\n')
					sys.exit()

				### launch simulation
				makeSimulation(filename,time = 10.0)

			elif len(sys.argv) == 4:

				### check dsp filename
				filename = sys.argv[2]
				if not os.path.exists(filename):
					sys.stderr.write('Error : .dsp not exist !\n')
					sys.exit()

				### check time
				time = sys.argv[3]
				if not IsAllDigits(str(time)):
					sys.stderr.write('Error : time should be a number!\n')
					sys.exit()

				### launch simulation
				makeSimulation(filename,time)
			else:
				sys.stderr.write('Error : Unspecified .dsp file !\n')
				sys.stdout.write('USAGE : python devsimpy.py -ng|-nogui yourfile.dsp\n')
				sys.stdout.write('\t To execute DEVSimPy nogui with timer: python devsimpy.py -ng|-nogui yourfile.dsp 15.0 \n')
				sys.exit()

		elif sys.argv[1] == '-js' or sys.argv[1] == '-javascript':
			if len(sys.argv) == 3:

				### check dsp filename
				filenameJS = sys.argv[2]
				if not os.path.exists(filenameJS):
					sys.stderr.write('Error : .dsp not exist !\n')
					sys.exit()

				### launch simulation
				makeJS(filenameJS)
			else:
				sys.stderr.write('Error : Unspecified .dsp file !\n')
				sys.stdout.write('USAGE : python devsimpy.py -js|-javascript yourfile.dsp\n')
				sys.exit()
	else:
		pass
	## si redirect=True et filename=None alors redirection dans une fenetre
	## si redirect=True et filename="fichier" alors redirection dans un fichier
	## si redirect=False redirection dans la console
	if __builtin__.__dict__['GUI_FLAG']:
		app = DEVSimPyApp(redirect = False, filename = None)
		app.MainLoop()
	else:
		app = wx.App()
		app.MainLoop()
