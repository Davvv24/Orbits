from pathlib import Path  

# Directories
orbits_dir = Path(__file__).parent
src_dir = orbits_dir.parent
project_dir = src_dir.parent
data_dir = src_dir / "data"
results_dir = project_dir / "results"
# JSON files
data_exp1_path = data_dir / "exp1.json"
data_exp2_path = data_dir / "exp2.json"
data_ss_path = data_dir / "solar_system.json"
data_ss_au_path = data_dir / "solar_system_scaled.json"
data_merc_jup_path = data_dir / "merc_jupiter.json"
data_test_path = data_dir / "test.json"

csv_out_path = results_dir / "results.csv"
video_out_path = results_dir / "video.mp4"


FRAME_INTERVAL = 30 # millisecond delay between animation frames (only used for saving videos)
WIN_SIZE = 6 # size in inches on the actual display, so the size is not display dependent
G_CONST = 6.67e-11 # not used in practice

def test():
    print("Folder directory:\t", orbits_dir)
    print("Data folder directory:\t", data_dir)
    print("Solar system data file path:\t\t", data_ss_path)
    print("Test data file path:\t", data_test_path)

if __name__=="__main__":
    test()