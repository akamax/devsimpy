# -*- coding: utf-8 -*-

"""
Name: SimpleLayer.py
Brief descritpion: two inputs and one output.

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
class SimpleLayer(DomainBehavior):
    """
    """

    def __init__(self):
        DomainBehavior.__init__(self)

        ### local copy

        self.state = {'status': 'IDLE', 'sigma': INFINITY }

        self.rain_msg = None

    def intTransition(self):
        """
        """
        self.state['sigma'] = INFINITY
        self.state['status'] = 'IDLE'
        self.rain_msg=None

    def outputFnc(self):
        """
        """
        assert self.rain_msg

        val = (float(self.rain_msg.value[0])*20)/100.0
        self.poke(self.OPorts[0], Message([val, 0, 0], self.timeNext))

    def extTransition(self):
        """
        """
        msg1 = self.peek(self.IPorts[0])

        if msg1: self.rain_msg = msg1

        if self.rain_msg:
            self.state['status'] = 'BUZY'
            self.state['sigma'] = 0
        else:
            self.state['sigma'] = INFINITY

    def timeAdvance(self): return self.state['sigma']

    def __str__(self): return self.__class__.__name__
