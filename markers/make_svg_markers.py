#!/usr/bin/env python
"""
#
# By: Charles Brandt [code at charlesbrandt dot com]
# On: *2012.09.27 17:52:10 
# License:  MIT 

# Requires:
# svgfig.py

# Description:
# generate markers for use in playlist sorting

"""
from __future__ import print_function
import re

#2.0 alpha uses a viewer that doesn't work out of the box
#needs rsvg, which I don't have installed here
#from svgfig import SVG
"""
loop through a list of markers
if not overwriting,
check if marker exists

generate a single SVG based on current item

then go through and regenerate all pngs

then make a playlist that can be easily loaded in a media player (m3u)
"""
#from svgfig.svg import SVG

#this uses svgfig version 1.x:
#from svgfig import *
from svgfig import SVG, Text, Fig, canvas
#1.0 seems sufficient for my needs

#for documentation, see:
#http://code.google.com/p/svgfig/wiki/Introduction

#lounge, calm, chill, move, 
markers = [ 'relax', 'sleep', 'meditate', 'link', 'love', 'other', 'dance', 'work', 'captain', 'rock', 'podcast', 'jazz', 'dinner', 'highschool', 'disco', 'classics', 'classic_rock', '80s', '90s', 'club', 'hip_hop', 'toget', 'vinyl', 'work' ]

#this is in pixels:
font_size = "240"
line_height = 50

#this shows some (not system level ones)
#ls ~/Library/Fonts/
# can also use inkscape

# python list all fonts available via system:
#http://stackoverflow.com/questions/1113040/list-of-installed-fonts-os-x-c
try:
    import Cocoa
    manager = Cocoa.NSFontManager.sharedFontManager()
    font_families = list(manager.availableFontFamilies())
    print(font_families)
except:
    print("Not on a mac it seems")

#AveriaLibre-Regular, Asap-Regular, ArchitectsDaughter, AnonymousPro-Regular, AdventPro-Regular, CabinSketch-Regular, Condiment-Regular, Dosis-Regular, IMFePIrm28P, NanumGothic-Regular, Nunito-Regular, PoiretOne-Regular, Quicksand-Regular, Rokkitt-Regular, Sacramento-Regular, Simonetta-Regular, TerminalDosis-Regular, 

#fonts = [ "Rancho-Regular", "Yesteryear-Regular", "Oregano-Regular", "PrincessSofia-Regular", "Cookie-Regular", "Yellowtail-Regular", "Radley-Italic", "Amiri-BoldSlanted", "BerkshireSwash-Regular", "Courgette-Regular", "Allura-Regular", "DroidSerif-BoldItalic", "Satisfy-Regular", "BadScript-Regular", "Condiment-Regular", "Damion-Regular", "Engagement-Regular", "Fascinate-Regular", "Federo-Regular", "Fondamento-Regular", "Handlee-Regular", "Lobster", "MrDafoe-Regular", "MrsSheppards-Regular",  ]

#main = Fig()
#collection = []

counter = 1
font = "IMFePIrm28P"
font = "AveriaLibre-Regular"
for content in markers:
    g = SVG("g", fill_opacity="50%", transform="translate(175, 0)")
    
    parts = font.split('-')
    name = parts[0]
    #if using styling in font name, may need to split by camel case too:
    #name = re.sub("([a-z])([A-Z])","\g<1> \g<2>",name)
    #(or you can do that manually when it is needed)
    print(name)

    bold = False
    italic = False
    if len(parts) > 1:
        properties = parts[1]
        if re.search("Bold", properties):
            bold = True

        if re.search("Italic", properties):
            italic = True

        if re.search("Slanted", properties):
            italic = True

    style = "fill:#000000;fill-opacity:1;stroke:none;"
    style += "font-size:%spx;" % font_size
    if bold:
        style += "font-weight:bold;"
    else:
        style += "font-weight:normal;"

    if italic:
        style += "font-style:italic;"
    else:
        style += "font-style:normal;"

    style += "font-family:%s" % name
    #t1 = SVG("text", content, x=0, y=line_height, style=style)
    t1 = SVG("text", content, x=-128, y=300, style=style)
    counter += 1
    g.append(t1)


    svg = canvas()
    width = 90
    svg.attr['viewBox'] = "0 0 %s %s" % (width, line_height*counter)
    svg.attr['width'] = width
    svg.attr['height'] = line_height

    svg.sub.append(g)
    svg.save("%s.svg" % content)


#this works:
#g = SVG("g", *collection, fill_opacity="50%")
#g.save("tmp.svg")
#main.save("tmp.svg")
