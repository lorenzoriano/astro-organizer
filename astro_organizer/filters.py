from body import Body
import utils
import ephem

def messier_only():
    """Returns True if b is a Messier"""
    return lambda b: b.additional_names.startswith("M ") 

def limit_magnitude(mag):
    """Returns a function that evaluates to True if the body magnitude is less
    or equal than the specified one"""
    return lambda b: b.mag <= mag

def limit_surface_brightness(br):
    """Returns a function that evaluates to True if the body surface brightness 
    is less or equal than the specified one"""
    return lambda b: b.surface_brightness <= br

def constellation(const):
    """Returns a function that evaluates to True if the body is in a specified
    constellation (abbreviated)"""
    return lambda b: b.constellation == const

def observable(observer, 
                start_time = None, 
                end_time = None, 
                horizon = None):
    """Returns a function that evaluates to True if the observer can observe a 
    body at least once in a timespan, False otherwise.
    
    Parameters:
    observer: an ephem.Observer instance
    start_time: an ephem.Date representing when an observation can start. If
                None then the observer time is used.
    end_time: an ephem.Date representing when an observation can start. If
                None then the observer time is used.
    horizon: if not None defines the observer's horizon, otherwise the one from
            the observer is used.
    """
    
    assert isinstance(observer, ephem.Observer)    
    def can_observe(body):        
        assert isinstance(body, Body)
        body = body.ephem_body
        
        copy_observer = ephem.Observer()
        copy_observer.name = observer.name
        copy_observer.lat = observer.lat
        copy_observer.lon = observer.lon
        copy_observer.elev = observer.elev
        copy_observer.date = observer.date
        
        if start_time is None:
            st = observer.date
        else:
            st = utils.create_date(observer, start_time)
        if end_time is None:
            et = observer.date
        else:
            et = utils.create_date(observer, end_time)
            
        if horizon is None:
            copy_observer.horizon = observer.horizon
        else:
            copy_observer.horizon = str(horizon)
        
        try:
            setting = copy_observer.next_setting(body, use_center=True)
            rising = copy_observer.next_rising(body, use_center=True)
        except ephem.NeverUpError:
            return False
        except ephem.AlwaysUpError:
            return True
        
        if rising > setting:
            rising = copy_observer.previous_rising(body, use_center=True)
        #====rise========set=======#
        #========observe======stop=#
        cond1 = rising < st < setting
        
        #===========rise========set=======#
        #===observe========stop===========#    
        cond2 = st < rising < et
        
        return cond1 or cond2    
    
    return can_observe

class MultiFilter(object):
    """This class represents a bank of filter, i.e. a list of boolean function.
    example filters are defined in this file.
    
    Note: since the filters are evaluated in the order they are appendend, put
    the faster filters first and the slower last.
    """
    
    def __init__(self):
        self._filters = []
    
    def append(self, filter_fun):
        """Add a filter function to the filters set."""
        assert callable(filter_fun)
        self._filters.append(filter_fun)
        
    def __call__(self, body):
        """True if all the filters report True for the particular body."""        
        for f in self._filters:
            if not f(body):
                return False
        return True
    
    def filter(self, bodies):
        """Returns a list of bodies filtered according to this class."""
        return filter(self.__call__, bodies)