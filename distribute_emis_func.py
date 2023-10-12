import numpy as np
from netCDF4 import Dataset

def make_grid_LL(llres, in_extent=[-180, 180, -90, 90], out_extent=[]):
    """
    Creates a lat/lon grid description.

    Args:
        llres: str
            lat/lon resolution in 'latxlon' format (e.g. '4x5')

    Keyword Args (optional):
        in_extent: list[float, float, float, float]
            Describes minimum and maximum latitude and longitude of initial grid
            in the format [minlon, maxlon, minlat, maxlat]
            Default value: [-180, 180, -90, 90]
        out_extent: list[float, float, float, float]
            Describes minimum and maximum latitude and longitude of target grid
            in the format [minlon, maxlon, minlat, maxlat]. Needed when intending
            to use grid to trim extent of input data
            Default value: [] (assumes value of in_extent)

    Returns:
        llgrid: dict
            dict grid description of format {'lat'   : lat midpoints,
                                            'lon'   : lon midpoints,
                                            'lat_b' : lat edges,
                                            'lon_b' : lon edges}
    """

    # get initial bounds of grid
    [minlon, maxlon, minlat, maxlat] = in_extent
    [dlat, dlon] = list(map(float, llres.split('x')))
    lon_b = np.linspace(minlon - dlon / 2, maxlon - dlon /
                        2, int((maxlon - minlon) / dlon) + 1)
    lat_b = np.linspace(minlat - dlat / 2, maxlat + dlat / 2,
                        int((maxlat - minlat) / dlat) + 2)
    if minlat <= -90:
        lat_b = lat_b.clip(-90, None)
    if maxlat >= 90:
        lat_b = lat_b.clip(None, 90)
    lat = (lat_b[1:] + lat_b[:-1]) / 2
    lon = (lon_b[1:] + lon_b[:-1]) / 2
    

    # Trim grid bounds when your desired extent is not the same as your initial grid extent
    if out_extent == []:
        out_extent = in_extent
    if out_extent != in_extent:
        [minlon, maxlon, minlat, maxlat] = out_extent
        minlon_ind = np.nonzero(lon >= minlon)
        maxlon_ind = np.nonzero(lon <= maxlon)
        lon_inds = np.intersect1d(minlon_ind, maxlon_ind)
        lon = lon[lon_inds]
        # make sure to get edges of grid correctly
        lon_inds = np.append(lon_inds, np.max(lon_inds) + 1)
        lon_b = lon_b[lon_inds]

        minlat_ind = np.nonzero(lat >= minlat)
        maxlat_ind = np.nonzero(lat <= maxlat)
        lat_inds = np.intersect1d(minlat_ind, maxlat_ind)
        lat = lat[lat_inds]
        # make sure to get edges of grid correctly
        lat_inds = np.append(lat_inds, np.max(lat_inds) + 1)
        lat_b = lat_b[lat_inds]

    llgrid = {'lat': lat,
            'lon': lon,
            'lat_b': lat_b,
            'lon_b': lon_b}
    return llgrid

def read_gc_box_height(gc_file,nlev):
    ''' This function reads GEOS-Chem box height from StateMet files. '''
    
    #Open Dataset.
    fk = Dataset(gc_file, mod='r')
    box_height = fk.variables['Met_BXHEIGHT'][:]
    box_height = box_height[0,:,:,:]
    area = fk.variables['AREA'][:]
    fk.close()

    # Calculate the top, mid, and bottom altitudes of each box.
    # Only the middle altitude is actually used elsewhere.
    top_alt = np.zeros_like(box_height)
    bot_alt = np.zeros_like(box_height)
    mid_alt = np.zeros_like(box_height)
    for l in range(nlev):
        if l==0:
            top_alt[l,:,:] = box_height[l,:,:]
            mid_alt[l,:,:] = 0.5*np.add(bot_alt[l,:,:], top_alt[l,:,:])
            #print(f"{l} {bot_alt[l,0,0]*1e-3:.2f} {box_height[l,0,0]*1e-3:.2f} {top_alt[l,0,0]*1e-3:.2f}")
            continue
        bot_alt[l,:,:] = top_alt[l-1,:,:]
        top_alt[l,:,:] = np.add(top_alt[l-1,:,:], box_height[l,:,:])
        mid_alt[l,:,:] = 0.5*np.add(bot_alt[l,:,:], top_alt[l,:,:])
        #print(f"{l} {bot_alt[l,0,0]*1e-3:.2f} {box_height[l,0,0]*1e-3:.2f} {top_alt[l,0,0]*1e-3:.2f}")
    
    return box_height, area, bot_alt, mid_alt, top_alt

def get_ross_profiles():
    """Get Ross profiles provided in 5-km increments in Figure 1 of
        https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013EF000160
    """
    # Centre altitude (km):
    # These are in 5-km increments, so 80-85, 75-80 and so on.
    ross_alt = np.arange(102.5, 0, -5)

    # Percent of propellant mass (unitless):
    # Old values        
    # ross_prop_mass = [2.3, 3.4, 3.5, 3.6, 3.8, 4.0, 3.5, 2.8, 3.0, 3.3, 3.5, 3.7, 4.0, 4.5, 5.0, 7.5, 17.5]
    
    # New values using webplotdigitizer. Percentages add to 79% so 21% unaccounted for, and must be emitted above 100 km.
    # So adding an extra bin at midpoint 102.5 containing 21% of emissions.    
    ross_prop_mass = np.asarray([21.0, 2.0, 2.1, 2.3, 2.4, 2.6, 2.7, 2.9, 3.5, 4.0, 3.2, 2.3, 2.5, 2.7, 3.0, 3.3, 3.9, 4.4, 5.0, 6.9, 17.3])
    ross_prop_mass = ross_prop_mass / np.sum(ross_prop_mass) * 100
    
    # Create cumulative distribution of propellant mass. 
    # This is used in the interp_prop_mass function to work out how much propellant is emitted above the gc limits.
    ross_cumulative_mass = np.zeros_like(ross_prop_mass)
    for i in range(0,len(ross_prop_mass)):
        if i == 0:
            ross_cumulative_mass[i] = 100
        else:
            ross_cumulative_mass[i] = ross_cumulative_mass[i-1] - ross_prop_mass[i-1]
            
    return ross_alt, ross_prop_mass, ross_cumulative_mass

def interp_prop_mass(bot_alt, mid_alt, top_alt, ross_alt, ross_cumulative_mass, ross_prop_mass, nlev, i, j):
    
    """Interpolate proportional propellant mass burned from Ross and Sheaffer
        5-km incremental grid to GEOS-Chem vertical grid.
        Input  (i) and  (j) 
        
        GEOS-Chem grids are ordered [alt, lat, lon].

    Args:
        i (numpy.int64): longitude index of model gridbox where launch occurs.
        j (numpy.int64): latitude index of model gridbox where launch occurs.
    """        
    # Interpolate the cumulative distribution to work out how much propellant is emitted above the top altitude.
    # y = y1 + ((x – x1) / (x2 – x1)) * (y2 – y1)]
    h = top_alt[-1,j,i]*1e-3
    for count, alt in enumerate(ross_alt):
        if alt-h < 0:
            break
    ross_ind = count - 1
    propellant_in_gc = ross_cumulative_mass[ross_ind] + ((h - ross_alt[ross_ind]) /
                                    (ross_alt[ross_ind-1] - ross_alt[ross_ind])) * (ross_cumulative_mass[ross_ind-1] - ross_cumulative_mass[ross_ind])
    
    
    # Define array of percent distribution of propellant mass on GEOS-Chem grid:
    # This sets up an array over number of GEOS-Chem levels (47 or 72).
    gc_relative_mass = np.zeros_like(mid_alt[:,j,i])
    count = 0
    # Loop over GEOS-Chem layers in reverse:
    for l, h in enumerate(reversed(mid_alt[:,j,i])):
        # Find Ross profile layer closest to centre altitude of GEOS-Chem grid:
        #ross_ind = np.argmin(np.abs(h*1e-3 - ross_alt)) # old method, wasn't interpolating properly.
        for count, alt in enumerate(ross_alt):
            if alt-h*1e-3 < 0:
                break
            if h*1e-3 > 2.5:
                ross_ind = count + 1
            else:
                ross_ind = count

        # Interpolate, and clip so that no values are above 17.5%.
        gc_relative_mass[l] = np.clip(ross_prop_mass[ross_ind-1] + ((h*1e-3 - ross_alt[ross_ind-1]) /
                                            (ross_alt[ross_ind] - ross_alt[ross_ind-1])) * (ross_prop_mass[ross_ind] - ross_prop_mass[ross_ind-1]),
                                        None,17.5)
        
        # Now scale by the box height and the fact that the Ross altitude is in 5 km bins.
        gc_relative_mass[l] = gc_relative_mass[l] / 5 * (top_alt[nlev-l-1,j,i]*1e-3 - bot_alt[nlev-l-1,j,i]*1e-3)
        
    
    # ~ 22% of propellant is consumed above the GC-boundary each time.
    # Normalize so that the portion in GC adds to ~ 68%:
    gc_relative_mass = propellant_in_gc * gc_relative_mass / np.sum(gc_relative_mass) 
    
    # This routine scales gc_relative_mass by the mass that should be in each bin. Not used, simpler function above used instead.
    #for count, mid_alt in enumerate(self.ross_alt):
    #    prop_mass_in_bin = 0
    #    top_alt = mid_alt + 2.5
    #    bot_alt = mid_alt - 2.5
    #    index_range=[]
    #    for level, gc_alt in enumerate(self.mid_alt[:,j,i]):
    #        box_height = self.top_alt[level,j,i]-self.bot_alt[level,j,i]
    #        if bot_alt <= gc_alt*1e-3 <= top_alt:
    #            prop_mass_in_bin += self.gc_mass_reversed[level]   
    #            index_range.append(level)
    #    if len(index_range) > 0:
    #        if mid_alt == 2.5:
    #            self.gc_mass_reversed[min(index_range):max(index_range)+1] = ross_prop_mass[count] / len(index_range)
    #        else:
    #            self.gc_mass_reversed[min(index_range):max(index_range)+1] = self.gc_mass_reversed[min(index_range):max(index_range)+1] * ross_prop_mass[count] / prop_mass_in_bin
    
    return propellant_in_gc, gc_relative_mass

def define_scale_factors_old():
    """Create vertical fuel burned scale factors for the 47-layer GEOS-Chem model.
    This is not used any more."""        
    
    # Scale factors obtained by regridding vertical profile from Ross and Sheaffer (2014) to the GEOS-Chem vertical grid.
    # https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013EF000160
    # This was original added by Eloise to manually regrid Ross2014 to GEOSChem. Now automatically doing this in interp_prop_mass.
    scale_emis=[0.049891495, 0.111470331, 0.078233471, 0.063383364,
                0.060797961, 0.059372945, 0.053323669, 0.046966629,
                0.023518583, 0.025045331, 0.023940206, 0.02557847,
                0.012627866, 0.012796323, 0.013007597, 0.019845309,
                0.020190667, 0.018954765, 0.016881733, 0.015656558,
                0.014616122, 0.009489471, 0.020372272, 0.018580066,
                0.017329028, 0.01620592,  0.015434268, 0.014502025,
                0.014023726, 0.013345366, 0.008601074, 0.008422093,
                0.008250749, 0.007984673, 0.007841863, 0.006174571,
                0.004551207, 0.004493408, 0.004437623, 0.004394395,
                0.004352409, 0.004298898, 0.004244104, 0.004205638,
                0.00416808,  0.004117436, 0.004080244]
    # Data are from layer 47 to the surface, aso need to be reversed:
    scale_emis = scale_emis[::-1]