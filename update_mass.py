def update_mass_info(i,temp_dict,unique_vehicle_name_list):
    
    temp_dict[f"Booster Number"] = 0
    temp_dict[f"Fairing Mass"] = 0
    
    if unique_vehicle_name_list[i] in ["Angara A5","Angara A5 Persei"]:
        
        # Prop masses:
        # DISCOSweb: 530400, 132600, 36000, 19800 (Briz-M), 15000 (Persei)
        # SLR      : 530400, 132600, 35800, 19800 (Briz-M), 18700 (Persei) 
        # Sp101    : 512000, 128000, 35800, 19800 (Briz-M), N/A   (Persei)
        # Manual   : 530400, 132600, 35800, 19800 (Briz-M), N/A   (Persei)
        
        # Stage masses:
        # DISCOSweb: 39200, 9800, 2000, 2370 (Briz-M), 2140 (Persei), N/A  (Fairing Briz-M), N/A (Fairing Persei)
        # SLR      : N/A,   N/A,  N/A,  2370 (Briz-M), 2900 (Persei), N/A  (Fairing Briz-M), N/A (Fairing Persei)
        # Sp101    : 39200, 9800, 4000, 2370 (Briz-M), N/A  (Persei), 1600 (Fairing Briz-M), N/A (Fairing Persei)
        # Manual   : N/A,   N/A,  N/A,  2370 (Briz-M), N/A  (Persei), 2600?? (Fairing Briz-M), N/A (Fairing Persei)
        
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Stage2 Propellant Mass"]  = 35800 # Manual
        temp_dict[f"Stage2 Stage Mass"]       = 4000 # SLR
        
        if unique_vehicle_name_list[i] == "Angara A5 Persei":
            temp_dict[f"Stage3 Propellant Mass"]  = 18700 # SLR
            temp_dict[f"Stage3 Stage Mass"]       = 2900  # SLR
            temp_dict[f"Fairing Mass"] = 1600 # No info, approximating using Briz-M.
        elif unique_vehicle_name_list[i] == "Angara A5":
            temp_dict[f"Fairing Mass"] = 1600 # Sp101, Angara A5 and Proton use the Briz-M upper stage.
            
    if unique_vehicle_name_list[i] == "Ariane 5ECA":
        temp_dict[f"Stage2 Stage Mass"] = 4540 # https://www.arianespace.com/wp-content/uploads/2016/10/Ariane5-users-manual-Jun2020.pdf
        temp_dict[f"Booster Number"] = 2
        # Fairing mass:
        #   - https://www.b14643.de/Spacerockets_1/West_Europe/Ariane-5/Description/Frame.htm           2380 kg
        #   - https://spaceflight101.com/spacerockets/ariane-5-eca/                                     2500 kg
        #   - https://www.arianespace.com/wp-content/uploads/2016/10/Ariane5-users-manual-Jun2020.pdf   2675 kg
        #   - https://web.archive.org/web/20220406013825/http://www.spacelaunchreport.com/ariane5.html  2500 kg (Long Fairing)
        temp_dict[f"Fairing Mass"] = 2675 # Using user manual value.
    
    # Fairing mass:
    #   - https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010.pdf            2305 kg (EPF)
    #   - https://spaceflight101.com/spacerockets/atlas-v-531/                                      2305 kg (EPF)
    #   - http://www.b14643.de/Spacerockets_2/United_States_3/Atlas_V/Description/Frame.htm         2305 kg (EPF)
    #   - https://web.archive.org/web/20220406013818/http://www.spacelaunchreport.com/atlas5.html   2260 kg (EPF)
    #   - https://spaceflight101.com/spacerockets/atlas-v-531/                                      3524 kg (5m short)  
    #   - https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010.pdf            3524 kg (5m short)
    #   - http://www.b14643.de/Spacerockets_2/United_States_3/Atlas_V/Description/Frame.htm         4085 kg (5m short)        
    if unique_vehicle_name_list[i] == "Atlas V 411":
        temp_dict[f"Booster Propellant Mass"] = 42630 * 1 # SLR  
        temp_dict[f"Booster Stage Mass"] = 3630 * 1 # SLR   
        temp_dict[f"Stage1 Stage Mass"] = 21054 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2
        temp_dict[f"Stage2 Stage Mass"] = 2243 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2  
        temp_dict[f"Booster Number"] = 1
        temp_dict[f"Fairing Mass"] = 2305 # Using user manual value.
    if unique_vehicle_name_list[i] == "Atlas V 501":
        temp_dict[f"Stage1 Stage Mass"] = 21351 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2
        temp_dict[f"Stage2 Stage Mass"] = 2247 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2 
        temp_dict[f"Fairing Mass"] = 3524 # Using user manual value.
    if unique_vehicle_name_list[i] == "Atlas V 531":
        temp_dict[f"Booster Propellant Mass"] = 44200 * 3 # https://web.archive.org/web/20180918143456/http://www.northropgrumman.com/Capabilities/GEM/Documents/GEM_63_GEM_63XL.pdf
        temp_dict[f"Booster Stage Mass"] = 5100 * 3 # https://web.archive.org/web/20180918143456/http://www.northropgrumman.com/Capabilities/GEM/Documents/GEM_63_GEM_63XL.pdf 
        temp_dict[f"Stage1 Stage Mass"] = 21351 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2
        temp_dict[f"Stage2 Stage Mass"] = 2247 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2 
        temp_dict[f"Booster Number"] = 3
        temp_dict[f"Fairing Mass"] = 3524 # Using user manual value.
    if unique_vehicle_name_list[i] == "Atlas V 541":
        temp_dict[f"Booster Propellant Mass"] = 42630 * 4 # SLR   
        temp_dict[f"Booster Stage Mass"] = 3630 * 4 # SLR    
        temp_dict[f"Stage1 Stage Mass"] = 21351 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2
        temp_dict[f"Stage2 Stage Mass"] = 2247 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2 
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 3524 # Using user manual value.
    if unique_vehicle_name_list[i] == "Atlas V 551":
        temp_dict[f"Booster Propellant Mass"] = 42630 * 5 # SLR    
        temp_dict[f"Booster Stage Mass"] = 3630 * 5 # SLR 
        temp_dict[f"Stage1 Stage Mass"] = 21351 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2
        temp_dict[f"Stage2 Stage Mass"] = 2247 # https://www.ulalaunch.com/docs/default-source/rockets/atlasvusersguide2010a.pdf?sfvrsn=f84bb59e_2
        temp_dict[f"Booster Number"] = 5
        temp_dict[f"Fairing Mass"] = 3524 # Using user manual value.
        
    # Antares 230, second stage solid propellant has a typo in DISCOSweb.
    # Looking at user manuals, this value is also wrong, it seems to be for the Castor 30B second stage.
    # This vehicle uses the Castor 30XL, which has double the propellant mass.
    # https://www.northropgrumman.com/wp-content/uploads/CASTOR-Motor-Series.pdf Had to convert LBM to kg.
    if unique_vehicle_name_list[i] == "Antares 230":
        temp_dict[f"Stage2 Propellant Mass"] = 24924 # CASTOR documentation
        temp_dict[f"Stage2 Stage Mass"] = 2100 # https://spaceflight101.com/spacerockets/antares-200-series/ and SLR.
        # Fairing mass:
        #   - https://spaceflight101.com/spacerockets/antares-200-series/                               970kg
        #   - https://web.archive.org/web/20220406013828/http://www.spacelaunchreport.com/taurus2.html  972kg
        #   - http://www.b14643.de/Spacerockets_2/United_States_2/Antares/Description/Frame.htm         972kg
        temp_dict[f"Fairing Mass"] = 972
    
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
        temp_dict[f"Stage1 Stage Mass"]      = 950 # Using value for Electron
        temp_dict[f"Stage2 Stage Mass"]      = 250 # Using value for Electron
        temp_dict[f"Fairing Mass"]           = 44  # Using value for Electron
    
    # Ceres-1 
    # Will assume hypergolic, as wikipedia and following link suggest hydrazine.
    # https://www.nasaspaceflight.com/2021/12/chinas-galactic-energy-launches-second-ceres-1-rocket-successfully/
    # https://space.skyrocket.de/doc_lau/ceres-1.htm
    # https://discosweb.esoc.esa.int/launch-vehicles/99915
    # https://en.wikipedia.org/wiki/Galactic_Energy
    # https://www.galactic-energy.cn/index.php/En/List/cid/14
    # Website lists fourth stage as 'advanced liquid upper stage', will assume hypergolic
    # Comparing to all other four-stage rockets, very similar to Kuaizhou-1 (same fuel types, similar size and max payload mass)
    # So going to use the propellant masses for Kuaizhou-1.
    # For fairing mass, approximating using Ceres-1 (which approximates using Shavit). All similar LEO payload mass and size.
    if unique_vehicle_name_list[i] == "Ceres-1":
        temp_dict[f"Stage1 Fuel Type"] = "Solid"
        temp_dict[f"Stage2 Fuel Type"] = "Solid"
        temp_dict[f"Stage3 Fuel Type"] = "Solid"
        temp_dict[f"Stage4 Fuel Type"] = "Hypergolic"
        temp_dict[f"Stage1 Propellant Mass"] = 16000 # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Stage2 Propellant Mass"] = 8000  # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Stage3 Propellant Mass"] = 3000  # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Stage4 Propellant Mass"] = 1000  # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Stage1 Stage Mass"] = 621  # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Stage2 Stage Mass"] = 686  # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Stage3 Stage Mass"] = 183  # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Stage4 Stage Mass"] = 200  # Kuaizhou-1 from DISCOSweb
        temp_dict[f"Fairing Mass"] = 57 # Approximating using Shavit.
    
    # "Chang'e 5 SSQ (Ascent Stage)" refers to the Chinese lunar exploration mission.
    # Specifically, the 'ascender' launching from the moon to dock with the 'orbiter'.
    # It eventually was 'crashed' back onto the moon to avoid space debris, so didn't re-enter. 
    # This can be ignored for the purpose of our study.
    
    # https://discosweb.esoc.esa.int/launch-vehicles/203
    # http://www.b14643.de/Spacerockets_2/United_States_5/Delta_IV/Description/Frame.htm
    # https://web.archive.org/web/20220406013823/http://www.spacelaunchreport.com/delta4.html
    # https://spaceflight101.com/spacerockets/delta-iv-heavy/
    # Fairing mass:
    #   - https://web.archive.org/web/20220406013823/http://www.spacelaunchreport.com/delta4.html   3550
    #   - http://www.b14643.de/Spacerockets_2/United_States_5/Delta_IV/Description/Frame.htm        3520
    if unique_vehicle_name_list[i] == "Delta 4H":
        temp_dict[f"Booster Propellant Mass"] = 204000 * 2 # SLR
        temp_dict[f"Stage1 Propellant Mass"]  = 204000     # SLR
        temp_dict[f"Stage2 Propellant Mass"]  = 3350       # SLR
        temp_dict[f"Booster Stage Mass"]      = 28000 * 2  # SLR
        temp_dict[f"Stage1 Stage Mass"]       = 28000      # SLR
        temp_dict[f"Stage2 Stage Mass"]       = 3350       # SLR
        temp_dict[f"Booster Number"] = 2
        temp_dict[f"Fairing Mass"] = 3550
        
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
    # Fairing mass:
    #   - https://spaceflight101.com/spacerockets/electron/                                                         50 kg
    #   - https://www.b14643.de/Spacerockets_3/Rocket-Lab/Description/Frame.htm                                     44 kg
    #   - https://www.mach5lowdown.com/wp-content/uploads/2023/02/Rocket-Lab-Electron-Payload-User-Guide-7.0.pdf    44 kg
    #   - https://web.archive.org/web/20220406013827/http://www.spacelaunchreport.com/electron.html                 50 kg
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
        temp_dict[f"Stage3 Stage Mass"]      = 40 # https://www.rocketlabusa.com/assets/Uploads/Electron-Payload-User-Guide-7.0.pdf 
        temp_dict[f"Fairing Mass"] = 44 # Using user manual value.
        
    # This is listed incorrectly on DISCOSweb, as it should actually be Falcon 9 Block 5, not v1.2.    
    # Fairing mass:
    #   - https://spaceflight101.com/spacerockets/falcon-9-ft/                                          1750 kg
    #   - http://www.b14643.de/Spacerockets_2/United_States_1/Falcon-9/Description/Frame.htm            2500 kg
    #   - https://web.archive.org/web/20220411235211/http://www.spacelaunchreport.com/falcon9ft.html    2000 kg
    if unique_vehicle_name_list[i] == "Falcon 9 v1.2":
        temp_dict[f"Stage1 Propellant Mass"] = 418700 # SLR 
        temp_dict[f"Stage2 Propellant Mass"] = 111500 # SLR 
        temp_dict[f"Stage1 Stage Mass"]      = 27200  # SLR 
        temp_dict[f"Stage2 Stage Mass"]      = 4500   # SLR
        temp_dict[f"Fairing Mass"] = (1750+2000+2500) / 3 # Average of sources.
    
    if unique_vehicle_name_list[i] == "H-IIA 202":
        # Fairing mass:
        #   - https://spaceflight101.com/spacerockets/h-iia-202/                                    1400 kg
        #   - http://www.b14643.de/Spacerockets_1/Japan/H-IIA/Description/Frame.htm                 1400 kg
        #   - https://web.archive.org/web/20220406013820/http://www.spacelaunchreport.com/h2.html   1400 kg
        temp_dict[f"Booster Stage Mass"]      = 21000   # https://global.jaxa.jp/projects/rockets/h2a/
        temp_dict[f"Stage1 Stage Mass"]       = 12900   # https://global.jaxa.jp/projects/rockets/h2a/
        temp_dict[f"Stage2 Stage Mass"]       = 3100    # https://global.jaxa.jp/projects/rockets/h2a/
        temp_dict[f"Booster Propellant Mass"] = 130000  # https://global.jaxa.jp/projects/rockets/h2a/
        temp_dict[f"Booster Number"] = 2
        temp_dict[f"Fairing Mass"] = 1400
        
    if unique_vehicle_name_list[i] == "H-IIB":
        #   - https://spaceflight101.com/spacerockets/h-iib/                                        3200 kg
        #   - http://www.b14643.de/Spacerockets_1/Japan/H-IIA/Description/Frame.htm                 2500 kg
        #   - https://web.archive.org/web/20220406013820/http://www.spacelaunchreport.com/h2.html   3200 kg
        temp_dict[f"Booster Stage Mass"]      = 42200   # https://global.jaxa.jp/projects/rockets/h2b/
        temp_dict[f"Stage1 Stage Mass"]       = 24200   # https://global.jaxa.jp/projects/rockets/h2b/
        temp_dict[f"Stage2 Stage Mass"]       = 3400    # https://global.jaxa.jp/projects/rockets/h2b/
        temp_dict[f"Booster Propellant Mass"] = 263800  # https://global.jaxa.jp/projects/rockets/h2b/
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 3200
    
    # Kuaizhou-1 - 2 successes and 1 failure.
    # https://web.archive.org/web/20220406013827/http://www.spacelaunchreport.com/kz.html
    # https://chinaspacereport.wordpress.com/launch-vehicles/kuaizhou/
    # https://www.nasaspaceflight.com/2014/11/china-launches-kuaizhou-2-second-launch-24-hours/ 'liquid upper stage'
    # Ryan22 approximated the the final mass using the mean of all four-stage solid rockets.
    # DISCOSweb gives stage4 wet and dry mass as 1200 and 200 kg, can use this to work out propellant mass of 1000 kg.
    # Norbert Brügge gives stage4 propellant mass as ~1.1t, so DISCOSweb figure is reasonable.
    # For fairing mass, approximating using Shavit. Similar LEO payload mass and size.
    if unique_vehicle_name_list[i] == "Kuaizhou-1":
        temp_dict[f"Stage4 Propellant Mass"] = 1000 # DISCOSweb(wet/dry)
        temp_dict[f"Stage1 Stage Mass"] = 621  # DISCOSweb, uses data from SLR?
        temp_dict[f"Stage2 Stage Mass"] = 686  # DISCOSweb, uses data from SLR?
        temp_dict[f"Stage3 Stage Mass"] = 183  # DISCOSweb, uses data from SLR?
        temp_dict[f"Stage4 Stage Mass"] = 200  # DISCOSweb, uses data from SLR?
        temp_dict[f"Fairing Mass"] = 57 # Approximating using Shavit.
    
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
        temp_dict[f"Stage1 Propellant Mass"] = 75800 # Using CZ-6 value from DISCOSweb.
        temp_dict[f"Stage2 Propellant Mass"] = 15150 # Using CZ-6 value from DISCOSweb.
        temp_dict[f"Stage3 Propellant Mass"] = 480   # Using CZ-6 value from NB.
        temp_dict[f"Stage1 Stage Mass"]      = 7530  # Using CZ-6 value from SLR.
        temp_dict[f"Stage2 Stage Mass"]      = 1490  # Using CZ-6 value from SLR.
        temp_dict[f"Stage3 Stage Mass"]      = 1000  # Using CZ-6 value from DISCOSweb.
        temp_dict[f"Fairing Mass"]           = 1500  # Using CZ-6 value from NB.
    
    # LauncherOne (Stage 1-2, no prop mass)
    # Failed launch without reentry so ignore.
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
        temp_dict[f"Stage1 Stage Mass"]      = 10000   # SLR
        temp_dict[f"Fairing Mass"] = 800 # http://www.b14643.de/Spacerockets_1/China/CZ-2C/Description/Frame.htm
        
    # Long March (CZ) 2D
    # https://discosweb.esoc.esa.int/launch-vehicles/158
    # https://en.wikipedia.org/wiki/Long_March_2D
    # http://cgwic.com/Launchservice/LM2D.html
    if unique_vehicle_name_list[i] == "Long March (CZ) 2D":
        temp_dict[f"Stage1 Propellant Mass"] = 182000  # http://cgwic.com/Launchservice/LM2D.html
        temp_dict[f"Stage2 Propellant Mass"] = 52700   # http://cgwic.com/Launchservice/LM2D.html
        temp_dict[f"Fairing Mass"] = 750 # http://www.b14643.de/Spacerockets_1/China/CZ-2D/Description/Frame.htm
    
    # Long March (CZ) 2F
    if unique_vehicle_name_list[i] == "Long March (CZ) 2F":
        temp_dict[f"Booster Propellant Mass"] = 37800 * 4 # SLR
        temp_dict[f"Booster Stage Mass"] = 3200 * 4  # SLR
        temp_dict[f"Stage1 Stage Mass"] = 9500      # SLR
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = (6000+3000)/2 # Average of SZ/TG in http://www.b14643.de/Spacerockets_1/China/CZ-2EF/Description/Frame.htm
        
    # Long March (CZ) 3B 
    # https://discosweb.esoc.esa.int/launch-vehicles/64
    # https://en.wikipedia.org/wiki/Long_March_3B
    # http://cgwic.com/Launchservice/LM3B.html
    # Fairing mass:
    #   - https://spaceflight101.com/spacerockets/long-march-3b/                1500 kg
    #   - http://www.b14643.de/Spacerockets_1/China/CZ-3/Description/Frame.htm  1800 kg
    if unique_vehicle_name_list[i] == "Long March (CZ) 3B":
        temp_dict[f"Booster Propellant Mass"] = 37746 * 4 # http://cgwic.com/Launchservice/LM3B.html
        temp_dict[f"Stage1 Propellant Mass"]  = 171775    # http://cgwic.com/Launchservice/LM3B.html
        temp_dict[f"Stage2 Propellant Mass"]  = 49605     # http://cgwic.com/Launchservice/LM3B.html
        temp_dict[f"Stage3 Propellant Mass"]  = 18193     # http://cgwic.com/Launchservice/LM3B.html
        temp_dict[f"Booster Stage Mass"] = 3300 * 4 # SLR
        temp_dict[f"Stage1 Stage Mass"]  = 9200     # SLR
        # Stage 2 info not in SLR so keeping DISCOSweb value.
        temp_dict[f"Stage3 Stage Mass"]  = 2800     # SLR 
        temp_dict[f"Booster Number"] = 4  
        temp_dict[f"Fairing Mass"] = (1500+1800) / 2
        
    if unique_vehicle_name_list[i] in ["Long March (CZ) 4B","Long March (CZ) 4C"]:  
        temp_dict[f"Stage3 Stage Mass"]  = 2000     # SLR
        temp_dict[f"Fairing Mass"] = 1800           # http://www.b14643.de/Spacerockets_1/China/CZ-4/Description/Frame.htm
        
    # Long March (CZ) 5
    # https://discosweb.esoc.esa.int/launch-vehicles/88066
    # https://en.wikipedia.org/wiki/Long_March_5
    if unique_vehicle_name_list[i] == "Long March (CZ) 5":
        temp_dict[f"Booster Propellant Mass"] = 152000 * 4 # From SLR (previous value was for when the same stage was used in LM7/8 as the 1st stage)
        temp_dict[f"Booster Stage Mass"]      = 12500 * 4  # From SLR
        temp_dict[f"Stage1 Stage Mass"]       = 17000      # From SLR
        temp_dict[f"Stage2 Stage Mass"]       = 3520       # From SLR
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 2400 # http://www.b14643.de/Spacerockets_1/China/CZ-5/Description/Frame.htm
        
    # Long March (CZ) 5B 
    # https://discosweb.esoc.esa.int/launch-vehicles/98090
    # https://en.wikipedia.org/wiki/Long_March_5
    if unique_vehicle_name_list[i] == "Long March (CZ) 5B":
        temp_dict[f"Booster Propellant Mass"] = 152000 * 4 # From SLR (previous value was for when the same stage was used in LM7/8 as the 1st stage)
        temp_dict[f"Stage1 Propellant Mass"]  = 158500     # From 5 variant (same stage)
        temp_dict[f"Booster Stage Mass"]      = 12500 * 4  # From SLR
        temp_dict[f"Stage1 Stage Mass"]       = 17000      # From SLR
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 3000 # http://www.b14643.de/Spacerockets_1/China/CZ-5/Description/Frame.htm
        
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
        temp_dict[f"Stage1 Stage Mass"]      = 7530 # SLR
        temp_dict[f"Stage2 Stage Mass"]      = 1490 # SLR
        # Stage 3 info not in SLR so keeping DISCOSweb value.
        temp_dict[f"Fairing Mass"] = 1500 # http://www.b14643.de/Spacerockets_1/China/CZ-6/Description/Frame.htm
            
    # Long March (CZ) 7A
    # https://discosweb.esoc.esa.int/launch-vehicles/98084
    # https://web.archive.org/web/20220411235209/http://www.spacelaunchreport.com/cz5.html
    # https://en.wikipedia.org/wiki/Long_March_7#CZ-7A_variant
    # The only launch in 2020 for this rocket only includes emissons for the booster and 1st stage. 
    # But we still need prop masses for the reentry info.
    if unique_vehicle_name_list[i] == "Long March (CZ) 7A":
        temp_dict[f"Booster Propellant Mass"] = 75500 * 4  # SLR
        temp_dict[f"Stage1 Propellant Mass"]  = 174000     # SLR
        temp_dict[f"Stage2 Propellant Mass"]  = 65000      # SLR
        temp_dict[f"Stage3 Propellant Mass"]  = 18200      # SLR  
        temp_dict[f"Booster Stage Mass"]      = 6000 * 4   # SLR
        temp_dict[f"Stage1 Stage Mass"]       = 12500      # SLR              
        temp_dict[f"Stage2 Stage Mass"]       = 5500       # SLR 
        temp_dict[f"Stage3 Stage Mass"]       = 2800       # SLR
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 2500 # http://www.b14643.de/Spacerockets_1/China/CZ-7A/Description/Frame.htm
        
    # Long March (CZ) 8
    # https://discosweb.esoc.esa.int/launch-vehicles/102354
    # https://web.archive.org/web/20220411235209/http://www.spacelaunchreport.com/cz5.html
    # https://en.wikipedia.org/wiki/Long_March_8
    if unique_vehicle_name_list[i] == "Long March (CZ) 8":
        temp_dict[f"Booster Propellant Mass"] = 75500 * 4 # SLR
        temp_dict[f"Booster Stage Mass"]      = 6000 * 2  # SLR
        temp_dict[f"Stage1 Stage Mass"]       = 12500     # SLR   
        temp_dict[f"Booster Number"] = 2   
        temp_dict[f"Fairing Mass"] = 2500 # http://www.b14643.de/Spacerockets_1/China/CZ-8/Description/Frame.htm        

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
    #       2nd stage prop  mass- 35000 / 45370 *  24490
    #       3rd stage prop  mass- 35000 / 45370 *  7070
    #       4th stage prop  mass- 35000 / 45370 *  770
    #       2nd stage stage mass - 4700 / 3620  *  3180
    #       3rd stage stage mass - 4700 / 3620  *  640
    #       4th stage stage mass - 4700 / 3620  *  410
    
    if unique_vehicle_name_list[i] == "Long March (CZ) 11":
        temp_dict[f"Stage1 Propellant Name"] = 'Solid'
        temp_dict[f"Stage2 Propellant Name"] = 'Solid'
        temp_dict[f"Stage3 Propellant Name"] = 'Solid'
        temp_dict[f"Stage4 Propellant Name"] = 'Solid'
        temp_dict[f"Stage1 Fuel Type"] = "Solid"
        temp_dict[f"Stage2 Fuel Type"] = "Solid"
        temp_dict[f"Stage3 Fuel Type"] = "Solid"
        temp_dict[f"Stage4 Fuel Type"] = 'Solid'
        temp_dict[f"Stage1 Propellant Mass"] = 35000              # From SLR/NB
        temp_dict[f"Stage2 Propellant Mass"] = 18892              # From approximation
        temp_dict[f"Stage3 Propellant Mass"] = 5454               # From approximation
        temp_dict[f"Stage4 Propellant Mass"] = 594                # From approximation
        temp_dict[f"Stage1 Stage Mass"]      = 4700               # SLR
        temp_dict[f"Stage2 Stage Mass"]      = 4129               # From approximation
        temp_dict[f"Stage3 Stage Mass"]      = 831                # From approximation
        temp_dict[f"Fairing Mass"]           = (400+400+450) / 3  # Approximated using Minotaur IV
        # Stage 4 Dry Mass is given by DISCOSweb as 500.
        
    # Minotaur-4
    # Based on LGM-118 Peacekeeper ICBM.
    # https://en.wikipedia.org/wiki/Minotaur_IV#STP-S26 
    # https://web.archive.org/web/20220406013816/http://www.spacelaunchreport.com/mintaur4.html
    # https://discosweb.esoc.esa.int/launch-vehicles/252
    # https://space.skyrocket.de/doc_lau_det/minotaur-4.htm
    # https://www.northropgrumman.com/wp-content/uploads/Minotaur-IV-VI-User-Guide.pdf
    # Fairing mass:
    #   - https://spaceflight101.com/spacerockets/minotaur-iv/                                          450 kg
    #   - https://web.archive.org/web/20220406013816/http://www.spacelaunchreport.com/mintaur4.html     400 kg
    #   - http://www.b14643.de/Spacerockets_2/United_States_2/PK-Minotaur/Description/Frame.htm         400 kg
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
        temp_dict[f"Stage1 Stage Mass"] = 3620       # SLR
        temp_dict[f"Stage2 Stage Mass"] = 3180       # SLR
        temp_dict[f"Stage3 Stage Mass"] = 640        # SLR
        temp_dict[f"Stage4 Stage Mass"] = 410        # SLR
        temp_dict[f"Fairing Mass"] = (400+400+450) / 3
        
    # Fairing mass:
    #   - https://spaceflight101.com/spacerockets/pslv/                                         1150 kg
    #   - https://web.archive.org/web/20220406013825/http://www.spacelaunchreport.com/pslv.html 1100 kg    
    #   - http://www.b14643.de/Spacerockets_1/India/PSLV/Description/Frame.htm                  1100 kg
    if unique_vehicle_name_list[i] == "PSLV-XL":
        temp_dict[f"Booster Propellant Mass"] = 12200 * 6 # https://www.isro.gov.in/media_isro/pdf/Missions/PSLVC41/PSLVC41.pdf  
        temp_dict[f"Booster Stage Mass"] = 2700 * 6 # SLR 
        temp_dict[f"Stage2 Stage Mass"] = 5400 # SLR  
        temp_dict[f"Stage3 Stage Mass"] = 700  # SLR
        temp_dict[f"Stage4 Stage Mass"] = 420  # SLR 
        temp_dict[f"Booster Number"] = 6
        temp_dict[f"Fairing Mass"] = (1150+1100+1100) / 3
        
    if unique_vehicle_name_list[i] == "PSLV-DL":
        temp_dict[f"Booster Propellant Mass"] = 12200 * 2 # https://www.isro.gov.in/media_isro/pdf/Missions/PSLV_C44_LaunchKit.pdf
        temp_dict[f"Booster Stage Mass"] = 2700 * 2 # SLR
        temp_dict[f"Stage2 Stage Mass"] = 5400 # SLR
        temp_dict[f"Stage3 Stage Mass"] = 700  # SLR
        temp_dict[f"Stage4 Stage Mass"] = 420  # SLR
        temp_dict[f"Booster Number"] = 2
        temp_dict[f"Fairing Mass"] = (1150+1100+1100) / 3

    if unique_vehicle_name_list[i] == "Proton-M/Briz-M":
        # DISCOSweb hasn't updated to inlcude the 'Enhanced' variant, which has been standard since 2007.
        # Stages 2-4 are correct, but stage 1 needs correcting.
        temp_dict[f"Stage1 Stage Mass"] = 30600 # SLR
        # Angara A5 and Proton use the Briz-M upper stage.
        temp_dict[f"Fairing Mass"] = 1600 # https://spaceflight101.com/spacerockets/angara-a5/
    
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
    # Fairing mass:
    #   - https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/safir.html    100 kg
    #   - http://www.b14643.de/Spacerockets_1/Rest_World/Qased-IRGC/Description/Frame.htm           40 kg
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
        # SLR only has 1 stage, so using DISCOSweb.
        temp_dict[f"Fairing Mass"] = (40+100) / 2 
    
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
        temp_dict[f"Stage1 Stage Mass"]      = 1240  # SLR
        temp_dict[f"Stage2 Stage Mass"]      = 1376  # SLR
        temp_dict[f"Stage3 Stage Mass"]      = 684   # SLR
        temp_dict[f"Stage4 Stage Mass"]      = 71    # SLR
        temp_dict[f"Fairing Mass"] = 57 # http://www.b14643.de/Spacerockets_1/Rest_World/Shavit/Description/Frame.htm
        
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
        temp_dict[f"Stage1 Stage Mass"]      = 12700 # SLR (v. similar to DISCOSwb(wet/dry))
        temp_dict[f"Stage2 Stage Mass"]      = 1600  # SLR (v. similar to DISCOSwb(wet/dry))
        temp_dict[f"Stage3 Stage Mass"]      = 230   # SLR (v. similar to DISCOSwb(wet/dry)) 
        temp_dict[f"Fairing Mass"] = 120 # http://www.b14643.de/Spacerockets_1/Rest_World/Simorgh-IRILV/Description/Frame.htm
        # also 120 in https://web.archive.org/web/20220406013833/http://www.spacelaunchreport.com/simorgh.html
    
    # https://www.mach5lowdown.com/wp-content/uploads/PUG/Soyuz-Users-Manual-March-2012.pdf (Booster and 1st two stages)  
    # https://web.archive.org/web/20151226122333/http://www.laspace.ru/rus/fregat_construction.php (Fregat/Fregat-M details) 
    # file:///C:/Users/ucfacb0/OneDrive%20-%20University%20College%20London/Downloads/soyuz_users_manual_190401%20(5).pdf 
    # Fairing mass:
    #   - http://www.b14643.de/Spacerockets_1/East_Europe_1/Soyuz-2/Description/Frame.htm           1000 kg (Soyuz-2 (1a)	Soyuz-2K (1b))
    #   - http://www.b14643.de/Spacerockets_1/East_Europe_1/Soyuz-2/Description/Frame.htm           1800 kg (Soyuz-2/Fregat	Soyuz-2K/Fregat)
    #   - http://www.b14643.de/Spacerockets_1/East_Europe_1/Soyuz-ST/Description/Frame.htm          1800 kg (Soyuz-2K/Fregat)
    #   - http://www.b14643.de/Spacerockets_1/West_Europe/Soyuz-ESA/Description/Frame.htm           1800 kg (Soyuz STK-A, Soyuz STK-B - Fregat and Fregat-M)
    #   - https://www.mach5lowdown.com/wp-content/uploads/PUG/Soyuz-Users-Manual-March-2012.pdf     1700 kg (ST Fairing for Arianespace with Fregat)
    if unique_vehicle_name_list[i] in ["Soyuz-2-1A","Soyuz-2-1A Fregat-M","Soyuz-ST-A Fregat-M","Soyuz-2-1B Fregat","Soyuz-2-1B Fregat-M"]:
        temp_dict[f"Booster Propellant Mass"] = (27900 + 11260) * 4
        temp_dict[f"Stage1 Propellant Mass"]  = 63800 + 26300
        temp_dict[f"Stage2 Propellant Mass"]  = 17800 + 7600
        temp_dict[f"Booster Stage Mass"]      = 3784 * 4
        temp_dict[f"Stage1 Stage Mass"]       = 6545
        
    if unique_vehicle_name_list[i] == "Soyuz-2-1A":
        temp_dict[f"Stage2 Stage Mass"]       = 2410  
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 1000
    
    if unique_vehicle_name_list[i] == "Soyuz-2-1A Fregat-M":
        temp_dict[f"Stage3 Propellant Mass"]  = 5600   
        temp_dict[f"Stage2 Stage Mass"]       = 2410  
        temp_dict[f"Stage3 Stage Mass"]       = 980    
        temp_dict[f"Booster Number"] = 4 
        temp_dict[f"Fairing Mass"] = 1700 # Using user manual value
        
    if unique_vehicle_name_list[i] in "Soyuz-ST-A Fregat-M":
        temp_dict[f"Stage3 Propellant Mass"]  = 5600   
        temp_dict[f"Stage2 Stage Mass"]       = 2470  
        temp_dict[f"Stage3 Stage Mass"]       = 980  
        temp_dict[f"Booster Number"] = 4 
        temp_dict[f"Fairing Mass"] = 1700 # Using user manual value           
        
    if unique_vehicle_name_list[i] == "Soyuz-2-1B Fregat":
        temp_dict[f"Stage3 Propellant Mass"]  = 5250
        temp_dict[f"Stage2 Stage Mass"]       = 2355
        temp_dict[f"Stage3 Stage Mass"]       = 930
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 1700 # Using user manual value
        
    if unique_vehicle_name_list[i] == "Soyuz-2-1B Fregat-M":
        temp_dict[f"Stage3 Propellant Mass"]  = 5600 
        temp_dict[f"Stage2 Stage Mass"]       = 2355
        temp_dict[f"Stage3 Stage Mass"]       = 980 
        temp_dict[f"Booster Number"] = 4
        temp_dict[f"Fairing Mass"] = 1700 # Using user manual value
    
    if unique_vehicle_name_list[i] == "Vega":
        # Fairing mass:
        #   - https://spaceflight101.com/spacerockets/vega/                                                     540 kg
        #   - http://www.b14643.de/Spacerockets_1/West_Europe/VEGA/Description/Frame.htm                        500 kg
        #   - https://www.mach5lowdown.com/wp-content/uploads/PUG/vega-users-manual_issue-04_april-2014.pdf     540 kg
        temp_dict[f"Stage1 Stage Mass"]      = 8533  # https://www.arianespace.com/wp-content/uploads/2018/05/Vega-Users-Manual_Issue-04_April-2014.pdf Gross mass - prop mass
        temp_dict[f"Stage2 Stage Mass"]      = 2486  # https://www.arianespace.com/wp-content/uploads/2018/05/Vega-Users-Manual_Issue-04_April-2014.pdf Gross mass - prop mass
        temp_dict[f"Stage3 Stage Mass"]      = 1433  # https://www.arianespace.com/wp-content/uploads/2018/05/Vega-Users-Manual_Issue-04_April-2014.pdf Gross mass - prop mass
        temp_dict[f"Stage4 Stage Mass"]      = 688   # https://www.arianespace.com/wp-content/uploads/2018/05/Vega-Users-Manual_Issue-04_April-2014.pdf Dry mass    
        temp_dict[f"Fairing Mass"] = 540 # Using user manual version.
            
    temp_dict["Fairing Mass"] = round(temp_dict["Fairing Mass"],1)
        
    return temp_dict