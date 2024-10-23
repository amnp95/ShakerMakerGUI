"""
#############################################################
# This script creates Shaker Maker model for simulations    #
# within the EE-UQ app.                                     #
# This code created by Amin Pakzad and Pedro Arduino based  #
# on the initial code by Jose Abell and Jorge Crempien      #
# date = September 2024                                     #
# ###########################################################
"""

import json
import os

# from shakermaker import shakermaker
# from shakermaker.crustmodel import CrustModel
# from shakermaker.faultsource import FaultSource
# from shakermaker.pointsource import PointSource
# from shakermaker.sl_extensions import DRMBox
# from shakermaker.slw_extensions import DRMHDF5StationListWriter
# from shakermaker.station import Station
# from shakermaker.stationlist import StationList


from shakermaker import shakermaker
from shakermaker.crustmodel import CrustModel
from shakermaker.pointsource import PointSource
from shakermaker.faultsource import FaultSource
from shakermaker.stf_extensions import Discrete
from shakermaker.stf_extensions import Dirac
from shakermaker.slw_extensions import DRMHDF5StationListWriter
from shakermaker.sl_extensions import DRMBox
from shakermaker.station import Station
from shakermaker.stationlist import StationList
from shakermaker.slw_extensions import DRMHDF5StationListWriter
from shakermaker.sl_extensions import DRMBox
from geopy.distance import geodesic

import numpy as np
from mpi4py import MPI


def calculate_distances_with_direction(lat1, lon1, lat2, lon2): 
    '''
    Calculate the distance between two points in the north-south and east-west directions 
    based on their latitudes and longitudes. Uses the geopy library to calculate the distance
    between two points on the Earth's surface.
    '''

    # Original points
    point1 = (lat1, lon1)

    # Calculate north-south distance (latitude changes, longitude constant)
    north_point = (lat2, lon1)
    north_south_distance = geodesic(point1, north_point).kilometers
    north_south_direction = 'north' if lat2 > lat1 else 'south'

    # Calculate east-west distance (longitude changes, latitude constant)
    west_point = (lat1, lon2)
    west_east_distance = geodesic(point1, west_point).kilometers
    west_east_direction = 'east' if lon2 > lon1 else 'west'

    # south is negative
    north_south_distance = (
        -north_south_distance
        if north_south_direction == 'south'
        else north_south_distance
    )
    # west is negative
    west_east_distance = (
        -west_east_distance if west_east_direction == 'west' else west_east_distance
    )

    return north_south_distance, west_east_distance


# ======================================================================================
# Code initialization
# ======================================================================================
# Initialize MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nprocs = comm.Get_size()

# Reading the metadata file
metadata_file = 'metadata.json'
f = open(metadata_file, 'r')  # Manually open the file
try:
    metadata = json.load(f)  # Load JSON data from the file
finally:
    f.close()  # Ensure the file is closed properly, even if an error occurs

# Make results directory if it doesn't exist
if rank == 0:
    if not os.path.exists('results'):  # noqa: PTH110
        os.makedirs('results')  # noqa: PTH103

# if rank == 0:
#     print("Initial information is done")
# Synchronize processes
# comm.barrier()

# Define the source parameters
# For estimating wave arrival windows,
# assume the following maximum and minimum propagation velocities
Vs_min = 3.14  # Minimum shear wave velocity
Vp_max = 8.00  # Maximum primary wave velocity
MINSLIP = 0  # Minimum slip for the fault

if rank == 0:
    print("Initial information is done")
# ======================================================================================
# Shakermaker configuration
# ======================================================================================
_m = 0.001  # meters (ShakerMaker uses kilometers)
dt = metadata['analysisdata']['dt']  # Time step
nfft = metadata['analysisdata']['nfft']  # Number of samples in the record
dk = metadata['analysisdata'][
    'dk'
]  # (Wavelength space discretization) adjust using theory
tb = 0  # How much to "advance" the simulation window... no advance
tmin = metadata['analysisdata']['tmin']  # Time when the final results start
tmax = metadata['analysisdata']['tmax']  # Time when the final results end
delta_h = metadata['analysisdata']['dh'] * _m  # Horizontal distance increment
delta_v_rec = (
    metadata['analysisdata']['delta_v_rec'] * _m
)  # Vertical distance increment for receivers
delta_v_src = (
    metadata['analysisdata']['delta_v_src'] * _m
)  # Vertical distance increment for sources

# nfft = 2048       # Number of samples in the record
# dk = 0.2          # (Wavelength space discretization) adjust using theory
# tb = 0            # How much to "advance" the simulation window... no advance
# tmin = 0.         # Time when the final results start
# tmax = 45.        # Time when the final results end
# delta_h = 40*_m   # Horizontal distance increment
# delta_v_rec = 5.0*_m   # Vertical distance increment for receivers
# delta_v_src = 200*_m   # Vertical distance increment for sources


# options for the simulation
npairs_max = 200000
allow_out_of_bounds = False

if rank == 0:
    print("Configuration is done")

# ======================================================================================
# Loading the crust model
# ======================================================================================
layers = metadata['crustdata']
num_layers = len(layers)
CRUST = CrustModel(num_layers)
for layer in layers:
    name = layer['name']
    vp = layer['vp']
    vs = layer['vs']
    rho = layer['rho']
    thickness = layer['thick']
    Qa = layer['Qa']
    Qb = layer['Qb']
    CRUST.add_layer(thickness, vp, vs, rho, Qa, Qb)
del layers

if rank == 0:
    print("Crust layer loaded")
# ======================================================================================
# Loading the fault
# ======================================================================================
# faultpath  = metadata["faultdata_path"]

# make Fault Directory
fault_dir = 'fault'





# load the faultInfo.json file into faultdata
with open('faultInfo.json') as f:  # noqa: PTH123
    faultdata = json.load(f)
f.close()


faultLat = faultdata['latitude']  # noqa: N816
faultLon = faultdata['longitude']  # noqa: N816
filenames = faultdata['Faultfilenames']
M0 = faultdata['M0']
faultName = faultdata['name']  # noqa: N816
xmean = faultdata['xmean']
ymean = faultdata['ymean']

# if rank == 0:
#     for filename in filenames:
#         os.system(f'{cmd} "{src}/{filename}" "{dst}"')

#     # check that SourceTimeFunction is in the fault file
#     files = os.listdir(fault_dir)
#     if "SourceTimeFunction.py" not in files:
#         raise ValueError("SourceTimeFunction.py not found in the fault file")


# wait for all processes to finish
# comm.barrier()

# import SourceTimeFunction from fault file
from SourceTimeFunction import source_time_function  # noqa: E402
# import numpy as np
# from scipy.integrate import trapezoid
# from shakermaker.stf_extensions import Discrete

# def source_time_function(Tp,Te,Tr,dt,slp):
#     a = 1.
#     b = 100.
#     t = np.arange(0, Tr, dt)
#     Nt = len(t)
#     svf = 0*t

#     i1 = t < Tp
#     svf[i1] = t[i1]/Tp*np.sqrt(a + b/Tp**2)*np.sin(np.pi*t[i1]/(2*Tp))
#     i2 = np.logical_and(t >= Tp, t < Te)
#     svf[i2] = np.sqrt(a + b/t[i2]**2)
#     i3 = t >= Te
#     svf[i3] = np.sqrt(a + b/t[i3]**2)*np.sin(5/3*np.pi*(Tr-t[i3])/Tr)

#     A = np.trapz(svf, dx=dt)

#     svf /= A
#     t = np.arange(Nt)*dt
#     slip_rate_function = svf * slp


#     return Discrete(slip_rate_function, t)

for filename in filenames:
    sources = []

    # read the json fault file
    f = open(f'{filename}')  # noqa: SIM115, PTH123
    faultsources = json.load(f)
    f.close()
    for source in faultsources:
        xsource = source['x']
        ysource = source['y']
        zsource = source['z']
        strike = source['strike']
        dip = source['dip']
        rake = source['rake']
        t0 = source['t0']
        stf = source['stf']
        stf_type = stf['type']
        params = stf['parameters']
        numparams = stf['numParameters']
        stf_func = source_time_function(*params)
        slip = source['slip']
        if slip > MINSLIP :
            sources.append(
                PointSource(
                    [xsource, ysource, zsource], [strike, dip, rake], tt=t0, stf=stf_func
                )
            )
        del xsource, ysource, zsource, strike, dip, rake, t0, stf, stf_type, params, numparams, stf_func

    del faultsources
FAULT = FaultSource(sources, metadata={'name': f'{faultName} M0={M0}'})
if rank == 0:
    print("fault is loaded")
# ======================================================================================
# Loading the stations
# ======================================================================================
stationsType = metadata['stationdata']['stationType']  # noqa: N816
# single station
if stationsType.lower() in ['singlestation', 'single']:
    stationslist = []
    for station in metadata['stationdata']['Singlestations']:
        stationLat = station['latitude']  # noqa: N816
        stationLon = station['longitude']  # noqa: N816
        stationDepth = station['depth']  # noqa: N816
        meta = station['metadata']
        xstation, ystation = calculate_distances_with_direction(
            faultLat, faultLon, stationLat, stationLon
        )
        stationslist.append(
            Station([xstation + xmean, ystation + ymean, stationDepth], metadata=meta)
        )
        del stationLat, stationLon, stationDepth, meta, xstation, ystation

    meta = {'name': metadata['stationdata']['name']}
    STATIONS = StationList(stationslist, metadata=meta)
    del meta

elif stationsType.lower() in ['drmbox', 'drm', 'drm box', 'drm_box', 'drm station']:
    DRMdata = metadata['stationdata']['DRMbox']
    name = DRMdata['name']
    latitude = DRMdata['latitude']
    longitude = DRMdata['longitude']
    depth = DRMdata['Depth']
    Lx = DRMdata['Width X']
    Ly = DRMdata['Width Y']
    Lz = DRMdata['Depth']
    dx = DRMdata['Mesh Size X']
    dy = DRMdata['Mesh Size Y']
    dz = DRMdata['Mesh Size Z']
    nx, ny, nz = int(Lx / dx), int(Ly / dy), int(Lz / dz)
    dx = dx * _m
    dy = dy * _m
    dz = dz * _m
    Lx = Lx * _m
    Ly = Ly * _m
    Lz = Lz * _m
    xstation, ystation = calculate_distances_with_direction(
        faultLat, faultLon, latitude, longitude
    )
    STATIONS = DRMBox(
        [xstation + xmean, ystation + ymean, 0], [nx, ny, nz], [dx, dy, dz], metadata={'name': name}
    )
    # Delete variables after usage
    del DRMdata, name, latitude, longitude, depth
    del Lx, Ly, Lz, dx, dy, dz, nx, ny, nz, xstation, ystation
else:
    raise ValueError(f'Unknown station type: {stationsType}')  # noqa: EM102, TRY003

if rank == 0:
    print("stations are loaded")

del faultLat, faultLon, M0, faultName, filenames, xmean, ymean, metadata_file, metadata
# ======================================================================================
# Create the shakermaker model
# ======================================================================================
model = shakermaker.ShakerMaker(CRUST, FAULT, STATIONS)

if stationsType.lower() in ['drmbox', 'drm', 'drm box', 'drm_box', 'drm station']:
    # creating the pairs
    model.gen_greens_function_database_pairs(
         dt=dt,  # Output time-step
         nfft=nfft,  # N timesteps
         dk=dk,  # wavenumber discretization
         tb=tb,  # Initial zero-padding
         tmin=tmin,
         tmax=tmax,
         smth=1,
         sigma=2,
         verbose=True,
         debugMPI=False,
         showProgress=True,
         store_here='results/greensfunctions_database',
         delta_h=delta_h,
         delta_v_rec=delta_v_rec,
         delta_v_src=delta_v_src,
         npairs_max=npairs_max,
         using_vectorize_manner=True,
         cfactor=0.5,
     )

    # # wait for all processes to finish
    comm.barrier()
    model.run_create_greens_function_database(
        h5_database_name='results/greensfunctions_database',
        dt=dt,  # Output time-step
        nfft=nfft,  # N timesteps
        dk=dk,  # wavenumber discretization
        tb=tb,  # Initial zero-padding
        tmin=tmin,
        tmax=tmax,
        smth=1,
        sigma=2,
        verbose=False,
        debugMPI=False,
        showProgress=True,
    )

    # wait for all processes to finish
    comm.barrier()
    writer = DRMHDF5StationListWriter('results/DRMLoad.h5drm')
    model.run_faster(
        h5_database_name='results/greensfunctions_database',
        dt=dt,  # Output time-step
        nfft=nfft,  # N timesteps
        dk=dk,  # wavenumber discretization
        tb=tb,  # Initial zero-padding
        tmin=tmin,
        tmax=tmax,
        smth=1,
        sigma=2,
        verbose=False,
        debugMPI=False,
        showProgress=True,
        writer=writer,
        delta_h=delta_h,
        delta_v_rec=delta_v_rec,
        delta_v_src=delta_v_src,
        allow_out_of_bounds=allow_out_of_bounds,
    )


# single station
if stationsType.lower() in ['singlestation', 'single']:
    if rank == 0:
        print(5)
    model.run(
        dt=dt,  # Output time-step
        nfft=nfft,  # N timesteps
        dk=dk,  # wavenumber discretization
        tb=tb,  # Initial zero-padding
        tmin=tmin,
        tmax=tmax,
        smth=1,
        sigma=2,
        verbose=False,
        debugMPI=False,
        showProgress=True,
    )
    if rank == 0:
        for i, s in enumerate(stationslist):
            output_filename = f'results/station{i+1}.npz'
            s.save(output_filename)