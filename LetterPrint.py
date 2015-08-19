# -*- coding: utf-8 -*-
from __future__ import division

import sys
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
except:
    print "Manjkajo GTK/Glade knjiznice"    
    sys.exit(1)
try:
    import getopt, sys, string, os
    from ConfigParser import ConfigParser as Cp
    import pango
    import cairo
    from xml.etree import ElementTree as ET
    from PIL import Image, ImageWin
    import tempfile as temp
    import random
except:
    print "Manjkajo nekatere knjiznice"
    sys.exit(1)
    
try:
    import win32print
    import win32ui
except:
    print "Manjka knjiznica win32print!"
    sys.exit(1)
    
try:
    from Printer import Printer
except:
    print "Manjka knjiznica za tiskanje oziroma v njej imas napako!"
    sys.exit(1)

def mm_to_pixel(mm,dpi=72):
    cm = mm/10;
    inch = cm/2.54

    if int(inch*dpi) == 0:
        return int(inch*dpi*100)
    else:
        return int(inch*dpi)
        
def font_size_to_pixel(size,dpi=72):
    return int((size*dpi)/72)


# Tole uproabljam za razvoj!
VERBOSE_NACIN = True

class LetterPrint:
    # Model, ki hrani vse uporabnika
    seznamUporabnikov = None
    # Kljuci, ki se uporabljajo za upravljanje z uporabniskimi programi
    _kljuci = ["m_naziv","m_ime","m_naslov","m_posta","m_drzava"]
    # Datoteka v kateri se hranijo prejemniki
    _datoteka = "Prejemniki.xml"
    _nastavitve = "Nastavitve.xml"
    # Parameter, ki pove ali urejamo nekega prejemnika ali ne
    urejanje = False
    # Interator, ki pove katerega prejemnika urejamo
    row_iter = None
    
    # Funkcija inicializira graficni vmestnik. Pokaze glavnoOkno iz gui.glade
    def __init__(self):
        self.gladefile = "gui.glade"
        
        if os.path.exists(self.gladefile) == False:
            print "GUI ne obstaja!"
            sys.exit(1);
        
        self.okno = gtk.glade.XML(self.gladefile, "glavnoOkno")
        dic = {"on_glavnoOkno_destroy" : self.izhod,
               "on_gumb_izhod_clicked" : self.izhod,
               "on_meni_izhod_gumb_activate" : self.izhod,
               "on_gumb_dodajPrejemnika_clicked":self.on_gumb_dodajPrejemnika_clicked,
               "on_drevo_row_activated":self.on_drevo_row_activated,
               "on_menu_dodaj_novega_activate":self.on_menu_dodaj_novega_activate,
               "on_oProgramuGumb_activate":self.on_oProgramuGumb_activate,
               "on_nastavitve_tistkanja_meni_activate":self.on_nastavitve_tistkanja_meni_activate,
               "on_tiskaj_izbor_activate":self.on_tiskaj_izbor_activate
               }
        
        self.drevo = self.okno.get_widget("drevo");
        # Nastavitev glave
        cell_t = gtk.CellRendererToggle()
        col = gtk.TreeViewColumn("Tiskaj",cell_t,active=5)
        col.set_resizable(False)       
        cell_t.connect("toggled",self.sprememba_toggle_tiskanje)
        self.drevo.append_column(col);
                
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn("Naziv",cell,text=0);
        col.set_sort_column_id(0);
        col.set_resizable(True)
        self.drevo.append_column(col);
        col = gtk.TreeViewColumn("Ime Priimek",cell,text=1)
        col.set_sort_column_id(1);
        col.set_resizable(True)
        self.drevo.append_column(col);
        col = gtk.TreeViewColumn("Naslov",cell,text=2)
        col.set_sort_column_id(2);
        col.set_resizable(True)
        self.drevo.append_column(col);
        col = gtk.TreeViewColumn("Pošta",cell,text=3)
        col.set_sort_column_id(3);
        col.set_resizable(True)
        self.drevo.append_column(col);
        col = gtk.TreeViewColumn("Država",cell,text=4)
        col.set_sort_column_id(4);
        col.set_resizable(True)       
        self.drevo.append_column(col);
        
        self.drevo.set_reorderable(True)
        self.okno.signal_autoconnect(dic);

        self.seznamUporabnikov = gtk.ListStore(str,str,str,str,str,bool);
        self.drevo.set_model(self.seznamUporabnikov);
        
        self.naloziModel();
    
    # Funkcija je klicana ko se zgodi izhod iz programa
    def izhod(self,p):
        if VERBOSE_NACIN:
            print("Hvala za uporabo!");
        self.shraniModel()
        sys.exit(0);
        
    # Funkcija zazena urejanje naslovnika. Poskrbi tudi za prikaz gumba brisanje
    def zazeniUrejanjeNaslovnika(self):
        self.oknoDodaj = gtk.glade.XML(self.gladefile, "urejanjePrejemnikaOkno")        
        self.urejanjePrejemnikaOkno = self.oknoDodaj.get_widget("urejanjePrejemnikaOkno");
        dic = {"on_shraniGumb_clicked":self.on_shraniGumb_clicked,
               "on_prekliciGumb_clicked":self.on_prekliciGumb_clicked,
               "on_zbrisiGumb_clicked":self.on_zbrisiGumb_clicked,
               "on_natisniGumb_clicked":self.on_tiskaj_izbor_activate}
        self.oknoDodaj.signal_autoconnect(dic);
        
        brisigum = self.oknoDodaj.get_widget("zbrisiGumb");
        natisnigum = self.oknoDodaj.get_widget("natisniGumb");
        if brisigum != None:
            brisigum.hide()
            if self.urejanje == True:
                brisigum.show()
                       
        if natisnigum != None:
            natisnigum.hide()
            if self.urejanje == True:
                natisnigum.show()
        
    def nastaviUrejanjeNaslovnika(self,param):
        for p in param:
            wid = self.oknoDodaj.get_widget(p);
            if wid != None:
                wid.set_text(param[p])
    
    def on_menu_dodaj_novega_activate(self,parameter):
        self.on_gumb_dodajPrejemnika_clicked(parameter)
        
    def on_oProgramuGumb_activate(self,param):
        self.oprog_d = gtk.glade.XML(self.gladefile, "oprogramuOkno")        
        self.urejanjePrejemnikaOkno = self.oprog_d.get_widget("oprogramuOkno");
        dic = {"on_gumbZapriOProgramu_clicked":self.on_gumbZapriOProgramu_clicked}
        self.oprog_d.signal_autoconnect(dic);

    # predogled in tiskanje
    tiskanje_izbora = False
    def on_tiskaj_izbor_activate(self,param):
        self.tiskanje_izbora = False
        if param.get_name() == "natisniGumb":
            if VERBOSE_NACIN:
                print "Tiskanje enega vnosa!"
            self.zacniOknoPredogled()
        else:
            if VERBOSE_NACIN:
                print "Tiskanje nabora vnosov!"
            self.tiskanje_izbora = True

            najden = False
            inc = 0
            for p in self.seznamUporabnikov:
                if p[5] == True:
                    self.u_data = {}
                    for inc in range(0,len(self._kljuci)):
                        if self._kljuci[inc] != None:
                            po = self._kljuci[inc];
                            self.u_data[po] = p[inc];
                    najden = True
                    break
                
            if najden:
                self.zacniOknoPredogled();

    # Zacetek predlogleda
    risalna = None # risalna povrsina za cairo!
    def zacniOknoPredogled(self):
        self.pred_tree = gtk.glade.XML(self.gladefile,"predogledTiskanja")
        self.predogledOkno = self.pred_tree.get_widget("predogledTiskanja");
        dic = {"on_predogledTiskanja_destroy":self.on_predogledTiskanja_destroy,
               "on_gumbZapri_clicked":self.on_predogledTiskanja_destroy,
               "on_gumbNatisni_clicked":self.on_gumbNatisni_clicked,
               "on_gumbObrni_clicked":self.on_gumbObrni_clicked,
               "on_povecava_change_value":self.on_povecava_change_value,
               "on_roboviCb_toggled":self.on_roboviCb_toggled,
               "on_gumbNastavitve_clicked":self.on_nastavitve_tistkanja_meni_activate
               }
        
        self.risalna = self.pred_tree.get_widget("risalna")
        self.risalna.connect("expose_event", self.expose)
        self.pred_tree.signal_autoconnect(dic);  
        
    def on_roboviCb_toggled(self,p):
        if p.get_active() == True:
            self.kuv_show_crte = True
        else:
            self.kuv_show_crte = False;
        self.predogledOkno.queue_draw()
         
    def on_gumbNastavitve_clicked(self,p):
        print "nastavitve..."
        
    # Funkcija se zgodi ko se prikaze povrsina oziroma zgodi expose!
    def expose(self, widget, event):
        context = widget.window.cairo_create()

        self.rp_sirina = event.area.width
        self.rp_visina = event.area.height
        context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        context.clip()
        self.draw(context)

    rp_sirina = 0;
    rp_visina = 0;
    kuv_show_crte = False
    zoom_faktor = 1
    rotacija = 0

    # Funkcija se klice vsakic ko je potreben redraw
    def draw(self, ctx):       
        dpi = 96;
         
        nastavitve = ET.ElementTree(file=self._nastavitve).getroot()
        odmik_desni = int(nastavitve.find("odmiki/odmik_od_desnega_roba").text)
        odmik_levi = int(nastavitve.find("odmiki/odmik_od_levega_roba").text)
        visina = int(nastavitve.find("kuverte/visina").text)
        sirina = int(nastavitve.find("kuverte/sirina").text)
        velikost_mm = (sirina,visina);
        
        pisava_x = nastavitve.find("pisava").text 
        spl = pisava_x.split(" ")
        pisava_size = font_size_to_pixel(int(spl[len(spl)-1]), dpi)

        if pisava_x.rfind(",") != -1:
            pisava = pisava_x[0:pisava_x.rfind(",")]
        else:
            pisava = pisava_x[0:pisava_x.rfind(" ")]

        velikost_pix = (mm_to_pixel(velikost_mm[0], dpi),
                        mm_to_pixel(velikost_mm[1], dpi))
        
        odmik_desno=mm_to_pixel(odmik_desni, dpi)
        odmik_spodaj=mm_to_pixel(odmik_levi, dpi)
        razmik_vrstice = mm_to_pixel(2, dpi)
        
        bes = self.u_data["m_naziv"]+" "+self.u_data["m_ime"]+"\n"+self.u_data["m_naslov"]+"\n"+"\n"+self.u_data["m_posta"];
        
        if self.u_data["m_drzava"] != "":
            bes+"\n"+self.u_data["m_drzava"]
        
        p = Printer()
        
        ctx.translate(self.rp_sirina/2, self.rp_visina/2);
        ctx.rotate(self.rotacija*(3.14/180));
        ctx.translate(-(self.rp_sirina/2),-(self.rp_visina/2));
        
        ctx.translate((self.rp_sirina-(velikost_pix[0]*self.zoom_faktor))/2,
                      (self.rp_visina-(velikost_pix[1]*self.zoom_faktor))/2)
        
        ctx.scale(self.zoom_faktor,self.zoom_faktor);

        ims = p.narediPNGKuverto(besedilo=bes,
                                 pisava = pisava,
                                 velikost_pisave = pisava_size,
                                 visina = velikost_pix[1],
                                 sirina = velikost_pix[0],
                                 odmik_desno = odmik_desno,
                                 odmik_spodaj = odmik_spodaj,
                                 razmik_vrstice = razmik_vrstice,
                                 show_crte=self.kuv_show_crte,
                                 ctx_p=ctx)
        
    # Poklicem otakrat ko je potrebno unicit tiskalno povrsino.
    def on_predogledTiskanja_destroy(self,p):
        self.predogledOkno.destroy()
    
    # Gumb ki sprozi tiskanje...
    def on_gumbNatisni_clicked(self,p):
        if self.tiskalnik == None:
            self.tiskalnik = win32print.GetDefaultPrinter()
            
        p = win32print.OpenPrinter(self.tiskalnik);
        t = (win32print.GetPrinter(p, 2)["pDevMode"])
        dpi = int(t.PrintQuality)
        
        if VERBOSE_NACIN:
            print "Pripravljam sliko za tiskalnik : "+self.tiskalnik

        nastavitve = ET.ElementTree(file=self._nastavitve).getroot()
        odmik_desni = int(nastavitve.find("odmiki/odmik_od_desnega_roba").text)
        odmik_levi = int(nastavitve.find("odmiki/odmik_od_levega_roba").text)
        visina = int(nastavitve.find("kuverte/visina").text)
        sirina = int(nastavitve.find("kuverte/sirina").text)
        velikost_mm = (sirina,visina);
        
        pisava_x = nastavitve.find("pisava").text 
        spl = pisava_x.split(" ")
        pisava_size = font_size_to_pixel(int(spl[len(spl)-1]), dpi)

        if pisava_x.rfind(",") != -1:
            pisava = pisava_x[0:pisava_x.rfind(",")]
        else:
            pisava = pisava_x[0:pisava_x.rfind(" ")]

        velikost_pix = (mm_to_pixel(velikost_mm[0], dpi),
                        mm_to_pixel(velikost_mm[1], dpi))
        
        odmik_desno=mm_to_pixel(odmik_desni, dpi)
        odmik_spodaj=mm_to_pixel(odmik_levi, dpi)
        razmik_vrstice = mm_to_pixel(2, dpi) 
        
        # Priprava besedila
        p = Printer()
 
        u_datalist = []
        if self.tiskanje_izbora:
            print "Tiskanje izbora..."
            inc = 0
            for px in self.seznamUporabnikov:
                if px[5] == True:
                    pom = {}
                    for inc in range(0,len(self._kljuci)):
                        if self._kljuci[inc] != None:
                            po = self._kljuci[inc];
                            pom[po] = px[inc];
                    pom["pot"] = self.nakljucna_pot()
                    u_datalist.append(pom)
            
        if not self.tiskanje_izbora:
            bes = self.u_data["m_naziv"]+" "+self.u_data["m_ime"]+"\n"+self.u_data["m_naslov"]+"\n"+"\n"+self.u_data["m_posta"];
            
            if self.u_data["m_drzava"] != "":
                bes+"\n"+self.u_data["m_drzava"]
                
            
            ims = p.narediPNGKuverto(besedilo=bes,
                                     pisava = pisava,
                                     velikost_pisave = pisava_size,
                                     visina = velikost_pix[1],
                                     sirina = velikost_pix[0],
                                     odmik_desno = odmik_desno,
                                     odmik_spodaj = odmik_spodaj,
                                     razmik_vrstice = razmik_vrstice,
                                     show_crte=self.kuv_show_crte)  
            file_name = self.nakljucna_pot()
                  
            if VERBOSE_NACIN:
                print "Shranjujem sliko na lokacijo : "+ file_name
            ims.write_to_png(file_name);
        else: #tiskanje izobra
            for pa in u_datalist:
                bes = pa["m_naziv"]+" "+pa["m_ime"]+"\n"+pa["m_naslov"]+"\n"+"\n"+pa["m_posta"];
                
                if pa["m_drzava"] != "":
                    bes+"\n"+pa["m_drzava"]
  
                ims = p.narediPNGKuverto(besedilo=bes,
                                         pisava = pisava,
                                         velikost_pisave = pisava_size,
                                         visina = velikost_pix[1],
                                         sirina = velikost_pix[0],
                                         odmik_desno = odmik_desno,
                                         odmik_spodaj = odmik_spodaj,
                                         razmik_vrstice = razmik_vrstice,
                                         show_crte=self.kuv_show_crte)       
                
                if VERBOSE_NACIN:
                    print "Pisem sliko : "+pa["pot"]
                
                ims.write_to_png(pa["pot"])         
                       
        
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(self.tiskalnik)
        
        PHYSICALWIDTH = 110
        PHYSICALHEIGHT = 111
        PHYSICALOFFSETX = PHYSICALWIDTH+2
        PHYSICALOFFSETY = PHYSICALHEIGHT+2
        LOGPIXELSX = 88
        LOGPIXELSY = 90
        HORZRES = 8
        VERTRES = 10
        printable_area = hDC.GetDeviceCaps (HORZRES), hDC.GetDeviceCaps (VERTRES)
        printer_size = hDC.GetDeviceCaps (PHYSICALWIDTH), hDC.GetDeviceCaps (PHYSICALHEIGHT)
        printer_margins = hDC.GetDeviceCaps (PHYSICALOFFSETX), hDC.GetDeviceCaps (PHYSICALOFFSETY)
        
        hDC.StartDoc ("Tiskanje nabora slik")
        if not self.tiskanje_izbora:
            bmp = Image.open (file_name)
            if self.rotacija != 0:
                bmp = bmp.rotate(self.rotacija)

            hDC.StartPage ()
            
            dib = ImageWin.Dib (bmp)
            desna_poravnava = not False
            negativni_odmik = False
            odm_levo = 0
            if desna_poravnava:
                odm_levo = (printer_size[0]-bmp.size[0])
            
            x1 = (-1)*int(printer_margins[0])+odm_levo
            y1 = (-1)*int((printer_size[1]-printable_area[1])/2)
            x2 = bmp.size[0] + (-1)*int((printer_size[0]-printable_area[0])/2)+odm_levo
            y2 = bmp.size[1] + (-1)*int((printer_size[1]-printable_area[1])/2)
    
            dib.draw (hDC.GetHandleOutput (), (x1, y1, x2, y2))
            hDC.EndPage ()
        else:
            for slika in u_datalist:
                bmp = Image.open (slika["pot"])
                if self.rotacija != 0:
                    bmp = bmp.rotate(self.rotacija)
                
                hDC.StartPage ()
                
                dib = ImageWin.Dib (bmp)
                desna_poravnava = not False
                negativni_odmik = False
                odm_levo = 0
                if desna_poravnava:
                    odm_levo = (printer_size[0]-bmp.size[0])
                
                x1 = (-1)*int(printer_margins[0])+odm_levo
                y1 = (-1)*int((printer_size[1]-printable_area[1])/2)
                x2 = bmp.size[0] + (-1)*int((printer_size[0]-printable_area[0])/2)+odm_levo
                y2 = bmp.size[1] + (-1)*int((printer_size[1]-printable_area[1])/2)
        
                dib.draw (hDC.GetHandleOutput (), (x1, y1, x2, y2))
                hDC.EndPage ()               

        hDC.EndDoc ()
        hDC.DeleteDC ()
        
        if VERBOSE_NACIN:
            print "Konec posiljanja slike v tiskalnik... "
            
        if VERBOSE_NACIN:
            print "Brisanje slik iz temp!"
            
        # Brisanje slik iz temp!
        if self.tiskanje_izbora:
            for slike in u_datalist:
                print "Brisem : "+slike["pot"]
                os.unlink(slike["pot"])
        else:
            print "Brisem : "+file_name
            os.unlink(file_name)
    
    # Gumb ki sprozi obracanje kovarte
    def on_gumbObrni_clicked(self,p):
        self.rotacija = self.rotacija + 90;
        if self.rotacija >= 360:
            self.rotacija = 0;
        self.predogledOkno.queue_draw()
    
    def nakljucna_pot(self):
        ime = ''
        for i in random.sample('abcdefghijklmnoprsABCDEFGH',5):
            ime += i
        file_name = os.path.join(temp.gettempdir(),ime+".png");
        return file_name
            
    # Event, ki se zgodi ko spreminjamo slider za zoom
    def on_povecava_change_value(self,a,b,z):
        self.zoom_faktor = (z/100)
        self.predogledOkno.queue_draw()
    
    # Nastavitve tiskanja run
    def on_nastavitve_tistkanja_meni_activate(self,param):
        self.nas_tree = gtk.glade.XML(self.gladefile, "nastavitveKuverte")        
        self.nastavitveOkno = self.nas_tree.get_widget("nastavitveKuverte");
        dic = {"on_shraniZapriGumb_clicked":self.on_shraniZapriGumb_clicked,
               "on_nastavitveKuverte_destroy":self.on_nastavitveKuverte_destroy,
               "on_m_tiskalnik_changed":self.on_m_tiskalnik_changed,
               "on_m_vrsta_k_changed":self.on_m_vrsta_k_changed,
               "on_spremeniPisavoGumb_clicked":self.on_spremeniPisavoGumb_clicked}
        
        self.m_odmik_desni = self.nas_tree.get_widget("m_odmik_desni");
        self.m_odmik_levi = self.nas_tree.get_widget("m_odmik_levi");
        self.m_vrsta_k = self.nas_tree.get_widget("m_vrsta_k");
        self.m_visina = self.nas_tree.get_widget("m_visina");
        self.m_sirina = self.nas_tree.get_widget("m_sirina");
        self.m_usmerjenost = self.nas_tree.get_widget("m_usmerjenost");
        self.m_tiskalnik = self.nas_tree.get_widget("m_tiskalnik");
        
        self.m_pisava_lab = self.nas_tree.get_widget("m_pisava_lab");
        self.m_pisava_dialog = gtk.FontSelectionDialog(title="Izbira pisave");
        self.m_pisava_dialog.connect("delete_event",self.on_pisd_delete_event)
        self.m_pisava_dialog.ok_button.connect("clicked",self.on_pisd_ok)
        self.m_pisava_dialog.cancel_button.connect("clicked",self.on_pisd_cancel)
        
        self.nas_tree.signal_autoconnect(dic);       
        self.naloziNastavitve()
    
    # Se zgodi ko zapremo urejevalnik kuverte
    def on_nastavitveKuverte_destroy(self,param):
        self.nastavitveOkno.destroy()
        
    # Ko klicemo gumb za zapiranje predogleda
    def on_shraniZapriGumb_clicked(self,param):
        try:
            self.predogledOkno.queue_draw()
        except AttributeError:
            pass
        self.shraniNastavitve();
        self.nastavitveOkno.destroy()
    
    # Ko kliknemo izhod iz 'O Programu'
    def on_gumbZapriOProgramu_clicked(self,param):
        self.urejanjePrejemnikaOkno.destroy()
    
    # Ko kliknemo dodaj prejemnika
    def on_gumb_dodajPrejemnika_clicked(self,parameter):
        self.zazeniUrejanjeNaslovnika()
        
    # Pobere spremenljivke ko pritisnemo shrani - se ne zapre
    def on_shraniGumb_clicked(self,param):
        pom = []
        for k in self._kljuci:
            wid = self.oknoDodaj.get_widget(k).get_text();
            if wid != None:
                pom.append(wid)
        
        if self.urejanje == True:
            k = 0;
            while k < len(self._kljuci):
                self.seznamUporabnikov.set_value(self.row_iter,k,pom[k])
                k = k + 1;
            self.shraniModel();
        else:
            pom.append([True])
            self.seznamUporabnikov.append(pom)
            self.shraniModel();
            
        self.urejanje = False;   
        self.row_iter = None;         
        self.urejanjePrejemnikaOkno.destroy()
    
    # Toogle printanje
    def sprememba_toggle_tiskanje(self,p,k):
        if self.seznamUporabnikov[k][5] == True:
            self.seznamUporabnikov[k][5] = False
        else:
            self.seznamUporabnikov[k][5] = True

    # Zapre dodajanje uporabnika
    def on_prekliciGumb_clicked(self,param):
        self.urejanjePrejemnikaOkno.destroy()
        
    # Brisanje prejemnika
    def on_zbrisiGumb_clicked(self,param):
        if self.urejanje == True:
            self.seznamUporabnikov.remove(self.row_iter)
            self.row_iter = None;
            self.urejanje = False;
            self.shraniModel(True)
            self.urejanjePrejemnikaOkno.destroy()
        
    # Vrstica aktivirana
    def on_drevo_row_activated(self,treeView,treePath,treeViewColumn):
        selection = self.drevo.get_selection()
        model, selection_iter = selection.get_selected()
        
        #TODO: Tole bi lahka mal bol lepo napisu!
        if selection_iter:
            m_naziv     = self.seznamUporabnikov.get_value(selection_iter, 0); 
            m_ime       = self.seznamUporabnikov.get_value(selection_iter, 1);
            m_naslov    = self.seznamUporabnikov.get_value(selection_iter, 2);
            m_posta     = self.seznamUporabnikov.get_value(selection_iter, 3);
            m_drzava    = self.seznamUporabnikov.get_value(selection_iter, 4);
            self.row_iter = selection_iter
            
        pom = [m_naziv,m_ime,m_naslov,m_posta,m_drzava]
        
        self.urejanje = True;
        self.zazeniUrejanjeNaslovnika()
        param = {"m_naziv":m_naziv,"m_ime":m_ime,"m_naslov":m_naslov,
                 "m_posta":m_posta,"m_drzava":m_drzava}
        self.u_data = param;
        self.nastaviUrejanjeNaslovnika(param)
        
    # Shrani model v xml
    def shraniModel(self,ne_nalozi=False):
        print "Shranjujem podatkovni model.."
        prejemniki = ET.Element("prejemniki");
        for p in self.seznamUporabnikov:
            prejemnik = ET.SubElement(prejemniki,"prejemnik");
            k = 0;
            while k < len(self._kljuci):
                prejemnik.set(self._kljuci[k],unicode( p[k], "utf-8" ));
                k = k + 1;

            if p[5] == True:
                prejemnik.set("m_tiskaj","True")
            else:
                prejemnik.set("m_tiskaj","False")
        tree = ET.ElementTree(prejemniki);
        tree.write(self._datoteka);
        
        if ne_nalozi == False:
            self.naloziModel()
        
    # Nalozi vsepodatke v formo
    def naloziModel(self):
        if VERBOSE_NACIN:
            print "Nalagam podatkovni model..."
        if os.path.exists(self._datoteka):
            self.seznamUporabnikov.clear()
            prejemniki = ET.ElementTree(file=self._datoteka).getroot()
            for p in prejemniki:
                k = 0;
                pom = []
                while k < len(self._kljuci):
                    pom.append(p.get(self._kljuci[k]))
                    k = k + 1;
                if p.get("m_tiskaj") == "True":
                    pom.append(True)
                else:
                    pom.append(False)
                self.seznamUporabnikov.append(pom)
                
    # Model tiskalnikov
    tiskalniki = None           # model
    tiskalnik = None            # trenuten tiskalnik
    tis_active = 0
    tipi_kuvert = None          # model  
    tipi_usmerjenost = None     # model
    
    # Nalozi podatki iz XMl dokumenta
    def naloziNastavitve(self):
        if VERBOSE_NACIN:
            print "Nalagam nastavitve...";
        
        nas_datoteka = self._nastavitve
        
        # naredim seznam tiskalnikov
        self.tiskalniki = gtk.ListStore(str);
        pp =0
        for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL):
            k = 0;
            while k < len(p):
                if k == 2:
                    self.tiskalniki.append([p[k]])
                    if VERBOSE_NACIN:
                        print "Dodajam tiskalnik : "+p[k]
                    if p[k] == win32print.GetDefaultPrinter():
                        self.tis_active = pp
                        self.tiskalnik = p[k]
                k = k + 1
            pp = pp + 1
        
        if os.path.exists(nas_datoteka):
            nastavitve = ET.ElementTree(file=nas_datoteka).getroot()
            self.m_odmik_desni.set_text(nastavitve.find("odmiki/odmik_od_desnega_roba").text)
            self.m_odmik_levi.set_text(nastavitve.find("odmiki/odmik_od_levega_roba").text)
            
            # Naredim seznam kuvert
            self.tipi_kuvert = gtk.ListStore(str,str,str);
            cell = gtk.CellRendererText()
            
            self.m_vrsta_k.pack_start(cell,True)
            self.m_vrsta_k.set_model(self.tipi_kuvert)
            self.m_vrsta_k.set_attributes(cell, text=0)
            i = 0
            for ku_tip in nastavitve.find("kuverte_seznam"):
                self.tipi_kuvert.append([ku_tip.get("ime"),
                                         ku_tip.get("visina"),
                                         ku_tip.get("sirina")])
                # Izberem izbrano kuverto
                if nastavitve.find("kuverte/zadnja_izbrana").text == ku_tip.get("ime"):
                    self.m_vrsta_k.set_active(i) 
                i = i + 1
                
            self.tipi_usmerjenost = gtk.ListStore(str,str)
            # Tuki more bit UTF-8!
            self.tipi_usmerjenost.append(["Ležeče","Lezece"])
            self.tipi_usmerjenost.append(["Stoječe","Stojece"])
            
            self.m_usmerjenost.pack_start(cell,True)
            self.m_usmerjenost.set_model(self.tipi_usmerjenost)
            self.m_usmerjenost.set_attributes(cell,text=0)
            
            self.m_usmerjenost.set_active(0)
            #print nastavitve.find("kuverte/usmerjenost").text
            if nastavitve.find("kuverte/usmerjenost").text != "Lezece":
                self.m_usmerjenost.set_active(1)

            # Izberem se ostale ze nastavljene parametre    
            self.m_visina.set_text(nastavitve.find("kuverte/visina").text)
            self.m_sirina.set_text(nastavitve.find("kuverte/sirina").text)       

        if self.m_tiskalnik != None:
            cell = gtk.CellRendererText()
            self.m_tiskalnik.pack_start(cell, True)
            self.m_tiskalnik.set_model(self.tiskalniki)
            self.m_tiskalnik.set_active(self.tis_active)
            self.m_tiskalnik.set_attributes(cell, text=0)
            
        pisava_x = nastavitve.find("pisava").text
        font = pango.FontDescription(pisava_x)
        self.m_pisava_lab.set_text(pisava_x)
        self.m_pisava_lab.modify_font(font)            
        self.m_pisava_dialog.set_font_name(pisava_x)
        
    # ko se spremeni tiskalnik?
    def on_m_tiskalnik_changed(self,p):
        self.tiskalnik = self.tiskalniki[p.get_active()][0]
    
    # Ko se spremeni vrsta papirja
    pap_ime = ""
    pap_vi = ""
    pap_si = ""
    def on_m_vrsta_k_changed(self,p):
        mod = p.get_model()
        it = mod.get_iter(p.get_active())
        self.m_visina.set_text(mod.get_value(it,1))
        self.m_sirina.set_text(mod.get_value(it,2))   
        self.pap_ime = mod.get_value(it,0)
        self.pap_vi = mod.get_value(it,1)
        self.pap_si = mod.get_value(it,2)
    
    def on_spremeniPisavoGumb_clicked(self,p):
        if VERBOSE_NACIN:
            print "Sprememba pisave dialog pognan!"
        self.m_pisava_dialog.run()
    
    # Klik na gumb preklici!
    def on_pisd_cancel(self,w):
        w.hide()
    
    # Klik na gumb OK!
    def on_pisd_ok(self,p):
        if VERBOSE_NACIN:
            print "Izbrana nova pisava : "+self.m_pisava_dialog.get_font_name()
        self.m_pisava_dialog.hide()
        font = pango.FontDescription(self.m_pisava_dialog.get_font_name())
        self.m_pisava_lab.set_text(self.m_pisava_dialog.get_font_name())
        self.m_pisava_lab.modify_font(font)
    
    # Zapiranje dialoga
    def on_pisd_delete_event(self,w,p):
        w.hide()

    def shraniNastavitve(self):
        if VERBOSE_NACIN:
            print "Shranjujem nastavitve";
        nastavitve = ET.Element("nastavitve");
        
        odmiki = ET.SubElement(nastavitve,"odmiki");
        odmik_od_desnega_roba = ET.SubElement(odmiki,"odmik_od_desnega_roba");
        odmik_od_desnega_roba.text = self.m_odmik_desni.get_text()
        odmik_od_levega_roba = ET.SubElement(odmiki,"odmik_od_levega_roba");
        odmik_od_levega_roba.text = self.m_odmik_levi.get_text()

        kuverte = ET.SubElement(nastavitve,"kuverte");
        zadnja_izbrana = ET.SubElement(kuverte,"zadnja_izbrana");
        zadnja_izbrana.text = self.pap_ime
        visina = ET.SubElement(kuverte,"visina");
        visina.text = self.m_visina.get_text()
        sirina = ET.SubElement(kuverte,"sirina");
        sirina.text = self.m_sirina.get_text()
        
        usmerjenost = ET.SubElement(kuverte,"usmerjenost");
        usmerjenost.text = self.tipi_usmerjenost[self.m_usmerjenost.get_active()][1]
        
        pisava = ET.SubElement(nastavitve,"pisava");
        pisava.text = self.m_pisava_lab.get_text()
        
        #tiskalnik = ET.SubElement(nastavitve, "tiskalnik")
        #tiskalnik.text = self.tiskalnik
        
        #kopiranje obstojecih kovert nazaj...
        kuverte_seznam = ET.SubElement(nastavitve,"kuverte_seznam");
        for k in self.tipi_kuvert:
            kuverta = ET.SubElement(kuverte_seznam,"kuverta");
            kuverta.set("ime",k[0])
            kuverta.set("sirina",k[2]) 
            kuverta.set("visina",k[1])           
        
        tree = ET.ElementTree(nastavitve);
        tree.write(self._nastavitve);    
        
if __name__ == "__main__":
    program = LetterPrint()
    gtk.main()
