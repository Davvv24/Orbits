import time

class ProgressBar():
    pr_bar_char:str # Character used to fill the bar
    size:int        # Size of the bar

    prev_perc:float
    prev_time:float

    def __init__(self, pr_bar_char:str="=", size:int=25):
        """
        ProgressBar
        =====
        Simple progress bar class that allows a progress bar to be displayed in the console.
        This bar is useful for keeping track of progress when handling long computations or downloads.
        
        Usage
        ---------
        >>> from progress_bar import ProgressBar()
        >>> bar = ProgressBar()
        >>> bar.set_percent(100.0)

        [=========================] 100.0%
        """
        assert type(pr_bar_char) is str
        self.pr_bar_char = pr_bar_char
        self.size = size
        self.prev_time = 0.0
        self.prev_perc = 0.0
    
    def set_percent(self, percentage:float|int, size:int=None, show_text:bool=False, time_estimate:bool=False):
        """Sets the bar to a given percentage, and prints it to the console."""
        if size is None: size = self.size
        
        if percentage > 100 or percentage<0: raise ValueError("Invalid percentage.")
        assert type(size) is int

        # Characters required to draw the bar
        n = int((percentage/100)*size)
        spaces = ' '*(size-n)
        pr_bar = self.pr_bar_char*n
        
        if show_text: perc_text = f" {percentage:.1f}%"
        else: perc_text = ""

        estimate_text = ""
        if time_estimate:
            new_time = time.time()
            elapsed_time = new_time-self.prev_time
            est_time = (100-percentage)*elapsed_time/(percentage-self.prev_perc)
            estimate_text = f"\tEstimated time: {est_time:.1f}"

        # Printing bar to console using "flush" flag, to allow overwriting of previous bar
        print(f"\r[{pr_bar}{spaces}]{perc_text}{estimate_text}", flush=True, end='',sep='')
        self.prev_perc = percentage

    def gradual_load(self, time_ms:int, percent:float|int):
        """Gradually loads to a given percentage making use of a constant time delay."""
        delay_time = time_ms/((percent+1)*1000)
        if delay_time<=0: raise ValueError("Invalid delay.")

        for i in range(0, percent+1):
            self.set_percent(i)
            time.sleep(delay_time)


