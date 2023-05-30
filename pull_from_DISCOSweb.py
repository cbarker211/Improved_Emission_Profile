from pprint import pprint
import requests
from datetime import datetime, timedelta
import time
import sys
import numpy as np
import xarray as xr

""" Script to request data from the DISCOSweb database. 
NB: Each request is limited to 30 results, and there is a maximum limit of requests in a certain timeframe (20 requests per 60s).
To solve this, the script makes multiple requests over different filters, and automatically calculates the time required to wait."""

#Define the URL for the data, and the authorisation token (get a new token here if needed https://discosweb.esoc.esa.int/tokens).
#This is important otherwise the program won't work!!!
api_url = 'https://discosweb.esoc.esa.int/api'
token = np.loadtxt("./Databases/DISCOSweb_token.txt", dtype=str)

class import_launches_from_discos:
    
    def __init__(self,year):
        """This function sets up the class.

        Args:
            year (_type_): _description_
        """        
        
        self.year = year

    def server_request(self,user_params,url_mod):
        """This function requests data from the API.

        Args:
            user_params (dictionary): The parameters for the request, will usually be filter and sort.
            url_mod (string): Where to request from, e.g. launches, objects, vehicles etc. 

        Returns:
            response: The response from the server (deal with errors in main function).
        """
        response = requests.get(
                #Set up the url name.
                f'{api_url}{url_mod}',
                #Set up authorization.
                headers={
                    'Authorization': f'Bearer {token}',
                    'DiscosWeb-Api-Version': '2',
                },
                #Use the user-specified parameters.
                params=user_params
            ) 
        return response

    def wait_function(self,message,wait_time):
        """This function outputs a message to the screen telling the user the wait time.

        Args:
            message (string): An additional message to print to the screen about the current process.
            wait_time (int): How many seconds are left befor emore requests can be made.
        """
        print("\n")        
        for i in range(wait_time,0,-1):
            #The 'end="\r", flush=True' means that the line will replace itself instead of printing 60 lines.
            #This is useful to clean up the terminal, but may look weird sometimes before/after waiting.
            print(f"{message}Too many requests, retrying in {str(i)}s.", end="\r", flush=True)
            time.sleep(1)
        print("\n")
            
    def response_error_handler(self,response,message):
        if response.status_code == 400:
            print("Client Error")
        elif response.status_code == 429:
            wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
            self.wait_function(message,wait_time)
        
    def get_yearly_launches(self): 
        """This function is called in all of the following functions.
        It gets the launch information for an entire year, which will be saved as self.full_launch_list

        Args:
            year (int): The year to get launches for.
        """        
        
        #Initialize variables.
        self.full_launch_list = []
        start_epoch = f'{str(self.year)}-01-01'
        end_epoch = f'{str(self.year+1)}-01-01'
        
        #This loop will run until all launches are found.
        while True:
            #Add the filtering here. Currently set up to show successful and unsuccessful launches per year.
            #The filtering params currently get all launches between start_epoch and end_epoch, sorted by epoch.
            params={
                    'filter': f"ge(epoch,epoch:'{start_epoch}')&lt(epoch,epoch:'{end_epoch}')",
                    'sort' : 'epoch'
                }
            #Now we need a while loop to deal with the rate limit. 
            #If the response is ok (code <400), then it breaks the while loop, and if not then the while loop continues after a delay.
            while True:  
                response = self.server_request(params, '/launches')
                if response.ok:
                    break
                else:
                    message = ""
                    #This line extracts information from the reponse on how long is left until more requests are allowed.
                    wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                    self.wait_function(message,wait_time)
                    continue
            
            #When the reponse is OK, the while loop breaks and the data is read from the reponse.
            #This converts the reponse to a json object.
            doc = response.json()
            #Can now extract the data from the json object.
            temp_launch_list = doc['data']
            self.full_launch_list.extend(temp_launch_list)
            
            #Each request gives a 'page' of results, and the maximum is 30 results per page.
            #There might be a way to increase the limit but I can't find it.
            #Here, we add three seconds onto the start_epoch so we don't double count when the next query starts.
            if len(temp_launch_list) == 30:
                old_start_epoch = temp_launch_list[-1]["attributes"]["epoch"][0:19]
                old_start_epoch = datetime.strptime(old_start_epoch, '%Y-%m-%dT%H:%M:%S')
                start_epoch = old_start_epoch + timedelta(0,3) # days, seconds, then other fields.
                start_epoch = start_epoch.isoformat() + "+00:00"
                continue
            else:
                break
        
        #This section simply goes through each launch and counts the numbers of successes and failures.
        #It then prints the totals to the screen. Can be switched off if not needed.    
        launch_success = 0
        launch_failure = 0
        for launch in self.full_launch_list:
            if launch["attributes"]["failure"] == True:
                launch_failure+=1
            elif launch["attributes"]["failure"] == False:
                launch_success+=1
            else:
                print("Error: Launch not recorded as success or failure.")         
        print(f'\nIn {self.year}, there were {launch_success} successful launches and {launch_failure} unsuccessful launches.')

        return self.full_launch_list
        
    def payloads_launched_per_year(self): 
        """This function calculates and outputs the number of payloads 
        launched each year.

        Args:
            year (int): The year to look at.
            
        Returns:
            self.num_payloads : The number of payloads.
        """        
        full_launch_list = self.get_yearly_launches()
        self.num_payloads = 0
        
        #Loop over all launches.
        for launch in full_launch_list:
            full_object_list = []
            #Filter only the successful launches (can change if required)
            if launch["attributes"]["failure"] == False:
                
                #The params select only the objects listed as 'payload', and sort by id.
                #You can change the params to also collect information about other objectClasses.
                params={
                        'filter' : "eq(objectClass,Payload)",
                        'sort' : 'id'         
                    }
                
                #Same routine as get_yearly_launches function, but now splits into specific error codes.
                while True:
                    #Now requiring a response from the objects url.
                    response = self.server_request(params,f'/launches/{launch["id"]}/objects')
                    
                    #If the request is successful, go through and sum the payloads.
                    if response.ok:
                        doc = response.json()
                        temp_object_list = doc['data']
                        full_object_list.extend(temp_object_list)
                        
                        #This section gets around the 30 requests per page limit.
                        #It assigns the final (30th) object id in the page to a variable.
                        #Then the params are set so that another request is made starting from the next object id. 
                        if len(temp_object_list) > 0:
                            final_object_id = str(int(temp_object_list[-1]["id"]) + 1)
                        if len(temp_object_list) == 30:
                            params={ 
                                    'filter' : f"eq(objectClass,Payload)&ge(id,{final_object_id})",
                                    'sort' : 'id'         
                                }
                            continue
                        break
                    
                    #This response usually means the params have incorrect syntax.
                    elif response.status_code == 400:
                        print("Client Error")
                        break
                    
                    #This response means that the number of requests has been reached in the 60s limit.
                    #It will then state how many payloads have been found and output the result while the timer counts down.
                    elif response.status_code == 429:
                        message = f"Currently found {self.num_payloads} payloads. "
                        wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                        self.wait_function(message,wait_time)
                        continue
                    
                self.num_payloads += len(full_object_list)
        
        #Print results.
        print(f'\nIn {self.year}, there were {self.num_payloads} payloads successfully launched.')   
        
        return self.num_payloads 

    def propellant_per_year(self):
        """Sums the propellant masses for a given year, split into fuel, oxidiser, and solid.

        Returns:
            fuel_mass,oxidiser_mass,solid_mass,total_mass: Masses of each propellant component.
        """        
        
        # Start similar to the payloads function by pulling the data for all successful launches.
        full_launch_list = self.get_yearly_launches()
        oxidiser_mass = np.float32(0)
        fuel_mass = np.float32(0)
        solid_mass = np.float32(0)
        total_mass = np.float32(0)
        
        #For only testing first five launches
        #self.full_launch_list = self.full_launch_list[:5]
        
        for count, launch in enumerate(full_launch_list):
            #First filter only the successful launches.
            if launch["attributes"]["failure"] == False:
                #First identify the vehicle, and account for errors in same way as before.
                while True:
                    response = self.server_request({},f'/launches/{launch["id"]}/vehicle')
                    if response.ok:
                        doc = response.json()
                        launch_info = doc['data']
                        #Then loop over all stages
                        while True:
                            response = self.server_request({},f'/launch-vehicles/{launch_info["id"]}/stages')
                            if response.ok:
                                doc = response.json()
                                vehicle_info = doc['data']
                                # Usually 2-5 stages, so won't need to account for the maximum of 30 items in a list.
                                #Now go over each stage and request the masses of fuel, oxidiser, and solid propellant.
                                for stage in vehicle_info:
                                    
                                    temp_fuel_mass = stage["attributes"]["fuelMass"]
                                    if temp_fuel_mass == None:
                                        temp_fuel_mass = 0
                                    fuel_mass += temp_fuel_mass
                                    
                                    temp_oxidiser_mass = stage["attributes"]["oxidiserMass"]
                                    if temp_oxidiser_mass == None:
                                        temp_oxidiser_mass = 0
                                    oxidiser_mass += temp_oxidiser_mass
                                    
                                    temp_solid_mass = stage["attributes"]["solidPropellantMass"]
                                    if temp_solid_mass == None:
                                        temp_solid_mass = 0
                                    solid_mass += temp_solid_mass
                                    
                                    #Calculate the total mass.
                                    total_mass = fuel_mass + solid_mass + oxidiser_mass
                                break
                            elif response.status_code == 400:
                                print("Client Error")
                                break
                            elif response.status_code == 429:
                                message = f"On launch {count} of {len(full_launch_list)} in {self.year}. Currently found {total_mass} kg of propellant. "
                                wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                                self.wait_function(message,wait_time)
                                continue
                        break
                    elif response.status_code == 400:
                        print("Client Error")
                        break
                    elif response.status_code == 429:
                        message = f"On launch {count} of {len(full_launch_list)} in {self.year}. Currently found {total_mass} kg of propellant. "
                        wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                        self.wait_function(message,wait_time)
                        continue 
        
        return fuel_mass,oxidiser_mass,solid_mass,total_mass

    def get_launch_info(self):
        """This function gathers all of the required launch information that HEMCO needs.

        Returns:
            launch_info: A list of all of the extracted launch information for the year.
        """        
        self.get_yearly_launches()
                
        self.Cospar_Id = []
        self.launch_time = []
        self.launch_day = []
        self.launch_month = []
        self.latitude = []
        self.longitude = []
        self.site_name = []
        self.rocket_type = []
        self.vehicle_id = []
        
        #self.full_launch_list = self.full_launch_list[:6]
        for count, launch in enumerate(self.full_launch_list):
            
            self.Cospar_Id.append(launch["attributes"]["cosparLaunchNo"])
            temp_launch_epoch = launch["attributes"]["epoch"]
            self.launch_day.append(np.float64(temp_launch_epoch[8:10]))
            self.launch_month.append(np.float64(temp_launch_epoch[5:7]))
            
            temp_launch_time = temp_launch_epoch[10:]
            hour = int(temp_launch_time[1:3])
            minute = int(temp_launch_time[4:6])
            sec = int(temp_launch_time[7:9])
            time_utc = np.float64(hour + minute / 60 + sec / 3600)
            self.launch_time.append(time_utc)

            # Get the launch site info.
            while True:
                response = self.server_request({},f'/launches/{launch["id"]}/site')
                if response.ok:
                    doc = response.json()
                    self.latitude.append(np.float64(doc['data']["attributes"]["latitude"]))
                    self.longitude.append(np.float64(doc['data']["attributes"]["longitude"]))
                    temp_site_name = doc['data']["attributes"]["name"]
                    self.site_name.append(temp_site_name.replace(",",""))
                    break
                elif response.status_code == 429:
                    message = f"On launch {count} of {len(self.full_launch_list)} in {self.year}."
                    self.response_error_handler(response,message)
                    continue
                else:
                    self.response_error_handler(response,"")
                break
                
            # Get the vehicle info.
            while True:
                response = self.server_request({},f'/launches/{launch["id"]}/vehicle')
                if response.ok:
                    doc = response.json()
                    self.rocket_type.append(doc['data']["attributes"]["name"])
                    self.vehicle_id.append(int(doc["data"]["id"]))
                elif response.status_code == 429:
                    message = f"On launch {count} of {len(self.full_launch_list)} in {self.year}."
                    self.response_error_handler(response,message)
                    continue
                else:
                    self.response_error_handler(response,"")
                break
                    
        return [self.Cospar_Id, self.launch_time, self.launch_day, self.launch_month, self.latitude, self.longitude, self.site_name, self.rocket_type]
            
    def launch_info_to_netcdf(self):
        """This saves the launch information as a NetCDF file for later processing for GEOS-Chem.
        This is only needed if using GEOS-Chem. Recommended to ignore if you don't need this.
        """        
        
        #Set up the dimensions of the netcdf file.
        #launches = np.arange(len(self.Cospar_Id), dtype=np.int64)
        dims = ('launches')
    
        #Create the DataArrays (The data is currently lists instead of numpy arrays, I guess this is fine?)
        data_da_cospar_id = xr.DataArray(self.Cospar_Id, dims=dims,
            attrs=dict(long_name="COSPAR ID",
                       short_name="COSPAR ID"))
        
        data_da_time = xr.DataArray(self.launch_time, dims=dims,
            attrs=dict(long_name="Time (UTC)",
                       short_name="Time (UTC)",
                       ))
        
        data_da_month = xr.DataArray(self.launch_month, dims=dims,
            attrs=dict(long_name="Month",
                       short_name="Month",
                       ))
        
        data_da_day = xr.DataArray(self.launch_day, dims=dims,
            attrs=dict(long_name="Day",
                       short_name="Day",
                       ))
        
        data_da_lon = xr.DataArray(self.longitude, dims=dims,
            attrs=dict(long_name="Longitude",
                       short_name="Longitude",
                       units="Degrees"))
        
        data_da_lat = xr.DataArray(self.latitude, dims=dims,
            attrs=dict(long_name="Latitude",
                       short_name="Latitude",
                       units="Degrees"))
        
        data_da_launch_site = xr.DataArray(self.site_name, dims=dims,
            attrs=dict(long_name="Launch Site",
                       short_name="Launch Site",
                       ))
        
        data_da_rocket_type = xr.DataArray(self.rocket_type, dims=dims,
            attrs=dict(long_name="Rocket Type",
                       short_name="Rocket Type",
                       ))
        
        data_da_vehicle_id = xr.DataArray(self.vehicle_id, dims=dims,
            attrs=dict(long_name="Vehicle ID",
                       short_name="Vehicle ID",
                       ))
        
        # Create an xarray Dataset from the DataArrays.
        ds = xr.Dataset()
        ds['COSPAR_ID'] = data_da_cospar_id
        ds['Time(UTC)'] = data_da_time
        ds['Month'] = data_da_month
        ds['Day'] = data_da_day
        ds['Longitude'] = data_da_lon
        ds['Latitude'] = data_da_lat
        ds['Launch_Site'] = data_da_launch_site
        ds['Rocket_Type'] = data_da_rocket_type
        ds['Vehicle_ID'] = data_da_vehicle_id
             
        #Save to file and close the DataSet     
        ds.to_netcdf(f'./Databases/launch_info_{year}.nc')
        ds.close()
        
    def handle_propellant_info(self, count, stage, i, temp_dict, unique_vehicle_name_list):
        
        #print(unique_vehicle_name_list[i])
        #If the boosters and stages are not in the right order on DISCOSweb, then manually rearrage.
        if unique_vehicle_name_list[i] in ["Angara A5", "Ariane 5ECA", "Atlas V 411", "Atlas V 531", "Atlas V 541", "Atlas V 551", 
                                           "Delta 4H", "H-IIA 202", "H-IIB", "PSLV-DL", "PSLV-XL", 
                                           "Long March (CZ) 11", "Long March (CZ) 2F", "Long March (CZ) 3B", "Long March (CZ) 5", 
                                           "Long March (CZ) 5B", "Long March (CZ) 6", "Long March (CZ) 7A", "Long March (CZ) 8",
                                           "Soyuz-2-1A", "Soyuz-2-1A Fregat-M", "Soyuz-2-1B Fregat", "Soyuz-2-1B Fregat-M", "Soyuz-ST-A Fregat-M"]:
            
            #print("Manually assigning propellant information.")
            stage_name = stage["attributes"]["name"]
            
            if stage_name in ["URM-1 Boosters", "EPS P241", "Atlas V 1 Boosters", "Atlas V 3 Boosters", "Atlas V Booster",
                              "Delta IV CBC Boosters", "H-II SRB-A", "PSOM-XL Boosters", "Soyuz-FG Blok-B,V,G,D",
                              "Booster LB-41 (YF25)", "Booster LB-38 (YF25)", "K2-1"]:
                stage_number = "Booster"
                
            elif (stage_name in ["URM-1","EPC H173", "Atlas V CCB", "H-II LE-7A", "H-II widebody LE-7A", "PS1", "Soyuz-FG Blok-A",
                                 "Long March (CZ) 11 Stage 1", "L-186 (YF21B)", "L-172 (YF21C)", "CZ-5-500", "L-165 (H5-1)", "L-76 (YF100)",
                                 ]) or stage["id"] == "775":
                stage_number = "Stage1"
                
            elif (stage_name in ["URM-2","ESC-A","Centaur-5 SEC", "H-II LE-5B", "PS2", "Blok-I", "Long March (CZ) 11 Stage 2", 
                                 "L-84 (YF26) (Long March (CZ) 2F)", "L-45 (YF-24E)", "CZ-5-HO", "L-15 (YF115)", "K3-2 short"]) or stage["id"] == "773":
                stage_number = "Stage2"
                
            elif stage_name in ["Briz-M", "PS3", "Fregat-M", "Fregat", "Long March (CZ) 11 Stage 3", "PBV"]:
                stage_number = "Stage3"
                
            elif stage_name in ["PSLV fourth stage (PS4)", "Long March (CZ) 11 Stage 4"]:
                stage_number = "Stage4"
                
            elif stage_name == "H-18 (Long March (CZ) YF)":
                if unique_vehicle_name_list[i] in ["Long March (CZ) 3B", "Long March (CZ) 7A"]:
                    stage_number = "Stage3"
                elif unique_vehicle_name_list[i] == "Long March (CZ) 8":
                    stage_number = "Stage2"

            elif stage_name == "K3-1":
                if unique_vehicle_name_list[i] in ["Long March (CZ) 5", "Long March (CZ) 5B"]:
                    stage_number = "Booster"
                elif unique_vehicle_name_list[i] in ["Long March (CZ) 8", "Long March (CZ) 7A"]:
                    stage_number = "Stage1"
                    
            else:
                sys.exit(f"Warning: Error manually assigning stages and boosters. Stage {stage_name} not in check lists.")
        else:
            #print("Automatically assigning propellant information.")
            stage_number = f"Stage{count+1}"

        #Now add the propellant mass together.
        temp_fuel_mass = stage["attributes"]["fuelMass"]
        if temp_fuel_mass == None:
            temp_fuel_mass = 0
        temp_oxidiser_mass = stage["attributes"]["oxidiserMass"]
        if temp_oxidiser_mass == None:
            temp_oxidiser_mass = 0
        temp_solid_mass = stage["attributes"]["solidPropellantMass"]
        if temp_solid_mass == None:
            temp_solid_mass = 0
        
        temp_prop_mass = temp_fuel_mass+temp_oxidiser_mass+temp_solid_mass
        if temp_prop_mass == 0:
            print(f"Warning: No propellant mass found for {stage_number} of {unique_vehicle_name_list[i]}")
        
        # Finally get the propellant name and assign type.
        while True:
            response = self.server_request({},f'/launch-vehicles/stages/{stage["id"]}/propellant')
            if response.ok:
                doc = response.json()
                if doc['data'] != None:
                    propellant_info = doc['data']["attributes"]
                    
                    #First get the name.
                    if (propellant_info["fuel"] != None) and (propellant_info["oxidiser"] != None):
                        temp_dict[f"{stage_number} Propellant Name"] = propellant_info["fuel"] + "/" + propellant_info["oxidiser"]
                    elif propellant_info["solidPropellant"] != None:
                        temp_dict[f"{stage_number} Propellant Name"] = propellant_info["solidPropellant"]
                        #The else case is handled below in the next else block.
                        
                    # Fix minor spelling errors from database.
                    if stage["attributes"]["name"] == "Antares-200 first stage (RD-181)":
                        temp_dict[f"Stage1 Propellant Name"] = "RP1 (Rocket Propellant 1)/LOX"
                    
                    if stage["attributes"]["name"] == "AVUM":
                        temp_dict[f"Stage4 Propellant Name"] = "UDMH (Unsymmetrical Dimethyl Hydrazine)/N2O4"
                    
                    #Now assign to a fuel type.
                    if temp_dict[f"{stage_number} Propellant Name"] in ['HTPB','Solid','HTPB-1912','TP-H8299']:
                        temp_dict[f"{stage_number} Fuel Type"] = "Solid"  
                    elif temp_dict[f"{stage_number} Propellant Name"] in ['RP1 (Rocket Propellant 1)/LOX','Kerosene/LOX']:
                        temp_dict[f"{stage_number} Fuel Type"] = "Kerosene"  
                    elif temp_dict[f"{stage_number} Propellant Name"] in ['UDMH (Unsymmetrical Dimethyl Hydrazine)/N2O4','UDMH (Unsymmetrical Dimethyl Hydrazine)/AK27',
                                                                          'MMH (Monomethyl Hydrazine)/N2O4','MMH (Monomethyl Hydrazine)/MON']:
                        temp_dict[f"{stage_number} Fuel Type"] = "Hypergolic"  
                    elif temp_dict[f"{stage_number} Propellant Name"] in ['LH2 (Liquid Hydrogen)/LOX']:
                        temp_dict[f"{stage_number} Fuel Type"] = "Hydrogen"  
                    else:
                        print(f"Warning: Couldn't assign propellant <{temp_dict[f'{stage_number} Propellant Name']}> for {stage_number} of {unique_vehicle_name_list[i]}.")     
                else:
                    print(f"Warning: Couldn't find any propellant for {stage_number} of {unique_vehicle_name_list[i]}.")
                    
            elif response.status_code == 429:
                message = f"On launch {i+1} of {len(unique_vehicle_name_list)} in {self.year}."
                self.response_error_handler(response,message)
                continue
            else:
                self.response_error_handler(response,"")
            break
        
        temp_dict[f"{stage_number} Propellant Mass"] = temp_prop_mass
        
        #pprint(temp_dict)
        return temp_dict
    
    def get_rocket_info(self):
        
        self.unique_rocket_list = []
        
        #Open file and get a list of unique vehicles.
        ds = xr.open_dataset('Databases/launch_info_2020.nc', decode_times=False)
        vehicle_name_list = ds['Rocket_Type'].values
        vehicle_id_list = ds['Vehicle_ID'].values
        unique_vehicle_name_list = sorted(list(set(vehicle_name_list)))
        ds.close()
            
        #Loop over all rockets, and pull the information for each.
        # There is currently missing propellant information for the following rockets (12/44):
        #       Astra Rocket 3 (Stage 1-2, no prop mass)
        #       Ceres-1 (Stage 1-4, no prop mass or type)
        #       Chang'e 5 SSQ (Ascent Stage) (Stage 1, no prop mass or type)
        #       Electron (Curie) (Stage 1-3, no prop mass or type)
        #       Kuaizhou-1 (Stage 4, no prop mass)
        #       Kuaizhou-11 (Stage 1-3, no prop mass or type)
        #       LauncherOne (Stage 1-2, no prop mass)
        #       Long March (CZ) 11 (Stage 1-4, no prop mass or type)
        #       Long March (CZ) 6 (Stage 3 PBV?, no prop mass)
        #       Minotaur-4 (Stage 1-3, no prop mass or type)
        #       Qased (Stage 1-3, no prop mass or type)
        #       Shavit (Stage 1-3, no prop mass or type)
        #       Simorgh (Stage 1-3, no prop mass or type)
        
        # The todo-list for handling incomplete information is later in this function.
        
        #unique_vehicle_name_list = unique_vehicle_name_list[29:31]
        for i in range(0,len(unique_vehicle_name_list)):
            
            temp_vehicle_id = vehicle_id_list[np.where(vehicle_name_list == unique_vehicle_name_list[i])[0][0]]
            temp_dict = {
                "id" : temp_vehicle_id,
                "name": unique_vehicle_name_list[i],
            }

            #print(temp_dict)                    
            # Get the propellant mass info.
            while True:
                response = self.server_request({},f'/launch-vehicles/{temp_vehicle_id}/stages')

                if response.ok:
                    doc = response.json()
                    vehicle_info = doc['data']
                    # Usually 2-5 stages, so won't need to account for the maximum of 30 items in a list.
                    run_func = True
                    if run_func == True:
                        temp_dict[f"Booster Propellant Mass"] = 0
                        temp_dict[f"Booster Fuel Type"] = ""
                        temp_dict[f"Booster Propellant Name"] = ""
                        for j in range(0,4):
                            temp_dict[f"Stage{j+1} Propellant Mass"] = 0
                            temp_dict[f"Stage{j+1} Fuel Type"] = ""
                            temp_dict[f"Stage{j+1} Propellant Name"] = ""
                            
                        for count,stage in enumerate(vehicle_info):
                            temp_dict = self.handle_propellant_info(count,stage,i,temp_dict,unique_vehicle_name_list)
                        #pprint(temp_dict) 
                                               
                elif response.status_code == 429:
                    message = f"On launch {i+1} of {len(unique_vehicle_name_list)} in {self.year}."
                    self.response_error_handler(response,message)
                    continue
                else:
                    self.response_error_handler(response,"")
                break      
            
            ####################################
            # Handle any imcomplete information.
            ####################################
            
            # 3 launches in 2020.
            # First not included in databases, fire destroyed rocket on launch pad.
            # Second launch, engines shut down by safety officer after 30s.
            # Third launch, rocket passed Karman line and reached orbital altitude, but didn't reach stable orbit.
            # TODO: Find Astra propellant mass.
            # First stage powered by 5 Delphin engines.
            # Second stage powered by 1 Aether engine.
            if unique_vehicle_name_list[i] == "Astra Rocket 3":
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                
            #Interent search seems to agree that upper stage is 'liquid-propellant', but no info.
            # Will assume hypergolic, as some sources suggest hydrazine.
            # https://www.nasaspaceflight.com/2021/12/chinas-galactic-energy-launches-second-ceres-1-rocket-successfully/
            # TODO: Find Ceres-1 propellant mass.
            if unique_vehicle_name_list[i] == "Ceres-1":
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage4 Fuel Type"] = "Hypergolic"
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                temp_dict[f"Stage3 Propellant Mass"] = 0
                temp_dict[f"Stage4 Propellant Mass"] = 0
            
            # "Chang'e 5 SSQ (Ascent Stage)" refers to the Chinese lunar exploration mission.
            # Specifically, the 'ascender' launching from the moon to dock with the 'orbiter'.
            # It eventually was 'crashed' back onto the moon to avoid space debris, so didn't re-enter. 
            
            # Electron (Curie) - 6 successes and one failure.
            # https://www.rocketlabusa.com/assets/Uploads/Electron-Payload-User-Guide-7.0.pdf
            # 3rd stage is 'kick-stage', and has a 'liquid bi-propellant' which wikipedia says is hypergolic.
            # Both 1st and 2nd stages use Rutherford engines, kick-stage uses Curie engine.
            # TODO: Find Electron propellant mass.
            if unique_vehicle_name_list[i] == "Electron (Curie)":
                temp_dict[f"Stage1 Propellant Name"] = 'Kerosene/LOX'
                temp_dict[f"Stage2 Propellant Name"] = 'Kerosene/LOX'
                temp_dict[f"Stage3 Propellant Name"] = 'Liquid bi-propellant'
                temp_dict[f"Stage1 Fuel Type"] = "Kerosene"
                temp_dict[f"Stage2 Fuel Type"] = "Kerosene"
                temp_dict[f"Stage3 Fuel Type"] = "Hypergolic"
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 2000
                temp_dict[f"Stage3 Propellant Mass"] = 0
            
            # Kuaizhou-1 - 2 successes and 1 failure.
            # https://www.nasaspaceflight.com/2014/11/china-launches-kuaizhou-2-second-launch-24-hours/ 'liquid upper stage'
            # Both successes were LEO launches of satellites. Both failures were SSO launches of satellites. 
            # Failed launch failed after liftoff, so still include. However, only missing info is 4th stage propellant mass.
            # Therefore ignore for now as we probably won't include 4th Stage emissions.             
            
            # Kuaizhou-11 (Stage 1-3, no prop mass or type)
            # Larger version of Kuaizhou-1.
            # First stage appeared to work correctly https://spaceflightnow.com/2020/07/10/new-chinese-satellite-launcher-fails-on-first-flight/
            # TODO: Find Kuaizhou-11 propellant mass.
            if unique_vehicle_name_list[i] == "Kuaizhou-11":
                temp_dict[f"Stage1 Propellant Name"] = 'Solid'
                temp_dict[f"Stage2 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                temp_dict[f"Stage3 Propellant Mass"] = 0
            
            # LauncherOne (Stage 1-2, no prop mass)
            # https://spaceflightnow.com/2020/05/25/virgin-orbits-air-launched-rocket-fails-on-first-test-flight/
            # Failed after ignition of 1st stage, so probably should include something.
            # TODO: Find LauncherOne propellant mass.
            if unique_vehicle_name_list[i] == "LauncherOne":
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                
            # Long March (CZ) 6
            # DISCOSweb lists third stage as 'PBV' with LH2/LOX propellant.
            # Wikipedia lists third stage as N2O4/UDMH propellant.
            # Gunter's Space Page lists third stage as Kerosene/Hydrogen peroxide.
            # https://space.skyrocket.de/doc_lau/cz-6.htm
            # Ignore for now as we probably won't include 3rd Stage emissions.
            
            # Long March (CZ) 11.
            # Likely based on DF-31 missile, may have to use and total mass to guess propellant mass.
            # https://space.skyrocket.de/doc_lau/cz-11.htm 
            if unique_vehicle_name_list[i] == "Long March (CZ) 11":
                temp_dict[f"Stage1 Propellant Name"] = 'Solid'
                temp_dict[f"Stage2 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage4 Propellant Name"] = 'Solid'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage4 Fuel Type"] = 'Solid'
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                temp_dict[f"Stage3 Propellant Mass"] = 0
                temp_dict[f"Stage4 Propellant Mass"] = 0
            
            # Minotaur-4
            # Based on LGM-118 Peacekeeper ICBM.
            # https://en.wikipedia.org/wiki/Minotaur_IV#STP-S26 
            # TODO: Find Minotaur-4 propellant mass.
            if unique_vehicle_name_list[i] == "Minotaur-4":
                temp_dict[f"Stage1 Propellant Name"] = 'Solid'
                temp_dict[f"Stage2 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                temp_dict[f"Stage3 Propellant Mass"] = 0
                temp_dict[f"Stage4 Propellant Mass"] = 0           
                
            # Qased
            # https://en.wikipedia.org/wiki/Qased_(rocket)
            # First stage uses UDMH/N2O4, second is 'solid fueled'.
            # First stage says oxidiser is AK27 on DISCOSweb.
            # Third stage is mysterious.
            # TODO: Find Qased propellant mass.
            if unique_vehicle_name_list[i] == "Qased":
                temp_dict[f"Stage1 Propellant Name"] = 'UDMH (Unsymmetrical Dimethyl Hydrazine)/N2O4'
                temp_dict[f"Stage2 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                temp_dict[f"Stage3 Propellant Mass"] = 0
            
            # Shavit (Stage 1-3, no prop mass or type)
            # The rocket launched in 2020 seems to be the RSA-3 vehicle.
            # This was the South African licensed version, so I will assume the details are same as for Shavit-2.
            # TODO: Find Shavit propellant mass.
            if unique_vehicle_name_list[i] == "Shavit":
                temp_dict[f"Stage1 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage2 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage3 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                temp_dict[f"Stage3 Propellant Mass"] = 0
                
            # Simorgh
            # Wiki: Simorgh operated for 475 seconds. 
            # Satellite reached speed of 6,500 m/s out of the 7,400 m/s required to orbit. 
            # First stage operated fully correctly.
            # Second stage failed in latests second of the flight.
            # Saman-1 is an upper-stage, used as a space tug to transfer satellites to higher orbits.
            # TODO: Find Simorgh propellant mass.
            if unique_vehicle_name_list[i] == "Simorgh":
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 0
                temp_dict[f"Stage2 Propellant Mass"] = 0
                temp_dict[f"Stage3 Propellant Mass"] = 185 # https://en.wikipedia.org/wiki/Saman-1_(rocket_stage)
            
            self.unique_rocket_list.append(temp_dict)    
        
    def rocket_info_to_netcdf(self):
        """This saves the propellant information as a NetCDF file for later processing for GEOS-Chem.
        This is only needed if using GEOS-Chem. Recommended to ignore if you don't need this.
        """        
        #Set up the dimensions of the netcdf file.
        #launches = np.arange(len(self.Cospar_Id), dtype=np.int64)
        dims = ('rockets')
        
        #Set up the data
        rocket_name_list = []
        booster_propmass_list, booster_fuel_type_list, booster_propname_list = [], [], []
        stage1_propmass_list, stage1_fuel_type_list, stage1_propname_list = [], [], []
        stage2_propmass_list, stage2_fuel_type_list, stage2_propname_list = [], [], []
        stage3_propmass_list, stage3_fuel_type_list, stage3_propname_list = [], [], []
        stage4_propmass_list, stage4_fuel_type_list, stage4_propname_list = [], [], []

        for rocket in self.unique_rocket_list:
            rocket_name_list.append(rocket["name"])
            booster_propmass_list.append(rocket["Booster Propellant Mass"])
            booster_fuel_type_list.append(rocket["Booster Fuel Type"])
            booster_propname_list.append(rocket["Booster Propellant Name"])
            stage1_propmass_list.append(rocket["Stage1 Propellant Mass"])
            stage1_fuel_type_list.append(rocket["Stage1 Fuel Type"])
            stage1_propname_list.append(rocket["Stage1 Propellant Name"])
            stage2_propmass_list.append(rocket["Stage2 Propellant Mass"])
            stage2_fuel_type_list.append(rocket["Stage2 Fuel Type"])
            stage2_propname_list.append(rocket["Stage2 Propellant Name"])
            stage3_propmass_list.append(rocket["Stage3 Propellant Mass"])
            stage3_fuel_type_list.append(rocket["Stage3 Fuel Type"])
            stage3_propname_list.append(rocket["Stage3 Propellant Name"])
            stage4_propmass_list.append(rocket["Stage4 Propellant Mass"])
            stage4_fuel_type_list.append(rocket["Stage4 Fuel Type"])
            stage4_propname_list.append(rocket["Stage4 Propellant Name"])
            
        #Create the DataArrays.
        data_da_name                = xr.DataArray(rocket_name_list,     dims=dims, attrs=dict(long_name="Rocket Name"))
        data_da_booster_propmass    = xr.DataArray(booster_propmass_list, dims=dims, attrs=dict(long_name="Booster Propellant Mass", units="kg"))
        data_da_booster_fuel_type   = xr.DataArray(booster_fuel_type_list,    dims=dims, attrs=dict(long_name="Booster Fuel Type"))
        data_da_booster_propname    = xr.DataArray(booster_propname_list, dims=dims, attrs=dict(long_name="Booster Propellant Name"))
        data_da_stage1_propmass     = xr.DataArray(stage1_propmass_list, dims=dims, attrs=dict(long_name="Stage 1 Propellant Mass", units="kg"))
        data_da_stage1_fuel_type    = xr.DataArray(stage1_fuel_type_list,    dims=dims, attrs=dict(long_name="Stage 1 Fuel Type"))
        data_da_stage1_propname     = xr.DataArray(stage1_propname_list, dims=dims, attrs=dict(long_name="Stage 1 Propellant Name"))
        data_da_stage2_propmass     = xr.DataArray(stage2_propmass_list, dims=dims, attrs=dict(long_name="Stage 2 Propellant Mass", units="kg"))
        data_da_stage2_fuel_type    = xr.DataArray(stage2_fuel_type_list,    dims=dims, attrs=dict(long_name="Stage 2 Fuel Type"))
        data_da_stage2_propname     = xr.DataArray(stage2_propname_list, dims=dims, attrs=dict(long_name="Stage 2 Propellant Name"))
        data_da_stage3_propmass     = xr.DataArray(stage3_propmass_list, dims=dims, attrs=dict(long_name="Stage 3 Propellant Mass", units="kg"))
        data_da_stage3_fuel_type    = xr.DataArray(stage3_fuel_type_list,    dims=dims, attrs=dict(long_name="Stage 3 Fuel Type"))
        data_da_stage3_propname     = xr.DataArray(stage3_propname_list, dims=dims, attrs=dict(long_name="Stage 3 Propellant Name"))
        data_da_stage4_propmass     = xr.DataArray(stage4_propmass_list, dims=dims, attrs=dict(long_name="Stage 4 Propellant Mass", units="kg"))
        data_da_stage4_fuel_type    = xr.DataArray(stage4_fuel_type_list,    dims=dims, attrs=dict(long_name="Stage 4 Fuel Type"))
        data_da_stage4_propname     = xr.DataArray(stage4_propname_list, dims=dims, attrs=dict(long_name="Stage 4 Propellant Name"))
        
        
        # Create an xarray Dataset from the DataArrays.
        ds = xr.Dataset()
        ds['Rocket_Name']           = data_da_name
        ds['Booster_PropMass']      = data_da_booster_propmass
        ds['Booster_Fuel_Type']     = data_da_booster_fuel_type
        ds['Booster_PropName']      = data_da_booster_propname
        ds['Stage1_PropMass']       = data_da_stage1_propmass
        ds['Stage1_Fuel_Type']      = data_da_stage1_fuel_type
        ds['Stage1_PropName']       = data_da_stage1_propname
        ds['Stage2_PropMass']       = data_da_stage2_propmass
        ds['Stage2_Fuel_Type']      = data_da_stage2_fuel_type
        ds['Stage2_PropName']       = data_da_stage2_propname
        ds['Stage3_PropMass']       = data_da_stage3_propmass
        ds['Stage3_Fuel_Type']      = data_da_stage3_fuel_type
        ds['Stage3_PropName']       = data_da_stage3_propname
        ds['Stage4_PropMass']       = data_da_stage4_propmass
        ds['Stage4_Fuel_Type']      = data_da_stage4_fuel_type
        ds['Stage4_PropName']       = data_da_stage4_propname

             
        #Save to file and close the DataSet     
        ds.to_netcdf(f'./Databases/rocket_info_{year}.nc')
        ds.close()
                
if __name__ == "__main__":
    """The main running of the program goes here. 
    All of the functions are inside the import_launches_from_discos class.
    Call each of the functions using import_launches_from_discos._function_
    e.g. import_launches_from_discos.launches_per_year(start_year,end_year)
    """         
    
    #Set up the year and filename.
    year = 2020
    
    #Create an instance of the class.
    LaunchData = import_launches_from_discos(year)
    
    #Now we can run class functions. E.g. launch_list = LaunchData.get_yearly_launches()
    #LaunchData.get_launch_info()
    #LaunchData.launch_info_to_netcdf()
    LaunchData.get_rocket_info()
    LaunchData.rocket_info_to_netcdf()
    
    #OPTIONAL: Save results to file.
    #with open(filename, 'a') as f:
    #   f.write(f'{self.Cospar_Id[count]},{self.launch_time[count]},{self.launch_day[count]},{self.launch_month[count]},{self.latitude[count]},{self.longitude[count]},{self.site_name[count]},{self.rocket_type[count]},\n')
    #   f.write(f'{year},{fuel_mass},{oxidiser_mass},{solid_mass},{total_mass}\n')
    #   f.write(f'In {year}, there were {num_payloads} payloads successfully launched.\n')   
    