import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm
import nipype.interfaces.fsl as fsl
from helper_functions import (create_pipeline_functional_run)

from StringIO import StringIO
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import *


def create_group_analysis(task_name):
    
    def getContrasts(task_name):
        from variables import design_parameters
        return range(1, len(design_parameters[task_name]['contrasts'])+1)
    
    pipeline = pe.Workflow(name="group_analysis_"+task_name)
    pipeline.base_dir = working_dir

    contrasts_infosource = pe.Node(interface=util.IdentityInterface(fields=['contrast_no']),
                               name="contrasts_infosource")
    contrasts_infosource.iterables = ('contrast_no', getContrasts(task_name))
    
    sessions_infosource = pe.Node(interface=util.IdentityInterface(fields=['session']),
                                  name="sessions_infosource")
    sessions_infosource.iterables = ('session', sessions)
    
    datasource = pe.Node(interface=nio.DataGrabber(infields=['task_name', 'contrast_no'],
                                                   outfields=['con_images_first', 'con_images_second']),
                         name = 'datasource', overwrite=True)
    
    datasource.inputs.base_directory = "/home/filo/workspace/2010reliability/results/volumes/con_images"
    datasource.inputs.template = '_subject_id_*/_session_%s/_task_name_%s/con_%04d.img'
    datasource.inputs.template_args = dict(con_images_first = [['first', 'task_name', 'contrast_no']],
                                           con_images_second = [['second', 'task_name', 'contrast_no']],)
    datasource.inputs.sort_filelist = True
    
    pipeline.connect(contrasts_infosource, "contrast_no", datasource, "contrast_no")
    #datasource.inputs.session = "first"
    datasource.inputs.task_name = task_name
    
    average = pe.MapNode(interface=fsl.maths.MultiImageMaths(op_string="-add %s -div 2"), name="average",
                         iterfield=['in_file', 'operand_files'])
    pipeline.connect([(datasource, average, [('con_images_first', 'in_file'),
                                             ('con_images_second', 'operand_files')])
                      ])
    #reslice = pe.MapNode(interface=spm.Coregister(jobtype="write"), name='reslice', iterfield=['source'])
    
    def srtSubjects(in_files):
        from variables import subjects
        import re
        mapping = [(subject, dict(scans=['',''],conds=[1,2])) for subject in subjects]
        tmp_dict = dict(mapping)
        print tmp_dict
        for file in in_files:
            subject_id = re.findall(r'_subject_id_([0-9a-z\-]+)',file)[0]
            session_no = int((re.findall(r'_session_([a-z]+)',file)[0] == 'second'))
            print subject_id
            tmp_dict[subject_id]['scans'][session_no] = file
        return tmp_dict.values()
    
    design = pe.Node(interface=spm.OneSampleTTestDesign(), name="design")
    pipeline.connect([(average, design, [('out_file', 'in_files')])
                      ])
#    
#    if subset == "all":
#        pipeline.connect([(datasource, onesamplettestdes, [('con_images', 'in_files')])
#                      ])
#    elif subset == "righties":
#        def pick_subjects(l):
#            from variables import subjects, lefties
#            righties = list(set(subjects) - set(lefties))
#            l_out = []
#            for item in l:
#                for subject in righties:
#                    if subject in item:
#                        l_out.append(item)
#            return l_out
#        pipeline.connect([(datasource, onesamplettestdes, [(('con_images', pick_subjects), 'in_files')])
#                      ])
#    elif subset == "lefties":
#        def pick_subjects(l):
#            from variables import subjects, lefties
#            l_out = []
#            for item in l:
#                for subject in lefties:
#                    if subject in item:
#                        l_out.append(item)
#            return l_out
#        pipeline.connect([(datasource, onesamplettestdes, [(('con_images', pick_subjects), 'in_files')])
#                      ])
    
    #reslice.inputs.target = '/media/data/2010reliability/normsize.nii'
        

    #pipeline.connect(reslice, "coregistered_source", onesamplettestdes, "in_files")
    
    l2estimate = pe.Node(interface=spm.EstimateModel(), name="level2estimate")
    l2estimate.inputs.estimation_method = {'Classical' : 1}
    pipeline.connect(design, "spm_mat_file", l2estimate, "spm_mat_file")
    
    l2conestimate = pe.Node(interface = spm.EstimateContrast(), name="level2conestimate")
    cont1 = ('Group','T', ['mean'],[1])
    l2conestimate.inputs.contrasts = [cont1]
    l2conestimate.inputs.group_contrast = True
    pipeline.connect(l2estimate, "spm_mat_file", l2conestimate, "spm_mat_file")
    pipeline.connect(l2estimate, "beta_images", l2conestimate, "beta_images")
    pipeline.connect(l2estimate, "residual_image", l2conestimate, "residual_image")
    
    threshold = pe.Node(interface=spm.Threshold(), name="threshold")
    threshold.inputs.contrast_index = 1
    threshold.inputs.use_fwe_correction = False
    threshold.inputs.height_threshold = 0.001
    pipeline.connect(l2conestimate, 'spm_mat_file', threshold, 'spm_mat_file')
    pipeline.connect(l2conestimate, 'spmT_images', threshold, 'stat_image')
    
    return pipeline

righties = list(set(subjects) - set(lefties))

subject_sets = {"all": subjects, "righties": righties, "lefties": lefties}

for task_name in tasks:
    pipeline = create_group_analysis(task_name)
    pipeline.run()


