applywarp --ref=standard --in=filtered_func_data.nii.gz --warp=highres2standard_warp --premat=example_func2highres.mat --out=filtered_func_data_standard.nii.gz
applywarp --ref=/Fridge/users/julia/project_chill_dataset_paper/validation/fmri/sub-bemmel_ses-3t1_task-chill_dir-PA_run-1_bold.feat/reg/example_func \
--in=/Fridge/users/julia/project_chill_dataset_paper/validation/fmri/sub-bemmel_ses-3t1_run-1_T1w_brain_pve_1.nii.gz \
--premat=/Fridge/users/julia/project_chill_dataset_paper/validation/fmri/sub-bemmel_ses-3t1_task-chill_dir-PA_run-1_bold.feat/reg/highres2example_func.mat \
--out=/Fridge/users/julia/project_chill_dataset_paper/validation/fmri/sub-bemmel_ses-3t1_task-chill_dir-PA_run-1_bold.feat/reg/sub-bemmel_ses-3t1_run-1_T1w_brain_pve_1_func_space.nii.gz 

