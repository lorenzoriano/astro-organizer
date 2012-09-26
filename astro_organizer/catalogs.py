import ephem
import tables
import logging
import pytz
import datetime
import dateutil

classes_dict = {"A":"Cluster of galaxies",
                "B":"Binary Star (Deprecated)",
                "C":"Cluster, globular",
                "D":"Star, visual double",
                "F":"Nebula, diffuse",
                "G":"Galaxy, spiral",
                "H":"Galaxy, spherical",
                "J":"Radio",
                "K":"Nebula, dark",
                "L":"Pulsar",
                "M":"Star, multiple",
                "N":"Nebula, bright",
                "O":"Cluster, open",
                "P":"Nebula, planetary",
                "Q":"Quasar",
                "R":"Supernova remnant",
                "S":"Star",
                "T":"Stellar object",
                "U":"Cluster, with nebulosity",
                "Y":"Supernova",
                "V":"Star, variable"
                }

class TableBody(tables.IsDescription):
    name = tables.StringCol(128)
    body_type = tables.StringCol(128)
    catalog = tables.StringCol(128)
    mag = tables.Float64Col()
    ra = tables.Float64Col()
    dec = tables.Float64Col()
    epoch = tables.Float64Col()
    radius = tables.Float64Col()
    elong = tables.Float64Col()
    edb_string = tables.StringCol(1024)

class Location(tables.IsDescription):
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
    
    def populate_groups(self):
        """Create the groups usually stored in the database, if those are not
        already present."""
        
        if "/catalogs" not in self.db:
            self.db.createGroup("/","catalogs")
        if "/locations" not in self.db:
            self.db.createTable("/","locations", Location)        
        
        self.db.flush()
        
    def load_edb(self, catalog_name, edb_file_obj):
        """Loads a xephem edb database specified in edb_file_obj and stores it
        into catalog_name.
        """
        create_catalog_from_edb(catalog_name, self, edb_file_obj)
        
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

    def __find_in_table(self, name, table):
        assert isinstance(table, tables.Table)
        newname = name.replace(" ", "").lower()
        for row in table.iterrows():            
            if newname in row["name"].replace(" ", "").lower():
                return row
        return None

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
        
    
    def find_body(self, name, catalog = None):
        """Look for an object by name. It can match non-exact results and 
        multiple names. If catalog is not None then only the specified catalog
        is used (faster).
        Note that this flexibility might trigger some false positives, better to
        specify a catalog.
        
        
        Returns a FixedBody or None if the object could not be found.
        """
        if catalog is None:
            for t in self.db.root.catalogs:
                res = self.__find_in_table(name, t)
                if res is not None:
                    return ephem.readdb(res["edb_string"])
            return None
        else:
            res = self.__find_in_table(name, self.db.getNode("/catalogs",
                                                             catalog))
            if res is not None:
                return ephem.readdb(res["edb_string"])
            else:
                return None
    def find_all_visible(self, observer, catalog, 
                         start_time = None, end_time = None, 
                         horizon = None,
                         filter_fun = None
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
        
        
        Returns:
        a list of ephem.FixedBody instances.
        """
        
        table = self.find_catalog(catalog)
        isinstance(table, tables.Table)
        
        bodies = []
        for line in table.col("edb_string"):
            body = ephem.readdb(line)
            if can_observe(observer, body, start_time, end_time, horizon):
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


def create_catalog_from_edb(name, master_db, edb_file_obj,):
    """Creates an h5 catalog from a xepeh edb one.
    The xephem database format is described at 
    ttp://www.clearskyinstitute.com/xephem/help/xephem.html.
    
    Parameters:
    name: the catalog name
    save_db: either a file or a string to use to store the database. An existing
             database will be updated but if a catalog with the same name already
             exists then an error will be raised.
    edb_file_obj: either a file or a string. This is the location of the edb
             database. The file is not overwritten.
    master_db: A MasterDatabase instance, or None if one has to be created.
             
    Returns a MasterDatabase instance, either master_db or a new one.     
    """
    if type(master_db) is str:
        master_db = MasterDatabase(master_db)
    db = master_db.db
    
    group = db.getNode("/", "catalogs")
    
    table = db.createTable(group, name, TableBody, "Catalog")
    element = table.row    
        
    if type(edb_file_obj) is str:
        edb_file_obj = open(edb_file_obj)
            
    for line in edb_file_obj:
        try:
            body = ephem.readdb(line)
        except ValueError:
            continue
        if not isinstance(body, ephem.FixedBody):
            logging.warn("Skipping line %s: it's not a fixed body",
                         line)
            continue
        
        body.compute()
        
        element['name'] = body.name
        try:
            body_type = classes_dict[body._class]
        except KeyError:
            logging.warn("Unknown type %s for line %s", body._class, line)
            body_type = body._class
        element["body_type"] = body_type
        element['catalog'] = name
        element['mag'] = body.mag
        element['ra'] = body.a_ra
        element['dec'] = body.a_dec
        element['epoch'] = body.a_epoch
        element['radius'] = body.radius
        element['elong'] = body.elong
        element['edb_string'] = line
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
            #assume UTC
            d = dateutil.parser.parse(time)
            if d.tzinfo is None:
                logging.warn("Assuming that time %s is local", d)
                d = d.replace(tzinfo = dateutil.tz.tzlocal()).astimezone(
                    pytz.UTC)
                t = ephem.Date(t)
        
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
        setting = copy_observer.next_setting(body)
        rising = copy_observer.next_rising(body)
    except ephem.NeverUpError:
        return False
    except ephem.AlwaysUpError:
        return True
    
    if rising > setting:
        rising = copy_observer.previous_rising(body)
    #====rise========set=======#
    #========observe======stop=#
    cond1 = rising < start_time < setting
    
    #===========rise========set=======#
    #===observe========stop===========#    
    cond2 = start_time < rising < end_time
    
    return cond1 or cond2

    
        
