from nipype.utils.config import config
import os
from StringIO import StringIO

b22 = [442, 446, 458, 460, 764, 765, 766, 767]
b45 = [602, 603,]
b44 = [689, 690, 748, 749,]
right_parietal = [int(a) for a in ['777',
 '778',
 '780',
 '782',
 '786',
 '793',
 '795',
 '797',
 '798',
 '802',
 '806',
 '807',
 '858',
 '859',
 '862',
 '864',
 '875',
 '880',
 '881',
 '883',
 '889',
 '892',
 '894',
 '896',
 '928',
 '930',
 '964',
 '966',
 '970',
 '972',
 '975',
 '977',
 '987',
 '989',
 '991',
 '993',
 '997',
 '998',
 '1000',
 '1015',
 '1019',
 '1038',
 '1040',
 '1042',
 '1044',
 '1050',
 '1062',
 '1066',
 '1067',
 '1072',
 '1073',
 '1081',
 '1096',
 '1098',
 '1099',
 '1102',
 '1105']]


design_parameters = {'finger_foot_lips':{'conditions': ['Finger', 'Foot', 'Lips'],
                                         'units': 'scans',
                                         'onsets': [[0, 36, 72, 108, 144],
                                                    [12, 48, 84, 120, 156],
                                                    [24, 60, 96, 132, 168]],
                                         'durations': [[6], [6], [6]],
                                         'sparse': False,
                                         'TR': 2.5, 
                                         'contrasts': [('Finger','T', ['Finger'],[1]),
                                                       ('Foot','T', ['Foot'],[1]),
                                                       ('Lips','T', ['Lips'],[1]),
                                                       ('Finger_vs_Other', 'T',['Finger','Foot','Lips'], [1,    -0.5,-0.5]),
                                                       ('Foot_vs_Other', 'T',  ['Finger','Foot','Lips'], [-0.5,  1,  -0.5]),
                                                       ('Lips_vs_Other', 'T',  ['Finger','Foot','Lips'], [-0.5, -0.5, 1  ])
                                                       ],
                                         'mask_file': '/media/data/2010reliability/Masks/ROI_Motor_cortex_MNI_bin_left.nii',
                                         'atlas_labels': [804,805,806,807,808],
                                         'dilation': 2},
                     "overt_verb_generation":{'conditions': ['Task'],
                                              'units': 'scans',
                                              'onsets': [[0, 12, 24, 36, 48, 60, 72]],
                                              'durations': [[6]],
                                              'sparse': True,
                                              'TR': 5.0,
                                              'contrasts': [('Task','T', ['Task'],[1])],
                                              'atlas_labels': b45 + b44,
                                              'mask_file': '/media/data/2010reliability/Masks/ROI_Broca_area_MNI.img',
                                              'dilation': 6},
                     "overt_word_repetition": {'conditions':['Task'],
                                               'units': 'scans',
                                               'onsets': [[0, 12, 24, 36, 48, 60]],
                                               'durations': [[6]],
                                               'sparse': True,
                                               'TR': 5.0,
                                               'contrasts': [('Task','T', ['Task'],[1])],
                                               'atlas_labels': b22,
                                               'mask_file': '/media/data/2010reliability/Masks/ROI_Wernicke_area_MNI.img',
                                               'dilation': 12},
                     'covert_verb_generation':{'conditions': ['Task'],
                                               'units': 'scans',
                                               'onsets': [[0, 24, 48, 72, 96, 120, 144]],
                                               'durations': [[12]],
                                               'sparse': False,
                                               'TR': 2.5,
                                               'contrasts': [('Task','T', ['Task'],[1])],
                                               'atlas_labels': b45 + b44,
                                               'mask_file': '/media/data/2010reliability/Masks/ROI_Broca_area_MNI.img',
                                               'dilation': 6},
                     'line_bisection':{'conditions': ['Correct_Task', 'Incorrect_Task', 'No_Response_Task',
                                                      'Response_Control', 'No_Response_Control'],
                                       'units': 'secs',
                                       'onsets': [[  16.25,   81.25,  146.25,  211.25,  276.25,  341.25,  406.25, 471.25, 536.25],
                                                  [  48.75,  113.75,  178.75,  243.75,  308.75,  373.75,  438.75, 503.75, 568.75]],
                                       'durations': [[0], [0], [0], [0], [0]],
                                       'sparse': False,
                                       'TR': 2.5,
                                       'contrasts': [('Task_All_Greater_Than_Control_All','T', ['Correct_Task', 'Incorrect_Task', 'No_Response_Task',
                                                      'Response_Control', 'No_Response_Control'],[1,1,1,-1,-1]),
                                                     ('Task_Answered_Greater_Than_Control_Answered','T', ['Correct_Task', 'Incorrect_Task', 
                                                      'Response_Control'],[1,1,-1]),
                                                     ('Task_Correct_Greater_Than_Control_Answered','T', ['Correct_Task', 'Response_Control'],[1,-1]),
                                                     ('Task_Correct_Greater_Than_Task_Incorrect','T', ['Correct_Task', 'Incorrect_Task'],[1,-1])],
                                       'atlas_labels': right_parietal,
                                       'mask_file': '/media/data/2010reliability/Masks/ROI_Broca_area_MNI.img', #TODO BOGUS!
                                       'dilation': 2}
                     }

def getStatLabels(task_name):
    from variables import design_parameters
    return [contrast[0] for contrast in design_parameters[task_name]['contrasts']]

data_dir = '/media/data/2010reliability/data'
results_dir = "/home/filo/workspace/2010reliability/results"
working_dir = '/media/data/2010reliability/workdir_fmri'
dbfile = os.path.join(results_dir, "results.db")
tasks = ["finger_foot_lips", "covert_verb_generation", "overt_word_repetition", 'overt_verb_generation', "line_bisection"]# 'overt_verb_generation', "covert_verb_generation", "finger_foot_lips", "overt_word_repetition"]#, "]
thr_methods = ['topo_fdr','topo_ggmm']
sessions = ['first', 'second']
roi = [False]#,True]

subjects = [
            '08143633-aec2-49a9-81cf-45867827b871',
            '3a3e1a6f-dc92-412c-870a-74e4f4e85ddb',
            '8bb20980-2dc4-4da9-9065-879e2e7e1fbe',
            '8d80a62b-aa21-49bd-b8ca-9bc678ffe7b0',
            '90bafbe8-c67f-4388-b677-27fcf2427c71',
            '94cfb26f-0060-4c44-b59f-702ca61143ca',
            'c2cc1c59-df88-4366-9f99-73b722235789',
            'cf48f394-1912-4202-89f7-dbf8ef9d6e19',
            'df4808a4-ecce-4d0a-9fe2-535c0720ec17',
            'e094aae5-8387-4b5c-bf56-df4a88623c5d',
            ]

lefties = ['8d80a62b-aa21-49bd-b8ca-9bc678ffe7b0',
           '90bafbe8-c67f-4388-b677-27fcf2427c71',
           '08143633-aec2-49a9-81cf-45867827b871']

exceptions = [{'task_name': 'overt_word_repetition', 'subject_id': "c2cc1c59-df88-4366-9f99-73b722235789", "which": "second"},
              {'task_name': 'overt_verb_generation', 'subject_id': "df4808a4-ecce-4d0a-9fe2-535c0720ec17", "which": "second"}]

exclude_subjects = {"overt_verb_generation": ["3a3e1a6f-dc92-412c-870a-74e4f4e85ddb", "e094aae5-8387-4b5c-bf56-df4a88623c5d"]}


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