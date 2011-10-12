from variables import tasks, getStatLabels, dbfile, thr_methods, exceptions,\
    exclude_subjects
import sqlite3
import sys
from xlwt import Workbook,Style
wb = Workbook()
ws = wb.add_sheet('topo_fdr topo_ggmm')
row_counter = 0

conn = sqlite3.connect(dbfile)
c = conn.cursor()
for task in tasks:
    for contrast in getStatLabels(task):
        ws.write_merge(row_counter,row_counter,0, 4,"task: %s contrast: %s"%(task, contrast))
        row_counter += 1
#        ws.write_merge(row_counter,row_counter,1,4, 'Dice')
#        ws.write_merge(row_counter,row_counter,5,8, 'Hausdorff')
#        row_counter += 1
        ws.write_merge(row_counter,row_counter,1,2, 'hmedian')
        ws.write_merge(row_counter,row_counter,3,4, 'tmean')
#        ws.write_merge(row_counter,row_counter,5,6, 'hmedian')
#        ws.write_merge(row_counter,row_counter,7,8, 'tmean')
#        out_file.write(",hdmedian,, IQR,, tmean,, winsorized_variance,\n")
        row_counter += 1
        ws.row(row_counter).write(1, 'ROI')
        ws.row(row_counter).write(2, 'full')
        ws.row(row_counter).write(3, 'ROI')
        ws.row(row_counter).write(4, 'full')
#        ws.row(row_counter).write(5, 'ROI')
#        ws.row(row_counter).write(6, 'full')
#        ws.row(row_counter).write(7, 'ROI')
#        ws.row(row_counter).write(8, 'full')
#        out_file.write(",ROI, full, ROI, full, ROI, full, ROI, full,\n")
        for i, name in enumerate(['topo_fdr', 'topo_ggmm', 'CI', 'p (q)']):
            col_counter = 0
            row_counter += 1
            ws.row(row_counter).write(col_counter, "%s"%name)
            #out_file.write("%s, "%name)
            for metric in ['dice']:
                for parameter in ['hdmedian', 'tmean']:
                    for masked_comparison in [True, False]:
                        if name == 'p (q)':
                            c.execute("select twosided_p, twosided_q from comparisons  where name_1 = 'topo_fdr'  and contrast_name = '%s' and task_name = '%s' and masked_comparison = %d and parameter = '%s' and metric = '%s'"%(contrast, task, int(masked_comparison), parameter, metric))
                        elif name == 'CI':
                            c.execute("select ci_l, ci_h from comparisons  where name_1 = 'topo_fdr'  and contrast_name = '%s' and task_name = '%s' and masked_comparison = %d and parameter = '%s' and metric = '%s'"%(contrast, task, int(masked_comparison), parameter, metric))
                        else:
                            c.execute("select value_%d from comparisons  where name_%d = '%s'  and contrast_name = '%s' and task_name = '%s' and masked_comparison = %d and parameter = '%s' and metric = '%s'"%(i+1, i+1, name, contrast, task, int(masked_comparison), parameter, metric))
                        val = c.fetchall()
                        col_counter += 1
                        if len(val) == 0 or val[0][0] == None:
                            ws.row(row_counter).write(col_counter, "N/A")
                            continue
                        
                        if name == 'CI':
                            ws.row(row_counter).write(col_counter, "[%f %f]"%(val[0][0], val[0][1]))
                        elif name == 'p (q)' and val[0][1] != None:
                            ws.row(row_counter).write(col_counter, "%f (%f)"%(val[0][0], val[0][1]))
                        else:
                            ws.row(row_counter).write(col_counter, "%f"%val[0][0])
                        #out_file.write("%f,"%val[0][0])
        row_counter += 1

ws = wb.add_sheet('within_between')
row_counter = 0
            
for task in tasks:
    for contrast in getStatLabels(task):
        ws.write_merge(row_counter,row_counter,0, 4,"task: %s contrast: %s"%(task, contrast))
        row_counter += 1
        ws.write_merge(row_counter,row_counter,1,2, 'hmedian')
        ws.write_merge(row_counter,row_counter,3,4, 'tmean')
#        out_file.write(",hdmedian,, IQR,, tmean,, winsorized_variance,\n")
        row_counter += 1
        ws.row(row_counter).write(1, 'ROI')
        ws.row(row_counter).write(2, 'full')
        ws.row(row_counter).write(3, 'ROI')
        ws.row(row_counter).write(4, 'full')
#        out_file.write(",ROI, full, ROI, full, ROI, full, ROI, full,\n")
        for i, name in enumerate(['within', 'between', 'CI', 'p (q)']):
            col_counter = 0
            row_counter += 1
            ws.row(row_counter).write(col_counter, "%s"%name)
            #out_file.write("%s, "%name)
            for parameter in ['hdmedian', 'tmean']:
                for masked_comparison in [True, False]:
                    if name == 'p (q)':
                        c.execute("select twosided_p, twosided_q from comparisons  where name_1 = 'within'  and contrast_name = '%s' and task_name = '%s' and masked_comparison = %d and parameter = '%s'"%(contrast, task, int(masked_comparison), parameter))
                    elif name == 'CI':
                        c.execute("select ci_l, ci_h from comparisons  where name_1 = 'within'  and contrast_name = '%s' and task_name = '%s' and masked_comparison = %d and parameter = '%s'"%(contrast, task, int(masked_comparison), parameter))
                    else:
                        c.execute("select value_%d from comparisons  where name_%d = '%s'  and contrast_name = '%s' and task_name = '%s' and masked_comparison = %d and parameter = '%s'"%(i+1, i+1, name, contrast, task, int(masked_comparison), parameter))
                    val = c.fetchall()
                    print val
                    col_counter += 1
                    if len(val) == 0 or val[0][0] == None:
                        ws.row(row_counter).write(col_counter, "N/A")
                        continue
                    if name == 'CI':
                        ws.row(row_counter).write(col_counter, "[%f %f]"%(val[0][0], val[0][1]))
                    elif name == 'p (q)' and val[0][1] != None:
                        ws.row(row_counter).write(col_counter, "%f (%f)"%(val[0][0], val[0][1]))
                    else:
                        ws.row(row_counter).write(col_counter, "%f"%val[0][0])
                    #out_file.write("%f,"%val[0][0])
        row_counter += 1
        
ws = wb.add_sheet('success_or_failure')
row_counter = 0
col_counter = 0
ws.write_merge(row_counter,row_counter+1,0, 0,"Task")
col_counter += 1
for session in ['Ses 1', 'Ses 2']:
    ws.write_merge(row_counter,row_counter, col_counter, col_counter+1,session)
    for thr_method in thr_methods:
        ws.row(row_counter+1).write(col_counter, thr_method)
        col_counter += 1
    
row_counter += 2
for task in tasks:
    for contrast in getStatLabels(task):
        col_counter = 0
        ws.row(row_counter).write(col_counter, task + " " + contrast)
        col_counter += 1
        for session in [">", "<"]:
            for thr_method in thr_methods:
                exclude = []
                for exception in exceptions:
                    if exception['task_name'] == task and {'>':'first','<':'second'}[session] == exception['which']:
                        exclude.append(exception['subject_id'])
                if task in exclude_subjects.keys():
                    exclude += exclude_subjects[task]
                c.execute("SELECT count(*) from reliability2010_within_subjects where thr_method='%s' and masked_comparison=1 and task_name='%s' and contrast_name='%s' and (dice != 0 or volume_difference %s 0) and subject_id not in (%s)"%(thr_method, task, contrast, session, 
                                                                                                                                                                                                                                               ",".join(["'%s'"%s for s in exclude])))
                count = int(c.fetchall()[0][0])
                c.execute("SELECT count(*) from reliability2010_within_subjects where thr_method='%s' and masked_comparison=1 and task_name='%s' and contrast_name='%s' and subject_id not in (%s)"%(thr_method, task, contrast,",".join(["'%s'"%s for s in exclude])))
                total = int(c.fetchall()[0][0])   
                print total                                                                                                                                                                                                                            
                ws.row(row_counter).write(col_counter, float(count)/float(total))
                col_counter += 1
        row_counter += 1
        
        
ws = wb.add_sheet('covert_vs_overt')
row_counter = 0
col_counter = 0
ws.write_merge(row_counter,row_counter+1,0, 0,"Task")
col_counter += 1
for session in ['Ses 1', 'Ses 2']:
    ws.write_merge(row_counter,row_counter, col_counter, col_counter+1,session)
    for thr_method in thr_methods:
        ws.row(row_counter+1).write(col_counter, thr_method)
        col_counter += 1
    
row_counter += 2
for task in tasks:
    for contrast in getStatLabels(task):
        col_counter = 0
        ws.row(row_counter).write(col_counter, task + " " + contrast)
        col_counter += 1
        for session in [">", "<"]:
            for thr_method in thr_methods:
                exclude = []
                for exception in exceptions:
                    if exception['task_name'] == task and {'>':'first','<':'second'}[session] == exception['which']:
                        exclude.append(exception['subject_id'])
                if task in exclude_subjects.keys():
                    exclude += exclude_subjects[task]
                c.execute("SELECT count(*) from reliability2010_within_subjects where thr_method='%s' and masked_comparison=1 and task_name='%s' and contrast_name='%s' and (dice != 0 or volume_difference %s 0) and subject_id not in (%s)"%(thr_method, task, contrast, session, 
                                                                                                                                                                                                                                               ",".join(["'%s'"%s for s in exclude])))
                count = int(c.fetchall()[0][0])
                c.execute("SELECT count(*) from reliability2010_within_subjects where thr_method='%s' and masked_comparison=1 and task_name='%s' and contrast_name='%s' and subject_id not in (%s)"%(thr_method, task, contrast,",".join(["'%s'"%s for s in exclude])))
                total = int(c.fetchall()[0][0])   
                print total                                                                                                                                                                                                                            
                ws.row(row_counter).write(col_counter, float(count)/float(total))
                col_counter += 1
        row_counter += 1
wb.save("/home/filo/Dropbox/PhD/thesis/chapter_4_figures/comparison_table.xls")