#!/bin/sh

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -p|--path)
    anatpath="$2"
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

echo "anat path = ${anatpath}"

cd ${anatpath}
for filename in *T1w.nii.gz ; do
  fname=`$FSLDIR/bin/remove_ext ${filename}`
  echo "Running bet for ${fname}"
  bet ${fname}.nii.gz ${fname}_brain.nii.gz -R -f .2 -g 0
done

echo "Bet done"
