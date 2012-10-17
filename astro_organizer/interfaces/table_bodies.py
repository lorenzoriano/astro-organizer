from PySide import QtGui, QtCore
import ephem

from .. import body
from .. import string_conversions
import graphs

class BodiesTable(QtGui.QTableView):
    def __init__(self, observer = None, 
                 list_of_bodies = None, parent = None):
        super(BodiesTable, self).__init__(parent)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        
        self.__observer = observer
        if observer is not None:
            name = observer.name
            date = str(ephem.localtime(observer.date))
            self.setWindowTitle(name + " - " + date)
        self.setSortingEnabled(True)
        
        self.__columns = ["name", 
                          "additional_names", 
                          "body_type", 
                          "constellation", 
                          "ra",
                          "dec", 
                          "mag", 
                          "size_max", 
                          "surface_brightness",
                          "notes"]
        
        identity = lambda x:x
        ra = lambda x: str(ephem.hours(x))
        dec = lambda x: str(ephem.degrees(x))
        body_type = string_conversions.sac_type
        constellation = lambda x:string_conversions.sac_constellation_to_str_dict[x]
        self.__value_translator = {"name" : identity,
                                    "additional_names" : identity, 
                                    "body_type" : body_type, 
                                    "constellation" : constellation, 
                                    "ra" : ra,
                                    "dec" : dec, 
                                    "mag" : identity, 
                                    "size_max" : identity, 
                                    "surface_brightness" : identity,
                                    "notes" : identity
                                    }
        
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
        names = self.__columns
        
        nrows = len(set_of_bodies)
        if nrows > 0:                    
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
        
        for b, row in zip(set_of_bodies, range(nrows)):
            assert isinstance(b, body.Body)
            for column, colname in enumerate(names):
                index = model.index(row+1, column)
                
                value = getattr(b, colname)
                v_str = self.__value_translator[colname](value)
                model.setData(index, str(v_str))
                
    
    def __createActions(self):
        self.display_info = QtGui.QAction("Plot Daily Altitude", 
                                          self,
                                          triggered=self.__plot_altitude)

        #self.openAct = QtGui.QAction("&Open...", self,
                #shortcut=QtGui.QKeySequence.Open,
                #statusTip="Open an existing file", triggered=self.open)

        #self.saveAct = QtGui.QAction("&Save", self,
                #shortcut=QtGui.QKeySequence.Save,
                #statusTip="Save the document to disk", triggered=self.save)    
                
    def __plot_altitude(self):
        obj = self.bodies[ self.__model_chosen.row()-1]
        graphs.plot_daily_altitude(obj,
                                   self.__observer)
        print "done"
        
    