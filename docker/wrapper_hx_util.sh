#!/bin/bash -e

SCRIPT_FULLPATH=${VENV_PATH}/bin/hx_util
SCRIPT_DIR=$(dirname ${SCRIPT_FULLPATH})
SCRIPT_FILENAME=$(basename ${SCRIPT_FULLPATH})

# hack to get subproc's pkg version
if [ ${1} == 'version_only' ]
then
    SCRIPT_VERSION=$(${VENV_PATH}/bin/pip show hx_util | grep 'Version' | cut -d ' ' -f 2)
    if [[ -z "${SCRIPT_VERSION// }" ]]; then
        exit 1
    else
        echo $SCRIPT_VERSION
        exit 0
    fi
fi

input_file=${1}
input_dir=$(dirname ${1})
input_id=$(basename ${input_dir})  # assumes input file has a unique parent dir

echo "***** untar/ungzip input file ${input_file}"
# untar uploaded file
tar xf ${input_file} -C ${input_dir}

echo
echo "***** remove macos specific files from ${input_dir}/course"
find ${input_dir}/course -name "._*" -print -exec rm {} \;

echo
echo "***** about to process input file ${input_file}"

# run hx_util script
#cd ${SCRIPT_DIR}
#${VENV_PATH}/bin/python ${SCRIPT_FILENAME} ${input_dir}/course
${SCRIPT_FULLPATH} ${input_dir}/course

echo "***** done processing"
echo

result_dir=${input_dir}/result_${input_id}
mkdir -p ${result_dir}

echo "***** copying output files to ${result_dir}"
echo

# move result to known location
cp ${input_dir}/course/*.tsv ${result_dir}
cp ${input_dir}/*.zip ${result_dir}

echo "***** generating tar.gz"
echo

cd ${input_dir}
output=result.tar.gz
tar cvzf ${input_dir}/${output} result_${input_id}

echo "***** all done"

