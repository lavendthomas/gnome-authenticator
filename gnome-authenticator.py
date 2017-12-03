#!/usr/bin/python3

SERVICESFILE = 'services.json'
SERVICENAME = 'simple-authentificator'

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import jsonSaveList
import pyotp
import keyring
import time
import threading

class MainWindow(Gtk.Window) :

    def __init__(self) :
        global services
        Gtk.Window.__init__(self, title="Authentificator")
        self.set_border_width(50)

        # Headerbar
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.props.title = 'Authentificator'
        self.set_titlebar(self.header_bar)

        # New button
        self.new_button = Gtk.Button(label='New')
        self.new_button.connect("clicked", self.new_service_window)
        self.header_bar.pack_start(self.new_button)

        # Delete Button
        self.delete_button = Gtk.Button(label='Delete')
        self.delete_button.connect("clicked", self.remove_service_window)
        self.header_bar.pack_start(self.delete_button)


        # List of services

        codes_listbox = Gtk.ListBox()
        codes_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        codes_listbox.set_border_width(0)
        self.add(codes_listbox)

        # For eath service add a new item to the list

        self.listboxrows = dict()

        remainingTime = 30 - ( int(time.time()) ) % 30

        for service in services :
            row = Gtk.ListBoxRow()
            mainBox = Gtk.Box()
            mainBox.set_border_width(10)
            mainGrid = Gtk.Grid(column_spacing=200)
            mainBox.add(mainGrid)
            row.add(mainBox)

            code = Gtk.Label()
            code.set_markup('<big><b>'+getTotpCode(keyring.get_password(SERVICENAME, service))+'</b></big>')
            name = Gtk.Label(label=service)
            code_and_name = Gtk.Grid()
            code_and_name.attach(code, 0, 0, 1, 1)
            code_and_name.attach_next_to(name, code, Gtk.PositionType.BOTTOM, 1, 1)

            time_box = Gtk.Box(spacing=5)
            remaining_time = Gtk.Label()
            remaining_time.set_markup('<big>'+str(remainingTime)+'</big>')
            time_box.add(remaining_time)

            mainGrid.attach(code_and_name, 0, 0, 1, 1)
            mainGrid.attach_next_to(time_box, code_and_name, Gtk.PositionType.RIGHT, 1, 1  )

            codes_listbox.add(row)
            self.listboxrows[service] = row, code, name, remaining_time # Use a tuple to add a to_show value in the future ?



    def new_service_window(self, widget) :
        print('New !')
        pass

    def remove_service_window(self, widget) :
        print('Remove !')
        pass

    def refresh_codes(self, force=False) :
        global services
        remainingTime = 30 - ( int(time.time()) ) % 30

        for service in services :
            # Refresh timer
            self.listboxrows[service][3].set_markup('<big>'+str(remainingTime)+'</big>')

        if remainingTime == 30 or force :
            # Refresh One-Time code
            for service in services :
                self.listboxrows[service][1].set_markup('<big><b>'+getTotpCode(keyring.get_password(SERVICENAME, service))+'</b></big>')



def cleanSecret(secret) :
    returnSecret = str()
    for c in secret :
        if c.isalnum() :
            returnSecret += c
    return returnSecret

def getTotpCode(secret) :
    secret = cleanSecret(secret)
    totp = totp = pyotp.TOTP(secret)
    return totp.now() # The code is a str, not an int

def refreshCodes() :
    global windowClosed
    global window
    while not windowClosed :
        window.refresh_codes()
        time.sleep(1)


services = jsonSaveList.load(SERVICESFILE)
windowClosed = False

window = MainWindow()
window.connect('delete-event', Gtk.main_quit)
window.show_all()

refreshCodesThread = threading.Thread(target=refreshCodes)
refreshCodesThread.start()

Gtk.main()
windowClosed = True