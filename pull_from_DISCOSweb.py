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
        self.mcs_check = []
        
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
            
            # Look for any payloads with the name 'Starlink' or 'Oneweb', and denote them as MCS.
            params={
                    'filter' : "(eq(objectClass,Payload))&(or(contains(name,Starlink),contains(name,OneWeb)))",
                    'sort' : 'id'         
                }
            while True:
                response = self.server_request(params,f'/launches/{launch["id"]}/objects')
                if response.ok:
                    doc = response.json()
                    temp_object_list = doc['data']
                    if len(temp_object_list) > 0:
                        self.mcs_check.append(True)
                        print(f"{int(self.launch_day[-1])}/{int(self.launch_month[-1])}")  
                    else:
                        self.mcs_check.append(False)   
                elif response.status_code == 429:
                    message = f"On launch {count} of {len(self.full_launch_list)} in {self.year}."
                    self.response_error_handler(response,message)
                    continue
                else:
                    self.response_error_handler(response,"")
                break
            
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
                    #print(doc['data']["attributes"]["name"])
                    self.vehicle_id.append(int(doc["data"]["id"]))
                elif response.status_code == 429:
                    message = f"On launch {count} of {len(self.full_launch_list)} in {self.year}."
                    self.response_error_handler(response,message)
                    continue
                else:
                    self.response_error_handler(response,"")
                break
                    
        return [self.Cospar_Id, self.launch_time, self.launch_day, self.launch_month, self.latitude, self.longitude, self.site_name, self.rocket_type, self.mcs_check]
            
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
        
        data_da_launch_MCS = xr.DataArray(self.mcs_check, dims=dims,
            attrs=dict(long_name="MCS Launch Check",
                       short_name="MCS Launch Check",
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
        ds['MCS_Check'] = data_da_launch_MCS
             
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
                    
                    if (propellant_info["fuel"] != None) and (propellant_info["oxidiser"] != None) and (propellant_info["solidPropellant"] != None):
                        print("HYBRID ROCKET DETECTED")
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
                    # TODO: Can the fuel types be more finely categorized?
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
                message = f"On rocket {i+1} of {len(unique_vehicle_name_list)} in {self.year}."
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
        
        #unique_vehicle_name_list = unique_vehicle_name_list[0:5]
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
                        #Set up the arrays
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
                    message = f"On rocket {i+1} of {len(unique_vehicle_name_list)} in {self.year}."
                    self.response_error_handler(response,message)
                    continue
                else:
                    self.response_error_handler(response,"")
                break      
            
            ##############################################
            # Handle any incomplete/incorrect information.
            ##############################################
            
            if unique_vehicle_name_list[i] == "Atlas V 411":
                temp_dict[f"Booster Propellant Mass"] = 42630 * 1 # SLR    
            elif unique_vehicle_name_list[i] == "Atlas V 531":
                temp_dict[f"Booster Propellant Mass"] = 44200 * 3 # https://web.archive.org/web/20180918143456/http://www.northropgrumman.com/Capabilities/GEM/Documents/GEM_63_GEM_63XL.pdf    
            elif unique_vehicle_name_list[i] == "Atlas V 541":
                temp_dict[f"Booster Propellant Mass"] = 42630 * 4 # SLR       
            elif unique_vehicle_name_list[i] == "Atlas V 551":
                temp_dict[f"Booster Propellant Mass"] = 42630 * 5 # SLR    
                
            # Antares 230, second stage solid propellant has a typo in DISCOSweb.
            # Looking at user manuals, this value is also wrong, it seems to be for the Castor 30B second stage.
            # This vehicle uses the Castor 30XL, which has double the propellant mass.
            # https://www.northropgrumman.com/wp-content/uploads/CASTOR-Motor-Series.pdf Had to convert LBM to kg.
            if unique_vehicle_name_list[i] == "Antares 230":
                temp_dict[f"Stage2 Propellant Mass"] = 24924 # CASTOR documentation
            
            # Astra Rocket (USA) - 3 failed launches in 2020.
            # 2-stage rocket (Kerosene/LOX both stages)
            # 1) https://web.archive.org/web/20220411235206/http://www.spacelaunchreport.com/astra.html
            # 2) https://discosweb.esoc.esa.int/launch-vehicles/99082
            # First stage powered by 5 Delphin engines, second stage powered by 1 Aether engine.
            # Other two-stage rockets in 2020 include:
            # Antares 230   (Kerosene,   Solid,      242000, 12837)
            # Atlas V 501   (Kerosene,   Hydrogen,   284089, 20830)
            # Falcon 9 v1.2 (Kerosene,   Kerosene,   294300, 108700)
            # CZ-2C         (Hypergolic, Hypergolic, 144000, 53600) 
            # CZ-2D         (Hypergolic, Hypergolic, 183170, 35550)
            # However, these are all much bigger rockets designed to launch much larger payloads.
            # Need to find another small rocket (~10m) with a small payload (25kg).
            # Electron (Curie) is similar if we ignore the kick stage (18m, 300 kg) so using this.
            if unique_vehicle_name_list[i] == "Astra Rocket 3":
                temp_dict[f"Stage1 Propellant Mass"] = 9250 # Using value for Electron from SLR/DISCOSweb(wet/dry) 
                temp_dict[f"Stage2 Propellant Mass"] = 2050 # Using value for Electron from SLR/DISCOSweb(wet/dry) 
                
            # Will assume hypergolic, as wikipedia and following link suggest hydrazine.
            # https://www.nasaspaceflight.com/2021/12/chinas-galactic-energy-launches-second-ceres-1-rocket-successfully/
            # https://space.skyrocket.de/doc_lau/ceres-1.htm
            # https://discosweb.esoc.esa.int/launch-vehicles/99915
            # https://en.wikipedia.org/wiki/Galactic_Energy
            # https://www.galactic-energy.cn/index.php/En/List/cid/14
            # Website lists fourth stage as 'advanced liquid upper stage', will assume hypergolic
            # Comparing to all other four-stage rockets, very similar to Kuaizhou-1 (same fuel types, similar size and max payload mass)
            # So going to use the propellant masses for Kuaizhou-1.
            if unique_vehicle_name_list[i] == "Ceres-1":
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage4 Fuel Type"] = "Hypergolic"
                temp_dict[f"Stage1 Propellant Mass"] = 16000 # Kuaizhou-1 from DISCOSweb
                temp_dict[f"Stage2 Propellant Mass"] = 8000  # Kuaizhou-1 from DISCOSweb
                temp_dict[f"Stage3 Propellant Mass"] = 3000  # Kuaizhou-1 from DISCOSweb
                temp_dict[f"Stage4 Propellant Mass"] = 1000  # Kuaizhou-1 from DISCOSweb
            
            # "Chang'e 5 SSQ (Ascent Stage)" refers to the Chinese lunar exploration mission.
            # Specifically, the 'ascender' launching from the moon to dock with the 'orbiter'.
            # It eventually was 'crashed' back onto the moon to avoid space debris, so didn't re-enter. 
            # This can be ignored for the purpose of our study.
            
            # Electron (Curie) - 6 successes and one failure in 2020.
            # https://discosweb.esoc.esa.int/launch-vehicles/91285
            # https://web.archive.org/web/20220406013827/http://www.spacelaunchreport.com/electron.html
            # https://www.rocketlabusa.com/assets/Uploads/Rocket-Lab-Launch-Payload-Users-Guide-6.5.pdf
            # https://www.rocketlabusa.com/assets/Uploads/Electron-Payload-User-Guide-7.0.pdf
            # https://www.b14643.de/Spacerockets_3/Rocket-Lab/Description/Frame.htm
            # 3rd stage is 'kick-stage', and has a 'liquid bi-propellant' which wikipedia says is hypergolic.
            # Kick-stage is placed into low elliptical orbit, and burns some propellant to move into final orbit.
            # Seems like it is specific to mission, so would have to take an educated guess to the average prop.
            # Norbert Brügge gives slightly different prop masses, 10340, 2640, ?? to sum to 13000.
            if unique_vehicle_name_list[i] == "Electron (Curie)":
                temp_dict[f"Stage1 Propellant Name"] = 'Kerosene/LOX'
                temp_dict[f"Stage2 Propellant Name"] = 'Kerosene/LOX'
                temp_dict[f"Stage3 Propellant Name"] = 'Liquid bi-propellant'
                temp_dict[f"Stage1 Fuel Type"] = "Kerosene"
                temp_dict[f"Stage2 Fuel Type"] = "Kerosene"
                temp_dict[f"Stage3 Fuel Type"] = "Hypergolic"
                temp_dict[f"Stage1 Propellant Mass"] = 9250 # Using value from SLR/DISCOSweb(wet/dry) 
                temp_dict[f"Stage2 Propellant Mass"] = 2050 # Using value from SLR/DISCOSweb(wet/dry) 
                temp_dict[f"Stage3 Propellant Mass"] = 245  # Using value from DISCOSweb(wet/dry)
            
            # This is listed incorrectly on DISCOSweb, as it should actually be Falcon 9 Block 5, not v1.2.    
            if unique_vehicle_name_list[i] == "Falcon 9 v1.2":
                temp_dict[f"Stage1 Propellant Mass"] = 418700 # SLR 
                temp_dict[f"Stage2 Propellant Mass"] = 111500 # SLR  
            
            if unique_vehicle_name_list[i] == "H-IIA 202":
                temp_dict[f"Booster Propellant Mass"] = 130000 # https://global.jaxa.jp/projects/rockets/h2a/
                
            if unique_vehicle_name_list[i] == "H-IIB":
                temp_dict[f"Booster Propellant Mass"] = 263800 # https://global.jaxa.jp/projects/rockets/h2b/
            
            # Kuaizhou-1 - 2 successes and 1 failure.
            # https://web.archive.org/web/20220406013827/http://www.spacelaunchreport.com/kz.html
            # https://chinaspacereport.wordpress.com/launch-vehicles/kuaizhou/
            # https://www.nasaspaceflight.com/2014/11/china-launches-kuaizhou-2-second-launch-24-hours/ 'liquid upper stage'
            # Ryan22 approximated the the final stage mass using the mean of all four-stage solid rockets.
            # DISCOSweb gives stage4 wet and dry mass as 1200 and 200 kg, can use this to work out propellant mass of 1000 kg.
            # Norbert Brügge gives stage4 propellant mass as ~1.1t, so DISCOSweb figure is reasonable.
            if unique_vehicle_name_list[i] == "Kuaizhou-1":
                temp_dict[f"Stage4 Propellant Mass"] = 1000 # DISCOSweb(wet/dry)
            
            # Kuaizhou-11 (Stage 1-3, no prop mass or type)
            # https://en.wikipedia.org/wiki/Kuaizhou
            # https://web.archive.org/web/20220406013817/http://www.spacelaunchreport.com/kz11.html
            # https://chinaspacereport.wordpress.com/launch-vehicles/kuaizhou/#kz11
            # http://www.b14643.de/Spacerockets_4/Expace_KZ-11/Description/Frame.htm
            # https://discosweb.esoc.esa.int/launch-vehicles/98654
            # https://space.skyrocket.de/doc_lau/kuaizhou-11.htm
            # Might be a liquid fourth stage for propulsion control?
            # For now, compare to other three-stage rockets.
            # Similar size to CZ-6 and Simorgh (even though fuel type is different), much more similar LEO payload to CZ-6.
            # So will approximate using CZ-6.
            if unique_vehicle_name_list[i] == "Kuaizhou-11":
                temp_dict[f"Stage1 Propellant Name"] = 'Solid'
                temp_dict[f"Stage2 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 75800 # Using CZ-6 value from DISCOSweb
                temp_dict[f"Stage2 Propellant Mass"] = 15150 # Using CZ-6 value from DISCOSweb
                temp_dict[f"Stage3 Propellant Mass"] = 480   # Using CZ-6 value from NB
            
            # LauncherOne (Stage 1-2, no prop mass)
            if unique_vehicle_name_list[i] == "LauncherOne":
                temp_dict[f"Stage1 Propellant Mass"] = 20000 # NB
                temp_dict[f"Stage2 Propellant Mass"] = 2750  # NB/DISCOSweb(wet/dry)
                
            # Long March (CZ) 2C 
            # https://discosweb.esoc.esa.int/launch-vehicles/157
            # https://en.wikipedia.org/wiki/Long_March_2C
            # http://cgwic.com/Launchservice/LM2C.html
            if unique_vehicle_name_list[i] == "Long March (CZ) 2C":
                temp_dict[f"Stage1 Propellant Mass"] = 162706  # http://cgwic.com/Launchservice/LM2C.html
                temp_dict[f"Stage2 Propellant Mass"] = 54667   # http://cgwic.com/Launchservice/LM2C.html
                
            # Long March (CZ) 2D
            # https://discosweb.esoc.esa.int/launch-vehicles/158
            # https://en.wikipedia.org/wiki/Long_March_2D
            # http://cgwic.com/Launchservice/LM2D.html
            if unique_vehicle_name_list[i] == "Long March (CZ) 2D":
                temp_dict[f"Stage1 Propellant Mass"] = 182000  # http://cgwic.com/Launchservice/LM2D.html
                temp_dict[f"Stage2 Propellant Mass"] = 52700   # http://cgwic.com/Launchservice/LM2D.html
            
            # Long March (CZ) 2F
            if unique_vehicle_name_list[i] == "Long March (CZ) 2F":
                temp_dict[f"Booster Propellant Mass"] = 37800 * 4 # SLR
                
            # Long March (CZ) 3B 
            # https://discosweb.esoc.esa.int/launch-vehicles/64
            # https://en.wikipedia.org/wiki/Long_March_3B
            # http://cgwic.com/Launchservice/LM3B.html
            if unique_vehicle_name_list[i] == "Long March (CZ) 3B":
                temp_dict[f"Booster Propellant Mass"] = 37746 * 4 # http://cgwic.com/Launchservice/LM3B.html
                temp_dict[f"Stage1 Propellant Mass"]  = 171775    # http://cgwic.com/Launchservice/LM3B.html
                temp_dict[f"Stage2 Propellant Mass"]  = 49605     # http://cgwic.com/Launchservice/LM3B.html
                temp_dict[f"Stage3 Propellant Mass"]  = 18193     # http://cgwic.com/Launchservice/LM3B.html
                
            # Long March (CZ) 5
            # https://discosweb.esoc.esa.int/launch-vehicles/88066
            # https://en.wikipedia.org/wiki/Long_March_5
            if unique_vehicle_name_list[i] == "Long March (CZ) 5":
                temp_dict[f"Booster Propellant Mass"] = 152000 * 4 # From SLR (previous value was for when the same stage was used in LM7/8 as the 1st stage)
                
            # Long March (CZ) 5B 
            # https://discosweb.esoc.esa.int/launch-vehicles/98090
            # https://en.wikipedia.org/wiki/Long_March_5
            if unique_vehicle_name_list[i] == "Long March (CZ) 5B":
                temp_dict[f"Booster Propellant Mass"] = 152000 * 4 # From SLR (previous value was for when the same stage was used in LM7/8 as the 1st stage)
                temp_dict[f"Stage1 Propellant Mass"]  = 158500     # From 5 variant (same stage)
                
            # Long March (CZ) 6
            # https://discosweb.esoc.esa.int/launch-vehicles/75
            # https://chinaspacereport.wordpress.com/launch-vehicles/cz6/#1st-stage
            # https://web.archive.org/web/20220411235209/http://www.spacelaunchreport.com/cz5.html
            # https://space.skyrocket.de/doc_lau/cz-6.htm
            # http://www.b14643.de/Spacerockets_1/China/CZ-6/Description/Frame.htm 
            # DISCOSweb lists third stage as 'PBV' with LH2/LOX propellant.
            # Wikipedia lists third stage as N2O4/UDMH propellant.
            # Gunter's Space Page lists third stage as H2O2/Kerosene -  4 × YF-85.
            # ChinaSpaceReport lists third stage as H2O2/Kerosene - 4 x YF-85.
            # SLR lists third stage as H2O2/Kerosene - 4 x YF-85.
            # SLR gives 76t, 15t for stage 1 and 2 prop mass.
            # DISCOSweb gives 75.8t, 15.15t for stage 1 and 2 prop mass.
            # NB gives propellant weights for gross (93.7t), stage 1 (77.02), and stage 2 (16.2).
            # Subtracting stages 1+2 from gross gives 93.7-77.02-16.2 = 0.48t
            if unique_vehicle_name_list[i] == "Long March (CZ) 6":
                temp_dict[f"Stage3 Propellant Name"] = 'Kerosene/H2O2'
                temp_dict[f"Stage3 Fuel Type"] = "Kerosene"
                temp_dict[f"Stage3 Propellant Mass"] = 480 # NB
                
            # Long March (CZ) 7A
            # https://discosweb.esoc.esa.int/launch-vehicles/98084
            # https://web.archive.org/web/20220411235209/http://www.spacelaunchreport.com/cz5.html
            # https://en.wikipedia.org/wiki/Long_March_7#CZ-7A_variant
            # The only launch in 2020 for this rocket only includes emissons for the booster and 1st stage. So will ignore upper stages.
            if unique_vehicle_name_list[i] == "Long March (CZ) 7A":
                temp_dict[f"Booster Propellant Mass"] = 75500 * 4  # SLR
                temp_dict[f"Stage2 Propellant Mass"]  = 65000      # SLR
                temp_dict[f"Stage2 Propellant Mass"]  = 0          # Failed launch
                temp_dict[f"Stage3 Propellant Mass"]  = 0          # Failed launch                
                
            # Long March (CZ) 8
            # https://discosweb.esoc.esa.int/launch-vehicles/102354
            # https://web.archive.org/web/20220411235209/http://www.spacelaunchreport.com/cz5.html
            # https://en.wikipedia.org/wiki/Long_March_8
            if unique_vehicle_name_list[i] == "Long March (CZ) 8":
                temp_dict[f"Booster Propellant Mass"] = 75500 * 4 # SLR
        
            # Long March (CZ) 11.
            # Ryan22 approximated the propellant masses using the masses from the Vega rocket.
            # https://space.skyrocket.de/doc_lau/cz-11.htm 
            # https://chinaspacereport.wordpress.com/launch-vehicles/cz11/
            # https://discosweb.esoc.esa.int/launch-vehicles/5
            # https://web.archive.org/web/20220411235209/http://www.spacelaunchreport.com/cz11.html
            # Fourth Stage is Solid (Wiki, GSP, CSR) or Liquid (SLR)?
            # Other four-stage rockets in 2020 include: 
            # Kuaizhou-1 (Solid, Solid, Solid, Hypergolic, 16000, 8000, 3000, 1000)
            # Minotaur-4 (Solid, Solid, Solid, Solid, 45370, 24490, 7070, 770)
            # Proton-M   (Hypergolic, Hypergolic, Hypergolic, Hypergolic) 
            # Vega       (Solid, Solid, Solid, Hypergolic)
            # Most similar sizes are Kuaizhou-1 or Minotaur-4, but Minotaur-4 has a much more similar first stage propellant mass.
            # So going to approximate using the Minotaur-4 rocket: 
            #       2nd stage - 35000 / 45370 *  24490
            #       3rd stage - 35000 / 45370 *  7070
            #       4th stage - 35000 / 45370 *  770
            if unique_vehicle_name_list[i] == "Long March (CZ) 11":
                temp_dict[f"Stage1 Propellant Name"] = 'Solid'
                temp_dict[f"Stage2 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage4 Propellant Name"] = 'Solid'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage4 Fuel Type"] = 'Solid'
                temp_dict[f"Stage1 Propellant Mass"] = 35000 # From SLR/NB
                temp_dict[f"Stage2 Propellant Mass"] = 18892 # From approximation
                temp_dict[f"Stage3 Propellant Mass"] = 5454  # From approximation
                temp_dict[f"Stage4 Propellant Mass"] = 594   # From approximation
            
            # Minotaur-4
            # Based on LGM-118 Peacekeeper ICBM.
            # https://en.wikipedia.org/wiki/Minotaur_IV#STP-S26 
            # https://web.archive.org/web/20220406013816/http://www.spacelaunchreport.com/mintaur4.html
            # https://discosweb.esoc.esa.int/launch-vehicles/252
            # https://space.skyrocket.de/doc_lau_det/minotaur-4.htm
            # https://www.northropgrumman.com/wp-content/uploads/Minotaur-IV-VI-User-Guide.pdf
            if unique_vehicle_name_list[i] == "Minotaur-4":
                temp_dict[f"Stage1 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage2 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage3 Propellant Name"] = 'NEPE'
                temp_dict[f"Stage4 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage4 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 45370 # SLR
                temp_dict[f"Stage2 Propellant Mass"] = 24490 # SLR
                temp_dict[f"Stage3 Propellant Mass"] = 7070  # SLR
                temp_dict[f"Stage4 Propellant Mass"] = 770   # SLR, overwriting DISCOSweb with 782 to keep this vehicle consistent.           
            
            if unique_vehicle_name_list[i] == "PSLV-XL":
                temp_dict[f"Booster Propellant Mass"] = 12200 * 6 # https://www.isro.gov.in/media_isro/pdf/Missions/PSLVC41/PSLVC41.pdf   
                
            if unique_vehicle_name_list[i] == "PSLV-DL":
                temp_dict[f"Booster Propellant Mass"] = 12200 * 2 # https://www.isro.gov.in/media_isro/pdf/Missions/PSLV_C44_LaunchKit.pdf
                
            # Qased
            # https://en.wikipedia.org/wiki/Qased_(rocket)
            # http://www.b14643.de/Spacerockets_1/Rest_World/Qased-IRGC/Description/Frame.htm
            # https://discosweb.esoc.esa.int/launch-vehicles/98094
            # https://space.skyrocket.de/doc_lau/qased.htm
            # https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/safir.html
            # First stage uses UDMH/N2O4, second/third are solid fueled.
            # First stage says oxidiser is AK27 on DISCOSweb/SLR/NB, N2O4 on Wiki.
            # Norbert Brügge gives     12330 + 1500 + 185 = 14020, but upper stage is wrong (wiki).
            # DISCOSweb(wet/dry) gives 12330 + 1500 + 770 = 14600, but upper stage is wrong (wiki).
            # SLR gives                14400 + ???? + 240 = 14640, but upper stage is wrong (wiki).
            # Approximating third stage by averaging values from each source.
            if unique_vehicle_name_list[i] == "Qased":
                temp_dict[f"Stage1 Propellant Name"] = 'UDMH (Unsymmetrical Dimethyl Hydrazine)/AK-27I'
                temp_dict[f"Stage2 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 12330 # DISCOSweb(wet/dry)/NB
                temp_dict[f"Stage2 Propellant Mass"] = 1500  # DISCOSweb(wet/dry)/NB 
                temp_dict[f"Stage3 Propellant Mass"] = 398   # Average
            
            # Shavit (Stage 1-3, no prop mass or type)
            # https://discosweb.esoc.esa.int/launch-vehicles/76
            # https://space.skyrocket.de/doc_lau/shavit.htm
            # https://web.archive.org/web/20220406013832/http://www.spacelaunchreport.com/shavit.html
            # https://www.rafael.co.il/wp-content/uploads/2021/07/RAFAEL-SPACE-PROPULSION-2021-CATALOGUE-2.pdf
            # https://www.iai.co.il/sites/default/files/2020-07/Shavit%20Brochure.pdf
            # The stages are listed on DISCOSweb as the RSA-3 vehicle from South Africa, however the launch in 2020 was for Shavit-2.
            # Fourth stage isn't included on DISCOSweb or NB, but is included on SLR and mentioned on wiki.
            # DISCOSweb(wet/dry) are similar to values for Shavit/Shavit-1. Will use SLR values as these are correct for Shavit-2.
            if unique_vehicle_name_list[i] == "Shavit":
                temp_dict[f"Stage1 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage2 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage3 Propellant Name"] = 'HTPB'
                temp_dict[f"Stage4 Propellant Name"] = 'MMH'
                temp_dict[f"Stage1 Fuel Type"] = "Solid"
                temp_dict[f"Stage2 Fuel Type"] = "Solid"
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage4 Fuel Type"] = "Hypergolic"
                temp_dict[f"Stage1 Propellant Mass"] = 12750 # SLR
                temp_dict[f"Stage2 Propellant Mass"] = 12750 # SLR
                temp_dict[f"Stage3 Propellant Mass"] = 1890  # SLR
                temp_dict[f"Stage4 Propellant Mass"] = 166   # SLR
                
            # Simorgh
            # https://discosweb.esoc.esa.int/launch-vehicles/88324
            # https://web.archive.org/web/20220406013833/http://www.spacelaunchreport.com/simorgh.html
            # https://en.wikipedia.org/wiki/Saman-1_(rocket_stage)
            # Saman-1 is an upper-stage, used as a space tug to transfer satellites to higher orbits.
            if unique_vehicle_name_list[i] == "Simorgh":
                temp_dict[f"Stage3 Propellant Name"] = 'Solid'
                temp_dict[f"Stage3 Fuel Type"] = "Solid"
                temp_dict[f"Stage1 Propellant Mass"] = 63000 # SLR (v. similar to DISCOSwb(wet/dry))
                temp_dict[f"Stage2 Propellant Mass"] = 8000  # SLR (v. similar to DISCOSwb(wet/dry))
                temp_dict[f"Stage3 Propellant Mass"] = 185   # SLR (v. similar to DISCOSwb(wet/dry)) 
            
            # https://www.mach5lowdown.com/wp-content/uploads/PUG/Soyuz-Users-Manual-March-2012.pdf (Booster and 1st two stages)
            if unique_vehicle_name_list[i] == "Soyuz-2-1A":
                temp_dict[f"Booster Propellant Mass"] = (27900 + 11260) * 4
                temp_dict[f"Stage1 Propellant Mass"]  = 63800 + 26300
                temp_dict[f"Stage2 Propellant Mass"]  = 17800 + 7600
                
            # https://www.mach5lowdown.com/wp-content/uploads/PUG/Soyuz-Users-Manual-March-2012.pdf (Booster and 1st two stages)
            # https://web.archive.org/web/20151226122333/http://www.laspace.ru/rus/fregat_construction.php (Fregat details)
            if unique_vehicle_name_list[i] == "Soyuz-2-1B Fregat":
                temp_dict[f"Booster Propellant Mass"] = (27900 + 11260) * 4
                temp_dict[f"Stage1 Propellant Mass"]  = 63800 + 26300
                temp_dict[f"Stage2 Propellant Mass"]  = 17800 + 7600
                temp_dict[f"Stage3 Propellant Mass"]  = 5250
                    
            # https://www.mach5lowdown.com/wp-content/uploads/PUG/Soyuz-Users-Manual-March-2012.pdf (Booster and 1st two stages)
            # https://web.archive.org/web/20151226122333/http://www.laspace.ru/rus/fregat_construction.php (Fregat M details)
            if unique_vehicle_name_list[i] in ["Soyuz-2-1A Fregat-M",
                                               "Soyuz-2-1B Fregat-M",
                                               "Soyuz-ST-A Fregat-M"]:
                temp_dict[f"Booster Propellant Mass"] = (27900 + 11260) * 4
                temp_dict[f"Stage1 Propellant Mass"]  = 63800 + 26300
                temp_dict[f"Stage2 Propellant Mass"]  = 17800 + 7600
                temp_dict[f"Stage3 Propellant Mass"]  = 5600
                
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
        ds['Total_Prop_Mass']       = np.sum(booster_propmass_list) + np.sum(data_da_stage1_propmass) + np.sum(data_da_stage2_propmass) + np.sum(data_da_stage3_propmass) + np.sum(data_da_stage4_propmass) 
             
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
    
    #Now we can run class functions.
    LaunchData.get_launch_info()
    LaunchData.launch_info_to_netcdf()
    #LaunchData.get_rocket_info()
    #LaunchData.rocket_info_to_netcdf()
    