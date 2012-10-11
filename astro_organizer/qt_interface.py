from PySide import QtCore, QtGui
import sys
import logging

import body

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
    
    tableView = QtGui.QTableView()
    
    nrows = len(set_of_bodies)
    if nrows > 0:        
        names = set_of_bodies[0].field_names

        #make name the first field
        i = names.index('name')
        names[i], names[0] = names[0], names[i]
        
        ncols = len(names)
    else:
        logging.warn("Empty set!")
        return tableView
    
    model = QtGui.QStandardItemModel(nrows +1 , ncols)    
    tableView.setModel(model)
    
    #adding headers
    for column in range(ncols):
        index = model.index(0, column)
        model.setData(index, names[column])
    
    for b, row in zip(set_of_bodies, range(1,nrows)):
        assert isinstance(b, body.Body)
        for column in range(ncols):
            index = model.index(row, column)
            value = getattr(b, names[column])            
            model.setData(index, str(value))
    
    return tableView