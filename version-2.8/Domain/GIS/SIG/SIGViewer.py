# -*- coding: utf-8 -*-

"""
Name: SIGViewer.py
Brief description: SIG plugin viewer 
Author(s): L. Capocchi <capocchi@univ-corse.fr>, J.F. Santucci <santucci@univ-corse.fr>, B. Poggi <poggi@univ-corse.fr>
Version: 0.1
Last modified: 08/07/2012
GENERAL NOTES AND REMARKS: Use the simplekml module.
GLOBAL VARIABLES AND FUNCTIONS:
"""

### just for python 2.5
from __future__ import with_statement
from DomainInterface.DomainBehavior import DomainBehavior 

import os
import simplekml

# ===================================================================   #
class SIGViewer(DomainBehavior):
	"""
	"""

	###
	def __init__(self, fileName = "out.kml"):
		""" Constructor.
		
			@param fileName : output file name
		"""

		DomainBehavior.__init__(self)

		self.fn = fileName

		### State variable
		self.state = {'status': 'INACTIF', 'sigma': INFINITY}
		
		self.kml = simplekml.Kml()
		
	###
	def extTransition(self):
		"""
		"""

		activePort = self.myInput.keys()[0]
		msg = self.peek(activePort)
		
		### new obj
		obj = msg.value[0]
		
		if hasattr(obj, 'folder'):
			### create new layer
			print obj.folder
			kml_folder = self.kml.newfolder(name=obj.folder)
			
		if str(obj) == 'Point':
			print "sdvc"

			### add point
			point = kml_folder.newpoint()
			point.name = obj.name
			point.coords = [(obj.lon, obj.lat, obj.alt)]
			point.description = obj.desc
		
		#### kml tree
		#kml_tree = KML.KML_Tree(self.fn)
		#doc = kml_tree.doc
		
		#### if there is no Folder, we create it with a placemark
		#if doc.findall("{%s}Folder" % (KML.KML_Tree.NS)) == []:
			#kml_tree.add_placemark(kml_tree.add_folder(doc, point), point)
		#### some Folder are present
		#else:
			
			#### if new folder exist
			#folder_list = filter(lambda f:point.folder == f.findtext("{%s}name" % (KML.KML_Tree.NS)) ,doc.findall("{%s}Folder" % (KML.KML_Tree.NS)))
			#if folder_list != []:
				#folder = folder_list[0]
				#place_list = filter(lambda p: point.name == p.findtext("{%s}name" % (KML.KML_Tree.NS)), folder.findall("{%s}Placemark" % (KML.KML_Tree.NS)))
				#### if the name of new placemark already exist, we replace it on the existing Folder
				#if place_list != []:
					#place = place_list[0]
					#kml_tree.add_placemark(folder, point, place)
				#### the new placemark is added on the existing Folder
				#else:
					#kml_tree.add_placemark(folder, point)
			#else:
				#kml_tree.add_placemark(kml_tree.add_folder(doc, point), point)
			
		##print self.kml_tree.tostring(kml)
		
		#### kml writing
		#kml_tree.write(self.fn)

		self.kml.save(self.fn)
		
		self.state['sigma'] = 0

	###
	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY
					
	###
	def timeAdvance(self):return self.state['sigma']

	###
	def __str__(self):return "SIGViewer"
