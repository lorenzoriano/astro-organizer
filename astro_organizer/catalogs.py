import ephem
import tables
import logging
import pytz
import datetime
import dateutil.parser
import csv
import math

from body import Body

class _TableBody(tables.IsDescription):
    name = tables.StringCol(20)
    additional_names = tables.StringCol(20)
    body_type = tables.StringCol(5)
    constellation = tables.StringCol(4)
    
    ra = tables.Float64Col()
    dec = tables.Float64Col()
    
    
    mag = tables.Float64Col()
    
    surface_brightness = tables.StringCol(4)
    size_max = tables.StringCol(8)
    size_min = tables.StringCol(8)
    positional_angle = tables.Float64Col()
    sci_class = tables.StringCol(11)
    central_star_mag = tables.Float64Col()
    catalog = tables.StringCol(4)
    ngc_descr = tables.StringCol(55)
    notes = tables.StringCol(86)
        

class _Location(tables.IsDescription):
    name = tables.StringCol(128)
    latitude = tables.Float64Col()
    longitude = tables.Float64Col()
    height = tables.Float64Col()
    bortle_class = tables.Int8Col()


class MasterDatabase(object):
    """This is a class that keeps track of all the info in the organizer. The
    data is stored in a h5 file"""
    
    def __init__(self, database):
        if type(database) is str:
            if not database.endswith(".h5"):
                database += ".h5"
            filters = tables.Filters(complevel=9)
            self.db = tables.openFile(database, "a", 
                                      title="AstroOrganizer Database",
                                      filters=filters)
        
        elif type(database) is tables.File:
            self.db = database
        
        else:
            raise ValueError("Wrong type for database: %s" % type(database))
        
        self.populate_groups()

    def __delete__(self):
        print "closing database %s"% self.db
        self.db.close()
    
    def populate_groups(self):
        """Create the groups usually stored in the database, if those are not
        already present."""
        
        if "/catalogs" not in self.db:
            self.db.createGroup("/","catalogs")
        if "/locations" not in self.db:
            self.db.createTable("/","locations", _Location)        
        if "/notes" not in self.db:
            self.db.createGroup("/","notes")                
        
        self.db.flush()
        
    #def load_edb(self, catalog_name, edb_file_obj):
        #"""Loads a xephem edb database specified in edb_file_obj and stores it
        #into catalog_name.
        #"""
        #create_catalog_from_edb(catalog_name, self, edb_file_obj)

    def load_sac(self, catalog_name, sac_file_obj):
        """Loads a xephem edb database specified in edb_file_obj and stores it
        into catalog_name.
        """
        create_catalog_from_sac(catalog_name, self, sac_file_obj)    
        
    def add_location(self, name, latitude, longitude, height, 
                     bortle_class = 7):
        """Adds a location to the database.
        
        Parameters:
        name: a string with the name of the location
        latitude: floating point number (positive is north)
        longitude: floating point number (poisitive is east)  
        height = height in meters
        """
        
        loc_table = self.db.root.locations
        row = loc_table.row
        row["name"] = name
        row["latitude"] = latitude
        row["longitude"] = longitude
        row["height"] = height
        row["bortle_class"] = bortle_class
        row.append()
        loc_table.flush()

    def find_catalog(self, name):
        """
        Finds a catalog from name.
        """
        return self.db.getNode("/catalogs", name)
    
    def list_all_catalogs(self):
        """
        Returns a list with all the catalogs.
        """
        return self.db.root.catalogs._v_children.keys()

    def __find_in_table(self, name, table):
        ret = set()
        assert isinstance(table, tables.Table)
        
        newname = name.replace(" ", "").lower()
        
        for row in table.iterrows():
            if ( (newname == row["name"].replace(" ", "").lower()) or
                 (newname == row["additional_names"].replace(" ", "").lower())
                 ):
                #found exactly the name
                return set([Body(row)])
            elif ((newname in row["name"].replace(" ", "").lower()) or
                  (newname in row["additional_names"].replace(" ", "").lower()) or
                  (newname in row["notes"].replace(" ", "").lower())
                 ):
                ret.add(Body(row))
                
        return ret
    
    def find_body(self, name, catalog = None):
        """Look for an object by name. It can match non-exact results and 
        multiple names. If catalog is not None then only the specified catalog
        is used (faster).
        Note that this flexibility might trigger some false positives, better to
        specify a catalog.
        
        
        Returns a set of Bodies whose name, additional names or notes match the
        supplied name. If no body is found the the returned set is empty.
        """
        if catalog is None:
            catalogs_to_search = self.db.root.catalogs
        else:
            catalogs_to_search = [self.db.getNode("/catalogs",
                                                  catalog)]
        ret = set()
        for t in catalogs_to_search:
            ret.update(self.__find_in_table(name, t))
        
        return ret

    def __getattr__(self, value):
        elements = self.find_body(value)
        if len(elements) == 0:
            raise AttributeError("%s object has no attribute %s" %(
                self.__class__.__name__, value))
        else:
            return elements.pop()
    
    def find_bodies(self, names):
        """Returns all the objects matching the names. 
        
        Parameters:
        names: an iterable over strings
        """
        ret = set()
        for name in names:
            ret.update(self.find_body(name))
        return ret
        
    
    def find_all_visible(self, observer, catalog, 
                         start_time = None, end_time = None, 
                         horizon = None,
                         filter_functions = None,
                         ):
        """Returns a list of all the objects in a catalog that are visible by 
        observer in a given timespan.
        
        Parameters:
        observer: an ephem.Observer instance
        db: a MasterDatabase instance
        catalog: a string defining a catalog
        start_time: an ephem.Date representing when an observation can start. If
                    None then the observer time is used.
        end_time: an ephem.Date representing when an observation can start. If
                    None then the observer time is used.
        horizon: if not None defines the observer's horizon, otherwise the one from
                the observer is used.
        filter_functions: a list of functions that take a Body instance and return
                either True or False. If all the functions return True then the
                body is added to the return list.
        
        
        Returns:
        a list of Body instances.
        """
        
        horizon = str(horizon)
        table = self.find_catalog(catalog)
        isinstance(table, tables.Table)
        if filter_functions is None:
            filter_functions = []
        
        bodies = []
        for row in table.iterrows():
            body = Body(row)
            if (all(f(body) for f in filter_functions) and
                can_observe(observer, body.ephem_body, start_time, end_time, horizon)):
                bodies.append(body)
        return bodies    
    
    def create_observer(self, location, time = "now"):
        """Creates an Observer in a specified location and at a given time.
        
        Parameters:
        db: a MasterDatabase instance.
        location: a string describing the location
        time: either a datetime instance, or one of the strings: 
              (now, sunrise, sunset)
        timezone: a timezone string (see pytz documentation)
        """
        
        location_found = False
        for r in self.db.root.locations.iterrows():
            if location.lower() in r["name"].lower():
                location_found = True
                break
        if not location_found:
            raise ValueError("Location %s not in the database" % location)
        
        latitude = r["latitude"]
        longitude = r["longitude"]
        height = r["height"]
        name = r["name"]
        
        observer = ephem.Observer()
        observer.name = name
        observer.lat = str(latitude)
        observer.lon = str(longitude)
        observer.elev = height    
        
        t = create_date(observer, time)
                
        observer.horizon = 0
        observer.date = t
        return observer

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
        master_db = MasterDatabase(master_db)
    db = master_db.db
    
    group = db.getNode("/", "catalogs")
    
    table = db.createTable(group, name, _TableBody, "SAC Database")
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
    
    time: either a datetime instance, or one of the strings: 
          (now, sunrise, sunset)
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
    else:
        raise ValueError("Wrong value passed as time: %s", time)    
    
    return t

    
def can_observe(observer, body, start_time = None, end_time = None, 
                horizon = None):
    """Return True of the observer can observe a body at least once in a 
    timespan, False otherwise.
    
    Parameters:
    observer: an ephem.Observer instance
    body: an ephem.FixedBody instance
    start_time: an ephem.Date representing when an observation can start. If
                None then the observer time is used.
    end_time: an ephem.Date representing when an observation can start. If
                None then the observer time is used.
    horizon: if not None defines the observer's horizon, otherwise the one from
            the observer is used.
    """
    assert isinstance(observer, ephem.Observer)
    assert isinstance(body, ephem.FixedBody)
    
    copy_observer = ephem.Observer()
    copy_observer.name = observer.name
    copy_observer.lat = observer.lat
    copy_observer.lon = observer.lon
    copy_observer.elev = observer.elev
    copy_observer.date = observer.date
    
    if start_time is None:
        start_time = observer.date
    if end_time is None:
        end_time = observer.date
    if horizon is None:
        copy_observer.horizon = observer.horizon
    else:
        copy_observer.horizon = horizon
    
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
    cond1 = rising < start_time < setting
    
    #===========rise========set=======#
    #===observe========stop===========#    
    cond2 = start_time < rising < end_time
    
    return cond1 or cond2
    
def create_sky_safari_list(set_of_bodies):
    """Creates a Sky Safari Observation list from a set (iterable) of bodies.
    Returns the string.
    """
    ret = "SkySafariObservingListVersion=3.0\n"
    ret += "\n".join(body.sky_safari_entry for body in set_of_bodies)
    return ret