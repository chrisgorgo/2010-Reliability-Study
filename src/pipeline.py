import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
from neuroutils.helper_functions import (create_pipeline_functional_run, 
                                         create_dwi_pipeline,
                                         create_prepare_seeds_from_fmri_pipeline)

from confidential_variables import subjects
from nipype.interfaces.utility import Merge
import neuroutils
from nipype.utils.config import config
from StringIO import StringIO

config.readfp(StringIO("""
[execution]
stop_on_first_crash = true
hash_method = timestamp
plugin = IPython
"""))


data_dir = os.path.abspath('/media/data/2010reliability/')

info = dict(T1 = [['subject_id','[0-9]_co_COR_3D_IR_PREP']],
            word_repetition = [['subject_id','[0-9]_word_repetition']],
            verb_generation = [['subject_id','[0-9]_verb_generation']],
            silent_verb_generation = [['subject_id', '[0-9]_silent_verb_generation']],
            line_bisection = [['subject_id', '[0-9]_line_bisection']],
            finger_foot_lips = [['subject_id', '[0-9]_finger_foot_lips']],
            dwi = [['subject_id', '[0-9]_DTI_64G_2.0_mm_isotropic']],
            dwi_bval = [['subject_id', '[0-9]_DTI_64G_2.0_mm_isotropic']],
            dwi_bvec = [['subject_id', '[0-9]_DTI_64G_2.0_mm_isotropic']])

subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="subjects_infosource")
subjects_infosource.iterables = ('subject_id', subjects)

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.base_directory = data_dir
datasource.inputs.template = 'E10800_CONTROL/%s_*/*/*%s.nii'
datasource.inputs.field_template = dict(dwi_bval=datasource.inputs.template.replace("nii", "bval"),
                                        dwi_bvec=datasource.inputs.template.replace("nii", "bvec"))
datasource.inputs.template_args = info

finger_foot_lips = create_pipeline_functional_run(name="finger_foot_lips", 
                                                  conditions=['Finger', 'Foot', 'Lips'], 
                                                  onsets=[[0, 36, 72, 108, 144],
                                                          [12, 48, 84, 120, 156],
                                                          [24, 60, 96, 132, 168]],
                                                  durations=[[6], [6], [6]],
                                                  tr=2.5, 
                                                  contrasts=[('Finger','T', ['Finger'],[1]),
                                                             ('Foot','T', ['Foot'],[1]),
                                                             ('Lips','T', ['Lips'],[1])],
                                                  units='scans')

overt_verb_generation = create_pipeline_functional_run(name="overt_verb_generation", 
                                                  conditions=['Task'], 
                                                  onsets=[[0, 12, 24, 36, 48, 60, 72]],
                                                  durations=[[6]],
                                                  tr=5.0, 
                                                  contrasts=[('Task','T', ['Task'],[1])],
                                                  units='scans',
                                                  sparse=True)

silent_verb_generation = create_pipeline_functional_run(name="silent_verb_generation", 
                                                  conditions=['Task'], 
                                                  onsets=[[0, 24, 48, 72, 96, 120, 144]],
                                                  durations=[[12]],
                                                  tr=2.5, 
                                                  contrasts=[('Task','T', ['Task'],[1])],
                                                  units='scans')

overt_word_repetition = create_pipeline_functional_run(name="overt_word_repetition", 
                                                  conditions=['Task'], 
                                                  onsets=[[0, 12, 24, 36, 48, 60]],
                                                  durations=[[6]],
                                                  tr=5.0, 
                                                  contrasts=[('Task','T', ['Task'],[1])],
                                                  units='scans',
                                                  sparse=True)

line_bisection = create_pipeline_functional_run(name="line_bisection", 
                                                  conditions=['Task', 'Control'], 
                                                  onsets=[[  16.25,   81.25,  146.25,  211.25,  276.25,  341.25,  406.25, 471.25, 536.25],
                                                          [  48.75,  113.75,  178.75,  243.75,  308.75,  373.75,  438.75, 503.75, 568.75]],
                                                  durations=[[16.25], [16.25]],
                                                  tr=2.5, 
                                                  contrasts=[('Task-Control','T', ['Task', 'Control'],[1,-1]),
                                                             ('Task','T', ['Task'],[1]),
                                                             ('Control','T', ['Control'],[1])],
                                                  units='secs')

finger_foot_lips_seed = create_prepare_seeds_from_fmri_pipeline("finger_foot_lips_seed")

proc_dwi = create_dwi_pipeline()

mergeinputs = pe.Node(interface=Merge(20), name="mergeinputs")

psmerge = pe.Node(interface = neuroutils.PsMerge(), name = "psmerge")

def getReportFilename(subject_id):
    return "subject_%s_report.pdf"%subject_id

def getConditions(task_name):
    conditions_dict = {'finger_feet_lips': ['Finger', 'Foot', 'Lips'], 
                       "overt_verb_generation": ['Task']}
    return conditions_dict[task_name]
    
def getOnsets(task_name):
    onsets_dict = {'finger_feet_lips': [[0, 36, 72, 108, 144],
                                        [12, 48, 84, 120, 156],
                                        [24, 60, 96, 132, 168]], 
                   "overt_verb_generation": [[0, 12, 24, 36, 48, 60, 72]]}
    return onsets_dict[task_name]

    
def getDurations(task_name):
    durations_dict = {'finger_feet_lips': [[6], [6], [6]], 
                   "overt_verb_generation": [[6]]}
    return durations_dict[task_name]

def getTR(task_name):
    tr_dict = {'finger_feet_lips': 2.5, 
                   "overt_verb_generation": 2.5}
    return tr_dict[task_name]

main_pipeline = pe.Workflow(name="pipeline")
main_pipeline.base_dir = os.path.join(data_dir,"workdir")
main_pipeline.connect([
                       (subjects_infosource, datasource, [('subject_id', 'subject_id')]),
                       (task_infosource, datasource, [('task_name', 'task_name')]),
                       
                       
                       (datasource, finger_foot_lips, [("finger_foot_lips", "inputnode.func"),
                                                       ("T1","inputnode.struct")]),
                       (task_infosource, functional_run, [(('task_name', getConditions), 'conditions')] )
#                       (finger_foot_lips, finger_foot_lips_seed, [("preproc_func.coregister.coregistered_source","inputnode.epi"),
#                                                                  ("preproc_func.compute_mask.brain_mask", "inputnode.mask"),
#                                                                  ("model.contrastestimate.spmT_images","inputnode.stat"),
#                                                                  ]),
#                       (datasource, finger_foot_lips_seed, [("dwi", "inputnode.dwi"),
#                                                            ("T1", "inputnode.T1")]),
#                       
#                       (finger_foot_lips, mergeinputs, [("preproc_func.plot_realign.plot", "in1")]),                                
#                       (finger_foot_lips, mergeinputs, [("report.psmerge_raw.merged_file", "in2")]),
#                       (finger_foot_lips, mergeinputs, [("report.psmerge_th.merged_file", "in3")]),
#                       (finger_foot_lips, mergeinputs, [("report.psmerge_ggmm_th.merged_file", "in4")]),
#                       
                       (datasource, overt_verb_generation, [("verb_generation", "inputnode.func"),
                                                            ("T1","inputnode.struct")]),
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
#                       (datasource, proc_dwi, [("dwi", "inputnode.dwi"),
#                                               ("dwi_bval", "inputnode.bvals"),
#                                               ("dwi_bvec", "inputnode.bvecs")]),
#                       (proc_dwi, finger_foot_lips_seed, [("bedpostx.outputnode.thsamples", "inputnode.thsamples"),
#                                                          ("bedpostx.outputnode.phsamples", "inputnode.phsamples"),
#                                                          ("bedpostx.outputnode.fsamples", "inputnode.fsamples")]),
#                       
#                       (mergeinputs, psmerge, [("out", "in_files")]),
#                       (subjects_infosource, psmerge, [(("subject_id", getReportFilename), "out_file")])
                       ])

#main_pipeline.run()
main_pipeline.write_graph(graph2use='flat')
main_pipeline.write_hierarchical_dot("hierarchical.dot")