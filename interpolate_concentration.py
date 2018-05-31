#!/usr/bin/python

# Requirements: mergepoints and orient from OpiniconModel
from progressbar import ProgressBar
pbar = ProgressBar()
from pyproj import Proj, transform
import scipy, numpy, pandas
from scipy.spatial.distance import cdist
from mergepoints import sqdistance
from orient import principal_axes, rotate_coord
from stl import mesh
import shapefile, fiona, csv, math, numpy, scipy, os, sys
print "\n************* Interpolate concentration **************"
# This script reads concentration points from xlsx file and lake
# perimeter shape file. Concentration is interpolated across the
# whole lake using IDW and meshed. All files should be in the same
# projection. 
#-------------------------------------------------------------------
# Required input:
WorkDir = os.getcwd()+"/"
PerimeterFile = WorkDir+"Opinicon/Data/opinicon_perim_and_offset-3.shp"
xlFile1= WorkDir+"Opinicon/Data/2017-2018.xlsx"
OutFile = WorkDir+"Opinicon/Output/opinicon_interp_conc."
verticesFile = WorkDir+'Opinicon/Output/vertices.csv'
vertices_extFile = WorkDir+'Opinicon/Output/vertices_ext.csv'
holesFile = WorkDir+'Opinicon/Output/holes.csv'
segmentsFile = WorkDir+'Opinicon/Output/segments.csv'
facesFile = WorkDir+'Opinicon/Output/faces.csv'

#---- z scaling factor, output will be multiplied by zmult.
zmult = 100.0
#----- Triangulation options: http://dzhelil.info/triangle/
#tri = 'pq20'
tri = 'pa100q20'
#----- Inverse distance interpolation:
invp = 2  # power
intn = 24 # number of nearest neighbours 
scz = 0.05 # weight of void points
#----- Align meshes with principal axes
align = False

#------------------------------------------------------------
x=[]; y=[]; z=[]; depth=[];
#------------------------------------------------------------
# <<<<<<<<<<<<<<<<< Read perimeter file >>.>>>>>>>>>>>>>>>>>>
#------------------------------------------------------------
sh = shapefile.Reader(PerimeterFile)
sh_records = sh.shapeRecords()
sh_shapes = sh.shapes()
nShapes=range(len(sh_shapes))
ii=0; j=0; ind=[]; ind.append(0)
segments=[]
holes=[]
count=0
for i in nShapes:
   n=len(sh_shapes[i].points)
   ii=ii+n; hx=0; hy=0
   ind.append(ii)
   for j in range(n):
       tx=sh_shapes[i].points[j][0]
       ty=sh_shapes[i].points[j][1] 
       x.append(tx); y.append(ty)
       hx += tx; hy += ty
   hx /= n; hy /= n
   holes.append([hx,hy])
   z += sh_shapes[i].z
print "<<< Reading perimeter >>>\n...", os.path.basename(PerimeterFile)+",", len(x), "points"
print "... min =", min(z), "max = ", max(z)
minp=min(z)
print "... resetting z values to -0.0001"
for i in range(len(z)):
  z[i] *= -0.001/minp

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
    for i in range(n):
          x.append(float(xt[i]))
          y.append(float(yt[i]))
          z.append(float(zt[i]/maxc))
          count+=1
    print "<<< Reading excel table>>>\n...", os.path.basename(xlFile1)+",",\
      count,"concentration measurement points"
    print "... maximal concentration =", maxc
    print "... rescaled concentration =",zmult

except IOError:
    pass
 
#---------------------------------------------------------
# <<<<<< Triangulate Planar Straight Line Graph >>>>>>>>>
#---------------------------------------------------------
import triangle
import triangle.plot
print "<<< Constrained conforming Delaunay triangulation >>>"   
print "... options:", tri
# segments from offset lines
nPoly=len(nShapes)/2
# offset line segments: 
for i in range(len(nShapes)/2, len(nShapes)):
   for j in range(ind[i],ind[i+1]-1):
      segments.append([j,j+1]) 
   segments.append([j+1,ind[i]])
   
ns=len(segments)
SEGM = numpy.ndarray(shape = (ns,2), dtype = int)
for i in range(ns):
   SEGM[i,0] = segments[i][0]; SEGM[i,1] = segments[i][1]; 

# vertices
ns=len(x)       
XY_S = numpy.ndarray(shape = (ns,2), dtype = float)
for i in range(ns):
   XY_S[i,0] = x[i]; XY_S[i,1] = y[i];    
# number of holes (islands)
ns=nPoly-1
# perimeter comes first, so we skip it
holes.pop(0)
HOLES = numpy.ndarray(shape = (ns,2), dtype = float)
for i in range(ns):
   HOLES[i,0] = holes[i][0]; HOLES[i,1] = holes[i][1]; 

A = dict(vertices=XY_S, segments=SEGM, holes=HOLES)
B = triangle.triangulate(A,tri)

#----------------------------------------------------
# <<<<<<<<<< Prepare to write stl files >>>>>>>>>>>>
#----------------------------------------------------
ns=len(x)
na = len(B['vertices'])

# allocate arrays for vertices
vrtb = numpy.ndarray(shape = (na,3), dtype = float)
vrtt = numpy.ndarray(shape = (na,3), dtype = float)
rpt = numpy.ndarray(shape = (1,2), dtype = float)

# fill arrays with existing data 
for i in range(ns):
      vrtb[i,0] = XY_S[i,0]; vrtb[i,1] = XY_S[i,1];vrtb[i,2] = abs(z[i])*zmult; # bottom surface
      vrtt[i,0] = XY_S[i,0]; vrtt[i,1] = XY_S[i,1]; vrtt[i,2] = 0.0;  # top surface

# Interpolate depth of new points using inverse distance weighting      
print "<<< Inverse distance weighting >>>"
print "... power =", invp
print "... number of neighbours =", intn
print "... weight of void points =", scz
print "... interpolating values of", na-ns, "vertices ..."

# New arrays for interpolation now including all vertices
XY_T = numpy.ndarray(shape = (na,2), dtype = float)
for i in range(na):
     XY_T[i,0] =  B['vertices'][i][0]
     XY_T[i,1] =  B['vertices'][i][1]

# We assume that concentration at all new triangulated points is 0.0
for j in range(ns,na):
   x.append(B['vertices'][j][0])
   y.append(B['vertices'][j][1])
   z.append(0.0)

# Interpolation iterrator
for j in pbar(range(ns,na)):
   # the new vertices
   vrtb[j,0] = vrtt[j,0] = B['vertices'][j][0]   
   vrtb[j,1] = vrtt[j,1] = B['vertices'][j][1]
   vrtb[j,2] = vrtt[j,2] = 0.0
   rpt[0][0] = vrtb[j,0] 
   rpt[0][1] = vrtb[j,1] 

# To include only measured points:
#   dist = scipy.spatial.distance.cdist(rpt,XY_S,'sqeuclidean')
   dist = scipy.spatial.distance.cdist(rpt,XY_T,'sqeuclidean')
   ds = numpy.argsort(dist)
   sm = 0; mu = 0; k = 0;
   # We skip the first distance because it is always 0.0 (rpt is present in XY_T)
   for k in range(1,intn): 
      if z[ds[0][k]] > -0.00001: # exclude negative perimeter lines from IDW
        di = math.sqrt(dist[0][ds[0][k]])
        wu = pow(di,-invp)
        if z[ds[0][k]] == 0.0:
          wu *= scz
        sm += wu
        mu += z[ds[0][k]]*wu
   if sm != 0.0:     
        vrtb[j,2] = mu*zmult/sm
   else:
        vrtb[j,2] = 0.0

# the faces (triangles)
faces = B['triangles']

# align with principal axes
if align == True:
  center,Rot = principal_axes(vrtb,2)
  vrtb = rotate_coord(vrtb,center,Rot)
  vrtt = rotate_coord(vrtt,center,Rot)  
  HOLES = rotate_coord(HOLES,center,Rot)

# <<<<<<<<< Create meshes >>>>>>>>>>
#-------------------------------------------------------------
bottom_msh = mesh.Mesh(numpy.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        bottom_msh.vectors[i][j] = vrtb[f[j],:]
        
top_msh = mesh.Mesh(numpy.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        top_msh.vectors[i][j] = vrtt[f[j],:]
# Write meshes to files
bottom_msh.save('bottom_mesh_.stl')
top_msh.save('top_mesh_.stl')

#----------------------------------------------------
# <<<<<<< Write out vertices, segments, holes >>>>>>>
with open(verticesFile, 'wb') as f:
    writer = csv.writer(f)
    writer.writerows(vrtb)
segments=[]
# Build array of segments from zero lines
for i in range(nPoly):
   for j in range(ind[i],ind[i+1]-1):
      segments.append([j,j+1]) 
   segments.append([j+1,ind[i]])
#---------------------------------   
ns=len(segments)
SEGM2 = numpy.ndarray(shape = (ns,2), dtype = int)
for i in range(ns):
   SEGM2[i,0] = segments[i][0]; SEGM2[i,1] = segments[i][1]; 
    
with open(segmentsFile, 'wb') as f:
    writer = csv.writer(f)
    writer.writerows(SEGM2)
with open(holesFile, 'wb') as f:
    writer = csv.writer(f)
    writer.writerows(HOLES)
with open(facesFile, 'wb') as f:
    writer = csv.writer(f)
    writer.writerows(faces)
     
#----------------------------------------------------------
# <<<<<<<< Write output shapefile and projection >>>>>>>>>>
#----------------------------------------------------------
# Initialize output shapefile
ShapeType=shapefile.POINTZ
w=shapefile.Writer(ShapeType)
w.autobalance=1
w.field("ID", "F",10,5)
print "<<< Output >>>\n...", os.path.basename(OutFile)+"shp,", len(x), "points"
# write as points
pcount=0

for i in range(na):
  w.point(vrtb[i,0],vrtb[i,1],vrtb[i,2])
  w.record(vrtb[i,2])
  pcount += 1

for s in w.shapes():
  s.shapeType = ShapeType
w.save(OutFile)
# Write projection
with fiona.open(PerimeterFile) as fp:
  prj=open(OutFile+"prj","w")
  prj.write(fp.crs_wkt)
  prj.close()
#import matplotlib.pyplot as plt
#triangle.plot.compare(plt, A, B)
#plt.show()


