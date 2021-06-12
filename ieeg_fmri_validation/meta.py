import pandas as pd
import os
import mne_bids
import argparse

from ieeg_fmri_validation.iemu.classes import FilmDataset, RestDataset

def read_one(bids_dir, subject, acq):

    print(subject)
    film = FilmDataset(bids_dir, subject, acquisition=acq)

    if 'rest' in mne_bids.get_entity_vals(os.path.join(bids_dir, 'sub-' + subject, 'ses-iemu', 'ieeg'), 'task'):
        rest = RestDataset(bids_dir, subject, acquisition=acq)
    else:
        rest = None

    return film, rest

def read_meta(bids_dir):

    subjects = mne_bids.get_entity_vals(bids_dir, 'subject')
    table_subjs = pd.read_csv(os.path.join(bids_dir, 'participants.tsv'), sep='\t')
    meta = {'sr':[], 'anat':[], 'rest':[], 'good': [], 'bad%': [],
            'ecog': [], 'seeg':[], 'hd':[], 'ah':[], 'eog':[], 'ecg':[]}

    for subject in subjects:
        if 'iemu' in mne_bids.get_entity_vals(os.path.join(bids_dir, 'sub-' + subject), 'session'):
            info = table_subjs.loc[table_subjs['participant_id']=='sub-'+subject]
            film, rest = read_one(bids_dir, subject, acq='clinical')

            # bad and good electrodes
            if film.bad_electrodes is not None:
                meta['bad%'].append(len(film.bad_electrodes) / len(film.all_electrodes) * 100)
                meta['good'].append(len(film.all_electrodes) - len(film.bad_electrodes))

            # sampling frequency across channels
            meta['sr'].append(film.channels['sampling_frequency'].unique())

            # anatomical sessions
            meta['anat'].append(film.anat_session)

            # types of rest
            meta['rest'].append(rest.type_rest if rest is not None else None)

            # channels with physiological recordings
            meta['ah'].append(1 if len(film.channels[(film.channels['name'] == 'AH') |
                                                             (film.channels['name'] == 'AH+')])>0 else 0)
            meta['ecg'].append(1 if sum(film.channels['type']=='ECG')>0 else 0)
            meta['eog'].append(1 if sum(film.channels['type']=='EOG')>0 else 0)

            # ECoG, sEEG and HD ECoG electrodes
            if (info['high_density_grid']=='yes').values:

                # subjects with HD in separate recording
                if 'HDgrid' in mne_bids.get_entity_vals(os.path.join(bids_dir, 'sub-' + subject, 'ses-iemu', 'ieeg'),
                                                                                                        'acquisition'):
                    film_hd, rest_hd = read_one(bids_dir, subject, acq='HDgrid')
                    meta['hd'].append(sum(film_hd.channels['type']=='ECOG'))
                    meta['ecog'].append(sum(film.channels['type'] == 'ECOG'))

                # subjects with HD in clinical recording: grid C
                else:
                    meta['hd'].append(sum(film.channels[film.channels["name"].str.contains('C')]['type'] == 'ECOG'))
                    meta['ecog'].append(sum(film.channels[~film.channels["name"].str.contains('C')]['type'] == 'ECOG'))
            else:
                meta['hd'].append(0)
                meta['ecog'].append(sum(film.channels['type']=='ECOG'))
            meta['seeg'].append(sum(film.channels['type']=='SEEG'))

    return pd.DataFrame(meta)

##
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bids_dir', type=str)
    args = parser.parse_args()

    read_meta(args.bids_dir)