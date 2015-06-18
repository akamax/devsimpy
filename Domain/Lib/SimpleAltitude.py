# -*- coding: utf-8 -*-

"""
Name: SimpleAltitude.py
Brief descritpion:
Author(s): L. Capocchi and JF. Santucci <{capocchi, santucci}@univ-corse.fr>
Version:  1.0
Last modified: 2014.11.24
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from __future__ import with_statement

from DomainInterface.DomainBehavior import DomainBehavior


import os.path

#    ======================================================================    #
class SimpleAltitude(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy

        self.state = {'status': 'IDLE', 'sigma': INFINITY}

        self.msgL = [None]*3

    def intTransition(self):
        """
        """
        self.state['sigma'] = INFINITY
        self.state['status'] = 'IDLE'

    def outputFnc(self):
        """
        """
        from Domain.Basic.Object import Message

        ### 10%
        msg = Message([1*self.msgL[0].value[0]+1*self.msgL[1].value[0]+1*self.msgL[2].value[0],0,0],self.timeNext)
        self.poke(self.OPorts[0], msg)

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
			self.state['sigma'] -= self.elapsed


    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
