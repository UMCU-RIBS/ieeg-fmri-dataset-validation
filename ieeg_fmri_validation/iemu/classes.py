import mne
import pandas as pd
import numpy as np
import os
import json
import mne_bids
import warnings

from collections import OrderedDict
from ieeg_fmri_validation.utils import resample, smooth_signal, zscore
from ieeg_fmri_validation.iemu.routines import run_OLS_block_design, calculate_r_squared


class SubjectDataset(object):
    def __init__(self, input_root, subject, preload=True, **kwargs):
        self.root = input_root
        self.subject = subject
        self.datatype = 'ieeg'
        self.acquisition = None
        self.__dict__.update(kwargs)

        if preload:
            self._set_paths()
            self._load_data()
            self._get_bad_electrodes()


    def _set_paths(self):
        bids_path = mne_bids.BIDSPath(subject=self.subject,
                                      task=self.task,
                                      suffix='ieeg',
                                      extension='vhdr',
                                      datatype=self.datatype,
                                      acquisition=self.acquisition,
                                      root=self.root)

        print(self.task)
        assert len(bids_path.match()) == 1, 'None or more than one run for task is found'

        self.raw_path = str(bids_path.match()[0])
        self.run = mne_bids.get_entities_from_fname(bids_path.match()[0])['run']
        self.session = mne_bids.get_entities_from_fname(bids_path.match()[0])['session']

        bids_path = mne_bids.BIDSPath(subject=self.subject,
                                      task=self.task,
                                      session=self.session,
                                      suffix='channels', run=self.run,
                                      extension='tsv',
                                      datatype=self.datatype,
                                      acquisition=self.acquisition,
                                      root=self.root)
        self.channels_path=str(bids_path)

        bids_path = mne_bids.BIDSPath(subject=self.subject,
                                      session=self.session, suffix='electrodes',
                                      extension='tsv',
                                      datatype=self.datatype,
                                      acquisition=self.acquisition,
                                      root=self.root)
        self.electrodes_path = str(bids_path)

        bids_path = mne_bids.BIDSPath(subject=self.subject,
                                      suffix='T1w',
                                      extension='.nii.gz',
                                      root=self.root)
        self.anat_path = str(bids_path.match()[0])
        self.anat_session = mne_bids.get_entities_from_fname(bids_path.match()[0])['session']
        print('Picking up BIDS files done')


    def _load_data(self):
        self.raw = mne.io.read_raw_brainvision(self.raw_path,
                                               eog=(['EOG']),
                                               misc=(['OTHER', 'ECG', 'EMG']),
                                               scale=1.0,
                                               preload=False,
                                               verbose=True)
        self.channels = pd.read_csv(self.channels_path, sep='\t', header=0, index_col=None)
        self.electrodes = pd.read_csv(self.electrodes_path, sep='\t', header=0, index_col=None)
        self.raw.set_channel_types({ch_name: str(x).lower()
                                if str(x).lower() in ['ecog', 'seeg', 'eeg'] else 'misc'
                                    for ch_name, x in zip(self.raw.ch_names, self.channels['type'].values)})
        self.other_channels = self.channels['name'][~self.channels['type'].isin(['ECOG', 'SEEG'])].tolist()
        self.raw.drop_channels(self.other_channels)
        print('Loading BIDS data done')


    def _get_bad_electrodes(self):
        self.bad_electrodes = self.channels['name'][
            (self.channels['type'].isin(['ECOG', 'SEEG'])) & (self.channels['status'] == 'bad')].tolist()
        self.all_electrodes = self.channels['name'][(self.channels['type'].isin(['ECOG', 'SEEG']))].tolist()
        print('Getting bad electrodes done')


    def preprocess(self):
        self._discard_bad_electrodes()
        self._notch_filter()
        self._common_average_reference()


    def _discard_bad_electrodes(self):
        if self.raw is not None:
            [self.bad_electrodes.remove(i) for i in self.bad_electrodes if i not in self.raw.ch_names]
            self.raw.info['bads'].extend([ch for ch in self.bad_electrodes])
            print('Bad channels indicated: ' + str(self.bad_electrodes))
            print('Dropped ' + str(self.raw.info['bads']) + 'channels')
            self.raw.drop_channels(self.raw.info['bads'])
            self.raw.load_data()
            print('Remaining channels ' + str(self.raw.ch_names))


    def _notch_filter(self):
        if self.raw is not None:
            if np.any(np.isnan(self.raw._data)):
                # self.raw._data[np.isnan(self.raw._data)]=0 # bad hack for nan values
                warnings.warn('There are NaNs in the data, replacing with 0')
            self.raw.notch_filter(freqs=np.arange(50, 251, 50))
            print('Notch filter done')


    def _common_average_reference(self):
        if self.raw is not None:
            self.raw_car, _ = mne.set_eeg_reference(self.raw.copy(), 'average')
            print('CAR done')


    def extract_events(self, plot=False):
        self._read_events()
        if plot:
            self._plot_events()


    def _read_events(self):
        if self.raw is not None:
            if self.task == 'film':
                custom_mapping = {'Stimulus/music': 2,
                                  'Stimulus/speech': 1,
                                  'Stimulus/end task': 5}
            elif self.task == 'rest':
                custom_mapping = {'Stimulus/start task': 1,
                                  'Stimulus/end task': 2}
            else:
                raise NotImplementedError
            self.events, self.event_id = mne.events_from_annotations(self.raw, event_id=custom_mapping,
                                                                     use_rounding=False)
            print('Reading events done')


    def _plot_events(self):
        if self.raw_car is not None:
            self.raw_car.plot(events=self.events,
                              start=0,
                              duration=180,
                              color='gray',
                              event_color={2: 'g', 1: 'r'},
                              bgcolor='w')


    def extract_bands(self, smooth=False):
        if self.raw_car is not None:
            self._compute_band_envelopes()
            self._crop_band_envelopes()
            self._resample_band_envelopes()
            if smooth: self._smooth_band_envelopes()
            self._compute_block_means_per_band()


    def _compute_band_envelopes(self):
        if self.raw_car is not None:
            bands = {'delta': [1, 4], 'theta': [5, 8], 'alpha': [8, 12], 'beta': [13, 24], 'gamma': [60, 120]}
            self.bands = OrderedDict.fromkeys(bands.keys())
            for key in self.bands.keys():
                self.bands[key] = self.raw_car.copy().filter(bands[key][0], bands[key][1]).apply_hilbert(
                    envelope=True).get_data().T
            print('Extracting band envelopes done')


    def _crop_band_envelopes(self):
        if self.bands is not None:
            for key in self.bands.keys():
                self.bands[key] = self.bands[key][self.events[0, 0]:self.events[-1, 0]]


    def _resample_band_envelopes(self):
        if self.bands is not None:
            for key in self.bands.keys():
                self.bands[key] = resample(self.bands[key], 25, int(self.raw.info['sfreq']))


    def _smooth_band_envelopes(self):
        if self.bands is not None:
            for key in self.bands.keys():
                self.bands[key] = np.apply_along_axis(smooth_signal, 0, self.bands[key], 5)


    def _compute_block_means_per_band(self):
        if self.bands is not None:
            self.band_block_means = OrderedDict.fromkeys(self.bands.keys())
            for key in self.bands.keys():
                band = zscore(self.bands[key][:self.expected_duration * 25])
                band = band.reshape((-1, 750, band.shape[-1]))  # 13 blocks in chill or 6 in rest
                self.band_block_means[key] = np.mean(band, 1)


class FilmDataset(SubjectDataset):
    def __init__(self, input_root, subject, preload=True, **kwargs):
        self.task = 'film'
        self.expected_duration = 390
        super().__init__(input_root, subject, preload, **kwargs)


    def run_task_gamma_ols(self, maxlag=25, alpha=5e-2):
        if self.bands is not None:
            design = np.hstack([np.zeros(30 * 25), np.ones(30 * 25)] * 7)[:-30 * 25]
            ts, lags, inds, ps = run_OLS_block_design(design, self.bands['gamma'][:9750], maxlag, alpha)
            print('OLS done')
            ols_output = pd.DataFrame({'subject': self.subject,
                                       'name': self.raw.ch_names,
                                       'tvalue': ts,
                                       'lags': lags,
                                       'pvalue': ps})
            print('OLS speech-music done')
            return ols_output


    def run_task_r_squared(self):
        if self.bands is not None:
            n_bands = len(self.bands.keys())
            design = np.array([0, 1] * 7)[:-1]
            r2s, ps = zip(*[calculate_r_squared(value, design[:, None]) for value in self.band_block_means.values()])
            r2s = np.hstack(r2s)
            ps = np.hstack(ps)
            r2_output = pd.DataFrame({'analysis': 'speech-music',
              'subject': self.subject,
              'name': self.raw.ch_names * n_bands,
              'r2': r2s,
              'pvalue': ps,
              'band': [item for sublist in [[key] * len(self.raw.ch_names) for key in self.bands.keys()]
                                                                                                for item in sublist]})
            print('R2 speech-music done')
            return r2_output


class RestDataset(SubjectDataset):
    def __init__(self, input_root, subject, preload=True, **kwargs):
        self.task = 'rest'
        self.expected_duration = 180
        super().__init__(input_root, subject, preload, **kwargs)

        if preload:
            self.set_rest_type()

    def set_rest_type(self):
        bids_path = mne_bids.BIDSPath(subject=self.subject,
                                      extension='json',
                                      session=self.session,
                                      run=self.run,
                                      task=self.task,
                                      datatype=self.datatype,
                                      acquisition=self.acquisition,
                                      root=self.root)
        with open(str(bids_path).split('.')[0] + '.json') as json_file:
            metadata = json.load(json_file)
        self.type_rest = metadata['TaskDescription']


