#!/usr/bin/python

'''Save out rocket emissions as COARDS compliant files for input to 
   HEMCO/GEOS-Chem.

   NOTE: still need to replace with updated emissions from Chloe.
   '''

# Import relevant packages:
import glob
import argparse
import sys
import os
from os import path
import netCDF4 as nc4
from netCDF4 import Dataset
import numpy as np
import math

import pdb

sys.path.append('/home/ucfacb0/python/packages/GCPy')
from gcpy.grid import make_grid_LL

class RocketData:
    '''Read rocket launch and re-entry emissions'''
    def __init__(self,launchfile,reentryfile):

        # Read launch file emissions:
        fh = Dataset(launchfile, mode='r')
        
        # Extract data of interest:
        self.launch_lons = fh.variables['Longitude'][:]
        self.launch_lats = fh.variables['Latitude'][:]
        self.launch_time = fh.variables['Time (UTC)'][:]  # UTC hours
        self.launch_month = fh.variables['Month'][:]
        self.launch_day = fh.variables['Day'][:]
        self.launch_id = fh.variables['ID'][:]
        self.rocket_type = fh.variables['Rocket Type'][:]
        self.launch_b_nox = fh.variables['Boosters NOx'][:]
        self.launch_b_h2o = fh.variables['Boosters H2O'][:]
        self.launch_b_bc = fh.variables['Boosters BC'][:]
        self.launch_b_al = fh.variables['Boosters Alumina'][:]
        self.launch_b_hcl = fh.variables['Boosters HCl'][:]
        self.launch_b_cl = fh.variables['Boosters Cl'][:]
        self.launch_s1_nox = fh.variables['Stage 1 NOx'][:]
        self.launch_s1_h2o = fh.variables['Stage 1 H2O'][:]
        self.launch_s1_bc = fh.variables['Stage 1 BC'][:]
        self.launch_s1_al = fh.variables['Stage 1 Alumina'][:]
        self.launch_s1_hcl = fh.variables['Stage 1 HCl'][:]
        self.launch_s1_cl = fh.variables['Stage 1 Cl'][:]
        fh.close()

        # Calculate BC emissions for all carbon-based fuels
        # (that's all rockets in 2019):
        #
        # EI_BC = max(0.04, min(1 * np.exp(0.12 * (h - 15))))

        print('Total booster + stage 1 BC emissions (tonnes) = ',sum(self.launch_s1_bc+self.launch_b_bc)*1e-3)
        print('Total booster + stage 1 NOx emissions (tonnes) = ',sum(self.launch_s1_nox+self.launch_b_nox)*1e-3)
        print('Total booster + stage 1 H2O emissions (tonnes) = ',sum(self.launch_s1_h2o+self.launch_b_h2o)*1e-3)
        print('Total booster + stage 1 Al2O3 emissions (tonnes) = ',sum(self.launch_s1_al+self.launch_b_al)*1e-3)
        print('Total booster + stage 1 Cl emissions (tonnes) = ',sum(self.launch_s1_cl+self.launch_b_cl)*1e-3)
        print('Total booster + stage 1 HCl emissions (tonnes) = ',sum(self.launch_s1_hcl+self.launch_b_hcl)*1e-3)
        
        # Read re-entry file emissions:
        fg = Dataset(reentryfile, mode='r')
        #print(fg)
        #self.tmp = fg.variables['ID'][:]   # Re-entry ID
        #self.tmp = fg.variables['Controlled?'][:]   # Whether controlled or not (Y/N)
        #print(self.tmp.shape)
        #index = 2
        # String with length of 8 is from rocket launch and should be ignored if not a controlled entry, something like if len(ID)==8 and Controlled=='Y', then calculate 0.175*mass to get NOx, if len(ID)==8 and Controlled=='Y', then don't calculate re-entry NOx.
        #print(len(self.tmp[index]))
        # Extract data of interest:
        self.reentry_id = fg.variables['ID'][:]
        self.reentry_type = fg.variables['Controlled?'][:]
        self.reentry_lons = fg.variables['Longitude'][:]
        self.reentry_lats = fg.variables['Latitude'][:]
        self.reentry_time = fg.variables['Time (UTC)'][:]   # UTC hours
        self.reentry_month = fg.variables['Month'][:]
        self.reentry_day = fg.variables['Day'][:]
        self.reentry_mass = fg.variables['Total Mass'][:]
        self.reentry_nox = fg.variables['NOx from re-entry'][:]  # in tonnes
        fg.close()

        print('Total reentry NOx emissions (tonnes) = ',sum(self.reentry_nox)*1e-3)

        # Create vertical fuel burned scale factors for the 47-layer GEOS-Chem model:
        # Scale factors obtained by regridding vertical profile from
        # Ross and Sheaffer (2014) 
        # https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013EF000160
        # to the GEOS-Chem vertical grid.
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
        self.scale_emis = scale_emis[::-1]

        # Read database of propellant mass per rocket type:
        # Define database filename:
        #rocket_prop_mass_file = './rocket_propellant_mass_dataset.nc'
        propellant_mass_file = './rocket_type_propellant_mass_2019_database.nc'

        # Get data:
        fh = Dataset(propellant_mass_file, mode='r')
        
        # Extract relevant data:
        self.rocket_name       = fh.variables['2019_rocket_name'][:]
        self.booster_prop_mass = fh.variables['booster_prop_mass'][:]
        self.stage1_prop_mass  = fh.variables['stage1_prop_mass'][:]
        self.booster_prop_type = fh.variables['booster_prop_type'][:]
        self.stage1_prop_type  = fh.variables['stage1_prop_type'][:]
        self.pei_fuel_type     = fh.variables['fuel_type_for_pei'][:]
        self.h2_pei            = fh.variables['h2_pei'][:]
        self.h2o_pei           = fh.variables['h2o_pei'][:]
        self.cl_pei            = fh.variables['cl_pei'][:]
        self.hcl_pei           = fh.variables['hcl_pei'][:]
        self.al2o3_pei         = fh.variables['al2o3_pei'][:]
        self.bc_pei            = fh.variables['bc_pei'][:]
        self.co_pei            = fh.variables['co_pei'][:]
        self.co2_pei           = fh.variables['co2_pei'][:]

        # Extract rocket name:
        #self.rocket_name = fh.variables['name'][:]

        # Extract propellant mass (in kg):
        #self.rocket_propellant_mass = fh.variables['mass'][:]

        # Close the file:
        fh.close()
        

class OutputEmis:
    def __init__(self, rocketdata, res, ts, levs, blev, reentry_levs, gc_dir):

        # Define relevant rocketdata:
        #self.launch_id = rocketdata.launch_id

        # Get Ross vertical profiles of propellant burned:
        # Data are self.ross_alt and self.ross_prop_mass
        self.get_ross_profiles()

        # Sum emissions (sanity check):
        self.nox_launch_total = 0.0
        self.bc_total  = 0.0
        self.h2o_total = 0.0
        self.co_total = 0.0
        self.al2o3_launch_total = 0.0
        self.cl_total = 0.0
        self.hcl_total = 0.0
        self.nox_reentry_total = 0.0
        self.al2o3_reentry_total = 0.0

        # Constants:
        self.mw_h = 1.008
        self.mw_h2 = self.mw_h * 2
        self.mw_h2o = self.mw_h2 + 16.00

        # Grid:
        # Make grid at input resolution:
        grid = make_grid_LL(res)

        # Define lats and lons:        
        self.nlon = len(grid['lon'])
        self.nlat = len(grid['lat'])
        self.nlev = levs
        self.lon =  grid['lon']
        self.lat =  grid['lat']
        #2D lat and lon:
        #X, Y = np.meshgrid(self.lon, self.lat,indexing='ij')
        #self.lon2d = X
        #self.lat2d = Y
        self.nhours = 24
        #self.blev = blev
        self.bot_reenter = min(reentry_levs)
        self.top_reenter = max(reentry_levs)
        self.n_reenter_levs = self.top_reenter - self.bot_reenter + 1

        # Time step:
        self.ts = ts 

        # months:
        month=np.arange(1,3)
        ndays = 31

        # Loop over months:
        for m in range(len(month)):

            month_emis=0.0

            # Get month string:
            if m+1<=9:
                self.strmon='0'+str(m+1)
            else:
                self.strmon=str(m+1)

            print('Month processing: ', self.strmon)

            # Read GEOS-Chem box height:
            # Define file path of GEOS-Chem file:
            if res == '4x5' and self.nlev==47:
                self.gc_file = path.join(gc_dir, 'GEOSChem.StateMet.2019'+self.strmon+'01_0000z.nc4')
                self.read_gc_box_height()
            
            # Loop over days:
            for d in range(ndays):

                # Get day string:
                if d+1<=9:
                    self.strday='0'+str(d+1)
                else:
                    self.strday=str(d+1)

                if res == '2x2.5' and self.nlev==72:
                    # StateMet file:
                    self.gc_file = path.join(gc_dir, 'GEOSChem.StateMet.2019'+self.strmon+self.strday+'_0000z.nc4')
                    file_exists = os.path.exists(self.gc_file)
                    if not file_exists: continue
                    self.read_gc_box_height()

                if res == '4x5' and self.nlev==72:
                    # StateMet file:
                    self.gc_file = path.join(gc_dir, 'GEOSChem.StateMet.2019'+self.strmon+self.strday+'_0000z.nc4')
                    file_exists = os.path.exists(self.gc_file)
                    if not file_exists: continue
                    self.read_gc_box_height()

                # Data arrays:
                #self.reentry_nox = np.zeros((self.nlon,self.nlat,self.nlev))
                self.rocket_nox = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_h2o = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_bc = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_co = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_al = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_hcl = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_cl = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))

                # Initialize:
                self.pmin,self.pmax=np.nan,np.nan
                self.qmin,self.qmax=np.nan,np.nan

                print('----> Day processing: ',self.strday)

                # Define output file name for this day:
                self.outfile_rocket_emis = path.join(outdir,self.strmon,'ROCKET_EMIS_'+res+'_'+str(self.nlev)+'L_2019'+self.strmon+self.strday+'.nc4')
                print(self.outfile_rocket_emis)
                #print('ROCKET_EMIS_2x2.5_47L_2019'+self.strmon+self.strday+'.nc4')
                
                # Launches:
                l_ind=np.where((rocket_data.launch_month==(m+1))&(rocket_data.launch_day==(d+1))&(~np.isnan(rocket_data.launch_time)))[0]
                if len(l_ind)>0:
                
                    # Call grid emissions routine:
                    self.grid_emis(l_ind,rocket_data.launch_lons[l_ind],rocket_data.launch_lats[l_ind],rocket_data.launch_time[l_ind],'launch',rocket_data.launch_id[l_ind], rocket_data.rocket_type[l_ind])
                    #sys.exit()
                    #month_emis += sum(rocket_data.launch_s1_nox[l_ind]+rocket_data.launch_b_nox[l_ind])*1e-3

                # Re-entries:
                r_ind=np.where((rocket_data.reentry_month==(m+1))&(rocket_data.reentry_day==(d+1)))[0]
                # Skip if non-controlled re-entry of immediately launched
                # rocket, as this was an error in the original inventory:
                #if len(r_ind)>0:
                    #tmp_id = (','.join(rocket_data.reentry_id[r_ind]))
                #if (len(tmp_id)==8 and rocket_data.reentry_type[r_ind]=='N'):
                #    r_ind=[]
                if len(r_ind)>0:
                    #print(rocket_data.reentry_id[r_ind], rocket_data.reentry_type[r_ind])
                    #print(rocket_data.reentry_id[r_ind])
                    #print(rocket_data.reentry_type[r_ind])
                    self.grid_emis(r_ind,rocket_data.reentry_lons[r_ind],rocket_data.reentry_lats[r_ind],rocket_data.reentry_time[r_ind],'reentry',' ',' ')
                    # Sum up all re-entry NOx (kg):
                    #self.nox_reentry_total += sum(rocket_data.reentry_nox[r_ind])

                # (4) Save file:
                if ( len(l_ind)>0 or len(r_ind)>0 ):
                    self.save_netcdf()
                else:
                    # Create dummy file to accommodate HEMCO file reading
                    # Settings:
                    #lat_ind=np.where(self.lat==0)[0]
                    #if len(lat_ind)==0:
                    lat_ind=np.argmin(abs(self.lat-0))
                    #    print(lat_ind)
                    
                    self.qmin,self.qmax=int(lat_ind),int(lat_ind)
                    lon_ind=np.argmin(abs(self.lon-0))
                    #lon_ind=np.where(self.lon==0)
                    self.pmin,self.pmax=int(lon_ind),int(lon_ind)
                    self.save_netcdf()

            #print('Month emissions (tonnes): ',month_emis)

    def read_gc_box_height(self):

        # Read GEOS-Chem box height:
        fk = Dataset(self.gc_file, mod='r')

        # Extract data of interest:
        self.box_height = fk.variables['Met_BXHEIGHT'][:]
        self.box_height = self.box_height[0,:,:,:]
        self.area = fk.variables['AREA'][:]

        # Calculate bottom altitude of each box:
        self.top_alt = np.zeros_like(self.box_height)
        self.bot_alt = np.zeros_like(self.box_height)
        self.mid_alt = np.zeros_like(self.box_height)
        #print(self.alt.shape)
        for l in range(self.nlev):
            if l==0:
                self.top_alt[l,:,:] = self.box_height[l,:,:]
                self.mid_alt[l,:,:] = 0.5*np.add(self.bot_alt[l,:,:], self.top_alt[l,:,:])
                continue
            #print(self.box_height[l-1,50,50])
            self.bot_alt[l,:,:] = self.top_alt[l-1,:,:]
            self.top_alt[l,:,:] = np.add(self.top_alt[l-1,:,:], self.box_height[l-1,:,:])
            self.mid_alt[l,:,:] = 0.5*np.add(self.bot_alt[l,:,:], self.top_alt[l,:,:])
            #if l>60: print(l, self.bot_alt[l-1,50,50], self.mid_alt[l-1,50,50], self.top_alt[l-1,50,50])

    def calculate_bc_ei(self, height):
        """Calculate black carbon vertical emission indices on the GEOS-Chem
           grid in g BC per kg propellant burned"""
        #sys.exit()
        self.ei_bc = np.zeros_like(height)
        
        for i, h in enumerate(height):
            self.ei_bc[i] = 25 * (max(0.04, (min(1, (0.04*(np.exp(0.12*(h-15))))))))

        ## !!!***  NEED TO CHANGE 25 TO 5 IN ABOVE EQUATION WHEN ALSO INCLUDE ROCKETS IN
        ##         FUTURE INVENTORY THAT USE LIQUID METHANE FUEL ***!!! ##

    def calculate_secondary_nox_ei(self, height):
        """Calculate secondary NOx emission index from high-temperature rocket plume 
           in g NO per kg propellant burned. Applies to all rockets"""
        self.ei_sec_nox = np.zeros_like(height)

        for i, h in enumerate(height):
            self.ei_sec_nox[i] = 33 * np.exp((-0.26)*h)

        ## !!**  STILL NEED TO CALCULATE PRIMARY NOx FOR ROCKETS WITH N-BASED FUEL **!! ##

    def calculate_co_ei(self, height, co_pei, co2_pei):
        """Calculate CO emission index in g CO per kg propellant burned."""
        self.ei_co = np.zeros_like(height)

        for i, h in enumerate(height):
            self.ei_co[i] = min( co_pei, 0.0025*np.exp(0.067*h)*(co2_pei + co_pei))

    def get_ross_profiles(self):
        """Get Ross profiles provided in 5-km increments in Figure 1 of
           https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013EF000160
        """
        # Centre altitude (km):
        # These are in 5-km increments, so 80-85, 75-80 and so on.
        self.ross_alt = np.arange(82.5, 0, -5)

        # Percent of propellant mass (unitless):
        ross_prop_mass = [2.3, 3.4, 3.5, 3.6, 3.8, 4.0, 3.5, 2.8, 3.0,
                          3.3, 3.5, 3.7, 4.0, 4.5, 5.0, 7.5, 17.5]
        self.ross_prop_mass = np.asarray(ross_prop_mass)

    def interp_prop_mass(self, i, j):
        """Interpolate proportional propellant mass burned from Ross and Sheaffer
           5-km incremental grid to GEOS-Chem vertical grid.
           Input longitude index (i) and latitude index (j) of model gridbox
           where this launch occurs.
           GEOS-Chem grids are ordered [alt, lat, lon].
        """
        # y = y1 + ((x – x1) / (x2 – x1)) * (y2 – y1)

        # Define array of percent distribution of propellant mass on GEOS-Chem grid:
        gc_relative_mass = np.zeros_like(self.mid_alt[:,j,i])

        # Loop over GEOS-Chem layers in reverse:
        for l, h in enumerate(reversed(self.mid_alt[:,j,i])):
            #print(l,h)

            # Find Ross profile layer closest to centre altitude of GEOS-Chem grid:
            ross_ind = np.argmin(np.abs(h*1e-3 - self.ross_alt))

            #print(' ')
            #print(self.ross_alt)

            # Interpolate:
            gc_relative_mass[l] = self.ross_prop_mass[ross_ind-1] + ((h*1e-3 - self.ross_alt[ross_ind-1]) /
                                                 (self.ross_alt[ross_ind] - self.ross_alt[ross_ind-1])) * (self.ross_prop_mass[ross_ind] - self.ross_prop_mass[ross_ind-1])

            #print(gc_relative_mass[l], self.ross_relative_mass[ross_ind], self.ross_relative_mass[ross_ind+1])
            #sys.exit()
        # Find Ross altitude closest to altitude
        #print(gc_relative_mass)
        #print(self.mid_alt[:-1,j,i])
        #print(j,i)
        #sys.exit()

        # Normalize so that adds to 100%:
        self.gc_relative_mass = 1e2 * gc_relative_mass / np.sum(gc_relative_mass)

    def grid_emis(self,index,lon,lat,hour,emis_type,launch_id,rocket_type):
        """Grid the data onto the GEOS-Chem horizontal and vertical grid"""

        for w in range(len(lon)):
        
            # Get grid horizontal indices (p is lon index; q is lat index):
            p,q = np.argmin(abs(lon[w]-self.lon)), np.argmin(abs(lat[w]-self.lat))
            # Update grid range (lat and lon edges) to save to file:
            if np.isnan(self.pmin):
                self.pmin,self.pmax=p,p
                self.qmin,self.qmax=q,q
            if ~np.isnan(self.pmin) and self.pmin>p:
                self.pmin=p
            if ~np.isnan(self.pmax) and self.pmax<p:
                self.pmax=p
            if ~np.isnan(self.qmin) and self.qmin>q:
                self.qmin=q
            if ~np.isnan(self.qmax) and self.qmax<q:
                self.qmax=q

            # Get factor to convert from kg to kg/m2/s:
            kg_to_kgm2s = self.area[q,p]*self.ts
                
            # NOTE: GEOS-Chem data is provided as [lat,lon,lev], where
            #       levels go from surface to top-of-atmosphere

            if emis_type=='launch':

                # Skip missions that failed at start of launch. For 2019, these
                # include all labelled "F" except F04 that failed at stage 3:
                t_id = launch_id[w]
                t_id = t_id[-3:]
                if t_id=='E01' or t_id=='F01' or t_id=='F02' or t_id=='F03' or t_id=='F05':
                    print('Launch ' + launch_id[w] + ' failed. Not processing')
                    continue

                # Linearly interpolate Ross profile proportion of propellant
                # mass to GEOS-Chem vertical grid:
                # Dataset of interest from this is self.gc_prop_mass
                self.interp_prop_mass(p, q)

                #print(self.gc_relative_mass)

                # Rename variable for rocket type:
                ttype = rocket_type[w]
                trim_type = ttype[0:5]
                
                # Trim the rocket names in the propellant mass database:
                # !!!Inefficient here. Need to move it outside this function, as only want to do this once.!!!
                trim_name = [elem[0:5] for elem in rocket_data.rocket_name]

                #print(len(ttype), len(trim_rocket_name[0]))

                #if trim_rocket_name[0]==ttype[0:5]:
                #    print('These are the same')
                #sys.exit()
                rocket_found = False
                valid_index = 0
                
                # Loop over 2019 rockets to find matching rocket and associated
                # propellant mass:
                for ll in range(len(trim_name)):
                    #print(ll, ttype)
                    if trim_type == trim_name[ll]:
                        #print('These are the same', ll, rocket_data.booster_prop_mass[ll], rocket_data.stage1_prop_mass[ll], rocket_data.rocket_name[ll])
                        
                        #sys.exit()
                        rocket_found = True
                        valid_index=ll
                        
                        # Get vertical distribution of propellant mass on GEOS-Chem
                        # grid in order from highest to lowest altitude (in kg):
                        self.gc_vert_prop_mass = 1e-2 * self.gc_relative_mass * (rocket_data.booster_prop_mass[ll]+rocket_data.stage1_prop_mass[ll])
                        #print(self.gc_vert_prop_mass)

                        # Error check:
                        if np.abs(sum(self.gc_vert_prop_mass) - (rocket_data.booster_prop_mass[ll]+rocket_data.stage1_prop_mass[ll])) > 0.2:
                            print('Possible issue with vertical distribution of propellant')
                            print('Difference value is: ', np.abs(sum(self.gc_vert_prop_mass) - (rocket_data.booster_prop_mass[ll]+rocket_data.stage1_prop_mass[ll])))
                            sys.exit()

                # Catch any missing rocket propellant masses:
                if rocket_found == False:
                    print('No propellant mass found for ' + trim_type)
                    print('Exiting programme')
                    sys.exit()

                # Next find index of fuel type in primary emissions index data:
                # (1) Boosters:
                pei_booster_index = np.where( rocket_data.pei_fuel_type == rocket_data.booster_prop_type[valid_index] )[0]
                # (2) Stage 1:
                pei_stage1_index = np.where( rocket_data.pei_fuel_type == rocket_data.stage1_prop_type[valid_index] )[0]

                # Apply emission indices:
                # Calculate emission indices of individual pollutants:
                # These are given in g pollutant per kg propellant.
                # Methodology is from https://crp.trb.org/uat/acrp0356/wp-content/uploads/sites/26/2021/07/ACRP-Web-Only-51-Commercial-Space-Vehicle-Emissions-Modeling.pdf

                # (1) Black carbon:
                # Calculate vertical profile of emission indices from highest to
                # lowest altitude:
                self.calculate_bc_ei(self.mid_alt[::-1,q,p]*1e-3)

                # Check fuel types produce BC:
                #print(rocket_data.booster_prop_type[valid_index], rocket_data.stage1_prop_type[valid_index])

                # Check booster produces BC or CO:
                if ( rocket_data.booster_prop_type[valid_index]=='solid' or
                     rocket_data.booster_prop_type[valid_index]=='hypergolic' or
                     rocket_data.booster_prop_type[valid_index]=='kerosene' ) :
                    # Temporary data variable (g BC):
                    t_bc_emis = self.ei_bc * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.bc_total += np.sum(t_bc_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_bc[int(hour[w]),::-1,q,p] += t_bc_emis*1e-3/kg_to_kgm2s
                    
                    # Get vertically resolved CO emission indices (g CO/kg propellant):
                    self.calculate_co_ei(self.mid_alt[::-1,q,p]*1e-3, rocket_data.co_pei[pei_booster_index], rocket_data.co2_pei[pei_booster_index])
                    # Temporary data variable (g CO):
                    t_co_emis = self.ei_co * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.co_total += np.sum(t_co_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_co[int(hour[w]),::-1,q,p] += t_co_emis*1e-3 / kg_to_kgm2s
                
                # Check stage 1 produces BC or CO:
                if ( rocket_data.stage1_prop_type[valid_index]=='solid' or
                     rocket_data.stage1_prop_type[valid_index]=='hypergolic' or
                     rocket_data.stage1_prop_type[valid_index]=='kerosene' ) :
                    # Temporary data variable (g BC):
                    t_bc_emis = self.ei_bc * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.bc_total += np.sum(t_bc_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_bc[int(hour[w]),::-1,q,p] += t_bc_emis*1e-3 / kg_to_kgm2s

                    # Get vertically resolved CO emission indices (g CO):
                    self.calculate_co_ei(self.mid_alt[::-1,q,p]*1e-3, rocket_data.co_pei[pei_stage1_index], rocket_data.co2_pei[pei_stage1_index])
                    # Temporary data variable (g CO):
                    t_co_emis = self.ei_co * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.co_total += np.sum(t_co_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_co[int(hour[w]),::-1,q,p] += t_co_emis*1e-3 / kg_to_kgm2s

                # Sanity check by summing emissions for the year:
                #self.bc_total += np.sum(t_bc_emis)

                # (2) Secondary NOx:
                # Calculate vertical profile of emission indices from highest to
                # lowest altitude:
                self.calculate_secondary_nox_ei(self.mid_alt[::-1,q,p]*1e-3)

                # Temporary data variable (g NO):
                # NOx emissions calculate using the same of booster and stage 1
                # propellant mass calculated earlier:
                t_nox_emis = self.ei_sec_nox * self.gc_vert_prop_mass

                # Apply to final array and convert to kg/m2/s
                self.rocket_nox[int(hour[w]),::-1,q,p] = t_nox_emis*1e-3 / kg_to_kgm2s
                #print(self.rocket_nox[int(hour[w]),:,q,p])

                # Sanity check by summing emissions for the year:
                self.nox_launch_total += np.sum(t_nox_emis)

                # Only Virgin Galactic space plane has primary NOx emissions of 4g/kg.

                # (3) H2O emissions:
                # Use formula:
                # E_f(H2O) = E_p(H2O) + E_P(HO)*MW_H2O/MW_H + E_p(H2)*MW_H2O/MW_H2 + E_p(OH)
                # No H primary emissions, so ignore that term. No OH for almost all rockets, so ignore that term too.
                #print(rocket_data.stage1_prop_type[valid_index])


                # Check whether there is a booster:
                if ( rocket_data.booster_prop_type[valid_index]!='None' ):
                    # Temporary data variable (g H2O):
                    t_h2o_emis = ( rocket_data.h2o_pei[pei_booster_index] + rocket_data.h2_pei[pei_booster_index]*self.mw_h2o / self.mw_h2 ) * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.h2o_total += np.sum(t_h2o_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_h2o[int(hour[w]),::-1,q,p] += t_h2o_emis*1e-3/kg_to_kgm2s
                    #sys.exit()
                
                # Check whether there is a stage 1 rocket:
                if ( rocket_data.stage1_prop_type[valid_index]!='None' ):
                    # Temporary data variable (g H2O):
                    t_h2o_emis = ( rocket_data.h2o_pei[pei_stage1_index] + rocket_data.h2_pei[pei_stage1_index]*self.mw_h2o / self.mw_h2 ) * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.h2o_total += np.sum(t_h2o_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_h2o[int(hour[w]),::-1,q,p] += t_h2o_emis*1e-3 / kg_to_kgm2s

                # (5) Alumina and (6) Chlorine:
                if ( rocket_data.booster_prop_type[valid_index]=='solid' ):
                    
                    # Temporary data variable (g Al2O3):
                    t_al2o3_emis = rocket_data.al2o3_pei[pei_booster_index] * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.al2o3_launch_total += np.sum(t_al2o3_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_al[int(hour[w]),::-1,q,p] += t_al2o3_emis*1e-3/kg_to_kgm2s

                    # Temporary data variable (g Cl):
                    t_cl_emis = rocket_data.cl_pei[pei_booster_index] * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.cl_total += np.sum(t_cl_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_cl[int(hour[w]),::-1,q,p] += t_cl_emis*1e-3/kg_to_kgm2s

                    # Temporary data variable (g HCl):
                    t_hcl_emis = rocket_data.hcl_pei[pei_booster_index] * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.hcl_total += np.sum(t_hcl_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_hcl[int(hour[w]),::-1,q,p] += t_hcl_emis*1e-3/kg_to_kgm2s


                if ( rocket_data.stage1_prop_type[valid_index]=='solid' ):
                    
                    # Temporary data variable (g Al2O3):
                    t_al2o3_emis = rocket_data.al2o3_pei[pei_stage1_index] * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.al2o3_launch_total += np.sum(t_al2o3_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_al[int(hour[w]),::-1,q,p] += t_al2o3_emis*1e-3/kg_to_kgm2s

                    # Temporary data variable (g Cl):
                    t_cl_emis = rocket_data.cl_pei[pei_stage1_index] * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.cl_total += np.sum(t_cl_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_cl[int(hour[w]),::-1,q,p] += t_cl_emis*1e-3/kg_to_kgm2s

                    # Temporary data variable (g HCl):
                    t_hcl_emis = rocket_data.hcl_pei[pei_stage1_index] * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.hcl_total += np.sum(t_hcl_emis)
                    # Apply to final array and convert to kg/m2/s
                    self.rocket_hcl[int(hour[w]),::-1,q,p] += t_hcl_emis*1e-3/kg_to_kgm2s
                    
                #print('BC emis (kg) = ', sum(t_bc_emis)*1e-3)

                # NEXT: UPDATE CODE TO CHECK IF BC IS ACTUALLY PRODUCED
                #       CHECK THAT ACCOUNT FOR ROCKET SERIES IN FINDING PROPELLANT MASS
                
                #sys.exit()


                
                # Apply scale factor (fractional contribution of each vertical grid to the total distance):
                # Double box height at surface to account for additional
                # 3-9 sec that rocket spends on launchpad before launch.
                #self.box_height[0,q,p] *= 2
                #s1_frac = (self.box_height[:,q,p]) / sum(self.box_height[:,q,p])
                #b_frac = (self.box_height[0:self.blev-1,q,p]) / sum(self.box_height[0:self.blev-1,q,p])
                # When there are no boosters:
                #if rocket_data.launch_b_nox[index[w]]==0:
                #    print('No booster emissions')
                #    # Using Ross and Sheaffer vertical distributions:
                #    s1_frac = np.asarray(rocket_data.scale_emis)
                #    b_frac = np.zeros(self.blev-1)
                #    # Error check:
                #    if np.round(np.sum(s1_frac),decimals=2)!=1.00:
                #        print('Error in vertical scaling factors')
                #        print('==== EXITING')
                #        sys.exit()
                        
                # When there are boosters:
                #else:
                #    print('Has booster emissions')
                #    # Scale factors for when there are boosters:
                #    # Using Ross and Sheaffer vertical distributions:
                #    s1_frac = np.asarray(rocket_data.scale_emis) #/ 2
                #    b_ross_prof  = np.asarray(rocket_data.scale_emis[0:self.blev-1])
                #    b_frac = b_ross_prof * (1.0/np.sum(b_ross_prof))
                #    #s1_frac[self.blev-1:] = s1_frac[self.blev-1:]*2
                #    # Error check:
                #    if np.round(np.sum(b_frac),decimals=2)!=1.00 or np.round(np.sum(s1_frac),decimals=2)!=1.00:
                #        print('Error in vertical scaling factors')
                #        print('==== EXITING')
                #        sys.exit()

                #alt=np.zeros(47)
                #i=0
                #for n in self.box_height[:,q,p]:
                #    if i==0:
                #        alt[i]=0
                #    else:
                #        alt[i] = n + alt[i-1]
                #    i = i+1
                #for l in reversed(alt):
                #    print(l*1e-3)
                    
                #print(b_frac)
                #sys.exit()
                # Only get emissions for bottom layer of model for Iranian rocket that
                # exploded before launch:
                #if launch_id[w]=='2019/E01':
                #    s1_frac[:]=0
                #    s1_frac[0]=1.0
                #    b_frac[:]=0
                #    b_frac[0]=1.0
                #    print('Setting launchpad explosion emissions to lowest layer')
                
                # Apply emissions to grid and convert from kg to kg/m2/s:
                #print('BC before scaling  = ',rocket_data.launch_s1_bc[index[w]]+rocket_data.launch_b_bc[index[w]])
                #print('BC after scaling = ', (np.sum(rocket_data.launch_s1_bc[index[w]]*s1_frac) + np.sum(rocket_data.launch_b_bc[index[w]]*b_frac)))
                #sys.exit()
                #self.bc_total += (np.sum(rocket_data.launch_s1_bc[index[w]]*s1_frac) + np.sum(rocket_data.launch_b_bc[index[w]]*b_frac))
                #self.rocket_nox[int(hour[w]),:,q,p] = rocket_data.launch_s1_nox[index[w]]*s1_frac/kg_to_kgm2s
                #self.rocket_nox[int(hour[w]),0:self.blev-1,q,p] = rocket_data.launch_b_nox[index[w]]*b_frac/kg_to_kgm2s
                #self.rocket_h2o[int(hour[w]),:,q,p] = rocket_data.launch_s1_h2o[index[w]]*s1_frac/kg_to_kgm2s
                #self.rocket_h2o[int(hour[w]),0:self.blev-1,q,p] = rocket_data.launch_b_h2o[index[w]]*b_frac/kg_to_kgm2s
                #self.rocket_bc[int(hour[w]),:,q,p] = rocket_data.launch_s1_bc[index[w]]*s1_frac/kg_to_kgm2s
                #self.rocket_bc[int(hour[w]),0:self.blev-1,q,p] = rocket_data.launch_b_bc[index[w]]*b_frac/kg_to_kgm2s
                #self.rocket_al[int(hour[w]),:,q,p] = rocket_data.launch_s1_al[index[w]]*s1_frac/kg_to_kgm2s
                #self.rocket_al[int(hour[w]),0:self.blev-1,q,p] = rocket_data.launch_b_al[index[w]]*b_frac/kg_to_kgm2s
                #self.rocket_hcl[int(hour[w]),:,q,p] = rocket_data.launch_s1_hcl[index[w]]*s1_frac/kg_to_kgm2s
                #self.rocket_hcl[int(hour[w]),0:self.blev-1,q,p] = rocket_data.launch_b_hcl[index[w]]*b_frac/kg_to_kgm2s
                #self.rocket_cl[int(hour[w]),:,q,p] = rocket_data.launch_s1_cl[index[w]]*s1_frac/kg_to_kgm2s
                #self.rocket_cl[int(hour[w]),0:self.blev-1,q,p] = rocket_data.launch_b_cl[index[w]]*b_frac/kg_to_kgm2s

                # Also only represent 8% of alumina mass, as this is the portion
                # that by mass that is estimated to contribute to ozone loss,
                # according to Schmid et al. (2003), https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2002JD002486:
                #self.rocket_al = self.rocket_al*8e-2
                
            # Re-entries (!!!STILL TO UPDATE!!!):
            if emis_type=='reentry':

                # Define temporary ID to get number of characters:
                tmp_id = rocket_data.reentry_id[index[w]]
                #if (tmp_id[0:8]=='2016-001998-010'):
                #    print('Re-entry ID', tmp_id)
                #    print(len(tmp_id))
                    #sys.exit()
                #print(len(tmp_id))
                #sys.exit()
                #tmp_id = (','.join(rocket_data.reentry_id[index[w]]))
                #print(len(tmp_id))

                #if self.rocket_nox[int(hour[w]),self.bot_reenter,q,p]!=0:
                #    print('Data already assigned')
                #    sys.exit()

                # Sum the re-entry emissions, as some of these are close in time (a few seconds apart due to re-entry of multiple rocket stages):
                # (1) NOx:
                # Uncontrolled re-entry of returning debris:
                if not(len(tmp_id)==8 and rocket_data.reentry_type[index[w]]=='N'):
                    #print(rocket_data.reentry_id[index[w]], rocket_data.reentry_type[index[w]])
                    self.nox_reentry_total += rocket_data.reentry_nox[index[w]]
                    self.rocket_nox[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += rocket_data.reentry_nox[index[w]]/self.n_reenter_levs/kg_to_kgm2s
                #self.rocket_nox[int(hour[w]),self.top_reenter,q,p] += rocket_data.reentry_nox[index[w]]/2/kg_to_kgm2s
                # Exception for re-entry that has 8 characters:
                if (tmp_id=='2016-00C'):
                    self.nox_reentry_total += rocket_data.reentry_nox[index[w]]
                    self.rocket_nox[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += rocket_data.reentry_nox[index[w]]/self.n_reenter_levs/kg_to_kgm2s
                
                # (2) Al2O3:
                # Calculate for all non-controlled re-entering objects:
                if (len(tmp_id)>8 and rocket_data.reentry_type[index[w]]=='N'):
                    #print(rocket_data.reentry_id[index[w]], rocket_data.reentry_type[index[w]])
                    tmp_reentry_al = rocket_data.reentry_mass[index[w]]*0.9
                    #print('Al2O3 reentry emis: ', tmp_reentry_al)
                    self.al2o3_reentry_total += tmp_reentry_al
                    # Initially with crude assumption that 90% of returning object is
                    # aluminum and that it is all converted to Al2O3.
                    self.rocket_al[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += tmp_reentry_al/self.n_reenter_levs/kg_to_kgm2s
                # Calculate proportion (17.5%, same as NOx) for all controlled re-entering objects (Soyuz):
                if (len(tmp_id)==9 and rocket_data.reentry_type[index[w]]=='Y'):
                    #print(rocket_data.reentry_id[index[w]], rocket_data.reentry_type[index[w]])
                    tmp_reentry_al = rocket_data.reentry_mass[index[w]]*0.9*0.175
                    print('Al2O3 reentry emis: ', tmp_reentry_al)
                    self.al2o3_reentry_total += tmp_reentry_al
                    # Initially with crude assumption that 90% of returning object is
                    # aluminum and that it is all converted to Al2O3.
                    self.rocket_al[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += tmp_reentry_al/self.n_reenter_levs/kg_to_kgm2s
                # Calculate proportion (17.5%, same as NOx) for Crew Dragon:
                if (tmp_id=='2019-011' and rocket_data.reentry_type[index[w]]=='Y'):
                    print(rocket_data.reentry_id[index[w]], rocket_data.reentry_type[index[w]])
                    tmp_reentry_al = rocket_data.reentry_mass[index[w]]*0.9*0.175
                    print('Al2O3 reentry emis: ', tmp_reentry_al)
                    self.al2o3_reentry_total += tmp_reentry_al
                    # Initially with crude assumption that 90% of returning object is
                    # aluminum and that it is all converted to Al2O3.
                    self.rocket_al[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += tmp_reentry_al/self.n_reenter_levs/kg_to_kgm2s
                # Exception for re-entry that has 8 characters:
                if (tmp_id=='2016-00C'):
                    print(rocket_data.reentry_id[index[w]], rocket_data.reentry_type[index[w]])
                    tmp_reentry_al = rocket_data.reentry_mass[index[w]]*0.9
                    print('Al2O3 reentry emis: ', tmp_reentry_al)
                    self.al2o3_reentry_total += tmp_reentry_al
                    # Initially with crude assumption that 90% of returning object is
                    # aluminum and that it is all converted to Al2O3.
                    self.rocket_al[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += tmp_reentry_al/self.n_reenter_levs/kg_to_kgm2s

                #if (tmp_id=='2016-00C'):
                #    print('Re-entry ID', tmp_id)
                #    print(tmp_reentry_al)
                #    sys.exit()

    def save_netcdf(self):
        """Save rocket emissions as COARDS compliant NetCDF files"""

        # Change (shift) indices on edges of grid:
        if self.pmin==0: self.pmin=1
        if self.pmax==0: self.pmax=1
        if self.pmax==self.nlon: self.pmax=self.nlon-1
        if self.qmin==0: self.qmin=1
        if self.qmax==0: self.qmax=1
        if self.qmin-1==0: self.qmin=1
        if self.qmax==self.nlat: self.qmax=self.nlat-1
        if (self.pmax+2)>=self.nlon:
            print('Longitude index out of bounds: updating')
            if ( self.pmax==self.pmin ):
                self.pmax,self.pmin=self.nlon-2,self.nlon-2
            else:
                self.pmax=self.nlon-2            
            sum_nox=np.sum(self.rocket_nox[:,46,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2])
            if sum_nox==0:
                'Error: lon index correction removes relevant data'

        # Check that output range isn't out-of-bounds:
        if self.qmin-1<0 or self.pmin-1<0:
            print('index is less than 0')
        if self.qmax+1>self.nlat:
            print('lat index exceeds no. of lats')
        if self.pmax+1>self.nlon:
            print('lon index exceeds no. of lons')

        # define dataset:
        ncout = Dataset(self.outfile_rocket_emis, mode='w', format='NETCDF4')

        # Set dimensions (lat, lon, time, lev):
        # Lat and lon data are trimmed.
        ncout.createDimension('lat', self.qmax-self.qmin+3)
        ncout.createDimension('lon', self.pmax-self.pmin+3)
        ncout.createDimension('lev', self.nlev)
        ncout.createDimension('time', self.nhours)

        #print(self.pmin,self.qmin)
        #print(self.lon[self.pmin],self.lat[self.qmin])

        # Create individual variables:
        # Time:
        time = ncout.createVariable('time', np.int64, ('time',))
        time.long_name = 'time'
        time.units = 'hours since 2019-'+self.strmon+'-'+self.strday+' 00:00:00'
        time.calendar = 'standard'
        time.axis = 'T'
        time[:] = np.arange(0,24)

        # Longitude:
        lon = ncout.createVariable('lon', np.float32, ('lon',))
        lon.long_name = 'Longitude'
        lon.units = 'degrees_east'
        lon.axis = 'X'
        lon[:] = self.lon[self.pmin-1:self.pmax+2]
        #print(self.lon[self.pmin-1:self.pmax+2])

        # Latitude:
        lat = ncout.createVariable('lat', np.float32, ('lat',))
        lat.long_name = 'Latitude'
        lat.units = 'degrees_north'
        lat.axis = 'X'
        lat[:] = self.lat[self.qmin-1:self.qmax+2]
        #print(self.lat[self.qmin-1:self.qmax+2])

        # Level:
        lev = ncout.createVariable('lev', np.int64, ('lev',))
        lev.long_name = 'GEOS-Chem level on '+str(self.nlev)+'-layer model grid'
        lev.units = 'level'
        lev.positive = 'up'
        lev.axis = 'Z'
        lev[:] = np.arange(0, self.nlev)+1

        # Emissions:
        # (1) NOx (emitted as NO):
        rocket_nox = ncout.createVariable('rocket_nox', np.float32, ('time','lev','lat','lon',))
        rocket_nox.long_name = 'Rocket NOx emissions emitted as NO'
        rocket_nox.short_name = 'Rocket NOx emissions'
        rocket_nox.units = 'kg/m2/s'
        rocket_nox[:] = self.rocket_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]
        #print(self.rocket_nox[:,46,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2])

        # (2) H2O:
        rocket_h2o = ncout.createVariable('rocket_h2o', np.float32, ('time','lev','lat','lon',))
        rocket_h2o.long_name = 'Rocket H2O emissions'
        rocket_h2o.short_name = 'Rocket H2O emissions'
        rocket_h2o.units = 'kg/m2/s'
        rocket_h2o[:] = self.rocket_h2o[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (3) BC:
        rocket_bc = ncout.createVariable('rocket_bc', np.float32, ('time','lev','lat','lon',))
        rocket_bc.long_name = 'Rocket BC emissions'
        rocket_bc.short_name = 'Rocket BC emissions'
        rocket_bc.units = 'kg/m2/s'
        rocket_bc[:] = self.rocket_bc[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (4) Alumina:
        rocket_al = ncout.createVariable('rocket_al', np.float32, ('time','lev','lat','lon',))
        rocket_al.long_name = 'Rocket alumina emissions'
        rocket_al.short_name = 'Rocket alumina emissions'
        rocket_al.units = 'kg/m2/s'
        rocket_al[:] = self.rocket_al[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (5) HCl:
        rocket_hcl = ncout.createVariable('rocket_hcl', np.float32, ('time','lev','lat','lon',))
        rocket_hcl.long_name = 'Rocket HCl emissions'
        rocket_hcl.short_name = 'Rocket HCl emissions'
        rocket_hcl.units = 'kg/m2/s'
        rocket_hcl[:] = self.rocket_hcl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (6) Cl:
        rocket_cl = ncout.createVariable('rocket_cl', np.float32, ('time','lev','lat','lon',))
        rocket_cl.long_name = 'Rocket Cl emissions'
        rocket_cl.short_name = 'Rocket Cl emissions'
        rocket_cl.units = 'kg/m2/s'
        rocket_cl[:] = self.rocket_cl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (7) CO:
        rocket_co = ncout.createVariable('rocket_co', np.float32, ('time','lev','lat','lon',))
        rocket_co.long_name = 'Rocket CO emissions'
        rocket_co.short_name = 'Rocket CO emissions'
        rocket_co.units = 'kg/m2/s'
        rocket_co[:] = self.rocket_co[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # Close the file:
        ncout.close()

        #self.out_reentry_file

# Main section of the program
if __name__ == "__main__":

    ##########################################################
    # Read the rocket emissions from the database.
    ##########################################################
    
    # Configure additional arguments when running the script.
    # Current options are grid levels and grid resolution.
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", default="47", help="Either 47 or 72")
    parser.add_argument("--grid_res", default = "4x5", help="Can only be 2x2.5 for now")
    args = parser.parse_args()

    # Define rocket emissions data directories:
    datadir = '/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/'
    launch_path = path.join(datadir, 'launches-28Aug2020.nc4')
    reentry_path = path.join(datadir, 'reentries-21Aug2020.nc4')
    outdir = '/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/'    

    # Read rocket emissions:
    rocket_data = RocketData(launch_path, reentry_path)

    ##########################################################
    # Calculate the distribution of rocket emissions and save.
    ##########################################################
    
    ''' Define booster and re-entry levels. '''
    
    # N.B. Boosters only extend to ~45 km (layer 44 of the 47-layer model, layer 57 of the 72-layer model)
    
    # N.B. Re-entry emissions are placed in the GC layer at ~68 km (reentry burnup location).
    # The emissions are evenly distributed across two vertical layers in the model.
    # 46-47 for the 47-layer model, 65-72 for the 72-layer model (equivalent to 60-80 km).
    # This means greater smoothing for the 47-layer model.
    
    levels = int(args.levels)
    if levels==47:
        booster_level = 44
        reentry_levs = [46-1,47-1]    # Convert to python indices
    if levels==72:
        booster_level = 57
        reentry_levs = [65-1,72-1]    # Convert to python indices

    ''' Define resolutions and set timings '''
    
    # Define grid and file resolutions:
    grid_res = args.grid_res
    if grid_res == '2x2.5': 
        #file_res = '2x25'
        timestep = 1800 #sec
    if grid_res == '4x5':
        #file_res = '4x5'   
        timestep = 3600 #sec
    
    # file_res no longer used??
    
    # Months and days are set within the OutputEmis class, could change this.
    # Define month:
    #monnum = args.month
    #print(monnum)

    # Define no. of days in month:
    ndays = 31

    ''' Define locations of StateMet files '''
    
    #Define paths dependent on resolution and levels.
    if grid_res == '4x5':
        if levels == 72:
            gcdir = '/home/ucfacb0/uptrop/GC/run_12.9.3_72L/methane_fluxes/merra2_4x5_og/StateMet/'
        if levels == 47:
            gcdir = ''
    if grid_res == '2x2.5':
        if levels == 72:
            gcdir = '/home/ucfacb0/uptrop/GC/run_12.9.3_72L/methane_fluxes/merra2_2x25_og/StateMet'
        if levels == 47:
            gcdir = ''

        
    # Go through process of gridding and saving rocket emissions:
    emis_data = OutputEmis(rocket_data, grid_res, timestep, levels, booster_level, reentry_levs, gcdir)
    
    ##########################################################
    # Print total emissions of each species.
    ##########################################################
    
    print('Total BC emissions (tonnes): ', emis_data.bc_total*1e-6)
    print('Total NOx launch emissions (tonnes): ', emis_data.nox_launch_total*1e-6)
    print('Total H2O emissions (tonnes): ', emis_data.h2o_total*1e-6)
    print('Total CO emissions (tonnes): ', emis_data.co_total*1e-6)
    print('Total Al2O3 launch emissions (tonnes): ', emis_data.al2o3_launch_total*1e-6)
    print('Total Cl emissions (tonnes): ', emis_data.cl_total*1e-6)
    print('Total HCl emissions (tonnes): ', emis_data.hcl_total*1e-6)
    print('Total NOx re-entry emissions (tonnes): ', emis_data.nox_reentry_total*1e-3)
    print('Total Al2O3 re-entry emissions (tonnes): ', emis_data.al2o3_reentry_total*1e-6)

    # Notes:
    # (1) not sure is zero or letter 'o' in Blok-DM-03
    # (2) check SI to determine Hyperbola, Jielong-1, Kuaizhou-1A propellant mass.
    # (3) Same propellant mass, different names: Proton-M, Soyuz, Ariane, CZ-3B, Anatres-230,
    #     
    #
    # rocket_id        = ['CZ-3B/G',    'Falcon-9 v1.2 (Block 5)', 'Simorgh',
    #                     'Epsilon (2) CLPA', 'Delta-4H (upg.)', 'CZ-11', 'PSLV-DL',
    #                     'Ariane-5ECA', 'Safir-1B', 'Soyuz', 'Delta-4M+(5,4) (upg.)',
    #                     'Vega', 'Electron KS', 'PSLV-QL',   'Falcon-Heavy (Block 5)',
    #                     'Antares-230', 'CZ-4B', 'CZ-3C/G2',  'PSLV-CA', 'CZ-4C',
    #                     'Proton-M', 'GSLV Mk.3 (2)', 'Hyperbola-1 (Shian Quxian-1)',
    #                     'CZ-2C (3)', 'Atlas-5(551)', 'Jielong-1', 'Delta-4M+(4,2) (upg.)',
    #                     'Rokot-KM', 'Kuaizhou-1A', 'H-2B-304',    'CZ-2D (2)', 'Pegasus-XL',
    #                     'CZ-6', 'PSLV-XL',    'Atlas-5(N22)', 'CZ-5']
    # Sum of booster(s) and first stage (kg):
    # rocket_prop_mass = [164400+186200, 418700,                    50000,
    #                     66000,              408000+204000,      35000,  24000+138000,
    #                     480000+175000, 18200+3050, 158400,   118800+204000,
    #                     88365,  9250,          48000+138000, 815200+407600,
    #                     242000,        183200,  82200+186200, 138000,   183200,
    #                     428300,                413380+115000,     20100,
    #                     143000,      213150+284090, 15500,        59400+204000,
    #                     71450,      15000,        264000+177800, 183200,      15010,
    #                     76000,  72000+138000, 85260+284090,   608000+158000]
