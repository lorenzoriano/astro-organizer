import sys
sys.path.append("/home/pezzotto/Projects/astro-organizer")

from astro_organizer import qt_interface
from astro_organizer import catalogs

def main():
    db = catalogs.MasterDatabase("main_database.h5")
    m13 = db.find_body("M ")
    observer = db.create_observer("Grizzly")
    t = qt_interface.create_table_from_set(observer, list(m13))

    return qt_interface.app.exec_()

if __name__ == "__main__":
    main()