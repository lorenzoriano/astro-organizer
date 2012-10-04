import csv
import ephem
import math
import datetime
import dateutil.parser
import logging
import pytz

import catalogs

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


def create_date(observer, time = "now"):
    """Creates a date for an observer. The actual time can be specified as a 
    string or a datetime. If the time is interpreted and no timezone is found
    then the local timezone is used. Similarly if time is a datetime and no
    tzinfo member is specified, it is assumed to be local.
    
    time: either a datetime instance, one of the strings: 
          (now, sunrise, sunset), or a string interpretable by dateutil.parser
    timezone: a timezone string (see pytz documentation)
    
    Return:
    an ephem.Date instance
    """

    if type(time) is str:
        now = datetime.datetime.utcnow()
        observer.date = ephem.Date(now)
        observer.horizon = "-18" #astronomical twilight
        if time == "now":
            t = ephem.Date(now)
        elif time == "sunrise":
            t = observer.next_rising(ephem.Sun(), use_center=True)
        elif time == "sunset":
            t = observer.next_setting(ephem.Sun(), use_center=True)
        else:
            #this requires parsing
            d = dateutil.parser.parse(time)
            if d.tzinfo is None:
                logging.warn("Assuming that time %s is local", d)
                d = d.replace(tzinfo = dateutil.tz.tzlocal()).astimezone(
                    pytz.UTC)
                t = ephem.Date(d)
        
    elif type(time) is datetime.datetime:
        #check for naive time
        isinstance(time, datetime.datetime)
        if time.tzinfo is None:
            logging.warn("Timezone unspecified, assuming local")
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