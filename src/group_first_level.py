import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.io as nio 
import nipype.algorithms.rapidart as ra      # artifact detection
import nipype.algorithms.modelgen as model   # model specification
from nipype.interfaces import fsl, utility
import neuroutils
from nipype.interfaces.utility import Merge, Rename
import nipype.workflows.spm as spm_wf          # spm

import os

fsl.FSLCommand.set_default_output_type('NIFTI')

from variables import data_dir,tasks, subjects, working_dir, sessions,\
    results_dir

def get_n_slices(volume):
    import nibabel as nb
    nii = nb.load(volume)
    return nii.get_shape()[2]

def get_tr(tr, sparse):
    if sparse:
        return tr/2
    else:
        return tr
    
def get_ta(real_tr, n_slices):
    return real_tr - real_tr/float(n_slices)

def get_slice_order(volume):
    import nibabel as nb
    nii = nb.load(volume)
    n_slices = nii.get_shape()[2]
    return range(1,n_slices+1,2) + range(2,n_slices+1,2)

def get_ref_slice(volume):
    import nibabel as nb
    if isinstance(volume,list) and len(volume) == 1:
        volume = volume[0]
    nii = nb.load(volume)
    n_slices = nii.get_shape()[2]
    return n_slices/2
        
def create_normalize_and_artdetect_func():
    
    inputnode = pe.Node(interface=util.IdentityInterface(fields=['func', 
                                                                 "mask_file", 
                                                                 "realignment_parameters", 
                                                                 'flowfield_files',
                                                                 'template_file']), 
                        name="inputnode")
    
    normalize_and_smooth_func = pe.Node(spm.DARTELNorm2MNI(modulate=True), name='normalize_and_smooth_func')
    normalize_and_smooth_func.inputs.fwhm = 8
    
    art = pe.Node(interface=ra.ArtifactDetect(), name="art")
    art.inputs.use_differences      = [True,False]
    art.inputs.use_norm             = True
    art.inputs.norm_threshold       = 1
    art.inputs.zintensity_threshold = 3
    art.inputs.mask_type            = 'file'
    art.inputs.parameter_source     = 'SPM'
    
    preproc_func = pe.Workflow(name="normalize_and_artdetect_func")
    preproc_func.base_dir = os.path.join(working_dir, "group", "first_level", "preproc")
    preproc_func.connect([
                          (inputnode,normalize_and_smooth_func, [("func", "apply_to_files"),
                                                                 ('flowfield_files', 'flowfield_files'),
                                                                 ('template_file', 'template_file')]),
                          (inputnode,art,[('realignment_parameters','realignment_parameters'),
                                          ('mask_file', 'mask_file')]),
                          (normalize_and_smooth_func,art,[('normalized_files','realigned_files')]),
                          ])
    
    outputnode = pe.Node(interface=util.IdentityInterface(fields=['preprocessed_files', 'outlier_files']), name="outputnode")
    
    preproc_func.connect(normalize_and_smooth_func, 'normalized_files', outputnode, 'preprocessed_files')
    preproc_func.connect(art, 'outlier_files', outputnode, 'outlier_files')
    
    return preproc_func

def create_normalize_and_skullstrip_struct():
    
    inputnode = pe.Node(interface=util.IdentityInterface(fields=["struct", 
                                                                 'flowfield_files',
                                                                 'template_file']), 
                        name="inputnode")
    
    normalize_struct = pe.Node(spm.DARTELNorm2MNI(modulate=True), name='normalize_struct')
    normalize_struct.inputs.fwhm = 2
    
    skullstrip = pe.Node(interface=fsl.BET(), name="skullstrip")
    skullstrip.inputs.mask = True
    
    preproc_func = pe.Workflow(name="normalize_and_skullstrip_struct")
    preproc_func.base_dir = os.path.join(working_dir, "group", "first_level", "preproc")
    preproc_func.connect([
                          (inputnode,normalize_struct, [("struct", "apply_to_files"),
                                                        ('flowfield_files', 'flowfield_files'),
                                                        ('template_file', 'template_file')]),
                          (normalize_struct,skullstrip,[('normalized_files','in_file')]),
                          ])
    
    outputnode = pe.Node(interface=util.IdentityInterface(fields=['preprocessed_files', 'mask_file']), name="outputnode")
    
    preproc_func.connect(normalize_struct, 'normalized_files', outputnode, 'preprocessed_files')
    preproc_func.connect(skullstrip, 'mask_file', outputnode, 'mask_file')
    
    return preproc_func

def create_skip_and_slice_time_piepeline():
    pipeline = pe.Workflow(name="skip_and_slice_time")
    pipeline.base_dir = os.path.join(working_dir, "group", "first_level", "preproc")
    
    subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                                  name="subjects_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)
    
    tasks_infosource = pe.Node(interface=util.IdentityInterface(fields=['task_name']),
                               name="tasks_infosource")
    tasks_infosource.iterables = ('task_name', tasks)
    
    sessions_infosource = pe.Node(interface=util.IdentityInterface(fields=['session']),
                                  name="sessions_infosource")
    sessions_infosource.iterables = ('session', sessions)
    
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
    
    get_session_id = pe.Node(interface=util.Function(input_names=['session', 'subject_id'], 
                                                        output_names=['session_id'], 
                                                        function=getSessionId), 
                         name="get_session_id")
    
    datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'session_id'],
                                               outfields=['func']),
                              name = 'datasource')
    datasource.inputs.base_directory = data_dir
    datasource.inputs.template = '%s/%s/*[0-9]_%s*.nii'
    datasource.inputs.template_args = dict(func = [['subject_id', 'session_id', 'task_name']])
    datasource.inputs.sort_filelist = True

    skip = pe.Node(interface=fsl.ExtractROI(), name="skip")
    skip.inputs.t_min = 4 #TODO
    skip.inputs.t_size = 100000
    
    def flipFunc(in_file):
        from variables import lefties
        if in_file.find("finger_foot_lips") != -1:
            for subject_id in lefties:
                if in_file.find(subject_id) != -1:
                    import nibabel, os
                    import numpy as np
                    nii = nibabel.load(in_file)
                    _, fname = os.path.split(in_file)
                    nibabel.save(nibabel.Nifti1Image(np.flipud(nii.get_data()), nii.get_affine()), "flipped_" + fname)
                    return os.path.abspath("flipped_" + fname)
        return in_file
    
    flip = pe.Node(interface=util.Function(input_names=['in_file'], 
                                           output_names=['out_file'], 
                                           function=flipFunc), name="flip")
    
    tr_convert = pe.Node(interface=util.Function(input_names=['tr', 'sparse'], 
                                                 output_names=['tr'], 
                                                 function=get_tr), name="tr_converter")
    ta = pe.Node(interface=util.Function(input_names=['real_tr', 'n_slices'], 
                                                 output_names=['ta'], 
                                                 function=get_ta), name="ta")
    
    slice_timing = pe.Node(interface=spm.SliceTiming(), name="slice_timing")
    
    def getTR(task_name):
        from variables import design_parameters
        return design_parameters[task_name]['TR']
    
    def getSparse(task_name):
        from variables import design_parameters
        return design_parameters[task_name]['sparse']
    
    
    pipeline.connect([(subjects_infosource, get_session_id, [('subject_id', 'subject_id')]),
                          (sessions_infosource, get_session_id, [('session', 'session')]),
                          (subjects_infosource, datasource, [('subject_id', 'subject_id')]),
                          (get_session_id, datasource, [('session_id', 'session_id')]),
                          (tasks_infosource, datasource, [('task_name', 'task_name')]),
                          
                          (datasource,skip, [("func", "in_file")]),
                          (skip, flip, [("roi_file", "in_file")]),
                          (flip, slice_timing, [("out_file", "in_files"),
                                                      (('out_file', get_n_slices), "num_slices"),
                                                      (('out_file', get_slice_order), "slice_order"),
                                                      (('out_file', get_ref_slice), "ref_slice")
                                                      ]),
                          (tasks_infosource, tr_convert, [(("task_name", getSparse), "sparse"),
                                                   (("task_name", getTR), "tr")]),
                          (tr_convert, slice_timing, [("tr", "time_repetition")]),
                          
                          (tr_convert, ta, [("tr", "real_tr")]),
                          (skip, ta, [(('roi_file', get_n_slices), "n_slices")]),
                          
                          (ta, slice_timing, [("ta", "time_acquisition")])
                          ])
    
    return pipeline

def create_realign_and_coregister_pipeline():
    pipeline = pe.Workflow(name="realign_and_coregister")
    pipeline.base_dir = os.path.join(working_dir, "group", "first_level", "preproc")
    
    subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                                  name="subjects_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)
    
    datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                                   outfields=['func']),
                         name = 'func_datasource', overwrite=True)
    datasource.inputs.base_directory = '/media/data/2010reliability/workdir_fmri/group/first_level/preproc/skip_and_slice_time/'
    datasource.inputs.template = '_session_*/_subject_id_%s/_task_name_%s/slice_timing/a*.nii'
    datasource.inputs.template_args = dict(func = [['subject_id', tasks]])
    datasource.inputs.sort_filelist = True
    pipeline.connect(subjects_infosource, "subject_id", datasource, "subject_id")
    
    rename = pe.MapNode(interface=util.Rename(), name="rename", iterfield = ["in_file", "format_string"])
    def new_name(list_of_lists):
        import os
        new_list = []
        for task in list_of_lists:
            assert len(task) == 2
            task.sort()
            _, fname1 = os.path.split(task[0])
            _, fname2 = os.path.split(task[1])
            new_list.append("first_"+fname1)
            new_list.append("second_"+fname2)
        return new_list
    
    def flat_list(list_of_lists):
        import os
        new_list = []
        for task in list_of_lists:
            new_list.append(task[0])
            new_list.append(task[1])
        return new_list
    
    pipeline.connect([(datasource, rename, [(("func", flat_list), "in_file"),
                                            (("func", new_name), "format_string")]),
                     ])
    
    realign = pe.Node(interface=spm.Realign(), name="realign")
    realign.inputs.register_to_mean = True
    pipeline.connect(rename, "out_file", realign, "in_files")
    
    
    struct_datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                                   outfields=['T1']),
                         name = 'struct_datasource')
    struct_datasource.inputs.base_directory = data_dir
    struct_datasource.inputs.template = '%s/*/*%s*.nii'
    struct_datasource.inputs.template_args = dict(T1 = [['subject_id', 'co_COR_3D_IR_PREP']])
    struct_datasource.inputs.sort_filelist = True
    
    coregister_T1s = pe.Node(interface=spm.Coregister(), name="coregister_T1s")
    coregister_T1s.jobtype = "estwrite"
    
    average_T1s = pe.Node(interface=fsl.maths.MultiImageMaths(op_string="-add %s -div 2"), name="average_T1s")
    
    def pickFirst(l):
        return l[0]
    
    def pickSecond(l):
        return l[1]
    
    pipeline.connect([(subjects_infosource, struct_datasource, [('subject_id', 'subject_id')]),
                           (struct_datasource, coregister_T1s, [(('T1', pickFirst), 'source'),
                                                                (('T1', pickSecond), 'target')]),
                           (coregister_T1s, average_T1s, [('coregistered_source', 'in_file')]),
                           (struct_datasource, average_T1s, [(('T1', pickSecond), 'operand_files')])
                      ])
    
    
    rename_dartel = pe.Node(util.Rename(format_string="subject_id_%(subject_id)s_struct"),
                            name = 'rename_dartel')
    rename_dartel.inputs.keep_ext = True
    pipeline.connect(average_T1s, "out_file", rename_dartel, "in_file")
    pipeline.connect(subjects_infosource, "subject_id", rename_dartel, "subject_id")
    
    coregister = pe.Node(interface=spm.Coregister(), name="coregister")
    coregister.inputs.jobtype = 'estimate'
    
    pipeline.connect([(realign, coregister,[('mean_image', 'source'),
                                           ('realigned_files','apply_to_files')]),
                      (rename_dartel, coregister,[('out_file', 'target')])
                      ])
    
    return pipeline

def create_model_fit_pipeline(high_pass_filter_cutoff=128, nipy = False, ar1 = True, name="model", save_residuals=False):
    inputnode = pe.Node(interface=util.IdentityInterface(fields=['outlier_files', 
                                                                 "realignment_parameters", 
                                                                 "functional_runs", 
                                                                 "mask_file",
                                                                 'conditions',
                                                                 'onsets',
                                                                 'durations',
                                                                 'TR',
                                                                 'contrasts',
                                                                 'contrasts_labels',
                                                                 'contrasts_indices',
                                                                 'units',
                                                                 'sparse',
                                                                 ]), name="inputnode")
    
    
    modelspec = pe.Node(interface=model.SpecifySPMModel(), name= "modelspec")
    if high_pass_filter_cutoff:
        modelspec.inputs.high_pass_filter_cutoff = high_pass_filter_cutoff
        
    def create_subject_inf(conditions, onsets, durations):
        from nipype.interfaces.base import Bunch
        return [Bunch(conditions=conditions,
                                    onsets=onsets,
                                    durations=durations,
                                    amplitudes=None,
                                    tmod=None,
                                    pmod=None,
                                    regressor_names=None,
                                    regressors=None)]
        
    create_subject_info = pe.Node(interface=util.Function(input_names=['conditions','onsets','durations'], 
                                                 output_names=['subject_info'], 
                                                 function=create_subject_inf), name="create_subject_info")
    
    modelspec.inputs.concatenate_runs        = True
    modelspec.inputs.output_units            = "secs"
    
    model_pipeline = pe.Workflow(name=name)
    
    model_pipeline.connect([(inputnode, create_subject_info, [('conditions','conditions'),
                                                               ('onsets','onsets'),
                                                                ('durations','durations')]),
                            (inputnode, modelspec,[('realignment_parameters','realignment_parameters'),
                                              ('functional_runs','functional_runs'),
                                              ('outlier_files','outlier_files'),
                                              ('units', 'input_units'),
                                              ('TR', 'time_repetition')]),
                            (create_subject_info, modelspec, [('subject_info', 'subject_info')]),
                            
                            ])
    
    level1design = pe.Node(interface=spm.Level1Design(), name= "level1design")
    level1design.inputs.bases              = {'hrf':{'derivs': [0,0]}}
    if ar1:
        level1design.inputs.model_serial_correlations = "AR(1)"
    else:
        level1design.inputs.model_serial_correlations = "none"
        
    level1design.inputs.timing_units       = modelspec.inputs.output_units
    
    def _get_microtime_resolution(volume, sparse):
        import nibabel as nb
        if isinstance(volume,list) and len(volume) == 1:
            volume = volume[0]
        nii = nb.load(volume)
        n_slices = nii.get_shape()[3]
        if sparse:
            return n_slices*2
        else:
            return n_slices
    
    microtime_resolution = pe.Node(interface=util.Function(input_names=['volume', 'sparse'], 
                                             output_names=['microtime_resolution'], 
                                             function=_get_microtime_resolution), name="microtime_resolution")
        
    level1estimate = pe.Node(interface=spm.EstimateModel(), name="level1estimate")
    level1estimate.inputs.estimation_method = {'Classical' : 1}
    
    contrastestimate = pe.Node(interface = spm.EstimateContrast(), name="contrastestimate")
    rename_t_maps = pe.MapNode(interface = Rename(format_string="%(contrast_name)s_t_map", keep_ext=True), name="rename_t_maps", iterfield=['in_file', 'contrast_name'] )
    
    threshold_topo_fdr = pe.MapNode(interface= spm.Threshold(), 
                                        name="threshold_topo_fdr", 
                                        iterfield=['contrast_index', 'stat_image'])
        
    threshold_topo_ggmm = neuroutils.CreateTopoFDRwithGGMM("threshold_topo_ggmm")
    
    model_pipeline.connect([                               
                            (modelspec, level1design,[('session_info','session_info')]),
                            (inputnode, level1design, [('mask_file','mask_image')]),
                            (inputnode, level1design, [('TR', 'interscan_interval'),
                                                       (("functional_runs", get_ref_slice), "microtime_onset")]),
                            (inputnode, microtime_resolution, [("functional_runs", "volume"),
                                                               ("sparse", "sparse")]),
                            (microtime_resolution, level1design, [("microtime_resolution", "microtime_resolution")]),                                   
                            (level1design,level1estimate,[('spm_mat_file','spm_mat_file')]),
                            (inputnode, contrastestimate, [('contrasts', 'contrasts')]),
                            (level1estimate,contrastestimate,[('spm_mat_file','spm_mat_file'),
                                                              ('beta_images','beta_images'),
                                                              ('residual_image','residual_image')]),
                            
                            (contrastestimate, rename_t_maps, [('spmT_images', 'in_file')]),
                            (inputnode, rename_t_maps, [('contrasts_labels', 'contrast_name')]),
                            
                            (contrastestimate, threshold_topo_fdr, [('spm_mat_file','spm_mat_file')]),
                            (rename_t_maps, threshold_topo_fdr , [('out_file', 'stat_image')]),
                            (inputnode, threshold_topo_fdr, [('contrasts_indices', 'contrast_index')]),
                            
                            (level1estimate, threshold_topo_ggmm, [('mask_image','inputnode.mask_file')]),
                            (contrastestimate, threshold_topo_ggmm, [('spm_mat_file','inputnode.spm_mat_file')]),
                            (rename_t_maps, threshold_topo_ggmm , [('out_file', 'inputnode.stat_image')]),
                            (inputnode, threshold_topo_ggmm, [('contrasts_indices', 'inputnode.contrast_index')]),
                            ])
    
    return model_pipeline

#pipeline = create_skip_and_slice_time_piepeline()
#pipeline.write_graph()
#pipeline.run(plugin_args={'n_procs': 4})
#
#pipeline = create_realign_and_coregister_pipeline()
#pipeline.write_graph()
#pipeline.run(plugin_args={'n_procs': 4})

datasource_dartel = pe.MapNode(interface=nio.DataGrabber(infields=['subject_id'],
                                                         outfields=['struct']),
                               name = 'datasource_dartel', 
                               iterfield = ['subject_id'])
datasource_dartel.inputs.base_directory = "/media/data/2010reliability/workdir_fmri/group/first_level/preproc/realign_and_coregister/"

datasource_dartel.inputs.template = '_subject_id_%s/rename_dartel/subject_id_%s_struct.nii'
datasource_dartel.inputs.template_args = dict(struct=[['subject_id', 'subject_id']])
datasource_dartel.inputs.subject_id = subjects

dartel_workflow = spm_wf.create_DARTEL_template(name='dartel_workflow')
dartel_workflow.inputs.inputspec.template_prefix = "template"

def pickFieldFlow(dartel_flow_fields, subject_id):
    from nipype.utils.filemanip import split_filename
    for f in dartel_flow_fields:
        _, name, _ = split_filename(f)
        if name.find("subject_id_%s"%subject_id) != -1:
            return f
        
    raise Exception
        
pick_flow = pe.Node(util.Function(input_names=['dartel_flow_fields', 'subject_id'], output_names=['dartel_flow_field'], function = pickFieldFlow),
                    name = "pick_flow")

subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                              name="subjects_infosource")
subjects_infosource.iterables = ('subject_id', subjects)

tasks_infosource = pe.Node(interface=util.IdentityInterface(fields=['task_name']),
                           name="tasks_infosource")
tasks_infosource.iterables = ('task_name', tasks)

sessions_infosource = pe.Node(interface=util.IdentityInterface(fields=['session']),
                              name="sessions_infosource")
sessions_infosource.iterables = ('session', sessions)

func_datasource = pe.Node(interface=nio.DataGrabber(infields=['task_name', 'session', 'subject_id', 'session_id'],
                                                   outfields=['func', 'realignment_parameters', 'line_bisection_log']),
                         name = 'func_datasource', overwrite=True)
func_datasource.inputs.base_directory = '/media/data/2010reliability/'
func_datasource.inputs.template = 'workdir_fmri/group/first_level/preproc/realign_and_coregister/_subject_id_%s/%s/r*%s*_%s*.%s'
func_datasource.inputs.template_args = dict(func = [['subject_id', 'coregister', 'session', 'task_name', 'nii']],
                                            realignment_parameters = [['subject_id', 'realign', 'session', 'task_name', 'txt']],
                                            line_bisection_log = [['subject_id', 'session_id', 'session_id']])
func_datasource.inputs.field_template = dict(line_bisection_log= 'data/%s/%s/logs/*%s-Line_Bisection.log')
func_datasource.inputs.sort_filelist = True

struct_datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                                         outfields=['struct']),
                               name = 'struct_datasource')
struct_datasource.inputs.base_directory = "/media/data/2010reliability/workdir_fmri/group/first_level/preproc/realign_and_coregister/"

struct_datasource.inputs.template = '_subject_id_%s/rename_dartel/subject_id_%s_struct.nii'
struct_datasource.inputs.template_args = dict(struct=[['subject_id', 'subject_id']])

normalize_func_pipeline = create_normalize_and_artdetect_func()
normalize_struct_pipeline = create_normalize_and_skullstrip_struct()

model_pipeline = create_model_fit_pipeline()

datasink = pe.Node(interface = nio.DataSink(), name='datasink')
datasink.inputs.base_directory = results_dir
datasink.inputs.regexp_substitutions = [
                                        (r'(?P<r1>_[^-/]*)(?P<id>[0-9]+)(?P<r2>[/])', r'/\g<id>'),
                                        ]

level1 = pe.Workflow(name="main")
level1.base_dir = os.path.join(working_dir, "group", "first_level")

def getConditions(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['conditions']
    
def getOnsets(task_name, line_bisection_log, delay):
    if task_name == "line_bisection":
        from parse_line_bisection_log import parse_line_bisection_log
        _,_,correct_pictures, incorrect_pictures, noresponse_pictures = parse_line_bisection_log(line_bisection_log, delay)
        return [correct_pictures["task"], incorrect_pictures["task"], noresponse_pictures["task"],
                sorted(correct_pictures["rest"] + incorrect_pictures["rest"]), noresponse_pictures["rest"]]
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

def getContrastsLabels(task_name):
    from variables import design_parameters
    contrasts = design_parameters[task_name]['contrasts']
    return [ contrast[0].lower() for contrast in contrasts]
    
def getContrastsIndices(task_name):
    from variables import design_parameters
    contrasts = design_parameters[task_name]['contrasts']
    return range(1,len(contrasts)+1)

def getUnits(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['units']

def getSparse(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['sparse']



get_onsets = pe.Node(interface=util.Function(input_names=['task_name', 'line_bisection_log', 'delay'], 
                                                    output_names=['onsets'], 
                                                    function=getOnsets),
                     name="get_onsets")
get_onsets.inputs.delay = 4*2.5

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

get_session_id = pe.Node(interface=util.Function(input_names=['session', 'subject_id'], 
                                                    output_names=['session_id'], 
                                                    function=getSessionId), 
                         name="get_session_id")


level1.connect([(datasource_dartel, dartel_workflow, [('struct','inputspec.structural_files')]),
                (dartel_workflow, pick_flow, [('outputspec.flow_fields', 'dartel_flow_fields')]),
                (subjects_infosource, pick_flow, [('subject_id', 'subject_id')]),
                
                (subjects_infosource, get_session_id, [('subject_id', 'subject_id')]),
                (sessions_infosource, get_session_id, [('session', 'session')]),
                (subjects_infosource, func_datasource, [('subject_id', 'subject_id')]),
                (get_session_id, func_datasource, [('session_id', 'session_id')]),
                
                (tasks_infosource, func_datasource, [("task_name", "task_name")]),
                (sessions_infosource, func_datasource, [("session", "session")]),
                
                (subjects_infosource, struct_datasource, [("subject_id", "subject_id")]),
                
                (struct_datasource, normalize_struct_pipeline, [('struct', 'inputnode.struct')]),
                (pick_flow, normalize_struct_pipeline, [('dartel_flow_field', 'inputnode.flowfield_files')]),
                (dartel_workflow, normalize_struct_pipeline, [('outputspec.template_file', 'inputnode.template_file')]),
                
                (normalize_struct_pipeline, normalize_func_pipeline, [('outputnode.mask_file', 'inputnode.mask_file')]),
                (func_datasource, normalize_func_pipeline, [('func', 'inputnode.func'),
                                                       ('realignment_parameters', 'inputnode.realignment_parameters')]),
                (pick_flow, normalize_func_pipeline, [('dartel_flow_field', 'inputnode.flowfield_files')]),
                (dartel_workflow, normalize_func_pipeline, [('outputspec.template_file', 'inputnode.template_file')]),
                
                (func_datasource, model_pipeline, [('realignment_parameters', 'inputnode.realignment_parameters')]),
                (normalize_func_pipeline, model_pipeline, [('outputnode.outlier_files', 'inputnode.outlier_files'),
                                                           ('outputnode.preprocessed_files', 'inputnode.functional_runs')]),
                (normalize_struct_pipeline, model_pipeline, [('outputnode.mask_file', 'inputnode.mask_file')]),
                
                (tasks_infosource, model_pipeline, [(('task_name', getConditions), 'inputnode.conditions'),
                                                    (('task_name', getDurations), 'inputnode.durations'),
                                                    (('task_name', getTR), 'inputnode.TR'),
                                                    (('task_name', getContrasts), 'inputnode.contrasts'),
                                                    (('task_name', getContrastsLabels), 'inputnode.contrasts_labels'),
                                                    (('task_name', getContrastsIndices), 'inputnode.contrasts_indices'),
                                                    (('task_name', getUnits), 'inputnode.units'),
                                                    (('task_name', getSparse), 'inputnode.sparse')]),
                (tasks_infosource, get_onsets, [('task_name', 'task_name')]),
                (func_datasource, get_onsets, [('line_bisection_log', 'line_bisection_log')]),
                (get_onsets, model_pipeline, [('onsets', 'inputnode.onsets')]),
                
                (model_pipeline, datasink, [('contrastestimate.con_images', 'volumes.con_images')]),
                (model_pipeline, datasink, [('contrastestimate.spmT_images', 'volumes.spmT_images')]),
                (model_pipeline, datasink, [('level1estimate.mask_image', 'volumes.mask_image')]),
                ])
level1.write_graph()
level1.run(plugin_args={'n_procs': 4})

