import pydevd
from parse_line_bisection_log import parse_line_bisection_log
pydevd.set_pm_excepthook()
from nipype.interfaces import utility


import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.algorithms.misc as misc
import nipype.interfaces.spm as spm
import nipype.interfaces.fsl as fsl
from helper_functions import (create_pipeline_functional_run, 
                                         create_dwi_pipeline,
                                         create_prepare_seeds_from_fmri_pipeline)
from nipype.interfaces.utility import Merge
import neuroutils

from StringIO import StringIO
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import *

#info = dict(T1 = [['subject_id', 'session_id', 'co_COR_3D_IR_PREP']],
#            func = [['subject_id', 'session_id', 'task_name']],
#            #dwi = [['subject_id', 'session_id', '[0-9]_DTI_64G_2.0_mm_isotropic']],
#            #dwi_bval = [['subject_id', 'session_id', '[0-9]_DTI_64G_2.0_mm_isotropic']],
#            #dwi_bvec = [['subject_id', 'session_id', '[0-9]_DTI_64G_2.0_mm_isotropic']]
#            )

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

sessions_infosource = pe.Node(interface=util.IdentityInterface(fields=['session']),
                              name="sessions_infosource")
sessions_infosource.iterables = ('session', sessions)

struct_datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['T1']),
                     name = 'struct_datasource')
struct_datasource.inputs.base_directory = data_dir
struct_datasource.inputs.template = '%s/*/*%s*.nii'
struct_datasource.inputs.template_args = dict(T1 = [['subject_id', 'co_COR_3D_IR_PREP']])
struct_datasource.inputs.sort_filelist = True

func_datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'session_id'],
                                               outfields=['func', 'line_bisection_log']),
                     name = 'func_datasource')

func_datasource.inputs.base_directory = data_dir
func_datasource.inputs.template = '%s/%s/*[0-9]_%s*.nii'
func_datasource.inputs.template_args = dict(func = [['subject_id', 'session_id', 'task_name']],
                                            line_bisection_log = [['08143633-aec2-49a9-81cf-45867827b871', '17107']])
func_datasource.inputs.field_template = dict(line_bisection_log= '%s/%s/logs/*Line_Bisection.log')
#                                                      #dwi_bval=func_datasource.inputs.template.replace("nii", "bval"),
#                                        #dwi_bvec=func_datasource.inputs.template.replace("nii", "bvec"),
#                                        func = '%s_*/*/*[0-9]_%s.nii'
#                                        )
func_datasource.inputs.sort_filelist = True

#second_session_datasource = func_datasource.clone(name = 'second_session_datasource')

coregister_T1s = pe.Node(interface=spm.Coregister(), name="coregister_T1s")
coregister_T1s.jobtype = "estwrite"

average_T1s = pe.Node(interface=fsl.maths.MultiImageMaths(op_string="-add %s -div 2"), name="average_T1s")

segment = pe.Node(interface=spm.Segment(), name='segment')

normalize = pe.Node(interface=spm.Normalize(jobtype="write"), name="normalize")


functional_run = create_pipeline_functional_run(name="functional_run", series_format="4d")
#second_session_functional_run = first_session_functional_run.clone("second_session_functional_run")



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

#seed = create_prepare_seeds_from_fmri_pipeline("seed")

#proc_dwi = create_dwi_pipeline()

#mergeinputs = pe.Node(interface=Merge(20), name="mergeinputs")

#psmerge = pe.Node(interface = neuroutils.PsMerge(), name = "psmerge")

datasink = pe.Node(interface = DataSink(), name='datasink')
datasink.inputs.base_directory = results_dir
datasink.inputs.regexp_substitutions = [
                                        #(r'(?P<root>/home/filo/workspace/2010reliability/results/)(?P<b1>.*)(?P<subject_id>_subject_id.*/)(?P<b2>.*)(?P<task_name>_task_name.*/)(?P<b3>.*)',
                                        # r'\g<root>\g<task_name>\g<b1>\g<b2>\g<subject_id>\g<b3>'),
                                        (r'(?P<r1>_[^-/]*)(?P<id>[0-9]+)(?P<r2>[/])', r'/\g<id>'),
                                        #(r'_task_name_', r''),
                                        #(r'(?P<subject_id>_subject_id[^/]*)([/])', r'\g<subject_id>_')
                                        ]

sqlitesink = pe.MapNode(interface = SQLiteSink(input_names=["subject_id",
                                                            "session",
                                                            'task_name', 
                                                            'contrast_name',
                                                            'cluster_forming_threshold',
                                                            'selected_model',
                                                            'activation_forced',
                                                            'n_clusters',
                                                            'pre_topo_n_clusters',
                                                            'roi']), 
                        name="sqlitesink", 
                        iterfield=["contrast_name", 'cluster_forming_threshold',
                                                            'selected_model',
                                                            'activation_forced',
                                                            'n_clusters',
                                                            'pre_topo_n_clusters'])
sqlitesink.inputs.database_file = dbfile
sqlitesink.inputs.table_name = "reliability2010_ggmm_thresholding"

def getReportFilename(subject_id):
    return "subject_%s_report.pdf"%subject_id

def getConditions(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['conditions']
    
def getOnsets(task_name, line_bisection_log, delay):
    if task_name == "line_bisection":
        from parse_line_bisection_log import parse_line_bisection_log
        _,_,correct_pictures, incorrect_pictures, noresponse_pictures = parse_line_bisection_log(line_bisection_log, delay)
        return [correct_pictures["task"], incorrect_pictures["task"], noresponse_pictures["task"],
                correct_pictures["rest"], incorrect_pictures["rest"], noresponse_pictures["rest"]]
    else:
        from variables import design_parameters
        return design_parameters[task_name]['onsets']

    
def getDurations(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['durations']

def getTR(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['TR']

def getContrasts(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['contrasts']

def getDiffLabels(task_name):
    from variables import design_parameters
    return [contrast[0] + "_diff.nii" for contrast in design_parameters[task_name]['contrasts']]

def getUnits(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['units']

def getSparse(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['sparse']

def getAtlasLabels(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['atlas_labels']

def getDilation(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['dilation']

def pickFirst(l):
    return l[0]

def pickSecond(l):
    return l[1]

def getSessionId(session, subject_id):
    s = {"8d80a62b-aa21-49bd-b8ca-9bc678ffe7b0": ["16841", "16849"],
         "08143633-aec2-49a9-81cf-45867827b871": ["17100", "17107"],
         '3a3e1a6f-dc92-412c-870a-74e4f4e85ddb': ["17168", "17180"],
         '8bb20980-2dc4-4da9-9065-879e2e7e1fbe': ["16889", "16907"],
         '90bafbe8-c67f-4388-b677-27fcf2427c71': ["16846", "16854"],
         '94cfb26f-0060-4c44-b59f-702ca61143ca': ["16967", "16978"],
         'c2cc1c59-df88-4366-9f99-73b722235789': ["16864", "16874"],
         'cf48f394-1912-4202-89f7-dbf8ef9d6e19': ["17119", "17132"],
         'df4808a4-ecce-4d0a-9fe2-535c0720ec17': ["17363", "17373"],
         'e094aae5-8387-4b5c-bf56-df4a88623c5d': ["17142", "17149"]}
    return s[subject_id][{"first":0, "second":1}[session]]

def get_vox_dims(volume):
    import nibabel as nb
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    voxdims = hdr.get_zooms()
    return [float(voxdims[0]), float(voxdims[1]), float(voxdims[2])]

get_session_id = pe.Node(interface=utility.Function(input_names=['session', 'subject_id'], 
                                                    output_names=['session_id'], 
                                                    function=getSessionId), 
                         name="get_session_id")

get_onsets = pe.Node(interface=utility.Function(input_names=['task_name', 'line_bisection_log', 'delay'], 
                                                    output_names=['onsets'], 
                                                    function=getOnsets), 
                         name="get_onsets")
get_onsets.inputs.delay = 4*2.5

main_pipeline = pe.Workflow(name="pipeline")
main_pipeline.base_dir = working_dir
main_pipeline.connect([(subjects_infosource, struct_datasource, [('subject_id', 'subject_id')]),
                       (struct_datasource, coregister_T1s, [(('T1', pickFirst), 'source'),
                                                            (('T1', pickSecond), 'target')]),
                       (coregister_T1s, average_T1s, [('coregistered_source', 'in_file')]),
                       (struct_datasource, average_T1s, [(('T1', pickSecond), 'operand_files')]),
                       (average_T1s, segment,[('out_file','data')]),
                       (segment, normalize, [('transformation_mat','parameter_file'),
                                             ('modulated_input_image', 'apply_to_files'),
                                             (('modulated_input_image', get_vox_dims), 'write_voxel_sizes')]),
                       
                       (subjects_infosource, get_session_id, [('subject_id', 'subject_id')]),
                       (sessions_infosource, get_session_id, [('session', 'session')]),
                       (subjects_infosource, func_datasource, [('subject_id', 'subject_id')]),
                       (get_session_id, func_datasource, [('session_id', 'session_id')]),
                       (tasks_infosource, func_datasource, [('task_name', 'task_name')]),
                       
                       (thr_method_infosource, functional_run, [('thr_method', 'model.thr_method_inputspec.thr_method'),
                                                                ('thr_method', 'report.visualise_thresholded_stat.inputnode.prefix')]),
                       (roi_infosource, functional_run, [('roi', 'model.roi_inputspec.roi')]),
                       (func_datasource, functional_run, [("func", "inputnode.func")]),
                       (normalize, functional_run, [("normalized_files","inputnode.struct")]),
                       (tasks_infosource, functional_run, [(('task_name', getConditions), 'inputnode.conditions'),
#                                                                         (('task_name', getOnsets), 'inputnode.onsets'),
                                                                         (('task_name', getDurations), 'inputnode.durations'),
                                                                         (('task_name', getTR), 'inputnode.TR'),
                                                                         (('task_name', getContrasts), 'inputnode.contrasts'),
                                                                         (('task_name', getUnits), 'inputnode.units'),
                                                                         (('task_name', getSparse), 'inputnode.sparse'),
                                                                         (('task_name', getAtlasLabels), 'inputnode.atlas_labels'),
                                                                         (('task_name', getDilation), 'inputnode.dilation_size'),
                                                                         ('task_name', 'inputnode.task_name')]),
                       (tasks_infosource, get_onsets, [('task_name', 'task_name')]),
                       (func_datasource, get_onsets, [('line_bisection_log', 'line_bisection_log')]),
                       (get_onsets, functional_run, [('onsets', 'inputnode.onsets')]),

                       (functional_run, datasink, [('report.visualise_thresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.thresholded')]),
                       (functional_run, datasink, [('report.visualise_unthresholded_stat.reslice_overlay.coregistered_source', 'volumes.t_maps.unthresholded')]),
                       (normalize, datasink, [("normalized_files","volumes.T1")]),
                       (functional_run, datasink, [('report.psmerge_all.merged_file', 'reports')]),
                       
                       (subjects_infosource, sqlitesink, [('subject_id', 'subject_id')]),
                       (sessions_infosource, sqlitesink, [('session', 'session')]),
                       (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
                                                       (('task_name', getStatLabels), 'contrast_name')]),
                       (roi_infosource, sqlitesink, [('roi', 'roi')]),
                       (functional_run, sqlitesink, [('model.threshold_topo_ggmm.ggmm.threshold','cluster_forming_threshold'),
                                                     ('model.threshold_topo_ggmm.ggmm.selected_model', 'selected_model'),
                                                     ('model.threshold_topo_ggmm.topo_fdr.activation_forced','activation_forced'),
                                                     ('model.threshold_topo_ggmm.topo_fdr.n_clusters','n_clusters'),
                                                     ('model.threshold_topo_ggmm.topo_fdr.pre_topo_n_clusters', 'pre_topo_n_clusters')])
                
                       ])
#compare_datagrabber = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'thr_method'],
#                                               outfields=['first_map', 'second_map', 'T1']),
#                     name = 'compare_datagrabber')
#
#compare_datagrabber.inputs.base_directory = os.path.join(results_dir, "volumes")
#compare_datagrabber.inputs.template = 't_maps/thresholded/_subject_id_%s/_session_%s/_task_name_%s/_thr_method_%s/*.img'
#compare_datagrabber.inputs.field_template = dict(T1= 'T1/_subject_id_%s/*.nii')
#compare_datagrabber.inputs.template_args = dict(first_map = [['subject_id', 'first', 'task_name', 'thr_method']],
#                                                second_map = [['subject_id', 'second', 'task_name', 'thr_method']],
#                                                T1 = [['subject_id']])
#compare_datagrabber.inputs.sort_filelist = True
#compare_datagrabber.overwrite = True
#
#def _make_titles(dice, jaccard, volume, contrast, subject_id, prefix=''):
#    return prefix + " %s: dice = %f, jaccard = %f, volume = %d, subject_id = %s"%(contrast, dice, jaccard, volume, subject_id.split('-')[0])
#
#compare_thresholded_maps = pe.MapNode(interface=misc.Overlap(), name="compare_thresholded_maps", iterfield=['volume1', 'volume2'])
#plot_diff = pe.MapNode(interface=neuroutils.Overlay(overlay_range = (1, 3)), name="plot", iterfield=['overlay', 'title'])
#make_titles_diff = pe.MapNode(interface=util.Function(input_names=['dice', 'jaccard', 'volume', 'contrast', 'subject_id', 'prefix'], 
#                                                 output_names=['title'], 
#                                                 function=_make_titles), name="make_titles_diff", iterfield=['dice', 'jaccard', 'volume', 'contrast'], overwrite = True)
#
#sqlitesink = pe.MapNode(interface = SQLiteSink(input_names=["subject_id", 'task_name', 'contrast_name', 'dice', 'jaccard', 'volume_difference', 'thr_method']), name="sqlitesink", iterfield=["contrast_name", "dice", 'jaccard', 'volume_difference'])
#sqlitesink.inputs.database_file = dbfile
#sqlitesink.inputs.table_name = "reliability2010"
#
#compare_pipeline = pe.Workflow(name="compare_pipeline")
#compare_pipeline.base_dir = working_dir
#compare_pipeline.connect([(subjects_infosource, compare_datagrabber, [('subject_id', 'subject_id')]),
#                          (tasks_infosource, compare_datagrabber, [('task_name', 'task_name')]),
#                          (thr_method_infosource, compare_datagrabber, [('thr_method', 'thr_method')]),
#                          (compare_datagrabber, compare_thresholded_maps, [('first_map', 'volume1'),
#                                                                           ('second_map', 'volume2')]),
#                          
#                          (compare_thresholded_maps, sqlitesink, [('dice', "dice",),
#                                                                  ('jaccard', 'jaccard'),
#                                                                  ('volume_difference', 'volume_difference')]),
#                          (subjects_infosource, sqlitesink, [('subject_id', 'subject_id')]),
#                          (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
#                                                          (('task_name', getStatLabels), 'contrast_name')]),
#                          (thr_method_infosource, sqlitesink, [('thr_method','thr_method')]),
#                          
#                          (compare_thresholded_maps, plot_diff, [('diff_file', "overlay")]),
#                          (compare_datagrabber, plot_diff, [('T1', 'background')]),
#                          (compare_thresholded_maps, make_titles_diff, [('dice', 'dice'),
#                                                                        ('jaccard', 'jaccard'),
#                                                                        ('volume_difference', 'volume')]),
#                          (tasks_infosource, make_titles_diff, [(('task_name', getStatLabels), 'contrast')]),
#                          (subjects_infosource, make_titles_diff, [('subject_id', 'subject_id')]),
#                          (thr_method_infosource, make_titles_diff, [('thr_method', 'prefix')]),
#                          (make_titles_diff, plot_diff, [('title', 'title')]),
#                          (plot_diff, datasink, [('plot', 'reports.difference_maps')]),
#])

#between_subjects_pipeline = pe.Workflow(name="between_subjects_pipeline")
#between_subjects_pipeline.base_dir = working_dir
#
#for i in range(len(subjects)):
#    for j in range(i+1,len(subjects)):
#        datagrabber1 = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'thr_method', 'session'],
#                                               outfields=['map', 'T1']),
#                     name = 'datagrabber1' + str((i,j)))
#
#        datagrabber1.inputs.base_directory = os.path.join(results_dir, "volumes")
#        datagrabber1.inputs.template = 't_maps/thresholded/_subject_id_%s/_session_%s/_task_name_%s/_thr_method_%s/*.img'
#        datagrabber1.inputs.field_template = dict(T1= 'T1/_subject_id_%s/*.nii')
#        datagrabber1.inputs.template_args = dict(map = [['subject_id', 'session', 'task_name', 'thr_method']],
#                                                 T1 = [['subject_id']])
#        datagrabber1.inputs.sort_filelist = True
#        datagrabber1.inputs.subject_id = subjects[i]
#        
#        datagrabber2 = datagrabber1.clone(name='datagrabber2' + str((i,j)))
#        datagrabber2.inputs.subject_id = subjects[j]
#        
#        compare_thresholded_maps = pe.MapNode(interface=misc.Overlap(), name="compare_thresholded_maps"+ str((i,j)), iterfield=['volume1', 'volume2'])
#        plot_diff = pe.MapNode(interface=neuroutils.Overlay(overlay_range = (1, 3)), name="plot"+ str((i,j)), iterfield=['overlay', 'title'])
#        make_titles_diff = pe.MapNode(interface=util.Function(input_names=['dice', 'jaccard', 'volume', 'contrast', 'subject_id', 'prefix'], 
#                                                         output_names=['title'], 
#                                                         function=_make_titles), name="make_titles_diff"+ str((i,j)), iterfield=['dice', 'jaccard', 'volume', 'contrast'], overwrite = True)
#        
#        sqlitesink = pe.MapNode(interface = SQLiteSink(input_names=["subject_id1", "subject_id2",
#                                                                    "session",
#                                                                    'task_name', 'contrast_name', 
#                                                                    'dice', 'jaccard', 
#                                                                    'volume_difference', 'thr_method']), 
#                                name="sqlitesink"+ str((i,j)), 
#                                iterfield=["contrast_name", "dice", 'jaccard', 'volume_difference'])
#        sqlitesink.inputs.database_file = dbfile
#        sqlitesink.inputs.table_name = "reliability2010_between_subjects"
#        sqlitesink.inputs.subject_id1 = subjects[i]
#        sqlitesink.inputs.subject_id1 = subjects[j]
#        
#        compare_pipeline.connect([(subjects_infosource, datagrabber1, [('subject_id', 'subject_id')]),
#                                  (tasks_infosource, datagrabber1, [('task_name', 'task_name')]),
#                                  (thr_method_infosource, datagrabber1, [('thr_method', 'thr_method')]),
#                                  (sessions_infosource, datagrabber1, [('session', 'session')]),
#                                  
#                                  (subjects_infosource, datagrabber2, [('subject_id', 'subject_id')]),
#                                  (tasks_infosource, datagrabber2, [('task_name', 'task_name')]),
#                                  (thr_method_infosource, datagrabber2, [('thr_method', 'thr_method')]),
#                                  (sessions_infosource, datagrabber2, [('session', 'session')]),
#                          
#                                  (datagrabber1, compare_thresholded_maps, [('map', 'volume1')]),
#                                  (datagrabber2, compare_thresholded_maps, [('map', 'volume2')]),
#                          
#                                  (compare_thresholded_maps, sqlitesink, [('dice', "dice",),
#                                                                          ('jaccard', 'jaccard'),
#                                                                          ('volume_difference', 'volume_difference')]),
#                                  (subjects_infosource, sqlitesink, [('subject_id', 'subject_id')]),
#                                  (tasks_infosource, sqlitesink, [('task_name', 'task_name'),
#                                                                  (('task_name', getStatLabels), 'contrast_name')]),
#                                  (thr_method_infosource, sqlitesink, [('thr_method','thr_method')]),
#                                  (sessions_infosource, sqlitesink, [('session', 'session')]),
#                                  
#                                  (compare_thresholded_maps, plot_diff, [('diff_file', "overlay")]),
#                                  (compare_datagrabber, plot_diff, [('T1', 'background')]),
#                                  (compare_thresholded_maps, make_titles_diff, [('dice', 'dice'),
#                                                                                ('jaccard', 'jaccard'),
#                                                                                ('volume_difference', 'volume')]),
#                                  (tasks_infosource, make_titles_diff, [(('task_name', getStatLabels), 'contrast')]),
#                                  (subjects_infosource, make_titles_diff, [('subject_id', 'subject_id')]),
#                                  (thr_method_infosource, make_titles_diff, [('thr_method', 'prefix')]),
#                                  (make_titles_diff, plot_diff, [('title', 'title')]),
#                                  (plot_diff, datasink, [('plot', 'reports.between_subjects_pipeline.difference_maps')])
#                          ])
        

if __name__ == '__main__':
    main_pipeline.run(plugin_args={'n_procs': 4})
    main_pipeline.write_graph()
