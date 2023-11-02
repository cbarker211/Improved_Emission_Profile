import numpy as np
import argparse
import xarray as xr
import pandas as pd
from datetime import datetime
import sys

class build_reentry_list:
    
    def add_failed_launch(self,cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon):
        for count,i in enumerate(stages):
            temp_reentry_dict = {
                "id"           : f"2020-{cospar_id}{pieces[count]}",
                "name"         : names[count],
                "type"         : types[count],
                "burnup"       : "Complete",
                "reentry_stage": i,
                "time"         : time_utc,
                "mon"          : mon,
                "day"          : day,
                "lat"          : lat,
                "lon"          : lon,
                "mass"         : masses[count],
                "MCS"          : False,
                "manual_loc"   : True,
            }    
            self.unique_reentry_list.append(temp_reentry_dict) 
            
    def print_stats(self):
        non_geo_count_notdebris, non_time_count_notdebris, non_mass_count_notdebris = 0, 0, 0
        total_mass, geolocated_mass = 0, 0
        starlink_count = 0
        for count, reentry in enumerate(self.unique_reentry_list):
        
            if reentry["lat"] == 0:
                non_geo_count_notdebris += 1
                if "starlink" in reentry["name"].lower():
                    starlink_count += 1
                      
            else:
                geolocated_mass += reentry["mass"]
            if reentry["time"] == -1:
                non_time_count_notdebris += 1
            if reentry["mass"] == 0:
                non_mass_count_notdebris += 1
                   
            total_mass += reentry["mass"]
        
        print(f"Total Reentries: {len(self.unique_reentry_list):.0f}.")
                
        
        geo_percent_all = (len(self.unique_reentry_list)-non_geo_count_notdebris) / (len(self.unique_reentry_list)) * 100
        time_percent_all = (len(self.unique_reentry_list)-non_time_count_notdebris) / (len(self.unique_reentry_list)) * 100
        mass_percent_all = (len(self.unique_reentry_list)-non_mass_count_notdebris) / (len(self.unique_reentry_list)) * 100
        print(f"Total mass (Gg):   {total_mass*1e-6}")
        print((27200*16)/total_mass*100)
        geolocated_mass_percent = geolocated_mass / total_mass * 100
        print(f"Geolocation (All): {geo_percent_all:.0f}%.")
        print(f"Timed (All):       {time_percent_all:.0f}%.")    
        print(f"Mass (All):        {mass_percent_all:.0f}%.")
        print(f"Geolocated Mass:   {geolocated_mass_percent:.0f}%.")
    
    def get_reentry_info(self):
             
        # Fairings should be included in the dry mass of the launched rocket, so can ignore here, but should acknowledge this in the write-up.
        
        #######################################
        # Load in all JSR Re-entries
        ########################################
        
        self.unique_reentry_list = []
        
        # Load in JSR first, as it has the most complete database.
        print("Searching for JSR re-entries.") 
        jsr_data = pd.read_csv("./Databases/JSR_ObjectList_Full_24Aug23.csv")
        
        # Reduce database by half to only include R (Reentry), D (Deorbit), or L (Landed) events.
        jsr_data_stripped = jsr_data[jsr_data["Status"].isin(["R","D","L"])].reset_index(drop=True)
        
        # If the reentry occured in 2020, then extract that row and build a new dataframe.
        jsr_data_stripped_2020_list = []
        for reentry_count in range(len(jsr_data_stripped)):
            if jsr_data_stripped["DDate"][reentry_count][0:4] == "2020":
                jsr_data_stripped_2020_list.append(jsr_data_stripped.iloc[[reentry_count]])
        jsr_data_stripped_2020 = pd.concat(jsr_data_stripped_2020_list, ignore_index=True)
        
        # Now left with a dataframe of 397 reentries that occured in 2020, but only 54 are geolocated.
        for reentry_count in range(len(jsr_data_stripped_2020)):
            
            mass = np.float64(jsr_data_stripped_2020["DryMass"][reentry_count]) 
            
            if jsr_data_stripped_2020["Type"][reentry_count][:1] == "R":
                
                # Sort out the rocket stages. All stages are 2-4, except for 2020-027C, which is 1st stage.
                reentry_stage = jsr_data_stripped_2020["Type"][reentry_count][1:2]
                if jsr_data_stripped_2020["Piece"][reentry_count] in ["2018-082B","2020-023B","2020-026B","2020-050B","2020-072B"]:
                    reentry_stage = 2
                elif jsr_data_stripped_2020["Piece"][reentry_count] == "2009-029B":
                    reentry_stage = 3
                elif jsr_data_stripped_2020["Piece"][reentry_count] == "2020-028C":
                    reentry_stage = 4  
                reentry_type = "R/B"
                 
            # These categories are P for Payload (for orbital attempt), and C for Component. 
            elif jsr_data_stripped_2020["Type"][reentry_count][:1] in ["C","P"]:
                reentry_stage = 5
                if jsr_data_stripped_2020["Type"][reentry_count][:1] == "C":
                    reentry_type = "Component"
                elif jsr_data_stripped_2020["Type"][reentry_count][:1] == "P":
                    reentry_type = "Payload"
                    
            # Sort out the reentry time/date.
            date = jsr_data_stripped_2020["DDate"][reentry_count].split()
            
            mon = datetime.strptime(date[1], '%b').month  
            if mon in np.arange(10):
                monstr = "0" + str(mon)
            else:
                monstr = str(mon)
                
            day = date[2].replace("?","")
            if int(day) in np.arange(10):
                daystr = "0" + day
            else:
                daystr = day
            
            if len(date) >= 4:    
                time_utc = np.float64(int(date[3].replace("?","")[0:2]) + int(date[3].replace("?","")[2:4]) / 60)
            else:
                if int(jsr_data_stripped_2020["Piece"][reentry_count][0:4]) < 2020:
                    time_utc = 0
                else:
                    time_utc = -1
                
            # Sort out the reentry lat/lon.
            if jsr_data_stripped_2020["Dest"][reentry_count] == "-":
                lat = 0 
                lon = 0
            elif jsr_data_stripped_2020["Dest"][reentry_count] == "Alashan": 
                # Landing expected east of Jiuquan launch site (this was actually launched from Wenchang).
                # Assuming that Alashan refers to Helen Shan Mountain (new name for Alashan Mountain).
                # https://space.skyrocket.de/doc_sdat/rcs-fc-sc.htm
                # https://planet4589.org/space/jsr/news.778
                # https://www.peakbagger.com/peak.aspx?pid=10693
                # https://www.nasaspaceflight.com/2020/05/china-next-generation-crew-capsule/
                lat = 38.833
                lon = 105.95
            elif jsr_data_stripped_2020["Dest"][reentry_count] == "Jiuquan":
                # This refers to the Chinese launch center, sources say it landed 'in the desert near Jiuquan', and 'in China’s Inner Mongolia autonomous region'.
                # Using lat/lon for Jiuquan launch site.
                # https://discosweb.esoc.esa.int/launch-sites/35
                # https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=2020-027A
                # https://space.skyrocket.de/doc_sdat/xzf-sc.htm 
                # https://spaceflightnow.com/2020/05/08/chinas-next-generation-crew-spacecraft-lands-after-unpiloted-test-flight/ 
                lat = 19.6
                lon = 111.0               
            elif jsr_data_stripped_2020["Dest"][reentry_count] == "LOPNOR RW05":
                # Reported test flight of a Chinese reusable experimental spacecraft.
                # Runway 05/22 at Lop Nor air base in Xinjiang (https://planet4589.org/space/gcat/data/tables/lp.html).
                # https://www.seradata.com/china-launches-own-mini-spaceplane-reusable-spacecraft-using-long-march-2f 
                # https://twitter.com/planet4589/status/1302486141090885632                
                lat = 40.78
                lon = 89.27
            else:
                geolocation = jsr_data_stripped_2020["Dest"][reentry_count].replace("?","").split()
                if geolocation[0][-1] in ["E","W"]: # If the longitude comes first.
                    lon_data = geolocation[0]
                    lat_data = geolocation[1]
                elif geolocation[1][-1] in ["E","W"]: # If the longitude comes last.
                    print(jsr_data_stripped_2020["Piece"][reentry_count])
                    lon_data = geolocation[1]
                    lat_data = geolocation[0]  
                if lon_data[-1] == "W":
                    lon = np.float64(lon_data.replace("W",""))*-1
                elif lon_data[-1] == "E":
                    lon = np.float64(lon_data.replace("E",""))
                if lat_data[-1] == "N":
                    lat = np.float64(lat_data.replace("N",""))
                elif lat_data[-1] == "S":
                    lat = np.float64(lat_data.replace("S",""))*-1
            
            # Ignore Z, this is a spurious entry according to JSR, and ignore D, this is debris objects. 
            # Set up the dictionary.                      
            if jsr_data_stripped_2020["Type"][reentry_count][:1] not in ["Z", "D"]:
                temp_reentry_dict = {
                    "id"           : jsr_data_stripped_2020["Piece"][reentry_count],
                    "name"         : jsr_data_stripped_2020["Name"][reentry_count],
                    "type"         : reentry_type,
                    "burnup"       : "Complete",
                    "reentry_stage": reentry_stage,  # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                    "time"         : time_utc,
                    "mon"          : monstr,
                    "day"          : daystr,
                    "lat"          : lat,
                    "lon"          : lon,
                    "mass"         : mass, 
                }
                
                self.unique_reentry_list.append(temp_reentry_dict) 
        ########################################
        # Load in all Aerospace Corp re-entries
        ########################################      
          
        # Now load the Aerospace Corp information, to see if we can fill in any missing time information.  
        print("Searching for Aerospace Corp re-entries.")
        aerospace_corp_data = pd.read_csv("./Databases/AerospaceCorp_Reentries.csv")
        
        # Check what items are already in the list.
        jsr_id_list = []
        for reentry in (self.unique_reentry_list):
            jsr_id_list.append(reentry["id"])
        
        # Add time information from Aerospace Corp for any JSR entries missing time information (20 items).
        for reentry in (self.unique_reentry_list):
            if reentry["time"] in [0,-1]:
                for reentry_count in range(len(aerospace_corp_data)): 
                    if aerospace_corp_data["International Designator"][reentry_count] == reentry["id"]:
                        reentry_time = aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][11:16]
                        reentry["time"] = np.float64(int(reentry_time[0:2]) + int(reentry_time[3:5]) / 60)
        
        # Now add any new entries.
        for reentry_count in range(len(aerospace_corp_data)):  
            if aerospace_corp_data["International Designator"][reentry_count] not in jsr_id_list:
                
                # 1992-021C, Ariane 44L H10+ 3rd Rocket Stage. DISCOSweb and AC list this as reentering in Oct 2020. JSR lists this as exploding in Apr 1993.
                # 2019-029Q, Starlink payload. DISCOSweb and JSR list this as reentering in July 2022. AC lists this as reentering in 2020. Ignoring.
                # 2020-012B, Starlink payload. DISCOSweb has no re-entry data. AC lists this as reentering Mar 2020. JSR lists this as still in orbit. Ignoring.
                if aerospace_corp_data["International Designator"][reentry_count] == "1992-021C":
                    
                    # Extract the UTC time.     
                    reentry_time = aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][11:16]
                    time_utc = np.float64(int(reentry_time[0:2]) + int(reentry_time[3:5]) / 60)
                    temp_reentry_dict = {
                        "id"           : aerospace_corp_data["International Designator"][reentry_count],
                        "name"         : aerospace_corp_data["Object Name"][reentry_count],
                        "type"         : aerospace_corp_data["Type"][reentry_count],
                        "burnup"       : "Complete",
                        "reentry_stage": 3,  # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris.
                        "time"         : time_utc,
                        "mon"          : aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][5:7],
                        "day"          : aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][8:10],
                        "lat"          : 0,
                        "lon"          : 0,
                        "mass"         : 2080, # From JSR.
                    }  
                    
                    self.unique_reentry_list.append(temp_reentry_dict)      
                    
        ########################################
        # Load in all DISCOSweb re-entries
        ######################################## 
        
        # Check what items are already in the list.
        jsr_ac_id_list = []
        for reentry in (self.unique_reentry_list):
            jsr_ac_id_list.append(reentry["id"]) 
        
        # All DISCOSweb data is contained within a netcdf file.
        print("Searching for DISCOSweb re-entries.")
        ds_dw = xr.open_dataset("/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/Databases/discosweb_reentries_2020.nc", decode_times=False)
        dsr = xr.open_dataset("/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/Databases/rocket_info_2020.nc", decode_times=False)
        dsl = xr.open_dataset("/home/ucfacb0/Emission_Inventory/Improved_Emission_Profile/Databases/launch_info_2020.nc", decode_times=False)
        
        for reentry_count in range(len(ds_dw["DISCOSweb_Reentry_ID"].values)):
            
            # Excluding Debris
            valid_types = ["Rocket Body","Rocket Mission Related Object","Payload Mission Related Object","Payload"]
            
            if (ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count] not in jsr_ac_id_list) and ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in valid_types:
                
                # Sort type, stage, mass.
                if ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] == "Rocket Body":
                    reentry_type = "R/B"
                    
                    if ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["Falcon 9 Merlin-V (1D+) (Falcon 9 v1.2)","H-II LE-5B (H-IIB)",
                                                                                 "L-53 (YF24B) (Long March (CZ) 2D)","CZ-5-HO (Long March (CZ) 5)"]:
                        reentry_stage = 2
                    elif ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["Fregat-M (Soyuz-ST-A Fregat-M)","Fregat (Soyuz-2-1B Fregat)", "Fregat-M (Soyuz-2-1B Fregat-M)"]:
                        reentry_stage = 3
                    elif ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["AVUM (Vega)","Ceres-1 upperstage"]:
                        reentry_stage = 4
                    else:
                        print("Missing stage designation for : ",ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count], ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count])
                        reentry_stage = 0
                
                    mass = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
                    if np.isnan(mass):
                        mass = 0
                        
                elif ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object","Payload"]:
                    if ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object"]:
                        reentry_type = "Component"
                    else: 
                        reentry_type = "Payload"
                    reentry_stage = 5
                    mass = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
                    if np.isnan(mass):
                        mass = 0
                
                day = int(ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][8:10])
                mon = int(ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][5:7])
                time_utc = -1
                lat = 0
                lon = 0
                
                # For all 2020 launches, if the reentry occurs on the same day as the launch, we can set the time and location using the launch.
                # For all pre-2020, 0 is sufficient.
                if ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][0:4] == "2020":
                    # Need to find the launch entry in the database and extract the time.
                    launch_ind = np.where(dsl["COSPAR_ID"].values == ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][0:8])
                    if len(launch_ind) > 1:
                        sys.exit("Multiple database entries found for a single launch.")
                    else:
                        if (day == int(dsl["Day"].values[launch_ind[0]])) and (mon == int(dsl["Month"].values[launch_ind[0]])):
                            time_utc = dsl["Time(UTC)"].values[launch_ind][0]
                            lat = dsl["Latitude"].values[launch_ind][0]
                            lon = dsl["Longitude"].values[launch_ind][0]
                            manual_loc = True
                elif int(ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][0:4]) < 2020:
                    time_utc = 0

                temp_reentry_dict = {
                    "id"           : ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count],
                    "name"         : ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count],
                    "type"         : reentry_type,
                    "burnup"       : "Complete",
                    "reentry_stage": reentry_stage, # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                    "time"         : time_utc,
                    "mon"          : mon,
                    "day"          : day,
                    "lat"          : lat,
                    "lon"          : lon,
                    "mass"         : mass, 
                    "manual_loc"   : manual_loc, 
                }
                
                self.unique_reentry_list.append(temp_reentry_dict)  
            
            else:
                # If the item already exists, check if the jsr entry is missing the mass information.
                # Only add if the jsr is missing the mass, and discosweb has the mass.
                # This is currently zero items, but leave this code in in case it is reused for future years.
                dict_ind = next((index for (index, d) in enumerate(self.unique_reentry_list) if d["id"] == ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count]), False)
                if dict_ind != False:
                    if (self.unique_reentry_list[dict_ind]["type"] == "Payload/Debris") and (self.unique_reentry_list[dict_ind]["payload_mass"] == 0):
                        if not np.isnan(ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]):
                            self.unique_reentry_list[dict_ind]["payload_mass"] = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
                            print("Added info for",ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count])                       
        
        ################################################
        # Assign as complete / partial reentry burn-up.
        ################################################
                
        # Falcon 9 reentries aren't included in reentry databases, so need to add manually. 26 launches in 2020. 
        # One launch was a suborbital abort test, so the 1st stage exploded after dragon escaped. Suborbital currently not included.
        for i in range(len(dsl["COSPAR_ID"])):
            if dsl["Rocket_Type"].values[i] == "Falcon 9 v1.2":
                
                if dsl["COSPAR_ID"].values[i] == "2020-086":
                    falcon_lat = dsl["Latitude"].values[i]
                    falcon_lon = dsl["Longitude"].values[i]
                else:
                    falcon_lat = 34
                    falcon_lon = -75
                temp_reentry_dict = {
                    "id"           : f'{dsl["COSPAR_ID"].values[i]}S1',
                    "name"         : f"{dsl['Rocket_Type'].values[i]} Stage 1",
                    "type"         : "R/B",
                    "burnup"       : "Partial",
                    "reentry_stage": 1, # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                    "time"         : dsl["Time(UTC)"].values[i],
                    "mon"          : int(dsl["Month"].values[i]),
                    "day"          : int(dsl["Day"].values[i]),
                    "lat"          : falcon_lat,
                    "lon"          : falcon_lon,
                    "mass"         : 27200 # SLR, this value was also used by Ryan22. 
                }

                self.unique_reentry_list.append(temp_reentry_dict)
               
        # Cygnus resupply missions are expendable. Cargo capsule on China resuable test operated "abnormally", and JSR lists as deorbited (read destroyed in atmosphere), so ignoring.    
        # These are geolocated using the landing site, as this is likely to be within the same GEOS-Chem grid as the reentry.
        for reentry in self.unique_reentry_list:
            if reentry["name"] in ["Soyuz MS-13","Soyuz MS-15","Soyuz MS-16","Crew Dragon DM-2","Dragon CRS-19", "Dragon CRS-20","XZF-SC"]:
                reentry["burnup"] = "Partial"
            if reentry["name"] == "Soyuz MS-13":
                reentry["lat"], reentry["lon"] = 47.78, 67.7    # https://www.nasaspaceflight.com/2020/02/record-setting-astronaut-return-earth/    
            if reentry["name"] == "Soyuz MS-15":   
                reentry["lat"], reentry["lon"] = 47.78, 67.7    # https://www.space.com/space-station-crew-lands-on-apollo-13-anniversary-exp62.html
            if reentry["name"] == "Soyuz MS-16":   
                reentry["lat"], reentry["lon"] = 47.78, 67.7    # https://www.nasa.gov/image-feature/support-personnel-arrive-at-the-soyuz-ms-16-spacecraft-landing-site
            if reentry["name"] == "Crew Dragon DM-2":
                reentry["lat"], reentry["lon"] = 30.42, -87.22  # https://www.nasaspaceflight.com/2020/08/demo2-splashdown-in-gulf/
            if reentry["name"] == "Dragon CRS-19":
                reentry["lat"], reentry["lon"] = 31.52, -120.40 # https://spaceflightnow.com/2020/01/07/dragon-cargo-capsule-brings-home-space-station-science-experiments/
            if reentry["name"] == "Dragon CRS-20":
                reentry["lat"], reentry["lon"] = 26.5, -117.5   # https://planet4589.org/space/jsr/back/news.777.txt
            if reentry["name"] == "XZF-SC":
                reentry["lat"], reentry["lon"] = 40.98, 100.21  # https://web.archive.org/web/20220102081307/http://www.xinhuanet.com/english/2020-05/08/c_139040336.htm 
            
        ###########################################################
        # Sort out MCS vs. Non MCS
        ###########################################################
        
        # Create a list of all MCS-related launches (from launch database), then assign all items from that launch as MCS.
        mcs_dict = {}
        for i in range(len(dsl["COSPAR_ID"])):
            mcs_dict[dsl["COSPAR_ID"].values[i]] = dsl["MCS_Check"].values[i]
        
        for reentry in (self.unique_reentry_list):
            try:
                reentry["MCS"] = mcs_dict[reentry["id"][:8]]
            except:
                if reentry["id"][:8] in ["2018-020","2019-029","2019-074"]:
                    reentry["MCS"] = True
                else:
                    reentry["MCS"] = False
                     
        ######################################
        # Add reentries for failed launches.
        ######################################
        
        add_failed_launches = True
        if add_failed_launches == True:
            print("Add failed launch re-entries.")
            # First check if any are already included.
            for reentry in self.unique_reentry_list:
                if reentry["id"][5:6] == "F":
                    sys.exit("Failed launch included in reentry databases. Code needs rewrite.")
            
            # When adding the wet mass, the dry mass + propellant mass has been used.
            
            # F01. Simorgh payload didn't reach orbit, failed during second or third flight.
            # Adding reentries from payload and all stages (dry mass).
            # Zafar 1 mass
            #       https://iranpress.com/content/18407/isa-head-satellite-imagery-from-orbit-530km-primary-mission-zafar-satellite
            #       https://space.skyrocket.de/doc_sdat/zafar.htm
            #       https://spaceflightnow.com/2020/02/10/iran-fails-in-satellite-launch-attempt/
            #       https://www.rferl.org/a/iran-says-satellite-launch-imminent-in-next-few-hours-/30424791.html 
            cospar_id = "F01"
            stages, pieces, masses = [5,1,2,3], ["A","B","C","D"], [113,12700,1600,230] 
            types, names = ["Payload","R/B","R/B","R/B"], ["Zafar 1","Simorgh S1","Simorgh S2","Simorgh S3"]
            time_utc, day, mon = np.float64(15 + 50/60), 9, 2
            lat, lon = 35.234338, 53.920601
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # Payload is secretive, so likely military with no official mass information. Some info available online, taking average:
            #       https://everydayastronaut.com/xjy-6-02-long-march-7a-2/ 6300 kg
            #       https://nextspaceflight.com/launches/details/2895       6800 kg
            # F02. Long March 7A (4 boosters plus first, second, third stage) failed near to start of second stage burn.
            # Adding payload reentries, dry mass reentry for first stage and boosters, and wet mass reentry for second and third stage.
            cospar_id = "F02"
            stages, pieces, masses = [5,0,1,2,3], ["A","B","C","D","E"], [6550,24000,12500,5500+65000,2800+18200]
            types, names = ["Payload","R/B","R/B","R/B","R/B"], ["XJY-6-01","Long March 7A B","Long March 7A S1","Long March 7A S2","Long March 7A S3"]
            time_utc, day, mon = np.float64(13 + 40/60), 16, 3
            lat, lon = 19.6,111
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # F03. Long March 3B/E (4 boosters plus first, second, third stage) failed at third stage.
            # Adding payload reentries, dry mass reentry for first and second stage and boosters, and wet mass reentry for third stage.
            # Palapa-N1 mass
            #       https://space.skyrocket.de/doc_sdat/palapa-n1.htm
            #       https://www.nasaspaceflight.com/2020/04/long-march-3b-launches-indonesian-satellite/
            cospar_id = "F03"
            stages, pieces, masses = [5,0,1,2,3], ["A","B","C","D","E"], [5550,13200,9200,5000,2800+18193] # Mass info for payload (may need checking) at https://www.nasaspaceflight.com/2020/04/long-march-3b-launches-indonesian-satellite/ 
            types, names = ["Payload","R/B","R/B","R/B","R/B"], ["Palapa-N1","Long March 3B/E B","Long March 3B/E S1","Long March 3B/E S2","Long March 3B/E S3"]
            time_utc, day, mon = np.float64(11 + 45/60), 9, 4
            lat, lon = 28.2,102
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # F04. LauncherOne (2 stages, air launched) failed after a few seconds of 1st stage burn. This occured at ~ 10.7km (https://web.archive.org/web/20220406013823/http://www.spacelaunchreport.com/launcherone.html)
            # Therefore we can safely ignore as it did not reach an altitude where reentry is possible.

            # F05. Electron (Curie) (3 stages) failed at second stage.
            # Adding payload reentries, dry mass reentry for first stage and wet mass reentry for second and third stage.
            # Payload masses:
            #       https://spacenews.com/rocket-lab-electron-launch-fails/                                         67  / N/A / N/A kg
            #       https://spaceflightnow.com/2020/07/04/rocket-lab-satellite-launch-fails-before-reaching-orbit/  67  / N/A / N/A kg
            #       https://pubs.usgs.gov/of/2021/1030/f/ofr20211030f.pdf                                           N/A / 5.8 /     kg
            #       JSR lists the re-flight of the same satellite (which hosts other payloads itself) as 10 kg.     N/A / N/A / 10  kg
            cospar_id = "F05"
            stages, pieces, masses = [5,5,5,1,2,3], ["A","B","C","D","E","F"], [67,5.8*5,10,950,250+2050,40+245]
            types, names = ["Payload","Payload","Payload","R/B","R/B","R/B"], ["CE-SAT-IB","SuperDovex5","Faraday 1","Electron (Curie) S1","Electron (Curie) S2","Electron (Curie) S3"]
            time_utc, day, mon = np.float64(21 + 21/60), 4, 7
            lat, lon = -39.2609,177.8655
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # F06. Kuaizhou-11 (3 stages) failed at second stage.
            # Adding payload reentries, dry mass reentry for first and second stage and wet mass reentry for third stage.
            # Payloads:
            #       https://spaceflightnow.com/2020/07/10/new-chinese-satellite-launcher-fails-on-first-flight/ 172 / ~100 kg
            #       https://web.archive.org/web/20220406013817/http://www.spacelaunchreport.com/kz11.html       230 / 97   kg
            #       https://space.skyrocket.de/doc_sdat/centispace-1.htm                                        N/A / 97   kg
            cospar_id = "F06"
            stages, pieces, masses = [5,5,1,2,3], ["A","B","C","D","E"], [201,97,7530,1490,1000+480]
            types, names = ["Payload","Payload","R/B","R/B","R/B"], ["Jilin-1 Gaofen-02E","Xiangrikui 2","Kuaizhou-11 S1","Kuaizhou-11 S2","Kuaizhou-11 S3"]
            time_utc, day, mon = np.float64(4 + 19/60), 10, 7
            lat, lon = 41.3,100.3
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # F07. Astra Rocket 3 (2 stages) shut off after 20s, fell to Earth near landing site. Ignoring.
            
            # F08. Kuaizhou-1A (4 stages) failed at upper stage. 1st stage is potentially too low for reentry so ignoring.
            # Adding payload reentries, dry mass reentry for second and third stage and wet mass reentry for fourth stage.
            # Jilin-1 Gaofen-02C Mass:
            #       https://web.archive.org/web/20220406013741/http://www.spacelaunchreport.com/kz.html  230 kg
            #       https://www.nasaspaceflight.com/2019/11/kuaizhou-1a-launches-jilin-1-gaofen-2a/ (2A) 230 kg
            #       https://space.skyrocket.de/doc_sdat/jilin-1-kuanfu-02.htm                       (2A) 230 kg   
            cospar_id = "F08"
            stages, pieces, masses = [5,2,3,4], ["A","B","C","D"], [230,686,183,200+1000]
            types, names = ["Payload","R/B","R/B","R/B"], ["Jilin-1 Gaofen-02C","Kuaizhou-1A S2","Kuaizhou-1A S3","Kuaizhou-1A S4"]
            time_utc, day, mon = np.float64(5 + 2/60), 12, 9
            lat, lon = 41.3,100.3
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # F09. Vega (4 stages) failed at upper stage. 1st stage is potentially too low for reentry so ignoring.
            # Adding payload reentries, dry mass reentry for second and third stage and wet mass reentry for fourth stage.
            # https://www.arianespace.com/wp-content/uploads/2020/11/VV17-launchkit-EN2.pdf 
            # https://spaceflightnow.com/2020/11/17/arianespace-traces-cause-of-vega-launch-failure-to-human-error/ 
            # https://spaceflightnow.com/2020/11/17/european-vega-rocket-suffers-second-failure-in-three-launches/ 
            # https://web.archive.org/web/20220406013740/http://www.spacelaunchreport.com/vega.html
            cospar_id = "F09"
            stages, pieces, masses = [5,5,2,3,4], ["A","B","C","D","E"], [750,175,2486,1433,688+550]
            types, names = ["Payload","Payload","R/B","R/B","R/B"], ["SEOSat-Ingenio","TARANIS","Vega S2","Vega S3","Vega S4"]
            time_utc, day, mon = np.float64(1 + 55/60), 17, 11
            lat, lon = 5.2,-52.8
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # F10. Astra Rocket 3 (2 stages), stage 2 depleted propellant 15-20 seconds early, falling short of orbit. No payloads.
            # Adding dry mass reentry for first and second stage.
            cospar_id = "F10"
            stages, pieces, masses = [1,2], ["A","B"], [950,250]
            types, names = ["R/B","R/B"], ["Astra Rocket 3 S1","Astra Rocket 3 S2"]
            time_utc, day, mon = np.float64(20 + 52/60), 15, 12
            lat, lon = 57.6,-152.2
            self.add_failed_launch(cospar_id,stages,pieces,masses,types,names,time_utc,mon,day,lat,lon)
            
            # F11. Moon launch so ignoring.

        #self.print_stats()
        
        ########################################################
        # Add remaining missing rocket launches and extra info.
        ########################################################
        
        print("Adding missing booster / 1st stage re-entries.")
        # Based on rocket configurations, boosters will cutoff and detach above 50km for all configs except B+4S.  
        # So for B+1/2S and B+3S, we need a reentry event for each lost booster at the launch site.
        # For B+4S, 2S and 3S, the 1st stage will cutoff and detach within 100 km altitude, so we need a reentry event for each of these.

        # This just checks what boosters have been added, its currently 0.
        booster_list = []
        for count, reentry in enumerate(self.unique_reentry_list):
            if (reentry["id"][:4] == "2020") and (reentry["type"] == "R/B") and (reentry["reentry_stage"] == 0):
                booster_list.append(reentry["id"][:8])
        
        # This just checks what 1st stages have been added, its currently all the Falcon reentries. 
        first_stage_list = []
        for count, reentry in enumerate(self.unique_reentry_list):
            if (reentry["id"][:4] == "2020") and (reentry["type"] == "R/B") and (reentry["reentry_stage"] == 1):
                first_stage_list.append(reentry["id"][:8])               
                      
        for i in range(len(dsl["COSPAR_ID"])):
            # First add the boosters.
            for count, rocket_name in enumerate(dsr["Rocket_Name"].values):
                if rocket_name == dsl["Rocket_Type"].values[i]: 
                    
                    # Filter to only B+1/2S and B+3S rockets and add all boosters (all missing in original inventories).
                    if (dsr["Booster_PropMass"].values[count] != 0) and (dsr["Stage4_PropMass"].values[count] == 0) and (dsl["COSPAR_ID"].values[i][:8] not in booster_list):
                        
                        mass = dsr["Booster_StageMass"].values[count]
                        if np.isnan(mass):
                            mass = 0
                            
                        temp_reentry_dict = {
                            "id"           : f'{dsl["COSPAR_ID"].values[i]}B',
                            "name"         : f"{dsl['Rocket_Type'].values[i]} Booster",
                            "type"         : "R/B",
                            "burnup"       : "Complete",
                            "reentry_stage": 0, # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                            "time"         : dsl["Time(UTC)"].values[i],
                            "mon"          : int(dsl["Month"].values[i]),
                            "day"          : int(dsl["Day"].values[i]),
                            "lat"          : dsl["Latitude"].values[i],
                            "lon"          : dsl["Longitude"].values[i],
                            "mass"         : mass,
                            "MCS"          : False,
                            "manual_loc"   : True,
                        }

                        self.unique_reentry_list.append(temp_reentry_dict)
                    
                    # Filter to only B+4S, 2S and 3S rockets and add all missing 1st stages (all missing in original inventories).
                    if (dsl["COSPAR_ID"].values[i][:8] not in first_stage_list) and (dsl["COSPAR_ID"].values[i][5] != "F"):
                        if ((dsr["Booster_PropMass"].values[count] == 0) and (dsr["Stage4_PropMass"].values[count] == 0)) or ((dsr["Booster_PropMass"].values[count] != 0) and (dsr["Stage4_PropMass"].values[count] != 0)):                    
                            mass = dsr["Stage1_StageMass"].values[count]
                            if np.isnan(mass):
                                mass = 0
                                
                            temp_reentry_dict = {
                                "id"           : f'{dsl["COSPAR_ID"].values[i]}S1',
                                "name"         : f"{dsl['Rocket_Type'].values[i]} Stage 1",
                                "type"         : "R/B",
                                "burnup"       : "Complete",
                                "reentry_stage": 1, # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                                "time"         : dsl["Time(UTC)"].values[i],
                                "mon"          : int(dsl["Month"].values[i]),
                                "day"          : int(dsl["Day"].values[i]),
                                "lat"          : dsl["Latitude"].values[i],
                                "lon"          : dsl["Longitude"].values[i],
                                "mass"         : mass,
                                "MCS"          : False,
                                "manual_loc"   : True,
                            }

                            self.unique_reentry_list.append(temp_reentry_dict)
          
        # Final missing mass info.
        # For West Ford dipoles, these are part of the West Ford Needles project. # https://space.skyrocket.de/doc_sdat/westford.htm
        # The needles each weigh 40 ng, and one 'clump' reentered in 2020. The needles are Copper, and so will not contribute to Al emissions.   
        for count, reentry in enumerate(self.unique_reentry_list):
            if reentry["name"] == "CZ-2C sep motor cover":
                # The same item is also listed as weighing 1 kg.
                reentry["mass"] = 1
            if reentry["id"] == "2020-086B":
                reentry["lon"] = 179.9
            if reentry["name"] == "Ceres-1 upperstage":
                reentry["mass"] = 200 
            # Set time to midnight whenever the reentry is occurs on a different day than the launch and no time info is available.
            if reentry["time"] == -1:  
                for count, launch_id in enumerate(dsl["COSPAR_ID"].values):
                    if reentry["id"][:8] == launch_id:
                        if (int(reentry["mon"]) == int(dsl["Month"].values[count])) and (int(reentry["day"]) == int(dsl["Day"].values[count])):
                            pass
                        else:    
                            reentry["time"] = 0
            if "manual_loc" not in reentry:
                reentry["manual_loc"] = False

        dsl.close()
        dsr.close()
        ds_dw.close()
        
        self.print_stats()
        
    def reentry_info_to_netcdf(self):
        """This saves the reentry information as a NetCDF file for later processing for GEOS-Chem.
        This is only needed if using GEOS-Chem. Recommended to ignore if you don't need this.
        """        
        #Set up the dimensions of the netcdf file.
        dims = ('reentries')
        
        #Set up the data
        id_list, name_list, type_list, burnup_list = [], [], [], []
        stage_list, time_list,  mon_list , day_list  = [], [], [], []
        lat_list,  lon_list,  mass_list, mcs_list, manual_loc_list  = [], [], [], [], []
        
        for reentry in self.unique_reentry_list:
            id_list.append(reentry["id"])
            name_list.append(reentry["name"])
            type_list.append(reentry["type"])
            burnup_list.append(reentry["burnup"])
            stage_list.append(reentry["reentry_stage"])
            time_list.append(reentry["time"])
            mon_list.append(reentry["mon"])
            day_list.append(reentry["day"])
            lat_list.append(reentry["lat"])
            lon_list.append(reentry["lon"])
            mass_list.append(reentry["mass"])
            mcs_list.append(reentry["MCS"])
            manual_loc_list.append(reentry["manual_loc"])    
        #print(type(id_list),id_list)
            
        #Create the DataArrays.
        data_da_id           = xr.DataArray(id_list,         dims=dims, attrs=dict(long_name="Reentry ID"))
        data_da_name         = xr.DataArray(name_list,       dims=dims, attrs=dict(long_name="Reentry Name"))
        data_da_type         = xr.DataArray(type_list,       dims=dims, attrs=dict(long_name="Reentry Type"))
        data_da_burnup       = xr.DataArray(burnup_list,     dims=dims, attrs=dict(long_name="Reentry Burnup Flag"))
        data_da_stage        = xr.DataArray(stage_list,      dims=dims, attrs=dict(long_name="Reentry Stage"))
        data_da_time         = xr.DataArray(time_list,       dims=dims, attrs=dict(long_name="Reentry Time (UTC)"))
        data_da_mon          = xr.DataArray(mon_list,        dims=dims, attrs=dict(long_name="Reentry Month"))
        data_da_day          = xr.DataArray(day_list,        dims=dims, attrs=dict(long_name="Reentry Day"))
        data_da_lat          = xr.DataArray(lat_list,        dims=dims, attrs=dict(long_name="Reentry Latitude", units="Degrees"))
        data_da_lon          = xr.DataArray(lon_list,        dims=dims, attrs=dict(long_name="Reentry Longitude", units="Degrees"))
        data_da_mass         = xr.DataArray(mass_list,       dims=dims, attrs=dict(long_name="Reentry Booster Mass", units="kg"))
        data_da_mcs          = xr.DataArray(mcs_list,        dims=dims, attrs=dict(long_name="Reentry MCS Check"))
        data_da_manual_loc   = xr.DataArray(manual_loc_list, dims=dims, attrs=dict(long_name="Reentry Manual Location Check"))
    
        # Create an xarray Dataset from the DataArrays.
        ds = xr.Dataset()
        ds['RE_ID']          = data_da_id
        ds['RE_Name']        = data_da_name
        ds['RE_Type']        = data_da_type
        ds['RE_Burnup']      = data_da_burnup
        ds['RE_Stage']       = data_da_stage
        ds['RE_Time']        = data_da_time
        ds['RE_Mon']         = data_da_mon
        ds['RE_Day']         = data_da_day
        ds['RE_Lat']         = data_da_lat
        ds['RE_Lon']         = data_da_lon
        ds['RE_Mass']        = data_da_mass
        ds['RE_MCS']         = data_da_mcs
        ds['RE_Manual_Loc']  = data_da_manual_loc
             
        #Save to file and close the DataSet     
        ds.to_netcdf(f'./Databases/reentry_info_{year}.nc')
        ds.close()
        
if __name__ == "__main__":
    """The main running of the program goes here. 
    All of the functions are inside the build_reentry_list class.
    Call each of the functions using build_reentry_list._function_
    e.g. build_reentry_list.launches_per_year(start_year,end_year)
    """         
    
    # Set up the arguments for each function.
    parser = argparse.ArgumentParser()
    parser.add_argument('-yr', "--yearly_reentries", action='store_true', help='Get reentry info.')
    parser.add_argument('-syr', "--save_reentry_info", action='store_true', help='Save reentry info.')
    parser.add_argument('-sy', "--start_year", default = "2020", choices=str(np.arange(1957,2023)), help='Start Year.')
    parser.add_argument('-fy', "--final_year", default = "2020", choices=str(np.arange(1957,2023)), help='Final Year.')
    args = parser.parse_args()
    
    # Sort out the year range.
    start_year = int(args.start_year)
    final_year = int(args.final_year)
    if start_year > final_year:
        final_year = start_year + 1
    print(f"Processing from year {start_year} to {final_year}.")
    year_range = np.arange(start_year,final_year+1)    
    
    #Loop over all years and run functions depending on input arguments.
    for year in year_range:
        Data = build_reentry_list(year)
        if args.yearly_reentries == True:
            Data.get_reentry_info()
            if args.save_reentry_info == True:
                Data.reentry_info_to_netcdf()