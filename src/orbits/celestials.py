from __future__ import annotations
import matplotlib.pyplot as plt
import numpy as np


class Celestial(object):
    # Variables that need to be assigned at runtime
    position:np.ndarray
    velocity:np.ndarray
    acceleration:np.ndarray
    prev_acceleration:np.ndarray # Required for Beeman algorithm
    mass:float
    radius:float
    g:float
    colour:str

    # Variables for orbital period calculations
    _below_0:bool
    _orbit_start_frame:int
    orbital_period:float
    orbit_times:list 

    check_alignment:bool

    JSON_ARGS:int = 4 # The number of positional arguments for the Celestial class when loading from a json file

    def __init__(
            self, 
            position:tuple|list, 
            velocity:tuple|list, 
            mass:float, 
            radius:float,  
            ax:plt.Axes|None=None,      # <---  Note: ax is always passed by reference but not saved. It is also not strictly required.
                                        #   To change any parameters on how a planet is displayed, an ax object must be passed again.
            
            **kwargs)->None:
        """
        Celestial
        ============
        Celestial class to represents stars, planets, asteroids and basic rockets. 

        Contains attributes such as position, velocity, mass, and radius, as well as other additional parameters.
        
        Args
        ------
        Positional arguments:
        - position, velocity - tuples, lists, or iterables that can be converted to Numpy arrays to represent the celestial's position and velocity
        - mass, radius - float values to indicate the celestial's mass, and radius when being displayed
        - ax - a MatplotLib ax object. This is needed to allow patches to be added for rendering
        
        Optional arguments (kwargs)
        - colour - the celestial's colour when displayed in MatplotLib
        - orbits - the star/planet that the celestial should be set to orbit
        - alignment - a condition to specify if the planet should be included when checking for planetary alignment
        
        Usage
        ------
        Objects of this class can be treated as point particles, and provide methods to get kinetic and potential energies. 
        Celestial objects can be created directly by unpacking JSON entries with their data in a set format.
        Example:
        >>> from orbits import Celestial
        >>> c1 = Celestial(position=(5e11,2e11),velocity=(-5e4,0.0),mass=2e30,radius=8e6)
        >>> c1.getKE()
        np.float64(2.5e+39)
        >>> c2 = Celestial(position=(0.0,0.0),velocity=(0.0,0.0),mass=2e32,radius=3e8)
        >>> c2.getVE(c1)
        np.float64(-4.954351622563745e+40)
        >>>
        >>> c1.velocity
        array([-50000.,      0.])
        >>> c1.setRelativeOrbit(c2, clockwise=False)
        >>> c1.velocityarray([-108453.35082318,  146133.37705795])
        array([-108453.35082318,  146133.37705795])
        >>> c1.getGravAcc(c2)
        array([-0.04270993, -0.01708397])
        """
        if radius==0 or mass==0:
            raise ValueError("Invalid parameters. Planets cannot have zero mass/radius.")
        
        # Assigning public and private variables
        self.position = np.array(position)
        self.velocity = np.array(velocity)
        self.acceleration, self.prev_acceleration = np.zeros(2), np.zeros(2)
        self.mass = mass
        self.radius = radius
        self.g = 6.67e-11
        self.orbit_times = []
        self.orbital_period = 0.0
        self._orbit_start_frame = 0
        self._below_0 = self.position[1]<0

        if "colour" in kwargs:  self.colour = kwargs["colour"]
        else: self.colour = "red"     # Defaults to red if no colour
        if "alignment" in kwargs and kwargs["alignment"]:
            self.check_alignment = True
        else: 
            self.check_alignment = False
    
        if ax is not None:
            # Patch to render celestial
            self.patch = plt.Circle(self.position, self.radius, color=self.colour, zorder=1000)
            self.patch.center = self.position # Points to position array so that position is always consistent
            ax.add_patch(self.patch)


    def resetPatch(c1:Celestial, ax:plt.Axes)->None:
        """Function that resets/updates a patch by creating a new instance with updated parameters, and deleting the previous one"""
        c1.patch = plt.Circle(c1.position, c1.radius, color=c1.colour, zorder=-1000)
        ax.add_patch(c1.patch)


    def setRelativeOrbit(c1:Celestial, c2:Celestial, clockwise=False)->None:
        """Given another celestial object, it sets its own motion to a relative orbit to that celestial.
        """
        distance_vec = c2.position - c1.position 
        # Rotates distance_vec by 90 degrees to simplify calculations, then is mirrored according to the rotation
        distance_vec = np.array((-distance_vec[1], distance_vec[0]))*(clockwise*2-1) 
        distance = np.linalg.norm(distance_vec)
        v = np.sqrt(c1.g*c2.mass*(distance**-3)) * distance_vec    # v = sqrt(GM/|r|^-3) * r, equation for orbital velocity where: r = distance_vec
        c1.velocity += v                                           # Adds relative velocity to account for movement of other celestial
        c1.acceleration = c1.getGravAcc(c2)                     # Sets initial acceleration to account for gravitational pull
        c1.previous_acceleration = c1.acceleration[:]           # Required for Beeman algorithm


    def getKE(c1:Celestial)->float: # returns 1/2 * mv^2 = 0.5 * mass * v.v
        """Returns the kinetic energy (in Joules) of this celestial object."""
        return 0.5 * c1.mass * c1.velocity.dot(c1.velocity) 


    def getVE(c1:Celestial, c2:Celestial)->float:
        """Returns the potential energy (in Joules) relative to celestial object."""
        distance_vec = c2.position - c1.position    # distance vector across 2 planets (r-vector)
        distance = np.linalg.norm(distance_vec)     # normalised
        m1, m2 = c1.mass, c2.mass
        potential_energy = c1.g * (distance**-1) * m1 * m2
        return -potential_energy
    

    def getGravAcc(c1:Celestial, c2:Celestial)->np.ndarray:
        """Returns a vector corresponding to the acceleration experienced by a celestial `c1`
        due to another celestial `c2`"""
        distance_vec = c2.position - c1.position                    # distance vector across 2 planets (r-vector)
        distance = np.linalg.norm(distance_vec)                     # distance value
        return c1.g * c2.mass * (distance**-3) * distance_vec    # a = GM r^-3 * r-vector


    def getTotAcc(c1:Celestial, celestials:list[Celestial])->np.ndarray:
        """Returns the net acceleration vector acting on a celestial `c1`."""
        a_vec = np.zeros(2)
        for c2 in celestials: # a_vec = a(t+dt) - total acceleration acting on c1
            if c1!=c2: a_vec += c1.getGravAcc(c2)
        return a_vec
        

def test():
    sun = Celestial(position=(0.0,0.0),velocity=(0.0,0.0),mass=2e30,radius=8e6)
    mars = Celestial(position=(2e11,0.0),velocity=(0.0,2.4e4),mass=6e23,radius=3e6)
    asteroid = Celestial(position=(5e14,0.0),velocity=(3e3,0.0),mass=6e15,radius=1e3)

    print(f"Mars kinetic energy: {mars.getKE()}J")
    print(f"Sun kinetic energy: {sun.getKE()}J")
    print(f"Sun-Mars potential energy: {mars.getVE(sun)}J")
    print(f"Sun-asteroid potential energy: {Celestial.getVE(sun, asteroid)}")
    print(f"Sun-mars gravitational acceleration: {sun.getGravAcc(mars)}")

    try: 
        Celestial(position=(0.0,0.0),velocity=(0.0,0.0),mass=0.0,radius=0.0)
    except ValueError as e:
        print(f"Test error: {e}")

if __name__=="__main__":
    test()
