import numpy as np
import math

def implied_probability(odds: int):
   if(odds < 0):
      return 1 / (1 - 100 / odds)
   else:
      return 1 / (1 + odds / 100)