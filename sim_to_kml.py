#!/bin/python

import pandas as pd
import yaml
import simplekml
import sys
from pathlib import Path
from datetime import datetime

def get_xp(csv_path, config, ctime):
    cfg = config['xp11']
    # Get good columns
    good_cols = list(cfg.values())
    # Prepare dictionary to rename columns
    ren_dict  = {v: k for k, v in cfg.items()}
    # Read CSV
    df = pd.read_csv(csv_path, delimiter='\s*\|\s*', engine='python')
    # Delete unneeded columns
    bad_cols = (set(df.columns) - set(good_cols))
    df = df.drop(columns=bad_cols)
    ## Rename columns
    df = df.rename(columns=ren_dict)
    # Set real time
    df.time += ctime
        
    return df

def set_stylemaps(kml):
    return []

def add_style_points(kml_buf):
    
    
    return kml_buf

def name_from_time(time, delim=':'):
    dt = datetime.fromtimestamp(time)
    name  = 'Flightlog ' 
    name += '{:02d}'.format(dt.day) + '-' 
    name += '{:02d}'.format(dt.month) + '-' 
    name += str(dt.year) + ' '
    name += '{:02d}'.format(dt.hour) + delim
    name += '{:02d}'.format(dt.minute)
    return name
    
# Return regular trajectory style
def norm_track_style():
    track_style = simplekml.Style()
    track_style.linestyle.color = 'ff00ff00'
    track_style.linestyle.width = 2
    track_style.polystyle.color = '7fff0000'
    track_style.polystyle.outline = 1
    return track_style

# Return stall trajectory style
def stall_track_style():
    track_style = simplekml.Style()
    track_style.linestyle.color = 'ff0000ff'
    track_style.linestyle.width = 2
    track_style.polystyle.outline = 1
    track_style.polystyle.color = '7f0000ff'
    return track_style

# Return pecial placemarks style map
def special_style_map():
    # Normal
    s_stl_n = simplekml.Style()
    s_ico_stl_n  = s_stl_n.iconstyle
    s_ico_stl_n.color = 'ffff0000'
    s_ico_stl_n.scale = 0.6
    s_ico_stl_n.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/cross-hairs.png'
    s_stl_n.labelstyle.color = 'ff7fffff'
    # Highlighted
    s_stl_h = simplekml.Style()
    s_ico_stl_h  = s_stl_h.iconstyle
    s_ico_stl_h.color = 'ffff0000'
    s_ico_stl_h.scale = 0.6
    s_ico_stl_h.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/cross-hairs_highlight.png'
    s_stl_h.labelstyle.color = 'ff7fffff'
    # Create placemarks style map
    spec_smap = simplekml.StyleMap(
        normalstyle=s_stl_n,
        highlightstyle=s_stl_h)
    return spec_smap

def stall_style_map():
    # Normal
    s_stl_n = simplekml.Style()
    s_ico_stl_n  = s_stl_n.iconstyle
    s_ico_stl_n.color = 'ff0000ff'
    s_ico_stl_n.scale = 0.6
    s_ico_stl_n.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/cross-hairs.png'
    s_stl_n.labelstyle.color = 'ff7fffff'
    # Highlighted
    s_stl_h = simplekml.Style()
    s_ico_stl_h  = s_stl_h.iconstyle
    s_ico_stl_h.color = 'ff0000ff'
    s_ico_stl_h.scale = 0.6
    s_ico_stl_h.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/cross-hairs_highlight.png'
    s_stl_h.labelstyle.color = 'ff7fffff'
    # Create placemarks style map
    spec_smap = simplekml.StyleMap(
        normalstyle=s_stl_n,
        highlightstyle=s_stl_h)
    return spec_smap
    return

def data_style_map():
    # Flight data style
    # Normal
    d_stl_n   = simplekml.Style()
    d_ico_stl_n = d_stl_n.iconstyle
    d_ico_stl_n.color = 'ff0000ff'
    d_ico_stl_n.scale = 0.15
    d_ico_stl_n.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    # Highlighted
    d_stl_h   = simplekml.Style()
    d_ico_stl_h = d_stl_h.iconstyle
    d_ico_stl_h.color = 'ff0000ff'
    d_ico_stl_h.scale = 0.4
    d_ico_stl_h.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    dat_smap = simplekml.StyleMap(
        normalstyle=d_stl_n,
        highlightstyle=d_stl_h)
    return dat_smap

def meters(feet):
    return feet * 0.3048

def format_coords(lon, lat, alt, hgt):
    return (lon, lat) if hgt < 1 else (lon, lat, meters(alt))
    
def is_in_air(hgt: float) -> bool:
    return True if hgt > 1 else False

def is_stall(stl: float) -> bool:
    return True if stl > 0 else False

def track_name(in_air: bool, stall: bool) -> str:
    if stall:
        return 'Stall!!'
    if in_air:
        return 'In the air'
    return 'On Ground'
    
def prepare_track(trk, in_air, stall):
    ls = trk.newlinestring(name=track_name(in_air, stall))
    
    ls.extrude    = 1
    ls.tessellate = 1
    
    if in_air:
        ls.altitudemode = 'absolute'
    else:
        ls.altitude = 0
        
    if stall:
        ls.style = stall_track_style
    else:
        ls.style = norm_track_style()
        
    return ls

def kml_debug(kml):
    flt_name = name_from_time(df.time[0])
    
    no_trk_stl = norm_track_style()
    st_trk_stl = stall_track_style()
    da_stl_map = data_style_map()
    sp_stl_map = special_style_map()
    st_stl_map = stall_style_map()
    
    # File and structure
    doc  = kml.document
    flt  = doc.newfolder(name='Flight')
    trk  = flt.newfolder(name=flt_name)
    spec = doc.newfolder(name='Special placemarks')
    dat  = doc.newfolder(name='Flight data')
    
    # Data elements
    # LineStyle
    ls = trk.newlinestring(name='In the air')
    ls.tessellate = 0
    ls.extrude = 1
    ls.altitudemode = 'absolute'
    ls.style = no_trk_stl
    ls.coords = [
        (48.229854523436, 54.2741259977851, 250),
        (48.2276952650135, 54.2719542330365, 270)]
    
    ls = trk.newlinestring(name='In the air')
    ls.tessellate = 0
    ls.extrude = 1
    ls.altitudemode = 'absolute'
    ls.style = st_trk_stl
    ls.coords = [
        (48.2276952650135, 54.2719542330365, 270),
        (48.2255303746956, 54.2699138552678, 240)]
    
    # Point
    pnt = spec.newpoint(name='Start log')
    pnt.stylemap = sp_stl_map
    pnt.coords = [(48.229854523436, 54.2741259977851)]
    
    pnt = dat.newpoint()
    pnt.altitudemode = 'absolute'
    pnt.stylemap = da_stl_map
    pnt.coords = [(48.2276952650135, 54.2719542330365, 270)]
    pnt.description = 'By DiTRay'
    
    pnt = spec.newpoint(name='Stall!!')
    pnt.altitudemode = 'absolute'
    pnt.stylemap = st_stl_map
    pnt.coords = [(48.2255303746956, 54.2699138552678, 240)]

def to_kml(df, ctime, file_path=None):
    # Generate document name by creation date/time
    kml_name = name_from_time(ctime, delim='.')
    # Generate flight folder name_from_time
    flt_name = name_from_time(df.time[0])
    
    no_trk_stl = norm_track_style()
    st_trk_stl = stall_track_style()
    da_stl_map = data_style_map()
    sp_stl_map = special_style_map()
    st_stl_map = stall_style_map()
    
    # File and structure
    kml  = simplekml.Kml(name=kml_name)
    doc  = kml.document
    flt  = doc.newfolder(name='Flight')
    trk  = flt.newfolder(name=flt_name)
    spec = doc.newfolder(name='Special placemarks')
    dat  = doc.newfolder(name='Flight data')
    
    #kml = kml_debug(kml)
    
    first = True
    for row_tuple in df.iterrows():
        row = row_tuple[-1]
        lon = row.lon
        lat = row.lat
        alt = row.alt
        hgt = row.hgt
        in_air = is_in_air(row.hgt)
        stall  = is_stall(row.stl)
        
        print(hgt)

        ## Main loop
        # End last track
        if not first and (prev_in_air != in_air or prev_stall != stall):
            print('Write track')
            ls = prepare_track(trk, prev_in_air, prev_stall)
            ls.coords = coords
        
        # Start new track
        if first or prev_in_air != in_air or prev_stall != stall:
            print('New track')
            coords = []
            
        coords += [format_coords(lon, lat, alt, hgt)]
            
        # Prepare for next iteration
        prev_in_air = in_air
        prev_stall  = stall
        if first:
            first = False
        ## End of main loop
    
    ls = prepare_track(trk, prev_in_air, prev_stall)
    ls.coords = coords
    
    # Saving
    if file_path == None:
        fpath = str(Path.cwd())
        fpath += '/' + kml_name + '.kml'
    else:
        fpath = str(file_path)
        
    print('Saving ' + fpath)
    kml.save(fpath)
    

if __name__ == "__main__":
    # Check if argumente received
    if len(sys.argv) == 1:
        print('Missing log file as argument. Quitting...')
        exit(1)
    csv_path = Path(sys.argv[1])
    
    fpath = None
    if len(sys.argv) > 2:
        fpath = Path(sys.argv[2])
        
    sim = None
    
    # Read config
    script_name = __file__.split('/')[-1]
    script_dir  = __file__.split('/' + script_name)[0]
    
    with open(script_dir + '/config.yaml', 'r') as file:
        cfg = yaml.safe_load(file)

    # Identify sim
    ext = str(csv_path).split('.')[-1]
    if ext != 'txt' and ext != 'scv':
        print('Unknown file type. Quitting...')
        exit(1)
    if ext == 'txt':
        sim = 'xp11'
    if ext == 'csv':
        sim = 'fgfs'
        
    # File creation time
    ctime = csv_path.stat().st_mtime
        
    if sim == 'xp11':
        print('X-Plane 11 data detected.')
        # Read file
        df = get_xp(csv_path, cfg, ctime)
    
    to_kml(df, ctime, fpath)
