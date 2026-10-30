import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = "D:/Downloads/Documents/Satellite/ch3_work/ch3_docx.txt"
lines = open(p, encoding='utf-8').read().split('\n')
for n in [806, 807, 808, 809, 815, 816, 817, 818, 819, 821, 822, 824, 826, 827, 829, 830, 831]:
    print(f"--- line {n} ---")
    print(lines[n-1])
    print()
