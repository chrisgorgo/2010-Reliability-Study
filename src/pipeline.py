import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
from nipype.interfaces import fsl
from helper_functions import create_pipeline_functional_run

from confidential_variables import subjects

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
                                                  onsets=[[  16.25,   81.25,  146.25,  211.25,  276.25,  341.25,  406.25, 471.25],
                                                          [  48.75,  113.75,  178.75,  243.75,  308.75,  373.75,  438.75, 503.75]],
                                                  durations=[[16.25], [16.25]],
                                                  tr=2.5, 
                                                  contrasts=[('Task-Control','T', ['Task', 'Control'],[1,-1]),
                                                             ('Task','T', ['Task'],[1]),
                                                             ('Control','T', ['Control'],[1])],
                                                  units='secs')

main_pipeline = pe.Workflow(name="pipeline")
main_pipeline.base_dir = os.path.join(data_dir,"workdir")
main_pipeline.connect([(subjects_infosource, datasource, [('subject_id', 'subject_id')]),
                       (datasource, finger_foot_lips, [("finger_foot_lips", "inputnode.func"),
                                                       ("T1","inputnode.struct")]),
                       (datasource, overt_verb_generation, [("verb_generation", "inputnode.func"),
                                                            ("T1","inputnode.struct")]),
                       (datasource, silent_verb_generation, [("silent_verb_generation", "inputnode.func"),
                                                            ("T1","inputnode.struct")]),
                       (datasource, overt_word_repetition, [("word_repetition", "inputnode.func"),
                                                            ("T1","inputnode.struct")]),
                       (datasource, line_bisection, [("line_bisection", "inputnode.func"),
                                                     ("T1","inputnode.struct")]),
                       ])

main_pipeline.run()