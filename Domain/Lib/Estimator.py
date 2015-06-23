# -*- coding: utf-8 -*-

"""
Name: Estimator.py
Brief descritpion:
Author(s): L. Capocchi and JF. Santucci <{capocchi, santucci}@univ-corse.fr>
Version:  1.0
Last modified: 2014.11.24
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from __future__ import with_statement

from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message

import os.path

#    ======================================================================    #
class Estimator(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy

        self.state = {'status': 'IDLE', 'sigma': INFINITY }

        self.msgL = [None]*3

    def intTransition(self):
        """
        """
        self.state['status'] = 'IDLE'
        self.state['sigma'] = INFINITY

    def outputFnc(self):
        """
        """
        sm = self.msgL[0].value[0]+self.msgL[1].value[0]+self.msgL[2].value[0]
        val1 = sm*0.5
        val2 = sm*0.5

        self.poke(self.OPorts[0], Message([val1,0,0], self.timeNext))
        self.poke(self.OPorts[1], Message([val2,0,0], self.timeNext))
        self.msgL = [None]*3

    def extTransition(self):
        """
        """

        for i in range(3):
            msg = self.peek(self.IPorts[i])
            if msg:
                self.msgL[i]=msg

		if not None in self.msgL:
			self.state['sigma'] = 0
			self.state['status'] = 'SENDING'
		else:
			self.state['sigma'] = INFINITY

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
