#!/usr/bin/env python3

import sys

n=int(sys.argv[1])
k=int(sys.argv[2])

# copies minmap model.

print("MINION 3")
print("**VARIABLES**")

for i in range(n):
    print("DISCRETE position_%d {1..%d}"%(i, (k*n)-((i+1)*(k-1))))

print("DISCRETE positionaux[%d,%d] {1..%d}"%(n, k-1, (k*n)))

print("**CONSTRAINTS**")

print("gacalldiff([")
for i in range(n):
    print("position_%d, "%(i))
print(" positionaux])")

for i in range(n):
    for j in range(k-1):
        print("sumleq([position_%d, %d], positionaux[%d,%d])"%(i, (i+1)*(j+1), i,j))
        print("sumgeq([position_%d, %d], positionaux[%d,%d])"%(i, (i+1)*(j+1), i,j))

print("**EOF**")
