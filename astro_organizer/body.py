from string_conversions import sac_to_ephem_dict, ngc_to_string
#from catalogs import _NotesTable
import ephem
import tables

class _NotesTable(tables.IsDescription):
    additional_notes = tables.StringCol(512)

class Body(object):
    """This class represents a generic body as stored in the database.
    Its attributes are fetched automatically from the database fields and they
    can be retrieved using self.field_names.
    
    Useful methods are provided to convert to an ephem.FixedBody instance. See
    ephem_string and ephem_body.
    
    The body can be converted to a SkySafari entry using the property 
    sky_safari_entry.
    
    If an attribute is changed the corresponding entry in the database is updated.
    """
    
    def __init__(self, row_pointer):
        self._ephem_body = None
        self._row_pointer = row_pointer
        self._table = row_pointer.table
        self._nrow = row_pointer.nrow
        self._db = self._table._v_file        

    @property
    def field_names(self):
        return self._table.cols._v_colnames
    
    def __getattr__(self, name):
        try:
            table = object.__getattribute__(self, "_table")
            nrow = object.__getattribute__(self, "_nrow")
            return getattr(table.cols, name)[nrow]
        except AttributeError, e:
            raise AttributeError("There is no %s value in the table" % name)
    
    def __setattr__(self, name, value):
        try:
            col  = getattr(self._table.cols, name)
            col[self._nrow] = value
            self._table.flush()
        except AttributeError:
            object.__setattr__(self, name, value)                
    
    def __repr__(self):
        return self.name + "; " + self.additional_names
    
    def ephem_string(self):
        string = []
        string.append(self.name)
        try:
            string.append("f|" + sac_to_ephem_dict[self.body_type])
        except KeyError:
            string.append("f|T")
        string.append(str(ephem.hours(self.ra)))
        string.append(str(ephem.degrees(self.dec)))
        string.append(str(self.mag))
        string.append("2000")
        
        max_s = self.size_max
        if len(max_s) == 0:
            fp = 0
        elif max_s[-1] == 'm': #arcmin
            fp = float(max_s[:-1]) / 3437.74677078
        elif max_s[-1] == 's': #arcsec
            fp = float(max_s[:-1]) / 206264.806247
        elif max_s[-1] == 'd': #degree
            fp = float(max_s[:-1]) / 57.2957795131 
        else:
            raise ValueError("Unkwnown format for size_max: " + max_s)
        string.append(str(fp * 206264.806247))
        
        return ','.join(string)
    
    @property
    def ephem_body(self):
        if self._ephem_body is None:
            self._ephem_body = ephem.readdb(self.ephem_string())
        return self._ephem_body

    def __get_additional_notes(self):
        try:
            node = self._db.getNode("/notes", self.name)
        except tables.NoSuchNodeError:
            return []
        return [r["additional_notes"] for r in node.iterrows()]

    def __set_additional_notes(self, value):
        if len(value) > 512:
            raise ValueError("Input length is %d, maximum is 512" % len(value))
        
        try:
            node = self._db.getNode("/notes", self.name)
        except tables.NoSuchNodeError:
            node = self._db.createTable("/notes", self.name, _NotesTable)
        
        row = node.row
        row["additional_notes"] = value
        row.append()
        node.flush()        
    
    def __delete_additional_notes(self):
        try:
            node = self._db.getNode("/notes", self.name)
        except tables.NoSuchNodeError:        
            return #silently ignore
        
        try:
            node.removeRows(-1)
        except NotImplementedError:
            #weird pytables thing
            self._db.removeNode("/notes", self.name)
        
    additional_notes = property(__get_additional_notes,
                                __set_additional_notes,
                                __delete_additional_notes
                                )    
    
    @property
    def sky_safari_entry(self, add_notes = True,
                         add_additional_notes = True,
                         add_ngc_description = True):
        """
        Returns a string with the SkySafari description. This is very 
        experimental!!
        """
        header = "SkyObject=BeginObject\n%s\nEndObject=SkyObject"
        lines = []
        
        #object id
        if self.body_type in ["STAR"]:
            object_id = 2
        else:
            object_id = 4
        lines.append("\tObjectID=%d,-1,-1" % object_id)
        lines.append("\tCommonName=%s" % self.additional_names)
        lines.append("\tCatalogNumber=%s" % self.name)
        lines.append("\tCatalogNumber=%s" % self.additional_names)
        
        comment = ""
        if add_notes:
            if self.notes != "":
                comment += self.notes
        if add_additional_notes:
            an = self.additional_notes
            if len(an) != 0:
                comment += " || " + " || ".join(an)
        if add_ngc_description:
            d = self.ngc_description
            comment += " -- NGC: " + d
            
        if comment != "":
            lines.append("\tComment=%s" % comment)
    
        full_text = header % "\n".join(lines)
        return full_text
    
    @property
    def ngc_description(self):
        descr = self.ngc_descr
        return ngc_to_string(descr)