import pydevd
pydevd.set_pm_excepthook()

import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.algorithms.misc as misc

import neuroutils
from StringIO import StringIO
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import results_dir,working_dir, dbfile, subjects, tasks, thr_methods, getStatLabels, roi

subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                              name="subjects_infosource")
subjects_infosource.iterables = ('subject_id', subjects)

tasks_infosource = pe.Node(interface=util.IdentityInterface(fields=['task_name']),
                           name="tasks_infosource")
tasks_infosource.iterables = ('task_name', tasks)

thr_method_infosource = pe.Node(interface=util.IdentityInterface(fields=['thr_method']),
                              name="thr_method_infosource")
thr_method_infosource.iterables = ('thr_method', thr_methods)

roi_infosource = pe.Node(interface=util.IdentityInterface(fields=['roi']),
                              name="roi_infosource")
roi_infosource.iterables = ('roi', roi)

compare_datagrabber = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'thr_method', 'roi'],
                                               outfields=['first_map', 'second_map', 'T1']),
                     name = 'compare_datagrabber')

compare_datagrabber.inputs.base_directory = os.path.join(results_dir, "volumes")
compare_datagrabber.inputs.template = 't_maps/thresholded/_subject_id_%s/_session_%s/_task_name_%s/_roi_%s/_thr_method_%s/*.img'
compare_datagrabber.inputs.field_template = dict(T1= 'T1/_subject_id_%s/*.nii')
compare_datagrabber.inputs.template_args = dict(first_map = [['subject_id', 'first', 'task_name', 'roi','thr_method']],
                                                second_map = [['subject_id', 'second', 'task_name', 'roi','thr_method']],
                                                T1 = [['subject_id']])
compare_datagrabber.inputs.sort_filelist = True
compare_datagrabber.overwrite = True

def _make_titles(dice, jaccard, volume, contrast, subject_id, prefix=''):
    return prefix + " %s: dice = %f, jaccard = %f, volume = %d, subject_id = %s"%(contrast, dice, jaccard, volume, subject_id.split('-')[0])

compare_thresholded_maps = pe.MapNode(interface=misc.Overlap(), name="compare_thresholded_maps", iterfield=['volume1', 'volume2'])
plot_diff = pe.MapNode(interface=neuroutils.Overlay(overlay_range = (1, 3)), name="plot", iterfield=['overlay', 'title'])
make_titles_diff = pe.MapNode(interface=util.Function(input_names=['dice', 'jaccard', 'volume', 'contrast', 'subject_id', 'prefix'], 
                                                 output_names=['title'], 
                                                 function=_make_titles), name="make_titles_diff", iterfield=['dice', 'jaccard', 'volume', 'contrast'], overwrite = True)

sqlitesink = pe.MapNode(interface = SQLiteSink(input_names=["subject_id", 
                                                            'task_name', 
                                                            'contrast_name', 
                                                            'dice', 
                                                            'jaccard', 
                                                            'volume_difference', 
                                                            'thr_method',
                                                            'roi']), 
                        name="sqlitesink", 
                        iterfield=["contrast_name", "dice", 'jaccard', 'volume_difference'])
sqlitesink.inputs.database_file = dbfile
sqlitesink.inputs.table_name = "reliability2010_within_subjects"

datasink = pe.Node(interface = DataSink(), name='datasink')
datasink.inputs.base_directory = results_dir
datasink.inputs.regexp_substitutions = [
                                        #(r'(?P<root>/home/filo/workspace/2010reliability/results/)(?P<b1>.*)(?P<subject_id>_subject_id.*/)(?P<b2>.*)(?P<task_name>_task_name.*/)(?P<b3>.*)',
                                        # r'\g<root>\g<task_name>\g<b1>\g<b2>\g<subject_id>\g<b3>'),
                                        (r'(?P<r1>_[^-/]*)(?P<id>[0-9]+)(?P<r2>[/])', r'/\g<id>'),
                                        #(r'_task_name_', r''),
                                        #(r'(?P<subject_id>_subject_id[^/]*)([/])', r'\g<subject_id>_')
                                        ]

within_subjects_pipeline = pe.Workflow(name="within_subjects_pipeline")
within_subjects_pipeline.base_dir = working_dir
within_subjects_pipeline.connect([(subjects_infosource, compare_datagrabber, [('subject_id', 'subject_id')]),
                          (tasks_infosource, compare_datagrabber, [('task_name', 'task_name')]),
                          (roi_infosource, compare_datagrabber, [('roi', 'roi')]),
                          (thr_method_infosource, compare_datagrabber, [('thr_method', 'thr_method')]),
                          (compare_datagrabber, compare_thresholded_maps, [('first_map', 'volume1'),
                                                                           ('second_map', 'volume2')]),
                          
                          (compare_thresholded_maps, sqlitesink, [('dice', "dice",),
                                                                  ('jaccard', 'jaccard'),
                                                                  ('volume_difference', 'volume_difference')]),
                          (subjects_infosource, sqlitesink, [('subject_id', 'subject_id')]),
                          (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
                                                          (('task_name', getStatLabels), 'contrast_name')]),
                          (thr_method_infosource, sqlitesink, [('thr_method','thr_method')]),
                          (roi_infosource, sqlitesink, [('roi', 'roi')]),
                          
                          (compare_thresholded_maps, plot_diff, [('diff_file', "overlay")]),
                          (compare_datagrabber, plot_diff, [('T1', 'background')]),
                          (compare_thresholded_maps, make_titles_diff, [('dice', 'dice'),
                                                                        ('jaccard', 'jaccard'),
                                                                        ('volume_difference', 'volume')]),
                          (tasks_infosource, make_titles_diff, [(('task_name', getStatLabels), 'contrast')]),
                          (subjects_infosource, make_titles_diff, [('subject_id', 'subject_id')]),
                          (thr_method_infosource, make_titles_diff, [('thr_method', 'prefix')]),
                          (make_titles_diff, plot_diff, [('title', 'title')]),
                          (plot_diff, datasink, [('plot', 'reports.within_subjects.difference_maps')]),
])

if __name__ == '__main__':
    within_subjects_pipeline.run(plugin_args={'n_procs': 4})
    #within_subjects_pipeline.write_graph()