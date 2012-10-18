import catalogs
import body

import tables
import logging
import itertools

class _TourTable(tables.IsDescription):
    name = tables.StringCol(20)
    note = tables.StringCol(512)

class Tour(object):
    """Defines a tour as a list of objects to view and notes. It automatically
    manages the entries in the database"""
    
    def __init__(self, tourname, db, title=""):
        """
        
        Parameters:
        tourname: name of the tour. Returns a tour if the name already exists.
        db: a catalogs.MasterDatabase instance
        tile: a tile for the table
        """
        self.name = tourname
        self._db = db        
        assert isinstance(db, catalogs.MasterDatabase)
        
        try: 
            self._table = db.db.getNode("/tours",tourname)
        except tables.NoSuchNodeError:
            self._table = db.db.createTable("/tours", tourname, _TourTable,
                                           title,
                                           createparents=True)
        
        self.title = self._table.title
        self._bodies = set()
        self._notes = []
        self._positions = {}
        self.__load_bodies()
        self.filter_fun = lambda x : True

    def __load_bodies(self):
        self._bodies = set()
        names = []
        
        for row in self._table.iterrows():
            n = row["name"]
            names.append(n)
            self._notes.append(row["note"])
            self._positions[n] = row.nrow
        
        if len(names) == 0:
            return 
        
        s = self._db.find_bodies(names)
        nbodies = self._table.nrows
        if len(s) != nbodies:
            raise Exception("Mismatch: %d bodies found over %d total" %(len(s),
                                                                        nbodies)
                                                                        )
        self._bodies = s
    
    def append(self, body_obj, note=""):
        """Add an element to the tour.
        
        Parameters:
        body: either a string or a body.Body instance. In the first case the element
              is searched for. An error is raised if more than one body is found.
        note: a note to add to this part of the tour.        
        """
        if type(body_obj) is str:
            s = self._db.find_body(body_obj)
            if len(s) == 0:
                raise Exception("No body found with name %s" % body_obj)
            elif len(s) > 1:
                raise Exception("%d bodies found with name %s" % (len(s), body_obj))
            body_obj = s.pop()
        
        assert isinstance(body_obj, body.Body)
        row = self._table.row
        row["name"] = body_obj.name
        row["note"] = note
        row.append()
        self._table.flush()
        
        self._bodies.add(body_obj)
        self._notes.append(note)
        self._positions[body_obj.name] = self._table.nrows - 1
    
    def delete(self):
        """Removes the tour from the database.
        WARNING: this object will be unusable after this operation so it would
        be safe to delete it as well.
        """
        
        self._db.db.removeNode("/tours", self.name)
    
    def __getitem__(self, i):        
        return (self.ordered_bodies[i])

    def __iter__(self):
        return iter(self.ordered_bodies)
    
    def iteritems(self):
        return itertools.izip(self.bodies, self._notes)
    
    def __len__(self):
        return len(self.bodies)
    
    def __repr__(self):
        if self.title != "":
            return "Tour: %s -- %s" %(self.name, self.title)
        else:
            return "Tour: %s" %(self.name)

    @property
    def bodies(self):
        return filter(self.filter_fun, self._bodies)
    
    @property
    def ordered_bodies(self):
        return sorted(self.bodies,
                      key = lambda b: self._positions[b.name]
                      )

    
    def sky_safari_entry(self, add_notes = True,
                         add_additional_notes = True,
                         add_ngc_description = True,
                         use_additional_names = False
                         ):
        """Creates a Sky Safari Observation list from this tour.
        Returns the string.
        """
        def __note_filter(note):
            if note != "":
                return "Tour note: " + note
            else:
                return None
        
        ret = "SkySafariObservingListVersion=3.0\n"
        ret += "\n".join(body.sky_safari_entry(add_notes,
                                               add_additional_notes,
                                               add_ngc_description,
                                               __note_filter(note),
                                               use_additional_names
                                               )
                         for body,note in zip(self.ordered_bodies,
                                              self._notes)
                         )
                                               
        return ret
    