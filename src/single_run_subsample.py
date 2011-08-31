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

blocks_infosource = pe.Node(interface=util.IdentityInterface(fields=['blocks']),
                              name="blocks_infosource")
blocks_infosource.iterables = ('blocks', [1,2,3,4,5])

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'task_name', 'session_id'],
                                               outfields=['func', 
                                                          'realignment_parameters', 
                                                          'outlier_files',
                                                          'mask_file',
                                                          'struct',
                                                          'roi_mask']),
                     name = 'datasource')

datasource.inputs.base_directory = "/media/data/2010reliability/workdir_fmri/pipeline"
datasource.inputs.template = '%s/%s/*[0-9]_%s*.nii'
datasource.inputs.template_args = dict(func = [['subject_id', 'session_id', 'task_name']],
                                       realignment_parameters = [['subject_id', 'session_id', 'task_name']],
                                       outlier_files = [['subject_id', 'session_id', 'task_name']],
                                       mask_file = [['subject_id', 'session_id', 'task_name']],
                                       struct = [['subject_id']],
                                       roi_mask = [['task_name']])
datasource.inputs.field_template = dict(func= 'functional_run/preproc_func/susan_smooth/_subject_id_%s/_session_%s/_task_name_%s/smooth/mapflow/_smooth0/*_smooth.nii',
                                        realignment_parameters = 'functional_run/preproc_func/_subject_id_%s/_session_%s/_task_name_%s/realign/r*.txt',
                                        outlier_files = 'functional_run/preproc_func/_subject_id_%s/_session_%s/_task_name_%s/art/art*.txt',
                                        mask_file = 'functional_run/preproc_func/_subject_id_%s/_session_%s/_task_name_%s/compute_mask/brain_mask.nii',
                                        struct = '_subject_id_%s/normalize/wmr*maths.nii',
                                        roi_mask = "_subject_id_3a3e1a6f-dc92-412c-870a-74e4f4e85ddb/_task_name_%s/reslice_roi_mask/rdialted_mask.nii")
datasource.inputs.sort_filelist = True


functional_run = create_pipeline_functional_run(name="functional_run", series_format="4d", preproc=False)

main_pipeline = pe.Workflow(name="single_run_subsample_pipeline")
main_pipeline.base_dir = working_dir

def getReportFilename(subject_id):
    return "subject_%s_report.pdf"%subject_id

def getConditions(task_name):
    from variables import design_parameters
    return design_parameters[task_name]['conditions']
    
def getOnsets(task_name):
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

subsample = pe.Node(interface=fsl.ExtractROI(t_min=0), name="subsample")

def getBlocks2scans(blocks, durations):
    block_duration = 0
    for i in durations:
        for j in i:
            block_duration += 2*j
    return blocks*block_duration

blocks2scans = pe.Node(interface=util.Function(input_names=['blocks', 'durations'], 
                                                    output_names=['scans'], 
                                                    function=getBlocks2scans), 
                         name="blocks2scans")
def getTrimRParams(realignment_parameters, scans):
    import os
    f_in = open(realignment_parameters)
    f_out = open("realignment_parameters_out.txt", "w")
    line_count = 0
    for line in f_in:
        f_out.write(line)
        line_count+=1
        if line_count >= scans:
            break
    f_in.close()
    f_out.close()
    return os.path.abspath("realignment_parameters_out.txt")

trimRParams = pe.Node(interface=util.Function(input_names=['realignment_parameters', 'scans'], 
                                                    output_names=['realignment_parameters'], 
                                                    function=getTrimRParams), 
                         name="trimRParams")

def getOutliers(outlier_files, scans):
    import os
    f_in = open(outlier_files)
    f_out = open("outlier_files_out.txt", "w")
    for line in f_in:
        if int(line) <= scans:
            f_out.write(line)
        else:
            break
    f_in.close()
    f_out.close()
    return os.path.abspath("outlier_files_out.txt")

trimOutliers = pe.Node(interface=util.Function(input_names=['outlier_files', 'scans'], 
                                                    output_names=['outlier_files'], 
                                                    function=getOutliers), 
                         name="trimOutliers")



main_pipeline.connect([                       
                       (subjects_infosource, datasource, [('subject_id', 'subject_id')]),
                       (sessions_infosource, datasource, [('session', 'session_id')]),
                       (tasks_infosource, datasource, [('task_name', 'task_name')]),
                       
                       (blocks_infosource, blocks2scans, [("blocks", 'blocks')]),
                       (tasks_infosource, blocks2scans, [(('task_name', getDurations), 'durations')]),
                       (blocks2scans, subsample, [("scans", "t_size")]),
                       (datasource, subsample, [("func", "in_file")]),
                       (subsample, functional_run, [("roi_file", "model.inputnode.functional_runs")]),
                       
                       (blocks2scans, trimRParams, [("scans", "scans")]),
                       (datasource, trimRParams, [("realignment_parameters", "realignment_parameters")]),
                       (trimRParams, functional_run, [("realignment_parameters", "model.inputnode.realignment_parameters"),
                                                      ("realignment_parameters", "report.inputnode.realignment_parameters")]),
                       
                       (blocks2scans, trimOutliers, [("scans", "scans")]),
                       (datasource, trimOutliers, [("outlier_files", "outlier_files")]),
                       (trimOutliers, functional_run, [("outlier_files", "model.inputnode.outlier_files"),
                                                      ("outlier_files", "report.inputnode.outlier_files")]),
                                                  
                       
                       (thr_method_infosource, functional_run, [('thr_method', 'model.thr_method_inputspec.thr_method'),
                                                                ('thr_method', 'report.visualise_thresholded_stat.inputnode.prefix')]),
                       (roi_infosource, functional_run, [('roi', 'model.roi_inputspec.roi')]),
                       (datasource, functional_run, [("mask_file", "model.inputnode.mask"),
                                                     ("roi_mask", "inputnode.mask_file"),
                                                     ("struct", "report.inputnode.struct")]),
                       
                       (tasks_infosource, functional_run, [(('task_name', getConditions), 'inputnode.conditions'),
                                                           (('task_name', getDurations), 'inputnode.durations'),
                                                           (('task_name', getTR), 'inputnode.TR'),
                                                           (('task_name', getContrasts), 'inputnode.contrasts'),
                                                           (('task_name', getUnits), 'inputnode.units'),
                                                           (('task_name', getSparse), 'inputnode.sparse'),
                                                           (('task_name', getOnsets), 'inputnode.onsets'),
                                                           ('task_name', 'inputnode.task_name')]),
                       ])

main_pipeline.run()
                       
                       
                       
                       