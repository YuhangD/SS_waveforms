import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator
from obspy.core import read
from pathlib import Path

def cut_waveforms(data, half_window_length, half_cut_length, sample_rate):
    n_data = len(data)
    l1 = int(n_data / 2) - round(half_window_length * sample_rate)
    l2 = int(n_data / 2) + round(half_window_length * sample_rate)

    idx = np.argmax(np.abs(data[l1:l2+1]))

    cut_start = l1 + idx - round(half_cut_length * sample_rate)
    cut_end = l1 + idx + round(half_cut_length * sample_rate) + 1
    return data[cut_start:cut_end] / data[round(l1 + idx)]

def lookup_arrival_time(tr, phase):
    table_name = f"./aux/{phase}_traveltime.npz"
    if not Path(table_name).exists():
        raise FileNotFoundError(f"Travel time table {table_name} not found.")
    data = np.load(table_name)
    interpolator = RegularGridInterpolator((data['gcarcs'][:], data['depths'][:]), data['timetable'][:, :])
    dp = tr.stats.sac['evdp']
    if dp > 1000:
        dp /= 1000
    gc = tr.stats.sac['gcarc']
    return interpolator((gc, dp))

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python plot_SSprecursors.py sac_file")
  
    
    sac_path = Path(sys.argv[1])
    tr = read(sac_path)[0] 
    tr.filter('bandpass', freqmin=0.02, freqmax=0.1, corners=4, zerophase=True)    
    tr.detrend('linear')
    tr.taper(max_percentage=0.05, type='cosine')
    sample_rate = 1
    tr.resample(sample_rate)
    
    SS_arr = lookup_arrival_time(tr, 'SS')
    S410S_arr = lookup_arrival_time(tr, 'S^410S')
    S660S_arr = lookup_arrival_time(tr, 'S^660S')
    
    half_window_length = 50 # in seconds
    half_cut_length = 400 # in seconds
    times = np.arange(-half_cut_length, half_cut_length + 1) 
    data_cut = cut_waveforms(tr.data, half_window_length, half_cut_length, sample_rate)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(times, data_cut, color='k', lw=1.5, zorder=1)
    ax.axvline(0, lw =2, color = 'r', zorder=0)
    ax.axvline(S410S_arr - SS_arr, lw =2, color = 'b', zorder=0)
    ax.axvline(S660S_arr - SS_arr, lw =2, color = 'cyan', zorder=0)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Normalized Amplitude')   
    ax.set_title(f"SS Precursors for {tr.stats.network}.{tr.stats.station} at {tr.stats.starttime}")
    ax.set_xlim([-half_cut_length, half_cut_length])
    ax.set_ylim([-1.5, 1.5])
    plt.show()

if __name__ == "__main__":
    main()
