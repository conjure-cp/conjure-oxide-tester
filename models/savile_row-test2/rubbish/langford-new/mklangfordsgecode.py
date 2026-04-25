#!/usr/bin/env python3

import sys

n=int(sys.argv[1])
k=int(sys.argv[2])

# copies minmap model.



print("predicate all_different_int(array [int] of var int: xs);")

for i in range(n):
    print("var 1..%d: position_%d :: output_var;"%((k*n)-((i+1)*(k-1)), i))

for i in range(n):
    for j in range(k-1):
        print("var 1..%d: positionaux_%d_%d;"%((k*n), i, j))

print("constraint all_different_int([")

for i in range(n):
    print("position_%d, "%(i))
for i in range(n):
    for j in range(k-1):
        print("positionaux_%d_%d,"%(i, j))
print("]);")

for i in range(n):
    for j in range(k-1):
        print("constraint int_lin_eq([1,1,-1], [position_%d, %d, positionaux_%d_%d], 0);"%(i, (i+1)*(j+1), i,j))

print("solve :: int_search([")
for i in range(n):
    print("position_%d, "%(i))
for i in range(n):
    for j in range(k-1):
        print("positionaux_%d_%d"%(i, j)),
        if i!=n-1 or j!=k-2: print(",")
print("], input_order, indomain_min, complete) satisfy;")

