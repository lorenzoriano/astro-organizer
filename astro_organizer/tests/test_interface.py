import sys
sys.path.append("/home/pezzotto/Projects/astro-organizer")

from astro_organizer import qt_interface
from astro_organizer import catalogs

def main():
    db = catalogs.MasterDatabase("main_database.h5")
    m13 = db.find_body("M13")
    t = qt_interface.create_table_from_set(list(m13))
    t.show()
    return qt_interface.app.exec_()

if __name__ == "__main__":
    main()