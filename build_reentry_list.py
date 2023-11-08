import numpy as np
import argparse
import xarray as xr
import pandas as pd
from datetime import datetime
import sys
import random
import geopandas as gpd
from shapely.geometry import Point, Polygon

class build_reentry_list:
    
    def __init__(self,year):
        """This function sets up the class.

        Args:
            year (_type_): The year.
        """        
        
        self.year = year
    
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
        geolocated_mass_percent = geolocated_mass / total_mass * 100
        print(f"Geolocation (All): {geo_percent_all:.0f}%.")
        print(f"Timed (All):       {time_percent_all:.0f}%.")    
        print(f"Mass (All):        {mass_percent_all:.0f}%.")
        print(f"Geolocated Mass:   {geolocated_mass_percent:.0f}%.")
        
    def convert_lat_lon(self,latlonstr,inc):
        # TODO: No location information for lower stages in lcat or rcat, set using launch data.
        manual_loc = True
        if inc > 90:
            inc = 180-inc
        if latlonstr == "-":
            lat = 0 
            lon = 0
        elif latlonstr == "Alashan": 
            # Landing expected east of Jiuquan launch site (this was actually launched from Wenchang).
            # Assuming that Alashan refers to Helen Shan Mountain (new name for Alashan Mountain).
            # https://space.skyrocket.de/doc_sdat/rcs-fc-sc.htm
            # https://planet4589.org/space/jsr/news.778
            # https://www.peakbagger.com/peak.aspx?pid=10693
            # https://www.nasaspaceflight.com/2020/05/china-next-generation-crew-capsule/
            lat = 38.833
            lon = 105.95
        elif latlonstr == "Jiuquan":
            # This refers to the Chinese launch center, sources say it landed 'in the desert near Jiuquan', and 'in China’s Inner Mongolia autonomous region'.
            # Using lat/lon for Jiuquan launch site.
            # https://discosweb.esoc.esa.int/launch-sites/35
            # https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=2020-027A
            # https://space.skyrocket.de/doc_sdat/xzf-sc.htm 
            # https://spaceflightnow.com/2020/05/08/chinas-next-generation-crew-spacecraft-lands-after-unpiloted-test-flight/ 
            lat = 19.6
            lon = 111.0               
        elif latlonstr == "LOPNOR RW05":
            # Reported test flight of a Chinese reusable experimental spacecraft.
            # Runway 05/22 at Lop Nor air base in Xinjiang (https://planet4589.org/space/gcat/data/tables/lp.html).
            # https://www.seradata.com/china-launches-own-mini-spaceplane-reusable-spacecraft-using-long-march-2f 
            # https://twitter.com/planet4589/status/1302486141090885632                
            lat = 40.78
            lon = 89.27
        elif latlonstr in ["Antarctic?", "Arctic", "E Pacific", "E Pacific?", "S Ocean", "S Ocean?", "Indian O?", "S of Tasmania?", "SE IOR?", 
                           "OCISLY", "JRTI", "AO", "Ms. Tree, AO", "Ms. Chief,AO", "Ms. Chief? AO", "Ms. Chief, AO", "PO", "Ocean"]:
            lat = 0
            lon = 0
        # TODO: This takes a long time so only enable later when everything else is done.
        #elif latlonstr == "Antarctic?":
        #    # TODO: Assuming this to mean south of 60S. Check with Jonathan.
        #    while True:
        #        lat = round(random.uniform(-inc, inc),2)
        #        lon = round(random.uniform(-180, 180),2)
        #        coordinate = Point(lon,lat)
        #        if lat <= -60:
        #            break 
        #elif latlonstr == "Arctic":
        #    # TODO: Check with Jonathan, Arctic means Arctic Ocean, not just above 66N?
        #    arctic = self.ocean_shapefile[self.ocean_shapefile.name.isin(['Arctic Ocean'])] 
        #    while True:
        #        lat = round(random.uniform(-inc, inc),2)
        #        lon = round(random.uniform(-180, 180),2)
        #        coordinate = Point(lon,lat)
        #        if arctic.geometry.contains(coordinate).any():
        #            break 
        #elif latlonstr in ["E Pacific", "E Pacific?"]:
        #    while True:
        #        random_location = self.pacific_union.sample_points(1).get_coordinates()
        #        lon = random_location["x"].values[0]
        #        lat = random_location["y"].values[0]
        #        if -inc <= lat <= inc and -180 <= lon <= -60: # Bounded to East Pacific only.
        #            break 
        #elif latlonstr in ["S Ocean", "S Ocean?"]:
        #    # For these three objects in auxcat, the inclination is 51.65-53.
        #    # This is outside of the general definition of the southern ocean (<60S).
        #    # Therefore we will just set the lat to the inclination.
        #    lat = -inc
        #    lon = round(random.uniform(-180, 180),2)
        #elif latlonstr in ["Indian O?"]:
        #    indian_ocean = self.ocean_shapefile[self.ocean_shapefile.name.isin(['Indian Ocean'])] 
        #    while True:
        #        lat = round(random.uniform(-inc, inc),2)
        #        lon = round(random.uniform(-180, 180),2)
        #        coordinate = Point(lon,lat)
        #        if indian_ocean.geometry.contains(coordinate).any():
        #            break 
        #elif latlonstr in ["S of Tasmania?"]:
        #    lon_lat_list = [[153.23, -30.02],[146.83, -43.64],[166.00, -50.92], [167.53, -47.29], [168.14, -46.85], [168.85, -46.66], [174.28, -41.72], [175.28, -41.62], [173.01, -34.39]]
        #    tasman_sea_geom = Polygon(lon_lat_list)
        #    tasman_sea = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[tasman_sea_geom])
        #    while True:
        #        lat = round(random.uniform(-inc, inc),2)
        #        lon = round(random.uniform(-180, 180),2)
        #        coordinate = Point(lon,lat)
        #        if tasman_sea.geometry.contains(coordinate).any():
        #            break 
        #elif latlonstr in ["SE IOR?"]:
        #    indian_ocean = self.ocean_shapefile[self.ocean_shapefile.name.isin(['Indian Ocean'])] 
        #    while True:
        #        lat = round(random.uniform(-inc, -30),2)
        #        lon = round(random.uniform(77, 180),2)
        #        coordinate = Point(lon,lat)
        #        if indian_ocean.geometry.contains(coordinate).any():
        #            break 
        elif latlonstr.replace("?","").split()[0][-1] in ["E","W","S","N"]:
            manual_loc = False
            geolocation = latlonstr.replace("?","").split()
            if geolocation[0][-1] in ["E","W"]: # If the longitude comes first.
                lon_data = geolocation[0]
                lat_data = geolocation[1]
            elif geolocation[1][-1] in ["E","W"]: # If the longitude comes last.
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
        else:
            lat = 0
            lon = 0
            print(f"Need to sort out geolocation for {latlonstr}")
        return lat, lon, manual_loc
    
    def convert_time(self,date,launch_id_year):
    
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
            if int(launch_id_year) < 2020:
                time_utc = 0
            else:
                time_utc = -1  
        
        return monstr, daystr, time_utc 
     
    def extract_jsr_info(self, filepath, year):
        
        # Check what items are already in the list.
        self.jsr_id_list = []
        for reentry in (self.unique_reentry_list):
            self.jsr_id_list.append(reentry["id"])
        
        jsr_data = pd.read_csv(filepath, delimiter='\t', dtype=object)
        # Only include R (Reentry), D (Deorbit), or L (Landed) events.
        jsr_data_stripped = jsr_data[jsr_data["Status"].isin(["R","D","L","L?","AR","S","AR IN", "AL IN"])].reset_index(drop=True)
        
        # If the reentry occured in 2020 and apogee was above 50 km, then extract that row and build a new dataframe.
        # For apogee, this really only affects the lcat, which includes suborbital objects with apogees below 80 km.
        jsr_data_stripped_2020_list = []
        for reentry_count in range(len(jsr_data_stripped)):
            
            # For some reason, there are 4 CZ-8 boosters listed in JSR rcat for 2020-102.
            # Should only be two, and mass looks correct for each booster. Removing two.
            if jsr_data_stripped["DDate"][reentry_count][0:4] != "-" and jsr_data_stripped["#JCAT"][reentry_count] not in ["R80054","R80055"]:
            
                if (
                    int(jsr_data_stripped["DDate"][reentry_count][0:4]) == year
                    and (int(jsr_data_stripped["Apogee"][reentry_count]) >= 50 or int(jsr_data_stripped["Apogee"][reentry_count]) == -54771)            
                    and jsr_data_stripped["Piece"][reentry_count][5:6] not in  ["F","U","S"]
                    and jsr_data_stripped["Primary"][reentry_count] not in ["Bennu", "Venus", "Luna"]
                ):
                    
                    jsr_data_stripped_2020_list.append(jsr_data_stripped.iloc[[reentry_count]])
        jsr_data_stripped_2020 = pd.concat(jsr_data_stripped_2020_list, ignore_index=True)
        
        # Now loop over the list and format into a dictionary.
        for reentry_count in range(len(jsr_data_stripped_2020)):
            
            if "fairing" in jsr_data_stripped_2020["Name"][reentry_count].lower():
                print(jsr_data_stripped_2020["Type"][reentry_count][:1], jsr_data_stripped_2020["DryMass"][reentry_count])
            
            jsr_id = jsr_data_stripped_2020["Piece"][reentry_count] 
            jsr_name = jsr_data_stripped_2020["Name"][reentry_count]
            burnup = "Complete"
                
            #if jsr_data_stripped_2020["Piece"][reentry_count] in self.jsr_id_list:
                #print(jsr_data_stripped_2020["Piece"][reentry_count])
                
            # Duplicates:
            #   2019-036H. This is TEPCE 1 and TEPCE 2, listed with same "Piece" in JSR. TEPCE 2 listed as 2019-036IA in DISCOSweb, so renaming to this.
            #   2020-027A. This is Xinyidai Zairen Feichuan (XZF) and XZF Service Module (not in DISCOSweb). Setting auxcat id to XZF 2020-027D.
            #   Remaining are where multiple objects in auxcat from same launch are just given the COSPAR ID of the launch.
            if jsr_data_stripped_2020["Name"][reentry_count] == "TEPCE 2":
                jsr_id = "2019-036IA" 
            elif jsr_data_stripped_2020["Name"][reentry_count] == "XZF Service Module":
                jsr_id = "2020-027D"  
            elif jsr_data_stripped_2020["Piece"][reentry_count] == "2020-078B":
                jsr_name = "Falcon 9-098 Stage 2"
                
            # Sort out the reentry time/date.
            monstr, daystr, time_utc = self.convert_time(jsr_data_stripped_2020["DDate"][reentry_count].split(),jsr_data_stripped_2020["Piece"][reentry_count][0:4]) 
                
            # Sort out the reentry lat/lon.
            if "Falcon 9 Stage 1" in jsr_name:
                # TODO: We can probably make this even more accurate by looking for groundtrack info directly from Raul's Space Map.
                # TODO: Mass seems low (12400, was 27200 in Ryan 22 and on SLR).
                manual_loc = True
                burnup = "Partial"
                if jsr_id == "2020-086":
                    lat = 34.7
                    lon = -120.6
                else:
                    lat = 34
                    lon = -75
            else:   
                lat, lon, manual_loc = self.convert_lat_lon(jsr_data_stripped_2020["Dest"][reentry_count],np.float64(jsr_data_stripped_2020["Inc"][reentry_count]))
        
            # Handle rocket bodies.
            if jsr_data_stripped_2020["Type"][reentry_count][:1] == "R":
                
                # Sort out the rocket stages.
                reentry_stage = int(jsr_data_stripped_2020["Type"][reentry_count][1:2])
                if "Blok-BVGD" in jsr_data_stripped_2020["Bus"][reentry_count]:
                    reentry_stage = 0
                if "Blok-A" in jsr_data_stripped_2020["Bus"][reentry_count]:
                    reentry_stage = 1
                elif "Blok-I" in jsr_data_stripped_2020["Name"][reentry_count]:
                    reentry_stage = 2
                elif "Fregat" in jsr_data_stripped_2020["Name"][reentry_count]:
                    reentry_stage = 3
                elif jsr_data_stripped_2020["Piece"][reentry_count] == "2020-028C":
                    reentry_stage = 4  
                reentry_type = "R/B"
                
            # Handle categories for P for Payload (for orbital attempt), and C for Component. 
            elif jsr_data_stripped_2020["Type"][reentry_count][:1] in ["C","P"]:
                reentry_stage = 5
                if jsr_data_stripped_2020["Type"][reentry_count][:1] == "C":
                    reentry_type = "Component"
                elif jsr_data_stripped_2020["Type"][reentry_count][:1] == "P":
                    reentry_type = "Payload"      
            
            # Ignore Z, this is a spurious entry according to JSR, and ignore D, this is debris objects. 
            # Set up the dictionary.                      
            if jsr_data_stripped_2020["Type"][reentry_count][:1] not in ["Z", "D"]:
                temp_reentry_dict = {
                    "id"           : jsr_id,
                    "name"         : jsr_name,
                    "type"         : reentry_type,
                    "burnup"       : burnup,
                    "reentry_stage": reentry_stage,  # -1 is nothing, B1-4 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                    "time"         : time_utc,
                    "mon"          : monstr,
                    "day"          : daystr,
                    "lat"          : lat,
                    "lon"          : lon,
                    "mass"         : np.float64(jsr_data_stripped_2020["DryMass"][reentry_count]),
                    "inc"          : np.float64(jsr_data_stripped_2020["Inc"][reentry_count]),
                    "manual_loc"   : manual_loc,
                }
                
                self.unique_reentry_list.append(temp_reentry_dict)   
                         
    def get_reentry_info(self):
        
        pd.set_option('display.max_rows', None)
        
        # TODO: Make sure to add this back in later.
        #self.ocean_shapefile = gpd.read_file("./Databases/GOaS_v1_20211214/goas_v01.shp")
        #pacific = self.ocean_shapefile[self.ocean_shapefile.name.isin(['North Pacific Ocean','South Pacific Ocean'])]
        #self.pacific_union = gpd.GeoDataFrame(geometry=[pacific.unary_union])       
             
        self.unique_reentry_list = []
        
        print("Adding JSR re-entries.")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/satcat_2ndNov.tsv", 2020) # Load in the JSR satcat database.
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/auxcat_2ndNov.tsv", 2020) # Load in the JSR auxcat database.
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/lcat_2ndNov.tsv", 2020)   # Load in the JSR lcat database.
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/rcat_2ndNov.tsv", 2020)   # Load in the JSR rcat database.
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/lprcat_2ndNov.tsv", 2020) # Load in the JSR lprcat database.
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/deepcat_7thNov.tsv", 2020) # Load in the JSR deepcat database.
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/ecat_7thNov.tsv", 2020) # Load in the JSR ecat database.
        
        # lcat is mainly suborbital rocket stages and 11 objects from suborbital launches (separate object for each booster).
        # rcat contains lots of fairings and more lower rocket stages.
        # lprcat contains a few objects returning to Earth from space.
        # deepcat only contains a few objects.   
        # Nothing of use in hcocat.
        # Nothing of use in tmpcat.
        # Nothing of use in csocat.
        
        # TODO: add ecat.
        
        # Update the id list.
        self.jsr_id_list = []
        for reentry in self.unique_reentry_list:
            self.jsr_id_list.append(reentry["id"])
            
        # Check for boosters and rename the reentry_stage to B1-B4.
        booster_id_list = []
        for reentry in self.unique_reentry_list:
            if reentry["reentry_stage"] == 0:
                booster_id_list.append(reentry["id"])
        booster_id_list = sorted(list(set(booster_id_list)))
        for booster_id in booster_id_list:
            count = 1
            for reentry in self.unique_reentry_list:
                if reentry["id"] == booster_id and reentry["reentry_stage"] == 0:
                    reentry["reentry_stage"] = "B" + str(count)
                    count += 1
        
          
        
        # TODO: Add ftocat.
        # TODO: Crewed modules only listed as docked with ISS, not as reentered. Need to find in ecat.
        
        # This code checks for reentries with the same name.
        # TODO: Do this after everything is added to check for duplicates.         
        self.jsr_name_list = []
        for reentry in self.unique_reentry_list:
            self.jsr_name_list.append(reentry["name"])
        duplicate_name_list = []
        for jsr_name in self.jsr_name_list:
            if self.jsr_name_list.count(jsr_name) > 1:
                duplicate_name_list.append(jsr_name)
        duplicate_name_list = sorted(list(set(duplicate_name_list)))
        #for item in duplicate_name_list:
            #print(item)
        
        
        #########################################
        ## Load in all Aerospace Corp re-entries
        #########################################      
        #  
        ## Now load the Aerospace Corp information, to see if we can fill in any missing time information.  
        #print("Searching for Aerospace Corp re-entries.")
        #aerospace_corp_data = pd.read_csv("./Databases/Reentry/AerospaceCorp/AerospaceCorp_Reentries.csv")
        #
        ## Check what items are already in the list.
        #jsr_id_list = []
        #for reentry in (self.unique_reentry_list):
        #    jsr_id_list.append(reentry["id"])
        #
        ## Add time information from Aerospace Corp for any JSR entries missing time information (20 items).
        #for reentry in (self.unique_reentry_list):
        #    if reentry["time"] in [0,-1]:
        #        for reentry_count in range(len(aerospace_corp_data)): 
        #            if aerospace_corp_data["International Designator"][reentry_count] == reentry["id"]:
        #                reentry_time = aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][11:16]
        #                reentry["time"] = np.float64(int(reentry_time[0:2]) + int(reentry_time[3:5]) / 60)
        #
        ## Now add any new entries.
        #for reentry_count in range(len(aerospace_corp_data)):  
        #    if aerospace_corp_data["International Designator"][reentry_count] not in jsr_id_list:
        #        
        #        # 1992-021C, Ariane 44L H10+ 3rd Rocket Stage. DISCOSweb and AC list this as reentering in Oct 2020. JSR lists this as exploding in Apr 1993.
        #        # 2019-029Q, Starlink payload. DISCOSweb and JSR list this as reentering in July 2022. AC lists this as reentering in 2020. Ignoring.
        #        # 2020-012B, Starlink payload. DISCOSweb has no re-entry data. AC lists this as reentering Mar 2020. JSR lists this as still in orbit. Ignoring.
        #        if aerospace_corp_data["International Designator"][reentry_count] == "1992-021C":
        #            
        #            # Extract the UTC time.     
        #            reentry_time = aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][11:16]
        #            time_utc = np.float64(int(reentry_time[0:2]) + int(reentry_time[3:5]) / 60)
        #            temp_reentry_dict = {
        #                "id"           : aerospace_corp_data["International Designator"][reentry_count],
        #                "name"         : aerospace_corp_data["Object Name"][reentry_count],
        #                "type"         : aerospace_corp_data["Type"][reentry_count],
        #                "burnup"       : "Complete",
        #                "reentry_stage": 3,  # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris.
        #                "time"         : time_utc,
        #                "mon"          : aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][5:7],
        #                "day"          : aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][8:10],
        #                "lat"          : 0,
        #                "lon"          : 0,
        #                "mass"         : 2080, # From JSR.
        #            }  
        #            
        #            self.unique_reentry_list.append(temp_reentry_dict)      
        #            
        #########################################
        ## Load in all DISCOSweb re-entries
        ######################################### 
        #
        ## Check what items are already in the list.
        #jsr_ac_id_list = []
        #for reentry in (self.unique_reentry_list):
        #    jsr_ac_id_list.append(reentry["id"]) 
        #
        ## All DISCOSweb data is contained within a netcdf file.
        #print("Searching for DISCOSweb re-entries.")
        ds_dw = xr.open_dataset("./Databases/Reentry/discosweb_reentries_2020.nc", decode_times=False)
        dsr = xr.open_dataset("./Databases/rocket_info_2020.nc", decode_times=False)
        dsl = xr.open_dataset("./Databases/launch_info_2020.nc", decode_times=False)
        #
        #for reentry_count in range(len(ds_dw["DISCOSweb_Reentry_ID"].values)):
        #    
        #    # Excluding Debris
        #    valid_types = ["Rocket Body","Rocket Mission Related Object","Payload Mission Related Object","Payload"]
        #    
        #    if (ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count] not in jsr_ac_id_list) and ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in valid_types:
        #        
        #        # Sort type, stage, mass.
        #        if ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] == "Rocket Body":
        #            reentry_type = "R/B"
        #            
        #            if ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["Falcon 9 Merlin-V (1D+) (Falcon 9 v1.2)","H-II LE-5B (H-IIB)",
        #                                                                         "L-53 (YF24B) (Long March (CZ) 2D)","CZ-5-HO (Long March (CZ) 5)"]:
        #                reentry_stage = 2
        #            elif ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["Fregat-M (Soyuz-ST-A Fregat-M)","Fregat (Soyuz-2-1B Fregat)", "Fregat-M (Soyuz-2-1B Fregat-M)"]:
        #                reentry_stage = 3
        #            elif ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["AVUM (Vega)","Ceres-1 upperstage"]:
        #                reentry_stage = 4
        #            else:
        #                print("Missing stage designation for : ",ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count], ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count])
        #                reentry_stage = 0
        #        
        #            mass = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
        #            if np.isnan(mass):
        #                mass = 0
        #                
        #        elif ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object","Payload"]:
        #            if ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object"]:
        #                reentry_type = "Component"
        #            else: 
        #                reentry_type = "Payload"
        #            reentry_stage = 5
        #            mass = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
        #            if np.isnan(mass):
        #                mass = 0
        #        
        #        day = int(ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][8:10])
        #        mon = int(ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][5:7])
        #        time_utc = -1
        #        lat = 0
        #        lon = 0
        #        
        #        # For all 2020 launches, if the reentry occurs on the same day as the launch, we can set the time and location using the launch.
        #        # For all pre-2020, 0 is sufficient.
        #        if ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][0:4] == "2020":
        #            # Need to find the launch entry in the database and extract the time.
        #            launch_ind = np.where(dsl["COSPAR_ID"].values == ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][0:8])
        #            if len(launch_ind) > 1:
        #                sys.exit("Multiple database entries found for a single launch.")
        #            else:
        #                if (day == int(dsl["Day"].values[launch_ind[0]])) and (mon == int(dsl["Month"].values[launch_ind[0]])):
        #                    time_utc = dsl["Time(UTC)"].values[launch_ind][0]
        #                    lat = dsl["Latitude"].values[launch_ind][0]
        #                    lon = dsl["Longitude"].values[launch_ind][0]
        #                    manual_loc = True
        #        elif int(ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][0:4]) < 2020:
        #            time_utc = 0
        #
        #        temp_reentry_dict = {
        #            "id"           : ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count],
        #            "name"         : ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count],
        #            "type"         : reentry_type,
        #            "burnup"       : "Complete",
        #            "reentry_stage": reentry_stage, # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
        #            "time"         : time_utc,
        #            "mon"          : mon,
        #            "day"          : day,
        #            "lat"          : lat,
        #            "lon"          : lon,
        #            "mass"         : mass, 
        #            "manual_loc"   : manual_loc, 
        #        }
        #        
        #        self.unique_reentry_list.append(temp_reentry_dict)  
        #    
        #    else:
        #        # If the item already exists, check if the jsr entry is missing the mass information.
        #        # Only add if the jsr is missing the mass, and discosweb has the mass.
        #        # This is currently zero items, but leave this code in in case it is reused for future years.
        #        dict_ind = next((index for (index, d) in enumerate(self.unique_reentry_list) if d["id"] == ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count]), False)
        #        if dict_ind != False:
        #            if (self.unique_reentry_list[dict_ind]["type"] == "Payload/Debris") and (self.unique_reentry_list[dict_ind]["payload_mass"] == 0):
        #                if not np.isnan(ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]):
        #                    self.unique_reentry_list[dict_ind]["payload_mass"] = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
        #                    print("Added info for",ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count])                       
        #
        #################################################
        ## Assign as complete / partial reentry burn-up.
        #################################################
        #       
        ## Cygnus resupply missions are expendable. Cargo capsule on China resuable test operated "abnormally", and JSR lists as deorbited (read destroyed in atmosphere), so ignoring.    
        ## These are geolocated using the landing site, as this is likely to be within the same GEOS-Chem grid as the reentry.
        #for reentry in self.unique_reentry_list:
        #    if reentry["name"] in ["Soyuz MS-13","Soyuz MS-15","Soyuz MS-16","Crew Dragon DM-2","Dragon CRS-19", "Dragon CRS-20","XZF-SC"]:
        #        reentry["burnup"] = "Partial"
        #    if reentry["name"] == "Soyuz MS-13":
        #        reentry["lat"], reentry["lon"] = 47.78, 67.7    # https://www.nasaspaceflight.com/2020/02/record-setting-astronaut-return-earth/    
        #    if reentry["name"] == "Soyuz MS-15":   
        #        reentry["lat"], reentry["lon"] = 47.78, 67.7    # https://www.space.com/space-station-crew-lands-on-apollo-13-anniversary-exp62.html
        #    if reentry["name"] == "Soyuz MS-16":   
        #        reentry["lat"], reentry["lon"] = 47.78, 67.7    # https://www.nasa.gov/image-feature/support-personnel-arrive-at-the-soyuz-ms-16-spacecraft-landing-site
        #    if reentry["name"] == "Crew Dragon DM-2":
        #        reentry["lat"], reentry["lon"] = 30.42, -87.22  # https://www.nasaspaceflight.com/2020/08/demo2-splashdown-in-gulf/
        #    if reentry["name"] == "Dragon CRS-19":
        #        reentry["lat"], reentry["lon"] = 31.52, -120.40 # https://spaceflightnow.com/2020/01/07/dragon-cargo-capsule-brings-home-space-station-science-experiments/
        #    if reentry["name"] == "Dragon CRS-20":
        #        reentry["lat"], reentry["lon"] = 26.5, -117.5   # https://planet4589.org/space/jsr/back/news.777.txt
        #    if reentry["name"] == "XZF-SC":
        #        reentry["lat"], reentry["lon"] = 40.98, 100.21  # https://web.archive.org/web/20220102081307/http://www.xinhuanet.com/english/2020-05/08/c_139040336.htm 
        #    
        ############################################################
        ## Sort out MCS vs. Non MCS
        ############################################################
        #
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
                     
        #######################################
        ## Add reentries for failed launches.
        #######################################
        
        # TODO: JCAT has far less than I have added, go through these and check the discrepancies.
        # So for B+1/2S and B+3S, we need a reentry event for each lost booster at the launch site.
        # For B+4S, 2S and 3S, the 1st stage will cutoff and detach within 100 km altitude, so we need a reentry event for each of these.
        
        add_failed_launches = False
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
        
        ###########################################
        ## Add remaining missing rocket launches.
        ###########################################
        
        print("Looking for missing rocket stages.")
        # Based on rocket configurations, boosters will cutoff and detach above 50km for all configs except B+4S.  
        # So for B+1/2S and B+3S, we need a reentry event for each lost booster at the launch site.
        # For B+4S, 2S and 3S, the 1st stage will cutoff and detach within 100 km altitude, so we need a reentry event for each of these.
        
        # Loop over each launch in 2020, locate the rocket and then filter for rocket configuration.
        for i in range(len(dsl["COSPAR_ID"])):
            for count, rocket_name in enumerate(dsr["Rocket_Name"].values):
                if rocket_name == dsl["Rocket_Type"].values[i] and dsl["COSPAR_ID"].values[i][5] != "F":
                    
                    # Adding boosters for B+1/2S and B+3S.
                    if (dsr["Booster_PropMass"].values[count] != 0) and (dsr["Stage4_PropMass"].values[count] == 0):
                        # Count how many boosters are currently added, and compare it to the number of boosters there should be.
                        booster_count = 0
                        for reentry in self.unique_reentry_list:
                            if reentry["id"][:8] == dsl["COSPAR_ID"].values[i] and str(reentry["reentry_stage"])[0] == "B":
                                booster_count += 1
                        if booster_count != dsr["Booster_No"].values[count]:
                            print(f"Adding {dsr['Booster_No'].values[count]-booster_count} boosters for {dsl['COSPAR_ID'].values[i]}")
                            for j in range(dsr["Booster_No"].values[count]-booster_count):
                                mass = dsr["Booster_StageMass"].values[count] / dsr["Booster_No"].values[count]
                                if np.isnan(mass):
                                    mass = 0
                                    
                                temp_reentry_dict = {
                                    "id"           : f'{dsl["COSPAR_ID"].values[i]}',
                                    "name"         : f"{dsl['Rocket_Type'].values[i]} Booster",
                                    "type"         : "R/B",
                                    "burnup"       : "Complete",
                                    "reentry_stage": "B" + str(j+1), # -1 is nothing, B1-4 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
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
        
                   
                    # Adding 1st stages for B+4S, 2S and 3S rockets.
                    if ((dsr["Booster_PropMass"].values[count] == 0) and (dsr["Stage4_PropMass"].values[count] == 0)) or ((dsr["Booster_PropMass"].values[count] != 0) and (dsr["Stage4_PropMass"].values[count] != 0)):    
                        # Check if there is a first stage, and add if not.
                        found_stage = False
                        for reentry in self.unique_reentry_list:
                            if reentry["id"][:8] == dsl["COSPAR_ID"].values[i] and reentry["reentry_stage"] == 1:
                                found_stage = True
                        if found_stage == False:
                            print(f"Adding 1st stage for {dsl['COSPAR_ID'].values[i]}")
                            
                            temp_reentry_dict = {
                                "id"           : f'{dsl["COSPAR_ID"].values[i]}S1',
                                "name"         : f"{dsl['Rocket_Type'].values[i]} Stage 1",
                                "type"         : "R/B",
                                "burnup"       : "Complete",
                                "reentry_stage": 1, # -1 is nothing, B1-4 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
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
                    
        ###########################################
        ## Add missing mass info and extra admin.
        ###########################################
        
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
        
        # TODO: Need references for each of these, and need to update to fill in remaining mass info.
        
        # Set time to midnight whenever the reentry is occurs on a different day than the launch and no time info is available.
        if reentry["time"] == -1:  
            for count, launch_id in enumerate(dsl["COSPAR_ID"].values):
                if reentry["id"][:8] == launch_id:
                    if (int(reentry["mon"]) == int(dsl["Month"].values[count])) and (int(reentry["day"]) == int(dsl["Day"].values[count])):
                        pass
                    else:    
                        reentry["time"] = 0
        
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
        ds.to_netcdf(f'./Databases/reentry_info_{year}_jcat.nc')
        ds.close()
        
if __name__ == "__main__":
    """The main running of the program goes here. 
    All of the functions are inside the build_reentry_list class.
    Call each of the functions using build_reentry_list._function_
    e.g. build_reentry_list.launches_per_year(start_year,end_year)
    """         
    
    # Set up the arguments for each function.
    parser = argparse.ArgumentParser()
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
        Data.get_reentry_info()
        if args.save_reentry_info == True:
            Data.reentry_info_to_netcdf()