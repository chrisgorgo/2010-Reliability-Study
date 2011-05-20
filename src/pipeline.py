import pydevd
pydevd.set_pm_excepthook()

import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm
import nipype.interfaces.fsl as fsl
from helper_functions import (create_pipeline_functional_run)

from StringIO import StringIO
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import *

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
                                            line_bisection_log = [['subject_id', 'session_id', 'session_id']])
func_datasource.inputs.field_template = dict(line_bisection_log= '%s/%s/logs/*%s-Line_Bisection.log')
func_datasource.inputs.sort_filelist = True

coregister_T1s = pe.Node(interface=spm.Coregister(), name="coregister_T1s")
coregister_T1s.jobtype = "estwrite"

average_T1s = pe.Node(interface=fsl.maths.MultiImageMaths(op_string="-add %s -div 2"), name="average_T1s")

segment = pe.Node(interface=spm.Segment(), name='segment')

normalize = pe.Node(interface=spm.Normalize(jobtype="write"), name="normalize")


functional_run = create_pipeline_functional_run(name="functional_run", series_format="4d")

get_session_id = pe.Node(interface=utility.Function(input_names=['session', 'subject_id'], 
                                                    output_names=['session_id'], 
                                                    function=getSessionId), 
                         name="get_session_id")

get_onsets = pe.Node(interface=utility.Function(input_names=['task_name', 'line_bisection_log', 'delay'], 
                                                    output_names=['onsets'], 
                                                    function=getOnsets), 
                         name="get_onsets")
get_onsets.inputs.delay = 4*2.5


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

if __name__ == '__main__':
    main_pipeline.run(plugin_args={'n_procs': 4})
    main_pipeline.write_graph()
