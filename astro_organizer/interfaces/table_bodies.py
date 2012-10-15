from PySide import QtGui, QtCore
from .. import body

class BodiesTable(QtGui.QTableView):
    def __init__(self, list_of_bodies = None, parent = None):
        super(BodiesTable, self).__init__(parent)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        
        if list_of_bodies is not None:
            self.load_from_list(list_of_bodies)
            
        self.__createActions()
    
    def context_menu(self, point):
        model_index = self.indexAt(point)
        print "Model chosen: ", model_index
        isinstance(model_index, QtCore.QModelIndex)        
        self.__model_chosen = model_index
        
        menu = QtGui.QMenu(self)
        menu.addAction(self.display_info)
        menu.exec_(self.mapToGlobal(point))
    
    def load_from_list(self, set_of_bodies):
        """Creates a QtGui.QTableView with all the elements
        in set_of_bodies.
        
        Parameters:
        set_of_bodies: an iterable of bodies.Body instances
        
        Returns:
        a QtGui.QTableView instance
        """
        
        self.bodies = list(set_of_bodies)
        
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
        self.setModel(model)
        
        #adding headers
        for column in range(ncols):
            index = model.index(0, column)
            model.setData(index, names[column])
        
        for b, row in zip(set_of_bodies, range(0,nrows)):
            assert isinstance(b, body.Body)
            for column in range(ncols):
                index = model.index(row+1, column)
                value = getattr(b, names[column])            
                model.setData(index, str(value))
                
    
    def __createActions(self):
        self.display_info = QtGui.QAction("Display Info", self,
                triggered=self.__display_info)

        #self.openAct = QtGui.QAction("&Open...", self,
                #shortcut=QtGui.QKeySequence.Open,
                #statusTip="Open an existing file", triggered=self.open)

        #self.saveAct = QtGui.QAction("&Save", self,
                #shortcut=QtGui.QKeySequence.Save,
                #statusTip="Save the document to disk", triggered=self.save)    
                
    def __display_info(self):
        obj = self.bodies[ self.__model_chosen.row()-1]
        print obj