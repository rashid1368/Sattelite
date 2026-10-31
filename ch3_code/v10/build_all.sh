#!/bin/bash
# Rebuild the v10 draft from v9 in the fixed order (the later patches are not idempotent).
set -e
cd "$(dirname "$0")/../.."
python3 ch3_code/v10/patch_ch4.py
python3 ch3_code/v10/patch_ch5.py > /dev/null
python3 ch3_code/v10/patch_extra.py
python3 ch3_code/v10/patch_front.py
python3 ch3_code/v10/patch_extra2.py
python3 ch3_code/v10/patch_extra3.py
python3 ch3_code/v10/patch_extra4.py
python3 ch3_code/v10/patch_extra5.py
python3 ch3_code/v10/patch_extra6.py
python3 ch3_code/v10/patch_extra7.py
python3 ch3_code/v10/patch_extra8.py
python3 ch3_code/v10/patch_extra9.py
python3 ch3_code/v10/patch_matlab.py
python3 ch3_code/v10/patch_end.py
echo "draft rebuilt: _build/thesis_v10_draft.docx"
