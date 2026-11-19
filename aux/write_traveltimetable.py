import numpy as np
from obspy.taup import TauPyModel

model = TauPyModel('prem')

def gen_traveltime(gcarcs, depths, phase:list):
    # if phase[0].lower() == 'p':
    #     phase = ['p','P']
    # elif phase[0].lower() =='s':
    #     phase = ['s','S']

    timetable = np.empty((len(gcarcs), len(depths)))
    for i in range(len(gcarcs)):
        for j in range(len(depths)):
            arrivals = model.get_travel_times(distance_in_degree = gcarcs[i],
                                              source_depth_in_km = depths[j],
                                              phase_list = phase)
            if not len(arrivals)==0:
                timetable[i][j] = arrivals[0].time
    return timetable


gcarcs = np.arange(60, 180,1)
depths = np.arange(0, 76, 1)
for phase in ["SS","S","S^410S","S^660S"]:
    timetable = gen_traveltime(gcarcs, depths, [phase])
    outfile_name = f'{phase}_traveltime.npz'
    np.savez(outfile_name, gcarcs = gcarcs, depths= depths, timetable = timetable )
    print(f"Generated travel time table of {phase}, saved to {outfile_name}")            