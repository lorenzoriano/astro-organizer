import ephem
import tables
import logging

import tour
import utils
import body

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

    def __del__(self):
        self.db.close()
    
    def populate_groups(self):
        """Create the groups usually stored in the database, if those are not
        already present."""
        
        if "/catalogs" not in self.db:
            self.db.createGroup("/", "catalogs")
        if "/locations" not in self.db:
            self.db.createTable("/", "locations", _Location)        
        if "/notes" not in self.db:
            self.db.createGroup("/", "notes")                
        if "/tours" not in self.db:
            self.db.createGroup("/", "tours")            
        
        self.db.flush()
        
    def load_sac(self, catalog_name, sac_file_obj):
        """Loads a xephem edb database specified in edb_file_obj and stores it
        into catalog_name.
        """
        utils.create_catalog_from_sac(catalog_name, self, sac_file_obj)    
        
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

    def get_catalog(self, name):
        """
        Finds a catalog from name.
        """
        return self.db.getNode("/catalogs", name)
    
    def list_catalogs(self):
        """
        Returns a list with all the catalogs.
        """
        return self.db.root.catalogs._v_children.keys()
    
    def __iter__(self):
        for table in self.db.root.catalogs:
            for row in table.iterrows():
                yield body.Body(row)
    
    def __len__(self):
        return sum(len(c) for c in self.db.root.catalogs)
        

    def __find_in_table(self, name, table):
        assert isinstance(table, tables.Table)        
        
        #looking for an exact match
        ret = set(body.Body(row) for row in table.where("name=='%s'" % name))        
        #only returns a set if it has exactly one match
        if len(ret) == 1:
            return ret
        
        newname = name.replace(" ", "").lower()
        
        for row in table.iterrows():
            if ( (newname == row["name"].replace(" ", "").lower()) or
                 (newname == row["additional_names"].replace(" ", "").lower())
                 ):
                #found exactly the name
                return set([body.Body(row)])
            elif ((newname in row["name"].replace(" ", "").lower()) or
                  (newname in row["additional_names"].replace(" ", "").lower()) or
                  (newname in row["notes"].replace(" ", "").lower())
                 ):
                ret.add(body.Body(row))
                
        return ret
    
    def find_body(self, name, catalog = None):
        """Look for an object by name. It can match non-exact results and 
        multiple names. If catalog is not None then only the specified catalog
        is used (faster).
        Note that this flexibility might trigger some false positives, better to
        specify a catalog.
        
        Returns the (possibly empty) set of Bodies whose name, additional names 
        or notes match the supplied name. 
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

    def find_bodies(self, names, catalog = None):
        """Returns all the objects matching the names. 
        
        Parameters:
        names: an iterable over strings
        
        Return:
        a (possibly empty) set of body.Body instances
        """

        if len(names) == 0:
            return set()
        
        #first step: search for an exact name match
        ret = set()
        if catalog is None:
            catalogs_to_search = self.db.root.catalogs
        else:
            catalogs_to_search = [self.db.getNode("/catalogs",
                                                  catalog)]        
        
        where_conditions = " | ".join("(name=='%s')" % s for s in names)
        for t in catalogs_to_search:
            ret.update(body.Body(row) for row in t.where(where_conditions))
        
        if len(ret) == len(names):
            return ret

        for name in names:
            ret.update(self.find_body(name))
        return ret
        
    def filter_catalog(self, catalog, master_filter):
        """Apply a bank of filters to a catalog, returning only the remaining
        elements.
        
        Parameters:
        catalog: a string, the name of the catalog (see list_catalogs)
        master_filter: a callable that filters the elements in the catalog.
                      candidates are in filters.py
        """
        
        table = self.get_catalog(catalog)
        assert isinstance(table, tables.Table)
        assert callable(master_filter)
        
        return filter(master_filter, 
                      (body.Body(row) for row in table.iterrows()))
    
    def create_observer(self, location, time = "now"):
        """Creates an Observer in a specified location and at a given time.
        
        Parameters:
        db: a MasterDatabase instance.
        location: a string describing the location
        time: either a datetime instance, or one of the strings: 
              (now, sunrise, sunset)
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
        
        t = utils.create_date(time)
                
        observer.horizon = 0
        observer.date = t
        return observer
    
    def get_tour(self, tourname, description=""):
        """Returns a tour. If the tour doens't exist, it will create a new one.
        
        Parameters:
        tourname: the name to give to this tour
        description: an optional description
        
        Returns:
        an instance of tour.Tour
        """
        return tour.Tour(tourname, self, description)
    
    def list_tours(self):
        """
        Returns a list with all the tours.
        """
        return self.db.root.tours._v_children.keys()        
    