#!/usr/bin/python
""" Save out rocket emissions as COARDS compliant files for input to HEMCO/GEOS-Chem.

    Input Files:
        launchfile     (str): The path of the launch database, a netcdf file containing information for each rocket launch.
        reentryfile    (str): The path of the reentry database, a netcdf file containing information for each object reentry.
        rocketinfofile (str): The path of the rocket database, a netcdf file containing information for each rocket.
        peifile        (str): The path of the pei database, a csv file containing primary emission indices of major emission species for each propellant type.

    Returns:
        Emission_Distribution (csv)   : A file for use in View_Prop_Distribution.ipynb to view the vertical distribution of emissions.
                                        Each launch or reentry adds three lines with len(altitude):
                                            1) % prop consumed in layer (0 for reentries).
                                            2) mid altitude of layer (from box heights).
                                            3) % prop consumed in layer according to Ross14 study (0 for reentries). 
        Species_Distribution  (csv)   : A file for use in View_Prop_Distribution.ipynb to view the vertical distribution of emissions per species.
                                        Each launch or reentry adds eight lines with len(altitude), containing species emissions in each layer in order of: 
                                            BC, CO, NOx, H2O, Al2O3, Cl, HCl, Cl2
        HEMCO Emission Files  (netcdf): Daily emission files with hourly time bins (dim = time, lon, lat, lev), containing the following variables:
                                            rocket_launch_nox
                                            rocket_fuel_nox
                                            rocket_reentry_nox
                                            rocket_h2o
                                            rocket_bc
                                            rocket_launch_al
                                            rocket_reentry_al
                                            rocket_hcl
                                            rocket_cl
                                            rocket_cl2
                                            rocket_co  
"""

# Import modules:
import argparse
import sys
import os
from os import path
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from distribute_emis_func import make_grid_LL, read_gc_box_height, get_ross_profiles, interp_prop_mass
from alt_emis_func import calculate_bc_ei, calculate_nox_ei, calculate_co_ei, calculate_cl_ei
import datetime
import geopandas as gpd
import fiona
pd.set_option('display.max_colwidth', None)

class RocketData:
    '''Read rocket launch and re-entry emissions'''
    def __init__(self,launchfile,reentryfile, rocketinfofile, peifile):
        
        self.read_launch_emissions(launchfile)
        self.read_reentry_emissions(reentryfile)
        self.read_rocket_info(rocketinfofile)
        self.define_pei(peifile)
    
    def read_launch_emissions(self, launchfile):
        """Read launch emissions from the database.

        Args:
            launchfile (str): The path of the launch database.
        """        

        #Open Dataset.
        fh = Dataset(launchfile, mode='r')
        
        #Extract variables.
        self.launch_lons   = fh.variables['Longitude'][:]
        self.launch_lats   = fh.variables['Latitude'][:]
        self.launch_time   = fh.variables['Time(UTC)'][:]  # UTC hours
        self.launch_month  = fh.variables['Month'][:]
        self.launch_day    = fh.variables['Day'][:]
        self.launch_id     = fh.variables['COSPAR_ID'][:]
        self.launch_rocket = fh.variables['Rocket_Type'][:]
        self.launch_mcs    = fh.variables['MCS_Check'][:]
        
        #Close Dataset.
        fh.close()
        
        print("Successfully loaded launch information.")
        
        # Previously, the emissions for each rocket launch were calculated elsewhere.
        # The values were then loaded in to check for any inconsistencies. 
        # However, now all the emission calculations are done here.
        # Therefore, the sanity check is replaced with a variety of other functions elsewhere.
        
    def read_reentry_emissions(self, reentryfile):
        """Read re-entry emissions from the database.

        Args:
            reentryfile (str): The path of the reentry database.
        """        

        #Open Dataset
        fg = Dataset(reentryfile, mode='r')
        
        # Extract variables:
        self.reentry_id           = fg.variables['RE_ID'][:]
        self.reentry_name         = fg.variables['RE_Name'][:]
        self.reentry_type         = fg.variables['RE_Type'][:]
        self.reentry_burnup       = fg.variables['RE_Burnup'][:]
        self.reentry_stage        = fg.variables['RE_Stage'][:]
        for i in range(len(self.reentry_stage)):
            if str(self.reentry_stage[i])[0] == "B":
                self.reentry_stage[i] = 0
        self.reentry_stage = self.reentry_stage.astype(int)
        self.reentry_lats         = fg.variables['RE_Lat'][:]
        self.reentry_lons         = fg.variables['RE_Lon'][:]
        self.reentry_month        = fg.variables['RE_Mon'][:].astype(int)
        self.reentry_day          = fg.variables['RE_Day'][:].astype(int)
        self.reentry_time         = fg.variables['RE_Time'][:] # UTC hours
        self.reentry_al_mass      = fg.variables['RE_Al_Mass'][:]
        self.reentry_non_al_mass  = fg.variables['RE_Non_Al_Mass'][:]
        self.reentry_mcs          = fg.variables['RE_MCS'][:]
        
        #Close Dataset.
        fg.close()
              
    def read_rocket_info(self, rocketinfofile):
        """Read information about the propellant mass and type for each rocket stage.
        The stage mass is also included in the database for reentry purposes, but not required here.

        Args:
            rocketinfofile (str): The path of the rocket database.
        """        

        # Open Dataset.
        fh = Dataset(rocketinfofile, mode='r')
        
        # Extract variables:
        self.rocket_name         = fh.variables['Rocket_Name'][:]
        self.booster_prop_mass   = fh.variables['Booster_PropMass'][:]
        self.booster_prop_type   = fh.variables['Booster_Fuel_Type'][:]
        self.stage1_prop_mass    = fh.variables['Stage1_PropMass'][:]
        self.stage1_prop_type    = fh.variables['Stage1_Fuel_Type'][:]
        self.stage2_prop_mass    = fh.variables['Stage2_PropMass'][:]
        self.stage2_prop_type    = fh.variables['Stage2_Fuel_Type'][:]
        self.stage2_prop_name    = fh.variables['Stage2_PropName'][:]         
        self.stage3_prop_mass    = fh.variables['Stage3_PropMass'][:]
        self.stage3_prop_type    = fh.variables['Stage3_Fuel_Type'][:]
        self.stage3_prop_name    = fh.variables['Stage3_PropName'][:]
        self.stage4_prop_mass    = fh.variables['Stage4_PropMass'][:]
        self.stage4_prop_type    = fh.variables['Stage4_Fuel_Type'][:]
        self.stage4_prop_name    = fh.variables['Stage4_PropName'][:]
        self.booster_prop_name   = fh.variables['Booster_PropName'][:]
        self.stage1_prop_name    = fh.variables['Stage1_PropName'][:]
        total_imported_prop_mass = fh.variables['Total_Prop_Mass'][:]
        
        # Close Dataset.
        fh.close()
        
        # Finally just check the import was successful by checking that total mass is the sum of all stages.
        if ((np.sum(self.booster_prop_mass) + 
             np.sum(self.stage1_prop_mass) + np.sum(self.stage2_prop_mass) + np.sum(self.stage3_prop_mass) + np.sum(self.stage4_prop_mass)) - total_imported_prop_mass) != 0:
            sys.exit("Error importing propellant information.")
        
        print("Successfully loaded rocket information.")
    
    def define_pei(self, peifile):
        """ Define the primary emission indices.
            Each array should contain 4 values, corresponding to the emission index for :
                Hypergolic, Kerosene, Solid, Hydrogen

        Args:
            peifile (str): The path of the pei database.
        """        
        
        self.pei_fuel_type     = np.array(['Hypergolic', 'Kerosene', 'Solid', 'Hydrogen', 'Methane'])
        
        #2019 values.
        #self.h2_pei            = np.array([4, 12, 27, 35])
        #self.h2o_pei           = np.array([290, 263, 71, 965.])
        #self.cl_pei            = np.array([0, 0, 5, 0])
        #self.hcl_pei           = np.array([0, 0, 209, 0])
        #self.al2o3_pei         = np.array([0, 0, 358, 0])
        #self.bc_pei            = np.array([25, 25, 25, 0])
        #self.co_pei            = np.array([69, 372, 228, 0])
        #self.co2_pei           = np.array([289, 350, 18, 0])
        
        #New values.
        pei_file = pd.read_csv(peifile)

        self.h2o_pei   = pei_file["H2O"].to_numpy() # Each variable must be a numpy array in order to make the np.where routine work later.
        self.h2_pei    = pei_file["H2"].to_numpy()          
        self.co_pei    = pei_file["CO"].to_numpy()
        self.co2_pei   = pei_file["CO2"].to_numpy()
        self.bc_pei    = pei_file["BC"].to_numpy()
        self.nox_pei   = pei_file["NOx"].to_numpy()
        self.al2o3_pei = pei_file["Al2O3"].to_numpy()
        self.cly_pei   = pei_file["Cly"].to_numpy()
        
        print("Successfully loaded PEI information.")
              
class OutputEmis:
    def __init__(self, rocketdata, res, ts, levs, booster_levs, meco_levs, sei_levs, reentry_levs, gc_dir, months, dataset, year, ground_landing_list,stage_alt_dict):

        ####################################
        # Initial Setup
        ####################################
        
        # Setup input variables.
        self.launch_id = rocketdata.launch_id # Extract launch IDs from the imported rocket data.
        self.ts = ts
        self.nlev = levs
        self.booster_levs = booster_levs
        self.meco_levs = meco_levs
        self.sei_levs = sei_levs
        self.bot_reenter = min(reentry_levs)
        self.top_reenter = max(reentry_levs)
        self.n_reenter_levs = self.top_reenter - self.bot_reenter + 1
        self.nhours = 24
        self.include_landing = True
        self.dataset = dataset
        self.year = year
        self.ground_landing_list = ground_landing_list
        self.stage_alt_dict = stage_alt_dict
        self.total_landing_prop = 0

        self.included_prop = 0
        self.missing_prop = 0
        
        # Define Molecular Weights:
        self.mw_h   = 1.008
        self.mw_h2  = self.mw_h * 2
        self.mw_h2o = self.mw_h2 + 16.00

        # Get Ross vertical profiles of propellant burned:
        #   self.ross_alt (centre alitiudes of each bin)
        #   self.ross_prop_mass (unitless percent of propellant mass)
        self.ross_alt, self.ross_prop_mass, self.ross_cumulative_mass = get_ross_profiles()

        # Create variables for totals for a future sanity check:
        self.nox_launch_total, self.bc_total, self.h2o_total = 0.0, 0.0, 0.0
        self.co_total,self.al2o3_launch_total, self.cl_total = 0.0, 0.0, 0.0
        self.hcl_total, self.cl2_total, self.nox_reentry_total, self.al2o3_reentry_total = 0.0, 0.0, 0.0, 0.0
        self.missing_emis = np.zeros(8)
        self.booster_prop_consumed, self.stage1_prop_consumed, self.stage2_prop_consumed = np.zeros(len(self.launch_id)), np.zeros(len(self.launch_id)), np.zeros(len(self.launch_id))
        self.total_prop_consumed = np.zeros((len(rocket_data.h2o_pei),3))
        self.launch_count = 0
        
        # Make grid at input resolution (no bounds supplied so full global).
        # Can use this with different in and out edges.
        grid = make_grid_LL(res)  
        #Extract useful variables from the grid.    
        self.nlon = len(grid['lon'])
        self.nlat = len(grid['lat'])
        self.lon =  grid['lon']
        self.lat =  grid['lat']
        
        #Creat 2D lat and lon grid.
        #X, Y = np.meshgrid(self.lon, self.lat,indexing='ij')
        #self.lon2d = X
        #self.lat2d = Y
        
        # Create the arrays for the output file to check prop/species distribution.
        reentry_length = len(rocket_data.reentry_id)
        #reentry_length = 0
        self.output_for_csv = np.zeros(((len(rocket_data.launch_id)+reentry_length)*3,self.nlev))
        self.csv_count = 0
        self.output_for_csv_2 = np.zeros(((len(rocket_data.launch_id)+reentry_length)*8,self.nlev))
        self.csv_count_2 = 0
        
        # Build the ocean landing list for the year in question.
        ocean_landings = raul_data[(raul_data["Name"].str.contains("ASDS")) & (raul_data["Description"].str.contains("Landing -"))].reset_index(drop=True)
        ocean_landings = ocean_landings[~ocean_landings["Name"].str.contains("planned")].reset_index(drop=True)
        ocean_landings = ocean_landings[~ocean_landings["Name"].str.contains("planed")].reset_index(drop=True)
        date_col = []
        for landing in range(len(ocean_landings["Name"])):
            year_ind = ocean_landings["Description"][landing].index("Landing -")
            datestr = ocean_landings["Description"][landing][year_ind:].replace(" ","")[8:17].replace("-","")
            date_col.append(datestr)
        ocean_landings["Date"] = date_col
        ocean_landings['Date'] = pd.to_datetime(ocean_landings['Date'],format='%d%b%y')
        self.ocean_landings = ocean_landings[(ocean_landings["Date"] < f'{year+1}-01-01') & (ocean_landings["Date"] >= f'{year}-01-01')].reset_index(drop=True)
        
        #################################
        # Loop over each day and month.
        #################################
        #for m in range(0,12):
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

            # Get month string:
            if m+1<=9:
                self.strmon='0'+str(m+1)
            else:
                self.strmon=str(m+1)

            print('MONTH = ', self.strmon)             
            
            #Loop over a single day
            #for d in range(6,9):
            
            #Loop over all days:
            for d in range(ndays):
                
                # Get day string:
                if d+1<=9:
                    self.strday='0'+str(d+1)
                else:
                    self.strday=str(d+1)

                # gc_dir is defined for each scenario in the main section of the python script.
                # So only need one block to read GEOS-Chem box height from StateMet file.
                
                #self.gc_file = path.join(gc_dir, 'GEOSChem.StateMet.'+str(self.year)+self.strmon+self.strday+'_0000z.nc4')
                #file_exists = os.path.exists(self.gc_file)
                #if not file_exists: continue
                #self.box_height, self.area, self.bot_alt, self.mid_alt, self.top_alt = read_gc_box_height(self.gc_file,self.nlev)
                
                gc_layer_data = np.loadtxt(".\Databases\GC_47.csv",delimiter=",")
                self.top_alt = np.zeros((self.nlev,self.nlat,self.nlon))
                self.bot_alt = np.zeros((self.nlev,self.nlat,self.nlon))
                self.mid_alt = np.zeros((self.nlev,self.nlat,self.nlon))
                self.area = np.zeros((self.nlat,self.nlon))
                for lat in range(self.nlat):
                    for lon in range(self.nlon):
                        self.bot_alt[:,lat,lon] = gc_layer_data[::-1,0]*1000
                        self.mid_alt[:,lat,lon] = gc_layer_data[::-1,1]*1000
                        self.top_alt[:,lat,lon] = gc_layer_data[::-1,2]*1000
                        self.area[lat,lon]      = 1
                        # TODO: Add back after Myriad is back.
                        # Set this back up when we have access to the StateMet files.
                        # This is currently set to 1 as its only needed to output the final netcdf files, not the stats.
                
                # Set up the data arrays which will be saved to file.
                self.rocket_launch_nox  = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_fuel_nox    = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_reentry_nox = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_h2o         = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_bc          = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_co          = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_launch_al   = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_reentry_al  = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_hcl         = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_cl          = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_cl2         = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))

                # Initialize:
                self.pmin,self.pmax=np.nan,np.nan
                self.qmin,self.qmax=np.nan,np.nan

                # Define output file name for this day:
                if self.dataset == 1:
                    l_ind=np.where((rocket_data.launch_month==(m+1))&(rocket_data.launch_day==(d+1))&(~np.isnan(rocket_data.launch_time))&(rocket_data.launch_mcs==False))[0]
                    r_ind=np.where((rocket_data.reentry_month==(m+1))&(rocket_data.reentry_day==(d+1))&(~np.isnan(rocket_data.reentry_time))&(rocket_data.reentry_mcs==False))[0]
                    self.outfile_rocket_emis = path.join(outdir,self.strmon,f'ROCKET_EMIS_{res}_{str(self.nlev)}L_{self.year}{self.strmon}{self.strday}.nc4')
                elif self.dataset == 2:
                    l_ind=np.where((rocket_data.launch_month==(m+1))&(rocket_data.launch_day==(d+1))&(~np.isnan(rocket_data.launch_time))&(rocket_data.launch_mcs==True))[0]
                    r_ind=np.where((rocket_data.reentry_month==(m+1))&(rocket_data.reentry_day==(d+1))&(~np.isnan(rocket_data.reentry_time))&(rocket_data.reentry_mcs==True))[0]
                    self.outfile_rocket_emis = path.join(outdir,self.strmon,f'ROCKET_EMIS_MCS_{res}_{str(self.nlev)}L_{self.year}{self.strmon}{self.strday}.nc4')
                elif self.dataset == 3:
                    l_ind=np.where((rocket_data.launch_month==(m+1))&(rocket_data.launch_day==(d+1))&(~np.isnan(rocket_data.launch_time)))[0]
                    r_ind=np.where((rocket_data.reentry_month==(m+1))&(rocket_data.reentry_day==(d+1)))[0]
                    self.outfile_rocket_emis = path.join(outdir,self.strmon,f'ROCKET_EMIS_ALL_{res}_{str(self.nlev)}L_{self.year}{self.strmon}{self.strday}.nc4')
                    
                ########################################################################
                # Call grid_emis function to calculate distribution from launches
                ########################################################################
                
                if len(l_ind)>0:
                    #print('----> Day processing: ',self.strday,f"{len(l_ind)} Launches.")
                    self.grid_emis(l_ind,
                                   rocket_data.launch_lons[l_ind],
                                   rocket_data.launch_lats[l_ind],
                                   rocket_data.launch_time[l_ind],
                                   'launch',
                                   rocket_data.launch_id[l_ind],
                                   rocket_data.launch_rocket[l_ind],
                                   d,
                                   m,
                                   )

                ########################################################################
                # Call grid_emis function to calculate distribution from re-entries
                ########################################################################              
                
                if len(r_ind)>0:
                    #print('----> Day processing: ',self.strday,f"{len(r_ind)} Re-entries.")
                    self.grid_emis(r_ind,
                                   rocket_data.reentry_lons[r_ind],
                                   rocket_data.reentry_lats[r_ind],
                                   rocket_data.reentry_time[r_ind],
                                   'reentry',
                                   ' ',
                                   ' ',
                                   d,
                                   m,
                                   )
                    
                    # Sum up all re-entry NOx (kg):
                    #self.nox_reentry_total += sum(rocket_data.reentry_nox[r_ind])

                ####################################
                # Save file as NetCDF
                ####################################
                
                #if len(l_ind)>0 or len(r_ind)>0:
                #    # If there are launches or reentries, then save file normally.
                #    self.save_netcdf()
                #else:
                #    # If there are no launches, create a dummy file to accommodate HEMCO file reading.
                #    lat_ind=np.argmin(abs(self.lat-0))
                #    self.qmin,self.qmax=int(lat_ind),int(lat_ind)
                #    lon_ind=np.argmin(abs(self.lon-0))
                #    self.pmin,self.pmax=int(lon_ind),int(lon_ind)
                #    self.save_netcdf()
        df = pd.DataFrame(self.output_for_csv)
        df_2 = pd.DataFrame(self.output_for_csv_2)
        if len(months) == 12:
            df.to_csv(f"./Emission_Output/Emission_Distribution_{self.year}.csv", float_format='%.3f')
            df_2.to_csv(f"./Emission_Output/Species_Distribution_{self.year}.csv", float_format='%.3f')
             
    def process_launch_event_altitudes(self, valid_index, p, q, launch_rocket,launch_id):
        
        # Define the propellant saved for landing for reusable rockets.
        if launch_id in self.ground_landing_list:
            landing_prop_percent = 100-5.6-5.6-1.2
        else:
            landing_prop_percent = 100-5.6-1.2
                    
        stage_alt_beco = stage_alt_dict[f"{launch_rocket} BECO"] 
        stage_alt_meco = stage_alt_dict[f"{launch_rocket} MECO"]
        stage_alt_sei  = stage_alt_dict[f"{launch_rocket} SEI1"] 
        
        if np.isnan(stage_alt_meco) and np.isnan(stage_alt_sei):
            # Define the rocket configuration.
            if rocket_data.booster_prop_type[valid_index] != '':
                if rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] == '' and rocket_data.stage3_prop_type[valid_index] == '' and rocket_data.stage4_prop_type[valid_index] == '':
                    rocket_config_type = 0
                elif rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] == '' and rocket_data.stage4_prop_type[valid_index] == '':
                    rocket_config_type = 0
                elif rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] != '' and rocket_data.stage4_prop_type[valid_index] == '':
                    rocket_config_type = 1
                elif rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] != '' and rocket_data.stage4_prop_type[valid_index] != '':
                    rocket_config_type = 2
                else:
                    sys.exit("Incorrect rocket configuration.")
            else:
                if rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] == '' and rocket_data.stage4_prop_type[valid_index] == '':
                    rocket_config_type = 3
                elif rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] != '' and rocket_data.stage4_prop_type[valid_index] == '':
                    rocket_config_type = 4
                elif rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] != '' and rocket_data.stage4_prop_type[valid_index] != '':
                    rocket_config_type = 5
                else:
                    sys.exit("Incorrect rocket configuration.")
                    
            stage_alt_beco = self.booster_levs[rocket_config_type]
            stage_alt_meco = self.meco_levs[rocket_config_type]
            stage_alt_sei  = self.sei_levs[rocket_config_type]    
        
        ###########
        # Boosters
        ###########
        
        if rocket_data.booster_prop_type[valid_index] != '':
            
            # If BECO occurs above the the GC boundary, then we only use some of the booster emissions.
            if stage_alt_beco * 1e3 > self.top_alt[-1,q,p]:
                
                self.gc_relative_mass_booster = np.asarray(self.gc_relative_mass)
                self.booster_alt_index = self.nlev - 1
                
                # If BECO is above GC, but in the range of the Ross distribution, we can interpolate to see how much propellant is consumed in GC and before BECO.
                if stage_alt_beco < 102.5:            
                    self.propellant_below_beco = np.interp(stage_alt_beco,self.ross_alt[::-1], self.ross_cumulative_mass[::-1])
                    # Now we can work out the proportion of propellant consumed within GC, and use this to correct the sum.
                    gc_percent = self.propellant_in_gc / self.propellant_below_beco * 100
                    self.gc_relative_mass_booster = self.gc_relative_mass_booster / np.sum(self.gc_relative_mass_booster) * gc_percent
                    
                # Note: If BECO is above 102.5, the sum of gc_relative_mass_booster is already equal to propellant_in_gc because its just a simple slice of gc_relative_mass.
            
            # If BECO occurs below the the GC boundary, then we can use all of the stage 1 emissions.
            else:
                # Find out which layer BECO occurs in.
                self.booster_alt_index = np.argmin(np.abs(stage_alt_beco*1e3 - self.mid_alt[:,q,p]))
                gc_relative_mass_booster = np.asarray(self.gc_relative_mass[self.nlev-self.booster_alt_index-1:])
                
                # Normalize the vertical emission profile for the booster emissions.
                if launch_rocket == "Falcon Heavy" and self.include_landing == True:
                    self.gc_relative_mass_booster = gc_relative_mass_booster / np.sum(gc_relative_mass_booster) * landing_prop_percent
                    self.total_landing_prop += (100 - landing_prop_percent) * rocket_data.booster_prop_mass[valid_index] / 100
                else:
                    self.gc_relative_mass_booster = gc_relative_mass_booster / np.sum(gc_relative_mass_booster) * 100
                
        ###########
        # Stage 1
        ###########              

        if launch_rocket in ["LauncherOne","GSLV Mk III"]:
            if launch_rocket == "LauncherOne":
                fei_alt = 12.37
            elif launch_rocket == "GSLV Mk III":
                fei_alt = 46.534
            else:
                sys.exit("Incorrect rocket found.")
            # The 1st stage of these rockets essentially act like a second stage, starting in GC with MECO above GC.
            self.fei_alt_index = np.argmin(np.abs(fei_alt*1e3 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_stage1 = np.asarray(self.gc_relative_mass[:self.nlev-self.fei_alt_index])
            # Now interpolate the cumulative mass to optimise what percentage of propellant is within GEOS-Chem.
            fei_mass = np.interp(fei_alt,self.ross_alt[::-1], self.ross_cumulative_mass[::-1])
            gc_percent = (self.propellant_in_gc - fei_mass) / (100 - fei_mass) * 100
            self.gc_relative_mass_stage1 = self.gc_relative_mass_stage1 / np.sum(self.gc_relative_mass_stage1) * gc_percent            
            
        # If MECO occurs above the the GC boundary, then we only use some of the booster emissions.        
        elif stage_alt_meco * 1e3 > self.top_alt[-1,q,p]:
            
            self.gc_relative_mass_stage1 = np.asarray(self.gc_relative_mass)
            self.MECO_alt_index = self.nlev - 1
            
            # If MECO is above GC, but in the range of the Ross distribution, we can interpolate to see how much propellant is consumed in GC and before MECO.
            if stage_alt_meco < 102.5:            
                self.propellant_below_meco = np.interp(stage_alt_meco,self.ross_alt[::-1], self.ross_cumulative_mass[::-1])
                # Now we can work out the proportion of propellant consumed within GC, and use this to correct the sum.
                gc_percent = self.propellant_in_gc / self.propellant_below_meco * 100
                self.gc_relative_mass_stage1 = self.gc_relative_mass_stage1 / np.sum(self.gc_relative_mass_stage1) * gc_percent
            # Note: If MECO is above 102.5, the sum of gc_relative_mass_stage1 is already equal to propellant_in_gc because its just a simple slice of gc_relative_mass.
        
        # If MECO occurs below the the GC boundary, then we can use all of the stage 1 emissions.
        else:
            
            # Find out which layer MECO occurs in.
            self.MECO_alt_index = np.argmin(np.abs(stage_alt_meco*1e3 - self.mid_alt[:,q,p]))
            if launch_rocket == "Pegasus XL":
                fei_alt = 11.79
                self.fei_alt_index = np.argmin(np.abs(fei_alt*1e3 - self.mid_alt[:,q,p]))
                self.gc_relative_mass_stage1 = np.asarray(self.gc_relative_mass[self.nlev-self.MECO_alt_index-1:self.nlev-self.fei_alt_index])
            else:
                self.gc_relative_mass_stage1 = np.asarray(self.gc_relative_mass[self.nlev-self.MECO_alt_index-1:])
            
            # If the rocket is Falcon v1.2 Block 5, then MECO is always in GC, and 93.2% of the emissions are used for ascent.
            # There is an extra 'boostback' burn for ground landings. No information of % of propellant, so assumed to be equal to the reentry burn.
            if launch_rocket == "Falcon 9 v1.2" and self.include_landing == True:
                self.gc_relative_mass_stage1 = self.gc_relative_mass_stage1 / np.sum(self.gc_relative_mass_stage1) * landing_prop_percent 
                self.total_landing_prop += (100 - landing_prop_percent) * rocket_data.stage1_prop_mass[valid_index] / 100                
            # For all other rockets, 100% is used for ascent.
            else:
                self.gc_relative_mass_stage1 = self.gc_relative_mass_stage1 / np.sum(self.gc_relative_mass_stage1) * 100
        
        ###########
        # Stage 2
        ###########
                               
        # If SEI occurs above the the GC boundary, then we can ignore the second stage.
        if stage_alt_sei * 1e3 > self.top_alt[-1,q,p]:
            self.gc_relative_mass_stage2 = np.asarray([0])
            self.SEI_alt_index = self.nlev
        
        # If SEI is within GC, we need to differentiate based on SECO.
        else:
            self.SEI_alt_index = np.argmin(np.abs(stage_alt_sei*1e3 - self.mid_alt[:,q,p]))
            
            # SECO is only within GC for one rocket.
            if launch_rocket in ["Minotaur 1"]:
                seco_alt = 71.70
                self.seco_alt_index = np.argmin(np.abs(seco_alt*1e3 - self.mid_alt[:,q,p]))
                self.gc_relative_mass_stage2 = np.asarray(self.gc_relative_mass[self.nlev-self.seco_alt_index-1:self.nlev-self.SEI_alt_index])
                self.gc_relative_mass_stage2 = self.gc_relative_mass_stage2 / np.sum(self.gc_relative_mass_stage2) * 100
            
            # SECO is above GC and below Ross (120km) for two rockets.   
            elif launch_rocket in ["Minotaur-4","Vega"]:
                self.gc_relative_mass_stage2 = np.asarray(self.gc_relative_mass[:self.nlev-self.SEI_alt_index])
                if launch_rocket == "Minotaur-4":
                    seco_alt = 111.18
                elif launch_rocket == "Vega":
                    seco_alt = 113.00          
                self.propellant_below_seco = np.interp(seco_alt,self.ross_alt[::-1], self.ross_cumulative_mass[::-1])
                # Now we can work out the proportion of propellant consumed within GC, and use this to correct the sum.
                gc_percent = self.propellant_in_gc / self.propellant_below_seco * 100
                self.gc_relative_mass_stage2 = self.gc_relative_mass_stage2 / np.sum(self.gc_relative_mass_stage2) * gc_percent
                
            # For everything else, SEI and SECO occur above GC.
            else:   
                
                self.gc_relative_mass_stage2 = np.asarray(self.gc_relative_mass[:self.nlev-self.SEI_alt_index])
                # Now interpolate the cumulative mass to optimise what percentage of propellant is within GEOS-Chem.
                sei_mass = np.interp(stage_alt_sei,self.ross_alt[::-1], self.ross_cumulative_mass[::-1])
                gc_percent = (self.propellant_in_gc - sei_mass) / (100 - sei_mass) * 100
                self.gc_relative_mass_stage2 = self.gc_relative_mass_stage2 / np.sum(self.gc_relative_mass_stage2) * gc_percent
            
        ###########
        # Stage 3
        ###########
                
        # Calculate third stage emissions for Minotaur 1 only.    
        if launch_rocket == "Minotaur 1":
            # Minotaur 1 third stage ignition occurs below the the GC boundary, so we can need to add some of the stage 3 emissions.
            self.TEI_alt_index = np.argmin(np.abs(73.47*1e3 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_stage3 = np.asarray(self.gc_relative_mass[:self.nlev-self.TEI_alt_index])
            # Now interpolate the cumulative mass to optimise what percentage of propellant is within GEOS-Chem.
            tei_mass = np.interp(73.47,self.ross_alt[::-1], self.ross_cumulative_mass[::-1])
            gc_percent = (self.propellant_in_gc - tei_mass) / (100 - tei_mass) * 100
            self.gc_relative_mass_stage3 = self.gc_relative_mass_stage3 / np.sum(self.gc_relative_mass_stage3) * gc_percent
            
        # Finally create an extra stage just for the landing emissions of Falcon 9 v1.2. 
        if launch_rocket in ["Falcon 9 v1.2","Falcon Heavy"]:
            # 5.6% are used in the entry burn, over 70-54.7 km.
            self.entry_top = np.argmin(np.abs(70000 - self.mid_alt[:,q,p]))
            self.entry_bot = np.argmin(np.abs(54700 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_entry = np.asarray(self.gc_relative_mass[self.nlev-self.entry_top-1:self.nlev-self.entry_bot])
            self.gc_relative_mass_entry = self.gc_relative_mass_entry / np.sum(self.gc_relative_mass_entry) * 5.6
            
            # 1.2% are used in the landing burn, over 3.3-0 km.
            self.landing_top = np.argmin(np.abs(3300 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_landing = np.asarray(self.gc_relative_mass[self.nlev-self.landing_top-1:])
            self.gc_relative_mass_landing = self.gc_relative_mass_landing / np.sum(self.gc_relative_mass_landing) * 1.2
        else:
            self.gc_relative_mass_landing = 0
            self.gc_relative_mass_entry = 0
        
        return stage_alt_beco,stage_alt_meco,stage_alt_sei 
    
    def calc_emis(self,start_ind,stop_ind,pei_index,prop_mass,vertical_profile,time_index, q, p, kg_to_kgm2s, total_vertical_propellant):
        ei_bc = calculate_bc_ei(self.mid_alt[start_ind:stop_ind:-1,q,p]*1e-3,rocket_data.bc_pei[pei_index])
        t_bc_emis = ei_bc * prop_mass * 1e-2 * vertical_profile
        self.bc_total += np.sum(t_bc_emis)
        self.rocket_bc[time_index,start_ind:stop_ind:-1,q,p] += t_bc_emis * 1e-3 / kg_to_kgm2s
        
        ei_co = calculate_co_ei(self.mid_alt[start_ind:stop_ind:-1,q,p]*1e-3, rocket_data.co_pei[pei_index], rocket_data.co2_pei[pei_index])
        t_co_emis = ei_co * prop_mass * 1e-2 * vertical_profile
        self.co_total += np.sum(t_co_emis)
        self.rocket_co[time_index,start_ind:stop_ind:-1,q,p] += t_co_emis * 1e-3 / kg_to_kgm2s
        
        ei_sec_nox = calculate_nox_ei(self.mid_alt[start_ind:stop_ind:-1,q,p]*1e-3)
        t_launch_nox_emis = ei_sec_nox * prop_mass * 1e-2 * vertical_profile
        self.nox_launch_total += np.sum(t_launch_nox_emis)
        self.rocket_launch_nox[time_index,start_ind:stop_ind:-1,q,p] = t_launch_nox_emis * 1e-3 / kg_to_kgm2s
        
        t_fuel_nox_emis = rocket_data.nox_pei[pei_index] * prop_mass * 1e-2 * vertical_profile
        self.nox_launch_total += np.sum(t_fuel_nox_emis)
        self.rocket_fuel_nox[time_index,start_ind:stop_ind:-1,q,p] += t_fuel_nox_emis * 1e-3 / kg_to_kgm2s
        
        self.ei_h2o =  rocket_data.h2o_pei[pei_index] + rocket_data.h2_pei[pei_index] * self.mw_h2o / self.mw_h2 
        t_h2o_emis = self.ei_h2o * prop_mass * 1e-2 * vertical_profile
        self.h2o_total += np.sum(t_h2o_emis)
        self.rocket_h2o[time_index,start_ind:stop_ind:-1,q,p] += t_h2o_emis * 1e-3 / kg_to_kgm2s
        
        t_al2o3_emis = rocket_data.al2o3_pei[pei_index] * prop_mass * 1e-2 * vertical_profile
        self.al2o3_launch_total += np.sum(t_al2o3_emis)
        self.rocket_launch_al[time_index,start_ind:stop_ind:-1,q,p] += t_al2o3_emis * 1e-3 / kg_to_kgm2s
        
        ei_cl, ei_hcl, ei_cl2 = calculate_cl_ei(self.mid_alt[start_ind:stop_ind:-1,q,p]*1e-3, rocket_data.cly_pei[pei_index])  
        
        t_cl_emis = ei_cl * prop_mass * 1e-2 * vertical_profile
        self.cl_total += np.sum(t_cl_emis)
        self.rocket_cl[time_index,start_ind:stop_ind:-1,q,p] += t_cl_emis * 1e-3 / kg_to_kgm2s

        t_hcl_emis = ei_hcl * prop_mass * 1e-2 * vertical_profile
        self.hcl_total += np.sum(t_hcl_emis)
        self.rocket_hcl[time_index,start_ind:stop_ind:-1,q,p] += t_hcl_emis * 1e-3 / kg_to_kgm2s
        
        t_cl2_emis = ei_cl2 * prop_mass * 1e-2 * vertical_profile
        self.cl2_total += np.sum(t_cl2_emis)
        self.rocket_cl2[time_index,start_ind:stop_ind:-1,q,p] += t_cl2_emis * 1e-3 / kg_to_kgm2s
        
        # These are all for viewing the individual propellant / species vertical distribution per launch.
        
        if stop_ind != None:
            stop_index_mod = stop_ind + 1
        else:
            stop_index_mod = stop_ind
        if start_ind != None:
            start_index_mod = start_ind + 1
        else:
            start_index_mod = start_ind
        
        
        vertical_propellant = prop_mass * vertical_profile
        
        self.included_prop += np.sum(vertical_propellant) * 1e-2

        total_vertical_propellant[stop_index_mod:start_index_mod,0]   += vertical_propellant[::-1]
        total_vertical_propellant[stop_index_mod:start_index_mod,1]   += t_bc_emis[::-1]
        total_vertical_propellant[stop_index_mod:start_index_mod,2]   += t_co_emis[::-1]
        total_vertical_propellant[stop_index_mod:start_index_mod,3]   += (t_launch_nox_emis[::-1] + t_fuel_nox_emis[::-1])
        total_vertical_propellant[stop_index_mod:start_index_mod,4]   += t_h2o_emis[::-1]
        total_vertical_propellant[stop_index_mod:start_index_mod,5]   += t_al2o3_emis[::-1]
        total_vertical_propellant[stop_index_mod:start_index_mod,6]   += t_cl_emis[::-1]
        total_vertical_propellant[stop_index_mod:start_index_mod,7]   += t_hcl_emis[::-1]
        total_vertical_propellant[stop_index_mod:start_index_mod,8]   += t_cl2_emis[::-1]
        
        return total_vertical_propellant
    
    def calc_missing_emis(self, pei_index, prop_mass, percent_included):
        
        ei_bc = calculate_bc_ei([80],rocket_data.bc_pei[pei_index])
        t_bc_emis = ei_bc * prop_mass * 1e-2 * percent_included
        self.missing_emis[0] += np.sum(t_bc_emis)
        
        ei_co = calculate_co_ei([80], rocket_data.co_pei[pei_index], rocket_data.co2_pei[pei_index])
        t_co_emis = ei_co * prop_mass * 1e-2 * percent_included
        self.missing_emis[1] += np.sum(t_co_emis)
        
        ei_sec_nox = calculate_nox_ei([80])
        t_launch_nox_emis = ei_sec_nox * prop_mass * 1e-2 * percent_included
        self.missing_emis[2] += np.sum(t_launch_nox_emis)
        
        t_fuel_nox_emis = rocket_data.nox_pei[pei_index] * prop_mass * 1e-2 * percent_included
        self.missing_emis[2] += np.sum(t_fuel_nox_emis)
        
        self.ei_h2o =  rocket_data.h2o_pei[pei_index] + rocket_data.h2_pei[pei_index] * self.mw_h2o / self.mw_h2 
        t_h2o_emis = self.ei_h2o * prop_mass * 1e-2 * percent_included
        self.missing_emis[3] += np.sum(t_h2o_emis)
        
        t_al2o3_emis = rocket_data.al2o3_pei[pei_index] * prop_mass * 1e-2 * percent_included
        self.missing_emis[4] += np.sum(t_al2o3_emis)
        
        ei_cl, ei_hcl, ei_cl2 = calculate_cl_ei([80], rocket_data.cly_pei[pei_index])  
        
        t_cl_emis = ei_cl * prop_mass * 1e-2 * percent_included
        self.missing_emis[5] += np.sum(t_cl_emis)

        t_hcl_emis = ei_hcl * prop_mass * 1e-2 * percent_included
        self.missing_emis[6] += np.sum(t_hcl_emis)
        
        t_cl2_emis = ei_cl2 * prop_mass * 1e-2 * percent_included
        self.missing_emis[7] += np.sum(t_cl2_emis)
        
        self.missing_prop += prop_mass * 1e-2 * percent_included
             
    def grid_emis(self,index,lon,lat,hour,emis_type,launch_id,launch_rocket,d,m):
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
            
            # NOTE: GEOS-Chem data is provided as [lat,lon,lev], where levels go from surface to top-of-atmosphere.
            
            ############################################
            # Format the time of the event.
            ############################################
                
            #time_index = int(hour[w]*60*60)//self.ts
            time_index = int(hour[w])
            
            #########################################################
            # Work out vertical distribution for launch emissions.
            #########################################################

            if emis_type=='launch':
                
                ############################################
                # Interpolate propellant mass distribution.
                ############################################

                # Linearly interpolate Ross profile proportion of propellant mass to GEOS-Chem vertical grid:
                # Dataset of interest from this is self.gc_relative_mass
                self.propellant_in_gc, self.gc_relative_mass = interp_prop_mass(self.bot_alt, self.mid_alt, self.top_alt,
                                                                                     self.ross_alt, self.ross_cumulative_mass, 
                                                                                     self.ross_prop_mass, self.nlev, p, q)

                ############################################
                # Check the rocket type 
                ############################################

                # Setup rocket type variables (trim_name contains all rockets and is defined in __init__ function of this class):
                # This was previously set up to trim the rocket name, however this was mixing up rockets with the same name.
                # Has been removed, so now the script selects the specific launch vehicle. 
                #trim_type = launch_rocket[w][0:5]
                
                rocket_found = False
                valid_index = 0
                
                # Loop over rockets to find matching rocket and associated propellant mass:
                for ll in range(len(rocket_data.rocket_name)):
                    if launch_rocket[w] == rocket_data.rocket_name[ll]:
                        rocket_found = True
                        valid_index=ll
                        #print(f"Rocket name is {launch_rocket[w]}")
                        break
                    
                # Catch any missing rocket propellant masses:
                if rocket_found == False:
                    sys.exit(f"No propellant mass found for {launch_rocket[w]}. Exiting programme.")
                    
                ############################################################################
                # Start processing the launch event altitudes and deal with failed launches.
                ############################################################################
                
                if launch_id[w] in ['2020-F04','2020-F11',
                                    '2021-F04']:
                    print(f'Launch {launch_id[w]} failed. Not processing.')
                    self.csv_count += 3
                    self.csv_count_2 += 8
                    continue
                                                    
                # Next find index of fuel type in primary emissions index data:
                pei_booster_index = np.where( rocket_data.pei_fuel_type == rocket_data.booster_prop_type[valid_index] )[0]
                pei_stage1_index  = np.where( rocket_data.pei_fuel_type == rocket_data.stage1_prop_type[valid_index] )[0]
                pei_stage2_index  = np.where( rocket_data.pei_fuel_type == rocket_data.stage2_prop_type[valid_index] )[0]
                pei_stage3_index  = np.where( rocket_data.pei_fuel_type == rocket_data.stage3_prop_type[valid_index] )[0]
                pei_stage4_index  = np.where( rocket_data.pei_fuel_type == rocket_data.stage4_prop_type[valid_index] )[0]
                
                stage_alt_beco,stage_alt_meco,stage_alt_sei = self.process_launch_event_altitudes(valid_index, p, q, launch_rocket[w],launch_id[w])
                
                # Most failures are for upper stages, and so can be treated as normal here.
                # Full information is provided in README.txt
                if launch_id[w] in ['2020-F02','2020-F05',
                                      '2021-F02','2021-F07','2021-F08',
                                      '2022-F01','2022-F02']:
                    self.gc_relative_mass_stage2 = np.asarray([0])
                    self.SEI_alt_index = self.nlev 
                elif launch_id[w] in ['2020-F07','2021-F01','2021-F07']:
                    if launch_id[w] == '2020-F07': # Astra Rocket 3 launch, rocket shut off at 0.9km.
                       failed_alt = 900
                    elif launch_id[w] == '2021-F01': # Shuang Quxian-1 launch, rocket disintegrated at Max-Q. Approximating altitude using Proton-M and Minotaur-IV max-q alts.
                        failed_alt = 10700
                    elif launch_id[w] == '2021-F07': # Astra Rocket 3 launch, rocket shut off at 31km.
                        failed_alt = 31000
                    cutoff_ind = np.argmin(np.abs(failed_alt - self.mid_alt[::-1,q,p]))
                    self.gc_relative_mass_stage1[:cutoff_ind+1] = np.zeros((len(self.gc_relative_mass_stage1[:cutoff_ind+1])))
                  
                ###########################################
                # Update the propellant masses for Atlas.
                ###########################################
                
                b_prop = rocket_data.booster_prop_mass[valid_index]
                
                if "Atlas" in rocket_data.rocket_name[valid_index] and datetime.datetime(self.year,m+1,d+1) >= datetime.datetime(2020,11,13):
                    b_prop = 44200 * int(rocket_data.rocket_name[valid_index][9])
                
                ##################################################
                # Sanity Checks for Propellant Mass Distributions
                ##################################################
                
                # For all rockets with boosters, the propellant consumed for the boosters should never be bigger than the total booster propellant.
                # Suppressed for Falcon Heavy, as this has reusable boosters.
                if rocket_data.booster_prop_type[valid_index] != '':
                    self.booster_prop_consumed[self.launch_count] = np.sum(self.gc_relative_mass_booster * b_prop * 1e-2)
                    if (self.booster_prop_consumed[self.launch_count] - b_prop) > 0.1:
                        print(self.booster_prop_consumed[self.launch_count],rocket_data.booster_prop_mass[valid_index])
                        sys.exit(f"Error with Booster emissions - 1. {launch_id[w]}")
                    if stage_alt_meco < 80:
                        if ((np.abs(self.booster_prop_consumed[self.launch_count] - b_prop) / b_prop * 100) > 1) and (rocket_data.rocket_name[valid_index] != "Falcon Heavy"):
                            print(np.abs(self.booster_prop_consumed[self.launch_count]),b_prop,np.abs(self.booster_prop_consumed[self.launch_count] - b_prop) / b_prop * 100)
                            sys.exit(f"Error with booster emissions -2. {launch_id[w]}") 
                        
                self.stage1_prop_consumed[self.launch_count]  = np.sum(self.gc_relative_mass_stage1 * rocket_data.stage1_prop_mass[valid_index] * 1e-2)
                self.stage2_prop_consumed[self.launch_count]  = np.sum(self.gc_relative_mass_stage2 * rocket_data.stage2_prop_mass[valid_index] * 1e-2)

                # For all rockets, the propellant consumed for each stage should never be bigger than the total propellant in each stage.
                if (self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) > 0.1:
                    sys.exit(f"Error with Stage 1 emissions - 1.")
                elif (self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) > 0.05 and (self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) < 0.1:
                    print(f"Warning: Floating point difference of {np.abs(self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index])}")
                if (self.stage2_prop_consumed[self.launch_count] - rocket_data.stage2_prop_mass[valid_index]) > 0.1:
                    sys.exit("Error with Stage 2 emissions.")
                
                # When MECO occurs in GC, the consumed propellant should be within 1% of the total propellant mass of stage 1.  
                # The error is suppressed for 2020-F07, 2021-F01, and 2021-F07 where rockets failed early. 
                # Also suppressed for Falcon 9, as this has a reusable first stage.
                # A check that the Falcon landing distribution is no greater than 7% of the stage 1 emissions is undertaken later in the grid_emis function.
                if stage_alt_meco < 80:
                    if (launch_id[w] not in ['2020-F07','2021-F01','2021-F07']) and rocket_data.rocket_name[valid_index] != "Falcon 9 v1.2" and ((np.abs(self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) / rocket_data.stage1_prop_mass[valid_index] * 100) > 1):
                        print(launch_id[w],self.stage1_prop_consumed[self.launch_count],rocket_data.stage1_prop_mass[valid_index],(np.abs(self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) / rocket_data.stage1_prop_mass[valid_index] * 100))
                        sys.exit("Error with Stage 1 emissions - 2.")  
                        
                self.total_prop_consumed[pei_booster_index,0] += self.booster_prop_consumed[self.launch_count]
                self.total_prop_consumed[pei_stage1_index,1]  += self.stage1_prop_consumed[self.launch_count]
                self.total_prop_consumed[pei_stage2_index,2]  += self.stage2_prop_consumed[self.launch_count]                  

                total_prop_mass = b_prop + rocket_data.stage1_prop_mass[valid_index] + rocket_data.stage2_prop_mass[valid_index]
                total_prop_mass += rocket_data.stage3_prop_mass[valid_index] + rocket_data.stage4_prop_mass[valid_index]
                
                #percent_dis_b = b_prop / total_prop_mass * 100
                #percent_dis_s1 = rocket_data.stage1_prop_mass[valid_index] / total_prop_mass * 100
                #percent_dis_s2 = rocket_data.stage2_prop_mass[valid_index] / total_prop_mass * 100
                #percent_dis_s3 = rocket_data.stage3_prop_mass[valid_index] / total_prop_mass * 100
                #percent_dis_s4 = rocket_data.stage4_prop_mass[valid_index] / total_prop_mass * 100
                #print(f"% Distribution is {percent_dis_b:.0f} {percent_dis_s1:.0f} {percent_dis_s2:.0f} {percent_dis_s3:.0f} {percent_dis_s4:.0f}")
                
                ##############################################
                # Calculate the emissions for each species.
                ##############################################     
                
                # Creating a 2d array for the prop output.
                # Total prop, bc, co, nox, h2o, al2o3, cl, hcl, cl2
                total_vertical_propellant = np.zeros((len(self.mid_alt[:,q,p]),9))      
                                
                # Check whether there is a booster:
                if ( rocket_data.booster_prop_type[valid_index] != '' ):
                    if np.sum(1e-2 * self.gc_relative_mass_booster) > 1.01:
                        sys.exit("Error with Boosters. Propellant distribution exceeds unity.")
                        
                    total_vertical_propellant = self.calc_emis(self.booster_alt_index,
                                   None,
                                   pei_booster_index,
                                   b_prop,
                                   self.gc_relative_mass_booster,
                                   time_index, 
                                   q, 
                                   p, 
                                   kg_to_kgm2s,
                                   total_vertical_propellant)
                        
                # Every rocket has a first stage.
                if np.sum(1e-2 * self.gc_relative_mass_stage1) > 1.01:
                    sys.exit("Error with Stage 1. Propellant distribution exceeds unity.")
                   
                if rocket_data.rocket_name[valid_index] in ["LauncherOne","GSLV Mk III"]:
                    start_ind = None
                    stop_ind  = self.fei_alt_index-1  
                elif rocket_data.rocket_name[valid_index] == "Pegasus XL":
                    start_ind = self.MECO_alt_index
                    stop_ind  = self.fei_alt_index-1
                else:
                    start_ind = self.MECO_alt_index
                    stop_ind  = None 
                    
                total_vertical_propellant = self.calc_emis(start_ind,
                                stop_ind,
                                pei_stage1_index,
                                rocket_data.stage1_prop_mass[valid_index],
                                self.gc_relative_mass_stage1,
                                time_index, 
                                q, 
                                p, 
                                kg_to_kgm2s,
                                total_vertical_propellant)

                # Check whether there is a second stage:
                if rocket_data.stage2_prop_type[valid_index] != '' and self.SEI_alt_index != self.nlev:
                    if np.sum(1e-2 * self.gc_relative_mass_stage2) > 1.01:
                        sys.exit("Error with Stage 2. Propellant distribution exceeds unity.")
                        
                    if rocket_data.rocket_name[valid_index] in ["Minotaur 1"]:
                        start_ind = self.seco_alt_index
                        stop_ind  = self.SEI_alt_index-1
                    else:
                        start_ind = None
                        stop_ind  = self.SEI_alt_index-1
                                         
                    total_vertical_propellant = self.calc_emis(start_ind,
                                stop_ind,
                                pei_stage2_index,
                                rocket_data.stage2_prop_mass[valid_index],
                                self.gc_relative_mass_stage2,
                                time_index, 
                                q, 
                                p, 
                                kg_to_kgm2s,
                                total_vertical_propellant)
                    
                # Add third stage emissions for Minotaur 1.
                if rocket_data.rocket_name[valid_index] == "Minotaur 1":
                    if np.sum(1e-2 * self.gc_relative_mass_stage3) > 1.01:
                        sys.exit("Error with Stage 3 for Minotaur 1. Propellant distribution exceeds unity.")
                        
                    total_vertical_propellant = self.calc_emis(None,
                                self.TEI_alt_index-1,
                                pei_stage3_index,
                                rocket_data.stage3_prop_mass[valid_index],
                                self.gc_relative_mass_stage3,
                                time_index, 
                                q, 
                                p, 
                                kg_to_kgm2s,
                                total_vertical_propellant)    
                    
                # If the rocket is a Falcon 9, then add the landing emissions. Kerosene, so no Al2O3 or Cly.     
                if rocket_data.rocket_name[valid_index] in ["Falcon 9 v1.2","Falcon Heavy"] and self.include_landing == True:
                    if launch_id[w] in self.ground_landing_list:
                        falcon_p = p
                        falcon_q = q
                    else:
                        matching = self.ocean_landings[self.ocean_landings["Date"].isin([f"{self.year}-{self.strmon}-{self.strday}"])].reset_index(drop=True)
                        # There is a typo in the databse, a 2023 launch is listed as 2022.      
                        if (matching.shape[0] == 1) or (f"{self.year}-{self.strmon}-{self.strday}" == "2022-04-27"):
                            falcon_lat = np.array(matching["geometry"].y)[0]
                            falcon_lon = np.array(matching["geometry"].x)[0]
                            falcon_p, falcon_q = np.argmin(abs(falcon_lon-self.lon)), np.argmin(abs(falcon_lat-self.lat))
                        # There are two launches on the same day.
                        elif launch_id[w] == "2022-124":
                            falcon_lat = np.array(matching["geometry"].y)[0]
                            falcon_lon = np.array(matching["geometry"].x)[0]
                            falcon_p, falcon_q = np.argmin(abs(falcon_lon-self.lon)), np.argmin(abs(falcon_lat-self.lat))
                        elif launch_id[w] == "2022-125":
                            falcon_lat = np.array(matching["geometry"].y)[1]
                            falcon_lon = np.array(matching["geometry"].x)[1]
                            falcon_p, falcon_q = np.argmin(abs(falcon_lon-self.lon)), np.argmin(abs(falcon_lat-self.lat))
                        elif matching.shape[0] == 0:
                            # The database hasn't been well updated for 2022, so lets just fill in based on most common geolocation for all other 2020-2022 launches.
                            #print(f"Warning: problem geolocating Falcon Stage 1 landing for {launch_id[w]}.") 
                            if lon[w] == -81.0 and lat[w] == 28.5:
                                falcon_p = 21
                                falcon_q = 31
                            elif lon[w] == -120.6 and lat[w] == 34.7:
                                falcon_p = 12
                                falcon_q = 30
                            else:
                                sys.exit("Launch not from assigned site.")
                        elif matching.shape[0] > 1: 
                            sys.exit(f"Multiple ocean entries for Falcon Stage 1 landing for {launch_id[w]}.")
                        else:
                            sys.exit(f"Problem geolocating Falcon Stage 1 landing for {launch_id[w]}") 
                            
                        if falcon_p > self.pmax:
                            self.pmax = falcon_p
                            #print(f"Falcon9 stage 1 reentry longitude out of bounds for {launch_id[w]}. Updating bounds.")
                        if falcon_q > self.qmax:
                            self.qmax = falcon_q
                            #print(f"Falcon9 stage 1 reentry latitude out of bounds for {launch_id[w]}. Updating bounds.")                  
                    
                    if np.sum(self.gc_relative_mass_entry) + np.sum(self.gc_relative_mass_landing) > 7:
                        sys.exit("Error with Stage 1 Ocean Landing. Propellant distribution exceeds what is expected.")
                        
                    if rocket_data.rocket_name[valid_index] == "Falcon 9 v1.2":
                        pei = pei_stage1_index
                        prop_mass = rocket_data.stage1_prop_mass[valid_index]
                    elif rocket_data.rocket_name[valid_index] == "Falcon Heavy":
                        pei = pei_booster_index
                        prop_mass = rocket_data.booster_prop_mass[valid_index]
                        # NOTE: If this script is run for future years (2023), then check if the Falcon Heavy still lands both boosters and not core stage.
                    
                    # First the entry emissions.
                    total_vertical_propellant = self.calc_emis(self.entry_top,
                                self.entry_bot-1,
                                pei,
                                prop_mass,
                                self.gc_relative_mass_entry,
                                time_index, 
                                falcon_q, 
                                falcon_p, 
                                kg_to_kgm2s,
                                total_vertical_propellant)
                    
                    # Now the landing emissions.
                    total_vertical_propellant = self.calc_emis(self.landing_top,
                                None,
                                pei,
                                prop_mass,
                                self.gc_relative_mass_landing,
                                time_index, 
                                falcon_q, 
                                falcon_p, 
                                kg_to_kgm2s,
                                total_vertical_propellant)
                  
                # Calculate the missing emissions from above GEOS-Chem.
                # Check if there are missing emissions from the first stage.
                if rocket_data.stage1_prop_type[valid_index] != '' and 100 - np.sum(self.gc_relative_mass_stage1) > 0 and launch_id[w] not in ['2020-F04','2020-F07','2020-F11',
                                                                                                                                               '2021-F01','2021-F07']:
                    if 100 - np.sum(self.gc_relative_mass_stage1) > 100:
                        sys.exit("Error with Stage 1 emissions above GEOS-Chem.") 
                    self.calc_missing_emis(pei_stage1_index,
                        rocket_data.stage1_prop_mass[valid_index],
                        100 - np.sum(self.gc_relative_mass_stage1) - np.sum(self.gc_relative_mass_entry) - np.sum(self.gc_relative_mass_landing),                    
                        )
                    
                # Check if there are missing emissions from the second stage.
                if rocket_data.stage2_prop_type[valid_index] != '' and 100 - np.sum(self.gc_relative_mass_stage2) > 0 and launch_id[w] not in ['2020-F02','2020-F04','2020-F05','2020-F07','2020-F11',
                                                                                                                                               '2021-F01','2021-F02','2021-F07','2021-F08',
                                                                                                                                               '2022-F01','2022-F02']:
                    if 100 - np.sum(self.gc_relative_mass_stage2) > 100:
                        sys.exit("Error with Stage 2 emissions above GEOS-Chem.") 
                    
                    if launch_id[w] == "2022-F03":
                        total_emis = 240/315*100
                    else:
                        total_emis = 100
                        
                    self.calc_missing_emis(pei_stage2_index,
                        rocket_data.stage2_prop_mass[valid_index],
                        total_emis - np.sum(self.gc_relative_mass_stage2),                    
                        )
                    
                # Check if there are missing emissions from the third stage.
                if rocket_data.stage3_prop_type[valid_index] != '' and launch_id[w] not in ['2020-F02','2020-F03','2020-F05','2020-F06','2020-F11',
                                                                                            '2021-F01','2021-F06','2021-F10',
                                                                                            '2022-F02','2022-F05','2022-F07']:
                    if launch_id[w] == "2021-F09":
                        included_emis = 475/521*100
                    elif rocket_data.rocket_name[valid_index] == "Minotaur 1":
                        included_emis = 100 - np.sum(self.gc_relative_mass_stage3)
                    else:
                        included_emis = 100
                        
                    self.calc_missing_emis(pei_stage3_index,
                        rocket_data.stage3_prop_mass[valid_index],
                        included_emis,                    
                        )
                
                # Check if there are missing emissions from the fourth stage.
                if rocket_data.stage4_prop_type[valid_index] != '' and launch_id[w][-3:] not in ['2020-F08','2020-F09','2020-F11',
                                                                                                 '2021-F01',
                                                                                                 '2022-F02','2022-F04','2022-F05','2022-F07']:
                    self.calc_missing_emis(pei_stage4_index,
                        rocket_data.stage4_prop_mass[valid_index],
                        100,                    
                        )
                
                ##############################################
                # Output the emissions to a file for viewing.
                ##############################################                  
        
                total_vertical_propellant[:,0] = total_vertical_propellant[:,0] / total_prop_mass
                self.output_for_csv[self.csv_count,:] = total_vertical_propellant[:,0]
                self.csv_count += 1
                self.output_for_csv[self.csv_count,:] = self.mid_alt[:,q,p]*1e-3
                self.csv_count += 1  
                self.output_for_csv[self.csv_count,:] = self.gc_relative_mass[::-1]
                self.csv_count += 1 
                
                if np.sum(self.gc_relative_mass[::-1]) == 0 and np.sum(total_vertical_propellant[:,0]) == 0:
                    print(rocket_data.rocket_name[valid_index])
                
                for i in range(1,9):
                    self.output_for_csv_2[self.csv_count_2,:] = total_vertical_propellant[:,i]
                    self.csv_count_2 += 1 

                self.launch_count += 1
                
            #########################################################
            # Work out vertical distribution for reentry emissions.
            #########################################################
            
            if emis_type=='reentry':              
                
                # Al2O3 emissions calculated using ablation and alumina content data from literature.
                # Different emissions for core stage / upper stage / payload. 
                # https://www.sciencedirect.com/science/article/pii/B0122274105008887
                # "Fairings are typically made of aluminum or composite materials."
                # Fairings treated as a core stage, except for Falcon 9 which are recovered intact.

                # Complete burnup on re-entry.
                if rocket_data.reentry_burnup[index[w]] == 'Complete': 
                    nox_burnup_factor = 1                                   # NOx emissions of 100% of reentering mass.
                    if (rocket_data.reentry_stage[index[w]] in [0,1]):
                        al_burnup_factor = 0.3 * 0.7  # https://doi.org/10.1016/j.asr.2020.10.036 (70% survivability) and https://hdl.handle.net/1721.1/151393 (70% Al)
                    elif "fairing" in rocket_data.reentry_name[index[w]].lower(): 
                        al_burnup_factor = 0.3 * 0.7  # https://doi.org/10.1016/j.asr.2020.10.036 (70% survivability) and https://hdl.handle.net/1721.1/151393 (70% Al)
                    elif rocket_data.reentry_stage[index[w]] in [2,3,4]:
                        al_burnup_factor = 0.65 * 0.7 # https://doi.org/10.1016/j.asr.2020.10.036 (35% survivability) and https://hdl.handle.net/1721.1/151393 (70% Al)
                    elif rocket_data.reentry_stage[index[w]] == 5:
                        if rocket_data.reentry_mcs[index[w]] == True:
                            al_burnup_factor = 0.4       # https://doi.org/10.1016/j.asr.2020.10.036 (0% survivability, 40% Al)
                        else:
                            al_burnup_factor = 0.4 * 0.8 # https://doi.org/10.1016/j.asr.2020.10.036 (20% survivability, 40% Al)
                    else:
                        al_burnup_factor = 0
                        
                # Partial burnup on re-entry - reusable capsules and Falcon 9 1st stage / fairings:
                # Still using the 17.5% value for NOx emissions.
                # For Al2O3, we assume no emissions from reusuable components.
                else: 
                    if rocket_data.reentry_stage[index[w]] not in [1,5]:
                        print("Reusuable reentry not payload or 1st stage.") 
                    al_burnup_factor = 0
                    nox_burnup_factor = 0.175
                 
                # For consistency with launch emissions, the totals are kept in g units. 
                           
                t_nox_reentry = (rocket_data.reentry_al_mass[index[w]] + rocket_data.reentry_non_al_mass[index[w]]) * nox_burnup_factor * 1000
                self.nox_reentry_total += t_nox_reentry
                self.rocket_reentry_nox[time_index,self.bot_reenter:self.top_reenter+1,q,p] += t_nox_reentry / self.n_reenter_levs * 1e-3 / kg_to_kgm2s
                
                t_al2o3_reentry = rocket_data.reentry_al_mass[index[w]] * al_burnup_factor * 1000
                self.al2o3_reentry_total += t_al2o3_reentry
                self.rocket_reentry_al[time_index,self.bot_reenter:self.top_reenter+1,q,p] += t_al2o3_reentry / self.n_reenter_levs * 1e-3 / kg_to_kgm2s
                
                total_vertical_propellant = np.zeros((len(self.mid_alt[:,q,p]),9))    
                total_vertical_propellant[self.bot_reenter:self.top_reenter+1,3]   += [t_nox_reentry/2, t_nox_reentry/2]
                total_vertical_propellant[self.bot_reenter:self.top_reenter+1,5]   += [t_al2o3_reentry/2, t_al2o3_reentry/2]
                
                self.output_for_csv[self.csv_count,:] = 0
                self.csv_count += 1
                self.output_for_csv[self.csv_count,:] = self.mid_alt[:,q,p]*1e-3
                self.csv_count += 1  
                self.output_for_csv[self.csv_count,:] = 0
                self.csv_count += 1 
                
                for i in range(1,9):
                    self.output_for_csv_2[self.csv_count_2,:] = total_vertical_propellant[:,i]
                    self.csv_count_2 += 1
                     
    def save_netcdf(self):
        """Save rocket emissions as COARDS compliant NetCDF files"""
        
        ###################
        # Set up range.
        ###################
        # Change (shift) indices on edges of grid:
        if self.pmin==0: self.pmin=1
        if self.pmax==0: self.pmax=1
        if self.pmax==self.nlon: self.pmax=self.nlon-1
        
        if self.qmin==0: self.qmin=1
        if self.qmin-1==0: self.qmin=1
        if self.qmax==0: self.qmax=1
        if self.qmax==self.nlat: self.qmax=self.nlat-1
        
        emis_initial =    np.sum(self.rocket_launch_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_fuel_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_reentry_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_h2o[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_bc[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_co[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_launch_al[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_reentry_al[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_hcl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_cl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                        + np.sum(self.rocket_cl2[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                                                
        updated_coords = False
        if (self.qmax+2)>=self.nlat:
            print('Latitude index out of bounds: updating')  
            updated_coords = True
            if ( self.qmax==self.qmin ):
                self.qmax,self.qmin=self.nlat-2,self.nlat-2
            else:
                self.qmax=self.nlat-2  
                          
        if (self.pmax+2)>=self.nlon:
            print('Longitude index out of bounds: updating')
            updated_coords = True
            if ( self.pmax==self.pmin ):
                self.pmax,self.pmin=self.nlon-2,self.nlon-2
            else:
                self.pmax=self.nlon-2   
        
        if updated_coords == True: 
            # H2O is different by e-27 (e-14 % diff), must be a rounding error.  
            emis_final =    np.sum(self.rocket_launch_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_fuel_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_reentry_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_h2o[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_bc[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_co[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_launch_al[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_reentry_al[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_hcl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_cl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                            + np.sum(self.rocket_cl2[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]) \
                                                            
            print(f'{emis_initial:.2e},{emis_final:.2e}') 
            if np.abs(emis_initial-emis_final) / emis_initial * 100 > 0.000001:
                sys.exit('Error: index correction removes relevant data')                

        # Check that output range isn't out-of-bounds:
        if self.qmin-1<0 or self.pmin-1<0:
            print('index is less than 0')
        if self.qmax+1>self.nlat:
            print('lat index exceeds no. of lats')
        if self.pmax+1>self.nlon:
            print('lon index exceeds no. of lons')

        #print("3)", self.qmin,self.qmax)
        ########################################
        # Open Dataset and set up dimensions.
        ########################################
        
        # define dataset:
        ncout = Dataset(self.outfile_rocket_emis, mode='w', format='NETCDF4')

        # Set dimensions (lat, lon, time, lev):
        # Lat and lon data are trimmed to just where the launch occurs.
        #print(self.qmax,self.qmin,self.qmax-self.qmin+3)
        ncout.createDimension('lat', self.qmax-self.qmin+3)
        ncout.createDimension('lon', self.pmax-self.pmin+3)
        ncout.createDimension('lev', self.nlev)
        ncout.createDimension('time', self.nhours)
        #ncout.createDimension('time', self.nhours*3)
        
        ######################################
        # Create variables for the dimensions.
        ######################################

        # Create individual variables:
        # Time:
        time = ncout.createVariable('time', np.int64, ('time',))
        time.long_name = 'time'
        time.units = 'hours since 2020-'+self.strmon+'-'+self.strday+' 00:00:00'
        #time.units = 'seconds since 2020-'+self.strmon+'-'+self.strday+' 00:00:00'
        time.calendar = 'standard'
        time.axis = 'T'
        time[:] = np.arange(0,self.nhours)
        #time[:] = np.arange(0,self.nhours*3600,1200)

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
        lat.axis = 'Y'
        #print(len(lat[:]),len(self.lat[self.qmin-1:self.qmax+2]))
        #print(self.lat[self.qmin-1:self.qmax+2])
        lat[:] = self.lat[self.qmin-1:self.qmax+2]
        
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

        # (1a) Launch NOx (default emitted as NO):
        rocket_launch_nox = ncout.createVariable('rocket_launch_nox', np.float32, ('time','lev','lat','lon',))
        rocket_launch_nox.long_name = 'Rocket NOx emissions from secondary thermal heating during launch'
        rocket_launch_nox.short_name = 'Thermal Launch Rocket NOx emissions'
        rocket_launch_nox.units = 'kg/m2/s'
        rocket_launch_nox[:] = self.rocket_launch_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]
        
        # (1b) Fuel NOx (default emitted as NO2):
        rocket_fuel_nox = ncout.createVariable('rocket_fuel_nox', np.float32, ('time','lev','lat','lon',))
        rocket_fuel_nox.long_name = 'Rocket NOx emissions from primary combustion of fuel during launch'
        rocket_fuel_nox.short_name = 'Fuel Launch Rocket NOx emissions'
        rocket_fuel_nox.units = 'kg/m2/s'
        rocket_fuel_nox[:] = self.rocket_fuel_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]
        
        # (1c) Reentry NOx (default emitted as NO):
        rocket_reentry_nox = ncout.createVariable('rocket_reentry_nox', np.float32, ('time','lev','lat','lon',))
        rocket_reentry_nox.long_name = 'Rocket NOx emissions from thermal heating during reentry'
        rocket_reentry_nox.short_name = 'Thermal Reentry Rocket NOx emissions'
        rocket_reentry_nox.units = 'kg/m2/s'
        rocket_reentry_nox[:] = self.rocket_reentry_nox[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

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

        # (4a) Launch Alumina:
        rocket_launch_al = ncout.createVariable('rocket_launch_al', np.float32, ('time','lev','lat','lon',))
        rocket_launch_al.long_name = 'Rocket alumina emissions from launch'
        rocket_launch_al.short_name = 'Rocket alumina emissions from launch'
        rocket_launch_al.units = 'kg/m2/s'
        rocket_launch_al[:] = self.rocket_launch_al[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]
        
        # (4b) Reentry Alumina:
        rocket_reentry_al = ncout.createVariable('rocket_reentry_al', np.float32, ('time','lev','lat','lon',))
        rocket_reentry_al.long_name = 'Rocket alumina emissions from reentry'
        rocket_reentry_al.short_name = 'Rocket alumina emissions from reentry'
        rocket_reentry_al.units = 'kg/m2/s'
        rocket_reentry_al[:] = self.rocket_reentry_al[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (5a) HCl:
        rocket_hcl = ncout.createVariable('rocket_hcl', np.float32, ('time','lev','lat','lon',))
        rocket_hcl.long_name = 'Rocket HCl emissions'
        rocket_hcl.short_name = 'Rocket HCl emissions'
        rocket_hcl.units = 'kg/m2/s'
        rocket_hcl[:] = self.rocket_hcl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (5b) Cl:
        rocket_cl = ncout.createVariable('rocket_cl', np.float32, ('time','lev','lat','lon',))
        rocket_cl.long_name = 'Rocket Cl emissions'
        rocket_cl.short_name = 'Rocket Cl emissions'
        rocket_cl.units = 'kg/m2/s'
        rocket_cl[:] = self.rocket_cl[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]
        
        # (5c) Cl2:
        rocket_cl2 = ncout.createVariable('rocket_cl2', np.float32, ('time','lev','lat','lon',))
        rocket_cl2.long_name = 'Rocket Cl2 emissions'
        rocket_cl2.short_name = 'Rocket Cl2 emissions'
        rocket_cl2.units = 'kg/m2/s'
        rocket_cl2[:] = self.rocket_cl2[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2]

        # (6) CO:
        rocket_co = ncout.createVariable('rocket_co', np.float32, ('time','lev','lat','lon',))
        rocket_co.long_name = 'Rocket CO emissions'
        rocket_co.short_name = 'Rocket CO emissions'
        rocket_co.units = 'kg/m2/s'
        rocket_co[:] = self.rocket_co[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2] 

        # Close the file:
        ncout.close()

def check_total_emissions(year,dataset):
    """ Print total emissions of each species.
        The total emissions including all afterburning are compared to a scenario where only primary emission indices are used.
    """    
    
    # This code adds the pei estimates.
    #estimated_bc, estimated_nox, estimated_h2o, estimated_co, estimated_al2o3, estimated_hcl, estimated_cl, estimated_cl2 = 0, 0, 0, 0, 0, 0, 0, 0
    #for i in range(4):
    #    for j in range(3):
    #        estimated_bc += emis_data.total_prop_consumed[i,j]  * rocket_data.bc_pei[i]
    #        estimated_nox += emis_data.total_prop_consumed[i,j] * rocket_data.nox_pei[i]
    #        estimated_h2o += emis_data.total_prop_consumed[i,j]  * rocket_data.h2o_pei[i]
    #        estimated_co += emis_data.total_prop_consumed[i,j]  * rocket_data.co_pei[i]
    #        estimated_al2o3 += emis_data.total_prop_consumed[i,j]  * rocket_data.al2o3_pei[i]
    #        estimated_hcl += emis_data.total_prop_consumed[i,j]  * rocket_data.cly_pei[i]
    #        estimated_cl += emis_data.total_prop_consumed[i,j]  * 0
    #        estimated_cl2 += emis_data.total_prop_consumed[i,j]  * 0
    
    total_missing_emis = np.sum(emis_data.missing_emis)*1e-9 
    total_inc_emis = np.sum([emis_data.bc_total*1e-9, emis_data.nox_launch_total*1e-9,   emis_data.h2o_total*1e-9, 
                                    emis_data.co_total*1e-9, emis_data.al2o3_launch_total*1e-9, emis_data.hcl_total*1e-9, 
                                    emis_data.cl_total*1e-9, emis_data.cl2_total*1e-9, emis_data.nox_reentry_total*1e-9, 
                                    emis_data.al2o3_reentry_total*1e-9])
    percent_missing_emis = total_missing_emis / (total_inc_emis + total_missing_emis) * 100
    percent_inc_emis = total_inc_emis / (total_inc_emis + total_missing_emis) * 100
    
    total_missing_prop = np.sum(emis_data.missing_prop)*1e-6
    total_inc_prop = np.sum(emis_data.included_prop)*1e-6
    percent_missing_prop = total_missing_prop / (total_inc_prop + total_missing_prop) * 100
    percent_inc_prop = total_inc_prop / (total_inc_prop + total_missing_prop) * 100
                   
    data = {'Species'        : ['BC', 'NOx (Launch)', 'H2O', 'CO', 'Al2O3 (Launch)', 'HCl', 'Cl', 'Cl2', 'NOx (Reentry)', 'Al2O3 (Reentry)',
                                'Total Emis', 'Total Percent Emis','Total Prop', 'Total Percent Prop'],
            #'PEI Estimate'   : [estimated_bc*1e-9, estimated_nox*1e-9, estimated_h2o*1e-9, estimated_co*1e-9, 
            #                    estimated_al2o3*1e-9, estimated_hcl*1e-9, estimated_cl*1e-9, estimated_cl2*1e-9, 0, 0],
            'Included Emissions / Gg': [emis_data.bc_total*1e-9, emis_data.nox_launch_total*1e-9,   emis_data.h2o_total*1e-9, 
                                        emis_data.co_total*1e-9, emis_data.al2o3_launch_total*1e-9, emis_data.hcl_total*1e-9, 
                                        emis_data.cl_total*1e-9, emis_data.cl2_total*1e-9, emis_data.nox_reentry_total*1e-9, 
                                        emis_data.al2o3_reentry_total*1e-9, total_inc_emis, percent_inc_emis, total_inc_prop, percent_inc_prop],
            'Missing Emissions / g': [emis_data.missing_emis[0] * 1e-9, emis_data.missing_emis[2] * 1e-9, emis_data.missing_emis[3] * 1e-9, 
                                        emis_data.missing_emis[1] * 1e-9, emis_data.missing_emis[4] * 1e-9, emis_data.missing_emis[5] * 1e-9,
                                        emis_data.missing_emis[6] * 1e-9, emis_data.missing_emis[7] * 1e-9, 0, 0, 
                                        total_missing_emis,percent_missing_emis, total_missing_prop, percent_missing_prop]}
    df = pd.DataFrame(data)
    print(df.round(2))    
    if dataset == 3:
        df.to_csv(f".\Emission_Output\EmissionTotals_{year}.csv",sep=',')
    else:
        df.to_csv(f".\Emission_Output\EmissionTotals_{year}_{dataset}.csv",sep=',')
    print(emis_data.total_landing_prop * 1e-6 / (total_inc_prop + total_missing_prop) * 100)
    
# Main section of the program
if __name__ == "__main__":

    # Configure additional arguments when running the script.

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', "--levels", default="47", choices=["47", "72"], help="Vertical resolution.")
    parser.add_argument('-g', "--grid_res", default = "4x5", choices=["4x5", "2x2.5"], help='Grid resolution.')
    parser.add_argument('-sm', "--start_month", default = "1", choices=str(np.arange(1,13)), help='Start Month (will override final month if greater than final month).')
    parser.add_argument('-fm', "--final_month", default = "12", choices=str(np.arange(1,13)), help='Final Month.')
    parser.add_argument('-d', "--dataset", default = "3", choices=str(np.arange(1,4)), help='Dataset. 1=Non-SMC, 2=SMC, 3=All')
    parser.add_argument('-sy', "--start_year", default = "2020", choices=str(np.arange(2020,2023)), help='Start Year.')
    parser.add_argument('-fy', "--final_year", default = "2020", choices=str(np.arange(2020,2023)), help='Final Year.')
    args = parser.parse_args()

    # Sort out the year range.
    start_year = int(args.start_year)
    final_year = int(args.final_year)
    if start_year > final_year:
        final_year = start_year + 1
    print(f"Processing from year {start_year} to {final_year}.")
    year_range = np.arange(start_year,final_year+1)  
    
    # Import the Falcon landing data.
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    raul_data = gpd.read_file('./Databases/General_SpaceX_Map_Raul.kml', driver='KML', layer =2)
      
    #### Define booster and re-entry levels.
    
    # In 2019, boosters set to extend to ~45 km (layer 44 of the 47-layer model, layer 57 of the 72-layer model).
    # In updated model, the actual BECO, MECO and SEI values are used wherever possible. 

    stage_alt_dict = {}
    stage_alt_rockets = np.genfromtxt("./Databases/Stage_Altitudes.csv",dtype=str,skip_header=1,usecols=[0],delimiter=",")
    stage_alt_data = np.genfromtxt("./Databases/Stage_Altitudes.csv",dtype=np.float64,skip_header=1,usecols=[1,2,3,4],delimiter=",")
    for i in range(len(stage_alt_data)):
        if stage_alt_data[i][0] == '':
            stage_alt_dict[f"{stage_alt_rockets[i]} BECO"] = None
        else:
            stage_alt_dict[f"{stage_alt_rockets[i]} BECO"] = np.float64(stage_alt_data[i][0])
        if stage_alt_data[i][1] == '':
            stage_alt_dict[f"{stage_alt_rockets[i]} MECO"] = None
        else:
            stage_alt_dict[f"{stage_alt_rockets[i]} MECO"] = np.float64(stage_alt_data[i][1])
        if stage_alt_data[i][2] == '':
            stage_alt_dict[f"{stage_alt_rockets[i]} SEI1"] = None
        else:
            stage_alt_dict[f"{stage_alt_rockets[i]} SEI1"] =  np.float64(stage_alt_data[i][2])
    
    # B+1/2S B+3S B+4S 2S 3S 4S    
    booster_cutoff_alts = [66,55,29,0,0,0]
    MECO_alts           = [220,120,64,90,56,52]
    SEI_alts            = [229,120,64,103,61,59]
    
    # N.B. Re-entry emissions are placed in the GC layer at ~68 km (reentry burnup location).
    # The emissions are evenly distributed across two vertical layers in the model.
    # 46-47 for the 47-layer model, 65-72 for the 72-layer model (equivalent to 60-80 km).
    # This means greater smoothing for the 47-layer model.
    
    # All indices have been subtracted by 1 to account for python indexing.
    levels = int(args.levels)
    if levels==47:
        reentry_levs = [45,46] 
    elif levels==72:
        reentry_levs = [64,71]
    else:
        sys.exit("Invalid number of levels.")
        
    ground_landing_list = ["2020-016","2020-059","2020-086","2020-101", "2021-059", "2022-002","2022-008","2022-009",
                           "2022-040","2022-057","2022-063","2022-144","2022-166","2022-168","2022-173","2022-179"]
        
    ''' Define resolutions and set timings '''
    
    # Define timesteps.
    grid_res = args.grid_res
    if grid_res == '2x2.5': 
        timestep = 3600 #sec
    elif grid_res == '4x5':
        timestep = 3600 #sec
    else:
        sys.exit("Invalid grid resolution.")

    ''' Define locations of StateMet files '''
    
    # Define paths dependent on resolution and levels. Errors should be handled above but included here just in case.
    # Can't use ~ for home directory, have to use '/home/ucfacb0/<path>'
    if grid_res == '4x5':
        if levels == 72:
            pass
            #gcdir = '/home/ucfacb0/uptrop/GC/run_12.9.3_72L/methane_fluxes/merra2_4x5_og/StateMet/'
        elif levels == 47:
            gcdir = '/home/ucfacb0/rundirs/StateMet_Runs/gc_4x5_47L_merra2_nochem_StateMet/StateMet'
        else:
            sys.exit("Invalid number of levels.")
    elif grid_res == '2x2.5':
        if levels == 72:
            gcdir = '/home/ucfacb0/rundirs/StateMet_Runs/gc_2x25_72L_merra2_nochem_StateMet/StateMet/'
            #gcdir = '/home/ucfacb0/uptrop/GC/run_12.9.3_72L/methane_fluxes/merra2_2x25_og/StateMet'
        elif levels == 47:
            pass
        else:
            sys.exit("Invalid number of levels.")
    else:
        sys.exit("Invalid grid resolution.")
        # For different resolutions, would first need to run GEOS-Chem to get StateMet files.
        
    start_month = int(args.start_month)
    final_month = int(args.final_month)
    if start_month > final_month:
        final_month = start_month + 1
    print(f"Processing from month {start_month} to {final_month}.")
    months = np.arange(start_month-1,final_month)    
    
    #Loop over all years and run functions depending on input arguments.
    for year in year_range:

        # Read the rocket emissions from the database.
        datadir = './Databases/'
        launch_path          = path.join(datadir, f'launch_info_{year}.nc')
        if year == 2020:
            reentry_path     = path.join(datadir, f'reentry_info_{year}_jcat_test.nc')
        elif year == 2021:
            reentry_path     = path.join(datadir, f'reentry_info_{year}_jcat_test.nc')
        elif year == 2022:
            reentry_path     = path.join(datadir, f'reentry_info_{year}_jcat_test.nc')
        else:
            reentry_path     = ""
        rocket_info_path = path.join(datadir, f'rocket_info_{year}.nc')
        pei_path         = path.join(datadir, 'PEI_info.csv')
        outdir = f'./Output/{year}/'    
        rocket_data = RocketData(launch_path, reentry_path, rocket_info_path, pei_path)
    
        # Go through process of gridding and saving rocket emissions:
        emis_data = OutputEmis(rocket_data, 
                            grid_res, 
                            timestep, 
                            levels, 
                            booster_cutoff_alts, 
                            MECO_alts, 
                            SEI_alts, 
                            reentry_levs, 
                            gcdir, 
                            months,
                            int(args.dataset),
                            year,
                            ground_landing_list,
                            stage_alt_dict
                            )

        check_total_emissions(year,int(args.dataset))