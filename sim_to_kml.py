#!/bin/python

## sim_to_kml converts flight sim data to KML
## Copyright (C) 2023  DiTRay

import pandas as pd
import yaml
import simplekml
import sys
from pathlib import Path
from datetime import datetime

def print_help():
    print('Usage: sim_to_kml.py src_file [dst_file]')
    print()
    print('Arguments:')
    print('  --help, -h    Print this help.')

def get_from_xp(csv_path, config, ctime):
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

def get_from_fg(csv_path, config, ctime):
    df = pd.read_csv(csv_path, delimiter=';')
    # Set real time
    df.time += ctime
    # Unify altitude to be less than 1
    df.alt -= 0.5
    df.hgt -= 0.5
        
    return df

def string_from_time(time, delim=':', second=False):
    dt = datetime.utcfromtimestamp(time)
    name  = '{:02d}'.format(dt.day) + '-' + \
            '{:02d}'.format(dt.month) + '-' + \
            str(dt.year) + ' ' + \
            '{:02d}'.format(dt.hour) + delim + \
            '{:02d}'.format(dt.minute)
    if second: 
        name += delim + '{:02d}'.format(dt.second)
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
    track_style.linestyle.width = 2.5
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
    return (lon, lat, meters(alt)) if hgt > 1 else (lon, lat)
    
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
    
def prepare_track(trk, in_air, stall, 
                  norm_track_style, stall_track_style):
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
        ls.style = norm_track_style
        
    return ls

def add_point(folder, lon, lat, alt, hgt, 
              time, hdg,
              ias, gs, tas, vs,
              data_style_map,
              name=None, msg=None,
              force_ground=False):
    time_str = string_from_time(time, delim=':', second=True)
    desc = '<![CDATA['
    if msg != None: desc += 'Event: ' + msg + '<br><br>'
    desc += 'Time/Date: '   + time_str + '<br>' + \
            'Hdg: '         + str(round(hdg)) + '<br>' + \
            'IAS: '         + str(round(ias)) + '<br>' + \
            'GS: '          + str(round(gs))  + '<br>' + \
            'TAS: '         + str(round(tas)) + '<br>' + \
            'Alt: '         + str(round(alt)) + '<br>' + \
            'Alt AGL: '     + str(round(hgt)) + '<br>' + \
            'VS: '          + str(round(vs))  + '<br><br>' + \
            'Generated by sim_to_kml'  + '<br>' + \
            'Copyright (C) 2023 ' + \
            '<a href="https://github.com/CMDR-DiTRay">DiTRay</a>' + \
            '<br>License: GNU GPLv3' + \
            ']]>'
    
    if name != None:
        pnt = folder.newpoint(name=name)
    else:
        pnt = folder.newpoint()
    
    if is_in_air(hgt) and not force_ground:
        pnt.altitudemode = 'absolute'
    pnt.stylemap = data_style_map
    pnt.coords = [format_coords(lon, lat, alt, hgt)]
    pnt.description = desc

def process_data(flt, trk, spec, dat,
                 no_trk_stl, st_trk_stl,
                 da_stl_map, sp_stl_map, st_stl_map):
    first = True
    for row_tuple in df.iterrows():
        row     = row_tuple[-1]
        time    = row.time
        lon     = row.lon
        lat     = row.lat
        alt     = row.alt
        hgt     = row.hgt
        hdg     = row.hdg
        vs      = row.vs
        ias     = row.ias
        gs      = row.gs
        tas     = row.tas
        flaps   = row.flp
        om      = (row.om > 0)
        mm      = (row.mm > 0)
        im      = (row.im > 0)
        hdg_thr = 10
        vs_thr  = 150
        in_air  = is_in_air(row.hgt)
        stall   = is_stall(row.stl)
        
        # On first iteration initialize variables
        if first:
            prev_in_air = in_air
            prev_stall  = stall
            prev_hdg    = hdg
            prev_vs     = vs
            prev_alt    = alt
            prev_hgt    = hgt
            prev_flaps  = flaps
            ls          = prepare_track(trk, in_air, stall, 
                                        no_trk_stl, st_trk_stl)
            coords      = [format_coords(lon, lat, alt, hgt)]
            flaps_move  = False
            marker      = False
            first       = False
            
            name = 'Start log'
            msg  = 'Started logging'
            add_point(spec, lon, lat, alt, hgt,
                      time, hdg, ias, gs, tas, vs,
                      sp_stl_map, name=name, msg=msg)
            continue
            
        # A walkaround to connect trajectories after landing
        if prev_in_air != in_air and not in_air:
            alt_fix = prev_alt
            hgt_fix = prev_hdg
        else:
            alt_fix = alt
            hgt_fix = hdg
            
        # If takeoff/landing place point on the ground
        if not stall and not prev_stall:
            force_ground = True
        else:
            force_ground = False
            
        if stall and not prev_stall:
            name = msg = 'Stall!!'
            
        if not stall and prev_stall:
            name = 'Recovered'
            msg  = 'Recovered from stall'
            
        if in_air and not prev_in_air:
            name = 'T/O'
            msg  = 'Takeoff'
            
        if not in_air and prev_in_air:
            name = 'T/D VS: ' + str(round(vs))
            msg  = 'Touchdown'
            
        if flaps != prev_flaps and not flaps_move:
            flaps_move = True
            
        if flaps == prev_flaps and flaps_move:
            flaps_str = str(round(flaps * 100)) + '%'
            name = 'Flaps ' + flaps_str
            msg  = 'Flaps set to ' + flaps_str
            add_point(spec, lon, lat, alt, hgt,
                      time, hdg, ias, gs, tas, vs,
                      sp_stl_map, name=name, msg=msg)
            coords += [format_coords(lon, lat, alt, hgt)]
            flaps_move = False
        
        prev_flaps = flaps
            
        # End/Start track
        if prev_in_air != in_air or prev_stall != stall:
            coords += [format_coords(lon, lat, alt_fix, hgt_fix)]
            ls.coords = coords
            ls = prepare_track(trk, in_air, stall, 
                               no_trk_stl, st_trk_stl)
            coords = [format_coords(lon, lat, alt, hgt)]
            
            add_point(spec, lon, lat, alt, hgt,
                      time, hdg, ias, gs, tas, vs,
                      sp_stl_map, name=name, msg=msg,
                      force_ground=force_ground)
            prev_hdg = hdg
            prev_vs  = vs
        
        name = None
        msg  = None
        
        if om and not marker:
            name = 'OM'
            msg  = 'Passed outer marker'
            coords += [format_coords(lon, lat, alt, hgt)]
            add_point(dat, lon, lat, alt, hgt,
                      time, hdg, ias, gs, tas, vs,
                      sp_stl_map,
                      name=name, msg=msg)
            prev_hdg = hdg
            prev_vs  = vs
            marker = True
            
        if mm and not marker:
            name = 'MM'
            msg  = 'Passed middle marker'
            coords += [format_coords(lon, lat, alt, hgt)]
            add_point(dat, lon, lat, alt, hgt,
                      time, hdg, ias, gs, tas, vs,
                      sp_stl_map,
                      name=name, msg=msg)
            prev_hdg = hdg
            prev_vs  = vs
            marker = True
        
        if im and not marker:
            name = 'IM'
            msg  = 'Passed inner marker'
            coords += [format_coords(lon, lat, alt, hgt)]
            add_point(dat, lon, lat, alt, hgt,
                      time, hdg, ias, gs, tas, vs,
                      sp_stl_map,
                      name=name, msg=msg)
            prev_hdg = hdg
            prev_vs  = vs
            marker = True
        
        if not (im or mm or om) and marker:
            marker = False
        
        # If direction deviation is more than threshold,
        # than add coords
        hdg_dev = abs(prev_hdg - hdg)
        vs_dev  = abs(prev_vs - vs)
        if hdg_dev > hdg_thr or (in_air and vs_dev > vs_thr):
            coords += [format_coords(lon, lat, alt, hgt)]
            add_point(dat, lon, lat, alt, hgt,
                      time, hdg, ias, gs, tas, vs,
                      da_stl_map,
                      name=name, msg=msg)
            prev_hdg = hdg
            prev_vs  = vs
            
        prev_alt = alt
        prev_hgt = hgt
        prev_in_air = in_air
        prev_stall  = stall
        ## End of main loop
        
    # Write unprocessed data
    coords += [format_coords(lon, lat, alt, hgt)]
    ls.coords = coords
    name = 'Stop log'
    msg  = 'Logging stopped'
    add_point(spec, lon, lat, alt, hgt,
              time, hdg, ias, gs, tas, vs,
              sp_stl_map, name=name, msg=msg)

def to_kml(df, ctime, file_path=None):
    # Generate document name by creation date/time
    kml_name = 'Flightlog ' + string_from_time(ctime, delim='.')
    # Generate flight folder name_from_time
    flt_name = 'Flightlog ' + string_from_time(df.time[0])
    
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
    
    process_data(flt, trk, spec, dat,
                 no_trk_stl, st_trk_stl,
                 da_stl_map, sp_stl_map, st_stl_map)
    
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
        print()
        print_help()
        exit(1)
    
    if sys.argv[1] in ['-h', '--help']:
        print_help()
        exit(0)
    csv_path = Path(sys.argv[1])
    
    fpath = None
    if len(sys.argv) > 2:
        if sys.argv[2] in ['-h', '--help']:
            print_help()
            exit(0)
        fpath = Path(sys.argv[2])
        
    sim = None
    
    # Read config
    script_name = __file__.split('/')[-1]
    script_dir  = __file__.split('/' + script_name)[0]
    
    with open(script_dir + '/config.yaml', 'r') as file:
        cfg = yaml.safe_load(file)

    # Identify sim
    ext = str(csv_path).split('.')[-1]
    if ext != 'txt' and ext != 'csv':
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
        df = get_from_xp(csv_path, cfg, ctime)
    if sim == 'fgfs':
        print('FlightGear data detected.')
        # Read file
        df = get_from_fg(csv_path, cfg, ctime)
    else:
        print('Simulator type unknown. Quitting...')
        exit(1)
    
    to_kml(df, ctime, fpath)
