

import numpy as np
import seaborn as sns

from matplotlib import pyplot as plt
from ieeg_fmri_validation.fmri.process import make_fsf_script
from ieeg_fmri_validation.fmri.motion import find_outliers
from ieeg_fmri_validation.fmri.tsnr import calculate_tsnr


bids_dir='/Fridge/users/julia/project_chill_dataset_paper/data/BIDS2'
output_dir='/Fridge/users/julia/project_chill_dataset_paper/validation/fmri'


make_fsf_script(bids_dir, output_dir, run=True)
fds, outliers = find_outliers(output_dir)
tsnrs = calculate_tsnr(output_dir)


# plot of framewise distplacement over all subjects
plt.figure(figsize=(5, 3))
plt.violinplot(fds, showmedians=True, widths=.85)
plt.hlines(y=4, xmin=0, xmax=len(fds) + 1, linestyles=':')
plt.xlim(0, len(fds) + 1)
plt.xlabel('Subjects')
plt.ylabel('Framewise displacement (mm)')


# percent of outliers: histogram
print(str(np.sum(np.round(np.array(outliers) / 641 * 100) > 5)) + ' subjects with >5% outliers')
plt.figure(figsize=(3, 3))
ax = sns.histplot(np.round(np.array(outliers) / 641 * 100),
                  kde=True, edgecolor="w", linewidth=1,
                  bins=range(int(np.max(np.round(np.array(outliers) / 641 * 100)) + 2)))
plt.xlabel('Percent outliers')
mids = [rect.get_x() + rect.get_width() / 2 for rect in ax.patches]
plt.xticks(mids, (np.array(mids) - .5).astype(int))
plt.tight_layout()


# temporal snr
print('Average tSNR over subjects: ' + str(np.mean([np.median(i) for i in tsnrs])),
      ', std: ' + str(np.std([np.median(i) for i in tsnrs])))
plt.figure(figsize=(5, 3))
plt.violinplot(tsnrs, showmedians=True, widths=.85)
plt.xlim(0, len(tsnrs) + 1)
plt.xlabel('Subjects')
plt.ylabel('tSNR')