#!/bin/bash
# Full build of the v10 final draft: v9 -> chapters -> structure -> footnotes -> page numbers.
set -e
cd "$(dirname "$0")/../.."
bash ch3_code/v10/build_all.sh
python3 ch3_code/v10/patch_final.py
python3 ch3_code/v10/patch_footnotes.py > /dev/null
python3 ch3_code/v10/patch_dedupe.py remove
S=/tmp/claude-0/-home-user-Sattelite/69e7f17c-8abb-5ecb-8a49-16b74261e311/scratchpad/v10
mkdir -p $S && cp _build/thesis_v10_draft.docx $S/pass1.docx && (cd $S && timeout 400 soffice --headless --convert-to pdf pass1.docx >/dev/null 2>&1)
python3 ch3_code/v10/patch_dedupe.py renumber $S/pass1.pdf
python3 ch3_code/v10/patch_pages.py _build/thesis_v10_draft.docx $S/pass1.pdf
echo "final draft: _build/thesis_v10_draft.docx"
