#!/usr/bin/env python3
import sys

n=int(sys.argv[1])

print("letting n = %d"%n)

print("letting values = [")

counter=1
sep=""
for i in range(1, n+1):
    for j in range(i+1, n+1):
        print("%s[%d,%d,%d]"%(sep,i,j,counter))
        counter+=1
        sep=","
        
print("]")

