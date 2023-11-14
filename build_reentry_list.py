import numpy as np
import argparse
import xarray as xr
import pandas as pd
from datetime import datetime
import sys
import random
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pprint import pprint

class build_reentry_list:
    
    def __init__(self,year):
        """This function sets up the class.

        Args:
            year (_type_): The year.
        """        
        
        self.year = year
            
    def print_stats(self):
        non_geo_count, non_time_count, non_mass_count = 0, 0, 0
        total_mass, geolocated_mass = 0, 0
        starlink_count = 0
        for reentry in self.unique_reentry_list:
        
            if reentry["lat"] == 0 and reentry["lon"] == 0:
                non_geo_count += 1
                if "starlink" in reentry["name"].lower():
                    starlink_count += 1
                      
            else:
                geolocated_mass += reentry["mass"]
            if reentry["time"] == -1:
                non_time_count += 1
            if reentry["mass"] == 0:
                non_mass_count += 1
                   
            total_mass += reentry["mass"]
        
        print(f"Total Reentries: {len(self.unique_reentry_list):.0f}.")
                
        
        geo_percent_all = (len(self.unique_reentry_list)-non_geo_count) / (len(self.unique_reentry_list)) * 100
        time_percent_all = (len(self.unique_reentry_list)-non_time_count) / (len(self.unique_reentry_list)) * 100
        mass_percent_all = (len(self.unique_reentry_list)-non_mass_count) / (len(self.unique_reentry_list)) * 100
        print(f"Total mass (Gg):   {total_mass*1e-6:.3f}")
        geolocated_mass_percent = geolocated_mass / total_mass * 100
        print(f"Geolocation (All): {geo_percent_all:.0f}%.")
        print(f"Timed (All):       {time_percent_all:.0f}%.")    
        print(f"Mass (All):        {mass_percent_all:.0f}%.")
        print(f"Geolocated Mass:   {geolocated_mass_percent:.0f}%.")
        
    def convert_lat_lon(self,latlonstr,inc,stage,apogee,dsl,jsr_id):
        
        # Adjust the inclination so its useful for our purpose of bounding the lat.
        # TODO: Check with Jonathan. Does inc = 0 mean its incomplete or the inc is actually 0.
        manual_loc = 0
        if inc > 90:
            inc = 180-inc
        elif inc == 0:
            inc=90
        
        if latlonstr == "-":
            # If location is missing for lower stages for failed and successful launches, set as launch coordinates.
            if apogee <= 100 and stage in [0,1]: 
                for i in range(len(dsl["COSPAR_ID"])):
                    if jsr_id[:8] == dsl["COSPAR_ID"].values[i][:8]:
                        lat = dsl["Latitude"].values[i]
                        lon = dsl["Longitude"].values[i]
            else: 
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                manual_loc = 1  
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
            # https://discosweb.esoc.esa.int/launch-sites/21
            # https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=2020-027A
            # https://space.skyrocket.de/doc_sdat/xzf-sc.htm 
            # https://spaceflightnow.com/2020/05/08/chinas-next-generation-crew-spacecraft-lands-after-unpiloted-test-flight/ 
            lat = 41.3
            lon = 100.3               
        elif latlonstr == "LOPNOR RW05":
            # Reported test flight of a Chinese reusable experimental spacecraft.
            # Runway 05/22 at Lop Nor air base in Xinjiang (https://planet4589.org/space/gcat/data/tables/lp.html).
            # https://www.seradata.com/china-launches-own-mini-spaceplane-reusable-spacecraft-using-long-march-2f 
            # https://twitter.com/planet4589/status/1302486141090885632                
            lat = 40.78
            lon = 89.27
        elif latlonstr == "Ocean":
            # Electron Stage 1 (rcat) is occasionally recovered in the ocean.
            # From https://spaceflightnow.com/2020/11/05/rocket-lab-to-attempt-booster-recovery-on-next-mission/:
            #   Recovery vessels stationed near the booster’s splashdown zone around 250 miles (400 kilometers) 
            #   south of the launch site will move in to secure the first stage and hoist it onto a ship for return to New Zealand.
            # Geoloating 400km south of launch site.
            lat = -42.86 
            lon = 177.87
        elif latlonstr == "Antarctic?":
            # TODO: Check with Jonathan. Assuming this to mean south of 60S.
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if lat <= -60:
                    break 
        #elif latlonstr in ["Arctic","Pacific", "Pacific?", "PO","AO","E Pacific", "E Pacific?","S Pacific", "S POR","Indian O?","SE IOR?"]:
        #    lat = 0
        #    lon = 0
        elif latlonstr == "Arctic":
            # TODO: Check with Jonathan, Arctic means Arctic Ocean, not just above 66N?
            arctic = self.ocean_shapefile[self.ocean_shapefile.name.isin(['Arctic Ocean'])] 
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if arctic.geometry.contains(coordinate).any():
                    break 
        elif latlonstr in ["Pacific", "Pacific?", "PO"]:
            while True:
                random_location = self.pacific_union.sample_points(1).get_coordinates()
                lon = random_location["x"].values[0]
                lat = random_location["y"].values[0]
                if -inc <= lat <= inc:
                    break
        elif latlonstr in ["AO"]:
            # TODO: Check with Jonathan, does this mean Arctic or Atlantic?
            atlantic = self.ocean_shapefile[self.ocean_shapefile.name.isin(['North Atlantic Ocean','South Atlantic Ocean'])]
            self.atlantic_union = gpd.GeoDataFrame(geometry=[atlantic.unary_union]) 
            while True:
                random_location = self.atlantic_union.sample_points(1).get_coordinates()
                lon = random_location["x"].values[0]
                lat = random_location["y"].values[0]
                if -inc <= lat <= inc:
                    break
        elif latlonstr in ["E Pacific", "E Pacific?"]:
            while True:
                random_location = self.pacific_union.sample_points(1).get_coordinates()
                lon = random_location["x"].values[0]
                lat = random_location["y"].values[0]
                if -inc <= lat <= inc and -180 <= lon <= -60: # Bounded to East Pacific only.
                    break 
        elif latlonstr in ["S Pacific", "S POR"]:
            while True:
                random_location = self.pacific_union.sample_points(1).get_coordinates()
                lon = random_location["x"].values[0]
                lat = random_location["y"].values[0]
                if -inc <= lat <= inc and lat <= 0: # Bounded to South Pacific only.
                    break 
        elif latlonstr in ["S Ocean", "S Ocean?"]:
            # For these three objects in auxcat, the inclination is 51.65-53.
            # This is outside of the general definition of the southern ocean (<60S).
            # Therefore we will just set the lat to the inclination.
            lat = -inc
            lon = round(random.uniform(-180, 180),2)
        elif latlonstr in ["Indian O?"]:
            indian_ocean = self.ocean_shapefile[self.ocean_shapefile.name.isin(['Indian Ocean'])] 
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if indian_ocean.geometry.contains(coordinate).any():
                    break 
        elif latlonstr in ["S of Tasmania?"]:
            lon_lat_list = [[153.23, -30.02],[146.83, -43.64],[166.00, -50.92], [167.53, -47.29], [168.14, -46.85], [168.85, -46.66], [174.28, -41.72], [175.28, -41.62], [173.01, -34.39]]
            tasman_sea_geom = Polygon(lon_lat_list)
            tasman_sea = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[tasman_sea_geom])
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if tasman_sea.geometry.contains(coordinate).any():
                    break 
        elif latlonstr in ["SE IOR?"]:
            indian_ocean = self.ocean_shapefile[self.ocean_shapefile.name.isin(['Indian Ocean'])] 
            while True:
                lat = round(random.uniform(-inc, -30),2)
                lon = round(random.uniform(77, 180),2)
                coordinate = Point(lon,lat)
                if indian_ocean.geometry.contains(coordinate).any():
                    break 
        elif latlonstr.replace("?","").split()[0][-1] in ["E","W","S","N"]:
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
    
    def convert_time(self,date):
    
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
            time_utc = -1  
        
        return monstr, daystr, time_utc 
    
    def failed_launch_mass(self, jsr_id, jsr_name, reentry_stage):
            
        # When adding the wet mass, the dry mass + propellant mass has been used.
        mass = 0
            
        if jsr_id == "2020-F01":
            stage_masses = [12700,1600,230] 
            if reentry_stage in [1,2,3]:
                mass = stage_masses[reentry_stage-1]
            elif reentry_stage == 5:
                mass = 113
          
        elif jsr_id == "2020-F02":
            stage_masses = [24000,12500,5500+65000,2800+18200]
            if reentry_stage == 0:
                mass = stage_masses[0] / 4  
            if reentry_stage in [1,2,3]:
                mass = stage_masses[reentry_stage]
            elif reentry_stage == 5:
                mass = 6550     
        
        elif jsr_id == "2020-F03":
            stage_masses = [13200,9200,5000,2800+18193]
            if reentry_stage == 0:
                mass = stage_masses[0] / 4  
            if reentry_stage in [1,2,3]:
                mass = stage_masses[reentry_stage]
            elif reentry_stage == 5:
                mass = 5550
        
        elif jsr_id == "2020-F05":
            stage_masses = [950,250+2050,40+245]
            payload_masses = [67,5.8,10]
            if reentry_stage in [1,2,3]:
                mass = stage_masses[reentry_stage-1]
            elif reentry_stage == 5:
                if "CE-SAT-I" in jsr_name:
                    mass = payload_masses[0]
                elif "Flock 4e" in jsr_name:
                    mass = payload_masses[1]
                elif "Faraday-1" in jsr_name:
                    mass = payload_masses[2]

        elif jsr_id == "2020-F06":
            stage_masses = [7530,1490,1000+480]
            payload_masses = [201,97]
            if reentry_stage in [1,2,3]:
                mass = stage_masses[reentry_stage-1]
            elif reentry_stage == 5:
                if "Jilin-1 Gaofen 02E" in jsr_name:
                    mass = payload_masses[0]
                elif "Xiangrikui 2" in jsr_name:
                    mass = payload_masses[1]
                    
        elif jsr_id == "2020-F08":
            stage_masses = [621,686,183,200+1000]
            if reentry_stage in [1,2,3,4]:
                mass = stage_masses[reentry_stage-1]
            elif reentry_stage == 5:
                mass = 230
                
        elif jsr_id == "2020-U01":
            stage_masses = [2486,1433,688+550]
            payload_masses = [750,175]
            if reentry_stage in [2,3,4]:
                mass = stage_masses[reentry_stage-2]
            elif reentry_stage == 5:
                if "SEOSat-Ingenio" in jsr_name:
                    mass = payload_masses[0]
                elif "Taranis" in jsr_name:
                    mass = payload_masses[1]
        
        elif jsr_id == "2020-F09":
            stage_masses = [950,250]
            if reentry_stage in [1,2]:
                mass = stage_masses[reentry_stage-1]
            elif reentry_stage == 5:
                mass = 5

        return mass
         
    def extract_jsr_info(self, filepath,dsl):
        
        jsr_data = pd.read_csv(filepath, delimiter='\t', dtype=object)
        # Only include R (Reentry), D (Deorbit), or L (Landed) events.
        jsr_data_stripped = jsr_data[jsr_data["Status"].isin(["R","D","L","L?","AR","S","F","AS","AF"])].reset_index(drop=True)
        # TODO: Check with Jonathan, currently not adding objects reentering inside other objects (AL IN / AR IN in ecat).
        
        # If the reentry occured in 2020 and apogee was above 50 km, then extract that row and build a new dataframe.
        # For apogee, this really only affects the lcat, which includes suborbital objects with apogees below 80 km.
        jsr_data_stripped_2020_list = []
        for reentry_count in range(len(jsr_data_stripped)):
            
            # For some reason, there are 4 CZ-8 boosters listed in JSR rcat for 2020-102.
            # Should only be two, and mass looks correct for each booster. Removing two.
            if jsr_data_stripped["DDate"][reentry_count][0:4] != "-" and jsr_data_stripped["#JCAT"][reentry_count] not in ["R80054","R80055"]:
            
                if (
                    int(jsr_data_stripped["DDate"][reentry_count][0:4]) == self.year
                    and (int(jsr_data_stripped["Apogee"][reentry_count]) >= 50 or int(jsr_data_stripped["Apogee"][reentry_count]) == -54771)            
                    and jsr_data_stripped["Piece"][reentry_count][5:6] != "S"
                    and jsr_data_stripped["Primary"][reentry_count] not in ["Bennu", "Venus", "Luna"]
                    and "fairing" not in jsr_data_stripped["Name"][reentry_count].lower()
                ):
                    
                    jsr_data_stripped_2020_list.append(jsr_data_stripped.iloc[[reentry_count]])
        jsr_data_stripped_2020 = pd.concat(jsr_data_stripped_2020_list, ignore_index=True)
        
        # Now loop over the list and format into a dictionary.
        for reentry_count in range(len(jsr_data_stripped_2020)):
            
            jsr_id = jsr_data_stripped_2020["Piece"][reentry_count] 
            jsr_name = jsr_data_stripped_2020["Name"][reentry_count]
            # The failure numbers are labelled differently for 2020 in DW and JSR.
            # To make sure the main script runs OK, adjust the COSPAR ID here.
            if jsr_id == "2020-F09":
                jsr_id = "2020-F10"
            elif jsr_id == "2020-U01":
                jsr_id = "2020-F09"
            
            if jsr_name in ["Soyuz MS-13","Soyuz MS-15","Soyuz MS-16","Endeavour","Dragon CRS-19", "Dragon CRS-20","XZF-SC"]:
                burnup = "Partial"
            else:
                burnup = "Complete"
                
            # Duplicates:
            #   2019-036H. This is TEPCE 1 and TEPCE 2, listed with same "Piece" in JSR. TEPCE 2 listed as 2019-036IA in DISCOSweb, so renaming to this.
            #   2020-027A. This is Xinyidai Zairen Feichuan (XZF) and XZF Service Module (not in DISCOSweb). Setting auxcat id to XZF 2020-027D.
            #   Remaining are where multiple objects in auxcat from same launch are just given the COSPAR ID of the launch.
            if jsr_data_stripped_2020["Name"][reentry_count] == "TEPCE 2":
                jsr_id = "2019-036IA" 
            elif jsr_data_stripped_2020["Name"][reentry_count] == "XZF Service Module":
                jsr_id = "2020-027D"  
            elif jsr_data_stripped_2020["Piece"][reentry_count] == "2020-078B": # This is just a mistake in JSR.
                jsr_name = "Falcon 9-098 Stage 2"
                
            # Sort out the reentry time/date.
            monstr, daystr, time_utc = self.convert_time(jsr_data_stripped_2020["DDate"][reentry_count].split()) 
            
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
            else:
                reentry_stage = -1
                
            # Sort out the reentry lat/lon.
            if "Falcon 9 Stage 1" in jsr_name:
                # TODO: We can probably make this even more accurate by looking for groundtrack info directly from Raul's Space Map.
                manual_loc = 0
                burnup = "Partial"
                if jsr_id == "2020-086":
                    lat = 34.7
                    lon = -120.6
                else:
                    lat = 34
                    lon = -75
            #elif "Falcon 9 Fairing" in jsr_name:
            #    # Geolocate the fairings here.
            #    lat = 0
            #    lon = 0
            else:   
                lat, lon, manual_loc = self.convert_lat_lon(jsr_data_stripped_2020["Dest"][reentry_count],
                                                            np.float64(jsr_data_stripped_2020["Inc"][reentry_count]),
                                                            reentry_stage,
                                                            int(jsr_data_stripped["Apogee"][reentry_count]),
                                                            dsl,
                                                            jsr_id)
                  
            if jsr_id[5:6] in ["F","U"]:
                mass = self.failed_launch_mass(jsr_id, jsr_name, reentry_stage)
            else:
                mass = np.float64(jsr_data_stripped_2020["DryMass"][reentry_count])
            
            if lat == 0 and lon == 0:
                print(jsr_id,jsr_data_stripped_2020["Dest"][reentry_count]) 
            
            # Ignore Z, this is a spurious entry according to JSR, and ignore D, this is debris objects. 
            # Set up the dictionary.                      
            if jsr_data_stripped_2020["Type"][reentry_count][:1] not in ["Z", "D"]:
                temp_reentry_dict = {
                    "id"           : jsr_id,
                    "jcat"         : jsr_data_stripped_2020["#JCAT"][reentry_count],
                    "name"         : jsr_name,
                    "type"         : reentry_type,
                    "burnup"       : burnup,
                    "reentry_stage": reentry_stage,  # -1 is nothing, B1-4 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                    "time"         : time_utc,
                    "mon"          : monstr,
                    "day"          : daystr,
                    "lat"          : lat,
                    "lon"          : lon,
                    "mass"         : mass,
                    "manual_loc"   : manual_loc,
                }
                
                self.unique_reentry_list.append(temp_reentry_dict)   
    
    def extract_aerospace_info(self, filepath):
        # Now load the Aerospace Corp information, to see if we can fill in any missing time information.  
        print("Searching for Aerospace Corp re-entries.")
        aerospace_corp_data = pd.read_csv(filepath)
        
        aerospace_corp_data_year_list = []
        for reentry_count in range(len(aerospace_corp_data)):
            if aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][0:4] != "-":
                if int(aerospace_corp_data["Aerospace Reentry Prediction (UTC)"][reentry_count][0:4]) == self.year:
                    aerospace_corp_data_year_list.append(aerospace_corp_data.iloc[[reentry_count]])
        aerospace_corp_data_year = pd.concat(aerospace_corp_data_year_list, ignore_index=True)
        
        # Check what items are already in the list.
        jsr_id_list = []
        for reentry in (self.unique_reentry_list):
            jsr_id_list.append(reentry["id"])
        
        # Add time information from Aerospace Corp for any JSR entries missing time information.
        for reentry in (self.unique_reentry_list):
            if reentry["time"] == -1:
                for reentry_count in range(len(aerospace_corp_data_year)): 
                    if aerospace_corp_data_year["International Designator"][reentry_count] == reentry["id"]:
                        reentry_time = aerospace_corp_data_year["Aerospace Reentry Prediction (UTC)"][reentry_count][11:16]
                        reentry["time"] = np.float64(int(reentry_time[0:2]) + int(reentry_time[3:5]) / 60)
        
        # Now add any new entries.
        # TODO: Future years. 
        # If running for 2021/22, need to go through each new entry to double check info.
        for reentry_count in range(len(aerospace_corp_data_year)):  
            if aerospace_corp_data_year["International Designator"][reentry_count] not in jsr_id_list:
                # 1992-021C, Ariane 44L H10+ 3rd Rocket Stage. DISCOSweb and AC list this as reentering in Oct 2020. JSR lists this as exploding in Apr 1993.
                # 2019-029Q, Starlink payload. DISCOSweb and JSR list this as reentering in July 2022. AC lists this as reentering in 2020. Ignoring.
                # 2020-012B, Starlink payload. DISCOSweb has no re-entry data. AC lists this as reentering Mar 2020. JSR lists this as still in orbit. Ignoring.
                print(aerospace_corp_data_year["International Designator"][reentry_count])
                if aerospace_corp_data_year["International Designator"][reentry_count] == "1992-021C":
                    # Extract the UTC time.     
                    reentry_time = aerospace_corp_data_year["Aerospace Reentry Prediction (UTC)"][reentry_count][11:16]
                    time_utc = np.float64(int(reentry_time[0:2]) + int(reentry_time[3:5]) / 60)
                    temp_reentry_dict = {
                        "id"           : aerospace_corp_data_year["International Designator"][reentry_count],
                        "jcat"         : "N/A",
                        "name"         : aerospace_corp_data_year["Object Name"][reentry_count],
                        "type"         : aerospace_corp_data_year["Type"][reentry_count],
                        "burnup"       : "Complete",
                        "reentry_stage": 3,  # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris.
                        "time"         : time_utc,
                        "mon"          : aerospace_corp_data_year["Aerospace Reentry Prediction (UTC)"][reentry_count][5:7],
                        "day"          : aerospace_corp_data_year["Aerospace Reentry Prediction (UTC)"][reentry_count][8:10],
                        "lat"          : round(random.uniform(-90,90),2),
                        "lon"          : round(random.uniform(-180, 180),2),
                        "mass"         : 2080, # From JSR.
                        "manual_loc"   : 0,
                    }  
                    
                    self.unique_reentry_list.append(temp_reentry_dict)
    
    def extract_discosweb_info(self, ds_dw, dsl):
        
        # Check what items are already in the list.
        jsr_ac_id_list = []
        for reentry in (self.unique_reentry_list):
            jsr_ac_id_list.append(reentry["id"]) 
        
        # All DISCOSweb data is contained within a netcdf file.
        print("Searching for DISCOSweb re-entries.")
        
        for reentry_count in range(len(ds_dw["DISCOSweb_Reentry_ID"].values)):
            
            # Excluding Debris
            valid_types = ["Rocket Body","Rocket Mission Related Object","Payload Mission Related Object","Payload"]
            if (ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count] not in jsr_ac_id_list) and ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in valid_types:
                
                # TODO: Future years.
                # Will have to define the rocket stage for new years. Also if the new entry is a payload then check its not already in dictionary.
                
                # Check if the stage has already been added.  
                found_stage = False               
                if ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] == "Rocket Body":
                    reentry_type = "R/B"
                    
                    if ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["Falcon 9 Merlin-V (1D+) (Falcon 9 v1.2)","H-II LE-5B (H-IIB)",
                                                                                                    "L-53 (YF24B) (Long March (CZ) 2D)","CZ-5-HO (Long March (CZ) 5)"]:
                        reentry_stage = 2
                    elif "Fregat" in ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count]:
                        reentry_stage = 3 
                    elif ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["AVUM (Vega)","Ceres-1 upperstage"]:
                        reentry_stage = 4
                    else:
                        print("Missing stage designation for : ",ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count], ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count])
                        reentry_stage = 0
                    
                    for reentry in self.unique_reentry_list:
                        if reentry["id"][:8] == ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][:8] and str(reentry["reentry_stage"]) == str(reentry_stage):
                            found_stage = True
                if found_stage == False:
                    print(f"Adding object with COSPAR ID {ds_dw['DISCOSweb_Reentry_ID'].values[reentry_count]}")          
                
                    if ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object","Payload"]:
                        if ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object"]:
                            reentry_type = "Component"
                        else: 
                            reentry_type = "Payload"
                        reentry_stage = 5

                    day = int(ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][8:10])
                    mon = int(ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][5:7])
                    time_utc = -1
                    lat = 0
                    lon = 0
                    mass = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
                    if np.isnan(mass):
                        mass = 0
    
                    temp_reentry_dict = {
                        "id"           : ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count],
                        "jcat"         : "N/A",
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
                        "manual_loc"   : -1, 
                    }

                    self.unique_reentry_list.append(temp_reentry_dict)  
            
            else:
                # If the item already exists, check if the jsr entry is missing the mass information.
                # Only add if the jsr is missing the mass, and discosweb has the mass.
                # This is currently zero items, but leave this code in in case it is reused for future years.
                dict_ind = next((index for (index, d) in enumerate(self.unique_reentry_list) if d["id"] == ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count]), False)
                if dict_ind != False:
                    if (self.unique_reentry_list[dict_ind]["type"] in ["Component", "Payload"]) and (self.unique_reentry_list[dict_ind]["mass"] == 0):
                        if not np.isnan(ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]):
                            self.unique_reentry_list[dict_ind]["payload_mass"] = ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
                            print("Added info for",ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count])                       
         
    def add_missing_stages(self, dsr, dsl):
        
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
                    
        print("Looking for missing rocket stages.")
        # Based on rocket configurations, boosters will cutoff and detach above 50km for all configs except B+4S.  
        # So for B+1/2S and B+3S, we need a reentry event for each lost booster at the launch site.
        # For B+4S, 2S and 3S, the 1st stage will cutoff and detach within 100 km altitude, so we need a reentry event for each of these.
        
        # TODO: Future years.
        # If we extend to 2021/2022, obviously need to get new information on rocket altitudes and may have to update this.
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
                                    "jcat"         : "N/A",
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
                                    "manual_loc"   : 0,
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
                                "jcat"         : "N/A",
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
                                "manual_loc"   : 0,
                            }
        
                            self.unique_reentry_list.append(temp_reentry_dict)
                             
    def get_reentry_info(self):
                
        self.ocean_shapefile = gpd.read_file("./Databases/GOaS_v1_20211214/goas_v01.shp")
        pacific = self.ocean_shapefile[self.ocean_shapefile.name.isin(['North Pacific Ocean','South Pacific Ocean'])]
        self.pacific_union = gpd.GeoDataFrame(geometry=[pacific.unary_union]) 
        
        ds_dw = xr.open_dataset(f"./Databases/Reentry/discosweb_reentries_{self.year}.nc", decode_times=False)
        dsr = xr.open_dataset(f"./Databases/rocket_info_{self.year}.nc", decode_times=False)
        dsl = xr.open_dataset(f"./Databases/launch_info_{self.year}.nc", decode_times=False)    
             
        self.unique_reentry_list = []
        
        print("Adding JSR re-entries.")
        
        print("satcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/satcat_2ndNov.tsv" ,dsl) # Load in the JSR satcat database.
        print("auxcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/auxcat_2ndNov.tsv" ,dsl) # Load in the JSR auxcat database.
        print("lcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/lcat_2ndNov.tsv"   ,dsl) # Load in the JSR lcat database.
        print("rcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/rcat_2ndNov.tsv"   ,dsl) # Load in the JSR rcat database.
        print("lprcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/lprcat_2ndNov.tsv" ,dsl) # Load in the JSR lprcat database.
        print("deepcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/deepcat_7thNov.tsv",dsl) # Load in the JSR deepcat database.
        print("ecat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/ecat_8thNov.tsv"   ,dsl) # Load in the JSR ecat database.
        print("ftocat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/ftocat_2ndNov.tsv" ,dsl) # Load in the JSR ftocat database.
        
        # lcat is mainly suborbital rocket stages and 11 objects from suborbital launches (separate object for each booster).
        # rcat contains lots of fairings and more lower rocket stages.
        # lprcat contains a few objects returning to Earth from space.
        # deepcat only contains a few objects.   
        # ecat mainly contains capsules from ISS / crewed missions.
        # Nothing of use in hcocat.
        # Nothing of use in tmpcat.
        # Nothing of use in csocat.     
        
        # This code checks for duplicate reentries with the same jcat id.       
        self.jsr_jcat_list = []
        for reentry in self.unique_reentry_list:
            self.jsr_jcat_list.append(reentry["jcat"])
        duplicate_jcat_list = []
        for jsr_jcat in self.jsr_jcat_list:
            if self.jsr_jcat_list.count(jsr_jcat) > 1:
                duplicate_jcat_list.append(jsr_jcat)
        duplicate_jcat_list = sorted(list(set(duplicate_jcat_list)))
        print(f"Duplicates: {duplicate_jcat_list}")
        
        self.add_missing_stages(dsr, dsl) # Add any missing stages.
        self.extract_aerospace_info("./Databases/Reentry/AerospaceCorp/AerospaceCorp_Reentries.csv") # Load in the Aerospace Corp database.            
        self.extract_discosweb_info(ds_dw, dsl) # Load in the DISCOSweb database.
        
        ###########################################
        ## Add missing mass info and extra admin.
        ###########################################
        
        # Create a list of all MCS-related launches (from launch database). 
        mcs_dict = {}
        for i in range(len(dsl["COSPAR_ID"])):
            mcs_dict[dsl["COSPAR_ID"].values[i]] = dsl["MCS_Check"].values[i]
            
        for count, reentry in enumerate(self.unique_reentry_list):
            # Update mass info for all rockets in 2020.
            for i in range(len(dsl["COSPAR_ID"])):
                if dsl["COSPAR_ID"].values[i][:8] == reentry["id"][:8] and reentry["reentry_stage"] in ["B1","B2","B3","B4","B5","B6",1,2,3,4] and dsl["COSPAR_ID"].values[i][5] != "F":
                    for count, rocket_name in enumerate(dsr["Rocket_Name"].values):
                        if rocket_name == dsl["Rocket_Type"].values[i]:
                            if reentry["reentry_stage"] in ["B1","B2","B3","B4"]:
                                reentry["mass"] = dsr["Booster_StageMass"].values[count] / dsr["Booster_No"].values[count]
                            elif reentry["reentry_stage"] == 1:
                                reentry["mass"] = dsr["Stage1_StageMass"].values[count]
                            elif reentry["reentry_stage"] == 2:
                                reentry["mass"] = dsr["Stage2_StageMass"].values[count]
                            elif reentry["reentry_stage"] == 3:
                                reentry["mass"] = dsr["Stage3_StageMass"].values[count]
                            elif reentry["reentry_stage"] == 4:
                                reentry["mass"] = dsr["Stage4_StageMass"].values[count]
            
            # TODO: Future years.
            # Need to check for items with missing mass each year.
            # TODO: Need references for each of these, and need to update to fill in remaining mass info.
            # For West Ford dipoles, these are part of the West Ford Needles project. # https://space.skyrocket.de/doc_sdat/westford.htm
            # The needles each weigh 40 ng, and one 'clump' reentered in 2020. The needles are Copper, and so will not contribute to Al emissions.  
            if reentry["name"] == "CZ-2C sep motor cover":
                # The same item is also listed as weighing 1 kg.
                reentry["mass"] = 1
            if reentry["id"] == "2020-086B": # Dest listed as 180E, this messes up other script so adjust to 179.9, will be in same grid square.
                reentry["lon"] = 179.9

            # Set time to midnight whenever the reentry is occurs on a different day than the launch and no time info is available.
            # Also set to midnight if the reentry is from a launch in a previous year.
            # When the reentry is on the same day, set it to the launch time.
            if reentry["time"] == -1:  
                for count, launch_id in enumerate(dsl["COSPAR_ID"].values):
                    if reentry["id"][:8] == launch_id:
                        if (int(reentry["mon"]) == int(dsl["Month"].values[count])) and (int(reentry["day"]) == int(dsl["Day"].values[count])):
                            reentry["time"] = dsl["Time(UTC)"].values[count]
                        else:    
                            reentry["time"] = 0
                if int(reentry["id"][:4]) < self.year:
                    reentry["time"] = 0    
            if reentry["time"] == -1:
                print(f"Need to add timings for {reentry['id']} {reentry['jcat']}")
                        
            # Assign all items from MCS launches as MCS.
            try:
                reentry["MCS"] = mcs_dict[reentry["id"][:8]]
            except:
                if reentry["id"][:8] in ["2018-020","2019-029","2019-074"]:
                    reentry["MCS"] = True
                else:
                    reentry["MCS"] = False
        
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
        datestr = datetime.today().strftime('%Y%m%d_%H%M%S') 
        ds.to_netcdf(f'./Databases/reentry_info_{self.year}_jcat_{datestr}.nc')
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