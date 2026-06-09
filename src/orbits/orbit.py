from __future__ import annotations
import json
import csv
import matplotlib.animation as an
import matplotlib.pyplot as plt
import numpy as np
import time

from .celestials import Celestial
from .progress_bar import ProgressBar
from .config import *   # Constants/file paths
from .energy_comparison import plotEnergies


class Simulation(object):
    celestials_map:dict[str, Celestial]         # Keeping both a dictonary and list of celestials for easy access, to avoid iterating over a dictionary
    celestials:list[Celestial]
    celestials_positions:list[list[np.ndarray]] # Used to store positions of celestials over multiple frames
    extra_data:list[dict]                       # Used to store extra data from simulation, e.g. kinetic energy, potential energy, etc.
    planet_alignment_frames:list
    frame_counter:int
    n_frames:int
    prev_time:float     # Used to calculate elapsed time between frames
    timescale:float     # Used to scale real time to simulation time, e.g. 1.0 means 1 second of simulation time per second of real time
    fps:float
    ax:plt.Axes
    prog_bar:ProgressBar
    
    MODE_ACCURATE = 1
    MODE_REAL_TIME = 2

    def __init__(self, data, ax:plt.Axes, text):
        """
        Simulation
        =====
        This class handles numerical computations and data storage for a system of `Celestial` objects, 
        simulating their motion over time. It stores the positions of celestials across each frame, including extra
        data such as kinetic and potential energy. It is reliant on an `ax` object to handle rendering aspects.
        
        Args
        ----------------------------
        - data - a JSON file object containing all required parameters. These are listed below.\n
        - ax - a Matplotlib Axes object to put planets on. This can be created with `Simulation.createSimulationAxes()`\n
        - text - a Matplotlib text object to display simulation values onto. This can be created with `Simulation.createSimulationText()`\n

        Usage
        ----------------------------
        The main function that handles the simulation is the `simulate()` method. This function should be called on any frame that needs
        to be simulated, and can be passed into MatplotLib's `an.FuncAnimation` to handle the rendering of planets in real time.
        Alternatively, `simulate()` can be used to preprocess data, or simply carry out calculations, which can later be animated using
        the `animate()` method.

        Example (with existing ax, text, fig, MatplotLib objects): 
        >>> with open(file_path) as json_data:
        >>>     data = json.load(json_data)                
        >>> sim = Simulation(data, ax, text)
        >>> anim = an.FuncAnimation(fig, sim.simulate, frames = 5000, interval = 1.0)

        JSON data
        ----------------------------
        The loaded JSON file requires 6 main parameters in order for the simulation to run
        - timescale - number of seconds passing in the simulation for each real life second.
        - fps - number of frames to be computed and rendered (although this is limited to around 20 by MatplotLib) for each simulation second.
        - n_frames - number of frames to run the simulation for.
        - axes_range - domain covered by the axis in the MatplotLib window.
        - G - gravitational constant.
        - celestials - array of celestials. Structuring celestials is described in celestials.py.
        
        Extra
        ----------------------------
        - `c1` and `c2` are always used to denote Celestial objects.
        - The first frame in the simulation data, and the first orbit of a planet should usually be discarded for gathering results
        - The actual "timestep" is given by `self.timescale`/`self.fps`
        """
        
        required_keys = ["timescale", "fps", "n_frames", "axes_range", "G", "celestials"]
        if not all(map(lambda key: key in data, required_keys)):    # Checks all required keys are inputed, although not their values
            raise KeyError("Not all required parameters have been added to the file.")

        # Generates celestials from parameters from json file. Uses celestials to run simulation.  
        if "radius_sf" in data: radius_sf = data["radius_sf"]
        else: radius_sf = 1.0
        if "star_sf" in data: star_sf = data["star_sf"]
        else: star_sf = 1.0
        self.celestials_map = Simulation.loadCelestials(ax, data["celestials"], radius_sf, star_sf)
        self.frame_counter = 0
        self.ax = ax
        self.text = text
        self.prev_time = time.time()
        self.celestials_map = self.celestials_map
        self.celestials = list(self.celestials_map.values())
        self.celestials_positions = [[c.position[:] for c in self.celestials]]
        self.prog_bar = ProgressBar()
        self.planet_alignment_frames = []
        self.extra_data = [{"KE":0.0, "VE":0.0, "alignment":False}]

        """Loads required data from the simulation"""
        self.fps = float(data["fps"])
        self.timescale = float(data["timescale"])
        self.n_frames = int(data["n_frames"])        # Number of frames to run simulation for
        g_const = float(data["G"])          # All celestial objects should use the same constant
        for c1 in self.celestials:
            c1.g = g_const

    """Calculation functions"""
    def getSystemKE(self)->float:
        """Returns the total kinetic energy within the system."""
        tot = 0
        for c1 in self.celestials: # Sums kinetic energy for every
            tot+=c1.getKE()
        return tot

    def getSystemVE(self)->float:
        """Returns the total potential energy in the system."""
        tot = 0
        for i, c1 in enumerate(self.celestials):
            for c2 in self.celestials[i:]: # This avoids double counting
                if c1 != c2:
                    tot += c1.getVE(c2)
        return tot

    def checkAlignment(self, origin_celestial_name:str, threshold:float|int=5.0)->bool:
        """
        Checks if celestials are aligned relative to a given celestial with name `origin_celestial_name`.
        
        Note: the `threshold` parameter is in degrees
        """
        n_alignment_celestials = sum([c1.check_alignment for c1 in self.celestials])
        if n_alignment_celestials<3: return False # If there are less than 3 planets, they are always aligned, so this check isn't needed

        # Stores all the angles relative to the x-axis in a list, to check if all angles are within a range lower than the threshold
        angles = []
        c1 = self.celestials_map[origin_celestial_name] # Celestial treated as alignment origin
        for name, c2 in self.celestials_map.items():
            if name!=origin_celestial_name and c2.check_alignment: # Can't check alignment with itself, or planets that shouldn't be considered
                dist_vec = c2.position-c1.position
                if dist_vec[0]==0: angle = np.pi/2 * (2*(dist_vec[1]>0)-1)  # pi/2 if y>0, -pi/2 if y<0, when x=0
                elif dist_vec[1]==0: angle = np.pi * (dist_vec[0]<0)        # 0 if x>0, pi if x<0, when y=0
                else: 
                    angle = np.arctan(dist_vec[1]/dist_vec[0])    # Normal case
                    if dist_vec[0]<0:                           # Left quadrants cases
                        if dist_vec[1]>0:   angle += np.pi
                        else:               angle -= np.pi
                angles.append(angle)

        rad_thr = np.deg2rad(threshold)
        # Calculates range and if it less than the threshold, then planets are aligned. 
        align_condition = max(angles)-min(angles)<rad_thr

        # Handles edge case where planets could all be aligned along the x-axis, but negative angles would make 
        # the normal condition not detect the alignment
        angles = [a + 2*np.pi*(a<0) for a in angles]
        align_edge_condition = max(angles)-min(angles)<rad_thr

        if align_condition or align_edge_condition: return True
        return False

    def framesToYears(self, n_frames:int)->float:
        """Returns the number of Earth years correspondding to a given number of simulation frames."""
        return n_frames*self.timescale/(86400*365*self.fps)

    """Numerical integration methods"""
    def _euler_cromer(c1:Celestial, celestials:list[Celestial], dt:float)->None:
        a_vec = c1.getTotAcc(celestials)
        c1.velocity += dt*a_vec             # v(t+dt) = v(t) + a(t)dt
        c1.position += dt*c1.velocity       # r(t+dt) = r(t) + v(t+dt)dt
        c1.prev_acceleration = c1.acceleration
        c1.acceleration = a_vec
    def _euler(c1:Celestial, celestials:list[Celestial], dt:float)->None:
        a_vec = c1.getTotAcc(celestials)
        c1.position += dt*c1.velocity       # r(t+dt) = r(t) + v(t)dt
        c1.velocity += dt*a_vec             # v(t+dt) = v(t) + a(t)dt
        c1.prev_acceleration = c1.acceleration
        c1.acceleration = a_vec
    # See Beeman integration (https://en.wikipedia.org/wiki/Beeman%27s_algorithm) for more info on algorithm used
    def _beeman(c1:Celestial, celestials:list[Celestial], dt:float)->None:
        c1.position += (c1.velocity + (1/6)*(4*c1.acceleration - c1.prev_acceleration)*dt)*dt   # Predicted position
        a_vec = c1.getTotAcc(celestials)                                                        # Acceleration from new position
        c1.velocity += (1/6)*(2*a_vec + 5*c1.acceleration - c1.prev_acceleration)*dt            # Corrected velocity
        c1.prev_acceleration = c1.acceleration
        c1.acceleration = a_vec
    def _verlet(c1:Celestial, celestials:list[Celestial], dt:float)->None:
        c1.position += (c1.velocity + 0.5*c1.acceleration*dt)*dt
        a_vec = c1.getTotAcc(celestials)
        c1.velocity +=  0.5*(c1.acceleration+a_vec)
        c1.prev_acceleration = c1.acceleration
        c1.acceleration = a_vec

    """Main simulation and display functions"""
    def _simIteration(self, dt:float, frame:int, method:callable)->None:
        """Computes a single iteration of the simulation, updating the values of the celestials assigned to this simulation.
        
        This function iterates over pairs of planets, applying the gravitational attraction, and doing numerical integration 
        to update the planets' positions. The type of numerical integration is specified by the `method` parameter.
        """
        # Iterates over celestials, carrying out required computations to move onto the next frame
        for c1 in self.celestials:
            if frame==0 and method==Simulation._beeman: # Verlet algorithm required to start Beeman algorithm
                method = Simulation._verlet

            # Calculate new position and velocity of celestial 1    
            method(c1, self.celestials, dt)
            
            # For orbit time calculations
            # Note: this works under the assumption that the orbit is across a star centered at the origin
            # For this to work with moons and planets the "orbits" attribute could be used 
            if c1.position[1]>0: # Checks the number of frames passed each time the x-axis is crossed a second time
                if c1._below_0:
                    c1.orbital_period = self.framesToYears(frame - c1._orbit_start_frame)  # Orbital period in Earth years
                    c1._below_0 = False
                    c1._orbit_start_frame = frame
                    c1.orbit_times.append(c1.orbital_period)
            else: c1._below_0 = True

    def simulate(self, i:int, sim_mode:int=0, store_data:bool=True, method:callable=_beeman,**kwargs)->list|None:
        """
        This function simulates and stores data of planets' energies and positions for the current frame `i`.

        This function can either be called on every frame of the animation by MatplotLib's FuncAnimation, 
        or used to preprocess data.
        
        It returns an array with the ax object to tell MatplotLib the objects that need to be redrawn.
        """
        real_fps = self.fps
        k_energy, v_energy = 0.0, 0.0

        if "origin_celestial" in kwargs: origin_celestial = kwargs["origin_celestial"]
        else: origin_celestial = "sun"

        match sim_mode:
            case Simulation.MODE_ACCURATE:
                self._simIteration(self.timescale/self.fps, i, method)

            # This mode is used to simulate the system in real time, using the actual time between frames.
            # Do not use to get experimaental data as it is intended for smooth real time animations without frame drops.
            case Simulation.MODE_REAL_TIME: 
                current_time = time.time()
                real_dt = current_time-self.prev_time
                dt = self.timescale*real_dt # Calculates change in simulation time between frames
                
                self._simIteration(dt, i, method)
                
                if real_dt!=-0: real_fps = real_dt**-1
                else:           real_fps = 0
                self.prev_time = current_time

        # Calculate energies and display them on plot
        k_energy = self.getSystemKE()
        v_energy = self.getSystemVE()
        temp_text = f"Frame: {i}\nKinetic energy: {k_energy:.5}J\nPotential energy: {v_energy:.5}J\n"
        temp_text2 = f"Timestep: {self.framesToYears(1)*365:.1f} days"
        self.text.set_text(temp_text+temp_text2)

        # Store data from simulation for later use
        extra_data = {"KE":k_energy, "VE":v_energy}
        if "alignment" in kwargs:
            alignment = self.checkAlignment(origin_celestial, kwargs["alignment"])
            if alignment and self.extra_data[-1]["alignment"] == False: # Print alignment message the first time frame that planets align
                self.planet_alignment_frames.append(i)
            extra_data["alignment"] = alignment

        if "loading_bar" in kwargs and kwargs["loading_bar"]: # For showing progress when dealing with large numbers of frames
            if i%int(self.n_frames/100)==0:
                self.prog_bar.set_percent(100*i/self.n_frames+1, show_text=True)

        if store_data:
            self.celestials_positions.append([np.array(c.position) for c in self.celestials])
        self.extra_data.append(extra_data)
        self.frame_counter += 1
        return [self.ax] # This is required for matplotlib, and useful for performance reasons as only the ax object is updated
            
    def animate(self, i:int, speed:int=1, start_frame:int=0)->list: 
        """Function to call when using a preprocessed simulation. It is intended to be called on every frame of the animation by MatplotLib's 
        FuncAnimation."""
        i = int(i*speed)+start_frame # Speeds up the animation by skipping frames
        if i>self.n_frames: return [self.ax]
        for j, c in enumerate(self.celestials): 
            # Celestials are always accessed in the same order so their positions can be accessed in the same order they're added
            c.patch.center = self.celestials_positions[i][j] 
        temp_text = f"Frame: {i}\nKinetic energy: {self.extra_data[i]['KE']:.5}J\nPotential energy: {self.extra_data[i]['VE']:.5}J\n"
        temp_text2 = f"Timestep: {self.framesToYears(1)*365:.1f} days"
        self.text.set_text(temp_text+temp_text2)
        return [self.ax] # Returns the artist object to be updated (this is for performance reasons, and not in fact needed)

    """Setup helper functions"""
    def addStars(ax:plt.Axes,axes_range:float,zorder:int=-1000)->None:
        """Adds aethstetic stars to a maplotlib Axes object."""
        for _ in range(100):
            arr = (np.random.random((100,2))*2-1)*axes_range                # Random star scattering
        ax.scatter(arr[:,0],arr[:,1], c="#CCCCCC", s=0.1, zorder=zorder)    # Creates scatter plot of white dots

    def loadCelestials(ax:plt.Axes, celestials_data:dict, radius_sf:float=1.0, star_sf:float=1.0, star_name:str="sun")->dict: 
        """Loads and returns a new list of celestial objects from a `celestials_data` JSON object, constructing each celestial from data.
        `radius_sf` and `star_sf` make the planets and star more visible, as their radii are scaled.
        """
        celestials_map = {}
        if len(celestials_data)==0: raise ValueError("Celestial data can't be empty.")
        for celestial in celestials_data.items():
            name = celestial[0]
            required_keys = ["radius", "position", "mass", "radius"]
            # Some keys are required for planets. If there are missing entries, then the planet will be invalid.
            # This can be tested by checking if all the key in required_keys appear in keys
            if not all(map(lambda key: key in celestial[1], required_keys)):    
                print(celestial[1])
                raise RuntimeError(f"The celestial '{name}' is missing required parameters.")
            data = celestial[1]
            if name != star_name: # Prevents sun from getting scaled as otherwise it covers the whole screen
                data["radius"] *= radius_sf
            else:
                data["radius"] *= star_sf
            
            # Unpacks celestial data into parameters for a new celestial object 
            required_args = list(data.values())[:Celestial.JSON_ARGS]
            optional_args = dict(list(data.items())[Celestial.JSON_ARGS:])
            try:
                celestials_map[name] = Celestial(*required_args, ax, **optional_args) 
            except ValueError as e:
                raise RuntimeError(f"An error occured when loading celestial {name}: {e}")

        # The loop must be run a second time separately to ensure that celestial are able to orbit each others, 
        # as they may not have been instantiates in a predefined order. This loop sets a relative orbit for each planet
        # containing the "orbits" key
        for celestial in celestials_data.items():
            data = celestial[1]
            if "orbits" in data:
                parent_planet = celestials_map[data["orbits"]]
                name = celestial[0]
                celestials_map[name].setRelativeOrbit(parent_planet)
        return celestials_map

    def createSimulationAxes(axes_range:float)->plt.Axes:
        """Returns a new ax object with required parameters for the simulation."""
        ax = plt.axes([0.0, 0.0, 1.0, 1.0], xlim=(-axes_range, axes_range), ylim=(-axes_range, axes_range)) # Creates plot axes that provide the canvas to the simulation
        ax.set_aspect("equal") # Enforces square zooming so that planets don't get stretched into ellipses
        ax.xaxis.set_units("m")
        ax.yaxis.set_units("m")
        return ax
    
    def createSimulationText(ax:plt.Axes, axes_range:float)->plt.Text:
        """Returns matplotlib text object to display information about the simulation."""
        return ax.text(-0.9*axes_range,-0.9*axes_range, "KE at frame 0: loading\nfps: loading", fontsize=8)

    def reset(self, ax, celestials_data:list)->None:
        """Resets stored simulation values to instantiation values.
        This creates new celestials and requires a new `ax` object.
        """
        self.ax = ax
        self.extra_data = [{"KE":0.0, "VE":0.0, "alignment":False}]
        for c1 in self.celestials:
            c1.patch.remove()
        new_celestials_map = Simulation.loadCelestials(self.ax, celestials_data)
        self.celestials_map = new_celestials_map
        self.celestials = list(new_celestials_map.values())
        self.celestials_positions = [c.position[:] for c in self.celestials]

    """I/O and file storage"""
    def printCelestialOrbitalPeriods(self)->None:
        """Prints the orbital periods for all celestials in the simulation."""
        print()
        for name, c1 in self.celestials_map.items():
            if len(c1.orbit_times)!=0: orbital_period = sum(c1.orbit_times)/len(c1.orbit_times)
            else: orbital_period = "NaN"
            # print(f"{name} orbital period: {orbital_period} Earth years.") 
            print(f"{name} orbital period: {orbital_period} Earth years.") 

    def printAlignments(self)->None:
        """Prints the frames on which planets are aligned"""
        time_years = [(self.framesToYears(frame)) for frame in self.planet_alignment_frames]
        alignment_planets = [name for name,c1 in self.celestials_map.items() if c1.check_alignment]
        print(f"\nPlanet alignments detected on frames: {self.planet_alignment_frames} for planets: {alignment_planets}\nIn Earth years: {time_years}")        

    def saveCSV(self, path=csv_out_path)->None:
        """Stores results data to a csv file in the 'results' folder."""
        with open(path, "w") as file:
            headers = self.extra_data[0].keys()
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(self.extra_data)

    def saveVideo(self, anim_func, path=video_out_path)->None:
        """Saves a video of the animation. However, it requires ffmpeg."""
        vid_writer = an.FFMpegWriter(fps=60)
        anim_func.save(path, vid_writer) 

def simSetup( # There are many possible parameters that can be used 
        display_window = True,
        energy_plot = True,
        add_stars = True,
        fp = data_ss_path,
        save_video = False,
        save_CSV = False,
        orbital_periods = True,
        alignment = True,
        loading_bar = True,
        method_name = "Beeman",
        alignment_thr = 10.0,
        mode = 1, 
        speed = 1.0,
        data_out_path = csv_out_path,
        vid_out_path = video_out_path,
        **kwargs
        ):  
    """This procedure handles every aspect of computing and rendering the simulation, given optional parameters parameters. It links together
    MatplotLib with the Simulation class, and provides calls to optional functions to handle features such as data storage.""
    
    It makes the class usable for users outside of being a reusable class. 
    """

    match method_name:
        case "Beeman": method = Simulation._beeman
        case "Euler": method = Simulation._euler
        case "Euler-Cromer": method = Simulation._euler_cromer

    # Parameters loaded from JSON file
    with open(fp) as json_data_file:
        data = json.load(json_data_file)
    axes_range = float(data["axes_range"]) 

    plt.style.use('dark_background')
    fig = plt.figure(figsize=[WIN_SIZE,WIN_SIZE], num="Orbits")     # Creates matplotib window. This is kept outside of the Simulation class for more control
    ax = Simulation.createSimulationAxes(axes_range)                # Creates axes object to hold/display celestials 
    text = Simulation.createSimulationText(ax, axes_range)          # Creates text object to diplay useful data within main window
    if add_stars: Simulation.addStars(ax, axes_range)    

    try:
        sim = Simulation(data,ax,text)
    except Exception as e:
        print(f"An error occured when creating the Simulation object: {e}")
        return

    match mode: # Main switch that handles preprocessing or real time simulating
        case Simulation.MODE_ACCURATE:
            print()
            for i in range(sim.n_frames):
                sim.simulate(i, 
                            sim_mode=Simulation.MODE_ACCURATE, 
                            store_data=True, #! This needs to be set to true if animating 
                            method=method,
                            file_write=save_CSV, 
                            alignment=alignment_thr,
                            loading_bar=loading_bar) # Initialises simulation

            if orbital_periods: sim.printCelestialOrbitalPeriods()
            if alignment: sim.printAlignments()
            anim_func = lambda i: sim.animate(i, speed=speed, start_frame=0)
        case Simulation.MODE_REAL_TIME: # Not used
            anim_func = lambda i: sim.simulate(i, 
                                               sim_mode=Simulation.MODE_ACCURATE, 
                                               check_alignment=alignment, 
                                               method=method,
                                               file_write=save_CSV, 
                                               alignment=alignment_thr,
                                               loading_bar=loading_bar)
        case _:
            raise ValueError("Invalid mode chosen.")

    if display_window:
        # An object must be stored even if not accessed because it is used by Matplotlib
        anim = an.FuncAnimation(fig, 
                                anim_func,              # <--- Function repeatedly called on every frame update
                                frames = sim.n_frames,  # Frames to run the simulation for
                                interval = 1.0,         # time between frames in milliseconds, this is added to the simulation time as extra delay
                                repeat = False,
                                blit = True)
    
    # Extra options
    if energy_plot and mode==Simulation.MODE_ACCURATE: # Plots energies if the simulation is not in real time
        plotEnergies(sim.extra_data)
    if display_window: plt.show()
    if save_video: sim.saveVideo(anim, vid_out_path)
    if save_CSV: sim.saveCSV(data_out_path)


def test():
    with open(data_test_path) as json_test_data:
        test_data = json.load(json_test_data)
    
    axes_range = test_data["axes_range"]

    fig, ax = plt.subplots()
    ax.set_xlim(-axes_range,axes_range)   
    ax.set_ylim(-axes_range,axes_range)
    text = plt.text(-5e11,0.0,"test")

    
    sim = Simulation(data=test_data, ax=ax, text=text)
    print(f"System kinetic energy: {sim.getSystemKE()}J")
    print(f"System potential energy: {sim.getSystemVE()}J")

    mars = sim.celestials_map["mars"]
    print(f"Mars velocity: {mars.velocity}")
    sim.simulate(1,Simulation.MODE_ACCURATE,store_data=True,method=Simulation._euler)
    print(f"Mars velocity after 1 iteration: {sim.celestials_map['mars'].velocity}")

    print(f"Planetary alignment: {sim.checkAlignment('sun', 5.0)}")
    plt.show()

if __name__=="__main__":
    test()