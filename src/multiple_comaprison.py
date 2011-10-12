from variables import tasks, getStatLabels, dbfile, thr_methods, exceptions,\
    exclude_subjects
import sqlite3
import sys
from scikits.statsmodels.stats.multicomp import multipletests


def fdr_correct(where_clauses):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    print len(where_clauses)
    p_vals = []
    for where_clause in where_clauses:
        c.execute("select twosided_p from comparisons where " + where_clause)
        val = c.fetchall()
        assert len(val) == 1
        where_clause
        p_vals.append(val[0][0])
    
    _, q_vals, _, _ = multipletests(p_vals, alpha=0.05, method='fdr_bh', returnsorted=False)
    
    for i, where_clause in enumerate(where_clauses):
        c.execute("update comparisons set twosided_q=%f where " % q_vals[i] + where_clause)
    
    conn.commit()
    c.close()

where_clauses = ["name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'covert_verb_generation' and contrast_name = 'Task' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'covert_verb_generation' and contrast_name = 'Task' and masked_comparison=0",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'covert_verb_generation' and contrast_name = 'Task' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'covert_verb_generation' and contrast_name = 'Task' and masked_comparison=0",
                 
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'overt_verb_generation' and contrast_name = 'Task' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'overt_verb_generation' and contrast_name = 'Task' and masked_comparison=0",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'overt_verb_generation' and contrast_name = 'Task' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'overt_verb_generation' and contrast_name = 'Task' and masked_comparison=0",
                 
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'overt_word_repetition' and contrast_name = 'Task' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'overt_word_repetition' and contrast_name = 'Task' and masked_comparison=0",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'overt_word_repetition' and contrast_name = 'Task' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'overt_word_repetition' and contrast_name = 'Task' and masked_comparison=0",
                 
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'finger_foot_lips' and contrast_name = 'Finger_vs_Other' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'finger_foot_lips' and contrast_name = 'Finger_vs_Other' and masked_comparison=0",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'finger_foot_lips' and contrast_name = 'Finger_vs_Other' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'finger_foot_lips' and contrast_name = 'Finger_vs_Other' and masked_comparison=0",
                 
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'finger_foot_lips' and contrast_name = 'Foot_vs_Other' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'finger_foot_lips' and contrast_name = 'Foot_vs_Other' and masked_comparison=0",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'finger_foot_lips' and contrast_name = 'Foot_vs_Other' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'finger_foot_lips' and contrast_name = 'Foot_vs_Other' and masked_comparison=0",
                 
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'finger_foot_lips' and contrast_name = 'Lips_vs_Other' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'finger_foot_lips' and contrast_name = 'Lips_vs_Other' and masked_comparison=0",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'finger_foot_lips' and contrast_name = 'Lips_vs_Other' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'finger_foot_lips' and contrast_name = 'Lips_vs_Other' and masked_comparison=0",
                 
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'line_bisection' and contrast_name = 'Task_Answered_Greater_Than_Control_Answered' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'hdmedian' and task_name = 'line_bisection' and contrast_name = 'Task_Answered_Greater_Than_Control_Answered' and masked_comparison=0",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'line_bisection' and contrast_name = 'Task_Answered_Greater_Than_Control_Answered' and masked_comparison=1",
                 "name_1 = 'topo_fdr' and metric = 'dice' and parameter = 'tmean' and task_name = 'line_bisection' and contrast_name = 'Task_Answered_Greater_Than_Control_Answered' and masked_comparison=0",]

fdr_correct(where_clauses)

for task in tasks:
    for contrast in getStatLabels(task):
        if contrast not in ['Task_Correct_Greater_Than_Task_Incorrect']:
            where_clauses = ["name_1 = 'within' and metric = 'dice' and parameter = 'hdmedian' and task_name = '%s' and contrast_name = '%s' and masked_comparison=1"%(task, contrast),
                             "name_1 = 'within' and metric = 'dice' and parameter = 'hdmedian' and task_name = '%s' and contrast_name = '%s' and masked_comparison=0"%(task, contrast),
                             "name_1 = 'within' and metric = 'dice' and parameter = 'tmean' and task_name = '%s' and contrast_name = '%s' and masked_comparison=1"%(task, contrast),
                             "name_1 = 'within' and metric = 'dice' and parameter = 'tmean' and task_name = '%s' and contrast_name = '%s' and masked_comparison=0"%(task, contrast)]
            fdr_correct(where_clauses)
