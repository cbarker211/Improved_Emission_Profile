import numpy as np
import pandas as pd
from atmos_pressure import print_pressures
import matplotlib.pyplot as plt
import sys

def calculate_bc_ei(height, bc_pei):
    """ Calculate BC emission index in g BC per kg propellant burned.
        No emissions for hydrogen-based fuels.
        https://nap.nationalacademies.org/catalog/26142/commercial-space-vehicle-emissions-modeling

    Args:
        height (numpy.ma.core.MaskedArray)      : Altitude range (decreasing)
        bc_pei (numpy.ndarray with single value): Primary emission index (combustion of propellant) for black carbon.

    Returns:
        numpy.ma.core.MaskedArray: Final emission index (combustion of propellant and afterburning effects) for black carbon.
    """    
    
    ei_bc = np.zeros_like(height)

    for i, h in enumerate(height):
        ei_bc[i] = bc_pei * (max(0.04, (min(1, (0.04*(np.exp(0.12*(h-15))))))))
    
    return ei_bc

def calculate_nox_ei(height):
    """ Calculate NOx emission index in g NOx per kg propellant burned.
        Secondary for all rockets, primary for hypergolic and solid only.
        https://nap.nationalacademies.org/catalog/26142/commercial-space-vehicle-emissions-modeling

    Args:
        height (numpy.ma.core.MaskedArray)      : Altitude range (decreasing)

    Returns:
        numpy.ma.core.MaskedArray: Secondary emission index (thermal heating) for NOx.
    """

    ei_sec_nox = np.zeros_like(height)

    for i, h in enumerate(height):
        ei_sec_nox[i] = 33 * np.exp((-0.26)*h)
    
    return ei_sec_nox 

def calculate_co_ei(height, co_pei, co2_pei):
    """ Calculate CO emission index in g CO per kg propellant burned.
        https://nap.nationalacademies.org/catalog/26142/commercial-space-vehicle-emissions-modeling

    Args:
        height (numpy.ma.core.MaskedArray)       : Altitude range (decreasing)
        co_pei (numpy.ndarray with single value) : Primary emission index (combustion of propellant) for carbon monoxide.
        co2_pei (numpy.ndarray with single value): Primary emission index (combustion of propellant) for carbon dioxide.

    Returns:
        numpy.ma.core.MaskedArray: Final emission index (combustion of propellant and afterburning effects) for carbon monoxide.
    """    
        
    ei_co = np.zeros_like(height)
    ei_co2 = np.zeros_like(height)
    mw_co2 = 44.01
    mw_co  = 28.01

    for i, h in enumerate(height):
        ei_co[i] = min(co_pei, 0.0025*np.exp(0.067*h)*(co2_pei + co_pei))
        ei_co2[i] = co2_pei + mw_co2/mw_co * (co_pei-ei_co[i])

    return ei_co, ei_co2
        
def calculate_cl_ei(height, cly_pei):    
    """ Calculate emission indices for all chlorine species in g per kg propellant burned.
        Using data from Gomberg, Zittel and Leone, refs originally obtained from:
        https://nap.nationalacademies.org/catalog/26142/commercial-space-vehicle-emissions-modeling

    Args:
        height (numpy.ma.core.MaskedArray)       : Altitude range (decreasing)
        cly_pei (numpy.ndarray with single value): Primary emission index (combustion of propellant) for carbon monoxide.

    Returns:
        numpy.ma.core.MaskedArray * 3: Final emission indices (combustion of propellant and afterburning effects) for atomic chlorine, hydrogen chloride and dichloride.
    """    
    
    pei_file = pd.read_csv("./../chlorine_partitioning/chlorine_pei.csv")

    alt_lit                = pei_file["Alt"].to_numpy()
    hcl_param              = pei_file["HCl"].to_numpy()[0:4]         
    mass_frac_cl_average   = pei_file["Cl"].to_numpy()
    mass_frac_cl2_average  = pei_file["Cl2"].to_numpy()
        
    ei_cl = np.zeros_like(height)
    ei_cl2 = np.zeros_like(height)
    ei_hcl = np.zeros_like(height)
    
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
            ei_cl[i]  = mass_frac_cl * cly_pei
            ei_cl2[i] = mass_frac_cl2 * cly_pei
            ei_hcl[i] = mass_frac_hcl * cly_pei
        else:
            print(ei_cl[i],ei_cl2[i],ei_hcl[i],ei_cl[i]+ei_cl2[i]+ei_hcl[i])
            sys.exit(f"Warning, Cly didn't add to 100%.")
    
    if (np.sum(ei_cl) + np.sum(ei_cl2) + np.sum(ei_hcl)) > 0:  
        plt.plot(height,ei_cl,'-',color='orange')
        plt.plot(height,ei_cl2,'-',color='aqua')
        plt.plot(height,ei_hcl,'-',color='black')
        plt.xlim(0,80)
        plt.ylim(0,200)
        plt.xlabel("Altitude / km")
        plt.ylabel("Emission Index / g/kg")
        #plt.savefig("Cl.png")

    return ei_cl, ei_hcl, ei_cl2