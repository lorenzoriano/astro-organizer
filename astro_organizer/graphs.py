import matplotlib
import numpy as np
import ephem

import utils

def plot_daily_altitude(body, observer, time="now"):
    
    time = utils.create_date(observer, time).triple()
    start_time = ephem.Date(time[0], time[1],0)
    end_time = ephem.Datae(start_time+1)
    
    
    
