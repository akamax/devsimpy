# -*- coding: utf-8 -*-

"""
Name: Layer.py
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
class Layer(DomainBehavior):
    """
    """

    def __init__(self, coef=0.0):
        DomainBehavior.__init__(self)

        ### local copy
        self.coef = coef

        self.state = {'status': 'IDLE', 'sigma': INFINITY }

        self.msgL = [None]*2

        self.buffer = 0.0

    def intTransition(self):
        """
        """
        self.state['sigma'] = INFINITY

    def outputFnc(self):
        """
        """
        self.poke(self.OPorts[0], Message([self.buffer, 0, 0], self.timeNext))
        self.buffer = 0
        self.msgL = [None]*2

    def extTransition(self):
        """
        """

        self.msg1 = self.peek(self.IPorts[0])
        #self.msg2 = self.peek(self.IPorts[1])

        if self.msg1: self.msgL[0] = self.msg1
        #if self.msg2: self.msgL[1] = self.msg2

        if not None in self.msgL:
           self.buffer = self.msgL[0].value[0] #+ self.msgL[1].value[0]
        #if self.state['status'] == 'IDLE':
        #    self.state["status"] = "BUZY"
        #    self.state['sigma'] = self.coef
        #else:
        #    self.state['sigma'] -= self.elapsed
           self.state['sigma'] = 0
        else:
           self.state['sigma'] = INFINITY

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
