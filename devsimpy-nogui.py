#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# devsimpy-nogui.py --- DEVSimPy - The Python DEVS no GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2014
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 2.9                                      last modified:  15/11/14
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Bach version of DEVSimPy (whitout GUI)
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### at the beginning to prevent with statement for python version <=2.5
from __future__ import with_statement

import os
import sys
import __builtin__

__version__ = '2.9'

ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

### specific builtin variables. (dont modify the defautls value. If you want to change it, go tot the PreferencesGUI from devsimpy interface.)
builtin_dict = {'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'),
				'DEVSIMPY_PNG': 'iconDEVSimPy.png',	# png file for devsimpy icon
				'HOME_PATH': ABS_HOME_PATH,
				'ICON_PATH': os.path.join(ABS_HOME_PATH, 'icons'),
				'ICON_PATH_16_16': os.path.join(ABS_HOME_PATH, 'icons', '16x16'),
				'SIMULATION_SUCCESS_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Success.wav'),
				'SIMULATION_ERROR_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Error.wav'),
				'DOMAIN_PATH': os.path.join(ABS_HOME_PATH, 'Domain'), # path of local lib directory
				'NB_OPENED_FILE': 5, # number of recent files
				'NB_HISTORY_UNDO': 5, # number of undo
				'OUT_DIR': 'out', # name of local output directory (composed by all .dat, .txt files)
				'PLUGINS_PATH': os.path.join(ABS_HOME_PATH, 'plugins'), # path of plug-ins directory
				'FONT_SIZE': 12, # Block font size
				'LOCAL_EDITOR': True, # for the use of local editor
				'LOG_FILE': os.devnull, # log file (null by default)
				'DEFAULT_SIM_STRATEGY': 'bag-based', #choose the default simulation strategy for PyDEVS
				'PYDEVS_SIM_STRATEGY_DICT' : {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}, # list of available simulation strategy for PyDEVS package
                'PYPDEVS_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'distributed':'SimStrategy5', 'parallel':'SimStrategy6'}, # list of available simulation strategy for PyPDEVS package
				'HELP_PATH' : os.path.join('doc', 'html'), # path of help directory
				'NTL' : False, # No Time Limit for the simulation
				'TRANSPARENCY' : True, # Transparancy for DetachedFrame
				'DEFAULT_PLOT_DYN_FREQ' : 100, # frequence of dynamic plot of QuickScope (to avoid overhead),
				'DEFAULT_DEVS_DIRNAME':'PyDEVS', # default DEVS Kernel directory
				'DEVS_DIR_PATH_DICT':{'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')},
				'GUI_FLAG' : True
				}

builtin_dict['GUI_FLAG'] = False

from SimulationNoGUI import makeSimulation, makeJSON, makeJS

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
__builtin__.__dict__.update(builtin_dict)

#-------------------------------------------------------------------
if __name__ == '__main__':

 	import gettext
 	_ = gettext.gettext

 	#sys.stdout.write(_("DEVSimPy - version %s\n"%__version__ ))

	if len(sys.argv) == 2:
		### check dsp filename
		filename = sys.argv[1]
		if not os.path.exists(filename):
			sys.stderr.write(_('ERROR: Unspecified devsimpy file!\n'))
			sys.exit()

		### launch simulation
		makeSimulation(filename, T = 10.0)

	elif len(sys.argv) == 3:
		### check dsp filename
		filename = sys.argv[1]
		if not os.path.exists(filename):
			sys.stderr.write(_('ERROR: Unspecified devsimpy file!\n'))
			sys.exit()

		### check time
		time = sys.argv[2]

		if str(time) in ('-js','-javascript'):
			### launch JS file generation
			makeJS(filename)
		elif str(time) in ('-json'):
			import json
			### launch JSON file generation
			j = makeJSON(filename)
			sys.stdout.write(json.dumps(j,sort_keys=True, indent=4))
		else:
			if str(time) in ('inf', 'ntl'):
				__builtin__.__dict__['NTL'] = True
				time = 0.0

			### launch simulation
			makeSimulation(filename, time, False)

	else:
		sys.stderr.write(_('ERROR: Unspecified .dsp file!\n'))
		sys.stdout.write(_('USAGE: to simulate $python devsimpy-nogui.py yourfile.dsp [time=10.0|[inf|ntl]]\n'))
		sys.stdout.write(_('USAGE: to generate JS file $python devsimpy-nogui.py yourfile.dsp [-js|-javascript]\n'))
		sys.exit()