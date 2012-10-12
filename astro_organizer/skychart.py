import socket
import logging
import datetime
import time

import catalogs
import body
import ephem
import utils


class SkyChartClient(object):
    
    def __init__(self, 
                 server_address = "localhost",
                 server_port = 3292):
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_address, server_port))
        data = self.socket.recv(1024)
        logging.info("Connection successfull, server replies " + data)
        
        self.escape_char = "\r\n"

    def __fix_response(self, msg):
        ret = msg.replace(".", "")
        return ret
    def __is_ok_message(self, msg):
        return "OK" in self.__fix_response(msg)
    def __not_found_message(self, msg):
        return "Not found" in self.__fix_response(msg)    
    
    def __send_and_check(self, msg):
        #print ("Command: " + msg)
        self.socket.sendall(msg + self.escape_char)
        time.sleep(1.0)
        res = self.socket.recv(1024)
        
        if self.__is_ok_message(res):
            logging.info("Command ok")
            return True
        else:
            logging.warn("Problem with message: " + self.__fix_response(res))
            return False        
    
    def search(self, body_obj):
        
        if type(body_obj) is body.Body:
            body_obj = body_obj.name
        
        body_obj = body_obj.replace(" ", "")
        cmd = "SEARCH " + body_obj
        
        return self.__send_and_check(cmd)
        
    
    def setdate(self, date):
        date = ephem.localtime(utils.create_date(date))
        #yyyy-mm-dd hh:mm:ss
        date_str = "\"%d-%d-%d %d:%d:%d\"" %(date.year, date.month, date.day,
                                         date.hour, date.minute, date.second)
        cmd = "SETDATE " +  date_str
        return self.__send_and_check(cmd)
        
        
            