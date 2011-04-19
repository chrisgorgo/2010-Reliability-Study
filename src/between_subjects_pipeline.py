import pydevd
pydevd.set_pm_excepthook()

import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.algorithms.misc as misc

import neuroutils
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import results_dir,working_dir, dbfile, subjects, tasks, thr_methods, sessions, getStatLabels, config

tasks_infosource = pe.Node(interface=util.IdentityInterface(fields=['task_name']),
                           name="tasks_infosource")
tasks_infosource.iterables = ('task_name', tasks)

thr_method_infosource = pe.Node(interface=util.IdentityInterface(fields=['thr_method']),
                              name="thr_method_infosource")
thr_method_infosource.iterables = ('thr_method', thr_methods)

sessions_infosource = pe.Node(interface=util.IdentityInterface(fields=['session']),
                              name="sessions_infosource")
sessions_infosource.iterables = ('session', sessions)

datasink = pe.Node(interface = DataSink(), name='datasink')
datasink.inputs.base_directory = results_dir
datasink.inputs.regexp_substitutions = [
                                #(r'(?P<root>/home/filo/workspace/2010reliability/results/)(?P<b1>.*)(?P<subject_id>_subject_id.*/)(?P<b2>.*)(?P<task_name>_task_name.*/)(?P<b3>.*)',
                                # r'\g<root>\g<task_name>\g<b1>\g<b2>\g<subject_id>\g<b3>'),
                                (r'(?P<r1>_[^-/]*)(?P<id>[0-9]+)(?P<r2>[/])', r'/\g<id>'),
                                #(r'_task_name_', r''),
                                #(r'(?P<subject_id>_subject_id[^/]*)([/])', r'\g<subject_id>_')
                                ]

between_subjects_pipeline = pe.Workflow(name="between_subjects_pipeline")
between_subjects_pipeline.base_dir = working_dir

for i, subject_id1 in enumerate(subjects):
    for i, subject_id2 in enumerate(subjects[i+1:]):
        datagrabber = pe.Node(interface=nio.DataGrabber(infields=['subject_id1', 'subject_id2', 'task_name', 'thr_method', 'session'],
                                               outfields=['map', 'T1']),
                     name = 'datagrabber' + "_%s_vs_%s"%(subject_id1.split('-')[0], subject_id2.split('-')[0]))

        datagrabber.inputs.base_directory = os.path.join(results_dir, "volumes")
        datagrabber.inputs.template = 't_maps/thresholded/_subject_id_%s/_session_%s/_task_name_%s/_thr_method_%s/*.img'
        datagrabber.inputs.field_template = dict(T1= 'T1/_subject_id_%s/*.nii')
        datagrabber.inputs.template_args = dict(map1 = [['subject_id1', 'session', 'task_name', 'thr_method']],
                                                 map2 = [['subject_id2', 'session', 'task_name', 'thr_method']],
                                                 T1 = [['subject_id1']])
        datagrabber.inputs.sort_filelist = True
        datagrabber.inputs.subject_id1 =subject_id1
        datagrabber.inputs.subject_id2 =subject_id2
        
        compare_thresholded_maps = pe.MapNode(interface=misc.Overlap(), name="compare_thresholded_maps"+ "_%s_vs_%s"%(subject_id1.split('-')[0], subject_id2.split('-')[0]), iterfield=['volume1', 'volume2'])
        plot_diff = pe.MapNode(interface=neuroutils.Overlay(overlay_range = (1, 3)), name="plot"+ "_%s_vs_%s"%(subject_id1.split('-')[0], subject_id2.split('-')[0]), iterfield=['overlay', 'title'])
        
        def _make_titles(dice, jaccard, contrast, subject_id1, subject_id2, prefix=''):
            return prefix + " %s: dice = %f, jaccard = %f, subject_id1 = %s, subject_id2 = %s"%(contrast, dice, jaccard, subject_id1.split('-')[0], subject_id2.split('-')[0])
        
        make_titles_diff = pe.MapNode(interface=util.Function(input_names=['dice', 'jaccard', 'contrast', 'prefix', 'subject_id1', 'subject_id2'], 
                                                         output_names=['title'], 
                                                         function=_make_titles), name="make_titles_diff"+ "_%s_vs_%s"%(subject_id1.split('-')[0], subject_id2.split('-')[0]), iterfield=['dice', 'jaccard', 'contrast'])
        make_titles_diff.inputs.subject_id1 = subject_id1
        make_titles_diff.inputs.subject_id2 = subject_id2
        
        sqlitesink = pe.MapNode(interface = SQLiteSink(input_names=["subject_id1", "subject_id2",
                                                                    "session",
                                                                    'task_name', 'contrast_name', 
                                                                    'dice', 'jaccard', 
                                                                    'volume_difference', 'thr_method']), 
                                name="sqlitesink"+ "_%s_vs_%s"%(subject_id1.split('-')[0], subject_id2.split('-')[0]), 
                                iterfield=["contrast_name", "dice", 'jaccard', 'volume_difference'])
        sqlitesink.inputs.database_file = dbfile
        sqlitesink.inputs.table_name = "reliability2010_between_subjects"
        sqlitesink.inputs.subject_id1 =subject_id1
        sqlitesink.inputs.subject_id2 = subject_id2
        
        between_subjects_pipeline.connect([
                                  (tasks_infosource, datagrabber, [('task_name', 'task_name')]),
                                  (thr_method_infosource, datagrabber, [('thr_method', 'thr_method')]),
                                  (sessions_infosource, datagrabber, [('session', 'session')]),
                          
                                  (datagrabber, compare_thresholded_maps, [('map1', 'volume1'),
                                                                           ('map2', 'volume2')]),
                          
                                  (compare_thresholded_maps, sqlitesink, [('dice', "dice",),
                                                                          ('jaccard', 'jaccard'),
                                                                          ('volume_difference', 'volume_difference')]),
                                  (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
                                                                  (('task_name', getStatLabels), 'contrast_name')]),
                                  (thr_method_infosource, sqlitesink, [('thr_method','thr_method')]),
                                  (sessions_infosource, sqlitesink, [('session', 'session')]),
                                  
                                  (compare_thresholded_maps, plot_diff, [('diff_file', "overlay")]),
                                  (datagrabber, plot_diff, [('T1', 'background')]),
                                  (compare_thresholded_maps, make_titles_diff, [('dice', 'dice'),
                                                                                ('jaccard', 'jaccard')]),
                                  (tasks_infosource, make_titles_diff, [(('task_name', getStatLabels), 'contrast')]),
                                  (thr_method_infosource, make_titles_diff, [('thr_method', 'prefix')]),
                                  (make_titles_diff, plot_diff, [('title', 'title')]),
                                  (plot_diff, datasink, [('plot', 'reports.between_subjects.difference_maps.' + "%s_vs_%s"%(subject_id1.split('-')[0], subject_id2.split('-')[0]))])
                          ])
        
if __name__ == '__main__':
    between_subjects_pipeline.run(plugin_args={'n_procs': 4})
    #between_subjects_pipeline.run(plugin_args={'n_procs': 4})
    #between_subjects_pipeline.write_graph()