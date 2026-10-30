import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = "D:/Downloads/Documents/Satellite/ch3_work/ch3_docx.txt"
lines = open(p, encoding='utf-8').read().split('\n')
for n in range(896, 930):
    print(f"--- line {n} ---")
    print(lines[n-1])
    print()
