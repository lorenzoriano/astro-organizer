def messier_only(b):
    """Returns True if b is a Messier"""
    return "M " in b.additional_names

def limit_magnitude(mag):
    """Returns a function that evaluates to True if the body magnitude is less
    or equal than the specified one"""
    return lambda b: b.mag <= mag

def limit_surface_brightness(br):
    """Returns a function that evaluates to True if the body surface brightness 
    is less or equal than the specified one"""
    return lambda b: b.surface_brightness <= br

def constellation(const):
    """Returns a function that evaluates to True if the body is in a specified
    constellation (abbreviated)"""
    return lambda b: b.constellation == const