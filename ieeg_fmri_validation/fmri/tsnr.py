

import nibabel
import numpy as np
import glob
import os
import argparse

from ieeg_fmri_validation.fmri.routines import make_grey_matter_mask, warp_native2_mni, nii2mgh
from ieeg_fmri_validation.utils import sort_nicely
from subprocess import check_call


def math_tsnr(data):
    m = np.mean(data, 1)
    s = np.std(data, 1)
    s[s == 0] += 1e-5
    tsnr = m/s
    return tsnr


def tsnr2img(y, z):
    y = y.reshape(z.get_fdata().shape)
    tsnr_img = nibabel.Nifti1Image(y, z.affine, z.header)
    return tsnr_img


def calculate_tsnr(output_dir, save_nii=True, use_grey_mask=False):

    subjects = []
    for f in glob.glob(output_dir + 'sub-*.feat/'):
        subjects.append(f.split('sub-')[1].split('_')[0])

    sort_nicely(subjects)
    print('Found ' + str(len(subjects)) + ' subjects')
    grey_mask_tag = '_grey_mask' if use_grey_mask else ''

    #
    tsnrs, tsnrs_mnis = [], []
    for subject in subjects:
        print(subject)
        func_file = os.path.join(output_dir, 'sub-' + subject +
                                 '_ses-mri3t_task-film_run-1_bold.feat', 'filtered_func_data.nii.gz')
        mean_file = os.path.join(output_dir, 'sub-' + subject +
                                 '_ses-mri3t_task-film_run-1_bold.feat', 'mean_func.nii.gz')
        print(func_file)
        x = nibabel.load(func_file)
        z = nibabel.load(mean_file)

        data0 = x.get_fdata()
        data0 = data0.reshape(-1, data0.shape[-1])
        if use_grey_mask:
            assert len(glob.glob(output_dir + '/sub-' + subject + '*_brain_pve_1.nii.gz')) == 1, \
                                                                                        'More than one or no pve1 file'
            pve1 = glob.glob(output_dir + '/sub-' + subject + '*_brain_pve_1.nii.gz')[0]
            grey_mask = make_grey_matter_mask(os.path.join(output_dir, 'sub-' + subject +
                                                           '_ses-mri3t_task-film_run-1_bold.feat'), pve1)
            a = nibabel.load(grey_mask)
            af = a.get_fdata().flatten()
            data = data0[af == 1]
            indices = af == 1
        else:
            data = data0[np.all(data0, axis=1)]
            indices = np.all(data0, axis=1)

        tsnr = math_tsnr(data)

        y = np.zeros((data0.shape[0],))
        y[indices] = tsnr
        tsnr_img = tsnr2img(y, z)
        if save_nii:
            tsnr_nii_file = os.path.join(output_dir + 'sub-' + subject +
                                         '_ses-mri3t_task-film_run-1_bold.feat', 'tsnr' + grey_mask_tag + '.nii')
            nibabel.save(tsnr_img, tsnr_nii_file)
            check_call(['gzip', '-f', tsnr_nii_file])
            tsnrs.append(tsnr)
            tsnr_nii_file += '.gz'

            tsnr_mni = warp_native2_mni(tsnr_nii_file)
            temp_mni = nibabel.load(tsnr_mni)
            tsnrs_mnis.append(temp_mni.get_fdata().flatten())
            mni_size = temp_mni.dataobj.shape
            print(mni_size)

    if save_nii:
        tsnrs_mnis_med = np.median(np.array(tsnrs_mnis), 0)
        tsnr_img_mni = tsnr2img(tsnrs_mnis_med, temp_mni)
        nibabel.save(tsnr_img_mni,
                     os.path.join(output_dir, 'tsnr_median_mni' + grey_mask_tag + '.nii'))
        nii2mgh(os.path.join(output_dir, 'tsnr_median_mni' + grey_mask_tag + '.nii'))



##
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_directory', '-o', type=str)
    parser.add_argument('--save_nii', dest='save_nii', action='store_true')
    parser.add_argument('--no-save_nii', dest='save_nii', action='store_false')
    parser.add_argument('--use_grey_mask', dest='use_grey_mask', action='store_true')
    parser.add_argument('--no-use_grey_mask', dest='use_grey_mask', action='store_false')
    parser.set_defaults(save_nii=True)
    parser.set_defaults(use_grey_mask=False)
    args = parser.parse_args()
    print(os.getcwd())

    calculate_tsnr(args.output_directory, args.save_nii, args.use_grey_mask)
