import webbrowser
import logging

import body

def get_messier_string(b):
    assert isinstance(b, body.Body)
    
    if 'M' not in b.catalog:
        return None
    else:        
        additional_name = b.additional_names[1:]
        number = int(additional_name)
        three_digit_code = ("%3d" % number).replace(" ","0")
        return "m"+three_digit_code

def open_seds_info(body_obj):
    assert isinstance(body_obj, body.Body)
    m_str = get_messier_string(body_obj)
    
    if m_str is None:
        logging.error("%s is not a Messier!" % body_obj)
        return
    
    web_url = "http://messier.seds.org/m/" + m_str + ".html"
    webbrowser.open(web_url)

def open_wikipedia_info(body_obj):
    assert isinstance(body_obj, body.Body)
    if 'M' not in body_obj.catalog:
        logging.error("Only Messier objects are supported at the moment!")
        return
    
    additional_name = body_obj.additional_names[1:]
    number = int(additional_name)    
    web_url = "http://en.wikipedia.org/wiki/Messier_" + str(number)
    webbrowser.open(web_url)