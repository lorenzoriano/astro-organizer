import csv
import ephem
import math
import datetime
import dateutil.parser
import logging
import pytz
import webbrowser

import catalogs
import body

from scipy import optimize

def create_catalog_from_sac(name, master_db, sac_file_obj,):
    """Creates an h5 catalog from a Saguaro Astronomical Catalog cvs file.
    The original file is available at:
    http://www.saguaroastro.org/content/downloads.htm
    
    Parameters:
    name: the catalog name
    save_db: either a file or a string to use to store the database. An existing
             database will be updated but if a catalog with the same name already
             exists then an error will be raised.
    sac_file_obj: either a file or a string. This is the location of the sac
             database. The file is not overwritten.
    master_db: A MasterDatabase instance, or None if one has to be created.
             
    Returns a MasterDatabase instance, either master_db or a new one.     
    """
    if type(master_db) is str:
        master_db = catalogs.MasterDatabase(master_db)
    db = master_db.db
    
    group = db.getNode("/", "catalogs")
    
    table = db.createTable(group, name, catalogs._TableBody, "SAC Database")
    element = table.row    
        
    if type(sac_file_obj) is str:
        sac_file_obj = open(sac_file_obj)    
    
    reader = csv.reader(sac_file_obj, delimiter = ',')
    #skip first line with the field names
    reader.next()
    
    for raw_line in reader:
        line = [obj.strip() for obj in raw_line]
        element['name'] = line[0]
        element['additional_names'] = line[1]
        element['body_type'] = line[2]
        element['constellation'] = line[3]
    
        element['ra'] = ephem.hours(line[4])
        element['dec'] = ephem.degrees(line[5])
        element['mag'] = float(line[6])
    
        try:
            element['surface_brightness'] = float(line[7])
        except ValueError:
            element['surface_brightness'] = float(line[6])
            
        element['size_max'] = line[10]
        element['size_min'] = line[11]
        try:
            element['positional_angle'] = math.radians(float(line[12]))
        except ValueError:
            element['positional_angle'] = 0
            
        element['sci_class'] = line[13]
        try:
            element['central_star_mag'] = float(line[15])
        except ValueError:
            element['central_star_mag'] = float(line[6])
        element['catalog'] = line[16]
        element['ngc_descr'] = line[17]
        element['notes'] = line[18]
        
        element.append()
            
    db.flush()
    return master_db        

def sunset(observer):
    """Returns the astronomical sunset time according to observer. 
    The observer's day is used for this calculation.
    
    Note: The astronomical sunset is much later than the common one.
    """
    
    observer = copy_observer(observer)
    now = datetime.datetime.utcnow()
    observer.date = ephem.Date(now)
    observer.horizon = "-18" #astronomical twilight    
    t = observer.next_setting(ephem.Sun(), use_center=True)
    return t

def sunrise(observer):
    """Returns the astronomical sunrise time according to observer. 
    The observer's day is used for this calculation.
    
    Note: The astronomical sunrise is much earlier than the common one.
    """
    
    observer = copy_observer(observer)
    now = datetime.datetime.utcnow()
    observer.date = ephem.Date(now)
    observer.horizon = "-18" #astronomical twilight    
    t = observer.next_rising(ephem.Sun(), use_center=True)
    return t

def create_date(time = "now"):
    """Creates an ephem date. The actual time can be specified as a 
    string or a datetime. If the time is interpreted and no timezone is found
    then the local timezone is used. Similarly if time is a datetime and no
    tzinfo member is specified, it is assumed to be local.
    
    time: either a datetime instance, now, or a string interpretable by dateutil.parser
    
    Return:
    an ephem.Date instance
    """
    
    if isinstance(time, str):
        if time == "now":
            now = datetime.datetime.utcnow()            
            t = ephem.Date(now)            
        else:
            #this requires parsing
            d = dateutil.parser.parse(time)
            if d.tzinfo is None:
                logging.debug("Assuming that time %s is local", d)
                d = d.replace(tzinfo = dateutil.tz.tzlocal()).astimezone(
                    pytz.UTC)
                t = ephem.Date(d)
        
    elif isinstance(time, datetime.datetime):
        #check for naive time
        isinstance(time, datetime.datetime)
        if time.tzinfo is None:
            logging.debug("Timezone unspecified, assuming local")
            d = time.replace(tzinfo = dateutil.tz.tzlocal()).astimezone(
                            pytz.UTC)
            t = ephem.Date(t)            
    elif type(time) is ephem.Date:
        #nothing to do really
        return time
    
    else:
        raise ValueError("Wrong value passed as time: %s", time)    
    
    return t

    
def create_sky_safari_list(set_of_bodies,
                           add_notes = True,
                           add_additional_notes = True,
                           add_ngc_description = True
                           ):
    """Creates a Sky Safari Observation list from a set (iterable) of bodies.
    Returns the string.
    """
    ret = "SkySafariObservingListVersion=3.0\n"
    ret += "\n".join(body.sky_safari_entry(add_notes,
                                           add_additional_notes,
                                           add_ngc_description,
                                           )
                                           for body in set_of_bodies)
    return ret

def copy_observer(observer):
    """Returns a copy of an observer. Useful since deepcopy doesn't work with
    the underlying C implementation.
    """
    
    assert isinstance(observer, ephem.Observer)
    copy_observer = ephem.Observer()
    copy_observer.name = observer.name
    copy_observer.lat = observer.lat
    copy_observer.lon = observer.lon
    copy_observer.elev = observer.elev
    copy_observer.date = observer.date
    copy_observer.pressure = observer.pressure
    copy_observer.epoch = observer.epoch
    copy_observer.horizon = observer.horizon
    
    return copy_observer

def find_best_observable_time(body_obj, observer, start_time, end_time):
    """Find the best time to observe an object in a given interval.
    
    Parameters:
    body_obj: a body.Body instance
    observer: an ephem.Observer instance
    start_time, end_time: values that create_date accepts
    
    Returns:
    an ephem.Date instance.
    """
    
    assert isinstance(body_obj, body.Body)
    start_time = create_date(start_time)
    end_time = create_date(end_time)
        
    ephem_body = body_obj.ephem_body
    
    observer = copy_observer(observer)
    
    def neg_altitude(time):
        observer.date = time[0]
        ephem_body.compute(observer)
        return -ephem_body.alt
    
    middtime = start_time + (end_time - start_time) / 2
    best_time = optimize.fmin_l_bfgs_b(neg_altitude, [middtime],
                                       bounds=[(start_time, end_time)],
                                       approx_grad=True,
                                       epsilon=ephem.minute
                                       )
    
    return ephem.Date(best_time[0])
            