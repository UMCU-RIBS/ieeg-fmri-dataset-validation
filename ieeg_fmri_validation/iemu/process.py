'''
mne environment is required, python 3.6
'''

import pandas as pd
import os
import argparse
import mne_bids

from ieeg_fmri_validation.iemu.routines import run_rest_speech_r_squared
from ieeg_fmri_validation.iemu.classes import FilmDataset, RestDataset

def process_one(bids_dir, subject, acq):

    print(subject)

    film = FilmDataset(bids_dir, subject, acquisition=acq)
    film.preprocess()
    film.extract_events()
    film.extract_bands()
    ols_music = film.run_task_gamma_ols()
    r2_music = film.run_task_r_squared()

    if 'rest' in mne_bids.get_entity_vals(os.path.join(bids_dir, 'sub-' + subject, 'ses-iemu', 'ieeg'), 'task'):
        rest = RestDataset(bids_dir, subject, acquisition=acq)
        rest.preprocess()
        rest.extract_events()
        rest.extract_bands()
        r2_rest = run_rest_speech_r_squared(film, rest)
    else:
        rest, r2_rest = None, None

    return ols_music, r2_music, r2_rest

##
def process_iemu(bids_dir):

    subjects = mne_bids.get_entity_vals(bids_dir, 'subject')
    ols_music, r2_music, r2_rest = [], [], []

    for subject in subjects:
        if 'iemu' in mne_bids.get_entity_vals(os.path.join(bids_dir, 'sub-' + subject), 'session'):
            for acq in mne_bids.get_entity_vals(os.path.join(bids_dir, 'sub-' + subject, 'ses-iemu', 'ieeg'),
                                                                                                    'acquisition'):
                if acq != 'render':
                    output = process_one(bids_dir, subject, acq)
                    for x, lst in zip(output, [ols_music, r2_music, r2_rest]):
                        lst.append(x)

    return pd.concat(ols_music, ignore_index=True), \
           pd.concat(r2_music, ignore_index=True), \
           pd.concat(r2_rest, ignore_index=True)


##
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bids_dir', '-i', type=str)
    args = parser.parse_args()

    process_iemu(args.bids_dir)
