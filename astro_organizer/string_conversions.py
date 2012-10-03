import logging

ephem_dict = {"A":"Cluster of galaxies",
              "B":"Binary Star (Deprecated)",
              "C":"Cluster, globular",
              "D":"Star, visual double",
              "F":"Nebula, diffuse",
              "G":"Galaxy, spiral",
              "H":"Galaxy, spherical",
              "J":"Radio",
              "K":"Nebula, dark",
              "L":"Pulsar",
              "M":"Star, multiple",
              "N":"Nebula, bright",
              "O":"Cluster, open",
              "P":"Nebula, planetary",
              "Q":"Quasar",
              "R":"Supernova remnant",
              "S":"Star",
              "T":"Stellar object",
              "U":"Cluster, with nebulosity",
              "Y":"Supernova",
              "V":"Star, variable"
              }

sac_to_ephem_dict = {'ASTER': 'T',
                     'BRTNB': 'N',
                     'CL+NB': 'U',
                     'DRKNB': 'K',
                     'GALCL': 'A',
                     'GALXY': 'F',
                     'GLOCL': 'C',
                     'GX+DN': 'F',
                     'GX+GC': 'C', 
                     'G+C+N': 'U',
                     'LMCCN': 'U',
                     'LMCDN': 'F',
                     'LMCGC': 'C',
                     'LMCOC': 'O',
                     'NONEX': 'T',
                     'OPNCL': 'O',
                     'PLNNB': 'P',
                     'SMCCN': 'U',
                     'SMCDN': 'F',
                     'SMCGC': 'C',
                     'SMCOC': 'O',
                     'SNREM': 'R',
                     'QUASR': 'Q'
                     }

ngc_dict = {'!': 'remarkable',
            '!!': 'very remarkable',
            '!!!': 'a magnificent or otherwise interesting object',
            '*': 'a star: *10, a star of 10th magnitude',
            '**': 'double star',
            '***': 'triple star',
            'Ab': 'about',
            'B': 'bright',
            'C': 'compressed',
            'C.G.H.': 'Cape of Good Hope',
            'Cl': 'cluster',
            'D': 'double',
            'E': 'extended',
            'F': 'faint',
            'L': 'large',
            'M': 'middle, or in the middle',
            'N': 'Nucleus, or to a Nucleus',
            'P': 'poor',
            'R': 'round',
            'RR': 'exactly round',
            'Ri': 'rich',
            'S': 'small',
            'alm': 'almost',
            'am': 'among',
            'app': 'appended',
            'att': 'attached',
            'b': 'brighter',
            'be': 'between',
            'bf': 'brightest towards the following side',
            'biN': 'binuclear',
            'bn': 'brightest towards the north side',
            'bp': 'brightest towards the preceding side',
            'bs': 'brightest towards the south side',
            'c': 'considerably',
            'ch': 'chevelure',
            'co': 'coarse, coarsely',
            'com': 'cometic',
            'cont': 'in contact',
            'd': 'diameter',
            'def': 'defined',
            'dif': 'diffused',
            'diffic': 'difficult',
            'dist': 'distance or distant',
            'e': 'extremely, excessively',
            'ee': 'most extremely',
            'er': 'easily resolvable',
            'exc': 'excentric',
            'f': 'following',
            'g': 'gradually',
            'gr': 'group',
            'i': 'irregular',
            'iF': 'irregular figure',
            'inv': 'involved,involving',
            'l': 'little,long',
            'm': 'much',
            'mm': 'mixed magnitudes',
            'mn': 'milky nebulosity',
            'n': 'north',
            'neb': 'nebula',
            'nf': 'north following',
            'np': 'north preceding',
            'nr': 'near',
            'p': 'preceding',
            'pg': 'pretty gradually',
            'pm': 'pretty much',
            'ps': 'pretty suddenly',
            'quad': 'quadrilateral',
            'quar': 'quartile',
            'r': 'resolvable (mottled,not resolved)',
            'rr': 'partially relolved, some stars seen',
            'rrr': 'well resolved, clearly consisting of stars',
            's': 'south',
            'sc': 'scattered',
            'sev': 'several',
            'sf': 'south following',
            'sh': 'shaped',
            'sm': 'smaller',
            'sp': 'south preceding',
            'st': '9 13 stars from the 9th to 13th magnitude',
            'stell': 'stellar',
            'susp': 'suspected',
            'trap': 'trapezium',
            'triN': 'trinuclear',
            'v': 'very',
            'var': 'variable',
            'vv': 'very, very'}

def ngc_to_string(ngc_string):
    try:
        import pyparsing
    except ImportError:
        logging.error("Could not import pyparsing, string is uninterpreted")
        return ngc_string
    
    words = [pyparsing.Literal(k) for k in ngc_dict.keys()]
    expr = pyparsing.OneOrMore(pyparsing.Or(words))
    parsed_list = []
    
    for sentence in ngc_string.split(";"):
        try:
            parse = expr.parseString(sentence)
            parsed_list.append(" ".join(ngc_dict[c] for c in parse))
        except pyparsing.ParseException:
            logging.error("Error while parsing %s", sentence)
    
    if len(parsed_list) == 0:
        return ngc_string
    else:
        return "; ".join(parsed_list)