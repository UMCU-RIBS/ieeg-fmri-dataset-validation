import numpy as np
import statsmodels.api as sm
import pandas as pd

from ieeg_fmri_validation.utils import zscore
from scipy.stats import pearsonr


def run_OLS_block_design(x, Y, maxlag=0, alpha=1e-2):
    Y = zscore(Y)
    sm_f, sm_fp, sm_ts, sm_tps, sm_w = [], [], [], [], []
    for e in range(Y.shape[-1]):
        sm_f.append([])
        sm_fp.append([])
        sm_ts.append([])
        sm_tps.append([])
        sm_w.append([])
        for i in range(maxlag):
            x_ = np.roll(x, i)
            est = sm.OLS(Y[:, e], sm.add_constant(x_))
            est2 = est.fit()
            sm_f[-1].append(est2.fvalue)
            sm_fp[-1].append(est2.f_pvalue)
            sm_ts[-1].append(est2.tvalues)
            sm_tps[-1].append(est2.pvalues)
            sm_w[-1].append(est2.params)
    sm_f, sm_fp, sm_ts, sm_tps, sm_w = np.array(sm_f), np.array(sm_fp), np.array(sm_ts), np.array(sm_tps), np.array(
        sm_w)

    sm_ts = sm_ts[:, :, -1]  # 0 is intercept
    sm_tps = sm_tps[:, :, -1]

    ts = np.max(sm_ts, 1)
    lags = np.argmax(sm_ts, 1)
    ps = np.array([sm_tps[counter, i] for counter, i in enumerate(lags)])

    inds1 = np.where(ps < alpha / Y.shape[-1] / maxlag)[0]
    inds2 = np.where(ts > 0)[0]
    inds = np.intersect1d(inds1, inds2)
    inds_b = np.zeros(Y.shape[-1], dtype=bool) # indices of significant positive t
    inds_b[inds] = True
    return ts, lags, inds_b, ps


def calculate_r_squared(a, b):
    if b.shape[1] == 1:
        b = np.repeat(b, a.shape[1], axis=1)
    elif a.shape[1] == 1:
        a = np.repeat(a, b.shape[1], axis=1)
    r = np.zeros((a.shape[-1]))
    p = np.zeros_like(r)
    for i, (ia, ib) in enumerate(zip(a.T, b.T)):
        r[i], p[i] = pearsonr(ia, ib)
    return np.sign(r)*(r** 2), p


def run_rest_speech_r_squared(film, rest):
    def run_per_band(key):
        film_band = film.bands[key][:film.expected_duration * 25]
        film_band = film_band.reshape((-1, 750, 1, film_band.shape[-1])) # 25 & 30
        film_band = pd.DataFrame(film_band[1::2].squeeze().reshape((-1, film_band.shape[-1])).T)

        rest_band = pd.DataFrame(rest.bands[key][:rest.expected_duration * 25].T)

        film_band.index = film.raw.ch_names
        rest_band.index = rest.raw.ch_names
        common = film_band.index.intersection(rest_band.index)
        c_ = film_band.loc[common].values
        r_ = rest_band.loc[common].values

        # normalize together
        temp = np.hstack([c_, r_])
        mean_common = np.mean(temp, 1, keepdims=True)
        std_common = np.std(temp, 1, keepdims=True)
        c_z = (c_ - mean_common) / std_common
        r_z = (r_ - mean_common) / std_common
        c_zm = np.mean(c_z.reshape((c_z.shape[0], -1, 750)), -1)  # means per block
        r_zm = np.mean(r_z.reshape((r_z.shape[0], -1, 750)), -1)  # means per block
        r, p = calculate_r_squared(np.vstack([r_zm.T, c_zm.T]), design[:, None])
        return r, p, c_zm, r_zm

    n_bands = len(film.band_block_means.keys())
    film_band = pd.DataFrame(film.band_block_means['gamma'].T)
    film_band.index = film.raw.ch_names
    rest_band = pd.DataFrame(rest.band_block_means['gamma'].T)
    rest_band.index = rest.raw.ch_names
    common = film_band.index.intersection(rest_band.index)

    design = np.array([0] * 1 * 6 + [1] * 1 * 6)
    r2s, ps, cs, rs = zip(*[run_per_band(key) for key in film.band_block_means.keys()])
    r2s = np.hstack(r2s)
    ps = np.hstack(ps)
    r2_output = pd.DataFrame({'analysis': 'speech-' + rest.type_rest,
                              'subject': film.subject,
                              'name': list(common.values) * n_bands,
                              'r2': r2s,
                              'pvalue': ps,
                              'band': [item for sublist in [[key] * len(common) for key in film.band_block_means.keys()]
                                       for item in sublist]})
    print('R2 speech-rest done')
    return r2_output
