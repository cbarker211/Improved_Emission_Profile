#!/usr/bin/python

'''Save out rocket emissions as COARDS compliant files for input to 
   HEMCO/GEOS-Chem. '''
   

# TODO: Add a comment about what files are input.

# Import relevant packages:
import argparse
import sys
import os
from os import path
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from OutputEmis_Functions import make_grid_LL, read_gc_box_height, get_ross_profiles, interp_prop_mass
from atmos_pressure import print_pressures

class RocketData:
    '''Read rocket launch and re-entry emissions'''
    def __init__(self,launchfile,reentryfile, rocketinfofile):
        
        self.read_launch_emissions(launchfile)
        self.read_reentry_emissions(reentryfile)
        self.define_scale_factors()
        self.read_rocket_info(rocketinfofile)
        self.define_pei()
    
    def read_launch_emissions(self, launchfile):
        ###########################################
        # Read launch emissions from the database.
        ###########################################
        
        #Open Dataset.
        fh = Dataset(launchfile, mode='r')
        
        #Extract variables.
        self.launch_lons = fh.variables['Longitude'][:]
        self.launch_lats = fh.variables['Latitude'][:]
        self.launch_time = fh.variables['Time(UTC)'][:]  # UTC hours
        self.launch_month = fh.variables['Month'][:]
        self.launch_day = fh.variables['Day'][:]
        self.launch_id = fh.variables['COSPAR_ID'][:]
        self.launch_rocket = fh.variables['Rocket_Type'][:]
        
        print("Successfully loaded launch information.")
        
        # Previously, the emissions for each rocket launch were calculated elsewhere.
        # The values were then loaded in to check for any inconsistencies. 
        # However, now all the emission calculations are done here.
        # Therefore, the sanity check is replaced with a variety of other functions elsewhere.
        
        #Close Dataset.
        fh.close()
        
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
        
        # TODO: Reentries.
        # Sort this sanity check out when reentries have been dealt with.
        if args.verbose == True:
            print(f'Total reentry NOx emissions             = {sum(self.reentry_nox)*1e-3} tonnes')
        
        # TODO: Reentries.
        # Need to sort out controlled vs uncontrolled entries.
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
        # This was original added by Eloise to manually regrid Ross2014 to GEOSChem. Now automatically doing this in interp_prop_mass
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
        
        # Importing these for use in determining rocket configuration.  
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
    
    def define_pei(self):
        
        #Define the primary emission indices here, instead of loading from file.
        # Each array should contain 4 values, corresponding to the emission index for :
        #       Hypergolic, Kerosene, Solid, Hydrogen
        # Each variable must be a numpy array in order to make the np.where routine work later.
        self.pei_fuel_type     = np.array(['Hypergolic', 'Kerosene', 'Solid', 'Hydrogen'])
        
        #Previous values.
        #self.h2_pei            = np.array([4, 12, 27, 35])
        #self.h2o_pei           = np.array([290, 263, 71, 965.])
        #self.cl_pei            = np.array([0, 0, 5, 0])
        #self.hcl_pei           = np.array([0, 0, 209, 0])
        #self.al2o3_pei         = np.array([0, 0, 358, 0])
        #self.bc_pei            = np.array([25, 25, 25, 0])
        #self.co_pei            = np.array([69, 372, 228, 0])
        #self.co2_pei           = np.array([289, 350, 18, 0])
        
        #New values.
        pei_file = pd.read_csv("/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/Databases/PEI_info_2020.csv")

        self.h2o_pei   = pei_file["H2O"].to_numpy()
        self.h2_pei    = pei_file["H2"].to_numpy()          
        self.co_pei    = pei_file["CO"].to_numpy()
        self.co2_pei   = pei_file["CO2"].to_numpy()
        self.bc_pei    = pei_file["BC"].to_numpy()
        self.nox_pei   = pei_file["NOx"].to_numpy()
        self.al2o3_pei = pei_file["Al2O3"].to_numpy()
        self.cly_pei   = pei_file["Cly"].to_numpy()
        
        print("Successfully loaded PEI information.")
              
class OutputEmis:
    def __init__(self, rocketdata, res, ts, levs, booster_levs, meco_levs, sei_levs, reentry_levs, gc_dir, months):

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
        self.errorcount = 0
        self.include_landing = False
        
        # Define Molecular Weights:
        self.mw_h   = 1.008
        self.mw_h2  = self.mw_h * 2
        self.mw_h2o = self.mw_h2 + 16.00

        # Get Ross vertical profiles of propellant burned:
        #   self.ross_alt (centre alitiudes of each bin)
        #   self.ross_prop_mass (unitless percent of propellant mass)
        self.ross_alt, self.ross_prop_mass, self.ross_cumulative_mass = get_ross_profiles()

        # Create variables for totals for a future sanity check:
        self.nox_launch_total = 0.0
        self.bc_total  = 0.0
        self.h2o_total = 0.0
        self.co_total = 0.0
        self.al2o3_launch_total = 0.0
        self.cl_total = 0.0
        self.hcl_total = 0.0
        self.cl2_total = 0.0
        self.nox_reentry_total = 0.0
        self.al2o3_reentry_total = 0.0
        self.booster_prop_consumed = np.zeros(len(self.launch_id))
        self.stage1_prop_consumed = np.zeros(len(self.launch_id))
        self.stage2_prop_consumed = np.zeros(len(self.launch_id))
        self.total_prop_consumed = np.zeros((4,3))
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
        
        # Trim the rocket names in the propellant mass database. This was added in 2019 script.
        # Eloise said this may have been to do with condensing the names from Chloe's excel file?
        # Have commented out, and now the program will use the full rocket name to find the specific launch vehicle.
        #self.trim_name = [elem[0:5] for elem in rocket_data.rocket_name]
        
        self.output_for_csv = np.zeros((len(rocket_data.launch_id)*3,self.nlev))
        self.csv_count = 0
        self.output_for_csv_2 = np.zeros((len(rocket_data.launch_id)*8,self.nlev))
        self.csv_count_2 = 0
        
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
            #for d in range(0,1):
            
            #Loop over all days:
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
                self.box_height, self.area, self.bot_alt, self.mid_alt, self.top_alt = read_gc_box_height(self.gc_file,self.nlev)
                
                # Set up the data arrays which will be saved to file.
                #self.reentry_nox = np.zeros((self.nlon,self.nlat,self.nlev))
                self.rocket_nox = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_h2o = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_bc = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_co = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_al = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_hcl = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_cl = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))
                self.rocket_cl2 = np.zeros((self.nhours,self.nlev,self.nlat,self.nlon))

                # Initialize:
                self.pmin,self.pmax=np.nan,np.nan
                self.qmin,self.qmax=np.nan,np.nan

                # Define output file name for this day:
                self.outfile_rocket_emis = path.join(outdir,self.strmon,f'ROCKET_EMIS_{res}_{str(self.nlev)}L_2020{self.strmon}{self.strday}.nc4')
                #print(f'Output to: {self.outfile_rocket_emis}')
                
                ########################################################################
                # Call grid_emis function to calculate distribution from launches
                ########################################################################
                
                l_ind=np.where((rocket_data.launch_month==(m+1))&(rocket_data.launch_day==(d+1))&(~np.isnan(rocket_data.launch_time)))[0]
                
                if len(l_ind)>0:
                    print('----> Day processing: ',self.strday,f"{len(l_ind)} Launches.")
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
                                   ' ',
                                   d,
                                   m,
                                   )
                    
                    # Sum up all re-entry NOx (kg):
                    #self.nox_reentry_total += sum(rocket_data.reentry_nox[r_ind])

                ####################################
                # Save file as NetCDF
                ####################################
                
                if len(l_ind)>0 or len(r_ind)>0:
                    # If there are launches, then save file normally.
                    self.save_netcdf()
                else:
                    # If there are no launches, create a dummy file to accommodate HEMCO file reading.
                    lat_ind=np.argmin(abs(self.lat-0))
                    self.qmin,self.qmax=int(lat_ind),int(lat_ind)
                    lon_ind=np.argmin(abs(self.lon-0))
                    self.pmin,self.pmax=int(lon_ind),int(lon_ind)
                    
                    self.save_netcdf()
        
        df = pd.DataFrame(self.output_for_csv)
        df.to_csv("/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/Databases/Propellant_Distribution.csv", float_format='%.3f')
        df_2 = pd.DataFrame(self.output_for_csv_2)
        df_2.to_csv("/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/Databases/Species_Distribution.csv", float_format='%.3f')
             
    def calculate_bc_ei(self, height, bc_pei):
        """Calculate BC emission index in g BC per kg propellant burned.
           No emissions for hydrogen-based fuels.
           From James2021."""
        self.ei_bc = np.zeros_like(height)

        for i, h in enumerate(height):
            self.ei_bc[i] = bc_pei * (max(0.04, (min(1, (0.04*(np.exp(0.12*(h-15))))))))

    def calculate_nox_ei(self, height, nox_pei):
        """Calculate NOx emission index in g NOx per kg propellant burned. 
           Secondary for all rockets, primary for hypergolic and solid only.
           From James2021."""
        self.ei_sec_nox = np.zeros_like(height)

        for i, h in enumerate(height):
            self.ei_sec_nox[i] = nox_pei + 33 * np.exp((-0.26)*h) 

    def calculate_co_ei(self, height, co_pei, co2_pei):
        """Calculate CO emission index in g CO per kg propellant burned.
           From James2021."""
        self.ei_co = np.zeros_like(height)

        for i, h in enumerate(height):
            self.ei_co[i] = min(co_pei, 0.0025*np.exp(0.067*h)*(co2_pei + co_pei))
                
    def calculate_cl_ei_old(self, height, cly_pei):
        """Calculate emission indices for all chlorine species in g per kg propellant burned.
           Using data from Gomberg, Zittel and Leone, refs originally obtained from James2021."""
        
        lit_alt = np.asarray([0.7, 6, 10, 15, 20, 30, 40])
        cl_mass_frac = np.asarray([0.09797571, 0.37944013, 1.22129252, 2.93772332, 1.87681504, 4.53166338, 23.44299425])
        cl2_mass_frac = np.asarray([7.06500364, 8.03296568, 10.62827697, 17.29888424, 29.61138669, 52.1746513, 45.15366282])
        hcl_mass_frac = np.asarray([92.83702064, 91.58759419, 88.15043051, 79.76339245, 68.51179827, 43.29368532, 31.40334294])
        
        self.ei_cl = np.zeros_like(height)
        self.ei_cl2 = np.zeros_like(height)
        self.ei_hcl = np.zeros_like(height)

        for i, h in enumerate(height):
            # At each altitude, interpolate the mass_frac arrays to get the % of each chlorine species.
            if h > 40:
                self.ei_cl[i]  = cl_mass_frac[-1]
                self.ei_cl2[i] = cl2_mass_frac[-1]
                self.ei_hcl[i] = hcl_mass_frac[-1]
            else:
                self.ei_cl[i]  = np.interp(h,lit_alt,cl_mass_frac)
                self.ei_cl2[i] = np.interp(h,lit_alt,cl2_mass_frac)
                self.ei_hcl[i] = np.interp(h,lit_alt,hcl_mass_frac)
            if 99.99 <= self.ei_cl[i]+self.ei_cl2[i]+self.ei_hcl[i] <= 100.01:
                self.ei_cl[i] = self.ei_cl[i] / 100 * cly_pei
                self.ei_cl2[i] = self.ei_cl2[i] / 100 * cly_pei
                self.ei_hcl[i] = self.ei_hcl[i] / 100 * cly_pei
            else:
                print(self.ei_cl[i]+self.ei_cl2[i]+self.ei_hcl[i])
                sys.exit(f"Warning, chlorine didn't add to 100%.")
                
        plt.plot(height,self.ei_cl,'-xr')
        plt.plot(height,self.ei_cl2,'-xk')
        plt.plot(height,self.ei_hcl,'-xb')
        plt.savefig("Cl.png")
            
    def calculate_cl_ei(self, height, cly_pei):
        """Calculate emission indices for all chlorine species in g per kg propellant burned.
           Using data from Gomberg, Zittel and Leone, refs originally obtained from James2021."""
           
        pei_file = pd.read_csv("/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/Databases/Chlorine_PEI.csv")

        alt_lit                = pei_file["Alt"].to_numpy()
        hcl_param              = pei_file["HCl"].to_numpy()[0:4]         
        mass_frac_cl_average   = pei_file["Cl"].to_numpy()
        mass_frac_cl2_average  = pei_file["Cl2"].to_numpy()
            
        self.ei_cl = np.zeros_like(height)
        self.ei_cl2 = np.zeros_like(height)
        self.ei_hcl = np.zeros_like(height)
        
        cl_frac_upper = mass_frac_cl_average[-1] / (mass_frac_cl_average[-1] + mass_frac_cl2_average[-1])
        cl2_frac_upper = mass_frac_cl2_average[-1] / (mass_frac_cl_average[-1] + mass_frac_cl2_average[-1])

        for i, h in enumerate(height):
            # Get pressure
            alt, temp, pressure, delta = print_pressures([h])
            # Calculate HCl mass frac
            mass_frac_hcl = 1 - (hcl_param[0] * np.exp(-hcl_param[1] * pressure*1e-3 +  hcl_param[2]) + hcl_param[3])
            
            mass_frac_cl = np.interp(h,alt_lit,mass_frac_cl_average)
            mass_frac_cl2 = np.interp(h,alt_lit,mass_frac_cl2_average)
            if h < 40:
                cl_frac = mass_frac_cl / (mass_frac_cl + mass_frac_cl2)
                cl2_frac = mass_frac_cl2 / (mass_frac_cl + mass_frac_cl2)
                mass_frac_cl  = (1-mass_frac_hcl) * cl_frac
                mass_frac_cl2 = (1-mass_frac_hcl) * cl2_frac
            else:
                mass_frac_cl  = (1-mass_frac_hcl) * cl_frac_upper
                mass_frac_cl2 = (1-mass_frac_hcl) * cl2_frac_upper
            
            if 0.9999 <= (mass_frac_hcl + mass_frac_cl + mass_frac_cl2) <= 1.0001:
                self.ei_cl[i]  = mass_frac_cl * cly_pei
                self.ei_cl2[i] = mass_frac_cl2 * cly_pei
                self.ei_hcl[i] = mass_frac_hcl * cly_pei
            else:
                print(self.ei_cl[i],self.ei_cl2[i],self.ei_hcl[i],self.ei_cl[i]+self.ei_cl2[i]+self.ei_hcl[i])
                sys.exit(f"Warning, Cly didn't add to 100%.")
        
        if (np.sum(self.ei_cl) + np.sum(self.ei_cl2) + np.sum(self.ei_hcl)) > 0:  
            plt.plot(height,self.ei_cl,'-xr')
            plt.plot(height,self.ei_cl2,'-xk')
            plt.plot(height,self.ei_hcl,'-xb')
            plt.xlim(0,80)
            plt.ylim(0,200)
            plt.xlabel("Altitude / km")
            plt.ylabel("Emission Index / g/kg")
            plt.savefig("Cl.png")
     
    def process_launch_event_altitudes(self, valid_index, p, q, launch_rocket):
        # Now define the rocket configuration (can this be written in fewer lines?)
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
            
            # If there are boosters, then this section calculates the propellant consumption profile for the boosters.    
            # Find out which layer the cutoff occurs in.
            self.booster_alt_index = np.argmin(np.abs(self.booster_levs[rocket_config_type]*1e3 - self.mid_alt[:,q,p]))
            # Booster cutoff is always within GC boundary so can simply index gc_relative_mass.
            gc_relative_mass_booster = np.asarray(self.gc_relative_mass[self.nlev-self.booster_alt_index-1:])
            # Normalize the vertical emission profile for the booster emissions.
            self.gc_relative_mass_booster = gc_relative_mass_booster / np.sum(gc_relative_mass_booster) * 100

        elif rocket_data.booster_prop_type[valid_index] == '':
            if rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] == '' and rocket_data.stage4_prop_type[valid_index] == '':
                rocket_config_type = 3
            elif rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] != '' and rocket_data.stage4_prop_type[valid_index] == '':
                rocket_config_type = 4
            elif rocket_data.stage1_prop_type[valid_index] != '' and rocket_data.stage2_prop_type[valid_index] != '' and rocket_data.stage3_prop_type[valid_index] != '' and rocket_data.stage4_prop_type[valid_index] != '':
                rocket_config_type = 5
            elif launch_rocket == "Chang'e 5 SSQ (Ascent Stage)":
                rocket_config_type = 0
            else:
                sys.exit("Incorrect rocket configuration.")
        else:
            sys.exit("Incorrect rocket configuration.")
        
        # Now calculate the propellant consumption profile for stage 1.        
        if self.meco_levs[rocket_config_type] * 1e3 > self.top_alt[-1,q,p]:
            # If MECO occurs above the the GC boundary, then we have to only use some of the stage 1 emissions.
            self.gc_relative_mass_stage1 = np.asarray(self.gc_relative_mass)
            self.MECO_alt_index = self.nlev - 1
            if self.meco_levs[rocket_config_type] < 102.5:
                # Interpolate to see how much propellant is emitted above MECO.
                h = self.meco_levs[rocket_config_type]
                for count, ross_alt in enumerate(self.ross_alt):
                    value = ross_alt-h
                    if value < 0:
                        break
                ross_ind = count - 1
                self.propellant_below_meco = self.ross_cumulative_mass[ross_ind] + ((h - self.ross_alt[ross_ind]) /
                                                (self.ross_alt[ross_ind-1] - self.ross_alt[ross_ind])) * (self.ross_cumulative_mass[ross_ind-1] - self.ross_cumulative_mass[ross_ind])
                
                self.gc_relative_mass_stage1 = self.gc_relative_mass_stage1 / (self.propellant_below_meco) * 100
                
                # TODO: This interpolation can probably be done in one line using a numpy interpolation function.
        
        else:
            # If MECO occurs below the the GC boundary, then we can use all of the stage 1 emissions.
            # Find out which layer MECO occurs in.
            self.MECO_alt_index = np.argmin(np.abs(self.meco_levs[rocket_config_type]*1e3 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_stage1 = np.asarray(self.gc_relative_mass[self.nlev-self.MECO_alt_index-1:])
            
            # If the rocket is Falcon v1.2 Block 5, then MECO is always in GC, and 93.2% of the emissions are used for ascent.
            if launch_rocket == "Falcon 9 v1.2" and self.include_landing == True:
                self.gc_relative_mass_stage1 = self.gc_relative_mass_stage1 / np.sum(self.gc_relative_mass_stage1) * (100-5.6-1.2)
            # For all other rockets, 100% is used for ascent.
            else:
                self.gc_relative_mass_stage1 = self.gc_relative_mass_stage1 / np.sum(self.gc_relative_mass_stage1) * 100
                       
        # Now calculate the propellant consumption profile for stage 2.
        if self.sei_levs[rocket_config_type] * 1e3 > self.top_alt[-1,q,p]:
            # If SEI occurs above the the GC boundary, then we can ignore the second stage.
            self.gc_relative_mass_stage2 = np.asarray([0])
            self.SEI_alt_index = self.nlev
        
        else:
            # If SEI occurs below the the GC boundary, then we can use some of the stage 2 emissions.
            # Find out which layer SEI occurs in. If its a 3 or 4 stage rocket with no boosters, then set SEI to occur in the layer above MECO to prevent a spike in emissions.
            if rocket_config_type in [2,4,5]:
                self.SEI_alt_index = self.MECO_alt_index + 1    
            else:
                self.SEI_alt_index = np.argmin(np.abs(self.meco_levs[rocket_config_type]*1e3 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_stage2 = np.asarray(self.gc_relative_mass[:self.nlev-self.SEI_alt_index])
            self.gc_relative_mass_stage2 = self.gc_relative_mass_stage2 / (np.sum(self.gc_relative_mass_stage2) + (100 - self.propellant_in_gc)) * 100

        # Finally create an extra stage just for the landing emissions of Falcon 9 v1.2.
        if launch_rocket == "Falcon 9 v1.2":
            # 5.6% are used in the entry burn, over 70-54.7 km.
            self.entry_top = np.argmin(np.abs(70000 - self.mid_alt[:,q,p]))
            self.entry_bot = np.argmin(np.abs(54700 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_entry = np.asarray(self.gc_relative_mass[self.nlev-self.entry_top-1:self.nlev-self.entry_bot])
            self.gc_relative_mass_entry = self.gc_relative_mass_entry / np.sum(self.gc_relative_mass_entry) * 5.6
            
            # 1.2% are used in the landing burn, over 3.3-0 km.
            self.landing_top = np.argmin(np.abs(3300 - self.mid_alt[:,q,p]))
            self.gc_relative_mass_landing = np.asarray(self.gc_relative_mass[self.nlev-self.landing_top-1:])
            self.gc_relative_mass_landing = self.gc_relative_mass_landing / np.sum(self.gc_relative_mass_landing) * 1.2
        
        return rocket_config_type
              
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
            
            #Print the altitudes if required.
            #alt=np.zeros(self.nlev)
            #i=0
            #for n in self.box_height[:,q,p]:
            #    if i==0:
            #        alt[i]=0
            #    else:
            #        alt[i] = n + alt[i-1]
            #    i += 1
            #for l in reversed(alt):
            #    print(l*1e-3)
            
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
                
                # TODO: Settling of emissions.
                # Some of these failures will still include emissions above the GC boundary.
                
                # TODO: Reentries.
                # For all failed launches, DISCOSweb does not include objects, so may need to manually add.
                
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
                    
                ##############################################
                # Start processing the launch even altitudes.
                ##############################################  
                                                    
                # Next find index of fuel type in primary emissions index data:
                pei_booster_index = np.where( rocket_data.pei_fuel_type == rocket_data.booster_prop_type[valid_index] )[0]
                pei_stage1_index  = np.where( rocket_data.pei_fuel_type == rocket_data.stage1_prop_type[valid_index] )[0]
                pei_stage2_index  = np.where( rocket_data.pei_fuel_type == rocket_data.stage2_prop_type[valid_index] )[0]
                
                rocket_config_type = self.process_launch_event_altitudes(valid_index, p, q, launch_rocket[w])
                
                # Treat failed launches. Most failures are for upper stages, and so can be treated as normal here.
                # Full information is provided in README.txt
                if launch_id[w][-3:] in ['F04','F11']:
                    print(f'Launch {launch_id[w]} failed. Not processing.')
                    self.csv_count += 3
                    continue
                elif launch_id[w][-3:] in ['F05']:
                    self.gc_relative_mass_stage2 = np.asarray([0])
                    self.SEI_alt_index = self.nlev
                elif launch_id[w][-3:] in ['F07']:
                    # Stage 2 is already above GC.
                    # Find altitude nearest 0.9 km, and make all relative mass 0 above this point.
                    cutoff_ind = np.argmin(np.abs(900 - self.mid_alt[::-1,q,p]))
                    self.gc_relative_mass_stage1[:cutoff_ind+1] = np.zeros((len(self.gc_relative_mass_stage1[:cutoff_ind+1])))
                
                ##################################################
                # Sanity Checks for Propellant Mass Distributions
                ##################################################
                
                # For all rockets with boosters, the propellant consumed for the boosters should never be bigger than the total booster propellant.
                if ( rocket_data.booster_prop_type[valid_index] != '' ):
                    self.booster_prop_consumed[self.launch_count] = np.sum(self.gc_relative_mass_booster * rocket_data.booster_prop_mass[valid_index] * 1e-2)
                    if (np.abs(self.booster_prop_consumed[self.launch_count] - rocket_data.booster_prop_mass[valid_index]) / rocket_data.booster_prop_mass[valid_index] * 100) > 1:
                        sys.exit("Error with booster emissions.") 
                        
                self.stage1_prop_consumed[self.launch_count]  = np.sum(self.gc_relative_mass_stage1 * rocket_data.stage1_prop_mass[valid_index] * 1e-2)
                self.stage2_prop_consumed[self.launch_count]  = np.sum(self.gc_relative_mass_stage2 * rocket_data.stage2_prop_mass[valid_index] * 1e-2)

                # For all rockets, the propellant consumed for each stage should never be bigger than the total propellant in each stage.
                if (self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) > 0.1:
                    sys.exit(f"Error with Stage 1 emissions - 1.")
                elif (self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) > 0 and (self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) < 0.1:
                    print(f"Warning: Floating point difference of {np.abs(self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index])}")
                if (self.stage2_prop_consumed[self.launch_count] - rocket_data.stage2_prop_mass[valid_index]) > 0.1:
                    sys.exit("Error with Stage 2 emissions.")
                
                # For these rocket types, MECO occurs in GC, and so the consumed propellant should be within 1% of the total propellant mass of stage 1.  
                # The error is suppressed for F07, where the Astra Rocket failed after 22s. Also suppressed for Falcon 9, as this has a reusable first stage.
                # A check that the Falcon landing distribution is no greater than 7% of the stage 1 emissions is undertaken later in the grid_emis function.
                if rocket_config_type in [2,3,4,5]:
                    if (launch_id[w][-3:] not in ['F07']) and rocket_data.rocket_name[valid_index] != "Falcon 9 v1.2" and ((np.abs(self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) / rocket_data.stage1_prop_mass[valid_index] * 100) > 1):
                        print(launch_id[w][-3:],self.stage1_prop_consumed[self.launch_count],rocket_data.stage1_prop_mass[valid_index],(np.abs(self.stage1_prop_consumed[self.launch_count] - rocket_data.stage1_prop_mass[valid_index]) / rocket_data.stage1_prop_mass[valid_index] * 100))
                        sys.exit("Error with Stage 1 emissions - 2.")  
                        
                self.total_prop_consumed[pei_booster_index,0] += self.booster_prop_consumed[self.launch_count]
                self.total_prop_consumed[pei_stage1_index,1] += self.stage1_prop_consumed[self.launch_count]
                self.total_prop_consumed[pei_stage2_index,2] += self.stage2_prop_consumed[self.launch_count]
                
                # TODO: Settling of emissions                  

                total_prop_mass = rocket_data.booster_prop_mass[valid_index] + rocket_data.stage1_prop_mass[valid_index] + rocket_data.stage2_prop_mass[valid_index]
                total_prop_mass += rocket_data.stage3_prop_mass[valid_index] + rocket_data.stage4_prop_mass[valid_index]
                #percent_dis_b = rocket_data.booster_prop_mass[valid_index] / total_prop_mass * 100
                #percent_dis_s1 = rocket_data.stage1_prop_mass[valid_index] / total_prop_mass * 100
                #percent_dis_s2 = rocket_data.stage2_prop_mass[valid_index] / total_prop_mass * 100
                #percent_dis_s3 = rocket_data.stage3_prop_mass[valid_index] / total_prop_mass * 100
                #percent_dis_s4 = rocket_data.stage4_prop_mass[valid_index] / total_prop_mass * 100
                #print(f"% Distribution is {percent_dis_b:.0f} {percent_dis_s1:.0f} {percent_dis_s2:.0f} {percent_dis_s3:.0f} {percent_dis_s4:.0f}")
                
                total_vertical_propellant = np.zeros_like(self.mid_alt[:,q,p])
                total_bc_propellant       = np.zeros_like(self.mid_alt[:,q,p])
                total_co_propellant       = np.zeros_like(self.mid_alt[:,q,p])
                total_nox_propellant      = np.zeros_like(self.mid_alt[:,q,p])
                total_h2o_propellant      = np.zeros_like(self.mid_alt[:,q,p])
                total_al2o3_propellant    = np.zeros_like(self.mid_alt[:,q,p])
                total_cl_propellant       = np.zeros_like(self.mid_alt[:,q,p])
                total_hcl_propellant      = np.zeros_like(self.mid_alt[:,q,p])
                total_cl2_propellant      = np.zeros_like(self.mid_alt[:,q,p])
                
                ##############################################
                # Calculate the emissions for each species.
                ##############################################              
                                
                # Check whether there is a booster:
                if ( rocket_data.booster_prop_type[valid_index] != '' ):
                    if np.sum(1e-2 * self.gc_relative_mass_booster) > 1.01:
                        sys.exit("Error with Boosters. Propellant distribution exceeds unity.")
                        
                    self.calculate_bc_ei(self.mid_alt[self.booster_alt_index::-1,q,p]*1e-3,rocket_data.bc_pei[pei_booster_index])
                    t_bc_emis = self.ei_bc * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.bc_total += np.sum(t_bc_emis)
                    self.rocket_bc[int(hour[w]),self.booster_alt_index::-1,q,p] += t_bc_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_co_ei(self.mid_alt[self.booster_alt_index::-1,q,p]*1e-3, rocket_data.co_pei[pei_booster_index], rocket_data.co2_pei[pei_booster_index])
                    t_co_emis = self.ei_co * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.co_total += np.sum(t_co_emis)
                    self.rocket_co[int(hour[w]),self.booster_alt_index::-1,q,p] += t_co_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_nox_ei(self.mid_alt[self.booster_alt_index::-1,q,p]*1e-3,rocket_data.nox_pei[pei_booster_index])
                    t_nox_emis = self.ei_sec_nox * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.nox_launch_total += np.sum(t_nox_emis)
                    self.rocket_nox[int(hour[w]),self.booster_alt_index::-1,q,p] = t_nox_emis * 1e-3 / kg_to_kgm2s
                    
                    self.ei_h2o =  rocket_data.h2o_pei[pei_booster_index] + rocket_data.h2_pei[pei_booster_index] * self.mw_h2o / self.mw_h2 
                    t_h2o_emis = self.ei_h2o * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.h2o_total += np.sum(t_h2o_emis)
                    self.rocket_h2o[int(hour[w]),self.booster_alt_index::-1,q,p] += t_h2o_emis * 1e-3 / kg_to_kgm2s
                    
                    t_al2o3_emis = rocket_data.al2o3_pei[pei_booster_index] * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.al2o3_launch_total += np.sum(t_al2o3_emis)
                    self.rocket_al[int(hour[w]),self.booster_alt_index::-1,q,p] += t_al2o3_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_cl_ei(self.mid_alt[self.booster_alt_index::-1,q,p]*1e-3, rocket_data.cly_pei[pei_booster_index])  
                    
                    t_cl_emis = self.ei_cl * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.cl_total += np.sum(t_cl_emis)
                    self.rocket_cl[int(hour[w]),self.booster_alt_index::-1,q,p] += t_cl_emis * 1e-3 / kg_to_kgm2s

                    t_hcl_emis = self.ei_hcl * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.hcl_total += np.sum(t_hcl_emis)
                    self.rocket_hcl[int(hour[w]),self.booster_alt_index::-1,q,p] += t_hcl_emis * 1e-3 / kg_to_kgm2s
                    
                    t_cl2_emis = self.ei_cl2 * rocket_data.booster_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_booster
                    self.cl2_total += np.sum(t_cl2_emis)
                    self.rocket_cl2[int(hour[w]),self.booster_alt_index::-1,q,p] += t_cl2_emis * 1e-3 / kg_to_kgm2s
                    
                    # These are all for viewing the individual propellant / species vertical distribution per launch.
                    vertical_propellant_booster = rocket_data.booster_prop_mass[valid_index] * self.gc_relative_mass_booster
                    total_vertical_propellant[:self.booster_alt_index+1] += vertical_propellant_booster[::-1]
                    total_bc_propellant[:self.booster_alt_index+1]    += t_bc_emis[::-1]
                    total_co_propellant[:self.booster_alt_index+1]    += t_co_emis[::-1]
                    total_nox_propellant[:self.booster_alt_index+1]   += t_nox_emis[::-1]
                    total_h2o_propellant[:self.booster_alt_index+1]   += t_h2o_emis[::-1]
                    total_al2o3_propellant[:self.booster_alt_index+1] += t_al2o3_emis[::-1]
                    total_cl_propellant[:self.booster_alt_index+1]    += t_cl_emis[::-1]
                    total_hcl_propellant[:self.booster_alt_index+1]   += t_hcl_emis[::-1]
                    total_cl2_propellant[:self.booster_alt_index+1]   += t_cl2_emis[::-1]

                # Every rocket has a first stage.
                if np.sum(1e-2 * self.gc_relative_mass_stage1) > 1.01:
                    sys.exit("Error with Stage 1. Propellant distribution exceeds unity.")

                self.calculate_bc_ei(self.mid_alt[self.MECO_alt_index::-1,q,p]*1e-3,rocket_data.bc_pei[pei_stage1_index])
                t_bc_emis = self.ei_bc * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.bc_total += np.sum(t_bc_emis)
                self.rocket_bc[int(hour[w]),self.MECO_alt_index::-1,q,p] += t_bc_emis*1e-3 / kg_to_kgm2s

                self.calculate_co_ei(self.mid_alt[self.MECO_alt_index::-1,q,p]*1e-3, rocket_data.co_pei[pei_stage1_index], rocket_data.co2_pei[pei_stage1_index])
                t_co_emis = self.ei_co * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.co_total += np.sum(t_co_emis)
                self.rocket_co[int(hour[w]),self.MECO_alt_index::-1,q,p] += t_co_emis * 1e-3 / kg_to_kgm2s
                
                self.calculate_nox_ei(self.mid_alt[self.MECO_alt_index::-1,q,p]*1e-3,rocket_data.nox_pei[pei_stage1_index])
                t_nox_emis = self.ei_sec_nox * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.nox_launch_total += np.sum(t_nox_emis)
                self.rocket_nox[int(hour[w]),self.MECO_alt_index::-1,q,p] = t_nox_emis * 1e-3 / kg_to_kgm2s
                
                self.ei_h2o =  rocket_data.h2o_pei[pei_stage1_index] + rocket_data.h2_pei[pei_stage1_index] * self.mw_h2o / self.mw_h2 
                t_h2o_emis = self.ei_h2o * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.h2o_total += np.sum(t_h2o_emis)
                self.rocket_h2o[int(hour[w]),self.MECO_alt_index::-1,q,p] += t_h2o_emis * 1e-3 / kg_to_kgm2s
                
                t_al2o3_emis = rocket_data.al2o3_pei[pei_stage1_index] * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.al2o3_launch_total += np.sum(t_al2o3_emis)
                self.rocket_al[int(hour[w]),self.MECO_alt_index::-1,q,p] += t_al2o3_emis * 1e-3 / kg_to_kgm2s
                
                self.calculate_cl_ei(self.mid_alt[self.MECO_alt_index::-1,q,p]*1e-3,rocket_data.cly_pei[pei_stage1_index])  
                      
                t_cl_emis = self.ei_cl * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.cl_total += np.sum(t_cl_emis)
                self.rocket_cl[int(hour[w]),self.MECO_alt_index::-1,q,p] += t_cl_emis * 1e-3 / kg_to_kgm2s

                t_hcl_emis = self.ei_hcl * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.hcl_total += np.sum(t_hcl_emis)
                self.rocket_hcl[int(hour[w]),self.MECO_alt_index::-1,q,p] += t_hcl_emis * 1e-3 / kg_to_kgm2s 
                
                t_cl2_emis = self.ei_cl2 * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage1
                self.cl2_total += np.sum(t_cl2_emis)
                self.rocket_cl2[int(hour[w]),self.MECO_alt_index::-1,q,p] += t_cl2_emis * 1e-3 / kg_to_kgm2s 
                
                # These are all for viewing the individual propellant / species vertical distribution per launch.
                vertical_propellant_stage1 = rocket_data.stage1_prop_mass[valid_index] * self.gc_relative_mass_stage1
                total_vertical_propellant[:self.MECO_alt_index+1] += vertical_propellant_stage1[::-1]
                total_bc_propellant[:self.MECO_alt_index+1]    += t_bc_emis[::-1]
                total_co_propellant[:self.MECO_alt_index+1]    += t_co_emis[::-1]
                total_nox_propellant[:self.MECO_alt_index+1]   += t_nox_emis[::-1]
                total_h2o_propellant[:self.MECO_alt_index+1]   += t_h2o_emis[::-1]
                total_al2o3_propellant[:self.MECO_alt_index+1] += t_al2o3_emis[::-1]
                total_cl_propellant[:self.MECO_alt_index+1]    += t_cl_emis[::-1]
                total_hcl_propellant[:self.MECO_alt_index+1]   += t_hcl_emis[::-1]
                total_cl2_propellant[:self.MECO_alt_index+1]   += t_cl2_emis[::-1]

                # Check whether there is a second stage:
                if rocket_data.stage2_prop_type[valid_index] != '' and launch_id[w][-3:] != 'F03':
                    if np.sum(1e-2 * self.gc_relative_mass_stage2) > 1.01:
                        sys.exit("Error with Stage 2. Propellant distribution exceeds unity.")
                    self.calculate_bc_ei(self.mid_alt[:self.SEI_alt_index-1:-1,q,p]*1e-3,rocket_data.bc_pei[pei_stage2_index])
                    t_bc_emis = self.ei_bc * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.bc_total += np.sum(t_bc_emis)
                    self.rocket_bc[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] += t_bc_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_co_ei(self.mid_alt[:self.SEI_alt_index-1:-1,q,p]*1e-3, rocket_data.co_pei[pei_stage2_index], rocket_data.co2_pei[pei_stage2_index])
                    t_co_emis = self.ei_co * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.co_total += np.sum(t_co_emis)
                    self.rocket_co[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] += t_co_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_nox_ei(self.mid_alt[:self.SEI_alt_index-1:-1,q,p]*1e-3,rocket_data.nox_pei[pei_stage2_index])
                    t_nox_emis = self.ei_sec_nox * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.nox_launch_total += np.sum(t_nox_emis)
                    self.rocket_nox[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] = t_nox_emis * 1e-3 / kg_to_kgm2s
                    
                    self.ei_h2o =  rocket_data.h2o_pei[pei_stage2_index] + rocket_data.h2_pei[pei_stage2_index] * self.mw_h2o / self.mw_h2 
                    t_h2o_emis = self.ei_h2o * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.h2o_total += np.sum(t_h2o_emis)
                    self.rocket_h2o[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] += t_h2o_emis * 1e-3 / kg_to_kgm2s
                    
                    t_al2o3_emis = rocket_data.al2o3_pei[pei_stage2_index] * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.al2o3_launch_total += np.sum(t_al2o3_emis)
                    self.rocket_al[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] += t_al2o3_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_cl_ei(self.mid_alt[:self.SEI_alt_index-1:-1,q,p]*1e-3,rocket_data.cly_pei[pei_stage2_index])
                    
                    t_cl_emis = self.ei_cl * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.cl_total += np.sum(t_cl_emis)
                    self.rocket_cl[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] += t_cl_emis * 1e-3 / kg_to_kgm2s

                    t_hcl_emis = self.ei_hcl * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.hcl_total += np.sum(t_hcl_emis)
                    self.rocket_hcl[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] += t_hcl_emis * 1e-3 / kg_to_kgm2s
                    
                    t_cl2_emis = self.ei_cl2 * rocket_data.stage2_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_stage2
                    self.cl2_total += np.sum(t_cl2_emis)
                    self.rocket_cl2[int(hour[w]),:self.SEI_alt_index-1:-1,q,p] += t_cl2_emis * 1e-3 / kg_to_kgm2s

                    # These are all for viewing the individual propellant / species vertical distribution per launch.
                    vertical_propellant_stage2 = rocket_data.stage2_prop_mass[valid_index] * self.gc_relative_mass_stage2
                    total_vertical_propellant[self.SEI_alt_index:] += vertical_propellant_stage2[::-1]
                    total_bc_propellant[self.SEI_alt_index:]    += t_bc_emis[::-1]
                    total_co_propellant[self.SEI_alt_index:]    += t_co_emis[::-1]
                    total_nox_propellant[self.SEI_alt_index:]   += t_nox_emis[::-1]
                    total_h2o_propellant[self.SEI_alt_index:]   += t_h2o_emis[::-1]
                    total_al2o3_propellant[self.SEI_alt_index:] += t_al2o3_emis[::-1]
                    total_cl_propellant[self.SEI_alt_index:]    += t_cl_emis[::-1]
                    total_hcl_propellant[self.SEI_alt_index:]   += t_hcl_emis[::-1]
                    total_cl2_propellant[self.SEI_alt_index:]   += t_cl2_emis[::-1]
                    
                # If the rocket is a Falcon 9, then add the landing emissions. Kerosene, so no Al2O3 or Cly.
                if rocket_data.rocket_name[valid_index] == "Falcon 9 v1.2" and self.include_landing == True:
                    if np.sum(self.gc_relative_mass_entry) + np.sum(self.gc_relative_mass_landing) > 7:
                        sys.exit("Error with Stage 1 Landing. Propellant distribution exceeds what is expected.")
                    
                    ############################
                    # First the entry emissions.
                    ############################
                        
                    self.calculate_bc_ei(self.mid_alt[self.entry_top:self.entry_bot-1:-1,q,p]*1e-3,rocket_data.bc_pei[pei_stage1_index])
                    t_bc_emis = self.ei_bc * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_entry
                    self.bc_total += np.sum(t_bc_emis)
                    self.rocket_bc[int(hour[w]),self.entry_top:self.entry_bot-1:-1,q,p] += t_bc_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_co_ei(self.mid_alt[self.entry_top:self.entry_bot-1:-1,q,p]*1e-3, rocket_data.co_pei[pei_stage1_index], rocket_data.co2_pei[pei_stage1_index])
                    t_co_emis = self.ei_co * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_entry
                    self.co_total += np.sum(t_co_emis)
                    self.rocket_co[int(hour[w]),self.entry_top:self.entry_bot-1:-1,q,p] += t_co_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_nox_ei(self.mid_alt[self.entry_top:self.entry_bot-1:-1,q,p]*1e-3,rocket_data.nox_pei[pei_stage1_index])
                    t_nox_emis = self.ei_sec_nox * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_entry
                    self.nox_launch_total += np.sum(t_nox_emis)
                    self.rocket_nox[int(hour[w]),self.entry_top:self.entry_bot-1:-1,q,p] = t_nox_emis * 1e-3 / kg_to_kgm2s
                    
                    self.ei_h2o =  rocket_data.h2o_pei[pei_stage1_index] + rocket_data.h2_pei[pei_stage1_index] * self.mw_h2o / self.mw_h2 
                    t_h2o_emis = self.ei_h2o * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_entry
                    self.h2o_total += np.sum(t_h2o_emis)
                    self.rocket_h2o[int(hour[w]),self.entry_top:self.entry_bot-1:-1,q,p] += t_h2o_emis * 1e-3 / kg_to_kgm2s
                    
                    # These are all for viewing the individual propellant / species vertical distribution per launch.
                    vertical_propellant_entry = rocket_data.stage1_prop_mass[valid_index] * self.gc_relative_mass_entry
                    total_vertical_propellant[self.entry_bot:self.entry_top+1] += vertical_propellant_entry[::-1]
                    total_bc_propellant[self.entry_bot:self.entry_top+1]    += t_bc_emis[::-1]
                    total_co_propellant[self.entry_bot:self.entry_top+1]    += t_co_emis[::-1]
                    total_nox_propellant[self.entry_bot:self.entry_top+1]   += t_nox_emis[::-1]
                    total_h2o_propellant[self.entry_bot:self.entry_top+1]   += t_h2o_emis[::-1]
                    
                    #############################
                    # Now the landing emissions.
                    #############################
                        
                    self.calculate_bc_ei(self.mid_alt[self.landing_top::-1,q,p]*1e-3,rocket_data.bc_pei[pei_stage1_index])
                    t_bc_emis = self.ei_bc * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_landing
                    self.bc_total += np.sum(t_bc_emis)
                    self.rocket_bc[int(hour[w]),self.landing_top::-1,q,p] += t_bc_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_co_ei(self.mid_alt[self.landing_top::-1,q,p]*1e-3, rocket_data.co_pei[pei_stage1_index], rocket_data.co2_pei[pei_stage1_index])
                    t_co_emis = self.ei_co * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_landing
                    self.co_total += np.sum(t_co_emis)
                    self.rocket_co[int(hour[w]),self.landing_top::-1,q,p] += t_co_emis * 1e-3 / kg_to_kgm2s
                    
                    self.calculate_nox_ei(self.mid_alt[self.landing_top::-1,q,p]*1e-3,rocket_data.nox_pei[pei_stage1_index])
                    t_nox_emis = self.ei_sec_nox * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_landing
                    self.nox_launch_total += np.sum(t_nox_emis)
                    self.rocket_nox[int(hour[w]),self.landing_top::-1,q,p] = t_nox_emis * 1e-3 / kg_to_kgm2s
                    
                    self.ei_h2o =  rocket_data.h2o_pei[pei_stage1_index] + rocket_data.h2_pei[pei_stage1_index] * self.mw_h2o / self.mw_h2 
                    t_h2o_emis = self.ei_h2o * rocket_data.stage1_prop_mass[valid_index] * 1e-2 * self.gc_relative_mass_landing
                    self.h2o_total += np.sum(t_h2o_emis)
                    self.rocket_h2o[int(hour[w]),self.landing_top::-1,q,p] += t_h2o_emis * 1e-3 / kg_to_kgm2s
                    
                    # These are all for viewing the individual propellant / species vertical distribution per launch.
                    vertical_propellant_landing = rocket_data.stage1_prop_mass[valid_index] * self.gc_relative_mass_landing
                    total_vertical_propellant[0:self.landing_top+1] += vertical_propellant_landing[::-1]
                    total_bc_propellant[0:self.landing_top+1]    += t_bc_emis[::-1]
                    total_co_propellant[0:self.landing_top+1]    += t_co_emis[::-1]
                    total_nox_propellant[0:self.landing_top+1]   += t_nox_emis[::-1]
                    total_h2o_propellant[0:self.landing_top+1]   += t_h2o_emis[::-1]
                
                ##############################################
                # Output the emissions to a file for viewing.
                ##############################################                  
                    
                total_vertical_propellant = total_vertical_propellant / total_prop_mass
                self.output_for_csv[self.csv_count,:] = total_vertical_propellant
                self.csv_count += 1
                self.output_for_csv[self.csv_count,:] = self.mid_alt[:,q,p]*1e-3
                self.csv_count += 1  
                self.output_for_csv[self.csv_count,:] = self.gc_relative_mass[::-1]
                self.csv_count += 1 
                
                self.output_for_csv_2[self.csv_count_2,:] = total_bc_propellant
                self.csv_count_2 += 1 
                self.output_for_csv_2[self.csv_count_2,:] = total_co_propellant
                self.csv_count_2 += 1 
                self.output_for_csv_2[self.csv_count_2,:] = total_nox_propellant
                self.csv_count_2 += 1 
                self.output_for_csv_2[self.csv_count_2,:] = total_h2o_propellant
                self.csv_count_2 += 1 
                self.output_for_csv_2[self.csv_count_2,:] = total_al2o3_propellant
                self.csv_count_2 += 1 
                self.output_for_csv_2[self.csv_count_2,:] = total_cl_propellant
                self.csv_count_2 += 1 
                self.output_for_csv_2[self.csv_count_2,:] = total_hcl_propellant
                self.csv_count_2 += 1    
                self.output_for_csv_2[self.csv_count_2,:] = total_cl2_propellant
                self.csv_count_2 += 1 

                self.launch_count += 1
                
            #########################################################
            # Work out vertical distribution for reentry emissions.
            #########################################################
            
            # TODO: Re-entries.
            # Looks like the nox and al2o3 reentry emissions are just added to the launch emissions. Shall we keep them separate?
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
                    #print('Al2O3 reentry emis: ', tmp_reentry_al)
                    self.al2o3_reentry_total += tmp_reentry_al
                    # Initially with crude assumption that 90% of returning object is
                    # aluminum and that it is all converted to Al2O3.
                    self.rocket_al[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += tmp_reentry_al/self.n_reenter_levs/kg_to_kgm2s
                # Calculate proportion (17.5%, same as NOx) for Crew Dragon:
                if (tmp_id=='2019-011' and rocket_data.reentry_type[index[w]]=='Y'):
                    #print(rocket_data.reentry_id[index[w]], rocket_data.reentry_type[index[w]])
                    tmp_reentry_al = rocket_data.reentry_mass[index[w]]*0.9*0.175
                    #print('Al2O3 reentry emis: ', tmp_reentry_al)
                    self.al2o3_reentry_total += tmp_reentry_al
                    # Initially with crude assumption that 90% of returning object is
                    # aluminum and that it is all converted to Al2O3.
                    self.rocket_al[int(hour[w]),self.bot_reenter:self.top_reenter+1,q,p] += tmp_reentry_al/self.n_reenter_levs/kg_to_kgm2s
                # Exception for re-entry that has 8 characters:
                if (tmp_id=='2016-00C'):
                    #print(rocket_data.reentry_id[index[w]], rocket_data.reentry_type[index[w]])
                    tmp_reentry_al = rocket_data.reentry_mass[index[w]]*0.9
                    #print('Al2O3 reentry emis: ', tmp_reentry_al)
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
        
        # TODO: Need to split emissions into categories:
        #       - Crewed
        #       - Satellites
        #       - Megaconstellations
        # define dataset:
        ncout = Dataset(self.outfile_rocket_emis, mode='w', format='NETCDF4')

        # Set dimensions (lat, lon, time, lev):
        # Lat and lon data are trimmed to just where the launch occurs.
        #print(self.qmax,self.qmin,self.qmax-self.qmin+3)
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
        #print(self.rocket_bc[:,:,self.qmin-1:self.qmax+2,self.pmin-1:self.pmax+2])

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
    parser.add_argument('-l', "--levels", default="47", choices=["47", "72"], help="Vertical resolution.")
    parser.add_argument('-g', "--grid_res", default = "4x5", choices=["4x5", "2x2.5"], help='Grid resolution.')
    parser.add_argument('-sm', "--start_month", default = "1", choices=str(np.arange(1,13)), help='Start Month (will override final month if greater than final month).')
    parser.add_argument('-fm', "--final_month", default = "12", choices=str(np.arange(1,13)), help='Final Month.')
    parser.add_argument('-v', "--verbose", action='store_true')
    args = parser.parse_args()
    
    ##########################################################
    # Read the rocket emissions from the database.
    ##########################################################
       
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
    
    # In 2019, boosters set to extend to ~45 km (layer 44 of the 47-layer model, layer 57 of the 72-layer model).
    # In updated model, booster_cutoff changes depending on number of rocket stages.
    # Stage 1 Cutoff (MECO) and Stage 2 Ignition (SEI) normally occur within 3s of each other.
    # For the purposes of GEOS-Chem (<80km), only three rocket sizes include MECO and SEI - B+4S, 3S, 4S (2S occurs)
    # For these three rocket types, MECO and SEI occur at the same alitudes.
    # Booster Cutoff:
    #       63 km  B+1/2S  Layer 46 / 66
    #       63 km  B+3S    Layer 46 / 66
    #       24 km  B+4S    Layer 39 / 42
    # Stage 1 Cutoff:
    #       163 km B+1/2S  Layer N/A
    #       158 km B+3S    Layer N/A
    #       57 km  B+4S    Layer 45 / 63
    #       73 km  2S      Layer 47 / 70
    #       69 km  3S      Layer 47 / 69 
    #       39 km  4S      Layer 43 / 53
    # Stage 2 Ignition:
    #       176 km  B+1/2S Layer N/A
    #       159 km  B+3S   Layer N/A
    #       57  km  B+4S   Layer 45 / 63
    #       92 km   2S     Layer N/A
    #       69  km  3S     Layer 47 / 69 
    #       39  km  4S     Layer 43 / 53
    
    # These are the raw altitudes, they are converted to a GC layer inside the OutputEmis class.
    # To stop overlap between MECO and SEI, going to set SEI to start in layer above MECO for last two configs.
    booster_cutoff_alts = [63,63,24,0,0,0]
    MECO_alts           = [163,158,57,73,69,39]
    SEI_alts            = [176,159,57,92,69,39]
    
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
    # TODO: Run GEOS-Chem so we have StateMet files for:
    #       - 4x5 72
    #       - 2x2.5 47

    if grid_res == '4x5':
        if levels == 72:
            pass
            #gcdir = '/home/ucfacb0/uptrop/GC/run_12.9.3_72L/methane_fluxes/merra2_4x5_og/StateMet/'
        elif levels == 47:
            gcdir = '/home/ucfacb0/rundirs/gc_4x5_47L_merra2_nochem_StateMet/StateMet'
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
    if start_month > final_month:
        final_month = start_month + 1
    print(f"Processing from month {start_month} to {final_month}.")
    months = np.arange(start_month-1,final_month)    
        
    # Go through process of gridding and saving rocket emissions:
    emis_data = OutputEmis(rocket_data, grid_res, timestep, levels, booster_cutoff_alts, MECO_alts, SEI_alts, reentry_levs, gcdir, months)
    
    ##########################################################
    # Print total emissions of each species.
    ##########################################################
    
    # The total emissions including all afterburning are compared to a scenario where only primary emission indices are used.
    def check_total_emissions():
        total_prop_consumed = 0
        estimated_bc, estimated_nox, estimated_h2o, estimated_co, estimated_al2o3, estimated_hcl, estimated_cl, estimated_cl2 = 0, 0, 0, 0, 0, 0, 0, 0
        for i in range(4):
            for j in range(3):
                estimated_bc += emis_data.total_prop_consumed[i,j]  * rocket_data.bc_pei[i]
                estimated_nox += emis_data.total_prop_consumed[i,j] * rocket_data.nox_pei[i]
                estimated_h2o += emis_data.total_prop_consumed[i,j]  * rocket_data.h2o_pei[i]
                estimated_co += emis_data.total_prop_consumed[i,j]  * rocket_data.co_pei[i]
                estimated_al2o3 += emis_data.total_prop_consumed[i,j]  * rocket_data.al2o3_pei[i]
                estimated_hcl += emis_data.total_prop_consumed[i,j]  * rocket_data.cly_pei[i]
                estimated_cl += emis_data.total_prop_consumed[i,j]  * 0
                estimated_cl2 += emis_data.total_prop_consumed[i,j]  * 0
                
        print(f'PEI Estimated BC:    {estimated_bc*1e-9:.4f}  Total BC:    {(emis_data.bc_total)*1e-9:.4f} (Gg)')
        print(f'PEI Estimated NOx:   {estimated_nox*1e-9:.4f}  Total NOx:   {(emis_data.nox_launch_total)*1e-9:.4f} (Gg)')
        print(f'PEI Estimated H2O:   {estimated_h2o*1e-9:.4f} Total H2O:   {(emis_data.h2o_total)*1e-9:.4f} (Gg)')
        print(f'PEI Estimated CO:    {estimated_co*1e-9:.4f}  Total CO:    {(emis_data.co_total)*1e-9:.4f} (Gg)')
        print(f'PEI Estimated Al2O3: {estimated_al2o3*1e-9:.4f}  Total Al2O3: {(emis_data.al2o3_launch_total)*1e-9:.4f} (Gg)')
        print(f'PEI Estimated HCl:   {estimated_hcl*1e-9:.4f}  Total HCl:   {(emis_data.hcl_total)*1e-9:.4f}  (Gg)')
        print(f'PEI Estimated Cl:    {estimated_cl*1e-9:.4f}  Total Cl:    {(emis_data.cl_total)*1e-9:.4f}   (Gg)')
        print(f'PEI Estimated Cl2:   {estimated_cl2*1e-9:.4f}  Total Cl2:   {(emis_data.cl2_total)*1e-9:.4f} (Gg)')
        
        # TODO: Reentries.
        # Add these sanity checks when reentries have been dealt with.
        #print('Total NOx re-entry emissions (tonnes): ', emis_data.nox_reentry_total*1e-3)
        #print('Total Al2O3 re-entry emissions (tonnes): ', emis_data.al2o3_reentry_total*1e-6)
        
    check_total_emissions()
    