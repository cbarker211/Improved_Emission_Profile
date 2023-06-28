###############################
# Notes on Emission Indices
###############################

1) General Routine:

        Calculate emission indices of individual pollutants:
        These are given in g pollutant per kg propellant.
        Methodology is from https://crp.trb.org/uat/acrp0356/wp-content/uploads/sites/26/2021/07/ACRP-Web-Only-51-Commercial-Space-Vehicle-Emissions-Modeling.pdf
        General structure is this for each species:
              0) Check if species is emitted
              1) calculate vertical profile of emission indices (g(xx) / kg(propellant)) using function self.calculate_xx_ei
              2) multiply propellant mass by (0.01 * ei * vertical mass profile) to get mass vertical profile (in g)
              3) add vertical mass profile (in g) to sanity check total
              3) convert vertical mass profile from kg to kgm2s and add to output variable

2) Species Specific Information

        NOx:
        In 2019, only Virgin Galactic space plane has primary NOx emissions of 4g/kg.
        Now in 2020, updated so all propellants produce secondary NOx, but only N-containing fuels (hypergolic/solid) produce primary NOx.
        NOx emissions calculate using the same of booster and stage 1 propellant mass calculated earlier

        H2O:
        E_f(H2O) = E_p(H2O) + E_P(H)*MW_H2O/MW_H + E_p(H2)*MW_H2O/MW_H2 + E_p(OH) - James 2021
        No H or OH primary emissions, so ignore that term (Would be present for Starship (Methane) and Minotaur I (APCP PBAN)).
        E_f(H2O) = E_p(H2O) + E_p(H2) * MW_H2O / MW_H2

        Alumina:   
        Also only represent 8% of alumina mass, as this is the portion
        that by mass that is estimated to contribute to ozone loss,
        according to Schmid et al. (2003), https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2002JD002486:
        self.rocket_al = self.rocket_al*8e-2
        
        Chlorine:
        According to James21, this contains a lot of uncertainty, so could combine into a single chlorine index?

#######################
# Failed Launches
#######################                                        

F01 - 09/02/2020 Simorgh (Iran)
    First stage operated for 475s correctly, but second stage failed to deploy payload succesfully...
    Satellite reached 540 km apogee but only reached 6,400 m/s, just short of 7,400 m/s orbital velocity...
    For the purposes of launch emissions, can include as normal.

F02 - 16/03/2020 Long March 7A (China) - 3 stages, 4 boosters
    https://web.archive.org/web/20220411235209/http://www.spacelaunchreport.com/cz5.html
        A video posted online later showed a possible failure during the early moments of the second stage burn...
    https://en.wikipedia.org/wiki/List_of_Long_March_launches_(2020%E2%80%932029)#2020
        Vehicle disintegrated at first stage separation due to booster LOX pressurization failure leading to engine shutdown and loss of control...
    https://www.nasaspaceflight.com/2020/03/long-march-7a-fails-xinjishu-yanzheng-6/ 
        The problem seems to have surfaced when the 3rd stage was to operate...
    Only LM7A this year, so Stage 2+3 propellant mass have been set to zero in pull_from_DISCOSweb.

F03 - 09/04/2020 Long March 3B/E (China) - 8 launches in 2020, this is the only failure.
    https://www.nasaspaceflight.com/2020/04/long-march-3b-launches-indonesian-satellite/
        Reportedly failed during third stage flight ... Reports from China noting an issue with the Long March’s third stage... 
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        Failure during first Stage 3 burn.           
    https://en.wikipedia.org/wiki/List_of_Long_March_launches_(2020%E2%80%932029)#2020
        Third stage engine failed to ignite.
    For the purposes of this script which only includes B+1S+2S, can treat as normal.

F04 - 25/05/2020 LauncherOne
    https://en.wikipedia.org/wiki/LauncherOne#Launch_outcomes
        Launch failure after successful release and ignition of the NewtonThree engines on the first stage. A high-pressure propellant line broke causing liquid oxygen to stop flowing into the engine.
    https://spacenews.com/virgin-orbit-identifies-cause-of-engine-shutdown-on-first-launcherone-flight/
        Went well until several seconds after the ignition of the NewtonThree engine that powers the rocket’s first stage...
    https://spaceflightnow.com/2020/07/25/virgin-orbit-traces-cause-of-launcherone-test-flight-mishap-to-propellant-line/
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        Failed shortly after Stg 1 ignition after drop from Cosmic Girl SW of Long Beach, CA. Launch Demo planned to LEO including two Stg 2 burns.
    So stage 1 only worked for several seconds. Ignore for now but speak to Eloise.

F05 - 04/07/2020 Electron (Curie)
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        Second stage failure.     
    https://www.rocketlabusa.com/updates/rocket-lab-mission-fails-to-reach-orbit/
        Following a successful lift-off, first stage burn, and stage separation, Rocket Lab experienced an anomaly...
    Ignore second stage.

F06 - 10/07/2020 Kuaizhou-11
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        Inaugural launch failure, sometime after Stg 2 separation. 
    https://spaceflightnow.com/2020/07/10/new-chinese-satellite-launcher-fails-on-first-flight/
        The Kuaizhou 11 appeared to fly normally through the burn of its first stage motor.
    https://web.archive.org/web/20220406013817/http://www.spacelaunchreport.com/kz11.html
        The first minutes of flight look nominal through second stage separation, but an unknown failure occurred before orbit could be attained.
    https://space.skyrocket.de/doc_lau/kuaizhou-11.htm
        stage 3 failed to ignite
    If error occured after second-stage separation, then can include emissions as normal.

F07 - 12/09/2020 Astra Rocket 3
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        Oscillations caused abort cutoff after about 22 seconds. Fell to Earth not far from launch site.
    https://web.archive.org/web/20220411235206/http://www.spacelaunchreport.com/astra.html
        The rocket rose for slightly more than 20 seconds before, "a commanded shutdown of the engines by the flight safety system".
    https://en.wikipedia.org/wiki/List_of_Astra_rocket_launches
        30 seconds after lift off engines were shut down by the range safety officer.
    Propellant for Astra is already approximated using Electron (Curie). For Electron, altitude is ~ 0.9 km at 22s (https://www.youtube.com/watch?v=af-PplDIkbc, https://www.youtube.com/watch?v=VRfm6RGVHf8)
    So will only output emissions up to 0.9 km.

F08 - 12/09/2020 Kuaizhou-1A
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        Possible upper stage failure.
    https://web.archive.org/web/20220406013827/http://www.spacelaunchreport.com/kz.html
        Possible liquid upper stage failure.
    https://spaceflightnow.com/2020/09/12/chinese-smallsat-launcher-fails/
        Xinhua said the launch vehicle “failed to enter the preset orbit” after “abnormal performance was identified during the rocket’s flight.”
    https://space.skyrocket.de/doc_lau/kuaizhou-1.htm
        Stage 4 failure
    Failure occured in upper stage, so can include the emissions as normal.

F09 - 17/11/2020 Vega
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        AVUM fourth stage tumbled out of control at first ignition.  Two TVC cables inverted.
    https://en.wikipedia.org/wiki/List_of_Vega_launches
        After ignition of the AVUM upper stage, a trajectory deviation caused failure.
    https://space.skyrocket.de/doc_lau_fam/vega.htm
        AVUM stage TVC cabeling error
    Failure occured in upper stage, so can include the emissions as normal.
    
F10 - 15/12/2020 Astra Rocket 3
    https://en.wikipedia.org/wiki/List_of_Astra_rocket_launches
        First Astra rocket to pass the Kármán Line and reach its target orbital altitude of 390 kilometers. 
        Narrowly failed to reach stable orbit due to issues with the upper stage propellant mixture ratio.
    https://web.archive.org/web/20220411235210/http://www.spacelaunchreport.com/log2020.html
        Second stage cutoff 15-20 seconds short of orbit.
    https://web.archive.org/web/20220411235206/http://www.spacelaunchreport.com/astra.html
        First stage, staging and second stage ignition succeeded.  Stage 2 depleted propellant 15-20 seconds early, falling short of orbit.
    In this case, the early SECO would have likely been well above GC, so can treat as normal.
    
F11 - 03/12/2020 Chang'e 5 SSQ (Ascent Stage)
    Moon launch, don't need to include.

