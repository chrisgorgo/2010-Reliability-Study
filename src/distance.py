'''
Created on 14 Sep 2011

@author: filo
'''
import sqlite3
from variables import dbfile
import numpy as np
import pylab as plt
from scipy.stats import pearsonr

conn = sqlite3.connect(dbfile)
c = conn.cursor()
c.execute("SELECT dice, distance  FROM reliability2010_within_subjects WHERE masked_comparison=1")
dice_distance = c.fetchall()

conn.commit()
c.close()

dice_distance =  np.array(dice_distance, dtype=float)
dice_distance = dice_distance[np.logical_not(np.isnan(dice_distance[:,1])), :]
plt.scatter(dice_distance[:,0], dice_distance[:,1])

r, p = pearsonr(dice_distance[:,0], dice_distance[:,1])
print "Pearson r = %f, p = %f"%(r, p)
plt.show()