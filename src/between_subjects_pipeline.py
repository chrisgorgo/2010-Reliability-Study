#import pydevd
#pydevd.set_pm_excepthook()

import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.algorithms.misc as misc

import neuroutils
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import results_dir,working_dir, dbfile, subjects, tasks, thr_methods, sessions, getStatLabels, config, roi
from nipype.interfaces.traits_extension import Undefined
from nipype.interfaces import spm
from pipeline import getMaskFile, getDilation
from within_subjects_pipeline import chooseindex_bool
from within_run_pipeline import trans_thr_method

tasks_infosource = pe.Node(interface=util.IdentityInterface(fields=['task_name']),
                           name="tasks_infosource")
tasks_infosource.iterables = ('task_name', tasks)

thr_method_infosource = pe.Node(interface=util.IdentityInterface(fields=['thr_method']),
                              name="thr_method_infosource")
thr_method_infosource.iterables = ('thr_method', thr_methods)

sessions_infosource = pe.Node(interface=util.IdentityInterface(fields=['session']),
                              name="sessions_infosource")
sessions_infosource.iterables = ('session', sessions)

pairs=[]
for i, subject_id1 in enumerate(subjects):
    for subject_id2 in subjects[i+1:]:
        pairs.append((subject_id1, subject_id2))
        
compare_infosource = pe.Node(interface=util.IdentityInterface(fields=['compare']),
                              name="compare_infosource")
compare_infosource.iterables = ('compare', pairs)

datasink = pe.Node(interface = DataSink(), name='datasink')
datasink.inputs.base_directory = results_dir
datasink.inputs.regexp_substitutions = [
                                #(r'(?P<root>/home/filo/workspace/2010reliability/results/)(?P<b1>.*)(?P<subject_id>_subject_id.*/)(?P<b2>.*)(?P<task_name>_task_name.*/)(?P<b3>.*)',
                                # r'\g<root>\g<task_name>\g<b1>\g<b2>\g<subject_id>\g<b3>'),
                                (r'(?P<r1>_[^-/]*)(?P<id>[0-9]+)(?P<r2>[/])', r'/\g<id>'),
                                #(r'_task_name_', r''),
                                #(r'(?P<subject_id>_subject_id[^/]*)([/])', r'\g<subject_id>_')
                                ]

datagrabber = pe.Node(interface=nio.DataGrabber(infields=['subject_id1', 'subject_id2', 'task_name', 'thr_method', 'session'],
                                       outfields=['map1','map1', 'T1']),
             name = 'datagrabber', overwrite=True)

datagrabber.inputs.base_directory = '/media/data/2010reliability/workdir_fmri/group/first_level/'
datagrabber.inputs.template = 'main/model/%s/_subject_id_%s/_session_%s/_task_name_%s/*topo_fdr/mapflow/*_topo_fdr*/*_map_thr.img'
datagrabber.inputs.field_template = dict(T1= 'preproc/realign_and_coregister/_subject_id_%s/average_T1s/*.nii')
datagrabber.inputs.template_args = dict(map1 = [['thr_method', 'subject_id1', 'first', 'task_name']],
                                        map2 = [['thr_method', 'subject_id2', 'second', 'task_name']],
                                                T1 = [['subject_id1']])
datagrabber.inputs.sort_filelist = True
datagrabber.inputs.overwrite = True

compare_thresholded_maps = pe.MapNode(interface=misc.Overlap(), name="compare_thresholded_maps", iterfield=['volume1', 'volume2'])
thresholded_maps_distance = pe.MapNode(interface=misc.Distance(method="eucl_max"), 
                                       name="thresholded_maps_distance", 
                                       iterfield=['volume1', 'volume2'])
plot_diff = pe.MapNode(interface=neuroutils.Overlay(overlay_range = (1, 3)), name="plot", iterfield=['overlay', 'title'])

def _make_titles(dice, jaccard, contrast, subject_id1, subject_id2, prefix=''):
    return prefix + " %s: dice = %f, jaccard = %f, subject_id1 = %s, subject_id2 = %s"%(contrast, dice, jaccard, subject_id1.split('-')[0], subject_id2.split('-')[0])

make_titles_diff = pe.MapNode(interface=util.Function(input_names=['dice', 'jaccard', 'contrast', 'prefix', 'subject_id1', 'subject_id2'], 
                                                 output_names=['title'], 
                                                 function=_make_titles), name="make_titles_diff", iterfield=['dice', 'jaccard', 'contrast'])

sqlitesink = pe.MapNode(interface = SQLiteSink(input_names=["subject_id1", "subject_id2",
                                                            "session",
                                                            'task_name', 'contrast_name', 
                                                            'dice', 'jaccard', 
                                                            'volume_difference', 'thr_method', 'roi', 'masked_comparison']), 
                        name="sqlitesink", 
                        iterfield=["contrast_name", "dice", 'jaccard', 'volume_difference'])
sqlitesink.inputs.database_file = dbfile
sqlitesink.inputs.table_name = "reliability2010_between_subjects"

def pickFirst(l):
    return l[0]

def pickSecond(l):
    return l[1]

between_subjects_pipeline = pe.Workflow(name="between_subjects_pipeline_roi")
between_subjects_pipeline.base_dir = working_dir

datagrabber.inputs.roi = True
sqlitesink.inputs.roi = True
sqlitesink.inputs.masked_comparison = True

def trans_thr_method(thr_method):
    if thr_method == "topo_ggmm":
        return "threshold_topo_ggmm"
    else:
        return ""

between_subjects_pipeline.connect([
                          (tasks_infosource, datagrabber, [('task_name', 'task_name')]),
                          (thr_method_infosource, datagrabber, [(('thr_method', trans_thr_method), 'thr_method')]),
                          (sessions_infosource, datagrabber, [('session', 'session')]),
                          (compare_infosource, datagrabber, [(('compare', pickFirst), 'subject_id1'),
                                                             (('compare', pickSecond), 'subject_id2')]),
                  
                          (datagrabber, compare_thresholded_maps, [('map1', 'volume1'),
                                                                   ('map2', 'volume2')]),
                          (datagrabber, thresholded_maps_distance, [('map1', 'volume1'),
                                                                    ('map2', 'volume2')]),

                          (thresholded_maps_distance, sqlitesink, [('distance', "distance")]),
                  
                          (compare_thresholded_maps, sqlitesink, [('dice', "dice",),
                                                                  ('jaccard', 'jaccard'),
                                                                  ('volume_difference', 'volume_difference')]),
                          (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
                                                          (('task_name', getStatLabels), 'contrast_name')]),
                          (thr_method_infosource, sqlitesink, [('thr_method','thr_method')]),
                          (sessions_infosource, sqlitesink, [('session', 'session')]),
                          (compare_infosource, sqlitesink, [(('compare', pickFirst), 'subject_id1'),
                                                                  (('compare', pickSecond), 'subject_id2')]),
                                                             
                          (compare_thresholded_maps, plot_diff, [('diff_file', "overlay")]),
                          (datagrabber, plot_diff, [('T1', 'background')]),
                          (compare_thresholded_maps, make_titles_diff, [('dice', 'dice'),
                                                                        ('jaccard', 'jaccard')]),
                          (tasks_infosource, make_titles_diff, [(('task_name', getStatLabels), 'contrast')]),
                          (thr_method_infosource, make_titles_diff, [('thr_method', 'prefix')]),
                          (compare_infosource, make_titles_diff, [(('compare', pickFirst), 'subject_id1'),
                                                                  (('compare', pickSecond), 'subject_id2')]),
                                   
                          (make_titles_diff, plot_diff, [('title', 'title')]),
                          (plot_diff, datasink, [('plot', 'reports.between_subjects.difference_maps')])
                  ])
        
if __name__ == '__main__':
#    between_subjects_pipeline.run(plugin_args={'n_procs': 2})
    between_subjects_pipeline.write_graph()

between_subjects_pipeline_noroi = between_subjects_pipeline.clone(name="between_subjects_pipeline_noroi")
tasks_infosource = between_subjects_pipeline_noroi.get_node("tasks_infosource")

reslice_roi_mask = pe.Node(interface=spm.Coregister(), name="reslice_roi_mask")
reslice_roi_mask.inputs.jobtype="write"
reslice_roi_mask.inputs.write_interp = 0
reslice_roi_mask.inputs.target = "/media/data/2010reliability/normsize.img"
def dilateROIMask(filename, dilation_size):
    import numpy as np
    import nibabel as nb
    from scipy.ndimage.morphology import grey_dilation
    import os
    
    nii = nb.load(filename)
    origdata = nii.get_data()
    newdata = grey_dilation(origdata , (2 * dilation_size + 1,
                                       2 * dilation_size + 1,
                                       2 * dilation_size + 1))
    nb.save(nb.Nifti1Image(newdata, nii.get_affine(), nii.get_header()), 'dialted_mask.nii')
    return os.path.abspath('dialted_mask.nii')

dilate_roi_mask = pe.Node(interface=util.Function(input_names=['filename', 'dilation_size'], 
                                                  output_names=['dilated_file'],
                                                  function=dilateROIMask),
                          name = 'dilate_roi_mask')
between_subjects_pipeline_noroi.connect([(tasks_infosource, dilate_roi_mask, [(('task_name', getMaskFile), 'filename'),
                                                                             (('task_name', getDilation), 'dilation_size')]),
                                        
                                        (dilate_roi_mask, reslice_roi_mask, [('dilated_file',"source")]),
               ])

compare_datagrabber = between_subjects_pipeline_noroi.get_node("datagrabber")
sqlitesink = between_subjects_pipeline_noroi.get_node("sqlitesink")
compare_thresholded_maps = between_subjects_pipeline_noroi.get_node("compare_thresholded_maps")

compare_datagrabber.inputs.roi = False
sqlitesink.inputs.roi = False
sqlitesink.inputs.masked_comparison = Undefined

masked_comparison_infosource = pe.Node(interface=util.IdentityInterface(fields=['masked_comparison']),
                                       name="masked_comparison_infosource")
masked_comparison_infosource.iterables = [('masked_comparison', [True, False])]

select_mask = pe.Node(interface=util.Select(), name="select_mask")

def prepend_by_undefiend(object):
    from nipype.interfaces.traits_extension import Undefined
    return [Undefined, object]

def chooseindex_bool(roi):
    return {True:1, False:0}[roi]
def return_false(whatever):
    return False

between_subjects_pipeline_noroi.connect([(reslice_roi_mask, select_mask, [(('coregistered_source', prepend_by_undefiend),'inlist')]),
                                        (masked_comparison_infosource, select_mask, [(('masked_comparison', chooseindex_bool),'index')]),
                                        (select_mask, compare_thresholded_maps, [('out', 'mask_volume')]),
                                        (masked_comparison_infosource, sqlitesink, [('masked_comparison', 'masked_comparison'),
                                                                                    (('masked_comparison', return_false), 'roi')])])

if __name__ == '__main__':
    between_subjects_pipeline_noroi.run(plugin_args={'n_procs': 4})
    between_subjects_pipeline_noroi.write_graph()

