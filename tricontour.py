#!/usr/bin/python

import matplotlib.pyplot as plt
import matplotlib.tri as tri
from matplotlib import cm
import csv, math, numpy, sys, os, pandas
from pyproj import Proj, transform

# Required input:
WorkDir = os.getcwd()+"/"
verticesFile = WorkDir+'Opinicon/Output/vertices.csv'
facesFile = WorkDir+'Opinicon/Output/faces.csv'
xlFile1= WorkDir+"Opinicon/Data/2017-2018.xlsx"

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


#--------------------------------------------------------
# << Read concentration measurements from excel file >>
#--------------------------------------------------------
# Projections:
wgs84 = Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')##4326
epsg26918 = Proj(init='epsg:26918')

try:
    count=0
    wb = pandas.read_excel(xlFile1)
    t0=list(wb['lon'])
    t1=list(wb['lat'])
    t2=list(wb['con'])
    xt,yt,zt=transform(wgs84,epsg26918,t0,t1,t2,radians=False)
    n=len(xt)
    maxc=max(zt)
    print "<<< Reading excel table>>>\n...", os.path.basename(xlFile1)+",",\
      n,"concentration measurement points"
except IOError:
    pass
 

plt.figure()
plt.rcParams['axes.facecolor'] = 'darkolivegreen'
plt.gca().set_aspect('equal')
plt.tricontourf(x, y, triangles, z, 100, cmap=cm.CMRmap)
plt.plot(xt, yt, '+', markersize=4, color='limegreen', alpha=0.6)
#plt.colorbar()
plt.minorticks_on()
plt.grid(c='grey', ls='-', alpha=0.3)
plt.title('Interpolated eDNA concentration')
plt.xlabel('Easting')
plt.ylabel('Northing')
# Set x,y limits or comment out to draw the whole map 
#plt.xlim(394800,395800) 
#plt.ylim(4934500,4935500)
#plt.xlim(391320, 395935)
#plt.ylim(4931861, 4936171)
plt.tight_layout()
plt.savefig('eDNA.png', dpi = 600)
# Interactive plot
plt.show()




