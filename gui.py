#!/usr/bin/python

import sys
import re
import threading
import time
import signal
import urllib.request, urllib.error, urllib.parse
import json
import os.path
from bs4 import BeautifulSoup
from gi.repository import Gtk, GObject, GLib

import au

class AnimeDl(object):
    def __init__(self):
        self.ep = []
        self.percent = 0
        self.verbose = True

    def set_list(self, episode_id, to_add=-1):
        store = interface.get_object('liststore1')
        spinner = interface.get_object('spinner1')
        spinner.start()
        spinner.show()
        i = 0
        while episode_id != None and (i < to_add or to_add == -1):
            self.ep.append(au.Episode(episode_id))
            self.ep[-1].get_metadata()
            episode_id = self.ep[-1].next_id
            self.ep[-1].treeiter = store.append([self.ep[-1].episode_id, self.ep[-1].title, int(self.ep[-1].size), 0, ""])
            i += 1
        spinner.hide()

    def update_url(self, ep):
        store = interface.get_object('liststore1')
        store[ep.treeiter][4] = ep.episode_url
        return (False)

    def update_percent(self, ep):
        store = interface.get_object('liststore1')
        store[ep.treeiter][3] = self.percent
        if self.percent == 100:
            return (False)
        return (True)

    def update_treestore(self, ep, dl):
        GLib.timeout_add_seconds(1, self.update_percent, ep)
        GLib.timeout_add(0, self.update_url, ep)
        while dl.get_percent() < 100:
            self.percent = dl.get_percent()
            print ('Progress: %.2f%%' % self.percent, end='\r')
            time.sleep(1)
        self.percent = 100

    def dl_episode(self, ep):
        if self.verbose:
            print('Getting link of', ep.title)
        ep.get_url()
        if self.verbose:
            print('Link is', ep.episode_url + '/')
        dl = au.Download(ep.episode_url)
        if self.verbose:
            print('Now downloading', ep.title)
        threading.Thread(target=dl.dl_start).start()
        self.update_treestore(ep, dl)

    def manage_dl(self, dl_list):
        for dl in dl_list:
            for ep in self.ep:
                if ep.episode_id == dl[0]:
                    if self.verbose:
                        print('Downloading',  ep.title)
                    self.dl_episode(ep)
                    break


class GuiHandler(object):
    def __init__(self, Anime):
        self.Anime = Anime

    def on_find_next_episodes_clicked(self, widget):
        try:
            curr_id = int(interface.get_object('id_entry').get_text())
            threading.Thread(target=self.Anime.set_list, args=(curr_id,)).start()
        except ValueError:
            pass

    def on_find_episode_clicked(self, widget):
        try:
            curr_id = int(interface.get_object('id_entry').get_text())
            threading.Thread(target=self.Anime.set_list, args=(curr_id, 1,)).start()
        except ValueError:
            pass

    def on_getfilename_button_clicked(self, widget):
        store = interface.get_object('liststore1')
        sel_model, sel_rows = interface.get_object('treeview1').get_selection().get_selected_rows()
        selection = []
        for sel in sel_rows:
            threading.Thread(target=self.get_anime_url, args=(list(sel_model[sel])[0],)).start()

    def on_download_button_clicked(self, widget):
        store = interface.get_object('liststore1')
        sel_model, sel_rows = interface.get_object('treeview1').get_selection().get_selected_rows()
        selection = []
        for row in sel_rows:
            selection.append(list(sel_model[row]))
        threading.Thread(target=self.Anime.manage_dl, args=(selection,)).start()

    def on_mainWindow_destroy(self, widget):
        Gtk.main_quit()

if __name__ == "__main__":
    GObject.threads_init()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    interface = Gtk.Builder()
    interface.add_from_file('gui.glade')
    interface.connect_signals(GuiHandler(AnimeDl()))
    Gtk.main()
