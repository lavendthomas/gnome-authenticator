#!/usr/bin/python3

SERVICESFILE = 'services.json'
SERVICENAME = 'gnome-authentificator'

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
        self.serviceslen = len(services) # Used to track if we have to rebuild the entire List of services

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
        self.gen_listbox_of_services()


    def gen_listbox_of_services(self) :
        self.codes_listbox = Gtk.ListBox()
        self.codes_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.codes_listbox.set_border_width(0)
        self.add(self.codes_listbox)

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

            self.codes_listbox.add(row)
            self.listboxrows[service] = row, code, name, remaining_time # Use a tuple to add a to_show value in the future ?
        self.show_all()

    def new_service_window(self, widget) :
        self.new_service = Gtk.Dialog()
        self.new_service.set_transient_for(self)
        self.new_service.set_modal(True)

        # HeaderBar

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(False)
        header_bar.props.title = 'New'
        self.new_service.set_titlebar(header_bar)

        # Add buttons and remove native x button

        cancel_button = Gtk.Button(label='Cancel')
        cancel_button.connect('clicked', self.cancel_new_service_window)
        header_bar.pack_start(cancel_button)

        ok_button = Gtk.Button(label='Ok')
        ok_button.connect('clicked', self.ok_new_service_window)
        header_bar.pack_end(ok_button)

        # End of the HeaderBar

        content_area = self.new_service.get_content_area()
        content_area.set_border_width(18)

        main_grid = Gtk.Grid(column_spacing=6, row_spacing=12)
        content_area.add(main_grid)


        name_label = Gtk.Label(label='Name')
        name_label.set_xalign(1)
        main_grid.attach(name_label, 0, 0, 1, 1)


        key_label = Gtk.Label(label='Secret key')
        key_label.set_xalign(1)
        main_grid.attach(key_label, 0, 1, 1, 1)

        self.service_entry = Gtk.Entry()
        main_grid.attach(self.service_entry, 1, 0, 1, 1)

        self.secret_key = Gtk.Entry()
        self.secret_key.set_visibility(False)
        main_grid.attach(self.secret_key, 1, 1, 1, 1)

        self.new_service.resize(30,30)
        self.new_service.set_resizable(False)
        self.new_service.show_all()

    def cancel_new_service_window(self, widget) :
        self.new_service.destroy()

    def ok_new_service_window(self, widget) :
        global services
        global allow_refresh

        # Get values from user
        new_service = self.service_entry.get_text()
        new_key = self.secret_key.get_text()

        if new_service in services :
            # TODO Display an in-app notificaton
            already_added_dialog = Gtk.MessageDialog(parent=self,
                                          flags=Gtk.DialogFlags.MODAL,
                                          type=Gtk.MessageType.INFO,
                                          buttons=Gtk.ButtonsType.OK,
                                          message_format=new_service+" was already added. Please use another name.")
                                          #title="Name conflict")
            already_added_dialog.connect("response", self.ok_dialog)
            already_added_dialog.show()
        else :

            allow_refresh = False
            services.append(new_service)
            services.sort()
            jsonSaveList.save(services, SERVICESFILE)

            keyring.set_password(SERVICENAME, new_service, cleanSecret(new_key))

            #Add to the listbox
            allow_refresh = True
            try :
                self.refresh_codes(force=True)
            except ValueError as e :
                services.remove(new_service)
                jsonSaveList.save(services, SERVICESFILE)
                keyring.delete_password(SERVICENAME, new_service)

                bad_key_dialog = Gtk.MessageDialog(parent=self,
                                              flags=Gtk.DialogFlags.MODAL,
                                              type=Gtk.MessageType.ERROR,
                                              buttons=Gtk.ButtonsType.OK,
                                              message_format="Please check your key.\n\nError message :\n"+str(e))
                bad_key_dialog.connect("response", self.ok_dialog)
                bad_key_dialog.show()


                self.codes_listbox.destroy()
                self.gen_listbox_of_services()
                start_refresh()

        self.new_service.destroy()

    def remove_service_window(self, widget) :
        global services

        self.remove_service = Gtk.Dialog()
        self.remove_service.set_transient_for(self)
        self.remove_service.set_modal(True)

        # HeaderBar

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(False)
        header_bar.props.title = 'Delete'
        self.remove_service.set_titlebar(header_bar)

        # Add buttons and remove native x button

        cancel_button = Gtk.Button(label='Cancel')
        cancel_button.connect('clicked', self.cancel_remove_service_window)
        header_bar.pack_start(cancel_button)

        ok_button = Gtk.Button(label='Ok')
        ok_button.connect('clicked', self.ok_remove_service_window)
        header_bar.pack_end(ok_button)

        # End of the HeaderBar

        content_area = self.remove_service.get_content_area()
        content_area.set_border_width(0)

        self.remove_listbox = Gtk.ListBox()
        self.remove_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.remove_listbox.set_border_width(100)
        content_area.add(self.remove_listbox)

        for service in services :
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            box.set_border_width(12)
            label = Gtk.Label()
            label.set_markup('<big>'+service+'</big>')
            box.add(label)
            row.add(box)
            self.remove_listbox.add(row)

        self.remove_service.resize(30,30)
        self.remove_service.set_resizable(False)
        self.remove_service.show_all()

    def cancel_remove_service_window(self, widget) :
        self.remove_service.destroy()

    def ok_remove_service_window(self, widget) :
        global services
        global allow_refresh
        service_to_delete = self.remove_listbox.get_selected_row().get_children()[0].get_children()[0].get_text()

        allow_refresh = False

        keyring.delete_password(SERVICENAME,service_to_delete)
        services.remove(service_to_delete)
        jsonSaveList.save(services, SERVICESFILE)

        allow_refresh = True
        self.refresh_codes(force=True)

        self.remove_service.destroy()

    def ok_dialog(self, widget, response_id) :
        widget.destroy()

    def refresh_codes(self, force=False) :
        global services
        if len(services) == self.serviceslen : # Not service added or remove so just update the values
            remainingTime = 30 - ( int(time.time()) ) % 30

            for service in services :
                # Refresh timer
                self.listboxrows[service][3].set_markup('<big>'+str(remainingTime)+'</big>')

            if remainingTime == 30 or force :
                # Refresh One-Time code
                for service in services :
                    self.listboxrows[service][1].set_markup('<big><b>'+getTotpCode(keyring.get_password(SERVICENAME, service))+'</b></big>')
        else : # rebuild the main services listbox from __init__
            # self.remove(self.codes_listbox)
            self.codes_listbox.destroy()
            self.gen_listbox_of_services()
            self.serviceslen = len(services)

# class NewServiceWindow(Gtk.Dialog) :
#     def __int__(self, parent) :
#         Gtk.Dialog.__init__(self, "New", parent)
#         self.set_border_width(3)
#         self.set_default_size(150, 100)
#
#         self.header_bar = Gtk.HeaderBar()
#         self.header_bar.set_show_close_button(True) # TODO False
#         self.set_titlebar(self.header_bar)
#
#         # Ok and close buttons
#         self.close_button = Gtk.Button(label='Cancel')
#         self.close_button.connect('clicked', self.cancel)
#         self.header_bar.pack_end(self.close_button)
#
#         label = Gtk.Label("This is a dialog to display additional information")
#
#         box = self.get_content_area()
#         box.add(label)
#         self.show_all()
#
#     def cancel(self, widget) :
#         # Destoy the popup window
#         self.destoy()
#
#     def ok(self, widget) :
#         pass

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

def refreshCodes(manual=False) :
    global windowClosed
    global window
    while not windowClosed :
        if allow_refresh :
            window.refresh_codes()
            if not manual :
                time.sleep(1)


services = jsonSaveList.load(SERVICESFILE)
windowClosed = False
allow_refresh = True # Used to temporarily prevent the code to refresh


window = MainWindow()
window.connect('delete-event', Gtk.main_quit)
window.show_all()

def start_refresh() :
    refreshCodesThread = threading.Thread(target=refreshCodes)
    refreshCodesThread.start()

start_refresh()

Gtk.main()
windowClosed = True
