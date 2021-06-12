#!/bin/sh
#make freesurfer maps for group25.gfeat/cope1.feat/stats/zstat1.nii.gz
#input is the full path to the zstat file - output of 2nd level fmri analysis

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -z|--zpath)
    zpath="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

echo "zstat path = ${zpath}"
echo "using standard template MNI_ch2better"
export filename=${zpath##*/}
export dirname=${zpath%/*}

export SUBJECTS_DIR=/home/julia/Documents/other/brain_templates/

mri_vol2surf \
--src ${zpath} \
--srcreg ./MNI_ch2better/mri/rawreg.dat \
--hemi lh \
--o ${dirname}"/lh."${filename/nii.gz/mgh} \
--out_type paint \
--regheader "MNI_ch2better" \
--projfrac 0.5

mri_vol2surf \
--src ${zpath} \
--srcreg ./MNI_ch2better/mri/rawreg.dat \
--hemi rh \
--o ${dirname}"/rh."${filename/nii.gz/mgh} \
--out_type paint \
--regheader "MNI_ch2better" \
--projfrac 0.5
 
