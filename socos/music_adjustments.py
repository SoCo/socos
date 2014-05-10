""" The MusicAdjustments class contains all functionality related to
adjusting value like volume, bass, treble. """

from __future__ import print_function
import sys


class MusicAdjustments(object):
    """ The MusicAdjustments class contains all functionality related to
    adjusting value like volume, bass, treble. """

    def __init__(self, soco):
        self.soco = soco

    @staticmethod
    def err(message):
        """ print an error message """
        print(message, file=sys.stderr)

    def adjust_volume(self, operator):
        """ Adjust the volume up or down with a factor from 1 to 100 """
        factor = self.get_adjustment_factor(operator)
        if not factor:
            return False

        vol = self.soco.volume

        if operator[0] == '+':
            if (vol + factor) > 100:
                factor = 1
            self.soco.volume = (vol + factor)
            return self.soco.volume
        elif operator[0] == '-':
            if (vol - factor) < 0:
                factor = 1
            self.soco.volume = (vol - factor)
            return self.soco.volume
        else:
            self.err("Valid operators for volume are + and -")

    def adjust_bass(self, operator):
        """ Adjust the bass up or down with a factor from -10 to 10 """
        factor = self.get_adjustment_factor(operator)
        if not factor:
            return False

        bass = self.soco.bass

        if operator[0] == '+':
            if (bass + factor) > 10:
                factor = 1
            self.soco.bass = (bass + factor)
            return self.soco.bass
        elif operator[0] == '-':
            if (bass - factor) < -10:
                factor = 1
            self.soco.bass = (bass - factor)
            return self.soco.bass
        else:
            self.err("Valid operators for bass are + and -")

    def adjust_treble(self, operator):
        """ Adjust the treble up or down with a factor from -10 to 10 """
        factor = self.get_adjustment_factor(operator)
        if not factor:
            return False

        treble = self.soco.treble

        if operator[0] == '+':
            if (treble + factor) > 10:
                factor = 1
            self.soco.treble = (treble + factor)
            return self.soco.treble
        elif operator[0] == '-':
            if (treble - factor) < -10:
                factor = 1
            self.soco.treble = (treble - factor)
            return self.soco.treble
        else:
            self.err("Valid operators for treble are + and -")

    def get_adjustment_factor(self, operator):
        """ get the factor to adjust the volume, bass, treble... with """
        factor = 1
        if len(operator) > 1:
            try:
                factor = int(operator[1:])
            except ValueError:
                self.err("Adjustment factor for has to be a int.")
                return
        return factor
