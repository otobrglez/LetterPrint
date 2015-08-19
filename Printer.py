# -*- coding: utf-8 -*-
from __future__ import division

import sys
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gtk.glade
    import getopt, sys, string, os
    from ConfigParser import ConfigParser as Cp
    import pango
    import cairo
    from xml.etree import ElementTree as ET
    import win32print
    import win32ui
    from PIL import Image, ImageWin
    import win32print

except:
    print "Manjka knjiznica win32print!"
    sys.exit(1)
      
class Printer:
    # Spremeni navadn HEX RGB vbedn CAIRO tupple
    def hex_to_rgba(self,color):
        if not (isinstance(color, str) or isinstance(color, unicode)):
            try:
                r,g,b,a = color
                return r,g,b,a
            except (TypeError, ValueError):
                pass
        
        color = color.replace("#", "")
        if len(color) in [3,4]:
            color = "".join([c*2 for c in color])
        
        hex_r, hex_g, hex_b = color[:2], color[2:4], color[4:6]
        hex_a = color[6:8]
        if not hex_a:
            hex_a = "ff"
        
        return map(lambda x: int(x, 16)/255.0, [hex_r, hex_g, hex_b, hex_a])

    # Naredi cairo surface
    def narediPNGKuverto(self,
                         besedilo,pisava,
                         visina=500,
                         sirina=600,
                         velikost_pisave=20,
                         odmik_desno=60,
                         odmik_spodaj=60,
                         razmik_vrstice=10,
                         show_crte=False,
                         podlaga_p=None,
                         ctx_p=None):
        
        #print "narediPNGKuverto("+str(visina)+","+str(sirina)+")";
        
        velikost_slike = {"visina":visina,"sirina":sirina}
        if podlaga_p == None:
            podlaga = cairo.ImageSurface(cairo.FORMAT_ARGB32, velikost_slike["sirina"], velikost_slike["visina"])
        else:
            podlaga = podlaga_p;
            
        if ctx_p == None:
            ctx = cairo.Context(podlaga)
        else:
            ctx = ctx_p;
            
        font_options = podlaga.get_font_options()
        font_options.set_antialias(cairo.ANTIALIAS_GRAY)
    
        ctx.set_line_width(2)
        ctx.set_source_rgb(1, 1, 1)
        ctx.move_to(0,0)
        ctx.line_to(velikost_slike["sirina"],0) #zgoraj desno
        ctx.line_to(velikost_slike["sirina"],velikost_slike["visina"]) # spodaj desno
        ctx.line_to(0,velikost_slike["visina"])
        ctx.close_path()
        ctx.fill()
        ctx.stroke()

        font = pisava
        ctx.set_source_rgb(0, 0, 0)
        ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(velikost_pisave)
        #besedilo = 'g. Oto Brglez ml.\nKavče 35\n3320 Velenje\nSlovenija'
        
        vrsta_c = 0
        height_p = 0
        besedilo_razbito = besedilo.split('\n')
        stevilo_vrst = len(besedilo_razbito)
        besedilo_razbito.reverse()
        
        max_sirina = 0
        for vrsta in besedilo_razbito:
            x_bearing, y_bearing, width, height = ctx.text_extents(vrsta)[:4]
            if width > max_sirina:
                max_sirina = width
        
        for vrsta in besedilo_razbito:
            x_bearing, y_bearing, width, height = ctx.text_extents(vrsta)[:4]
            if vrsta_c == 0:
                height_p = height
            else:
                height = height_p
            
            # Malce matematike ;)
            ctx.move_to(velikost_slike["sirina"]-(max_sirina+odmik_desno),
                        velikost_slike["visina"]-
                        (vrsta_c*(razmik_vrstice+height))
                        -odmik_spodaj)
            vrsta_c = vrsta_c + 1
            ctx.text_path(vrsta)
            ctx.set_line_width(0.5)
            ctx.stroke_preserve()
            ctx.fill()

        if show_crte:
            # navpicna crta
            
            rdeca = self.hex_to_rgba("#990000");
            zelena = self.hex_to_rgba("#339900");
            ctx.set_source_rgba(zelena[0],zelena[1],zelena[2]);
            
            ctx.set_line_width(2)
            ctx.move_to(velikost_slike["sirina"]-odmik_desno,0)
            ctx.line_to(velikost_slike["sirina"]-odmik_desno,velikost_slike["visina"])

            ctx.move_to(0,velikost_slike["visina"]-odmik_spodaj)
            ctx.line_to(velikost_slike["sirina"],velikost_slike["visina"]-odmik_spodaj)
            ctx.stroke()   
            
            ctx.set_source_rgba(rdeca[0],rdeca[1],rdeca[2]);
            ctx.set_line_width(4)
            ctx.move_to(0,0)
            ctx.line_to(0,velikost_slike["visina"])
            ctx.line_to(velikost_slike["sirina"],velikost_slike["visina"])
            ctx.line_to(velikost_slike["sirina"],0)
            ctx.close_path()
            ctx.stroke()  
            
        self.context = ctx;
        return podlaga
    
    
def mm_to_pixel(mm,dpi=72):
    cm = mm/10;
    inch = cm/2.54
    #return int(inch*dpi)
    print "tr:" +str(inch*dpi)
    if int(inch*dpi) == 0:
        return int(inch*dpi*100)
    else:
        return int(inch*dpi)
        
def font_size_to_pixel(size,dpi=72):
    return int((size*dpi)/72)

if __name__ == "__main__":
    print "Zagon za potrebe testa!"
    velikost_mm = (150,100); #mm!
    
    dpi = 96 # tolk ma enkran!
    #dpi = 300 # tolk ma pa moj printet
    #dpi = 600 # doma
    
    velikost_pix = (mm_to_pixel(velikost_mm[0], dpi),mm_to_pixel(velikost_mm[1], dpi))
    pisava_size = font_size_to_pixel(18, dpi)
    odmik_desno=mm_to_pixel(10, dpi)
    odmik_spodaj=mm_to_pixel(20, dpi)
    razmik_vrstice = mm_to_pixel(2, dpi)

    p = Printer()
    ims = p.narediPNGKuverto(besedilo="g.\nOto Brglez\nKavče 35,x\n3320 Velenje\nSlovenija",
                             pisava="Calibri",
                             velikost_pisave = pisava_size,
                             visina = velikost_pix[1],
                             sirina = velikost_pix[0],
                             odmik_desno = odmik_desno,
                             odmik_spodaj = odmik_spodaj,
                             razmik_vrstice = razmik_vrstice,
                             show_crte=True)
    
    ims.write_to_png("slika.png")
    
    
    print p.hex_to_rgba("#FF0000");
    print "Done..."
    
    