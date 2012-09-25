import ephem
import tables
import itertools
import logging

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
    

def create_catalog_from_edb(name, save_db, edb_file_obj):
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
    """
    db = tables.openFile(save_db, "a", title="AstroOrganizer Database")
    try:
        group = db.getNode("/", "catalogs")
    except tables.NoSuchNodeError:
        group = db.createGroup("/", "catalogs", "All the catalogs")
    
    
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
    
    db.close()    
