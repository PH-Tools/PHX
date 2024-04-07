#!/usr/bin/env bash
# Used to run the python script in a new terminal window. 
# This is needed for MacOS in order to get around the permissions issues with Rhino and Excel.

exe_path=$1
python_exe_path=$2
python_script_path=$3
hbjson_file_path=$4
activate_variants=$5

PYTHONHOME=""
export PYTHONHOME
echo Using:
echo - Path: ${exe_path}
echo - Python: ${python_exe_path}
echo - Script: ${python_script_path}
echo - HBJSON: ${hbjson_file_path}
echo - Variants: ${activate_variants}
cd "$exe_path"
osascript -e "tell app \"Terminal\"
    do script \"\\\"${python_exe_path}\\\" \\\"${python_script_path}\\\" \\\"${hbjson_file_path}\\\" ${activate_variants}\"
end tell"