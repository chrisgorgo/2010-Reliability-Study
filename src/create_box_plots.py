'''
Created on 17 Apr 2011

@author: filo
'''
from bootstrap_test import paired_one_sample, two_sample

import sqlite3
import numpy as np
import matplotlib as mpl
import pylab as plt
import os
from variables import getStatLabels, dbfile, tasks, results_dir, lefties,\
    thr_methods, exceptions, exclude_subjects
from variables import roi as rois
from scipy.stats.mstats_extras import hdmedian, hdquantiles
from scipy.stats.stats import scoreatpercentile, tmean
from scipy.stats.mstats_basic import winsorize, trimr

def hdIQR(v):
    q = hdquantiles(v, prob=list([.25,.75]))
    return q[1] - q[0] 

def plot_between_session_box_plot(metric, where, compare, exclude, filename, table='reliability2010_within_subjects', test = True):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    metric_vals = []
    where_keys = " and ".join([t[0] + "=?" for t in where])
    c.execute("SELECT DISTINCT subject_id FROM %s where %s and %s in (%s) and dice = 0 and distance is NULL ORDER BY subject_id"%(table,where_keys, compare[0], ','.join(["'%s'"%s for s in compare[1]])), tuple([t[1] for t in where]))
    exclude = ('subject_id', exclude[1] + [i[0] for i in c.fetchall()])
    
    
    for compare_c in compare[1]:
        where_keys = " and ".join([t[0] + "=?" for t in where+[compare]])
        exclude_clause = "%s not in (%s)"%(exclude[0], ",".join(["'%s'"%s for s in exclude[1]]))
        c.execute("SELECT %s FROM %s where %s ORDER BY subject_id"%(metric,table,where_keys+ " and " +exclude_clause), tuple([t[1] for t in where] + [compare_c]))
        metric_vals.append(np.array(c.fetchall(), dtype=np.float))
    
    c.execute("SELECT DISTINCT subject_id FROM reliability2010_within_subjects WHERE %s"%exclude_clause)
    subject_ids = c.fetchall()
    if len(subject_ids) < 2:
        return
    conn.commit()
    c.close()
    
    metric_vals = np.array(metric_vals, dtype=np.float)
    metric_vals.shape = (metric_vals.shape[0], metric_vals.shape[1])
    
    fig = plt.figure(figsize=(8.27,11.69))
    figtitle = ", ".join([t[0] + "=" + str(t[1]) for t in where])
    t = fig.text(0.5, 0.95, figtitle,
               horizontalalignment='center',
               fontproperties=mpl.font_manager.FontProperties(size=16))
    ax1 = fig.add_subplot(212)
    ax1.boxplot(metric_vals.T)
    ax1.set_xticklabels(compare[1])
    ax1.set_ylabel(metric + " overlap")
    #ax1.set_ylim(bottom=-0.1, top=1.1)
    
    subject_ids =[subject_id[0].split('-')[0] for subject_id in subject_ids]
    
    
    ax2 = fig.add_subplot(211)
    colormap = plt.cm.spectral
    ax2.set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, len(subject_ids))])
    ax2.plot(range(1,len(compare[1])+1), metric_vals, marker = 'o')
    ax2.set_ylabel(metric + " overlap")
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_ylim(ax1.get_ylim())
    ax2.get_xaxis().set_visible(False)
    ax2.legend(subject_ids, title="Subjects", 
               #bbox_to_anchor=(0., 1.02, 1., .102), loc=9,
               ncol=4, 
               mode="expand", 
               borderaxespad=0.)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    if test:
        ax1.text(0.5, 0.90, "onesided_p = %.2f, twosided_p = %.2f"%paired_one_sample(metric_vals[1,:], 
                                                                                     metric_vals[0,:], 
                                                                                     func=hdmedian),
                   horizontalalignment='center',
                   fontproperties=mpl.font_manager.FontProperties(size=16),
                   transform=ax1.transAxes)
        print figtitle
        conn = sqlite3.connect(dbfile)
        c = conn.cursor()
        insert_vals = dict(where)
        insert_vals['metric'] = metric
        
        
        parameters = {'hdmedian': hdmedian, 
                      #'IQR': hdIQR,
                      'tmean': lambda v:trimr(v, (0.2,0.2)).mean(),
                      #'winsorized_variance': lambda v:winsorize(v, (0.2,0.2)).var()
                      }
        
        for parameter,func in parameters.iteritems():
            
            if parameter in ['IQR', 'winsorized_variance']:
                _, insert_vals['twosided_p'], insert_vals['ci_l'], insert_vals['ci_h'] = two_sample(metric_vals[1,:], metric_vals[0,:], func = func, ci = True)
            else:
                _, insert_vals['twosided_p'], insert_vals['ci_l'], insert_vals['ci_h'] = paired_one_sample(metric_vals[1,:], metric_vals[0,:], func = func, ci = True)
            insert_vals['parameter'] = parameter
            insert_vals['value_1'] = float(func(metric_vals[0,:]))
            insert_vals['value_2'] = float(func(metric_vals[1,:]))
            insert_vals['name_1'] = compare[1][0]
            insert_vals['name_2'] = compare[1][1]
            
            print "%s = %f and %f (twosided_p = %.2f)"%(insert_vals['parameter'], insert_vals['value_1'], insert_vals['value_2'], insert_vals['twosided_p'])
            print "INSERT OR REPLACE INTO comparisons ("+",".join(insert_vals.keys()) + ") VALUES (" + ",".join(["?"]*len(insert_vals.values())) + ")"
            print insert_vals.values()
            c.execute("INSERT OR REPLACE INTO comparisons ("+",".join(insert_vals.keys()) + ") VALUES (" + ",".join(["?"]*len(insert_vals.values())) + ")", 
                      insert_vals.values())
        conn.commit()
        c.close()
    
    
    
    plt.savefig(filename)
    
def plot_between_subjects_box_plot(metric, where, compare, filename, table='reliability2010_between_subjects'):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    metric_vals = []
    exclude = []
    exclude_str = ""
    
    for compare_c in compare[1]:
        where_keys = " and ".join([t[0] + "=?" for t in where+[compare]])
        
        exclude = []
        exclude_str = ""
    
#        for key in [t[1] for t in where if t[0] == "contrast_name"] + [compare_c]:
#            print key
#            if key.lower().find('finger') != -1 or key.lower().find('foot') != -1:
#                exclude = lefties
#                break
            
        if exclude:
            exclude_str = " and (subject_id1 not in (%s) and subject_id2 not in (%s))"%(",".join(["'%s'"%s for s in exclude]), ",".join(["'%s'"%s for s in exclude]))
            
        print exclude_str
        c.execute("SELECT %s FROM %s where %s"%(metric,table,where_keys) + exclude_str, tuple([t[1] for t in where] + [compare_c]))
        arr = np.array(c.fetchall())
        print arr.shape
        metric_vals.append(arr)
        
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
        
    conn.commit()
    c.close()
    
    #metric_vals = np.array(metric_vals)
    #metric_vals.shape = (metric_vals.shape[0], metric_vals.shape[1])
    
    fig = plt.figure()
    figtitle = ", ".join([t[0] + "=" + str(t[1]) for t in where])
    t = fig.text(0.5, 0.95, figtitle,
               horizontalalignment='center',
               fontproperties=mpl.font_manager.FontProperties(size=16))
    ax1 = fig.add_subplot(111)
    ax1.boxplot(metric_vals)
    ax1.set_xticklabels(compare[1])
    ax1.set_ylabel(metric + " overlap")
    ax1.set_ylim(bottom=-0.1, top=1.1)
    
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    plt.savefig(filename)
    
    
def plot_between_within_box_plot(metric, where, filename, exclude):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    metric_vals = []
    
    
    
    
    where_keys = " and ".join([t[0] + "=?" for t in where])
    c.execute("SELECT DISTINCT subject_id FROM reliability2010_within_subjects where %s and dice = 0 and distance is NULL ORDER BY subject_id"%(where_keys), tuple([t[1] for t in where]))
    exclude = ('subject_id', exclude[1] + [i[0] for i in c.fetchall()])
    exclude_clause = "%s not in (%s)"%(exclude[0], ",".join(["'%s'"%s for s in exclude[1]]))
    c.execute("SELECT %s FROM reliability2010_within_subjects where %s ORDER BY subject_id"%(metric,where_keys + " and " + exclude_clause), tuple([t[1] for t in where]))
    print "SELECT %s FROM reliability2010_within_subjects where %s ORDER BY subject_id"%(metric,where_keys + " and " + exclude_clause), tuple([t[1] for t in where])
    res = np.array(c.fetchall(), dtype=np.float)
    if len(res) < 2:
        return
    metric_vals.append(res[:,0])
    
    
    
    where_keys = " and ".join([t[0] + "=?" for t in where])
#    exclude = []
    exclude_str = ""
#
#    for key in [t[1] for t in where if t[0] == "contrast_name"]:
#        if key.lower().find('finger') != -1 or key.lower().find('foot') != -1:
#            exclude = lefties
#            break
#        
#    if exclude:
#        #exclude_str = " and (subject_id1 not in (%s) and subject_id2 not in (%s))"%(",".join(["'%s'"%s for s in exclude]), )*2
#        exclude_str = " and ((subject_id1 not in (%s) and subject_id2 not in (%s)) or (subject_id1 in (%s) and subject_id2 in (%s)))"%((",".join(["'%s'"%s for s in exclude]), )*4)
    if exclude[1]:    
        exclude_str = " and ((subject_id1 not in (%s) and subject_id2 not in (%s)) or (subject_id1 in (%s) and subject_id2 in (%s)))"%((",".join(["'%s'"%s for s in exclude[1]]), )*4)
    c.execute("SELECT %s FROM reliability2010_between_subjects where %s"%(metric,where_keys) + exclude_str, tuple([t[1] for t in where]))
    
    print "SELECT %s FROM reliability2010_between_subjects where %s"%(metric,where_keys) + exclude_str, tuple([t[1] for t in where])
    #arr = np.array(c.fetchall())
    res = np.array(c.fetchall(), dtype=np.float)
    print res.shape
    metric_vals.append(res[:,0])
    #metric_vals = np.array(metric_vals, dtype=np.float)
    
    conn.commit()
    c.close()
    
    
    fig = plt.figure()
    figtitle = ", ".join([t[0] + "=" + str(t[1]) for t in where])
    t = fig.text(0.5, 0.95, figtitle,
               horizontalalignment='center',
               fontproperties=mpl.font_manager.FontProperties(size=16))
    ax1 = fig.add_subplot(111)
    ax1.boxplot(metric_vals)
    ax1.set_xticklabels(["within subjects", "between subjects"])
    ax1.set_ylabel(metric + " overlap")
    ax1.set_ylim(bottom=-0.1, top=1.1)
    
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    
    ax1.text(0.5, 0.90, "onesided_p = %.2f, twosided_p = %.2f"%two_sample(metric_vals[1], metric_vals[0], func=hdmedian),
               horizontalalignment='center',
               fontproperties=mpl.font_manager.FontProperties(size=16),
               transform=ax1.transAxes)
    
    print figtitle
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    insert_vals = dict(where)
    insert_vals['metric'] = metric
    
    parameters = {'hdmedian': hdmedian, 
                  #'IQR': hdIQR, 
                  'tmean': lambda v:trimr(v, (0.2,0.2)).mean(),
                  #'winsorized_variance': lambda v:winsorize(v, (0.2,0.2)).var()
                  }
    
    for parameter,func in parameters.iteritems():
    
        _, insert_vals['twosided_p'], insert_vals['ci_l'], insert_vals['ci_h'] = two_sample(metric_vals[0], metric_vals[1], func = func, ci = True)
        insert_vals['parameter'] = parameter
        insert_vals['value_1'] = float(func(metric_vals[0]))
        insert_vals['value_2'] = float(func(metric_vals[1]))
        insert_vals['name_1'] = "within"
        insert_vals['name_2'] = "between"
        
        print "%s = %f and %f (twosided_p = %.2f)"%(insert_vals['parameter'], insert_vals['value_1'], insert_vals['value_2'], insert_vals['twosided_p'])
        print "INSERT OR REPLACE INTO comparisons ("+",".join(insert_vals.keys()) + ") VALUES (" + ",".join(["?"]*len(insert_vals.values())) + ")"
        print insert_vals.values()
        c.execute("INSERT OR REPLACE INTO comparisons ("+",".join(insert_vals.keys()) + ") VALUES (" + ",".join(["?"]*len(insert_vals.values())) + ")", 
                  insert_vals.values())
    conn.commit()
    c.close()

    plt.savefig(filename)


#plot_between_session_box_plot(task="motor", contrast="Finger", metric="dice", thr_methods=['topo_ggmm', 'topo_fdr'], filename = os.path.join(results_dir, "motor","%s_dice.pdf"%("Finger")))

#compare topo_ggmm with topo_fdr
#for roi in rois:
#    for task in tasks:
#        for contrast in getStatLabels(task):
#            if roi:
#                masked_comparisons = [True]
#            else:
#                masked_comparisons = [False, True]
#            for masked_comparison in masked_comparisons:
#                exclude = []
#                for exception in exceptions:
#                    if exception['task_name'] == task:
#                        exclude.append(exception['subject_id'])
#                if task in exclude_subjects.keys():
#                    exclude += exclude_subjects[task]
#                    
#                plot_between_session_box_plot(where=[('task_name',task), ('contrast_name',contrast), ('roi', roi), ('masked_comparison', masked_comparison)], 
#                                              metric="dice", 
#                                              compare= ('thr_method',['topo_fdr', 'topo_ggmm']),
#                                              exclude=('subject_id', exclude), 
#                                              filename = os.path.join(results_dir, "compare topo_ggmm with topo_fdr", "%s_%s_roi_%s_masked_%s_dice.pdf"%(task,contrast, roi, masked_comparison)))
##
#for roi in rois:
#    for task in tasks:
#        for contrast in getStatLabels(task):
#            if roi:
#                masked_comparisons = [True]
#            else:
#                masked_comparisons = [False, True]
#            for masked_comparison in masked_comparisons:
#                exclude = []
#                for exception in exceptions:
#                    if exception['task_name'] == task:
#                        exclude.append(exception['subject_id'])
#                if task in exclude_subjects.keys():
#                    exclude += exclude_subjects[task]
#                    
#                plot_between_session_box_plot(where=[('task_name',task), ('contrast_name',contrast), ('roi', roi), ('masked_comparison', masked_comparison)], 
#                                              metric="distance", 
#                                              compare= ('thr_method',['topo_fdr', 'topo_ggmm']),
#                                              exclude=('subject_id', exclude), 
#                                              filename = os.path.join(results_dir, "compare topo_ggmm with topo_fdr", "%s_%s_roi_%s_masked_%s_distance.pdf"%(task,contrast, roi, masked_comparison)))

#for roi in rois:
#    for task in tasks:
#        if roi:
#            masked_comparisons = [True]
#        else:
#            masked_comparisons = [False, True]
#        for masked_comparison in masked_comparisons:
#            exclude = []
#            for exception in exceptions:
#                if exception['task_name'] == task:
#                    exclude.append(exception['subject_id'])
#            if task in exclude_subjects.keys():
#                exclude += exclude_subjects[task]
#            plot_between_session_box_plot(where=[('task_name',task), ('roi', roi), ('masked_comparison', masked_comparison)], 
#                                          metric="dice", 
#                                          compare= ('thr_method',['topo_fdr', 'topo_ggmm']),
#                                          exclude=('subject_id', exclude), 
#                                          filename = os.path.join(results_dir, "compare topo_ggmm with topo_fdr", "%s_roi_%s_masked_%s_dice.pdf.pdf"%(task, roi, masked_comparison)))



# compare within with between
#for roi in rois:
#    for thr_method in thr_methods:
#        for task in tasks:
#            for contrast in getStatLabels(task):
#                if roi:
#                    masked_comparisons = [True]
#                else:
#                    masked_comparisons = [False, True]
#                for masked_comparison in masked_comparisons:
#                    exclude = []
#                    for exception in exceptions:
#                        if exception['task_name'] == task:
#                            exclude.append(exception['subject_id'])
#                    if task in exclude_subjects.keys():
#                        exclude += exclude_subjects[task]
#                    plot_between_within_box_plot(where=[('task_name',task), ('contrast_name',contrast), ('thr_method', thr_method), ('roi', roi), ('masked_comparison', masked_comparison)], 
#                                                  metric="dice", 
#                                                  exclude=('subject_id', exclude),
#                                                  filename = os.path.join(results_dir, "compare within with between", "%s_%s_%s_roi_%s_masked_%s_dice.pdf"%(task,contrast, thr_method, roi, masked_comparison)))
                    
#for roi in rois:
#    for thr_method in thr_methods:
#        for task in tasks:
#            for contrast in getStatLabels(task):
#                if roi:
#                    masked_comparisons = [True]
#                else:
#                    masked_comparisons = [False, True]
#                for masked_comparison in masked_comparisons:
#                    exclude = []
#                    for exception in exceptions:
#                        if exception['task_name'] == task:
#                            exclude.append(exception['subject_id'])
#                    if task in exclude_subjects.keys():
#                        exclude += exclude_subjects[task]
#                    plot_between_within_box_plot(where=[('task_name',task), ('contrast_name',contrast), ('thr_method', thr_method), ('roi', roi), ('masked_comparison', masked_comparison)], 
#                                                  metric="distance", 
#                                                  exclude=('subject_id', exclude),
#                                                  filename = os.path.join(results_dir, "compare within with between", "%s_%s_%s_roi_%s_masked_%s_distance.pdf"%(task,contrast, thr_method, roi, masked_comparison)))
                    
#                plot_between_within_box_plot(where=[('task_name',task), ('contrast_name',contrast), ('thr_method', thr_method), ('roi', roi)], 
#                                              metric="jaccard", 
#                                              filename = os.path.join(results_dir, "compare within with between", "%s_%s_%s_roi_%s_jaccard.pdf"%(task,contrast, thr_method, roi)))
# compare covert with overt
for roi in rois:
    for thr_method in ['topo_ggmm', 'topo_fdr']:
        if roi:
            masked_comparisons = [True]
        else:
            masked_comparisons = [False, True]
        for masked_comparison in masked_comparisons:
            exclude = []
            for task in ["covert_verb_generation", "overt_verb_generation"]:
                for exception in exceptions:
                    if exception['task_name'] == task:
                        exclude.append(exception['subject_id'])
                if task in exclude_subjects.keys():
                    exclude += exclude_subjects[task]
            plot_between_session_box_plot(where=[('thr_method',thr_method), ('roi', roi), ('masked_comparison', masked_comparison)], 
                                          metric="dice", 
                                          compare= ('task_name',["overt_verb_generation", "covert_verb_generation"]),
                                          exclude=('subject_id', exclude), 
                                          filename = os.path.join(results_dir, "compare covert_verb_generation with overt_verb_generation", "%s_roi_%s_masked_%s_dice.pdf"%(thr_method, roi, masked_comparison)))
            
#for roi in rois:
#    for thr_method in ['topo_ggmm', 'topo_fdr']:
#        if roi:
#            masked_comparisons = [True]
#        else:
#            masked_comparisons = [False, True]
#        for masked_comparison in masked_comparisons:
#            exclude = []
#            for task in ["covert_verb_generation", "overt_verb_generation"]:
#                for exception in exceptions:
#                    if exception['task_name'] == task:
#                        exclude.append(exception['subject_id'])
#                if task in exclude_subjects.keys():
#                    exclude += exclude_subjects[task]
#            plot_between_session_box_plot(where=[('thr_method',thr_method), ('roi', roi), ('masked_comparison', masked_comparison)], 
#                                          metric="distance", 
#                                          compare= ('task_name',["overt_verb_generation", "covert_verb_generation"]),
#                                          exclude=('subject_id', exclude), 
#                                          filename = os.path.join(results_dir, "compare covert_verb_generation with overt_verb_generation", "%s_roi_%s_masked_%s_distance.pdf"%(thr_method, roi, masked_comparison)))

#for roi in rois:
#    for task in tasks:
#        for thr_method in ['topo_ggmm', 'topo_fdr']:
#            if roi:
#                masked_comparisons = [True]
#            else:
#                masked_comparisons = [False, True]
#            for masked_comparison in masked_comparisons:
#                exclude = []
#                for exception in exceptions:
#                    if exception['task_name'] == task:
#                        exclude.append(exception['subject_id'])
#                if task in exclude_subjects.keys():
#                    exclude += exclude_subjects[task]
#                print task
#                plot_between_session_box_plot(where=[('thr_method',thr_method), ('roi', roi), ('masked_comparison', masked_comparison), ('task_name', task)], 
#                                              metric="distance", 
#                                              compare= ('contrast_name',sorted(getStatLabels(task))),
#                                              exclude=('subject_id', exclude), 
#                                              test=False,
#                                              filename = os.path.join(results_dir, "compare distance", "%s_task_%s_roi_%s_masked_%s_distance.pdf"%(thr_method, task,roi, masked_comparison)))

#
##compare contrasts within subjects
#for roi in rois:
#    for task in [task for task in tasks if len(getStatLabels(task)) > 1]:
#        for thr_method in ['topo_ggmm', 'topo_fdr']:
#            plot_between_session_box_plot(where=[('task_name',task), ('thr_method',thr_method), ('roi', roi)], 
#                                          metric="dice", 
#                                          compare= ('contrast_name',sorted(getStatLabels(task))), 
#                                          filename = os.path.join(results_dir,"compare contrasts within subjects", "%s_%s_roi_%s_dice.pdf"%(task,thr_method, roi)))
#            plot_between_session_box_plot(where=[('task_name',task), ('thr_method',thr_method), ('roi', roi)], 
#                                          metric="jaccard", 
#                                          compare= ('contrast_name',sorted(getStatLabels(task))), 
#                                          filename = os.path.join(results_dir, "compare contrasts within subjects", "%s_%s_roi_%s_jaccard.pdf"%(task,thr_method, roi)))
#
##compare contrasts between subjects
#for roi in rois:
#    for task in [task for task in tasks if len(getStatLabels(task)) > 1]:
#        for thr_method in ['topo_ggmm', 'topo_fdr']:
#            plot_between_subjects_box_plot(where=[('task_name',task), ('thr_method',thr_method), ('roi', roi)], 
#                                          metric="dice", 
#                                          compare= ('contrast_name',sorted(getStatLabels(task))), 
#                                          filename = os.path.join(results_dir, "compare contrasts between subjects", "%s_%s_roi_%s_dice.pdf"%(task,thr_method, roi)))
#            plot_between_subjects_box_plot(where=[('task_name',task), ('thr_method',thr_method), ('roi', roi)], 
#                                          metric="jaccard", 
#                                          compare= ('contrast_name',sorted(getStatLabels(task))), 
#                                          filename = os.path.join(results_dir,"compare contrasts between subjects", "%s_%s_roi_%s_jaccard.pdf"%(task,thr_method, roi)))
#plt.show()