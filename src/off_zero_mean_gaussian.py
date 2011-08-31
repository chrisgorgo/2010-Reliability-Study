'''
Created on 13 Jul 2011

@author: filo
'''
from bootstrap_test import paired_one_sample, two_sample

import sqlite3
import numpy as np
import matplotlib as mpl
import pylab as plt
import os
from variables import getStatLabels, dbfile, tasks, results_dir, lefties,\
    thr_methods
from variables import roi as rois

def plot_between_subjects_box_plot(metric, where, filename, table='reliability2010_ggmm_thresholding'):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    metric_vals = []
    labels = []
#    exclude = []
#    exclude_str = ""
#    
    for task in tasks:
        for contrast in getStatLabels(task):
            where_keys = " and ".join([t[0] + "=?" for t in where+[["task_name"], ["contrast_name"]]])
            
#            exclude = []
#            exclude_str = ""
#        
#            for key in [t[1] for t in where if t[0] == "contrast_name"] + [compare_c]:
#                print key
#                if key.lower().find('finger') != -1 or key.lower().find('foot') != -1:
#                    exclude = lefties
#                    break
#                
#            if exclude:
#                exclude_str = " and (subject_id1 not in (%s) and subject_id2 not in (%s))"%(",".join(["'%s'"%s for s in exclude]), ",".join(["'%s'"%s for s in exclude]))
                
#            print exclude_str
            query_str = "SELECT %s FROM %s where %s ORDER BY session, subject_id"%(metric,table,where_keys)
            print query_str
            c.execute(query_str, tuple([t[1] for t in where] + [task, contrast]))
            arr = np.array(c.fetchall())
            print arr.shape
            metric_vals.append(arr)
            labels.append(task+contrast)
        
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    
    c.execute("SELECT DISTINCT subject_id FROM reliability2010_ggmm_thresholding ORDER BY subject_id")
    subject_ids = c.fetchall()
    conn.commit()
    c.close()
    
    metric_vals = np.array(metric_vals)
    metric_vals.shape = (metric_vals.shape[0], metric_vals.shape[1])
    
    fig = plt.figure(figsize=(8.27,11.69))
    figtitle = ", ".join([t[0] + "=" + str(t[1]) for t in where])
    t = fig.text(0.5, 0.95, figtitle,
               horizontalalignment='center',
               fontproperties=mpl.font_manager.FontProperties(size=16))
    ax1 = fig.add_subplot(212)
    ax1.boxplot(metric_vals.T)
    ax1.set_xticklabels(labels)
    fig.autofmt_xdate()
    ax1.set_ylabel(metric)
    #ax1.set_ylim(bottom=-0.1, top=1.1)
    
    subject_ids =[subject_id[0].split('-')[0] for subject_id in subject_ids]
    
    
    ax2 = fig.add_subplot(211)
    colormap = plt.cm.spectral
    ax2.set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, len(subject_ids))])
    ax2.plot(range(1,len(labels)+1), metric_vals, marker = 'o')
    ax2.set_ylabel(metric)
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_ylim(top=ax2.get_ylim()[1]+3)
    ax2.get_xaxis().set_visible(False)
    ax2.legend(subject_ids, title="Subjects", 
               #bbox_to_anchor=(0., 1.02, 1., .102), loc=9,
               ncol=4, 
               mode="expand", 
               borderaxespad=0.)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    plt.savefig(filename)
    plt.show()


plot_between_subjects_box_plot(where=[('roi', 0)], 
                                          metric="gaussian_mean", 
                                          filename = os.path.join(results_dir, "off_zero_mean.pdf"))
            