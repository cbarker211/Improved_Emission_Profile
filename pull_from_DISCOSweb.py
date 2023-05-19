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
        for i in range(wait_time,0,-1):
            #The 'end="\r", flush=True' means that the line will replace itself instead of printing 60 lines.
            #This is useful to clean up the terminal, but may look weird sometimes before/after waiting.
            print(f"{message}Too many requests, retrying in {str(i)}s.", end="\r", flush=True)
            time.sleep(1)
 
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
                print(type(params))  
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
        self.rocket_name = []

        self.full_launch_list = self.full_launch_list[:5]
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

            while True:
                response = self.server_request({},f'/launches/{launch["id"]}/site')
                if response.ok:
                    doc = response.json()
                    self.latitude.append(np.float64(doc['data']["attributes"]["latitude"]))
                    self.longitude.append(np.float64(doc['data']["attributes"]["longitude"]))
                    temp_site_name = doc['data']["attributes"]["name"]
                    self.site_name.append(temp_site_name.replace(",",""))
                    break
                elif response.status_code == 400:
                    print("Client Error")
                    break
                elif response.status_code == 429:
                    message = f"On launch {count} of {len(self.full_launch_list)} in {self.year}."
                    wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                    self.wait_function(message,wait_time)
                    continue
                
            while True:
                response = self.server_request({},f'/launches/{launch["id"]}/vehicle')
                if response.ok:
                    doc = response.json()
                    self.rocket_name.append(doc['data']["attributes"]["name"])
                    break
                elif response.status_code == 400:
                    print("Client Error")
                    break
                elif response.status_code == 429:
                    message = f"On launch {count} of {len(self.full_launch_list)} in {self.year}."
                    wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                    self.wait_function(message,wait_time)
                    continue
        
    
        return [self.Cospar_Id, self.launch_time, self.launch_day, self.launch_month, self.latitude, self.longitude, self.site_name, self.rocket_name]
            
    def convert_to_netcdf(self):
        """This saves the launch information as a NetCDF file for later processing for GEOS-Chem.
        This is only needed if using GEOS-Chem. Recommended to ignore if you don't need this.
        """        
        
        #Set up the dimensions of the netcdf file.
        launches = np.arange(len(self.Cospar_Id), dtype=np.int64)
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
        
        data_da_rocket_type = xr.DataArray(self.rocket_name, dims=dims,
            attrs=dict(long_name="Rocket Type",
                       short_name="Rocket Type",
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
             
        #Save to file and close the DataSet     
        ds.to_netcdf(f'{self.filename}.nc')
        ds.close()

if __name__ == "__main__":
    """The main running of the program goes here. 
    All of the functions are inside the import_launches_from_discos class.
    Call each of the functions using import_launches_from_discos._function_
    e.g. import_launches_from_discos.launches_per_year(start_year,end_year)
    """         
    
    #Set up the year and filename.
    year = 2020
    filename = f'./Databases/launch_info_{year}'
    
    #Create an instance of the class.
    LaunchData = import_launches_from_discos(year)
    
    #Now we can run class functions. E.g. launch_list = LaunchData.get_yearly_launches()
    LaunchData.get_launch_info()
    LaunchData.convert_to_netcdf()
    
    #OPTIONAL: Save results to file.
    #with open(filename, 'a') as f:
    #   f.write(f'{self.Cospar_Id[count]},{self.launch_time[count]},{self.launch_day[count]},{self.launch_month[count]},{self.latitude[count]},{self.longitude[count]},{self.site_name[count]},{self.rocket_name[count]},\n')
    #   f.write(f'{year},{fuel_mass},{oxidiser_mass},{solid_mass},{total_mass}\n')
    #   f.write(f'In {year}, there were {num_payloads} payloads successfully launched.\n')   
    