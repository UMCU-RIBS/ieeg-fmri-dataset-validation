

import pandas as pd
import seaborn as sns

from ieeg_fmri_validation.iemu.process import process_iemu
from matplotlib import pyplot as plt

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def get_ols_mask(r2):
    ols_subset = ols_music.loc[(ols_music['pvalue'] < 1e-3 / len(ols_music)) & (ols_music['tvalue'] > 0)]
    s = []
    for subject in r2_music['subject'].unique():
        s.append(r2.loc[r2['subject'] == subject, 'name'].isin(ols_subset.loc[ols_subset['subject'] == subject, 'name']))
    return pd.concat(s)

def plot_boxplots(r2df, alpha=5e-2):
    sns.set_context('paper', font_scale=1.2)
    plt.figure(figsize=(3, 3))
    sns.boxplot(x='band', y='r2',
                data= r2df.loc[r2df['pvalue'] < alpha / r2df.shape[0]],
                showfliers=True,
                zorder=-1,
                order=r2df['band'].unique())
    plt.ylim(-1.2, 1.2)
    plt.tight_layout()


##
bids_dir='/Fridge/users/julia/project_chill_dataset_paper/data/BIDS2'

## get preprocessed results
ols_music, r2_music, r2_rest = process_iemu(bids_dir)

## separate tesk rest and natural rest
r2_rest_task = r2_rest.loc[r2_rest['analysis'] == 'speech-rest task']
r2_rest_natural = r2_rest.loc[r2_rest['analysis'] == 'speech-natural rest']

## take electrode mask from ols_music

ols_music_mask = get_ols_mask(r2_music)
ols_rest_task_mask = get_ols_mask(r2_rest_task)
ols_rest_natural_mask = get_ols_mask(r2_rest_natural)

## plot boxplots for r2 values per analysis
plot_boxplots(r2_music[ols_music_mask])
plot_boxplots(r2_rest_task[ols_rest_task_mask])
plot_boxplots(r2_rest_natural[ols_rest_natural_mask])




