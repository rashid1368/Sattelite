#!/bin/bash
# Convert the v10 draft with LibreOffice and print the page spans of chapters 3-5 and references.
S=/tmp/claude-0/-home-user-Sattelite/69e7f17c-8abb-5ecb-8a49-16b74261e311/scratchpad/v10
mkdir -p $S && rm -f $S/pg_*.txt && cp /home/user/Sattelite/_build/thesis_v10_draft.docx $S/v10.docx
cd $S && timeout 400 soffice --headless --convert-to pdf v10.docx >/dev/null 2>&1
N=$(pdfinfo v10.pdf | awk '/Pages/{print $2}'); echo "total pages $N"
for p in $(seq 1 $N); do pdftotext -f $p -l $p -layout v10.pdf - 2>/dev/null | tr -d '\f' > pg_$p.txt; done
for p in $(seq 70 $N); do if grep -q -E "فصل (سوم|چهارم|پنجم)|منابع و مأخذ" pg_$p.txt; then echo "page $p: $(grep -m1 -E 'فصل (سوم|چهارم|پنجم)|منابع و مأخذ' pg_$p.txt | tr -s ' ' | cut -c1-40)"; fi; done
