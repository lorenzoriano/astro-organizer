import matplotlib
matplotlib.use('Qt4Agg')

import pylab
import numpy as np
import ephem

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .. import utils
from .. import body


def plot_daily_altitude(element, observer):
    
    assert isinstance(element, body.Body)
    assert isinstance(observer, ephem.Observer)
    observer = utils.copy_observer(observer)
    
    date_tuple = observer.date.tuple()
    start_time = utils.create_date("%d/%d/%d 0:00" % date_tuple[:3])
    #one day later
    end_time = ephem.Date(start_time+1)

    ephem_body = element.ephem_body    
    isinstance(ephem_body, ephem.Body)
    
    altitudes = []
    dtimes = []
    all_times = np.linspace(start_time, end_time, 100)
    for t in all_times:
        observer.date = t
        ephem_body.compute(observer)
        altitudes.append(ephem_body.alt)
        dtimes.append(ephem.localtime(ephem.Date(t)))
    
    altitudes = np.rad2deg(altitudes)
    fig = pylab.figure()
    #fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
    ax = fig.add_subplot(111)
    ax.plot_date(dtimes, altitudes, '-')    
    
    #sunrise and sunset
    sunrise = ephem.localtime(utils.sunrise(observer))
    l = matplotlib.lines.Line2D([sunrise, sunrise],
                                [-90, 90],
                                #transform=ax.transAxes,
                                linewidth=2, color=(1.0, 0.0, 0.0),
                                linestyle="--",
                                )
    ax.add_line(l)    
    
    sunset = ephem.localtime(utils.sunset(observer))
    l = matplotlib.lines.Line2D([sunset, sunset],
                                [-90, 90],
                                #transform=ax.transAxes,
                                linewidth=2, color=(0, 0.0, 0.0),
                                linestyle="--",
                                )
    ax.add_line(l)        

    ax.set_title("Daily altitude for " + element.name)
    ax.set_xlabel("Local time for day %d/%d/%d" % date_tuple[:3])
    ax.set_ylabel("Altitude in degrees")
    
    ax.xaxis.set_major_locator(matplotlib.dates.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
                                              
    ax.grid(True)
    fig.autofmt_xdate()
        
    pylab.show()
    
def plot_yearly_altitude(element, observer, hour=20):
    assert isinstance(element, body.Body)
    assert isinstance(observer, ephem.Observer)    
    observer = utils.copy_observer(observer)
    
    date_tuple = observer.date.tuple()
    start_time = utils.create_date("%d/1/1 %d:00" % (date_tuple[0], hour))
    
    #one year later
    end_time = ephem.Date(start_time+365)
    
    ephem_body = element.ephem_body    
    isinstance(ephem_body, ephem.Body)
    
    altitudes = []
    dtimes = []
    all_times = np.arange(start_time, end_time, 1)
    for t in all_times:
        observer.date = t
        ephem_body.compute(observer)
        altitudes.append(ephem_body.alt)
        dtimes.append(ephem.localtime(ephem.Date(t)))
    
    altitudes = np.rad2deg(altitudes)
    fig = pylab.figure()
    ax = fig.add_subplot(111)
    ax.plot_date(dtimes, altitudes, '-')    
    
    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
    #ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
    
    ax.grid(True)
    fig.autofmt_xdate()
    
    pylab.show()