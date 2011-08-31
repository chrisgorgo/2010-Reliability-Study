import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.algorithms.misc as misc

import neuroutils
from StringIO import StringIO
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import results_dir,working_dir, dbfile, subjects, tasks, thr_methods, getStatLabels, roi
from pipeline import getMaskFile, getDilation
from nipype.interfaces import spm
from nipype.interfaces.traits_extension import Undefined

subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                              name="subjects_infosource")
subjects_infosource.iterables = ('subject_id', subjects)

tasks_infosource = pe.Node(interface=util.IdentityInterface(fields=['task_name']),
                           name="tasks_infosource")
tasks_infosource.iterables = ('task_name', tasks)

thr_method_infosource = pe.Node(interface=util.IdentityInterface(fields=['thr_method']),
                              name="thr_method_infosource")
thr_method_infosource.iterables = ('thr_method', thr_methods)

compare_datagrabber = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'thr_method', 'roi'],
                                               outfields=['first_map', 'second_map', 'T1']),
                     name = 'compare_datagrabber', overwrite=True)

compare_datagrabber.inputs.base_directory = '/media/data/2010reliability/workdir_fmri/group/first_level/'
compare_datagrabber.inputs.template = 'main/model/%s/_subject_id_%s/_session_%s/_task_name_%s/*topo_fdr/mapflow/*_topo_fdr*/*_map_thr.img'
compare_datagrabber.inputs.field_template = dict(T1= 'preproc/realign_and_coregister/_subject_id_%s/average_T1s/*.nii')
compare_datagrabber.inputs.template_args = dict(first_map = [['thr_method', 'subject_id', 'first', 'task_name']],
                                                second_map = [['thr_method', 'subject_id', 'second', 'task_name']],
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
                                                            'roi',
                                                            'masked_comparison']), 
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


compare_datagrabber.inputs.roi = True
sqlitesink.inputs.roi = True
sqlitesink.inputs.masked_comparison = True

def trans_thr_method(thr_method):
    if thr_method == "topo_ggmm":
        return "threshold_topo_ggmm"
    else:
        return ""

within_subjects_pipeline = pe.Workflow(name="within_subjects_pipeline_roi")
within_subjects_pipeline.base_dir = working_dir
within_subjects_pipeline.connect([(subjects_infosource, compare_datagrabber, [('subject_id', 'subject_id')]),
                          (tasks_infosource, compare_datagrabber, [('task_name', 'task_name')]),
                          (thr_method_infosource, compare_datagrabber, [(('thr_method', trans_thr_method), 'thr_method')]),
                          (compare_datagrabber, compare_thresholded_maps, [('first_map', 'volume1'),
                                                                           ('second_map', 'volume2')]),
                          
                          (compare_thresholded_maps, sqlitesink, [('dice', "dice",),
                                                                  ('jaccard', 'jaccard'),
                                                                  ('volume_difference', 'volume_difference')]),
                          (subjects_infosource, sqlitesink, [('subject_id', 'subject_id')]),
                          (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
                                                          (('task_name', getStatLabels), 'contrast_name')]),
                          (thr_method_infosource, sqlitesink, [('thr_method','thr_method')]),
                          
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


within_subjects_pipeline_noroi = within_subjects_pipeline.clone(name="within_subjects_pipeline_noroi")

tasks_infosource = within_subjects_pipeline_noroi.get_node("tasks_infosource")

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
within_subjects_pipeline_noroi.connect([(tasks_infosource, dilate_roi_mask, [(('task_name', getMaskFile), 'filename'),
                                                                             (('task_name', getDilation), 'dilation_size')]),
                                        
                                        (dilate_roi_mask, reslice_roi_mask, [('dilated_file',"source")]),
               ])

compare_datagrabber = within_subjects_pipeline_noroi.get_node("compare_datagrabber")
sqlitesink = within_subjects_pipeline_noroi.get_node("sqlitesink")
compare_thresholded_maps = within_subjects_pipeline_noroi.get_node("compare_thresholded_maps")

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

within_subjects_pipeline_noroi.connect([(reslice_roi_mask, select_mask, [(('coregistered_source', prepend_by_undefiend),'inlist')]),
                                        (masked_comparison_infosource, select_mask, [(('masked_comparison', chooseindex_bool),'index')]),
                                        (select_mask, compare_thresholded_maps, [('out', 'mask_volume')]),
                                        (masked_comparison_infosource, sqlitesink, [('masked_comparison', 'masked_comparison'),
                                                                                    (('masked_comparison',return_false), 'roi')])])

if __name__ == '__main__':
    within_subjects_pipeline_noroi.run(plugin_args={'n_procs': 4})
    within_subjects_pipeline_noroi.write_graph()
    #within_subjects_pipeline.run(plugin_args={'n_procs': 4})
    #within_subjects_pipeline.write_graph()

