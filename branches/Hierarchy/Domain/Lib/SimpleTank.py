# -*- coding: utf-8 -*-

"""
Name: SimpleTank.py
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
class SimpleTank(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy

        self.state = {'status': 'IDLE', 'sigma': INFINITY }

        self.msgL=[None]*2

        ### tank buffer
        self.buffer = 0

    def intTransition(self):
        self.state['sigma'] = INFINITY

    def outputFnc(self):

        ### test temp
        if self.msgL[0].value[0] > 0:
            self.buffer -= self.buffer/3.5
            flow = self.msgL[1].value[0]
            msg = Message([self.buffer+flow,0,0], self.timeNext)
        else:
            self.buffer += self.msgL[1].value[0]
            msg = Message([0,0,0], self.timeNext)

        self.poke(self.OPorts[0], msg)
        self.msgL=[None]*2

    def extTransition(self):
        """
        """

        for i in range(2):
            msg = self.peek(self.IPorts[i])
            if msg:
               self.msgL[i]=msg
       
        if not None in self.msgL:
            self.state['sigma'] = 0
        else:
            self.state['sigma'] = INFINITY

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
