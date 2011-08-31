'''
Created on 31 May 2011

@author: filo
'''
from variables import dbfile
import sqlite3
import numpy as np
import matplotlib as mpl
import pylab as plt
import matplotlib.cm as cm

query = """select t. subject_id, t.task_name || t.contrast_name as task_contrast, t.th1 ,  t. th2, w.dice from 
(select s. subject_id, s.task_name,  s.contrast_name, f.cluster_forming_threshold as th1 ,  s.cluster_forming_threshold as th2 from 
(select cluster_forming_threshold, subject_id,task_name,contrast_name, session from reliability2010_ggmm_thresholding where session = "first" and roi = 0) as f 
 join 
(select cluster_forming_threshold, subject_id,task_name,contrast_name , session from reliability2010_ggmm_thresholding where session = "second" and roi = 0) as s 
on f.subject_id = s.subject_id and f.task_name = s.task_name and f.contrast_name = s.contrast_name) as t
join
(select subject_id,task_name,contrast_name, dice from reliability2010_within_subjects where roi = 0 and thr_method = "topo_ggmm") as w
on t.subject_id = w.subject_id and t.task_name = w.task_name and t.contrast_name = w.contrast_name where w.task_name != "line_bisection"
"""

conn = sqlite3.connect(dbfile)
c = conn.cursor()

c.execute(query)
arr = np.array(c.fetchall())

th2 = arr[:,3].astype('float')
th1 = arr[:,2].astype('float')
mean_th = arr[:,2:3].astype('float').mean(axis=1)
dice = arr[:,4].astype('float')
task_contrasts = arr[:,1]
task_contrasts_set = set(task_contrasts)
task_contrasts_map = dict(zip(task_contrasts_set, np.linspace(0,1,len(task_contrasts_set)) ))

#task_contrast_int = np.vectorize(lambda x: task_contrasts_map[x])(task_contrast).astype('int')
print task_contrasts_map
#print task_contrast_int

print arr.shape
fig = plt.figure()
ax = fig.add_subplot(111)
for task_contrast in task_contrasts_set:
    indices = (task_contrasts == task_contrast)
    print task_contrasts_map[task_contrast]
    ax.scatter(mean_th[indices], dice[indices], c = cm.rainbow(task_contrasts_map[task_contrast]), 
               s = 2*np.pi*np.square(np.abs(th1[indices] - th2[indices])), 
               label = task_contrast, faceted=False)
ax.set_xlabel("threshold")
ax.set_ylabel("Dice overlap")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)

fig = plt.figure()
ax = fig.add_subplot(111)
for task_contrast in task_contrasts_set:
    indices = (task_contrasts == task_contrast)
    print task_contrasts_map[task_contrast]
    ax.scatter(np.abs(th1[indices] - th2[indices]), dice[indices], c = cm.rainbow(task_contrasts_map[task_contrast]), 
#                   s = 2*np.pi*np.square(np.abs(th1[indices] - th2[indices])), 
                   label = task_contrast, faceted=False)
ax.set_xlabel("abs threshold difference")
ax.set_ylabel("Dice overlap")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)

fig = plt.figure()
ax = fig.add_subplot(111)
for task_contrast in task_contrasts_set:
    indices = (task_contrasts == task_contrast)
    print task_contrasts_map[task_contrast]
    ax.scatter(th1[indices] - th2[indices], dice[indices], c = cm.rainbow(task_contrasts_map[task_contrast]), 
#                   s = 2*np.pi*np.square(np.abs(th1[indices] - th2[indices])), 
                   label = task_contrast, faceted=False)
ax.set_xlabel("threshold difference")
ax.set_ylabel("Dice overlap")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)

query = """select t. subject_id, t.task_name || t.contrast_name as task_contrast, t.th1 ,  t. th2, w.dice from 
(select s. subject_id, s.task_name,  s.contrast_name, f.cluster_forming_threshold_fwe as th1 ,  s.cluster_forming_threshold_fwe as th2 from 
(select cluster_forming_threshold_fwe, subject_id,task_name,contrast_name, session from reliability2010_ggmm_thresholding where session = "first" and roi = 0) as f 
 join 
(select cluster_forming_threshold_fwe, subject_id,task_name,contrast_name , session from reliability2010_ggmm_thresholding where session = "second" and roi = 0) as s 
on f.subject_id = s.subject_id and f.task_name = s.task_name and f.contrast_name = s.contrast_name) as t
join
(select subject_id,task_name,contrast_name, dice from reliability2010_within_subjects where roi = 0 and thr_method = "topo_fdr") as w
on t.subject_id = w.subject_id and t.task_name = w.task_name and t.contrast_name = w.contrast_name where w.task_name != "line_bisection"
"""

conn = sqlite3.connect(dbfile)
c = conn.cursor()

c.execute(query)
arr = np.array(c.fetchall())

fwe_th2 = arr[:,3].astype('float')
fwe_th1 = arr[:,2].astype('float')
fwe_mean_th = arr[:,2:3].astype('float').mean(axis=1)
fwe_dice = arr[:,4].astype('float')
task_contrasts = arr[:,1]
task_contrasts_set = set(task_contrasts)
task_contrasts_map = dict(zip(task_contrasts_set, np.linspace(0,1,len(task_contrasts_set)) ))

fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(np.abs(th1 - th2), dice, c = 'g', 
#                   s = 2*np.pi*np.square(np.abs(th1[indices] - th2[indices])), 
                   label = "topo_ggmm", faceted=False)
ax.scatter(np.abs(fwe_th1 - fwe_th2), fwe_dice, c = 'b', 
#                   s = 2*np.pi*np.square(np.abs(th1[indices] - th2[indices])), 
                   label = "topo_fdr", faceted=False)
ax.set_xlabel("abs threshold difference")
ax.set_ylabel("Dice overlap")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(mean_th, dice, c = 'g', 
               label = "topo_ggmm", faceted=False)
ax.scatter(fwe_mean_th, fwe_dice, c = 'b', 
               label = "topo_fdr", faceted=False)
ax.set_xlabel("threshold")
ax.set_ylabel("Dice overlap")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)

fig = plt.figure()
ax = fig.add_subplot(111)
for task_contrast in task_contrasts_set:
    indices = (task_contrasts == task_contrast)
    print task_contrasts_map[task_contrast]
    ax.scatter(np.abs(th1[indices] - th2[indices]), dice[indices], c = cm.rainbow(task_contrasts_map[task_contrast]), 
#                   s = 2*np.pi*np.square(np.abs(th1[indices] - th2[indices])), 
                   label = task_contrast, faceted=False, marker = 'o')
    ax.scatter(np.abs(fwe_th1[indices] - fwe_th2[indices]), fwe_dice[indices], c = cm.rainbow(task_contrasts_map[task_contrast]), 
#                   s = 2*np.pi*np.square(np.abs(th1[indices] - th2[indices])), 
                   label = task_contrast, faceted=False, marker = '>')
ax.set_xlabel("abs threshold difference")
ax.set_ylabel("Dice overlap")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)

plt.show()

