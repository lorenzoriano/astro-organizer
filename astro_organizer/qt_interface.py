from PySide import QtCore, QtGui
import sys
import logging

import body
import interfaces
import interfaces.table_bodies

app = QtGui.qApp
if app is None:
    app = QtGui.QApplication(sys.argv)

def create_table_from_set(set_of_bodies):
    """Creates a QtGui.QTableView with all the elements
    in set_of_bodies.
    
    Parameters:
    set_of_bodies: an iterable of bodies.Body instances
    
    Returns:
    a QtGui.QTableView instance
    """
    
    tableView = interfaces.table_bodies.BodiesTable(set_of_bodies)   
    
    return tableView