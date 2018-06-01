#!/usr/bin/python

import matplotlib.pyplot as plt
import matplotlib.tri as tri
from matplotlib import cm
import csv, math, numpy, sys, os

# Required input:
WorkDir = os.getcwd()+"/"
verticesFile = WorkDir+'Opinicon/Output/vertices.csv'
facesFile = WorkDir+'Opinicon/Output/faces.csv'

print "<<< Reading vertices >>>"
# read vertices
x=[]; y=[]; z=[]
try:
  with open(verticesFile) as csvDataFile:
    csvReader = csv.reader(csvDataFile)
    for row in csvReader:
      x.append(float(row[0]))
      y.append(float(row[1]))
      z.append(float(row[2]))

except IOError:
  print 'Error: file',file,'not found'
  raise SystemExit
n1=len(x)
print "... Number of vertices:", n1


print "<<< Reading triangles >>>"
# read triangles
triangles=[]
try:
  with open(facesFile) as csvDataFile:
    csvReader = csv.reader(csvDataFile)
    for row in csvReader:
        triangles.append([int(row[0]),int(row[1]),int(row[2])])

except IOError:
  print 'Error: file',file,'not found'
  raise SystemExit
n1=len(triangles)
print "... Number of triangles:", n1

plt.figure()
plt.rcParams['axes.facecolor'] = 'darkolivegreen'
plt.gca().set_aspect('equal')
plt.tricontourf(x, y, triangles, z, 100, cmap=cm.CMRmap)
plt.colorbar()
plt.title('Interpolated eDNA concentration')
plt.xlabel('Easting')
plt.ylabel('Northing')
#plt.xlim(394600,395700)
#plt.ylim(4934400,4935500)
plt.savefig('figure.png', dpi = 600)
plt.show()




