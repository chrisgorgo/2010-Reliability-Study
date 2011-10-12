'''
Created on 26 May 2011

@author: filo
'''
import numpy as np
from scipy.stats.mstats_extras import hdmedian
from scipy.stats.stats import scoreatpercentile

def paired_one_sample(set1, set2, func, n_resample = 3000, alpha = 0.05, ci = False):
    resampled_medians = np.zeros((n_resample))
    
    for i in range(n_resample):
        index = np.random.random_integers(0,len(set1)-1, len(set1))
        resampled_medians[i] = func(set1[index] - set2[index])
    
    
    p_onesided = float(np.sum(resampled_medians > 0))/float(n_resample)
    p_twosided = 2* min(p_onesided,1-p_onesided)
    if ci:
        resampled_medians.sort()
        ci_l, ci_h = (resampled_medians[int(n_resample*alpha/2)], resampled_medians[int(n_resample*(1-alpha/2))])
        print p_twosided, ci_l, ci_h
        #assert (p_twosided <= alpha) == ((0 < ci_l or 0 > ci_h) or ci_l == ci_h)
        return (p_onesided, p_twosided, ci_l, ci_h)
    else:
        return (p_onesided, p_twosided)

def two_sample(set1, set2, func, n_resample = 3000, alpha = 0.05, ci = False):
    resampled_diff = np.zeros((n_resample))
    
    for i in range(n_resample):
        sample1 = set1[np.random.random_integers(0,len(set1)-1, len(set1))]
        sample2 = set2[np.random.random_integers(0,len(set2)-1, len(set2))]
        
        resampled_diff[i] = func(sample1.flatten()) - func(sample2.flatten())
    
    p_onesided = float(np.sum(resampled_diff > 0))/float(n_resample)
    p_twosided = 2* min(p_onesided,1-p_onesided)
    if ci:
        resampled_diff.sort()
        ci_l, ci_h = (resampled_diff[int(n_resample*alpha/2)], resampled_diff[int(n_resample*(1-alpha/2))])
        print p_twosided, ci_l, ci_h
        assert ((p_twosided <= alpha) == (0 < ci_l or 0 > ci_h)) or (ci_l == ci_h or abs(p_twosided - alpha) < 0.0000000001)
        return (p_onesided, p_twosided, ci_l, ci_h)
    else:
        return (p_onesided, p_twosided)


#a = np.array([1,2,3,4,5,6])
#b = np.array([1.1,2.2,3.1,4.3,5.2,6.1])
#c = np.array([0.9,2.2,2.8,4.3,4.7,6.1])
#print paired_one_sample(a,c, average)
#print two_sample(a,b, average)
    