#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LibrayTree.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software 
#                     --------------------------------
#                            Copyright (c) 2013
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 3.0                                      last modified:  08/01/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
import os
import copy
import inspect
import zipfile
import urlparse
import httplib
import urllib
import time
import wx

if wx.VERSION_STRING < '2.9':  # to send event
	from wx.lib.pubsub import Publisher as pub
else:
	from wx.lib.pubsub import pub

import GUI.Menu as Menu
import GUI.ShapeCanvas as ShapeCanvas
import GUI.ZipManager as ZipManager

import Core.Utilities.ConnectionThread as ConnectionThread
import Core.Utilities.Utilities as Utilities
import Core.Utilities.ReloadModule as ReloadModule
import Core.Components.Decorators as Decorators
import Core.Components.Container as Container
import Core.Components.Components as Components
import Core.DomainInterface.DomainBehavior as DomainBehavior

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

		isz = (16, 16)
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

		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftClick)
		self.Bind(wx.EVT_MOTION, self.OnMotion)


	def Populate(self, chargedDomainList=None):
		""" Populate the Tree from a list of domain path.
		"""
		if not chargedDomainList: chargedDomainList = []

		assert self.root is not None, _("Missing root")

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
				if domain_list:
					tip = '\n'.join(domain_list)
				elif model_list:
					tip = '\n'.join(model_list)
				else:
					tip = ""
			### is last item
			else:
				module = Components.BlockFactory.GetModule(path)
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
				m = GetBlockModel(canvas=canvas,
								  x=40,
								  y=40,
								  label=self.GetItemText(item_selected),
								  id=0,
								  inputs=1,
								  outputs=1,
								  python_file=path,
								  model_file="")
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

		# si pas d'item selectionnner, le evt.Skip a la fin propage l'evenement vers OnRightItemClick			
		if not self.GetSelections():
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
		ShapeCanvas.ShapeCanvas.StartWizard(self)

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
			c.request('GET', o.path + '/__init__.py')

			r = c.getresponse()

			code = r.read()
			if r.status == 200:
				exec code
				#return filter(lambda d: d not in LibraryTree.EXCLUDE_DOMAIN, __all__)
				return __all__
			else:
				return []

		else:
			return [f for f in os.listdir(dName) if os.path.isdir(os.path.join(dName, f)) and f not in LibraryTree.EXCLUDE_DOMAIN] if os.path.isdir( dName) else []

	###
	def GetItemChildren(self, item, recursively=False):
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
				c.request('GET', o.path + '/__init__.py')

				r = c.getresponse()
				code = r.read()

				if r.status == 200:
					exec code
					tmp = filter(lambda s: s.replace('\n', '').replace('\t', '').replace(',', '').replace('"', "").replace('\'', "").strip(), __all__)
					### test if the content of __init__.py file is python file (isfile equivalent)
					py_file_list = [s for s in tmp if 'python' in urllib.urlopen(dName + '/' + s + '.py').info().type]

				else:
					py_file_list = []

				return py_file_list
			else:
				try:
					name_list = Utilities.getFileListFromInit(os.path.join(dName, '__init__.py'))
					py_file_list = []
					for s in name_list:
						python_file = os.path.join(dName, s + '.py')
						### test if tmp is only composed by python file (case of the user write into the __init__.py file directory name is possible ! then we delete the directory names)
						if os.path.isfile(python_file):

							cls = Components.GetClass(python_file)

							if cls is not None and not isinstance(cls, tuple):
								### only model that herite from DomainBehavior is shown in lib
								if issubclass(cls, DomainBehavior.DomainBehavior):
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
		devsimpy_file_list = [f for f in os.listdir(dName) if os.path.isfile(os.path.join(dName, f)) and (f[:2] != '__') and ( f.endswith(LibraryTree.EXT_LIB_FILE))]

		return py_file_list + devsimpy_file_list

	###
	def InsertNewDomain(self, dName, parent, L=None):
		""" Recurcive function that insert new Domain on library panel.
		"""
		if not L: L = []

		### au depard seulement pour le parent de plus haut niveau (comme PowerSystem)
		if dName not in self.ItemDico.keys():
			label = os.path.basename(dName) if not dName.startswith('http') else filter(lambda a: a != '', dName.split('/'))[-1]
			id = self.InsertItemBefore(parent, 0, label)
			self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
			self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)
			self.SetItemBold(id)
			self.ItemDico.update({dName: id})
			self.SetPyData(id, dName)

		### fin de la recursion
		if not L:
			return
		else:
			item = L.pop(0)
			assert not isinstance(item, unicode), _("Warning unicode item !")
			### element a faire remonter dans la liste
			D = []
			### si le fils est un modele construit dans DEVSimPy
			if isinstance(item, str):

				### le parent est recupere dans le Dico
				parent = self.ItemDico[dName]
				assert parent is not None

				### path correspondant au parent
				parentPath = self.GetPyData(parent)

				### remplacement des espaces
				item = item.strip()

				come_from_net = parentPath.startswith('http')

				### suppression de l'extention su .cmd (model atomic lue a partir de __init__ donc pas d'extention)
				if item.endswith('.cmd'):
					### gestion de l'importation de module (.py) associe au .cmd si le fichier .py n'a jamais ete decompressse (pour edition par exemple)
					if not come_from_net:
						path = os.path.join(parentPath, item)
						zf = ZipManager.Zip(path)
						module = zf.GetModule()
						image_file = zf.GetImage()
					else:
						path = parentPath + '/' + item + '.py'
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
					### gestion de l'importation de module (.py) associe au .amd si le fichier .py n'a jamais ete decompressse (pour edition par exemple)
					if not come_from_net:
						path = os.path.join(parentPath, item)
						zf = ZipManager.Zip(path)
						module = zf.GetModule()
						image_file = zf.GetImage()
					else:
						path = parentPath + '/' + item + '.py'
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

					path = os.path.join(parentPath, item + '.py') if not parentPath.startswith('http') else parentPath + '/' + item + '.py'

					info = Container.CheckClass(path)

					error = isinstance(info, tuple)
					img = self.not_importedidx if error else self.pythonfileidx
					### insertion dans le tree
					id = self.InsertItemBefore(parent, 0, item, img, img)
					self.SetPyData(id, path)

				### error info back propagation
				if error:
					while parent:
						self.SetItemImage(parent, self.not_importedidx, wx.TreeItemIcon_Normal)
						### next parent item
						parent = self.GetItemParent(parent)

				### insertion des donnees dans l'item et gestion du ItemDico
				self.ItemDico.update({os.path.join(parentPath, item, ): id})

			### si le fils est un sous repertoire contenant au moins un fichier (all dans __init__.py different de [])
			elif isinstance(item, dict) and item.values() != [[]]:

				### nom a inserer dans l'arbe
				dName = os.path.basename(item.keys()[0])

				### nouveau parent	
				parent = self.ItemDico[os.path.dirname(item.keys()[0])] if not dName.startswith('http') else self.ItemDico[item.keys()[0].replace('/' + dName, '')]

				assert (parent is not None)
				### insertion de fName sous parent
				id = self.InsertItemBefore(parent, 0, dName)

				self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
				self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)
				### stockage du parent avec pour cle le chemin complet avec extention (pour l'import du moule dans le Dnd)
				self.ItemDico.update({item.keys()[0]: id})
				self.SetPyData(id, item.keys()[0])
				### pour les fils du sous domain
				for elem in item.values()[0]:
					# si elem simple (modele couple ou atomic)
					if isinstance(elem, str):
						### remplacement des espaces
						elem = elem.strip() #replace(' ','')
						### parent provisoir
						p = self.ItemDico[item.keys()[0]]
						assert (p is not None)
						come_from_net = item.keys()[0].startswith('http')
						### si model atomic
						if elem.endswith('.cmd'):
							### gestion de l'importation de module (.py) associe au .amd si le fichier .py n'a jamais ete decompressse (pour edition par exemple)
							if not come_from_net:
								path = os.path.join(item.keys()[0], elem)
								zf = ZipManager.Zip(path)
								module = zf.GetModule()
								image_file = zf.GetImage()
							else:
								path = item.keys()[0] + '/' + elem + '.py'
								moduel = load_module_from_net(path)

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
							### gestion de l'importation de module (.py) associe au .amd si le fichier .py n'a jamais ete decompressse (pour edition par exemple)
							if not come_from_net:
								path = os.path.join(item.keys()[0], elem)
								zf = ZipManager.Zip(path)
								module = zf.GetModule()
								image_file = zf.GetImage()
							else:
								path = item.keys()[0] + '/' + elem + '.py'
								moduel = load_module_from_net(path)

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

							path = os.path.join(item.keys()[0], elem + '.py') if not item.keys()[0].startswith('http') else item.keys()[0] + '/' + elem + '.py'
							info = Container.CheckClass(path)

							error = isinstance(info, tuple)
							img = self.not_importedidx if error else self.pythonfileidx

							### insertion dans le tree
							id = self.InsertItemBefore(p, 0, elem, img, img)
							self.SetPyData(id, path)

						### error info back propagation
						if error:
							### insert error to the doc field
							while p:
								self.SetItemImage(p, self.not_importedidx, wx.TreeItemIcon_Normal)
								### next parent item
								p = self.GetItemParent(p)

						self.ItemDico.update({os.path.join(item.keys()[0], os.path.splitext(elem)[0]): id})

					else:
						### pour faire remonter l'info dans la liste
						D.append(elem)

				### mise a jour avec le nom complet
				dName = item.keys()[0]

			### for spash screen
			try:
				### format the string depending the nature of the item
				if isinstance(item, dict):
					item = "%s from %s" % (os.path.basename(item.keys()[0]), os.path.basename(os.path.dirname(item.keys()[0])))
				else:
					item = "%s from %s" % (item, os.path.basename(dName))

				pub.sendMessage('object.added', 'Loading %s domain...' % item)
			except:
				pass

			### gestion de la recursion
			if D:
				return self.InsertNewDomain(dName, parent, L + D)
			else:
				return self.InsertNewDomain(dName, parent, L)

	###
	def GetSubDomain(self, dName, domainSubList=None):
		""" Get the dico composed by all of the sub domain of dName (like{'../Domain/PowerSystem': ['PSDomainStructure', 'PSDomainBehavior', 'Object', 'PSSDB', {'../Domain/PowerSystem/Rt': []}, {'../Domain/PowerSystem/PowerMachine': ['toto.cmd', 'Integrator.cmd', 'titi.cmd', 'Mymodel.cmd', {'../Domain/PowerSystem/PowerMachine/TOTO': []}]}, {'../Domain/PowerSystem/Sources': ['StepGen', 'SinGen', 'CosGen', 'RampGen', 'PWMGen', 'PulseGen', 'TriphaseGen', 'ConstGen']}, {'../Domain/PowerSystem/Sinks': ['To_Disk', 'QuickScope']}, {'../Domain/PowerSystem/MyLib': ['', 'model.cmd']}, {'../Domain/PowerSystem/Hybrid': []}, {'../Domain/PowerSystem/Continuous': ['WSum', 'Integrator', 'Gain', 'Gain2', 'NLFunction']}]}
	)
		"""
		if not domainSubList: domainSubList = []

		if not domainSubList:
			### attention il faut que le fichier __init__.py respecte une certain ecriture
			return {dName: self.GetModelList(dName)}
		else:
			### on comptabilise les fichiers si il y en a dans le rep courant (la recusion s'occupe des sous domaines)
			D = {dName: self.GetModelList(dName)}
			### on lance la recursion sur les repertoires fils
			for d in domainSubList:
				p = os.path.join(dName, d)
				D[dName].append(self.GetSubDomain(p, self.GetDomainList(p)))
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
		return dName in self.GetChildRoot()

	def HasString(self, s=""):
		"""
		"""
		return s in map(lambda item: str(self.GetItemText(item)), self.ItemDico.values())

	def CheckItem(self, path):
		"""
		"""

		item = self.ItemDico[path]
		file_path = "%s.py" % path

		info = Container.CheckClass(file_path)
		### there is error in file
		if isinstance(info, tuple):
			### Until it has parent, we redifine icon to inform user
			while item:
				### change image
				self.SetItemImage(item, self.not_importedidx, wx.TreeItemIcon_Normal)
				### next parent item
				item = self.GetItemParent(item)
		else:
			### recompile if no error
			info = ReloadModule.recompile(Utilities.path_to_module(file_path))

			### if not error
			if not isinstance(info, (Exception, str)):
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
					name_list = d.values()[0]
					if name_list:
						path = d.keys()[0]
						for name in filter(lambda a: not isinstance(a, dict) and not a.endswith(('.cmd', '.amd')), name_list):
							self.CheckItem(os.path.join(path, name))

			### extend item if it was extended
			if expanded:
				self.Expand(self.ItemDico[dName])

	@Decorators.BuzyCursorNotification
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
										 _("Connecting to %s ...") % "code.google.com", parent=self,
										 style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
		progress_dlg.Pulse()

		thread = ConnectionThread.UpgradeLibThread(progress_dlg)

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
		devscomp = Components.DEVSComponent()

		### path depends on the nature of droped component
		### if pure python path
		if path.endswith('.py'):
			devscomp.setDEVSPythonPath(path)
		### if devsimpy model
		elif zipfile.is_zipfile(path):
			#zf = ZipManager.Zip(path)
			devscomp.setDEVSPythonPath(os.path.join(path, ZipManager.getPythonModelFileName(path)))
			devscomp.model_path = path
		else:
			sys.stdout.write(_('The code of this type of model is not editable'))
			return

		### call frame editor
		Components.DEVSComponent.OnEditor(devscomp, evt)

	def OnItemRename(self, evt):
		item = self.GetSelection()
		path = self.GetItemPyData(item)

		bn = os.path.basename(path)
		dn = os.path.dirname(path)
		name, ext = os.path.splitext(bn)

		d = wx.TextEntryDialog(self, _('New file name'), defaultValue=name, style=wx.OK)
		d.ShowModal()

		### new label
		new_label = d.GetValue()
		os.rename(path, os.path.join(dn, new_label) + ext)
		Utilities.replaceAll(os.path.join(dn, '__init__.py'), os.path.splitext(bn)[0], new_label)

		self.UpdateAll()

	def OnItemDocumentation(self, evt):
		""" Display the item's documentation on miniFrame.
		"""

		item = self.GetSelection()
		path = self.GetItemPyData(item)
		name = self.GetItemText(item)

		module = Components.BlockFactory.GetModule(path)
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
			wx.MessageBox(_('No documentation for %s') % name, 'Info', wx.OK)

	def OnInfo(self, event):
		"""
		"""
		wx.MessageBox(_(
			'Lybraries Import Manager.\nYou can inport, refresh or upgrade librairies by using right options.\nDefault libraries directory is %s.') % DOMAIN_PATH)

