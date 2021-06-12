'''
Script to make fsl template for fmri analysis. By default does not run the created script, but generates temp dir with
all funcitonal and anatomical data

Bet brain extraction included

python process_fmri.py
    -i bids_dir
    -o output_dir
    --run


'''

import glob
import shutil
import argparse
import subprocess
import os

from ieeg_fmri_validation.utils import sort_nicely
from ieeg_fmri_validation.fmri.classes import FSL_template


def make_fsf_script(bids_dir, output_dir, run=False):

    if not os.path.isdir(output_dir): os.makedirs(output_dir)

    # load functional and anatomical images
    func_inputs = []
    struct_inputs = []
    for file in glob.glob(os.path.join(bids_dir, '**/ses-mri3t/func/*.nii.gz')):
        destination = os.path.join(output_dir, os.path.split(file)[-1])
        shutil.copyfile(file, destination)
        func_inputs.append(destination)

        file_anat = glob.glob(os.path.join(file.split('func')[0], 'anat', '*.nii.gz'))[0]
        destination_anat = os.path.join(output_dir, os.path.split(file_anat)[-1])
        shutil.copyfile(file_anat, destination_anat)
        struct_inputs.append(destination_anat)

    sort_nicely(func_inputs)
    print('Functional files: ' + str(len(func_inputs)))

    sort_nicely(struct_inputs)
    print('Structural files: ' + str(len(struct_inputs)))

    assert len(func_inputs) == len(struct_inputs), 'Functional and structural data do not match'

    func_inputs = [s.strip('.nii.gz') for s in func_inputs]
    struct_inputs = [s.strip('.nii.gz') for s in struct_inputs]
    struct_inputs = [s.replace('T1w', 'T1w_brain') for s in struct_inputs]

    # update fsl template
    inputs_4d = func_inputs
    structural_images =struct_inputs
    filename_1st = os.path.join(output_dir, 'fsl_first_level.fsf')
    filename_2nd = os.path.join(output_dir, 'fsl_second_level.fsf')

    # copy bet bash
    shutil.copyfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bet_fsl_per_dir.sh'),
                    os.path.join(output_dir, 'bet_fsl_per_dir.sh'))

    # update fsf templates
    print('Updating template_first_level.fsf')
    fsf = FSL_template(analysis='first_level')
    fsf.set_4D_data(inputs_4d)
    fsf.set_structural_images(structural_images)
    fsf.write(filename_1st)
    print('FSL script writen to ' + filename_1st)

    print('Updating template_second_level.fsf')
    fsf = FSL_template(analysis='second_level')
    fsf.set_output_directory(output_dir)
    fsf.set_4D_data(inputs_4d)
    fsf.set_EV_values()
    fsf.set_group_membership()
    fsf.write(filename_2nd)
    print('FSL script writen to ' + filename_2nd)

    if run:
        rc = subprocess.check_call(['bash', os.path.join(output_dir, 'bet_fsl_per_dir.sh'), '-p', output_dir])
        print(rc)
        rc = subprocess.check_call('feat ' + filename_1st, shell=True)
        print(rc)
        rc = subprocess.check_call('feat ' + filename_2nd, shell=True)
        print(rc)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bids_dir', '-i', type=str)
    parser.add_argument('--output_dir', '-o', type=str)
    parser.add_argument('--run', dest='run', action='store_true')
    parser.add_argument('--no-run', dest='run', action='store_false')
    parser.set_defaults(run=False)
    args = parser.parse_args()

    make_fsf_script(args.bids_directory, args.output_directory, args.run)
