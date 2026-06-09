import matplotlib.pyplot as plt
import numpy as np
import csv

from .config import WIN_SIZE


def plotEnergies(data:list[dict], fig=None, label=None):
    """
    Function to plot the kinetic, potential, and total energies of the simulation across its frames.
    
    Args
    ----
    - data - The extra_data list from a Simulation object
    - fig - An optional MatPlotLib figure object
    - label - An optional label for the energy lines

    """
    if fig is None:
        print("Creating new figure")
        fig = plt.figure(figsize = (WIN_SIZE+2,WIN_SIZE+1), num="Energy data")
    subplots = fig.get_axes()
    if len(subplots)==0:
        subplots = fig.subplots(nrows = 3, ncols = 1)    
    # ax.grid(True, which='both')

    # Extracts data from sim.extra_data 
    ke, ve, tot_e = [], [], []
    for row in data[1:]: # First frame is invalid
        if "KE" in row: ke.append(float(row["KE"]))
        else:           break
        if "VE" in row: ve.append(float(row["VE"]))
        else:           break

    n_frames = len(ke)
    frames = np.arange(n_frames)

    for i in range(len(ke)):
        tot_e.append(ke[i]+ve[i])

    
    # Axis labelling
    subplots[0].set_xlabel("Frames")
    subplots[0].set_ylabel("Kinetic energy (J)")
    subplots[1].set_xlabel("Frames")
    subplots[1].set_ylabel("Potential energy (J)")
    subplots[2].set_xlabel("Frames")
    subplots[2].set_ylabel("Total energy (J)")

    # Data plots
    subplots[0].plot(ke, label=label)
    subplots[1].plot(ve, label=label)
    subplots[2].plot(tot_e, label=label)

    # Mean energies
    mean_ke = sum(ke)/n_frames
    mean_ve = sum(ve)/n_frames
    mean_tot_e = sum(tot_e)/n_frames
    subplots[0].plot((0,n_frames-1), (mean_ke, mean_ke), "w--")
    subplots[1].plot((0,n_frames-1), (mean_ve, mean_ve), "w--")
    subplots[2].plot((0,n_frames-1), (mean_tot_e, mean_tot_e), "w--")

    # Best fit
    a, b = np.polyfit(frames, ke, 1)
    subplots[0].plot((0,n_frames-1), (b,b+a*(n_frames-1)), "--")
    a, b = np.polyfit(frames, ve, 1)
    subplots[1].plot((0,n_frames-1), (b,b+a*(n_frames-1)), "--")
    a, b = np.polyfit(frames, tot_e, 1)
    subplots[2].plot((0,n_frames-1), (b,b+a*(n_frames-1)), "--")


def compareFromCSVs(file_paths:list[str], labels:list[str]=None):
    """
    Function to compare the energies of two simulations from CSV files.
    
    Args
    ----
    - file_paths - A list of filepaths containing various energies to the first CSV file
    """
    fig = plt.figure(figsize = (WIN_SIZE+2,WIN_SIZE+1), num="Energy data")
    for i,file in enumerate(file_paths):
        with open(file, newline='') as csvfile:
            reader_list = list(csv.DictReader(csvfile))
            # for row in reader[1:]:
            #     ke_i = float(row["VE"])
            #     ve_i = float(row["VE"])
            #     tot_e_i = ve_i + ke_i
            #     ke.append(ke_i)
            #     ve.append(ve_i)
            #     tot_e.append(tot_e_i)
            if labels is not None:
                plotEnergies(reader_list[1::2], fig, labels[i])
            else:
                plotEnergies(reader_list[1::2], fig)
        
    for subplot in fig.get_axes(): subplot.legend()

            