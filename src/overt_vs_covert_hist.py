import numpy as np
import nibabel as nb
import pylab as plt
import matplotlib as mpl
from scipy.stats import percentileofscore


overt_fname = '/media/data/2010reliability/workdir_fmri/group_analysis_overt_verb_generation/_contrast_no_1/icc/icc_map.nii'
overt_mask = '/media/data/2010reliability/workdir_fmri/group_analysis_overt_verb_generation/_contrast_no_1/level2estimate/mask.img'
overt_roi = '/media/data/2010reliability/workdir_fmri/within_subjects_pipeline_noroi/_task_name_overt_verb_generation/reslice_roi_mask/rdialted_mask.nii'

covert_fname = '/media/data/2010reliability/workdir_fmri/group_analysis_covert_verb_generation/_contrast_no_1/icc/icc_map.nii'
covert_mask = '/media/data/2010reliability/workdir_fmri/group_analysis_covert_verb_generation/_contrast_no_1/level2estimate/mask.img'
covert_roi = '/media/data/2010reliability/workdir_fmri/within_subjects_pipeline_noroi/_task_name_covert_verb_generation/reslice_roi_mask/rdialted_mask.nii'


overt_mask_data = nb.load(overt_mask).get_data()
overt_mask_data = np.logical_not(np.logical_or(overt_mask_data == 0, np.isnan(overt_mask_data)))
overt_mask_roi = nb.load(overt_roi).get_data()
overt_mask_roi = np.logical_not(np.logical_or(overt_mask_roi == 0, np.isnan(overt_mask_roi)))
overt_mask_data = np.logical_and(overt_mask_data, overt_mask_roi)

overt_data = nb.load(overt_fname).get_data()[overt_mask_data]

covert_mask_data = nb.load(covert_mask).get_data()
covert_mask_data = np.logical_not(np.logical_or(covert_mask_data == 0, np.isnan(covert_mask_data)))
covert_mask_roi = nb.load(covert_roi).get_data()
covert_mask_roi = np.logical_not(np.logical_or(covert_mask_roi == 0, np.isnan(covert_mask_roi)))
covert_mask_data = np.logical_and(covert_mask_data, covert_mask_roi)

covert_data = nb.load(covert_fname).get_data()[covert_mask_data]

ax = plt.subplot(1,1,1)
plt.xlabel("ICC")
plt.ylabel("voxel count")

ax.hist([overt_data, covert_data], 40, histtype='bar', label=['Overt', 'Covert'])
ax.legend(loc=2)
plt.show()

print np.median(overt_data), np.median(covert_data)
print percentileofscore(overt_data, 0), percentileofscore(covert_data, 0)