
import os
from subprocess import check_call



def nii2mgh(file):
    rc = check_call(['bash', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bash', 'zstat.nii2mgh.sh'),
                                                                                                            '-z', file])
    print(rc)


def warp_native2_mni(file):
    assert os.path.isfile(file), 'Not found ' + file
    subject_path = os.path.dirname(file)
    rc = check_call(['applywarp',
                '--ref=' + os.path.join(subject_path, 'reg', 'standard.nii.gz'),
                '--in=' + file,
                '--warp=' + os.path.join(subject_path, 'reg', 'highres2standard_warp.nii.gz'),
                '--premat=' + os.path.join(subject_path, 'reg', 'example_func2highres.mat'),
                '--out=' + file.replace('tsnr', 'tsnr_mni')])
    print(rc)
    return file.replace('.', '_mni.')


def make_grey_matter_mask(subject_path, pve1):
    assert os.path.isfile(pve1), 'Not found ' + pve1
    out_file = os.path.join(subject_path, 'reg', os.path.basename(pve1).replace('.nii', '_func_space.nii'))
    rc = check_call(['applywarp',
                '--ref=' + os.path.join(subject_path, 'reg', 'example_func.nii.gz'),
                '--in=' + pve1,
                '--premat=' + os.path.join(subject_path, 'reg', 'highres2example_func.mat'),
                '--out=' + out_file])
    print(rc)
    rc = check_call(['fslmaths',
                     out_file,
                    '-thr', '.2',
                    '-bin', out_file.replace(os.path.basename(out_file), 'grey_mask_func_space.nii.gz')])
    print(rc)
    return out_file.replace(os.path.basename(out_file), 'grey_mask_func_space.nii.gz')
