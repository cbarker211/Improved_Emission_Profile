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
URL = 'https://discosweb.esoc.esa.int/api'
token = np.loadtxt("./Databases/DISCOSweb_token.txt", dtype=str)

class import_launches_from_discos:   
    '''Read rocket launches from DISCOSweb'''
    def __init__(self,filename,year):
        
        self.filename = filename
        self.year = year
        self.get_launch_info(self.filename, self.year)
        self.convert_to_netcdf()

    def server_request(self,user_params,url_mod):
        response = requests.get(
                #Request information from the launches database.
                f'{URL}{url_mod}',
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
        for i in range(wait_time,0,-1):
            print(f"{message}Too many requests, retrying in {str(i)}s.", end="\r", flush=True)
            time.sleep(1)
 
    def get_yearly_launches(self,year): 
        self.full_launch_list = []
        start_epoch = f'{str(year)}-01-01'
        end_epoch = f'{str(year+1)}-01-01'
        while True:
            #Add the filtering here. Currently set up to show successful and unsuccessful launches per year.
            params={
                    'filter': f"ge(epoch,epoch:'{start_epoch}')&lt(epoch,epoch:'{end_epoch}')",
                    'sort' : 'epoch'
                }
            #Now we need a while loop to deal with the rate limit. 
            #If the response is ok (code <400), then it breaks the while loop, and if not then the while loop continues after a 60 second delay.
            while True:
                response = self.server_request(params, '/launches')
                if response.ok:
                    break
                else:
                    message = ""
                    wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                    self.wait_function(message,wait_time)
                    continue
            doc = response.json()
            temp_launch_list = doc['data']
            self.full_launch_list.extend(temp_launch_list)
            #Add a single second onto the start_epoch so we don't double count when the next query starts.
            if len(temp_launch_list) == 30:
                old_start_epoch = temp_launch_list[-1]["attributes"]["epoch"][0:19]
                old_start_epoch = datetime.strptime(old_start_epoch, '%Y-%m-%dT%H:%M:%S')
                start_epoch = old_start_epoch + timedelta(0,3) # days, seconds, then other fields.
                start_epoch = start_epoch.isoformat() + "+00:00"
                continue
            else:
                break
   
    def get_launch_info(self,filename, year):
        self.get_yearly_launches(year)
                
        self.Cospar_Id = []
        self.launch_time = []
        self.launch_day = []
        self.launch_month = []
        self.latitude = []
        self.longitude = []
        self.site_name = []
        self.rocket_name = []

        #self.full_launch_list = self.full_launch_list[:5]
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
                    message = f"On launch {count} of {len(self.full_launch_list)} in {year}."
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
                    message = f"On launch {count} of {len(self.full_launch_list)} in {year}."
                    wait_time=(int(response.headers["X-Ratelimit-Reset"])-int(time.time()))+1
                    self.wait_function(message,wait_time)
                    continue
            
            # Save the data as a .txt file in case we want to quickly check the values later.    
            with open(f'{filename}.txt', 'a') as f:
                f.write(f'{self.Cospar_Id[count]},{self.launch_time[count]},{self.launch_day[count]},{self.launch_month[count]},{self.latitude[count]},{self.longitude[count]},{self.site_name[count]},{self.rocket_name[count]},\n')

    def convert_to_netcdf(self):  
        
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
    
    #Set up the year and filename and run the main class.  
    year = 2020
    filename = f'./Databases/launch_info_{year}'
    LaunchData = import_launches_from_discos(filename,year)