import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm
import nipype.interfaces.fsl as fsl
from helper_functions import (create_pipeline_functional_run)

from StringIO import StringIO
from nipype.interfaces.io import DataSink, SQLiteSink
from variables import *
from nipype.interfaces.fsl.utils import Merge
from nipype.interfaces.utility import Function
import neuroutils


def create_group_analysis(task_name):
    
    def getContrasts(task_name):
        from variables import design_parameters
        return range(1, len(design_parameters[task_name]['contrasts'])+1)
    
    from variables import subjects, exclude_subjects
    
    if task_name in exclude_subjects.keys():
        subjects = list(set(subjects) - set(exclude_subjects[task_name]))
    
    pipeline = pe.Workflow(name="group_analysis_"+task_name)
    pipeline.base_dir = working_dir

    contrasts_infosource = pe.Node(interface=util.IdentityInterface(fields=['contrast_no']),
                               name="contrasts_infosource")
    contrasts_infosource.iterables = ('contrast_no', getContrasts(task_name))
    
    sessions_infosource = pe.Node(interface=util.IdentityInterface(fields=['session']),
                                  name="sessions_infosource")
    sessions_infosource.iterables = ('session', sessions)
    
    datasource = pe.Node(interface=nio.DataGrabber(infields=['task_name', 'contrast_no'],
                                                   outfields=['con_images_first', 
                                                              'con_images_second', 
                                                              'spm_t_images_first',
                                                              'spm_t_images_second',
                                                              'mask_images']),
                         name = 'datasource', overwrite=True)
    
    datasource.inputs.base_directory = "/home/filo/workspace/2010reliability/results/volumes/"
    datasource.inputs.template = '%simages/_subject_id_%s/_session_%s/_task_name_%s/%s%04d.img'
    datasource.inputs.field_template = dict(mask_images='mask_image/_subject_id_%s/_session_*/_task_name_%s/%s.img')
    datasource.inputs.template_args = dict(con_images_first = [['con_', subjects, 'first', 'task_name', 'con_', 'contrast_no']],
                                           con_images_second = [['con_', subjects, 'second', 'task_name', 'con_', 'contrast_no']],
                                           spm_t_images_first = [['spmT_', subjects, 'first', 'task_name', 'spmT_','contrast_no']],
                                           spm_t_images_second = [['spmT_', subjects, 'second', 'task_name', 'spmT_','contrast_no']],
                                           mask_images = [[subjects, 'task_name', 'mask']])
    datasource.inputs.sort_filelist = True
    
    pipeline.connect(contrasts_infosource, "contrast_no", datasource, "contrast_no")
    #datasource.inputs.session = "first"
    datasource.inputs.task_name = task_name
    
    thr_method_infosource = pe.Node(interface=util.IdentityInterface(fields=['thr_method']),
                              name="thr_method_infosource")
    thr_method_infosource.iterables = ('thr_method', thr_methods)
    
    overlap_datasource = pe.Node(interface=nio.DataGrabber(infields=['task_name', 'contrast_no'],
                                                   outfields=['overlap_map']),
                         name = 'overlap_datasource', overwrite=True)
    overlap_datasource.inputs.base_directory = '/media/data/2010reliability/workdir_fmri/within_subjects_pipeline_noroi/'
    overlap_datasource.inputs.template = '_task_name_%s/_masked_comparison_False/_subject_id_%s/_thr_method_%s/just_the_overlap/mapflow/_just_the_overlap%d/diff_thresh.nii'
    overlap_datasource.inputs.template_args = dict(overlap_map = [['task_name', subjects, 'thr_method', 'contrast_no']])
    overlap_datasource.inputs.sort_filelist = True
    
    
    def minusOne(number):
        return number -1
    
    pipeline.connect(contrasts_infosource, ("contrast_no", minusOne), overlap_datasource, "contrast_no")
    pipeline.connect(thr_method_infosource, 'thr_method', overlap_datasource, "thr_method")
    #datasource.inputs.session = "first"
    overlap_datasource.inputs.task_name = task_name
    
    def stack_overlaps_func(file_list):
        import nibabel as nb
        import numpy as np
        
        data_list = []
        sum_max = 0
        
        for file in file_list:
            nii = nb.load(file)
            data = nii.get_data()
            data_list.append(data)
            sum_max += data.max()
        
        newdata = np.array(data_list).sum(axis=0)/sum_max
        
        new_nii = nb.Nifti1Image(newdata, nii.get_affine(), nii.get_header())
        new_file = "stack.nii"
        nb.save(new_nii, new_file)
        return new_file
    
    stack_overlaps = pe.Node(interface=Function(function=stack_overlaps_func, 
                                                input_names=['file_list'], 
                                                output_names=['stack']), name="stack_overlaps")
    pipeline.connect(overlap_datasource, "overlap_map", stack_overlaps, "file_list")
    
    average = pe.MapNode(interface=fsl.maths.MultiImageMaths(op_string="-add %s -div 2"), name="average",
                         iterfield=['in_file', 'operand_files'])
    pipeline.connect([(datasource, average, [('con_images_first', 'in_file'),
                                             ('con_images_second', 'operand_files')])
                      ])
    
    def pickCons(averages, firsts, seconds):
        from variables import exceptions
        new_list = []
        for i,f in enumerate(firsts):
            for exception in exceptions:
                if f.find('task_name_'+exception["task_name"]) != -1 and f.find("subject_id_"+exception["subject_id"]) != -1:
                    if exception["which"] == "first":
                        new_list.append(f)
                    else:
                        new_list.append(seconds[i])
                    break
            if len(new_list) == i:
                new_list.append(averages[i])
        assert len(averages) == len(new_list)
        return new_list
                
        
    
    pick_cons = pe.Node(interface=util.Function(function=pickCons,
                                           input_names=['averages', 'firsts', 'seconds'], 
                                           output_names='out_list'),
                   name='pick_cons')
    pipeline.connect([(average, pick_cons, [('out_file', 'averages')]),
                      (datasource, pick_cons, [('con_images_first', 'firsts'),
                                             ('con_images_second', 'seconds')])
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
    
    
    def mask_union(list_of_masks):
        import numpy as np
        import nibabel as nb
        import os
        n_list_of_masks = []
        for pair in list_of_masks:
            for mask in pair:
                n_list_of_masks.append(mask)
        
        list_of_masks = n_list_of_masks
        nii = nb.load(list_of_masks[0])
        final_mask = np.ones(nii.get_shape())
        for mask in list_of_masks:
            print mask
            data = nb.load(mask).get_data()
            final_mask = np.logical_and(final_mask, np.logical_not(np.logical_or(data == 0, np.isnan(data))))
        out_file = os.path.abspath("union_mask.nii")
        
        nb.save(nb.Nifti1Image(final_mask, nii.get_affine(), nii.get_header()), out_file)
        return out_file
    
    union_mask = pe.Node(Function(function=mask_union, 
                                  input_names=['list_of_masks'], 
                                  output_names=['union_mask']), 
                         name='union_mask')
    pipeline.connect([(datasource, union_mask, [('mask_images', 'list_of_masks')]),
                      
                      ])
    
    design = pe.Node(interface=spm.OneSampleTTestDesign(), name="design")
    pipeline.connect([(pick_cons, design, [('out_list', 'in_files')]),
                      (union_mask, design, [('union_mask', 'explicit_mask_file')])
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
    
    icc = pe.Node(interface=neuroutils.ICC(), name="icc")
    pipeline.connect(l2estimate, "mask_image", icc, "mask")
    pipeline.connect(datasource, "spm_t_images_first", icc, "first_session_t_maps")
    pipeline.connect(datasource, "spm_t_images_second", icc, "second_session_t_maps")
    
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
    pipeline.run(plugin_args={'n_procs': 4})


