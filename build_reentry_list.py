import numpy as np
import argparse
import xarray as xr
import pandas as pd
from datetime import datetime
import sys
import random
import geopandas as gpd
from shapely.geometry import Point, Polygon
import fiona

class build_reentry_list:
    
    def __init__(self,year):
        """This function sets up the class.

        Args:
            year (int): The year.
        """        
        
        self.year = year
            
    def print_stats(self):
        """Print out statistics about the database at the end of the program.
        """        
        
        # Set all variable counters to 0, then count how many items are missing location, time, and mass information.
        non_geo_count, non_time_count, non_mass_count, total_mass, geolocated_mass, starlink_count = 0, 0, 0, 0, 0, 0
        for reentry in self.unique_reentry_list:
            
            if reentry["lat"] == 0 and reentry["lon"] == 0:
                non_geo_count += 1
                if "starlink" in reentry["name"].lower():
                    starlink_count += 1      
            else:
                geolocated_mass += (reentry["al_mass"] + reentry["non_al_mass"])
            if reentry["time"] == -1:
                non_time_count += 1
            if (reentry["al_mass"] + reentry["non_al_mass"]) == 0:
                non_mass_count += 1
                   
            total_mass += (reentry["al_mass"] + reentry["non_al_mass"])
        
        print(f"Total Reentries: {len(self.unique_reentry_list):.0f}.")
                
        geo_percent_all = (len(self.unique_reentry_list)-non_geo_count) / (len(self.unique_reentry_list)) * 100
        time_percent_all = (len(self.unique_reentry_list)-non_time_count) / (len(self.unique_reentry_list)) * 100
        mass_percent_all = (len(self.unique_reentry_list)-non_mass_count) / (len(self.unique_reentry_list)) * 100
        print(f"Total mass (Gg):   {total_mass*1e-6:.3f}")
        geolocated_mass_percent = geolocated_mass / total_mass * 100
        print(f"Geolocation (All): {geo_percent_all:.0f}%, {non_geo_count}.")
        print(f"Timed (All):       {time_percent_all:.0f}%, {non_time_count}.")    
        print(f"Mass (All):        {mass_percent_all:.0f}%, {non_mass_count}.")
        print(f"Geolocated Mass:   {geolocated_mass_percent:.0f}%.")
        
    def convert_lat_lon(self,latlonstr,inc,stage,apogee,jsr_id):
        """Set the geolocation for all items that are not Falcon 9 fairings/1st stage.

        Args:
            latlonstr (str)     : The 
            inc (np.float64)    : The orbital inclination of the object.
            stage (int)         : The stage number of the object (# -1 is nothing, B1-4 = Booster, 1-4 = Stage Number, 5 = Payload/Debris).
            apogee (int)        : The apogee of the object.
            dsl (xarray Dataset): A database of all rocket launches in the specified year.
            jsr_id (str)        : The COSPAR ID of the object.

        Returns:
            lat(np.float64) : The latitude of the object.
            lon(np.float64) : The longitude of the object.
            manual_loc(int) : A toggle for whether the location was randomised (1) or not (0).
        """        
        
        # Adjust the inclination so its useful for our purpose of bounding the lat.
        manual_loc = 0
        if inc > 90:
            inc = 180-inc
        elif inc == 0:
            print(f"0 Inc for {jsr_id}")
            inc=90
        
        if latlonstr == "-":
            # If location is missing for lower stages for failed and successful launches, set as launch coordinates.
            if (apogee <= 100) and (stage in [0,1]): 
                for i in range(len(self.dsl["COSPAR_ID"])):
                    if jsr_id[:8] == self.dsl["COSPAR_ID"].values[i][:8]:
                        lat = self.dsl["Latitude"].values[i]
                        lon = self.dsl["Longitude"].values[i]
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
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if lat <= -60:
                    break 
        elif latlonstr == "Arctic": 
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if lat >= 66:
                    break
        elif latlonstr in ["S Ocean", "S Ocean?"]:
            # For these three objects in auxcat, the inclination is 51.65-53.
            # This is outside of the general definition of the southern ocean (<60S).
            # Therefore we will just set the lat to the inclination.
            lat = -inc
            lon = round(random.uniform(-180, 180),2)
        elif latlonstr in ["Pacific","Pacific?","PO","AO","E Pacific","E Pacific?","S Pacific","S POR","Indian O?","SE IOR?","SE IOR","Atlantic","POR"]:
            lat = 0
            lon = 0
        elif latlonstr == "WSSH":
            # This is the White Sands Missile Range in New Mexico.
            lat = 33.238462 
            lon = -106.346383 
        elif latlonstr == "GM 86.2W 29.7N":
            # Gulf of Mexico
            lat = 29.7
            lon = -86.2
        elif latlonstr == "Splash?":
            # This is the Electron failed helicopter stage 1 recovery in May 22. 
            # https://www.youtube.com/watch?v=BY0CXlOeWHI "Several hundred kilometers from the launch site."
            # Using inclination of 94 degrees (wiki), and distance of 300km.
            lat = -36.57
            lon = 177.63
        elif latlonstr == "Gujarat":
            gujurat     = self.states_shapefile[self.states_shapefile.name_en.isin(['Gujarat'])] 
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if gujurat.geometry.contains(coordinate).any():
                    break
        elif latlonstr == "KSC SLF": # https://www.world-airport-codes.com/united-states/nasa-shuttle-landing-facility-69738.html
            # https://www.spaceforce.mil/News/Article/3217077/x-37b-orbital-test-vehicle-concludes-sixth-successful-mission/
            lat = 28.61
            lon = -80.69
        elif latlonstr == "Kazakhstan":
            kazakhstan     = self.country_shapefile[self.country_shapefile.NAME.isin(['Kazakhstan'])]
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if kazakhstan.geometry.contains(coordinate).any():
                    break
        elif latlonstr == "Mexico":
            mexico     = self.country_shapefile[self.country_shapefile.NAME.isin(['Mexico'])]
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if mexico.geometry.contains(coordinate).any():
                    break
        elif latlonstr == "S Africa":
            s_africa     = self.country_shapefile[self.country_shapefile.NAME.isin(['South Africa'])]
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if s_africa.geometry.contains(coordinate).any():
                    break
        elif latlonstr == "100 03E 41 39N":
            lon = 100.05
            lat = 41.65
        elif latlonstr == "47 20N 69 34E":     
            lon = 69.57
            lat = 47.33
        elif latlonstr == "41 39N 100 09E":     
            lon = 100.15
            lat = 41.65            
        elif latlonstr == "47 20N 69 35E?":     
            lon = 69.58
            lat = 47.33      
        elif latlonstr == "100 04E 41 37N":
            lon = 100.07
            lat = 41.62
        elif latlonstr == "69 37E 47 21N":
            lon = 69.62
            lat = 47.35
        elif latlonstr in ["Pacific", "Pacific?", "PO", "POR"]:
            while True:
                random_location = self.pacific_union.sample_points(1).get_coordinates()
                lon = random_location["x"].values[0]
                lat = random_location["y"].values[0]
                if -inc <= lat <= inc:
                    break
        elif latlonstr in ["AO","Atlantic"]: 
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
        elif latlonstr in ["Indian O?"]:
            indian_ocean = self.ocean_shapefile[self.ocean_shapefile.name.isin(['Indian Ocean'])] 
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if indian_ocean.geometry.contains(coordinate).any():
                    break 
        elif latlonstr in ["S of Tasmania?"]:
            lon_lat_list = [[153.23, -30.02],[146.83, -43.64],[166.00, -50.92], [167.53, -47.29],
                            [168.14, -46.85], [168.85, -46.66], [174.28, -41.72], [175.28, -41.62], [173.01, -34.39]]
            tasman_sea_geom = Polygon(lon_lat_list)
            tasman_sea = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[tasman_sea_geom])
            while True:
                lat = round(random.uniform(-inc, inc),2)
                lon = round(random.uniform(-180, 180),2)
                coordinate = Point(lon,lat)
                if tasman_sea.geometry.contains(coordinate).any():
                    break 
        elif latlonstr in ["SE IOR?","SE IOR"]:
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
        
        lat = np.float64(lat) 
        lon = np.float64(lon) 
            
        return lat, lon, manual_loc
    
    def falcon_stage_lat_lon(self,daystr,monstr,jsr_id):
        
        """Set the geolocation for all Falcon 9 1st stages.

        Returns:
            lat(np.float64) : The latitude of the object.
            lon(np.float64) : The longitude of the object..
        """        
        
        matching = self.ocean_landings[self.ocean_landings["Date"].isin([f"{self.year}-{monstr}-{daystr}"])].reset_index(drop=True)
        if (matching.shape[0] == 1) or (f"{self.year}-{monstr}-{daystr}" == "2022-04-27"):
            # This is 27th April - typo in Raul's Space Map where second should be 2023. 
            lat = np.array(matching["geometry"].y)[0]
            lon = np.array(matching["geometry"].x)[0]
        # These next two are where there are two launches on the same day.
        elif jsr_id == "2022-124":
            lat = np.array(matching["geometry"].y)[0]
            lon = np.array(matching["geometry"].x)[0]
        elif jsr_id == "2022-125":
            lat = np.array(matching["geometry"].y)[1]
            lon = np.array(matching["geometry"].x)[1]
        elif matching.shape[0] == 0:
            matching = self.ground_landings[self.ground_landings["Date"].isin([f"{self.year}-{monstr}-{daystr}"])].reset_index(drop=True)
            if matching.shape[0] == 1:
                lat = np.array(matching["geometry"].y)[0]
                lon = np.array(matching["geometry"].x)[0]
            elif jsr_id == "2022-144":
                # This is 1st Nov - Falcon Heavy where two boosters land. 
                lat = np.array(matching["geometry"].y)[0]
                lon = np.array(matching["geometry"].x)[0]
            elif matching.shape[0] == 0:
                found_launch = False
                for i in range(len(self.dsl["COSPAR_ID"])):
                    if self.dsl["COSPAR_ID"].values[i] == jsr_id:
                        found_launch = True
                        launch_site = self.dsl["Launch_Site"].values[i]
                        if launch_site == "Kennedy Space Center (ETR)":
                            lat = 34
                            lon = -75   
                        elif launch_site in ["Vandenberg AFB (WTR)","Vandenberg Space Force Base"]:
                            lat = 30
                            lon = -120 
                        else:
                            sys.exit("Falcon launch site not found.")
                if found_launch == False:
                    sys.exit(f"Problem geolocating Falcon Stage 1 recovery - {jsr_id}.")
            elif matching.shape[0] > 1:
                sys.exit(f"Multiple ground entries for Falcon Stage 1 landing- {jsr_id}.")
            else:
                sys.exit(f"Problem geolocating Falcon Stage 1 landing- {jsr_id}.")
        elif matching.shape[0] > 1:
            sys.exit(f"Multiple ocean entries for Falcon Stage 1 landing- {jsr_id}.")
        else:
            sys.exit(f"Problem geolocating Falcon Stage 1 landing- {jsr_id}.") 
            
        return lat, lon 
    
    def falcon_fairing_lat_lon(self,daystr,monstr,jsr_id):   
        
        """Set the geolocation for all Falcon 9 fairings.

        Returns:
            lat(np.float64) : The latitude of the object.
            lon(np.float64) : The longitude of the object..
        """
        
        matching = self.fairings[self.fairings["Date"].isin([f"{self.year}-{monstr}-{daystr}"])].reset_index(drop=True)
        if matching.shape[0] == 1:
            lat = np.array(matching["geometry"].y)[0]
            lon = np.array(matching["geometry"].x)[0]
        elif matching.shape[0] == 0:
            found_launch = False
            for i in range(len(self.dsl["COSPAR_ID"])):
                if self.dsl["COSPAR_ID"].values[i] == jsr_id:
                    found_launch = True
                    launch_site = self.dsl["Launch_Site"].values[i]
                    if launch_site == "Kennedy Space Center (ETR)":
                        lat = 34
                        lon = -75   
                    elif launch_site in ["Vandenberg AFB (WTR)","Vandenberg Space Force Base"]:
                        lat = 30
                        lon = -120 
                    else:
                        sys.exit("Falcon launch site not found.")
            if found_launch == False:
                sys.exit(f"Problem geolocating Falcon fairing recovery - {jsr_id}.")
        elif matching.shape[0] > 1:
            sys.exit(f"Multiple entries for Falcon fairing recovery - {jsr_id}.")
        else:
            sys.exit(f"Problem geolocating Falcon fairing recovery - {jsr_id}.")
              
        return lat, lon
        
    def convert_time(self,date):
        
        """Converts the "DDate" listing from GCAT to day, month, and time strings.

        Returns:
            monstr(str):   The zero padded month.
            daystr(str):   The zero padded day.
            time_utc(str): The decimal time in hours.
        """        
        date[1] = date[1].replace("?","")
        mon = datetime.strptime(date[1], '%b').month  
        if mon in np.arange(10):
            monstr = "0" + str(mon)
        else:
            monstr = str(mon)
        if len(date) > 2: 
            day = date[2].replace("?","")
            if int(day) in np.arange(10):
                daystr = "0" + day
            else:
                daystr = day
        elif date == ['2022', 'Apr']:
            # DISCOSweb puts reentry on Mar 31st. Setting as March 31st.
            daystr = "31"
            monstr = "03"
        elif date == ['2022', 'Dec']:
            # DISCOSweb puts reentry on Nov 30th. Setting as Nov 30th.
            daystr = "30"
            monstr = "11"
        else:
            print(date)
            daystr = "01"
        
        if len(date) >= 4:    
            time_utc = np.float64(int(date[3].replace("?","")[0:2]) + int(date[3].replace("?","")[2:4]) / 60)
        else:
            time_utc = -1  
        
        return monstr, daystr, time_utc 
    
    def failed_launch_mass(self, jsr_id, jsr_name, reentry_stage):
        
        """For all failed launches, set the masses manually as we need to differentiate wet vs dry mass reentry.

        Returns:
            mass(float)       : The mass of aluminium.
            non_al_mass(float): Extra non-aluminium mass.
        """        
            
        mass = 0
        non_al_mass = 0
        
        for i in range(len(self.dsl["COSPAR_ID"])):
            if self.dsl["COSPAR_ID"].values[i] == jsr_id:
                for count, rocket_name in enumerate(self.dsr["Rocket_Name"].values):
                    if rocket_name == self.dsl["Rocket_Type"].values[i]:
                        rocket_ind = count
                        
        if reentry_stage == 0:
            mass = self.dsr["Booster_StageMass"].values[rocket_ind] / int(self.dsr["Booster_No"].values[rocket_ind])
        if reentry_stage in [1,2,3,4]:
            mass = self.dsr[f"Stage{reentry_stage}_StageMass"].values[rocket_ind]
        elif "fairing" in jsr_name.lower():
                mass = self.dsr["Fairing_Mass"].values[rocket_ind]  / 2    
        elif reentry_stage == 5:
            
            # 2020
            if jsr_name == "Zafar":
                mass = 113
            elif jsr_name == "Xinjishu Yanzheng 6":
                mass = 6550
            elif jsr_name == "Nusantara Dua":
                mass = 5550
            elif jsr_name == "CE-SAT-I":
                mass = 67
            elif "Flock 4e" in jsr_name:
                mass = 5.8
            elif jsr_name == "Faraday-1":
                mass = 10
            elif jsr_name == "Jilin-1 Gaofen 02E":
                mass = 201    
            elif jsr_name == "Xiangrikui 2":
                mass = 97
            elif jsr_name == "Neimonggol 1":
                mass = 230
            elif jsr_name == "SEOSat-Ingenio":
                mass = 750
            elif jsr_name == "Taranis":
                mass = 175 
            elif jsr_name == "Astra Test Payload":
                mass = 5

            # 2021   
            elif jsr_name == "Global-10":
                mass = 60
            elif jsr_name == "Global-11":
                mass = 60
            elif jsr_name == "Tolou-2?":
                mass = 90
            elif jsr_name == "Jilin-1 Mofang 01":
                mass = 18
            elif jsr_name == "GISAT-1":
                mass = 2286
            elif jsr_name == "Wiseongmosache":
                mass = 1500
            elif jsr_name == "GeeSat-1A":
                mass = 130
            elif jsr_name == "GeeSat-1B":
                mass = 130
            elif jsr_name == "Test payloads":
                mass = 90
                
            # 2022
            elif jsr_name == "R5-S1":
                mass = 1
            elif jsr_name == "INCA":
                mass = 3.8
            elif jsr_name == "QubeSat":
                mass = 4
            elif jsr_name == "BAMA-1":
                mass = 4
            elif jsr_name == "Jilin-1 Mofang 01A/R":
                mass = 18
            elif jsr_name == "TROPICS SV02":
                mass = 5.34
            elif jsr_name == "TROPICS SV04":
                mass = 5.34
            elif jsr_name == "EOS-02":
                mass = 145
            elif jsr_name == "AzaadiSAT":
                mass = 8
            elif jsr_name == "ESMS":
                mass = 200
            elif jsr_name == "RAISE-3":
                mass = 110
            elif jsr_name == "Amateru-I":
                mass = 170
            elif jsr_name == "Amateru-II":
                mass = 170
            elif jsr_name == "E-SSOD 1":
                mass = 10
            elif jsr_name == "E-SSOD 2":
                mass = 10
            elif jsr_name == "E-SSOD 3":
                mass = 10
            elif jsr_name == "MITSUBA":
                mass = 1.7
            elif jsr_name == "WASEDA-SAT-ZERO":
                mass = 1.2
            elif jsr_name == "MAGNARO A":
                mass = 3
            elif jsr_name == "MAGNARO B":
                mass = 1.5
            elif jsr_name == "KOSEN-2":
                mass = 2.7
            elif jsr_name == "FSI-SAT":
                mass = 1.4
            elif jsr_name == "Zhixing 1B":
                mass = 50       
            elif "Unknown payload" in jsr_name:
                mass = 10
            elif jsr_name == "Pleiades Neo 5":
                mass = 920
            elif jsr_name == "Pleiades Neo 6":
                mass = 920
                     
        # Add second stage propellant mass to non aluminium mass.    
        if jsr_id in ["2020-F02","2020-F05",
                      "2021-F02",
                      "2022-F01","2022-F02","2022-F03"] and reentry_stage == 2:
            non_al_mass = self.dsr[f"Stage2_PropMass"].values[rocket_ind]
            if jsr_id == "2022-F03":
                non_al_mass = non_al_mass * 0.24
                
        # Add third stage propellant mass to non aluminium mass.    
        if jsr_id in ["2020-F02","2020-F03","2020-F05","2020-F06",
                      "2021-F02","2021-F06","2021-F09","2021-F10",
                      "2022-F02","2022-F05","2022-F07"] and reentry_stage == 3:   
            non_al_mass = self.dsr[f"Stage3_PropMass"].values[rocket_ind]
            if jsr_id == "2021-F09":
                non_al_mass = non_al_mass * 0.08
                    
        # Add fourth stage propellant mass to non aluminium mass.  
        if jsr_id in ["2020-F08","2020-F09",
                      "2021-F10",
                      "2022-F02","2022-F04","2022-F05","2022-F07"] and reentry_stage == 4:   
            non_al_mass = self.dsr[f"Stage4_PropMass"].values[rocket_ind]

        return mass, non_al_mass
        
    def sort_inclination(self,jsr_inc,jsr_id):      
        
        """When the inclination on file is zero (including failed), this function sets it appropriately.
        This is mainly the case for lower suborbital stages, which can then be set using the inclination of an upper stage or payload.

        Returns:
            jsr_inc(np.float64): The orbital inclination of the object.
        """        
        
        # Try to find an entry from satcat/auxcat that is already loaded.
        # NOTE: Occasionally, the inclinations are slightly different for each object
        # The difference is usually <1 degree, but can be higher. As we don't know which inclination is 'correct',
        # we use the larger one to bound the geolocation.
        count = 0
        for reentry in (self.unique_reentry_list):
            if reentry["id"][:8] == jsr_id[:8] and reentry["inc"] != 0:
                if count == 0:
                    jsr_inc = reentry["inc"] 
                elif count > 0:
                    if reentry["inc"] > jsr_inc:
                        #if (reentry["inc"] - jsr_inc) > 2:
                            #print(f"Inclination difference of {reentry['inc'] - jsr_inc}, {reentry['inc']}, {jsr_inc}, {jsr_id}")
                        jsr_inc == reentry["inc"]
                count += 1
            
        # Sometimes, there is no entry in the reentry list because it didn't meet the criteria before.
        # In this case we need to reload the satcat to look for any matching entries.
        if jsr_inc == 0:
            for filename in ["./Databases/Reentry/JSR_Cat/satcat_2ndNov.tsv","./Databases/Reentry/JSR_Cat/ftocat_2ndNov.tsv"]:
                jsr_data = pd.read_csv(filename, delimiter='\t', dtype=object)
                satcat_list = []
                for reentry_count in range(1,len(jsr_data)):
            
                    if jsr_data["Piece"][reentry_count][:8] == "2020-F09":
                        new_id = "2020-F10"
                    elif jsr_data["Piece"][reentry_count][:8] == "2020-U01":
                        new_id = "2020-F09"
                    elif jsr_data["Piece"][reentry_count][:8] == "2022-U02":
                        new_id = "2022-F04"
                    elif jsr_data["Piece"][reentry_count][:8] == "2022-F04":
                        new_id = "2022-F05"
                    elif jsr_data["Piece"][reentry_count][:8] == "2022-F05":
                        new_id = "2022-F06"
                    elif jsr_data["Piece"][reentry_count][:8] == "2022-F06":
                        new_id = "2022-F07"
                    else:
                        new_id = jsr_data["Piece"][reentry_count][:8]
                    
                    if (
                        jsr_data["Primary"][reentry_count] == "Earth" 
                        and new_id == jsr_id[:8]
                        and np.float64(jsr_data["Inc"][reentry_count]) != 0
                    ):
                        satcat_list.append(jsr_data.iloc[[reentry_count]])
                if len(satcat_list) > 0:
                    satcat = pd.concat(satcat_list, ignore_index=True)
                    count = 0
                    for i in range(len(satcat)):
                        if satcat["Status"][i] in ["O","R","DSO","DSA","AF","AS","F","S","GRP","AO","AR"]:
                            if count == 0:
                                jsr_inc = np.float64(satcat["Inc"][i])
                            elif count > 0:
                                if np.float64(satcat["Inc"][i]) > jsr_inc:
                                    #if (np.float64(satcat["Inc"][i]) - jsr_inc) > 2:
                                        #print(f"Inclination difference of {np.float64(satcat['Inc'][i]) - jsr_inc}, {np.float64(satcat['Inc'][i])}, {jsr_inc}, {jsr_id}")
                                    jsr_inc == np.float64(satcat["Inc"][i])
                            count += 1
                        else:
                            print(f'Extra item loaded for inclination, {jsr_id},{satcat["Status"][i]}')
                
        if jsr_inc == 0:
            print(f"inc still empty for {jsr_id}")
            
        return jsr_inc 
         
    def extract_jsr_info(self, filepath):
        
        """For each GCAT database, extract all the relevant information and output to the dictionary of all reentry objects.
        """        
        
        # Load in the database.
        jsr_data = pd.read_csv(filepath, delimiter='\t', dtype=object)
        # Only include specific statuses (see https://planet4589.org/space/gcat/web/intro/phases.html)
        jsr_data_stripped = jsr_data[jsr_data["Status"].isin(["R","R?","D","L","L?","S","F","AF","AS"])].reset_index(drop=True)
        
        jsr_data_stripped_2020_list = []
        for reentry_count in range(len(jsr_data_stripped)):
            # For some reason, there are 4 CZ-8 boosters listed in JSR rcat for 2020-102.
            # Should only be two, and mass looks correct for each booster. Removing two (Jonathan has since updated his database to correct this).
            # Also removing 1st stage for 2020-F09 (U01 in GCAT). Apogee is 50km but is probably too low using the rocket configs used for stage altitudes.
            # TODO: Check failed launch stage altitudes.
            # Check this after updating stage altitudes and for 2021/22.
            
            # Skipping 2021-U01, 2022-U01 and 2022-U03, all military tests.
        
            if jsr_data_stripped["DDate"][reentry_count][0:4] != "-" and jsr_data_stripped["#JCAT"][reentry_count] not in ["R80054","R80055","L80348",
                                                                                                                           "L80508","L80509","L80510"  # Skipping 2021-F07
                                                                                                                           ]:
                # Note: A negative apogee means that the object was in a hyperbolic orbit (velocity above escape velocity), so passes by Earth.
                # However, Hayabusa2 (apogee=-54771) did reenter on 5th Dec, so including this.

                if (jsr_data_stripped["Apogee"][reentry_count] == "-") or ("Inf" in jsr_data_stripped["Apogee"][reentry_count]):
                    jsr_data_stripped["Apogee"][reentry_count] = 0
                
                if (
                    int(jsr_data_stripped["DDate"][reentry_count][0:4]) == self.year                              # This year only
                    and (int(jsr_data_stripped["Apogee"][reentry_count]) >= 50 or int(jsr_data_stripped["Apogee"][reentry_count]) == -54771) # Apogee above 50 km.           
                    and jsr_data_stripped["Piece"][reentry_count][5:6] != "S"                                     # No suborbital launches (mainly military rockets.)
                    and jsr_data_stripped["Piece"][reentry_count][:8] not in ["2021-U01","2022-U01","2022-U03"]   # No military test flights.
                    and jsr_data_stripped["Primary"][reentry_count] == "Earth"                                    # Only objects whose primary body is Earth.
                ): 
                    if jsr_data_stripped["Status"][reentry_count] == "AS":
                        if jsr_data_stripped["Piece"][reentry_count][5:6] in ["F","U"]: 
                            jsr_data_stripped_2020_list.append(jsr_data_stripped.iloc[[reentry_count]])
                    else:
                        jsr_data_stripped_2020_list.append(jsr_data_stripped.iloc[[reentry_count]])
        # Rebuild the database.
        if len(jsr_data_stripped_2020_list) > 0:          
            jsr_data_stripped_2020 = pd.concat(jsr_data_stripped_2020_list, ignore_index=True)
        else:
            jsr_data_stripped_2020 = []
        # Now loop over the list and format into a dictionary.
        for reentry_count in range(len(jsr_data_stripped_2020)):
            
            jsr_id = jsr_data_stripped_2020["Piece"][reentry_count] 
            jsr_name = jsr_data_stripped_2020["Name"][reentry_count]
            jsr_inc = np.float64(jsr_data_stripped_2020["Inc"][reentry_count])
            jsr_dest = jsr_data_stripped_2020["Dest"][reentry_count]
            jsr_apogee = int(jsr_data_stripped["Apogee"][reentry_count])
         
            # The failure numbers are labelled differently for 2020 in DW and JSR. To make sure the main script runs OK, adjust the COSPAR ID here.
            if jsr_id == "2020-F09":
                jsr_id = "2020-F10"
            elif jsr_id == "2020-U01":
                jsr_id = "2020-F09"
            elif jsr_id == "2022-U02":
                jsr_id = "2022-F04"
            elif jsr_id == "2022-F04":
                jsr_id = "2022-F05"
            elif jsr_id == "2022-F05":
                jsr_id = "2022-F06"
            elif jsr_id == "2022-F06":
                jsr_id = "2022-F07"
            
            # Set the burnup as partial for all re-entering capsules.
            if jsr_name in ["Soyuz MS-13","Soyuz MS-15","Soyuz MS-16","Soyuz MS-17",
                            "Soyuz MS-18","Soyuz MS-19","Soyuz MS-20","Soyuz MS-21",
                            "Shenzhou 12", "Shenzhou 13", "Shenzhou 14",
                            "Endeavour","Endurance","Freedom","Resilience",
                            "Axiom Ax-1","Inspiration4","XZF-SC","X-37B OTV-6",
                            "Dragon CRS-18","Dragon CRS-19", "Dragon CRS-20",
                            "Dragon CRS-21","Dragon CRS-22", "Dragon CRS-23",
                            "Dragon CRS-24","Dragon CRS-25", "Dragon CRS-20",
                            "Starliner OFT-2","Artemis I","Chonfu Shiyong Shiyan HQ",
                            "Bernard Kutter LOFTID","Hayabusa 2 Return Capsule","Chang'e-5 Fanhui Qi",
                            ]:
                burnup = "Partial"
            else:
                #if jsr_data_stripped_2020["Status"][reentry_count] == "L" and "Falcon 9" not in jsr_name:
                    #print(jsr_name)
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
            
            # Handle categories.
            if jsr_data_stripped_2020["Type"][reentry_count][:1] == "R":
                # Sort out the rocket stages. This is mainly Soyuz (Russian's just do the numbering differently), and errors in the GCAT.
                reentry_stage = int(jsr_data_stripped_2020["Type"][reentry_count][1:2])
                if jsr_data_stripped_2020["#JCAT"][reentry_count] in ["R81714","R81715"]:
                    reentry_stage = 0
                if jsr_data_stripped_2020["Name"][reentry_count] in ["RSRMV-1L","RSRMV-1R"]:
                    reentry_stage = 0    
                if "Blok-BVGD" in jsr_data_stripped_2020["Bus"][reentry_count]:
                    reentry_stage = 0
                elif "Blok-A" in jsr_data_stripped_2020["Bus"][reentry_count]:
                    reentry_stage = 1
                elif "Blok-I" in jsr_data_stripped_2020["Name"][reentry_count]:
                    reentry_stage = 2
                elif "Fregat" in jsr_data_stripped_2020["Name"][reentry_count]:
                    reentry_stage = 3
                elif jsr_data_stripped_2020["Piece"][reentry_count] in ["2020-028C","2021-086B","2021-097B","2021-112B","2022-066B","2022-102B"]:
                    reentry_stage = 4  
                reentry_type = "R/B"
            elif jsr_data_stripped_2020["Type"][reentry_count][:1] in ["C","P"]:
                reentry_stage = 5
                if jsr_data_stripped_2020["Type"][reentry_count][:1] == "C":
                    reentry_type = "Component"
                elif jsr_data_stripped_2020["Type"][reentry_count][:1] == "P":
                    reentry_type = "Payload"
            else:
                reentry_stage = -1
                
            #for reentry in self.unique_reentry_list:
                #if jsr_id == reentry["id"] and jsr_name == reentry["name"] and reentry_stage != 0 and "fairing" not in jsr_name.lower():
                    #print(f"Already an item with id {jsr_id}, name {jsr_name}")
                
            # Sort the inc.
            if jsr_inc == 0:
                jsr_inc = self.sort_inclination(jsr_inc,jsr_id)
                
            # Sort out the reentry lat/lon.
            if ("Falcon 9 Stage 1" in jsr_name) and (jsr_data_stripped_2020["#JCAT"][reentry_count] != "R81716"):
                lat, lon = self.falcon_stage_lat_lon(daystr,monstr,jsr_id)
                burnup = "Partial"
                manual_loc = 0
            elif ("Falcon 9 Fairing" in jsr_name) or ("Falcon Heavy Fairing" in jsr_name):    
                lat, lon = self.falcon_fairing_lat_lon(daystr,monstr,jsr_id)
                burnup = "Partial"
                manual_loc = 0
            else:   
                lat, lon, manual_loc = self.convert_lat_lon(jsr_dest, jsr_inc, reentry_stage, jsr_apogee, jsr_id)
            
            # Sort the mass.      
            if jsr_id[5:6] in ["F","U"]:
                al_mass, non_al_mass = self.failed_launch_mass(jsr_id, jsr_name, reentry_stage)
            else:
                al_mass = np.float64(jsr_data_stripped_2020["DryMass"][reentry_count])
                non_al_mass = 0
            
            # Check for items with a missing geolocation (should have been dealt with already so this is just a sanity check).    
            if lat == 0 and lon == 0:
                print(f"No location for {jsr_id}, dest = {jsr_data_stripped_2020['Dest'][reentry_count]}")
            
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
                    "al_mass"      : al_mass,
                    "non_al_mass"  : non_al_mass,
                    "manual_loc"   : manual_loc,
                    "inc"          : jsr_inc,
                }
                
                self.unique_reentry_list.append(temp_reentry_dict)   
    
    def add_cargo(self,filepath):
        
        """Short function to add the cargo mass to its parent object.
        """        
        
        jsr_data = pd.read_csv(filepath, delimiter='\t', dtype=object)        
        for reentry_count in range(len(jsr_data)):           
            if jsr_data["Status"][reentry_count] in ["AL IN","AR IN"] and int(jsr_data["DDate"][reentry_count][0:4]) == self.year:
                cargo_found = False 
                for reentry in self.unique_reentry_list:
                    if reentry["jcat"] == jsr_data["Parent"][reentry_count]:
                        reentry["non_al_mass"] += np.float64(jsr_data["DryMass"][reentry_count]) 
                        cargo_found = True    
                        if jsr_data["Piece"][reentry_count][5:6] in ["F","U","S"]:
                            sys.exit(f'Cargo in failed/suborbital object {jsr_data["Piece"][reentry_count]}.')
                    if reentry["jcat"] == "S51660" and jsr_data["#JCAT"][reentry_count] == "A09988":
                        reentry["non_al_mass"] += np.float64(jsr_data["DryMass"][reentry_count])
                        cargo_found = True
                    if reentry["jcat"] == "A06581" and jsr_data["#JCAT"][reentry_count] == "A09680":
                        reentry["non_al_mass"] += np.float64(jsr_data["DryMass"][reentry_count])
                        cargo_found = True    
                if cargo_found == False:
                    print(f'Cargo missing for {jsr_data["Piece"][reentry_count]}')                    
     
    def add_attached(self):
        
        for filepath in ["./Databases/Reentry/JSR_Cat/satcat_2ndNov.tsv","./Databases/Reentry/JSR_Cat/auxcat_2ndNov.tsv",
                            "./Databases/Reentry/JSR_Cat/lcat_2ndNov.tsv","./Databases/Reentry/JSR_Cat/rcat_2ndNov.tsv",
                            "./Databases/Reentry/JSR_Cat/lprcat_2ndNov.tsv","./Databases/Reentry/JSR_Cat/deepcat_7thNov.tsv",
                            "./Databases/Reentry/JSR_Cat/ecat_8thNov.tsv"]:
            attached_data = pd.read_csv(filepath, delimiter='\t', dtype=object)
            attached_data_stripped = attached_data[attached_data["Status"].isin(["AR","AS","AL"])].reset_index(drop=True)   
            missing_list = []
            added = 0
            # First see if the parent is already in the reentry list. Add the mass to the parent object if it is, or add the details to a list if missing.
            
            for reentry_count in range(len(attached_data_stripped)): 
                if int(attached_data_stripped["DDate"][reentry_count][0:4]) == self.year and attached_data_stripped["Piece"][reentry_count][5:6] not in ["S","F","U"]:
                    #if attached_data_stripped["Status"][reentry_count] == "AL":
                        #print("AL",filepath) 
                    found_parent = False
                    for reentry in self.unique_reentry_list:
                        if reentry["jcat"][:6] == attached_data_stripped["Parent"][reentry_count][:6]:
                            found_parent = True
                            added += 1
                            if reentry["id"][:8] != attached_data_stripped["Piece"][reentry_count][:8]:
                                pass
                                #print(f'Found missing item in original list. {reentry["id"]},{attached_data_stripped["Piece"][reentry_count]},{filepath}.')
                            reentry["al_mass"] += np.float64(attached_data_stripped["DryMass"][reentry_count]) 
                            

                    if found_parent == False and filepath not in ["./Databases/Reentry/JSR_Cat/lprcat_2ndNov.tsv"]:
                        missing_list.append([attached_data_stripped['Piece'][reentry_count],
                                             attached_data_stripped['Parent'][reentry_count][:6],
                                             attached_data_stripped["DryMass"][reentry_count],
                                             filepath])          
            # Loopover all items where the parent couldn't be found. The parent is always starts with A, but is usually in the ecat.
            for i in range(len(missing_list)):
                found_parent = False
                if missing_list[i][1][0] != "A":
                    sys.exit("Item has a missing parent from another database than auxcat.")
                ecat_data = pd.read_csv("./Databases/Reentry/JSR_Cat/ecat_8thNov.tsv", delimiter='\t', dtype=object)  
                # Now loop over the ecat and look for the parent.
                for reentry_count in range(len(ecat_data)): 
                    if (missing_list[i][1] == ecat_data['#JCAT'][reentry_count][:6]
                    and ecat_data['Status'][reentry_count] in ["AR","AL"]):
                        for reentry_count_2 in range(len(ecat_data)): 
                            if (ecat_data['Parent'][reentry_count][:6] == ecat_data['#JCAT'][reentry_count_2][:6]
                            and ecat_data['Status'][reentry_count_2] in ["D","L"]):
                                # If we find the grandparent, then hopefully the object is already in the reentry list.
                                for reentry in self.unique_reentry_list:
                                    if ecat_data['#JCAT'][reentry_count_2][:6] == reentry["jcat"][:6]:
                                        if reentry["id"][:8] != missing_list[i][0][:8]:
                                            pass
                                            #print(f'Found missing item in ecat. {reentry["id"]},{missing_list[i][0]},{filepath}.')
                                        reentry["al_mass"] += np.float64(missing_list[i][2])
                                        added += 1
                                        found_parent = True
                        
                if found_parent == False:
                    aux_data = pd.read_csv("./Databases/Reentry/JSR_Cat/auxcat_2ndNov.tsv", delimiter='\t', dtype=object)
                    for reentry_count in range(len(aux_data)): 
                        if (missing_list[i][1] == aux_data['#JCAT'][reentry_count][:6]
                        and aux_data['Status'][reentry_count] in ["AR","AL"]):    
                               
                            # If the grandparent is also in the auxcat, then look for the grandparent.
                            if aux_data['Parent'][reentry_count][0] == "A":             
                                for reentry_count_2 in range(len(aux_data)): 
                                    if (aux_data['Parent'][reentry_count][:6] == aux_data['#JCAT'][reentry_count_2][:6]
                                        and aux_data['Status'][reentry_count_2] in ["D","L"]):
                                        # If we find the grandparent, then hopefully the object is already in the reentry list.
                                        for reentry in self.unique_reentry_list:
                                            if aux_data['#JCAT'][reentry_count_2][:6] == reentry["jcat"][:6]:
                                                if reentry["id"][:8] != missing_list[i][0][:8]:
                                                    pass
                                                    #print(f'Found missing item in existing reentries. {reentry["id"]},{missing_list[i][0]},{filepath}.')
                                                reentry["al_mass"] += np.float64(missing_list[i][2])
                                                added += 1
                                                found_parent = True
                            # If the grandparent starts with S, its either in the satcat or ecat, and has probably already been added to the list.
                            elif aux_data['Parent'][reentry_count][0] == "S":
                                for reentry in self.unique_reentry_list:
                                    if aux_data['Parent'][reentry_count][:6] == reentry["jcat"][:6]:
                                        if reentry["id"][:8] != missing_list[i][0][:8]:
                                            pass
                                            #print(f'Found missing item in existing reentries. {reentry["id"]},{missing_list[i][0]},{filepath}.')
                                        reentry["al_mass"] += np.float64(missing_list[i][2])
                                        added += 1
                                        found_parent = True
                            else:
                                print("Grandparent does not start with S or A.")
                # For 2022-002, for A10426/7/8, the parent chain is A09939/42 > 38 > 37. So just hard setting to avoid a huge indented block.            
                if missing_list[i][1] in ["A09942","A09939"]:
                    for reentry in self.unique_reentry_list:
                        if reentry["jcat"][:6] == "A09937":
                            reentry["al_mass"] += np.float64(missing_list[i][2])
                            added += 1
                            found_parent = True
                                        
                if found_parent == False:
                    print(missing_list[i])
                    
            #print(added)
        
    def extract_aerospace_info(self, filepath):
        
        """Use the Aerospace Corp database to fill in  missing time information and any other missing objects.
        """
        
        # First load the database and strip to only reentries in the year specified.        
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
        for reentry_count in range(len(aerospace_corp_data_year)):  
            if aerospace_corp_data_year["International Designator"][reentry_count] not in jsr_id_list:
                #print(f"Found new reentry from Aerospace Corp - {aerospace_corp_data_year['International Designator'][reentry_count]}, {aerospace_corp_data_year['Object Name'][reentry_count]}") 
                # 1992-021C, Ariane 44L H10+ 3rd Rocket Stage. DISCOSweb and AC list this as reentering in Oct 2020. JSR lists this as exploding in Apr 1993.
                # 2019-029Q, Starlink payload. DISCOSweb and JSR list this as reentering in July 2022. AC lists this as reentering in 2020. Ignoring.
                # 2020-012B, Starlink payload. DISCOSweb has no re-entry data. AC lists this as reentering Mar 2020. JSR lists this as still in orbit. Ignoring.
                # 2019-024AG, Starlink 2259, this should be 2021-024AG. Modified AC csv file.
                # 2020-001Z, Starlink 1072, listed as 2020-001X in JSR. Modified AC csv file.
                # 2021-074Z, Starlink 1901, this should be 2020-074Z.   Modified AC csv file.
                # 2021-073G, STARLINK-1731, this should be 2020-073G.   Modified AC csv file.
                # 2021-073BG, STARLINK-1827, this should be 2020-073BG. Modified AC csv file.
                # 2020-050B, this is wildly wrong, should be 2019-073B. Modified AC csv file. SSN seems to be correct each time.
                # 1977-010A , also wrong, should be 2020-064B. Modified AC csv file.
                # 1010-012BF, typo, should be 2020-012BF. Modified AC csv file.
                # 1998-067PU, according to JSR, this is a payload that was jettisoned due to a failed ISS disposal. https://www.planet4589.org/pipermail/jsr/2019-January/000134.html. Adding.
                # 2021-024AS, extra spaces in AC csv file, fixed.    
                # 2021-041K, STARLINK-2173, should be 2021-041H. Modified AC csv file.
                # 1982-092AJF, debris on DISCOSweb, JSR and AC, ignoring.  
                # 2021-125AE, this is already included in the 2021 reentry list, as JSR says it reentered on 28/12/21.
                if aerospace_corp_data_year["International Designator"][reentry_count] in ["1992-021C","1998-067PU"]:
                    if aerospace_corp_data_year["International Designator"][reentry_count] == "1992-021C":
                        reentry_stage = 3
                        al_mass = 2080
                    if aerospace_corp_data_year["International Designator"][reentry_count] == "1998-067PU": 
                        reentry_stage = 5
                        al_mass = 450
                    # Extract the UTC time.     
                    print(f"Adding reentry from Aerospace Corp - {aerospace_corp_data_year['International Designator'][reentry_count]}")      
                    reentry_time = aerospace_corp_data_year["Aerospace Reentry Prediction (UTC)"][reentry_count][11:16]
                    time_utc = np.float64(int(reentry_time[0:2]) + int(reentry_time[3:5]) / 60)
                    temp_reentry_dict = {
                        "id"           : aerospace_corp_data_year["International Designator"][reentry_count],
                        "jcat"         : "N/A",
                        "name"         : aerospace_corp_data_year["Object Name"][reentry_count],
                        "type"         : aerospace_corp_data_year["Type"][reentry_count],
                        "burnup"       : "Complete",
                        "reentry_stage": reentry_stage, # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                        "time"         : time_utc,
                        "mon"          : aerospace_corp_data_year["Aerospace Reentry Prediction (UTC)"][reentry_count][5:7],
                        "day"          : aerospace_corp_data_year["Aerospace Reentry Prediction (UTC)"][reentry_count][8:10],
                        "lat"          : round(random.uniform(-90,90),2),
                        "lon"          : round(random.uniform(-180, 180),2),
                        "al_mass"      : al_mass,
                        "non_al_mass"  : 0,
                        "manual_loc"   : 0,
                    }  
                    
                    self.unique_reentry_list.append(temp_reentry_dict)
    
    def extract_discosweb_info(self):
        
        """Look for and add any missing objects from DISCOSweb (contained within a netcdf file built in pull_from_discosweb.py).
        """        
        
        # Check what items are already in the list.
        jsr_ac_id_list = []
        for reentry in (self.unique_reentry_list):
            jsr_ac_id_list.append(reentry["id"]) 
        
        for reentry_count in range(len(self.ds_dw["DISCOSweb_Reentry_ID"].values)):
            
            # Excluding Debris
            valid_types = ["Rocket Body","Rocket Mission Related Object","Payload Mission Related Object","Payload"]
            if (self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count] not in jsr_ac_id_list) and self.ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in valid_types:
                
                # Check if the stage has already been added.  
                found_stage = False               
                if self.ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] == "Rocket Body":
                    reentry_type = "R/B"
                    
                    if self.ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["Falcon 9 Merlin-V (1D+) (Falcon 9 v1.2)","Falcon 9 Merlin-V (1D) (Falcon 9 v1.1)",
                                                                                 "H-II LE-5B (H-IIB)", "L-53 (YF24B) (Long March (CZ) 2D)","CZ-5-HO (Long March (CZ) 5)",
                                                                                "Delta IV DCSS 5 (Delta 4H)","Centaur-5 SEC (Atlas V 421)",
                                                                                "Centaur-5 SEC (Atlas V 401)","Centaur-5 DEC (Atlas V N22)"]:
                        reentry_stage = 2
                    elif (("Fregat" in self.ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count])
                        or (self.ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["PBV (Long March (CZ) 6)","YZ-1S (Long March (CZ) 2C/YZ-1S)",
                                                                                      "H-18 (Long March (CZ) YF) (Long March (CZ) 3C/E)","Angara AM (Angara 1.2)"])):
                        reentry_stage = 3 
                    elif self.ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count] in ["AVUM (Vega)","Ceres-1 upperstage","YZ-1 (Long March (CZ) 3B/YZ-1)",
                                                                                   "KZ-1 Stage 4 (Kuaizhou-1)","Long March (CZ) 11 Stage 4"]:
                        reentry_stage = 4
                    else:
                        print("Missing stage designation for : ",self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count], self.ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count])
                        reentry_stage = 0
                    
                    for reentry in self.unique_reentry_list:
                        if reentry["id"][:8] == self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count][:8] and str(reentry["reentry_stage"]) == str(reentry_stage):
                            found_stage = True
                            
                skipped_ids = ["2014-065A", # Chang'e 5-T1, reentered in 2014.
                               "2021-011A", # Progress MS-16 is listed in JSR as AR, so the mass is just added to the parent object and no object exists.
                               # Progress MS-16 has been added though, so we can ignore it.
                               "2020-001N", # Starlink, still in orbit??
                               "2020-001T", # Starlink, still in orbit??
                               "2017-069C", # Listed in JSR as still in orbit.
                               "2020-001AQ",# Starlink, still in orbit??
                               "2020-001BG",# Starlink, still in orbit??
                               "2020-001BF",# Starlink, still in orbit??
                               "2020-001A", # Starlink, still in orbit??
                               "2021-122E", # Debris.
                               "2020-001AU",# Starlink, still in orbit??
                               "1967-014M", # Debris.
                               
                               "2022-010ID", # https://www.spacex.com/launches/sl4-7/ 49 starlink satellites launched.
                               "2022-010IS", # https://en.wikipedia.org/wiki/List_of_Starlink_and_Starshield_launches 
                               "2022-010IE", # Wiki says 38 satellites reentered by 12th Feb, so ignoring all of these.
                               "2022-010IT", "2022-010IF", "2022-010IG", "2022-010IQ", "2022-010IR", "2022-010II",
                               "2022-010IO", "2022-010IB", "2022-010IY", "2022-010IJ", "2022-010IU", "2022-010IV",
                               "2022-010IAF","2022-010IH","2022-010IL",  "2022-010IX", "2022-010IAE","2022-010IW",       
                               "2022-010IK", "2022-010IC",
                               
                               "2015-007B", # Debris.
                               "2014-065B", # Reentered on the moon.
                               "1990-010C", # Debris.
                               "2022-085C", # Debris.
                               "2022-094B", # Falcon Stage 2 # JSR has this has as deep space.
                               "2014-047H", # Debris.
                               "2021-110A", # Deorbited on Didymos.
                               ]
                
                # Included IDs: 
                #               2020-022A https://www.n2yo.com/satellite/?s=45464     
                #               2020-029B DDate = "2023 Jan?", DISCOSweb has 31st Dec, so it has reentered and we can include.     
                if found_stage == False and self.ds_dw['DISCOSweb_Reentry_ID'].values[reentry_count] not in skipped_ids:
                    print(f"Adding object with COSPAR ID {self.ds_dw['DISCOSweb_Reentry_ID'].values[reentry_count]}")          
                
                    if self.ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object","Payload"]:
                        if self.ds_dw["DISCOSweb_Reentry_Class"].values[reentry_count] in ["Rocket Mission Related Object","Payload Mission Related Object"]:
                            reentry_type = "Component"
                        else: 
                            reentry_type = "Payload"
                        reentry_stage = 5

                    day = int(self.ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][8:10])
                    mon = int(self.ds_dw["DISCOSweb_Reentry_Epoch"].values[reentry_count][5:7])
                    time_utc = -1
                    
                    if self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count] == "2020-029B":
                        inc = 45.01
                    elif self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count] == "2020-022A":
                        inc = 26.50
                    else: 
                        sys.exit("Added object not expected.")
                    lat = round(random.uniform(-inc, inc),2)
                    lon = round(random.uniform(-180, 180),2)
                    mass = self.ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
                    if np.isnan(mass):
                        mass = 0
    
                    temp_reentry_dict = {
                        "id"           : self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count],
                        "jcat"         : "N/A",
                        "name"         : self.ds_dw["DISCOSweb_Reentry_Name"].values[reentry_count],
                        "type"         : reentry_type,
                        "burnup"       : "Complete",
                        "reentry_stage": reentry_stage, # -1 is nothing, 0 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                        "time"         : time_utc,
                        "mon"          : mon,
                        "day"          : day,
                        "lat"          : lat,
                        "lon"          : lon,
                        "al_mass"      : mass,
                        "non_al_mass"  : 0, 
                        "manual_loc"   : 1, 
                    }

                    self.unique_reentry_list.append(temp_reentry_dict)  
            
            else:
                # If the item already exists, check if the jsr entry is missing the mass information.
                # Only add if the jsr is missing the mass, and discosweb has the mass.
                # This is currently zero items, but leave this code in in case it is reused for future years.
                dict_ind = next((index for (index, d) in enumerate(self.unique_reentry_list) if d["id"] == self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count]), False)
                if dict_ind != False:
                    if (self.unique_reentry_list[dict_ind]["type"] in ["Component", "Payload"]) and ((self.unique_reentry_list[dict_ind]["al_mass"] +self.unique_reentry_list[dict_ind]["non_al_mass"]) == 0):
                        if not np.isnan(self.ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]):
                            self.unique_reentry_list[dict_ind]["payload_mass"] = self.ds_dw["DISCOSweb_Reentry_Mass"].values[reentry_count]
                            print("Added info for",self.ds_dw["DISCOSweb_Reentry_ID"].values[reentry_count])                       
         
    def add_missing_stages(self):
        
        """Add any missing stages for launches in the year.
        """        
        
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
                    
        # Based on rocket configurations, boosters will cutoff and detach above 50km for all configs except B+4S.  
        # So for B+1/2S and B+3S, we need a reentry event for each lost booster at the launch site.
        # For B+4S, 2S and 3S, the 1st stage will cutoff and detach within 100 km altitude, so we need a reentry event for each of these.
        
        # TODO: Stage altitudes. This should load in the actual BECO/MECO altitudes.
        # The default is add boosters for B+1/2S and B+3S, and 1st stage for B+4S, 2S, 3S, and 4S.
        
    
        # Loop over each launch in 2020, locate the rocket and then filter for rocket configuration.
        for i in range(len(self.dsl["COSPAR_ID"])):
            for count, rocket_name in enumerate(self.dsr["Rocket_Name"].values):
                if rocket_name == self.dsl["Rocket_Type"].values[i] and self.dsl["COSPAR_ID"].values[i][5] != "F":
                    # Count how many boosters are currently added, and compare it to the number of boosters there should be.
                    booster_count = 0
                    for reentry in self.unique_reentry_list:
                        if reentry["id"][:8] == self.dsl["COSPAR_ID"].values[i] and str(reentry["reentry_stage"])[0] == "B":
                            booster_count += 1
                    if booster_count != int(self.dsr['Booster_No'].values[count]):
                        print(f"There are {booster_count} boosters when there should be {self.dsr['Booster_No'].values[count]} boosters.")
                        # Adding boosters for B+1/2S and B+3S.
                        if (self.dsr["Booster_PropMass"].values[count] != 0) and (self.dsr["Stage4_PropMass"].values[count] == 0):    
                            print(f"Adding {int(self.dsr['Booster_No'].values[count])-booster_count} boosters for {self.dsl['COSPAR_ID'].values[i]}")
                            for j in range(int(self.dsr["Booster_No"].values[count])-booster_count):
                                mass = self.dsr["Booster_StageMass"].values[count] / int(self.dsr["Booster_No"].values[count])
                                if np.isnan(mass):
                                    mass = 0
                                    
                                temp_reentry_dict = {
                                    "id"           : f'{self.dsl["COSPAR_ID"].values[i]}',
                                    "jcat"         : "N/A",
                                    "name"         : f"{self.dsl['Rocket_Type'].values[i]} Booster",
                                    "type"         : "R/B",
                                    "burnup"       : "Complete",
                                    "reentry_stage": "B" + str(j+1), # -1 is nothing, B1-4 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                                    "time"         : self.dsl["Time(UTC)"].values[i],
                                    "mon"          : int(self.dsl["Month"].values[i]),
                                    "day"          : int(self.dsl["Day"].values[i]),
                                    "lat"          : self.dsl["Latitude"].values[i],
                                    "lon"          : self.dsl["Longitude"].values[i],
                                    "al_mass"      : mass,
                                    "non_al_mass"  : 0,
                                    "MCS"          : False,
                                    "manual_loc"   : 0,
                                }
                
                                self.unique_reentry_list.append(temp_reentry_dict) 
        
                    # Check the number of stages.
                    stage_count = np.zeros((4))
                    for reentry in self.unique_reentry_list:
                        for j in range(1,5):
                            if reentry["id"][:8] == self.dsl["COSPAR_ID"].values[i] and reentry["reentry_stage"] == j:
                                stage_count[j-1] += 1
                    #print(stage_count)
                    for stage in stage_count:
                        if stage > 1:
                            print(f"Multiple stages for {self.dsl['COSPAR_ID'].values[i]}")
                    
                    # Adding 1st stages for B+4S, 2S and 3S rockets. # TODO: Edit this.
                    if ((self.dsr["Booster_PropMass"].values[count] == 0) and (self.dsr["Stage4_PropMass"].values[count] == 0)) or ((self.dsr["Booster_PropMass"].values[count] != 0) and (self.dsr["Stage4_PropMass"].values[count] != 0)):    
                        # Check if there is a first stage, and add if not.
                        found_stage = False
                        for reentry in self.unique_reentry_list:
                            if reentry["id"][:8] == self.dsl["COSPAR_ID"].values[i] and reentry["reentry_stage"] == 1:
                                found_stage = True
                        if found_stage == False:
                            print(f"Adding 1st stage for {self.dsl['COSPAR_ID'].values[i]}")
                            mass = self.dsr["Stage1_StageMass"].values[count]
                            if np.isnan(mass):
                                mass = 0
                            
                            temp_reentry_dict = {
                                "id"           : f'{self.dsl["COSPAR_ID"].values[i]}S1',
                                "jcat"         : "N/A",
                                "name"         : f"{self.dsl['Rocket_Type'].values[i]} Stage 1",
                                "type"         : "R/B",
                                "burnup"       : "Complete",
                                "reentry_stage": 1, # -1 is nothing, B1-4 = Booster, 1-4 = Stage Number, 5 = Payload/Debris
                                "time"         : self.dsl["Time(UTC)"].values[i],
                                "mon"          : int(self.dsl["Month"].values[i]),
                                "day"          : int(self.dsl["Day"].values[i]),
                                "lat"          : self.dsl["Latitude"].values[i],
                                "lon"          : self.dsl["Longitude"].values[i],
                                "al_mass"      : mass,
                                "non_al_mass"  : 0,                              
                                "MCS"          : False,
                                "manual_loc"   : 0,
                            }
        
                            self.unique_reentry_list.append(temp_reentry_dict)
    
    def import_raul_spacex_map(self):
        """Import and set up the geolocation lists for falcon landings.
        """        
        
        # Import the data.
        fiona.drvsupport.supported_drivers['KML'] = 'rw'
        raul_data = gpd.read_file('./Databases/General_SpaceX_Map_Raul.kml', driver='KML', layer =2)
        
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
        self.ocean_landings = ocean_landings[(ocean_landings["Date"] < f'{self.year+1}-01-01') & (ocean_landings["Date"] >= f'{self.year}-01-01')].reset_index(drop=True)
            
        # Build the ground landing list for the year in question.
        ground_landings = raul_data[(raul_data["Name"].str.contains("landing")) & (raul_data["Name"].str.contains("LZ"))].reset_index(drop=True)
        ground_landings = ground_landings[~ground_landings["Name"].str.contains("planned")].reset_index(drop=True)
        date_col = []
        for landing in range(len(ground_landings["Name"])):
            year_ind = ground_landings["Description"][landing].index("Landing -")
            datestr = ground_landings["Description"][landing][year_ind:].replace(" ","")[8:17].replace("-","")
            date_col.append(datestr)
        ground_landings["Date"] = date_col
        ground_landings['Date'] = pd.to_datetime(ground_landings['Date'],format='%d%b%y')
        self.ground_landings = ground_landings[(ground_landings["Date"] < f'{self.year+1}-01-01') & (ground_landings["Date"] >= f'{self.year}-01-01')].reset_index(drop=True)
        
        # Build the fairing recovery list for the year in question.
        ocean_missions, ocean_dates = self.ocean_landings["Name"].tolist(), self.ocean_landings["Date"].tolist()
        ground_missions, ground_dates = self.ground_landings["Name"].tolist(), self.ground_landings["Date"].tolist()
        dataframe_size = 0
        for count,mission in enumerate(ocean_missions):
            mission_string = mission.replace("ASDS position","")
            extract_df = raul_data[(raul_data["Name"].str.contains(mission_string, regex=False)) & (raul_data["Name"].str.contains("fairing", regex=False))].reset_index(drop=True)
            extract_df["Date"] = ocean_dates[count]
            if dataframe_size == 0:
                fairings = extract_df
                dataframe_size += 1
            else: 
                fairings = pd.concat([fairings,extract_df], ignore_index=True)
        for count,mission in enumerate(ground_missions):
            mission_string = mission.replace("ASDS position","")
            extract_df = raul_data[(raul_data["Name"].str.contains(mission_string, regex=False)) & (raul_data["Name"].str.contains("fairing", regex=False))].reset_index(drop=True)
            extract_df["Date"] = ground_dates[count]
            if dataframe_size == 0:
                fairings = extract_df
                dataframe_size += 1
            else: 
                fairings = pd.concat([fairings,extract_df], ignore_index=True)
        self.fairings = fairings
                             
    def get_reentry_info(self):
        """This is the main function of this class, and loops over all the key databases (GCAT, AC, DW).
        It also does small final adjustments:
            - checks for duplicates
            - sets MCS info
            - sets rocket stage/fairing mass from database
            - fixes fairing geolocation
            - fixes timings where launch and reentry are on same day
            - sets any missing masses
            - fixes any geolocations on grid border (180E) 
        """        
        
        # Import the shapefiles and create unions for the main oceans.
        #self.ocean_shapefile = gpd.read_file("./Databases/GOaS_v1_20211214/goas_v01.shp")
        #pacific = self.ocean_shapefile[self.ocean_shapefile.name.isin(['North Pacific Ocean','South Pacific Ocean'])]
        #self.pacific_union = gpd.GeoDataFrame(geometry=[pacific.unary_union]) 
        #atlantic = self.ocean_shapefile[self.ocean_shapefile.name.isin(['North Atlantic Ocean','South Atlantic Ocean'])]
        #self.atlantic_union = gpd.GeoDataFrame(geometry=[atlantic.unary_union])
        
        self.country_shapefile = gpd.read_file("./Databases/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp") 
        self.states_shapefile = gpd.read_file("./Databases/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp") 
        
        # Import the netcdf files.
        self.ds_dw = xr.open_dataset(f"./Databases/Reentry/discosweb_reentries_{self.year}.nc", decode_times=False)
        self.dsr = xr.open_dataset(f"./Databases/rocket_info_{self.year}.nc", decode_times=False)
        self.dsl = xr.open_dataset(f"./Databases/launch_info_{self.year}.nc", decode_times=False) 
        
        # Import the landing data (https://t.co/RAsQ9NDmEr)
        self.import_raul_spacex_map()
             
        self.unique_reentry_list = []
        
        print("Adding JSR re-entries.") # (see https://planet4589.org/space/gcat/web/cat/cats.html)
        
        print("satcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/satcat_2ndNov.tsv")  # Load in the JSR satcat database (main database).
        print("auxcat") 
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/auxcat_2ndNov.tsv")  # Load in the JSR auxcat database (should be in main but isn't).
        print("lcat") 
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/lcat_2ndNov.tsv")    # Load in the JSR lcat database (suborbital stages/objects).
        print("rcat") 
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/rcat_2ndNov.tsv")    # Load in the JSR rcat database (lower stages and fairings).
        print("lprcat") 
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/lprcat_2ndNov.tsv")  # Load in the JSR lprcat database (several objects returning from space).
        print("deepcat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/deepcat_7thNov.tsv") # Load in the JSR deepcat database (several objects returning from space).
        print("ecat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/ecat_8thNov.tsv")    # Load in the JSR ecat database (capsules from ISS / crewed missions).
        print("ecat cargo")
        self.add_cargo("./Databases/Reentry/JSR_Cat/ecat_8thNov.tsv")           # Load in the JSR ecat database.
        print("ftocat")
        self.extract_jsr_info("./Databases/Reentry/JSR_Cat/ftocat_2ndNov.tsv")  # Load in the JSR ftocat database.
        print("attached")
        self.add_attached()

        # There was nothing of use in hcocat, tmpcat and csocat.   
        
        # This code checks for duplicate reentries with the same jcat id.         
        self.jsr_jcat_list = []
        for reentry in self.unique_reentry_list:
            self.jsr_jcat_list.append(reentry["jcat"])
        duplicate_jcat_list = []
        for jsr_jcat in self.jsr_jcat_list:
            if self.jsr_jcat_list.count(jsr_jcat) > 1:
                duplicate_jcat_list.append(jsr_jcat)
        duplicate_jcat_list = sorted(list(set(duplicate_jcat_list)))
        if len(duplicate_jcat_list) > 0:
            print(f"Duplicates: {duplicate_jcat_list}")
        
        print("Looking for missing rocket stages.")
        self.add_missing_stages()                                                                                 # Add any missing stages.
        print("Searching for Aerospace Corp re-entries.")
        self.extract_aerospace_info("./Databases/Reentry/AerospaceCorp/AerospaceCorp_Reentries_14thDec23.csv")    # Load in the Aerospace Corp database. 
        print("Searching for DISCOSweb re-entries.")           
        self.extract_discosweb_info()                                                                        # Load in the DISCOSweb database.
        
        #######################
        ## Final adjustments.
        #######################
        
        mcs_dict = {}
        for launch_year in [2020,2021,2022]:
            dsl_year = xr.open_dataset(f"./Databases/launch_info_{launch_year}.nc", decode_times=False)
            for i in range(len(dsl_year["COSPAR_ID"])): 
                mcs_dict[dsl_year["COSPAR_ID"].values[i]] = dsl_year["MCS_Check"].values[i]
            dsl_year.close()
            
        for reentry in self.unique_reentry_list:
            try:
                reentry["MCS"] = mcs_dict[reentry["id"][:8]]
            except:
                if reentry["id"][:8] in ["2018-020","2019-029","2019-074"]:
                    reentry["MCS"] = True
                else:
                    reentry["MCS"] = False
        
        fairing_count_list = []
        for i in range(len(self.dsl["COSPAR_ID"])): 
             
            # Create a list of all MCS-related launches (from launch database). 
            mcs_dict[self.dsl["COSPAR_ID"].values[i]] = self.dsl["MCS_Check"].values[i]
            
            # Loop over all the fairings to check the number (should be two as it splits in half).
            # Also look for any difference in the inclination (should be zero).
            # Then set the geolocation to the location of the first fairing.  
            fairing_count = 0  
            fairing_inc = np.zeros((2))
            for count, reentry in enumerate(self.unique_reentry_list):  
                if (self.dsl["COSPAR_ID"].values[i][:8] == reentry["id"][:8] 
                and self.dsl["COSPAR_ID"].values[i][5] != "F"
                and "fairing" in reentry["name"].lower()):
                    fairing_count += 1
                    fairing_inc[fairing_count-1] = reentry["inc"]
                    if fairing_count == 1:
                        lat = reentry["lat"]
                        lon = reentry["lon"]
                    elif fairing_count == 2 and "Falcon 9" not in reentry["name"]:
                        reentry["lat"] = lat
                        reentry["lon"] = lon
            if fairing_inc[1]-fairing_inc[0] > 0:
                print(f"Warning: fairing inclinations differ for {self.dsl['COSPAR_ID'].values[i]} by {fairing_inc[1]-fairing_inc[0]}")      
            if fairing_count not in [0,2]:
                # NOTE: Apogee adjusted for 2022-150 fairing. One was 200km, one was 0km. Adjusted to make both 200km.
                sys.exit(f"Incorrect number of fairings ({fairing_count}) found for ID: {self.dsl['COSPAR_ID'].values[i]}")
            if fairing_count == 0 and self.dsl["COSPAR_ID"].values[i][5] != "F":
                pass # NOTE: If we want to manually add fairings, need to enable this to see which are missing.
                #print(f"No fairings found for {self.dsl['COSPAR_ID'].values[i]}")
            fairing_count_list.append(fairing_count)
                    
        for reentry in self.unique_reentry_list:
            for i in range(len(self.dsl["COSPAR_ID"])):
                if self.dsl["COSPAR_ID"].values[i][:8] == reentry["id"][:8]:
                    
                    # Update mass info for all rocket stages.
                    if reentry["reentry_stage"] in ["B1","B2","B3","B4","B5","B6",1,2,3,4] and self.dsl["COSPAR_ID"].values[i][5] != "F":
                        for count, rocket_name in enumerate(self.dsr["Rocket_Name"].values):
                            if rocket_name == self.dsl["Rocket_Type"].values[i]:
                                if reentry["reentry_stage"] in ["B1","B2","B3","B4","B5","B6"]:
                                    if "Atlas" in rocket_name and datetime(self.year,int(reentry["mon"]),int(reentry["day"])) >= datetime(2020,11,13):
                                        reentry["al_mass"] = 44200
                                    else:    
                                        reentry["al_mass"] = self.dsr["Booster_StageMass"].values[count] / int(self.dsr["Booster_No"].values[count])
                                elif reentry["reentry_stage"] == 1:
                                    reentry["al_mass"] = self.dsr["Stage1_StageMass"].values[count]
                                elif reentry["reentry_stage"] == 2:
                                    if datetime(self.year,int(reentry["mon"]),int(reentry["day"])) in [datetime(2021,5,18),datetime(2022,8,4)]:
                                        reentry["al_mass"] = self.dsr["Stage2_StageMass"].values[count] - 2
                                    else:
                                        reentry["al_mass"] = self.dsr["Stage2_StageMass"].values[count]
                                elif reentry["reentry_stage"] == 3:
                                    reentry["al_mass"] = self.dsr["Stage3_StageMass"].values[count]
                                elif reentry["reentry_stage"] == 4:
                                    reentry["al_mass"] = self.dsr["Stage4_StageMass"].values[count]
                    
                    # Update mass info for all fairings.
                    elif "fairing" in reentry["name"].lower() and self.dsl["COSPAR_ID"].values[i][5] != "F":
                        for count, rocket_name in enumerate(self.dsr["Rocket_Name"].values):
                            if rocket_name == self.dsl["Rocket_Type"].values[i]:
                                reentry["al_mass"] = self.dsr["Fairing_Mass"].values[count] / fairing_count_list[i]
                         
            # For West Ford dipoles, these are part of the West Ford Needles project. # https://space.skyrocket.de/doc_sdat/westford.htm
            # The needles each weigh 40 ng, and one 'clump' reentered in 2020. The needles are Copper, and so will not contribute to Al emissions.  
            if reentry["name"] in ["CZ-2C sep motor cover","CZ-4C sep motor cover?","CZ-2D sep motor cover",
                                   "CZ-2D sep motor cover"]:
                # The same item is also listed as weighing 1 kg elsewhere.
                reentry["al_mass"] = 1
            if reentry["id"] == "2020-086B": # Dest listed as 180E, this messes up other script so adjust to 179.9, will be in same grid square.
                reentry["lon"] = 179.9
            if reentry["name"] == "DLA-U": # Object 2013-009J (PSLV upper Dual Launch Adapter (DLA-U)) has this mass on DW.
                reentry["al_mass"] = 100

            # Set time to midnight whenever the reentry is occurs on a different day than the launch and no time info is available.
            # Also set to midnight if the reentry is from a launch in a previous year.
            # When the reentry is on the same day, set it to the launch time.
            if reentry["time"] == -1:  
                for count, launch_id in enumerate(self.dsl["COSPAR_ID"].values):
                    if reentry["id"][:8] == launch_id:
                        if (int(reentry["mon"]) == int(self.dsl["Month"].values[count])) and (int(reentry["day"]) == int(self.dsl["Day"].values[count])):
                            reentry["time"] = self.dsl["Time(UTC)"].values[count]
                        else:    
                            reentry["time"] = 0
                if int(reentry["id"][:4]) < self.year:
                    reentry["time"] = 0    
            if reentry["time"] == -1:
                print(f"Need to add timings for {reentry['id']} {reentry['jcat']}")
        
        self.dsl.close()
        self.dsr.close()
        self.ds_dw.close()
        
        self.print_stats()
        
    def reentry_info_to_netcdf(self):     
        """This saves the reentry information as a NetCDF file for later processing for GEOS-Chem.
        """        
        #Set up the dimensions of the netcdf file.
        dims = ('reentries')
        
        #Set up the data
        id_list, name_list, type_list, burnup_list = [], [], [], []
        stage_list, time_list,  mon_list , day_list  = [], [], [], []
        lat_list,  lon_list,  al_mass_list, non_al_mass_list = [], [], [], []
        mcs_list, manual_loc_list  = [], []
        
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
            al_mass_list.append(reentry["al_mass"])
            non_al_mass_list.append(reentry["non_al_mass"])
            mcs_list.append(reentry["MCS"])
            manual_loc_list.append(reentry["manual_loc"])    
            
        #Create the DataArrays.
        data_da_id           = xr.DataArray(id_list,          dims=dims, attrs=dict(long_name="Reentry ID"))
        data_da_name         = xr.DataArray(name_list,        dims=dims, attrs=dict(long_name="Reentry Name"))
        data_da_type         = xr.DataArray(type_list,        dims=dims, attrs=dict(long_name="Reentry Type"))
        data_da_burnup       = xr.DataArray(burnup_list,      dims=dims, attrs=dict(long_name="Reentry Burnup Flag"))
        data_da_stage        = xr.DataArray(stage_list,       dims=dims, attrs=dict(long_name="Reentry Stage"))
        data_da_time         = xr.DataArray(time_list,        dims=dims, attrs=dict(long_name="Reentry Time (UTC)"))
        data_da_mon          = xr.DataArray(mon_list,         dims=dims, attrs=dict(long_name="Reentry Month"))
        data_da_day          = xr.DataArray(day_list,         dims=dims, attrs=dict(long_name="Reentry Day"))
        data_da_lat          = xr.DataArray(lat_list,         dims=dims, attrs=dict(long_name="Reentry Latitude", units="Degrees"))
        data_da_lon          = xr.DataArray(lon_list,         dims=dims, attrs=dict(long_name="Reentry Longitude", units="Degrees"))
        data_da_al_mass      = xr.DataArray(al_mass_list,     dims=dims, attrs=dict(long_name="Reentry Al Mass", units="kg"))
        data_da_non_al_mass  = xr.DataArray(non_al_mass_list, dims=dims, attrs=dict(long_name="Reentry Non Al Mass", units="kg"))
        data_da_mcs          = xr.DataArray(mcs_list,         dims=dims, attrs=dict(long_name="Reentry MCS Check"))
        data_da_manual_loc   = xr.DataArray(manual_loc_list,  dims=dims, attrs=dict(long_name="Reentry Manual Location Check"))
    
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
        ds['RE_Al_Mass']     = data_da_al_mass
        ds['RE_Non_Al_Mass'] = data_da_non_al_mass
        ds['RE_MCS']         = data_da_mcs
        ds['RE_Manual_Loc']  = data_da_manual_loc
             
        #Save to file and close the DataSet  
        datestr = datetime.today().strftime('%Y%m%d_%H%M%S') 
        #ds.to_netcdf(f'./Databases/reentry_info_{self.year}_jcat_{datestr}.nc')
        ds.to_netcdf(f'./Databases/reentry_info_{self.year}_jcat_test.nc')
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