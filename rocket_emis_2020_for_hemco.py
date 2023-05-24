#!/usr/bin/python

'''Save out rocket emissions as COARDS compliant files for input to 
   HEMCO/GEOS-Chem.

   NOTE: still need to replace with updated emissions from Chloe.
   '''

# Import relevant packages:
import argparse
import sys
import os
from os import path
from netCDF4 import Dataset
import numpy as np

#sys.path.append('/home/ucfacb0/python/packages/GCPy')
#from gcpy.grid import make_grid_LL

class RocketData:
    '''Read rocket launch and re-entry emissions'''
    def __init__(self,launchfile,reentryfile, rocketinfofile):
        
        self.read_launch_emissions(launchfile)
        self.read_reentry_emissions(reentryfile)
        self.define_scale_factors()
        self.read_rocket_info(rocketinfofile)
    
    def read_launch_emissions(self, launchfile):
        ###########################################
        # Read launch emissions from the database.
        ###########################################
        
        #Open Dataset.
        fh = Dataset(launchfile, mode='r')
        
        #TODO: Why do we load in the launch emissions? Surely this is the output??
        # Have removed for now.
        
        #Extract variables.
        self.launch_lons = fh.variables['Longitude'][:]
        self.launch_lats = fh.variables['Latitude'][:]
        self.launch_time = fh.variables['Time(UTC)'][:]  # UTC hours
        self.launch_month = fh.variables['Month'][:]
        self.launch_day = fh.variables['Day'][:]
        self.launch_id = fh.variables['COSPAR_ID'][:]
        self.rocket_type = fh.variables['Rocket_Type'][:]
        
        print("Successfully loaded launch information.")
        
        # These are used for a monthly nox emissions check later.
        #self.launch_b_nox = fh.variables['Boosters NOx'][:]
        #self.launch_s1_nox = fh.variables['Stage 1 NOx'][:]
        
        # All of these are used in:
        #       1) Sanity check below
        #       2) Now commented out code for launches in grid_emis
        #self.launch_b_h2o = fh.variables['Boosters H2O'][:]
        #self.launch_b_bc = fh.variables['Boosters BC'][:]
        #self.launch_b_al = fh.variables['Boosters Alumina'][:]
        #self.launch_b_hcl = fh.variables['Boosters HCl'][:]
        #self.launch_b_cl = fh.variables['Boosters Cl'][:]
        #self.launch_s1_h2o = fh.variables['Stage 1 H2O'][:]
        #self.launch_s1_bc = fh.variables['Stage 1 BC'][:]
        #self.launch_s1_al = fh.variables['Stage 1 Alumina'][:]
        #self.launch_s1_hcl = fh.variables['Stage 1 HCl'][:]
        #self.launch_s1_cl = fh.variables['Stage 1 Cl'][:]
        
        #All of these are only used for the sanity check below.
        #self.launch_t_nox = fh.variables['Total NOx'][:]
        #self.launch_t_h2o = fh.variables['Total H2O'][:]
        #self.launch_t_bc = fh.variables['Total BC'][:]
        #self.launch_t_al = fh.variables['Total Alumina'][:]
        #self.launch_t_hcl = fh.variables['Total HCl'][:]
        #self.launch_t_cl = fh.variables['Total Cl'][:]
        
        #Close Dataset.
        fh.close()

        # TODO: Sanity Check
        if args.verbose == True:
            pass
            #Print total emissions for each species.
            #print(f'Total booster + stage 1 NOx emissions   = {sum(self.launch_s1_nox+self.launch_b_nox)*1e-3:.4f} tonnes')
            #print(f'Total booster + stage 1 H2O emissions   = {sum(self.launch_s1_h2o+self.launch_b_h2o)*1e-3:.4f} tonnes')
            #print(f'Total booster + stage 1 BC emissions    = {sum(self.launch_s1_bc+self.launch_b_bc)*1e-3:.4f} tonnes')
            #print(f'Total booster + stage 1 Al2O3 emissions = {sum(self.launch_s1_al+self.launch_b_al)*1e-3:.4f} tonnes')
            #print(f'Total booster + stage 1 HCl emissions   = {sum(self.launch_s1_hcl+self.launch_b_hcl)*1e-3:.4f} tonnes')
            #print(f'Total booster + stage 1 Cl emissions    = {sum(self.launch_s1_cl+self.launch_b_cl)*1e-3:.4f} tonnes')
            
            #Use this to check totals after database is complete.
            #print(f'Total Check (NOx)                       = {(sum(self.launch_s1_nox+self.launch_b_nox)-sum(self.launch_t_nox))*1e-3} tonnes')
            #print(f'Total Check (H2O)                       = {(sum(self.launch_s1_h2o+self.launch_b_h2o)-sum(self.launch_t_h2o))*1e-3} tonnes')
            #print(f'Total Check (BC)                        = {(sum(self.launch_s1_bc+self.launch_b_bc)-sum(self.launch_t_bc))*1e-3} tonnes')
            #print(f'Total Check (Al2O3)                     = {(sum(self.launch_s1_al+self.launch_b_al)-sum(self.launch_t_al))*1e-3} tonnes')
            #print(f'Total Check (HCl)                       = {(sum(self.launch_s1_hcl+self.launch_b_hcl)-sum(self.launch_t_hcl))*1e-3} tonnes')
            #print(f'Total Check (Cl)                        = {(sum(self.launch_s1_cl+self.launch_b_cl)-sum(self.launch_t_cl))*1e-3} tonnes')
        
    def read_reentry_emissions(self, reentryfile):
        ############################################
        # Read re-entry emissions from the database.
        ############################################

        #Open Dataset
        fg = Dataset(reentryfile, mode='r')
        
        # Extract variables:
        self.reentry_id = fg.variables['ID'][:]
        self.reentry_type = fg.variables['Controlled?'][:]
        self.reentry_lons = fg.variables['Longitude'][:]
        self.reentry_lats = fg.variables['Latitude'][:]
        self.reentry_time = fg.variables['Time (UTC)'][:]   # UTC hours
        self.reentry_month = fg.variables['Month'][:]
        self.reentry_day = fg.variables['Day'][:]
        self.reentry_mass = fg.variables['Total Mass'][:]
        self.reentry_nox = fg.variables['NOx from re-entry'][:]  # in tonnes
        self.reentry_booster_mass = fg.variables['Booster mass'][:]
        self.reentry_stage1_mass = fg.variables['First stage mass'][:]
        self.reentry_stage2_mass = fg.variables['Second stage mass'][:]
        
        #Close Dataset.
        fg.close()
        
        # TODO: Sanity Check
        if args.verbose == True:
            print(f'Total reentry NOx emissions             = {sum(self.reentry_nox)*1e-3} tonnes')
        
        # TODO: Reentries - Need to sort out controlled vs uncontrolled entries.
        # ID String with length of 8 is from rocket launch and should be ignored if not a controlled entry.
        # Something like:
        #           if len(ID)==8 and Controlled=='Y', then calculate 0.175*mass to get NOx
        #           if len(ID)==8 and Controlled=='Y', then don't calculate re-entry NOx.
        
        
        # Can use this to check the totals after database is complete.
        # However, the input file contains lots of empty data for the booster, stage 1 and stage 2 mass. 
        # Therefore the total from all three is very different from the total mass.
        if args.verbose == True:
            print(f'Total Reentry Check (NOx)               = {(np.nansum(self.reentry_booster_mass+self.reentry_stage1_mass+self.reentry_stage2_mass)-sum(self.reentry_mass))*1e-3} tonnes')
            
    def define_scale_factors(self):
        ###############################################################################
        # Create vertical fuel burned scale factors for the 47-layer GEOS-Chem model:
        ###############################################################################
        
        # Scale factors obtained by regridding vertical profile from Ross and Sheaffer (2014) to the GEOS-Chem vertical grid.
        # https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013EF000160
        # TODO: Pretty sure this isn't used anymore
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
        
    def read_rocket_info(self, rocketinfofile):
        ##########################################################
        # Read propellant mass per rocket type from the database.
        ##########################################################

        #TODO: Probably need a sanity check here, and also a lot of these are probably not used anymore.
        
        # Open Dataset.
        #rocketinfofile = './Databases/Old/rocket_type_propellant_mass_2019_database.nc'
        fh = Dataset(rocketinfofile, mode='r')
        
        # Extract variables:
        self.rocket_name = fh.variables['Rocket_Name'][:]
        self.stage1_prop_mass  = fh.variables['Stage1_PropMass'][:]
        self.stage1_solid      = fh.variables['Stage1_Solid'][:]
        self.stage1_prop_name  = fh.variables['Stage1_PropName'][:]
        self.stage2_prop_mass  = fh.variables['Stage2_PropMass'][:]
        self.stage2_solid      = fh.variables['Stage2_Solid'][:]
        self.stage2_prop_name  = fh.variables['Stage2_PropName'][:]
        self.stage3_prop_mass  = fh.variables['Stage3_PropMass'][:]
        self.stage3_solid      = fh.variables['Stage3_Solid'][:]
        self.stage3_prop_name  = fh.variables['Stage3_PropName'][:]
        self.stage4_prop_mass  = fh.variables['Stage4_PropMass'][:]
        self.stage4_solid      = fh.variables['Stage4_Solid'][:]
        self.stage4_prop_name  = fh.variables['Stage4_PropName'][:]
        self.stage5_prop_mass  = fh.variables['Stage5_PropMass'][:]
        self.stage5_solid      = fh.variables['Stage5_Solid'][:]
        self.stage5_prop_name  = fh.variables['Stage5_PropName'][:]
        
        #Old variables
        #self.rocket_name       = fh.variables['2019_rocket_name'][:]
        #self.booster_prop_mass = fh.variables['booster_prop_mass'][:]
        #self.stage1_prop_mass  = fh.variables['stage1_prop_mass'][:]
        #self.booster_prop_type = fh.variables['booster_prop_type'][:]
        #self.stage1_prop_type  = fh.variables['stage1_prop_type'][:]
        #self.pei_fuel_type     = fh.variables['fuel_type_for_pei'][:]
        #self.h2_pei            = fh.variables['h2_pei'][:]
        #self.h2o_pei           = fh.variables['h2o_pei'][:]
        #self.cl_pei            = fh.variables['cl_pei'][:]
        #self.hcl_pei           = fh.variables['hcl_pei'][:]
        #self.al2o3_pei         = fh.variables['al2o3_pei'][:]
        #self.bc_pei            = fh.variables['bc_pei'][:]
        #self.co_pei            = fh.variables['co_pei'][:]
        #self.co2_pei           = fh.variables['co2_pei'][:]
        # Close Dataset.
        fh.close()
        
        print("Successfully loaded rocket information.")
        
class OutputEmis:
    def __init__(self, rocketdata, res, ts, levs, blev, reentry_levs, gc_dir, months):

        ####################################
        # Initial Setup
        ####################################
        
        # Setup input variables.
        self.launch_id = rocketdata.launch_id # Extract launch IDs from the imported rocket data.
        self.ts = ts
        self.nlev = levs
        self.blev = blev
        self.bot_reenter = min(reentry_levs)
        self.top_reenter = max(reentry_levs)
        self.n_reenter_levs = self.top_reenter - self.bot_reenter + 1
        self.nhours = 24
        
        # Define Molecular Weights:
        self.mw_h = 1.008
        self.mw_h2 = self.mw_h * 2
        self.mw_h2o = self.mw_h2 + 16.00

        # Get Ross vertical profiles of propellant burned:
        #   self.ross_alt (centre alitiudes of each bin)
        #   self.ross_prop_mass (unitless percent of propellant mass)
        self.get_ross_profiles()

        # Create variables for totals for a future sanity check:
        self.nox_launch_total = 0.0
        self.bc_total  = 0.0
        self.h2o_total = 0.0
        self.co_total = 0.0
        self.al2o3_launch_total = 0.0
        self.cl_total = 0.0
        self.hcl_total = 0.0
        self.nox_reentry_total = 0.0
        self.al2o3_reentry_total = 0.0

        # Make grid at input resolution (no bounds supplied so full global).
        # Can use this with different in and out edges.
        grid = self.make_grid_LL(res)  
        #Extract useful variables from the grid.    
        self.nlon = len(grid['lon'])
        self.nlat = len(grid['lat'])
        self.lon =  grid['lon']
        self.lat =  grid['lat']
        
        #Creat 2D lat and lon grid.
        #X, Y = np.meshgrid(self.lon, self.lat,indexing='ij')
        #self.lon2d = X
        #self.lat2d = Y
        
        # Trim the rocket names in the propellant mass database:
        # TODO: Why do we trim? I guess duplicates don't matter? 
        self.trim_name = [elem[0:5] for elem in rocket_data.rocket_name]

        #################################
        # Loop over each day and month.
        #################################
        
        for m in months:
            
            #Setup days in month
            if m in [0,2,4,6,7,9,11]:
                ndays = 31
            elif m in [3,5,8,10]:
                ndays = 30
            elif m == 1:
                ndays = 29
            else:
                sys.exit("Invalid month selected.")
                
            #ndays = 1
                        
            #month_emis=0.0

            # Get month string:
            if m+1<=9:
                self.strmon='0'+str(m+1)
            else:
                self.strmon=str(m+1)

            print('Month processing: ', self.strmon)             
            
            # Loop over days:
            for d in range(ndays):

                # Get day string:
                if d+1<=9:
                    self.strday='0'+str(d+1)
                else:
                    self.strday=str(d+1)

                # gc_dir is defined for each scenario in the main section of the python script.
                # So only need one block to read GEOS-Chem box height from StateMet file.
                self.gc_file = path.join(gc_dir, 'GEOSChem.StateMet.2020'+self.strmon+self.strday+'_0000z.nc4')

                file_exists = os.path.exists(self.gc_file)
                if not file_exists: continue
                self.read_gc_box_height()

                # Set up the data arrays which will be saved to file.
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
                self.outfile_rocket_emis = path.join(outdir,self.strmon,f'ROCKET_EMIS_{res}_{str(self.nlev)}L_2020{self.strmon}{self.strday}.nc4')
                #print(f'Output to: {self.outfile_rocket_emis}')
                
                ########################################################################
                # Call grid_emis function to calculate distribution from launches
                ########################################################################
                
                l_ind=np.where((rocket_data.launch_month==(m+1))&(rocket_data.launch_day==(d+1))&(~np.isnan(rocket_data.launch_time)))[0]
                
                print(f"Num launches is {len(l_ind)}")
                if len(l_ind)>0:
                    self.grid_emis(l_ind,
                                   rocket_data.launch_lons[l_ind],
                                   rocket_data.launch_lats[l_ind],
                                   rocket_data.launch_time[l_ind],
                                   'launch',
                                   rocket_data.launch_id[l_ind],
                                   rocket_data.rocket_type[l_ind]
                                   )
                    
                    #TODO: Why are we only adding NOx to the monthly emission total?
                    #month_emis += sum(rocket_data.launch_s1_nox[l_ind]+rocket_data.launch_b_nox[l_ind])*1e-3

                ########################################################################
                # Call grid_emis function to calculate distribution from re-entries
                ########################################################################
                
                r_ind=np.where((rocket_data.reentry_month==(m+1))&(rocket_data.reentry_day==(d+1)))[0]
                
                # This code is used to skip any non-controlled re-entry of immediately launched
                # rocket, as this was an error in the original inventory. Might not be necessary for 
                # future fixed inventories.
                #if len(r_ind)>0:
                #    tmp_id = (','.join(rocket_data.reentry_id[r_ind]))
                #if (len(tmp_id)==8 and rocket_data.reentry_type[r_ind]=='N'):
                #    r_ind=[]
                
                if len(r_ind)>0:
                    self.grid_emis(r_ind,
                                   rocket_data.reentry_lons[r_ind],
                                   rocket_data.reentry_lats[r_ind],
                                   rocket_data.reentry_time[r_ind],
                                   'reentry',
                                   ' ',
                                   ' '
                                   )
                    
                    # Sum up all re-entry NOx (kg):
                    #self.nox_reentry_total += sum(rocket_data.reentry_nox[r_ind])

                ####################################
                # Save file as NetCDF
                ####################################
                
                if  len(l_ind)>0 or len(r_ind)>0:
                    self.save_netcdf()
                else:

                    # Create dummy file to accommodate HEMCO file reading
                    # Settings:
                    
                    #lat_ind=np.where(self.lat==0)[0]
                    #lon_ind=np.where(self.lon==0)
                    #if len(lat_ind)==0:
                    
                    lat_ind=np.argmin(abs(self.lat-0))
                    self.qmin,self.qmax=int(lat_ind),int(lat_ind)
                    lon_ind=np.argmin(abs(self.lon-0))
                    self.pmin,self.pmax=int(lon_ind),int(lon_ind)
                    
                    self.save_netcdf()
                    
            #TODO: Sanity Check
            #print('Monthly NOx launch emissions (tonnes): ',month_emis)
            
    def make_grid_LL(self, llres, in_extent=[-180, 180, -90, 90], out_extent=[]):
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

    def read_gc_box_height(self):
        ''' This function reads GEOS-Chem box height from StateMet files. '''
        
        #Open Dataset.
        fk = Dataset(self.gc_file, mod='r')
        self.box_height = fk.variables['Met_BXHEIGHT'][:]
        self.box_height = self.box_height[0,:,:,:]
        self.area = fk.variables['AREA'][:]

        fk.close()

        # Calculate the top, mid, and bottom altitudes of each box.
        # Only the middle altitude is actually used elsewhere.
        self.top_alt = np.zeros_like(self.box_height)
        self.bot_alt = np.zeros_like(self.box_height)
        self.mid_alt = np.zeros_like(self.box_height)
        for l in range(self.nlev):
            if l==0:
                self.top_alt[l,:,:] = self.box_height[l,:,:]
                self.mid_alt[l,:,:] = 0.5*np.add(self.bot_alt[l,:,:], self.top_alt[l,:,:])
                continue
            self.bot_alt[l,:,:] = self.top_alt[l-1,:,:]
            self.top_alt[l,:,:] = np.add(self.top_alt[l-1,:,:], self.box_height[l-1,:,:])
            self.mid_alt[l,:,:] = 0.5*np.add(self.bot_alt[l,:,:], self.top_alt[l,:,:])

    def calculate_bc_ei(self, height):
        """Calculate black carbon vertical emission indices on the GEOS-Chem
           grid in g BC per kg propellant burned"""
        self.ei_bc = np.zeros_like(height)
        
        for i, h in enumerate(height):
            self.ei_bc[i] = 25 * (max(0.04, (min(1, (0.04*(np.exp(0.12*(h-15))))))))

        ## TODO: NEED TO CHANGE 25 TO 5 IN ABOVE EQUATION WHEN ALSO INCLUDE ROCKETS IN
        ##         FUTURE INVENTORY THAT USE LIQUID METHANE FUEL

    def calculate_secondary_nox_ei(self, height):
        """Calculate secondary NOx emission index from high-temperature rocket plume 
           in g NO per kg propellant burned. Applies to all rockets"""
        self.ei_sec_nox = np.zeros_like(height)

        for i, h in enumerate(height):
            self.ei_sec_nox[i] = 33 * np.exp((-0.26)*h)

        ## TODO: STILL NEED TO CALCULATE PRIMARY NOx FOR ROCKETS WITH N-BASED FUEL

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
           Input  (i) and  (j) 
           
           GEOS-Chem grids are ordered [alt, lat, lon].

        Args:
            i (numpy.int64): longitude index of model gridbox where launch occurs.
            j (numpy.int64): latitude index of model gridbox where launch occurs.
        """        

        # y = y1 + ((x – x1) / (x2 – x1)) * (y2 – y1)
        
        # Define array of percent distribution of propellant mass on GEOS-Chem grid:
        # This sets up an array over number of GEOS-Chem levels (47 or 72).
        gc_relative_mass = np.zeros_like(self.mid_alt[:,j,i])

        # Loop over GEOS-Chem layers in reverse:
        for l, h in enumerate(reversed(self.mid_alt[:,j,i])):

            # Find Ross profile layer closest to centre altitude of GEOS-Chem grid:
            ross_ind = np.argmin(np.abs(h*1e-3 - self.ross_alt))

            # Interpolate:
            gc_relative_mass[l] = self.ross_prop_mass[ross_ind-1] + ((h*1e-3 - self.ross_alt[ross_ind-1]) /
                                                 (self.ross_alt[ross_ind] - self.ross_alt[ross_ind-1])) * (self.ross_prop_mass[ross_ind] - self.ross_prop_mass[ross_ind-1])

        # Find Ross altitude closest to altitude
        #print(gc_relative_mass)
        #print(self.mid_alt[:-1,j,i])
        #print(j,i)
        #sys.exit()

        # Normalize so that adds to 100%:
        self.gc_relative_mass = 1e2 * gc_relative_mass / np.sum(gc_relative_mass)

    def grid_emis(self,index,lon,lat,hour,emis_type,launch_id,rocket_type):
        """Grid the data onto the GEOS-Chem horizontal and vertical grid"""

        #Loop over each launch/reentry.
        for w in range(len(lon)):
            
            ################
            # Setup grid.
            ################
            # Get grid horizontal indices (p is lon index; q is lat index).
            # This works out the nearest latitude and longitude on the grid.
            p,q = np.argmin(abs(lon[w]-self.lon)), np.argmin(abs(lat[w]-self.lat))
            
            # Usually, any reentries from launches are placed at the same lat/lon as the launch itself.
            # This code is only used where a non launch related reentry occurs on the same day as a launch.
            # It updates the grid range (lat and lon edges) to account for the new location and to prepare for saving to file:
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
            
            #########################################################
            # Work out vertical distribution for launch emissions.
            #########################################################

            if emis_type=='launch':
                
                #######################
                # Skip Failed Launches
                #######################
                
                # For all failed launches, DISCOSweb does not include objects.
                
                # For 2019, these include all labelled "F" except F04 that failed at stage 3:
                # List of 2020 Failed Launches
                
                    # F01 - 09/02/2020 Simorgh (Iran) - 2 stage rocket
                    # First stage operated correctly, but second stage failed to deploy payload succesfully.
                    # Satellite reached 540 km apogee but only reached 6,400 m/s, so short of 7,400 m/s orbital velocity.
 
                    # F02 - 16/03/2020 Long March 7A (China) - 3 stages, 4 boosters?
                    # Limited information about what happened on this failed launch. 
                    # SLR: Failure just after S2 start.
                    # Wiki: Vehicle disintegrated at first stage separation due to booster LOX pressurization failure leading to engine shutdown and loss of control.
                    
                    # F03 - 09/04/2020 Long March 3B/E (China)
                    # Wiki/SLR: Third stage engine failed to ignite. Failed to put satellite in orbit.
                    
                    # F04 - 25/05/2020 LauncherOne ()
                    # F05 - 04/07/2020 Electron (Curie) ()
                    # F06 - 10/07/2020 Kuaizhou-11 ()
                    # F07 - 12/09/2020 Astra Rocket 3 ()
                    # F08 - 12/09/2020 Kuaizhou-11 ()
                    # F09 - 17/11/2020 Vega ()
                    # F10 - 15/12/2020 Astra Rocket 3 ()
                    # F11 - 03/12/2020 Chang'e 5 SSQ (Ascent Stage)
                

                #For now, exclude all failed launches. # TODO: Go through each failed launch and decide which emissions to include in final inventory. 
                if launch_id[w][-3:-2] == 'F':
                    print(f'Launch {launch_id[w]} failed. Not processing.')
                    continue
                
                ############################################
                # Interpolate propellant mass distribution.
                ############################################

                # Linearly interpolate Ross profile proportion of propellant
                # mass to GEOS-Chem vertical grid:
                # Dataset of interest from this is self.gc_prop_mass
                self.interp_prop_mass(p, q)
                
                ############################################
                # Check the rocket type 
                ############################################

                # Setup rocket type variables (trim_name contains all rockets and is defined in __init__ function of this class):
                # TODO: Isn't this section mixing up rockets with the same name? It only uses the final rocket that it finds.
                # Why do we even trim the rocket names at all??
                trim_type = rocket_type[w][0:5]
                rocket_found = False
                valid_index = 0
                
                # Loop over 2019 rockets to find matching rocket and associated propellant mass:
                for ll in range(len(self.trim_name)):
                    #print(ll, ttype)
                    if trim_type == self.trim_name[ll]:
                        rocket_found = True
                        valid_index=ll
                        
                        # Get vertical distribution of propellant mass on GEOS-Chem
                        # grid in order from highest to lowest altitude (in kg):
                        self.gc_vert_prop_mass = 1e-2 * self.gc_relative_mass * (rocket_data.booster_prop_mass[ll]+rocket_data.stage1_prop_mass[ll])

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
                
                ##########################################################
                # Apply emission indices:
                # Calculate emission indices of individual pollutants:
                # These are given in g pollutant per kg propellant.
                # Methodology is from https://crp.trb.org/uat/acrp0356/wp-content/uploads/sites/26/2021/07/ACRP-Web-Only-51-Commercial-Space-Vehicle-Emissions-Modeling.pdf
                # General structure is this for each species:
                #       0) Check if species is emitted
                #       1) calculate vertical profile of emission indices (g(xx) / kg(propellant)) using function self.calculate_xx_ei
                #       2) multiply propellant mass by (0.01 * ei * vertical mass profile) to get mass vertical profile (in g)
                #       3) add vertical mass profile (in g) to sanity check total
                #       3) convert vertical mass profile from kg to kgm2s and add to output variable
                ##########################################################
                
                ###########################
                # (1) BC and (2) CO
                ###########################
                
                # TODO: Update these to reflect changes in fuel types (e.g. liq. methane)
                
                # Check if booster produces BC or CO:
                if rocket_data.booster_prop_type[valid_index] in ['solid','hypergolic','kerosene']:

                    self.calculate_bc_ei(self.mid_alt[::-1,q,p]*1e-3)
                    t_bc_emis = self.ei_bc * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.bc_total += np.sum(t_bc_emis)
                    self.rocket_bc[int(hour[w]),::-1,q,p] += t_bc_emis * 1e-3/kg_to_kgm2s
                    
                    self.calculate_co_ei(self.mid_alt[::-1,q,p]*1e-3, rocket_data.co_pei[pei_booster_index], rocket_data.co2_pei[pei_booster_index])
                    t_co_emis = self.ei_co * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.co_total += np.sum(t_co_emis)
                    self.rocket_co[int(hour[w]),::-1,q,p] += t_co_emis * 1e-3 / kg_to_kgm2s

                # Check if stage 1 produces BC or CO:
                if rocket_data.stage1_prop_type[valid_index] in ['solid','hypergolic','kerosene']:
                    
                    self.calculate_bc_ei(self.mid_alt[::-1,q,p]*1e-3)
                    t_bc_emis = self.ei_bc * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.bc_total += np.sum(t_bc_emis)
                    self.rocket_bc[int(hour[w]),::-1,q,p] += t_bc_emis*1e-3 / kg_to_kgm2s

                    self.calculate_co_ei(self.mid_alt[::-1,q,p]*1e-3, rocket_data.co_pei[pei_stage1_index], rocket_data.co2_pei[pei_stage1_index])
                    t_co_emis = self.ei_co * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.co_total += np.sum(t_co_emis)
                    self.rocket_co[int(hour[w]),::-1,q,p] += t_co_emis*1e-3 / kg_to_kgm2s

                ###########################
                # (3) Secondary NOx:
                ###########################
                
                # Every launch.
                # Only Virgin Galactic space plane has primary NOx emissions of 4g/kg.
                # NOx emissions calculate using the same of booster and stage 1 propellant mass calculated earlier.
                
                self.calculate_secondary_nox_ei(self.mid_alt[::-1,q,p]*1e-3)
                t_nox_emis = self.ei_sec_nox * self.gc_vert_prop_mass
                self.nox_launch_total += np.sum(t_nox_emis)
                self.rocket_nox[int(hour[w]),::-1,q,p] = t_nox_emis*1e-3 / kg_to_kgm2s
                
                ###########################
                # (4) H2O emissions:
                ###########################

                # Use formula:
                # E_f(H2O) = E_p(H2O) + E_P(HO)*MW_H2O/MW_H + E_p(H2)*MW_H2O/MW_H2 + E_p(OH)
                # No H primary emissions, so ignore that term. No OH for almost all rockets, so ignore that term too.

                # Check whether there is a booster:
                if ( rocket_data.booster_prop_type[valid_index]!='None' ):
                    
                    self.ei_h2o =  rocket_data.h2o_pei[pei_booster_index] + rocket_data.h2_pei[pei_booster_index] * self.mw_h2o / self.mw_h2 
                    t_h2o_emis = self.ei_h2o * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.h2o_total += np.sum(t_h2o_emis)
                    self.rocket_h2o[int(hour[w]),::-1,q,p] += t_h2o_emis*1e-3/kg_to_kgm2s
                
                # Check whether there is a stage 1 rocket:
                if ( rocket_data.stage1_prop_type[valid_index]!='None' ):
                    
                    self.ei_h2o =  rocket_data.h2o_pei[pei_stage1_index] + rocket_data.h2_pei[pei_stage1_index] * self.mw_h2o / self.mw_h2 
                    t_h2o_emis = self.ei_h2o * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.h2o_total += np.sum(t_h2o_emis)
                    self.rocket_h2o[int(hour[w]),::-1,q,p] += t_h2o_emis*1e-3 / kg_to_kgm2s
                
                ###########################
                # (5) Alumina and (6) Chlorine:
                ###########################
                
                # Check if booster produces Al2O3, HCl or Cl:
                if ( rocket_data.booster_prop_type[valid_index]=='solid' ):
                    
                    t_al2o3_emis = rocket_data.al2o3_pei[pei_booster_index] * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.al2o3_launch_total += np.sum(t_al2o3_emis)
                    self.rocket_al[int(hour[w]),::-1,q,p] += t_al2o3_emis*1e-3/kg_to_kgm2s

                    t_cl_emis = rocket_data.cl_pei[pei_booster_index] * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.cl_total += np.sum(t_cl_emis)
                    self.rocket_cl[int(hour[w]),::-1,q,p] += t_cl_emis*1e-3/kg_to_kgm2s

                    t_hcl_emis = rocket_data.hcl_pei[pei_booster_index] * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.hcl_total += np.sum(t_hcl_emis)
                    self.rocket_hcl[int(hour[w]),::-1,q,p] += t_hcl_emis*1e-3/kg_to_kgm2s

                # Check if stage 1 produces Al2O3, HCl or Cl:
                if ( rocket_data.stage1_prop_type[valid_index]=='solid' ):
                    
                    t_al2o3_emis = rocket_data.al2o3_pei[pei_stage1_index] * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.al2o3_launch_total += np.sum(t_al2o3_emis)
                    self.rocket_al[int(hour[w]),::-1,q,p] += t_al2o3_emis*1e-3/kg_to_kgm2s

                    t_cl_emis = rocket_data.cl_pei[pei_stage1_index] * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.cl_total += np.sum(t_cl_emis)
                    self.rocket_cl[int(hour[w]),::-1,q,p] += t_cl_emis*1e-3/kg_to_kgm2s

                    t_hcl_emis = rocket_data.hcl_pei[pei_stage1_index] * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass
                    self.hcl_total += np.sum(t_hcl_emis)
                    self.rocket_hcl[int(hour[w]),::-1,q,p] += t_hcl_emis*1e-3/kg_to_kgm2s
                    
                # TODO: Check if all of this code is still needed.
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

            #########################################################
            # Work out vertical distribution for reentry emissions.
            #########################################################
            
            #TODO: Looks like the nox and al2o3 reentry emissions are just added to the launch emissions. Shall we keep them separate?
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
        
        ###################
        # Set up range.
        ###################
        
        # Change (shift) indices on edges of grid:
        # TODO: What does this section accomplish?
        if self.pmin==0: self.pmin=1
        if self.pmax==0: self.pmax=1
        if self.pmax==self.nlon: self.pmax=self.nlon-1
        
        if self.qmin==0: self.qmin=1
        if self.qmin-1==0: self.qmin=1
        if self.qmax==0: self.qmax=1
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

        ########################################
        # Open Dataset and set up dimensions.
        ########################################
        
        # TODO: This section could probably be rewritten using xarray in much fewer lines.
        # TODO: Key here is we probably want to split emissions into categories.
        # define dataset:
        ncout = Dataset(self.outfile_rocket_emis, mode='w', format='NETCDF4')

        # Set dimensions (lat, lon, time, lev):
        # Lat and lon data are trimmed.
        # TODO: Why are lat and lon trimmed?
        ncout.createDimension('lat', self.qmax-self.qmin+3)
        ncout.createDimension('lon', self.pmax-self.pmin+3)
        ncout.createDimension('lev', self.nlev)
        ncout.createDimension('time', self.nhours)
        
        ######################################
        # Create variables for the dimensions.
        ######################################

        # Create individual variables:
        # Time:
        time = ncout.createVariable('time', np.int64, ('time',))
        time.long_name = 'time'
        time.units = 'hours since 2020-'+self.strmon+'-'+self.strday+' 00:00:00'
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

        ######################################
        # Create variables for each species.
        ######################################

        # (1) NOx (emitted as NO):
        rocket_nox = ncout.createVariable('rocket_nox', np.float32, ('time','lev','lat','lon',))
        rocket_nox.long_name = 'Rocket NOx emissions emitted as NO'
        rocket_nox.short_name = 'Rocket NOx emissions'
        rocket_nox.units = 'kg/m2/s'
        rocket_nox[:] = self.rocket_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

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

# Main section of the program
if __name__ == "__main__":

    ##########################################################
    # Configure additional arguments when running the script.
    ##########################################################

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', "--levels", default="72", choices=[47, 72], help="Vertical resolution.")
    parser.add_argument('-g', "--grid_res", default = "2x2.5", choices=["4x5", "2x2.5"], help='Grid resolution.')
    parser.add_argument('-sm', "--start_month", default = "1", choices=np.arange(1,13), help='Start Month.')
    parser.add_argument('-fm', "--final_month", default = "1", choices=np.arange(1,13), help='Final Month.')
    parser.add_argument('-v', "--verbose", action='store_true')
    args = parser.parse_args()
    
    ##########################################################
    # Read the rocket emissions from the database.
    ##########################################################
    
    # TODO: Write databases for 2020. Probably CSV into NetCDF.

    # Define rocket emissions data directories:
    year = 2020
    datadir = './Databases/'
    launch_path = path.join(datadir, f'launch_info_{year}.nc')
    reentry_path = path.join('./Databases/Old/', 'reentries-21Aug2020.nc4')
    rocket_info_path = path.join(datadir, f'rocket_info_{year}.nc')
    outdir = './Output/2020/'    

    # Read rocket emissions:
    rocket_data = RocketData(launch_path, reentry_path, rocket_info_path)

    ##########################################################
    # Calculate the distribution of rocket emissions and save.
    ##########################################################
    
    ''' Define booster and re-entry levels. '''
    
    # N.B. Boosters only extend to ~45 km (layer 44 of the 47-layer model, layer 57 of the 72-layer model)
    # N.B. Re-entry emissions are placed in the GC layer at ~68 km (reentry burnup location).
    # The emissions are evenly distributed across two vertical layers in the model.
    # 46-47 for the 47-layer model, 65-72 for the 72-layer model (equivalent to 60-80 km).
    # This means greater smoothing for the 47-layer model.
    
    # TODO: Do we need to change the reentry or booster locations?
    levels = int(args.levels)
    if levels==47:
        booster_level = 44
        reentry_levs = [46-1,47-1]    # Convert to python indices
    elif levels==72:
        booster_level = 57
        reentry_levs = [65-1,72-1]    # Convert to python indices
    else:
        sys.exit("Invalid number of levels.")
        
        
    ''' Define resolutions and set timings '''
    
    # Define timesteps.
    grid_res = args.grid_res
    if grid_res == '2x2.5': 
        timestep = 1800 #sec
    elif grid_res == '4x5':
        timestep = 3600 #sec
    else:
        sys.exit("Invalid grid resolution.")

    ''' Define locations of StateMet files '''
    
    #Define paths dependent on resolution and levels. Errors should be handled above but included here just in case.
    #Can't use ~ for home directory, have to use '/home/ucfacb0/<path>'
    # TODO: Need to run GEOS-Chem so we have StateMet files for all options.
    if grid_res == '4x5':
        if levels == 72:
            pass
            #gcdir = '/home/ucfacb0/uptrop/GC/run_12.9.3_72L/methane_fluxes/merra2_4x5_og/StateMet/'
        elif levels == 47:
            pass
        else:
            sys.exit("Invalid number of levels.")
    elif grid_res == '2x2.5':
        if levels == 72:
            gcdir = '/home/ucfacb0/rundirs/gc_2x25_72L_merra2_nochem_StateMet/StateMet/'
            #gcdir = '/home/ucfacb0/uptrop/GC/run_12.9.3_72L/methane_fluxes/merra2_2x25_og/StateMet'
        elif levels == 47:
            pass
        else:
            sys.exit("Invalid number of levels.")
    else:
        sys.exit("Invalid grid resolution.")
        
    start_month = int(args.start_month)
    final_month = int(args.final_month)
    months = np.arange(start_month-1,final_month)    
        
    # Go through process of gridding and saving rocket emissions:
    emis_data = OutputEmis(rocket_data, grid_res, timestep, levels, booster_level, reentry_levs, gcdir, months)
    
    ##########################################################
    # Print total emissions of each species.
    ##########################################################
    
    # TODO: Sanity Check (Final Emissions)
    #def print_total_emissions():
    #    print('Total BC emissions (tonnes): ', emis_data.bc_total*1e-6)
    #    print('Total NOx launch emissions (tonnes): ', emis_data.nox_launch_total*1e-6)
    #    print('Total H2O emissions (tonnes): ', emis_data.h2o_total*1e-6)
    #    print('Total CO emissions (tonnes): ', emis_data.co_total*1e-6)
    #    print('Total Al2O3 launch emissions (tonnes): ', emis_data.al2o3_launch_total*1e-6)
    #    print('Total Cl emissions (tonnes): ', emis_data.cl_total*1e-6)
    #    print('Total HCl emissions (tonnes): ', emis_data.hcl_total*1e-6)
    #    print('Total NOx re-entry emissions (tonnes): ', emis_data.nox_reentry_total*1e-3)
    #    print('Total Al2O3 re-entry emissions (tonnes): ', emis_data.al2o3_reentry_total*1e-6)
    
    #if args.verbose == True:
        #print_total_emissions()

    # TODO: Go through and understand these notes.
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
