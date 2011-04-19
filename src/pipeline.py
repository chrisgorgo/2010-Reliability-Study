import pydevd
pydevd.set_pm_excepthook()

import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.algorithms.misc as misc
from helper_functions import (create_pipeline_functional_run, 
                                         create_dwi_pipeline,
                                         create_prepare_seeds_from_fmri_pipeline)
from nipype.interfaces.utility import Merge
import neuroutils
from nipype.utils.config import config
from StringIO import StringIO
from nipype.interfaces.io import DataSink, SQLiteSink

config.readfp(StringIO("""
[logging]
workflow_level = DEBUG
filemanip_level = DEBUG
interface_level = DEBUG

[execution]
stop_on_first_crash = true
stop_on_first_rerun = false
hash_method = timestamp
remove_unnecessary_outputs = false
#plugin = MultiProc
"""))


data_dir = '/media/data/2010reliability/data'
results_dir = "/home/filo/workspace/2010reliability/results"
working_dir = '/media/data/2010reliability/workdir'
dbfile = os.path.join(results_dir, "results.db")
tasks = ["finger_foot_lips"]#, 'overt_verb_generation', "overt_word_repetition", "covert_verb_generation", "line_bisection"]
thr_methods = ['topo_fdr','topo_ggmm']

subjects = ['08143633-aec2-49a9-81cf-45867827b871',
#            '3a3e1a6f-dc92-412c-870a-74e4f4e85ddb',
#            '8bb20980-2dc4-4da9-9065-879e2e7e1fbe',
#            '8d80a62b-aa21-49bd-b8ca-9bc678ffe7b0',
#            '90bafbe8-c67f-4388-b677-27fcf2427c71',
#            '94cfb26f-0060-4c44-b59f-702ca61143ca',
#            'c2cc1c59-df88-4366-9f99-73b722235789',
#            'cf48f394-1912-4202-89f7-dbf8ef9d6e19',
#            'df4808a4-ecce-4d0a-9fe2-535c0720ec17',
#            'e094aae5-8387-4b5c-bf56-df4a88623c5d',
            ]

info = dict(T1 = [['subject_id', 'session_id', 'co_COR_3D_IR_PREP']],
            func = [['subject_id', 'session_id', 'task_name']],
            #dwi = [['subject_id', 'session_id', '[0-9]_DTI_64G_2.0_mm_isotropic']],
            #dwi_bval = [['subject_id', 'session_id', '[0-9]_DTI_64G_2.0_mm_isotropic']],
            #dwi_bvec = [['subject_id', 'session_id', '[0-9]_DTI_64G_2.0_mm_isotropic']]
            )

subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                              name="subjects_infosource")
subjects_infosource.iterables = ('subject_id', subjects)

tasks_infosource = pe.Node(interface=util.IdentityInterface(fields=['task_name']),
                           name="tasks_infosource")
tasks_infosource.iterables = ('task_name', tasks)

thr_method_infosource = pe.Node(interface=util.IdentityInterface(fields=['thr_method']),
                              name="thr_method_infosource")
thr_method_infosource.iterables = ('thr_method', thr_methods)

first_session_datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'session_id'],
                                               outfields=info.keys()),
                     name = 'first_session_datasource')

first_session_datasource.inputs.base_directory = data_dir
first_session_datasource.inputs.template = '%s/%s/*%s*.nii'
#first_session_datasource.inputs.field_template = dict(T1= '%s/%s/%s/co*.img')
#                                                      #dwi_bval=first_session_datasource.inputs.template.replace("nii", "bval"),
#                                        #dwi_bvec=first_session_datasource.inputs.template.replace("nii", "bvec"),
#                                        func = '%s_*/*/*[0-9]_%s.nii'
#                                        )
first_session_datasource.inputs.template_args = info
first_session_datasource.inputs.sort_filelist = True

second_session_datasource = first_session_datasource.clone(name = 'second_session_datasource')

first_session_functional_run = create_pipeline_functional_run(name="first_session_functional_run", series_format="4d")
second_session_functional_run = first_session_functional_run.clone("second_session_functional_run")

def _make_titles(dice, jaccard, volume, contrast, subject_id, prefix=''):
    return prefix + "%s: dice = %f, jaccard = %f, volume = %d, subject_id = %s"%(contrast, dice, jaccard, volume, subject_id.split('-')[0])

compare_thresholded_maps = pe.MapNode(interface=misc.Dissimilarity(), name="compare_thresholded_maps", iterfield=['volume1', 'volume2', 'out_file'])
plot_diff = pe.MapNode(interface=neuroutils.Overlay(bbox=True, overlay_range = (1, 3)), name="plot", iterfield=['overlay', 'title'])
make_titles_diff = pe.MapNode(interface=util.Function(input_names=['dice', 'jaccard', 'volume', 'contrast', 'subject_id', 'prefix'], 
                                                 output_names=['title'], 
                                                 function=_make_titles), name="make_titles_diff", iterfield=['dice', 'jaccard', 'volume', 'contrast'], overwrite = True)

#compare_topo_fdr_thresholded_maps = compare_thresholded_maps.clone(name='compare_topo_fdr_thresholded_maps')
#plot_topo_fdr_diff = plot_diff.clone(name="plot_topo_fdr_diff")
#make_titles_topo_fdr_diff = pe.MapNode(interface=util.Function(input_names=['dice', 'jaccard', 'volume', 'contrast', 'subject_id', 'prefix'], 
#                                                 output_names=['title'], 
#                                                 function=_make_titles), name="make_titles_topo_fdr_diff", iterfield=['dice', 'jaccard', 'volume', 'contrast'], overwrite = True)
#make_titles_topo_fdr_diff.inputs.prefix = "Topo FDR: "
#make_titles_topo_fdr_diff.overwrite=True

#finger_foot_lips = create_pipeline_functional_run(name="finger_foot_lips", 
#                                                  conditions=['Finger', 'Foot', 'Lips'], 
#                                                  onsets=[[0, 36, 72, 108, 144],
#                                                          [12, 48, 84, 120, 156],
#                                                          [24, 60, 96, 132, 168]],
#                                                  durations=[[6], [6], [6]],
#                                                  tr=2.5, 
#                                                  contrasts=[('Finger','T', ['Finger'],[1]),
#                                                             ('Foot','T', ['Foot'],[1]),
#                                                             ('Lips','T', ['Lips'],[1])],
#                                                  units='scans')
#
#overt_verb_generation = create_pipeline_functional_run(name="overt_verb_generation", 
#                                                  conditions=['Task'], 
#                                                  onsets=[[0, 12, 24, 36, 48, 60, 72]],
#                                                  durations=[[6]],
#                                                  tr=5.0, 
#                                                  contrasts=[('Task','T', ['Task'],[1])],
#                                                  units='scans',
#                                                  sparse=True)
#
#silent_verb_generation = create_pipeline_functional_run(name="silent_verb_generation", 
#                                                  conditions=['Task'], 
#                                                  onsets=[[0, 24, 48, 72, 96, 120, 144]],
#                                                  durations=[[12]],
#                                                  tr=2.5, 
#                                                  contrasts=[('Task','T', ['Task'],[1])],
#                                                  units='scans')
#
#overt_word_repetition = create_pipeline_functional_run(name="overt_word_repetition", 
#                                                  conditions=['Task'], 
#                                                  onsets=[[0, 12, 24, 36, 48, 60]],
#                                                  durations=[[6]],
#                                                  tr=5.0, 
#                                                  contrasts=[('Task','T', ['Task'],[1])],
#                                                  units='scans',
#                                                  sparse=True)
#
#line_bisection = create_pipeline_functional_run(name="line_bisection", 
#                                                  conditions=['Task', 'Control'], 
#                                                  onsets=[[  16.25,   81.25,  146.25,  211.25,  276.25,  341.25,  406.25, 471.25, 536.25],
#                                                          [  48.75,  113.75,  178.75,  243.75,  308.75,  373.75,  438.75, 503.75, 568.75]],
#                                                  durations=[[16.25], [16.25]],
#                                                  tr=2.5, 
#                                                  contrasts=[('Task-Control','T', ['Task', 'Control'],[1,-1]),
#                                                             ('Task','T', ['Task'],[1]),
#                                                             ('Control','T', ['Control'],[1])],
#                                                  units='secs')

seed = create_prepare_seeds_from_fmri_pipeline("seed")

proc_dwi = create_dwi_pipeline()

mergeinputs = pe.Node(interface=Merge(20), name="mergeinputs")

psmerge = pe.Node(interface = neuroutils.PsMerge(), name = "psmerge")

datasink = pe.Node(interface = DataSink(), name='datasink')
datasink.inputs.base_directory = results_dir
datasink.inputs.remove_dest_dir = True
datasink.inputs.regexp_substitutions = [(r'(?P<root>/home/filo/workspace/2010reliability/results/)(?P<b1>.*)(?P<subject_id>_subject_id.*/)(?P<b2>.*)(?P<task_name>_task_name.*/)(?P<b3>.*)',
                                         r'\g<root>\g<task_name>\g<b1>\g<b2>\g<subject_id>\g<b3>'),
                                        (r'_[^-/]*[0-9][/]', r'/'),
                                        (r'_task_name_', r''),
                                        (r'(?P<subject_id>_subject_id[^/]*)([/])', r'\g<subject_id>_')]

sqlitesink = pe.MapNode(interface = SQLiteSink(input_names=["subject_id", 'task_name', 'contrast_name', 'dice', 'jaccard', 'volume_difference', 'thr_method']), name="sqlitesink", iterfield=["contrast_name", "dice", 'jaccard', 'volume_difference'])
sqlitesink.inputs.database_file = dbfile
sqlitesink.inputs.table_name = "reliability2010"

#sqlitesink_topo_fdr = pe.MapNode(interface = SQLiteSink(input_names=["subject_id", 'task_name', 'contrast_name', 'dice', 'jaccard', 'volume_difference', 'thr_method']), name="sqlitesink_topo_fdr", iterfield=["contrast_name", "dice", 'jaccard', 'volume_difference'])
#sqlitesink_topo_fdr.inputs.database_file = dbfile
#sqlitesink_topo_fdr.inputs.table_name = "reliability2010"
#sqlitesink_topo_fdr.inputs.thr_method = "topo_fdr"

def getReportFilename(subject_id):
    return "subject_%s_report.pdf"%subject_id

def getConditions(task_name):
    conditions_dict = {'finger_foot_lips': ['Finger', 'Foot', 'Lips'], 
                       "overt_verb_generation": ['Task'],
                       "overt_word_repetition": ['Task'],
                       'covert_verb_generation': ['Task'],
                       'line_bisection': ['Task', 'Control']}
    return conditions_dict[task_name]
    
def getOnsets(task_name):
    onsets_dict = {'finger_foot_lips': [[0, 36, 72, 108, 144],
                                        [12, 48, 84, 120, 156],
                                        [24, 60, 96, 132, 168]], 
                   "overt_verb_generation": [[0, 12, 24, 36, 48, 60, 72]],
                   "overt_word_repetition": [[0, 12, 24, 36, 48, 60]],
                   'covert_verb_generation': [[0, 24, 48, 72, 96, 120, 144]],
                   'line_bisection': [[  16.25,   81.25,  146.25,  211.25,  276.25,  341.25,  406.25, 471.25, 536.25],
                                      [  48.75,  113.75,  178.75,  243.75,  308.75,  373.75,  438.75, 503.75, 568.75]],}
    return onsets_dict[task_name]

    
def getDurations(task_name):
    durations_dict = {'finger_foot_lips': [[6], [6], [6]], 
                      "overt_verb_generation": [[6]],
                      "overt_word_repetition": [[6]],
                      'covert_verb_generation': [[12]],
                      'line_bisection': [[16.25], [16.25]]}
    return durations_dict[task_name]

def getTR(task_name):
    tr_dict = {'finger_foot_lips': 2.5, 
               'overt_verb_generation': 5.0,
               'overt_word_repetition': 5.0,
               'covert_verb_generation': 2.5,
               'line_bisection': 2.5}
    return tr_dict[task_name]

def getContrasts(task_name):
    contrasts_dict = {'finger_foot_lips': [('Finger','T', ['Finger'],[1]),
                                           ('Foot','T', ['Foot'],[1]),
                                           ('Lips','T', ['Lips'],[1]),
                                           ('Finger_vs_Other', 'T',['Finger','Foot','Lips'], [1,    -0.5,-0.5]),
                                           ('Foot_vs_Other', 'T',  ['Finger','Foot','Lips'], [-0.5,  1,  -0.5]),
                                           ('Lips_vs_Other', 'T',  ['Finger','Foot','Lips'], [-0.5, -0.5, 1  ]),], 
               'overt_verb_generation': [('Task','T', ['Task'],[1])],
               'overt_word_repetition': [('Task','T', ['Task'],[1])],
               'covert_verb_generation': [('Task','T', ['Task'],[1])],
               'line_bisection': [('Task-Control','T', ['Task', 'Control'],[1,-1]),
                                  ('Task','T', ['Task'],[1]),
                                  ('Control','T', ['Control'],[1])]}
    return contrasts_dict[task_name]

def getStatLabels(task_name):
    contrasts_dict = {'finger_foot_lips': ['Finger','Foot','Lips', 'Finger_vs_Other','Foot_vs_Other','Lips_vs_Other'], 
               'overt_verb_generation': ['overt_verb_generation'],
               'overt_word_repetition': ['overt_word_repetition'],
               'covert_verb_generation': ['covert_verb_generation'],
               'line_bisection': ['Task-Control', 'Task', 'Control']}
    return contrasts_dict[task_name]

def getDiffLabels(task_name):
    contrasts_dict = {'finger_foot_lips': ['Finger','Foot','Lips', 'Finger_vs_Other','Foot_vs_Other','Lips_vs_Other'], 
               'overt_verb_generation': ['overt_verb_generation'],
               'overt_word_repetition': ['overt_word_repetition'],
               'covert_verb_generation': ['covert_verb_generation'],
               'line_bisection': ['Task-Control', 'Task', 'Control']}
    return [n + "_diff.nii" for n in contrasts_dict[task_name]]

def getUnits(task_name):
    units_dict = {'finger_foot_lips': 'scans', 
               'overt_verb_generation': 'scans',
               'overt_word_repetition': 'scans',
               'covert_verb_generation': 'scans',
               'line_bisection': 'secs'}
    return units_dict[task_name]

def getSparse(task_name):
    sparse_dict = {'finger_foot_lips': False, 
               'overt_verb_generation': True,
               'overt_word_repetition': True,
               'covert_verb_generation': False,
               'line_bisection': False}
    return sparse_dict[task_name]

def getFirstSessionId(subject_id):
    import os
    data_dir = '/media/data/2010reliability/data'
    return sorted(os.listdir(os.path.join(data_dir, subject_id)))[0]

def getSecondSessionId(subject_id):
    import os
    data_dir = '/media/data/2010reliability/data'
    return sorted(os.listdir(os.path.join(data_dir, subject_id)))[1]

main_pipeline = pe.Workflow(name="pipeline")
main_pipeline.base_dir = os.path.join(data_dir,"workdir")
main_pipeline.connect([
                       (subjects_infosource, first_session_datasource, [('subject_id', 'subject_id'),
                                                                        (('subject_id', getFirstSessionId), 'session_id')]),
                       (tasks_infosource, first_session_datasource, [('task_name', 'task_name')]),
                       (thr_method_infosource, first_session_functional_run, [('thr_method', 'model.thr_method_inputspec.thr_method'),
                                                                              ('thr_method', 'report.visualise_thresholded_stat.inputnode.prefix')]),
                       (first_session_datasource, first_session_functional_run, [("func", "inputnode.func"),
                                                                                 ("T1","inputnode.struct")]),
                       (tasks_infosource, first_session_functional_run, [(('task_name', getConditions), 'inputnode.conditions'),
                                                                         (('task_name', getOnsets), 'inputnode.onsets'),
                                                                         (('task_name', getDurations), 'inputnode.durations'),
                                                                         (('task_name', getTR), 'inputnode.TR'),
                                                                         (('task_name', getContrasts), 'inputnode.contrasts'),
                                                                         (('task_name', getUnits), 'inputnode.units'),
                                                                         (('task_name', getSparse), 'inputnode.sparse'),
                                                                         ('task_name', 'inputnode.task_name')]),
                                       
                       (subjects_infosource, second_session_datasource, [('subject_id', 'subject_id'),
                                                                        (('subject_id', getSecondSessionId), 'session_id')]),
                       (tasks_infosource, second_session_datasource, [('task_name', 'task_name')]),
                       (thr_method_infosource, second_session_functional_run, [('thr_method', 'model.thr_method_inputspec.thr_method'),
                                                                               ('thr_method', 'report.visualise_thresholded_stat.inputnode.prefix')]),
                       (first_session_datasource, second_session_functional_run, [("T1","inputnode.struct")]),
                       (second_session_datasource, second_session_functional_run, [("func","inputnode.func")]),
                       (tasks_infosource, second_session_functional_run, [(('task_name', getConditions), 'inputnode.conditions'),
                                                                          (('task_name', getOnsets), 'inputnode.onsets'),
                                                                          (('task_name', getDurations), 'inputnode.durations'),
                                                                          (('task_name', getTR), 'inputnode.TR'),
                                                                          (('task_name', getContrasts), 'inputnode.contrasts'),
                                                                          (('task_name', getUnits), 'inputnode.units'),
                                                                          (('task_name', getSparse), 'inputnode.sparse'),
                                                                          ('task_name', 'inputnode.task_name')]),
                       
                       (first_session_functional_run, compare_thresholded_maps, [('report.visualise_thresholded_stat.reslice_overlay.coregistered_source', 'volume1')]),
                       (second_session_functional_run, compare_thresholded_maps, [('report.visualise_thresholded_stat.reslice_overlay.coregistered_source', 'volume2')]),
                       (tasks_infosource, compare_thresholded_maps, [(('task_name', getDiffLabels), 'out_file')]),
                                                                               
#                       (first_session_functional_run, compare_topo_fdr_thresholded_maps, [('report.visualisethresholded_stat.reslice_overlay.coregistered_source', 'volume1')]),
#                       (second_session_functional_run, compare_topo_fdr_thresholded_maps, [('report.visualisethresholded_stat.reslice_overlay.coregistered_source', 'volume2')]),
#                       (tasks_infosource, compare_topo_fdr_thresholded_maps, [(('task_name', getDiffLabels), 'out_file')]),
                       
                       (compare_thresholded_maps, plot_diff, [('diff_file', "overlay")]),
                       (first_session_datasource, plot_diff, [('T1', 'background')]),
                       (compare_thresholded_maps, make_titles_diff, [('dice', 'dice'),
                                                                                         ('jaccard', 'jaccard'),
                                                                                         ('volume', 'volume')]),
                       (tasks_infosource, make_titles_diff, [(('task_name', getStatLabels), 'contrast')]),
                       (subjects_infosource, make_titles_diff, [('subject_id', 'subject_id')]),
                       (thr_method_infosource, make_titles_diff, [('thr_method', 'prefix')]),
                       (make_titles_diff, plot_diff, [('title', 'title')]),
                       
#                       (compare_topo_fdr_thresholded_maps, plot_topo_fdr_diff, [('diff_file', "overlay")]),
#                       (first_session_datasource, plot_topo_fdr_diff, [('T1', 'background')]),
#                       (compare_topo_fdr_thresholded_maps, make_titles_topo_fdr_diff, [('dice', 'dice'),
#                                                                                         ('jaccard', 'jaccard'),
#                                                                                         ('volume', 'volume')]),
#                       (tasks_infosource, make_titles_topo_fdr_diff, [(('task_name', getStatLabels), 'contrast')]),
#                       (subjects_infosource, make_titles_topo_fdr_diff, [('subject_id', 'subject_id')]),
#                       (make_titles_topo_fdr_diff, plot_topo_fdr_diff, [('title', 'title')]),
                       
                       (compare_thresholded_maps, sqlitesink, [('dice', "dice",),
                                                                         ('jaccard', 'jaccard'),
                                                                         ('volume', 'volume_difference')]),
                       (subjects_infosource, sqlitesink, [('subject_id', 'subject_id')]),
                       (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
                                                       (('task_name', getStatLabels), 'contrast_name')]),
                       (thr_method_infosource, sqlitesink, [('thr_method','thr_method')]),
                       
#                       (compare_topo_fdr_thresholded_maps, sqlitesink_topo_fdr, [('dice', "dice",),
#                                                                         ('jaccard', 'jaccard'),
#                                                                         ('volume', 'volume_difference')]),
#                       (subjects_infosource, sqlitesink_topo_fdr, [('subject_id', 'subject_id')]),
#                       (tasks_infosource, sqlitesink_topo_fdr, [('task_name', 'task_name'),
#                                                       (('task_name', getStatLabels), 'contrast_name')]),
                       
                       
                       (compare_thresholded_maps, datasink, [('diff_file', "volumes.difference_maps.topo_ggmm")]),
#                       (compare_topo_fdr_thresholded_maps, datasink, [('diff_file', "volumes.difference_maps.topo_fdr")]),
                       
                       (plot_diff, datasink, [('plot', 'reports.difference_maps.topo_ggmm')]),
#                       (plot_topo_fdr_diff, datasink, [('plot', 'reports.difference_maps.topo_fdr')]),
                       
                       (first_session_functional_run, datasink, [('report.visualise_thresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.thresholded.topo_ggmm.first_session')]),
                       (second_session_functional_run, datasink, [('report.visualise_thresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.thresholded.topo_ggmm.second_session')]),
                       
                       (first_session_functional_run, datasink, [('report.visualise_thresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.thresholded.topo_fdr.first_session')]),
                       (second_session_functional_run, datasink, [('report.visualise_thresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.thresholded.topo_fdr.second_session')]),
                       
                       (first_session_functional_run, datasink, [('report.visualise_unthresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.unthresholded.first_session')]),
                       (second_session_functional_run, datasink, [('report.visualise_unthresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.unthresholded.second_session')]),
                       
                       (first_session_functional_run, datasink, [('report.psmerge_all.merged_file', 'reports.first_session')]),
                       (second_session_functional_run, datasink, [('report.psmerge_all.merged_file', 'reports.second_session')]),
                                             

#                       (tasks_infosource, functional_run, [(('task_name', getConditions), 'inputnode.conditions'),
#                                                          (('task_name', getOnsets), 'inputnode.onsets'),
#                                                          (('task_name', getDurations), 'inputnode.durations'),
#                                                          (('task_name', getTR), 'inputnode.TR'),
#                                                          (('task_name', getContrasts), 'inputnode.contrasts'),
#                                                          (('task_name', getUnits), 'inputnode.units'),
#                                                          (('task_name', getSparse), 'inputnode.sparse'),
#                                                          ('task_name', 'inputnode.task_name')]),
#                                                          
#                        (datasource, proc_dwi, [("dwi", "inputnode.dwi"),
#                                               ("dwi_bval", "inputnode.bvals"),
#                                               ("dwi_bvec", "inputnode.bvecs")]),
#                       (proc_dwi, seed, [("bedpostx.outputnode.thsamples", "inputnode.thsamples"),
#                                                          ("bedpostx.outputnode.phsamples", "inputnode.phsamples"),
#                                                          ("bedpostx.outputnode.fsamples", "inputnode.fsamples")]),
#                       (functional_run, seed, [("preproc_func.coregister.coregistered_source","inputnode.epi"),
#                                               ("preproc_func.compute_mask.brain_mask", "inputnode.mask"),
#                                               ("model.contrastestimate.spmT_images","inputnode.stat"),
#                                                                  ]),
#                       (datasource, seed, [("dwi", "inputnode.dwi"),
#                                           ("T1", "inputnode.T1")]),
#                       (tasks_infosource, seed, [(('task_name', getStatLabels), 'inputnode.stat_labels')]),
##                       
#                       (finger_foot_lips, mergeinputs, [("preproc_func.plot_realign.plot", "in1")]),                                
#                       (finger_foot_lips, mergeinputs, [("report.psmerge_raw.merged_file", "in2")]),
#                       (finger_foot_lips, mergeinputs, [("report.psmerge_th.merged_file", "in3")]),
#                       (finger_foot_lips, mergeinputs, [("report.psmerge_ggmm_th.merged_file", "in4")]),
#                       
#                       (datasource, overt_verb_generation, [("verb_generation", "inputnode.func"),
#                                                            ("T1","inputnode.struct")]),
#                       (overt_verb_generation, mergeinputs, [("preproc_func.plot_realign.plot", "in5")]),
#                       (overt_verb_generation, mergeinputs, [("report.psmerge_raw.merged_file", "in6")]),
#                       (overt_verb_generation, mergeinputs, [("report.psmerge_th.merged_file", "in7")]),
#                       (overt_verb_generation, mergeinputs, [("report.psmerge_ggmm_th.merged_file", "in8")]),
#                       
#                       (datasource, silent_verb_generation, [("silent_verb_generation", "inputnode.func"),
#                                                            ("T1","inputnode.struct")]),
#                       (silent_verb_generation, mergeinputs, [("preproc_func.plot_realign.plot", "in9")]),
#                       (silent_verb_generation, mergeinputs, [("report.psmerge_raw.merged_file", "in10")]),
#                       (silent_verb_generation, mergeinputs, [("report.psmerge_th.merged_file", "in11")]),
#                       (silent_verb_generation, mergeinputs, [("report.psmerge_ggmm_th.merged_file", "in12")]),
#                       
#                       (datasource, overt_word_repetition, [("word_repetition", "inputnode.func"),
#                                                            ("T1","inputnode.struct")]),
#                       (overt_word_repetition, mergeinputs, [("preproc_func.plot_realign.plot", "in13")]),
#                       (overt_word_repetition, mergeinputs, [("report.psmerge_raw.merged_file", "in14")]),
#                       (overt_word_repetition, mergeinputs, [("report.psmerge_th.merged_file", "in15")]),
#                       (overt_word_repetition, mergeinputs, [("report.psmerge_ggmm_th.merged_file", "in16")]),
#                       
#                       (datasource, line_bisection, [("line_bisection", "inputnode.func"),
#                                                     ("T1","inputnode.struct")]),
#                       (line_bisection, mergeinputs, [("preproc_func.plot_realign.plot", "in17")]),
#                       (line_bisection, mergeinputs, [("report.psmerge_raw.merged_file", "in18")]),
#                       (line_bisection, mergeinputs, [("report.psmerge_th.merged_file", "in19")]),
#                       (line_bisection, mergeinputs, [("report.psmerge_ggmm_th.merged_file", "in20")]),
#                       

#                       
#                       (mergeinputs, psmerge, [("out", "in_files")]),
#                       (subjects_infosource, psmerge, [(("subject_id", getReportFilename), "out_file")])
                       ])
if __name__ == '__main__':
    main_pipeline.run(plugin_args={'n_procs': 4})
    main_pipeline.write_graph(graph2use='flat')
