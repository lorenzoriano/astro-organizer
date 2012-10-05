import socket
import logging

import catalogs
import body


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
    
    def search(self, body_obj):
        
        if type(body_obj) is body.Body:
            body_obj = body_obj.name
        
        cmd = "SEARCH " + body_obj + self.escape_char
        self.socket.sendall(cmd)
        res = self.socket.recv(1024)
        
        if self.__is_ok_message(res):
            logging.info("Object was found correctly")
            return True
        elif self.__not_found_message(res):
            logging.warn("Object not found!")
        else:
            logging.warn("Uninterpreted message: " + self.__fix_response(res))
            return False
        
            