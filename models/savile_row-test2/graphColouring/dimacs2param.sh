#!/bin/bash

nodes=`grep '^p' $1 | awk '{print $3}'`
edges=`grep '^p' $1 | awk '{print $4}'`
echo letting vertices = $nodes
echo letting edge_count = $edges
echo letting colours = 10
echo letting edges = [
grep '^e' $1 | awk '{print "[",$2,",",$3,"],"}'
echo ]