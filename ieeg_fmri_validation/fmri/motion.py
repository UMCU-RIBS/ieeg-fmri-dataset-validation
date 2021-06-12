'''
python motion.py
'''

import subprocess
import glob
import argparse
import os
import numpy as np
import re

from ieeg_fmri_validation.utils import sort_nicely


def calculate_fd(subject_directory, subject_4D):
    result = subprocess.run(['fsl_motion_outliers', '-i', subject_4D,
                             '-o', os.path.join(subject_directory, 'mc', 'fd_outliers'),
                             '-s', os.path.join(subject_directory, 'FD'), '--fd', '-v'], stdout=subprocess.PIPE)
    n = int(re.split(' outliers', re.split('Found ', result.stdout.decode('utf-8'))[1])[0])

    # fsl_motion_outliers does not create output file fd_outliers if there are 0 outliers, create one manually here
    if n == 0:
        np.savetxt(os.path.join(subject_directory, 'mc', 'fd_outliers'), np.zeros((641, 24)), '%1d')

def calculate_dvar(subject_directory, subject_4D):
    rc = subprocess.check_call(['fsl_motion_outliers', '-i', subject_4D,
                     '-o', os.path.join(subject_directory, 'mc', 'dvars_outliers'),
                     '-s', os.path.join(subject_directory, 'DVAR'), '--dvars', '--nomoco'])
    print(rc)

def find_outliers(output_directory, type_outliers='fd'):
    subjects = []
    for f in glob.glob(output_directory + 'sub-*.feat/'):
        subjects.append(f.split('sub-')[1].split('_')[0])

    sort_nicely(subjects)
    print('Found ' + str(len(subjects)) + ' subjects')

    fds, outliers = [], []
    for i, subject in enumerate(subjects):
        print(i, subject)
        assert len(glob.glob(output_directory + '/sub-' + subject + '*_bold.nii.gz')) == 1, 'More than one func 4D file'
        subject_4D = glob.glob(output_directory + '/sub-' + subject + '*_bold.nii.gz')[0]
        assert len(glob.glob(output_directory + '/sub-' + subject + '*.feat')) == 1, 'More than one subject directory'
        subject_directory = glob.glob(output_directory + '/sub-' + subject + '*.feat')[0]
        subprocess.check_call(['cd', subject_directory], shell=True)
        if not os.path.isfile(os.path.join(subject_directory, 'FD')) or \
                not os.path.isfile(os.path.join(subject_directory, 'mc', type_outliers+'_outliers')):
            calculate_fd(subject_directory, subject_4D)
        if type_outliers == 'dvar' and (not os.path.isfile(os.path.join(subject_directory, 'DVAR')) or
                not os.path.isfile(os.path.join(subject_directory, 'mc', type_outliers+'_outliers'))):
            calculate_dvar(subject_directory, subject_4D)
        fd_file = os.path.join(subject_directory, 'FD')
        print(fd_file)
        fds.append(np.loadtxt(fd_file))
        temp = np.loadtxt(os.path.join(subject_directory, 'mc', type_outliers+'_outliers'))
        print('FD outliers: ' + str(np.sum(np.sum(temp, 1) > 0)) + '/' + str(temp.shape[0]))
        print('It is ' + str(np.sum(np.sum(temp, 1) > 0) / temp.shape[0]*100) + '%')
        outliers.append(np.sum(np.sum(temp, 1) > 0))
    return fds, outliers


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_directory', '-o', type=str)
    parser.add_argument('--type_outliers', '-t', type=str, default='fd', choices=['dvar', 'fd'])
    args = parser.parse_args()

    find_outliers(args.output_directory, args.type_outliers)
