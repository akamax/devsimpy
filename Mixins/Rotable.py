# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Rotable.py ---
#                     --------------------------------
#                          Copyright (c) 2013
#                           Laurent CAPOCCHI
#                         University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 05/03/2013
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#---------------------------------------------------------
class Rotable:
	""" Creates rotable Block can rotate under 4 direction (est, ouest, nord, sud)
	"""

	def __init__(self):
		""" Constructor.
		"""
		self.direction = "ouest"

	###
	def OnRotateR(self, event):
		if self.direction == "ouest":
			self.direction = "nord"
		elif self.direction == "nord":
			self.direction = "est"
		elif self.direction == "est":
			self.direction = "sud"
		else:
			self.direction = "ouest"

	###
	def OnRotateL(self, event):
		if self.direction == "ouest":
			self.direction = "sud"
		elif self.direction == "nord":
			self.direction = "ouest"
		elif self.direction == "est":
			self.direction = "nord"
		else:
			self.direction = "est"

