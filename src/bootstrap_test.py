'''
Created on 26 May 2011

@author: filo
'''
import numpy as np
from scipy.stats.mstats_extras import hdmedian

def paired_one_sample(set1, set2, n_resample = 1000, alpha = 0.05):
    diff = set1 - set2
    resampled_medians = np.zeros((n_resample))
    
    for i in range(n_resample):
        sample = diff[np.random.random_integers(0,len(diff)-1, len(diff))]
        resampled_medians[i] = hdmedian(sample)
    
    p_onesided = float(np.sum(resampled_medians > 0))/float(n_resample)
    p_twosided = 2* min(p_onesided,1-p_onesided)
    return (p_onesided, p_twosided)

def two_sample(set1, set2, n_resample = 1000, alpha = 0.05):
    resampled_diff = np.zeros((n_resample))
    
    for i in range(n_resample):
        sample1 = set1[np.random.random_integers(0,len(set1)-1, len(set1))]
        sample2 = set2[np.random.random_integers(0,len(set2)-1, len(set2))]
        
        resampled_diff[i] = hdmedian(sample1.flatten()) - hdmedian(sample2.flatten())
    
    p_onesided = float(np.sum(resampled_diff > 0))/float(n_resample)
    p_twosided = 2* min(p_onesided,1-p_onesided)
    return (p_onesided, p_twosided)
    