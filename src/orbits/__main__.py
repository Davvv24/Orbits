import orbits
import re

commands_list = """
run|main - calls the orbits_sim function from orbits.py, using saved configurations

plot-energy - toggles plotting of energies over time
store-data - toggles storing of results to csv file in 'results' folder
print-alignments - toggles printing of alignment frame/alignment time
print-orbit-times - toggles printing of orbit times for celestials
loading-bar - toggles the loading bar
add-stars - toggles stars 
display-window - toggles matplotlib window and animation (useful for just calculating values)

set-method (method) - sets the numerical integration method. Valid options are 'Beeman', 'Euler', and 'Euler-Cromer'
set-threshold (float) - sets the threshold in degrees for planetary alignment
set-fp (path) - sets the file path to load celestials from
set-speed (float) - sets the playback speed to the given value

help - displays this list
quit - exits program
"""

def main(): # Main function for the module
    print("\n--- Orbits main ---\n")

    # Simulation/MatplotLib window variables
    mode = 1
    display_window = True
    energy_plot = True
    add_stars = True
    fp = orbits.data_ss_path
    data_out_path = orbits.csv_out_path
    vid_out_path = orbits.video_out_path
    save_video = False
    save_CSV = True
    orbital_periods = True
    alignment = True
    alignment_thr = 3.0
    loading_bar = True
    method_name = "Beeman"
    speed = 10.0

    def startSim():
        try:
            # There are many available optional parameters which are unrelated to the parameters in the JSON files
            orbits.simSetup(mode=mode,display_window=display_window,energy_plot=energy_plot,add_stars=add_stars,fp=fp,save_video=save_video,
                            save_CSV=save_CSV,orbital_periods=orbital_periods,alignment=alignment,alignment_thr=alignment_thr,loading_bar=loading_bar,
                            method_name=method_name,speed=speed,data_out_path=data_out_path, vid_out_path=vid_out_path)
        except Exception as e:
            print(e)

    loop_condition = True
    while loop_condition: # Main loop
        args = input("Input a command, or type 'help' for help with usage and to list available commands: ")
        args = re.sub(r"\s+", " " ,args).replace(r"[-()\"#/@;:<>{}-=~|.?,]", "").split(" ") # Removes double spaces, cleans string, then separates args by space

        match args[0]: # Match first command
            case "run":
                startSim()
                loop_condition = False
            case "main":
                startSim()
                loop_condition = False
            case "help":
                print(commands_list)

            # Toggles
            case "plot-energy":
                energy_plot = not energy_plot
                print(f"Set energy_plot to {energy_plot}")
            case "store-data":
                save_CSV = not save_CSV
                print(f"Set save_CSV to {save_CSV}")
            case "print-alignments":
                alignment = not alignment
                print(f"Set alignment to {alignment}")
            case "print-orbit-times":
                orbital_periods = not orbital_periods
                print(f"Set orbital_periods to {orbital_periods}")
            case "loading-bar":
                loading_bar = not loading_bar
                print(f"Set loading_bar to {loading_bar}")
            case "add-stars":
                add_stars = not add_stars
                print(f"Set add_stars to {add_stars}")
            case "display-window":
                display_window = not display_window
                print(f"Set display_window to {display_window}")

            # Set commands
            case "set-fp":
                print(f"Switched file path from {fp} file path {args[1]}")
                fp = args[1]
            case "set-results-fp":
                print(f"Switched CSV file path from {data_out_path} file path {args[1]}")
                data_out_path = args[1]
            case "set-video-fp":
                print(f"Switched video file path from {vid_out_path} file path {args[1]}")
                vid_out_path = args[1]
            case "set-speed":
                print(f"Set animation speed to {float(args[1])}")
                speed = float(args[1])
            case "set-method":
                print(f"Set integration method to {args[1]}")
                method_name = args[1]
            case "set-threshold":
                print(f"Set alignment threshold to {args[1]} degrees")
                alignment_thr = float(args[1])

            case "quit":
                loop_condition = False

            case _:
                print("\nInvalid command entered.\n")

if __name__=="__main__":
    main()