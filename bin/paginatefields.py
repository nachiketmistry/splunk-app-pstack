#   Version 4.0
import csv
import sys

count = 10
offset = 0
if len(sys.argv) >= 3:
    count = int(sys.argv[1])
    offset = int(sys.argv[2]) - 1

start = offset*count 
start = 1 if start==0 else start
end = start + count

r = csv.reader(sys.stdin)

rows = []

i = 0
for l in r:  
    rows.append(l[:1] + l[start:end])
    i = i + 1

if(i > 1): 
    csv.writer(sys.stdout).writerows(rows)

