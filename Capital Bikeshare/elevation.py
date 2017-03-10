import numpy as np
from matplotlib import pyplot as plt
import gdal
import pyproj

elev_filename = r"BARE_EARTH_2004.TIF\BARE_EARTH_2004.TIF"
# projection for Maryland State Plane: http://www.mgs.md.gov/geology/maryland_coordinate_system.html
# testing: http://www.earthpoint.us/StatePlane.aspx
MSPproj = dict(proj='lcc',lon_0=-77, lat_1=38+(18.0/60), lat_2=39+(27.0/60), lat_0=37+(40.0/60), x_0=4e5)
#proj = pyproj.Proj(proj='lcc',lon_0=-77, lat_1=38+(18.0/60), lat_2=39+(27.0/60), lat_0=37+(40.0/60), x_0=4e5)


class elevationModel:
    def __init__(self, filename=elev_filename):
        self._raster = gdal.Open(filename)
        self.proj = pyproj.Proj(**MSPproj)
        self._affine = self._raster.GetGeoTransform()
        
    def map2raster(self,x,y):
        x0,dx,_,y0,_,dy = self._affine
        return (x-x0)/dx, (y-y0)/dy
    
    def elevation(self,x,y):
        X,Y = self.map2raster(x,y)
        try:
            z = self._raster.ReadAsArray(xoff=int(X),yoff=int(Y),xsize=1,ysize=1).flat[0]
            assert z >= 0
            return z
        except:
            return None