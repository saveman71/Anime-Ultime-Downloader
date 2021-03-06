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
        self.verbose = False
        self.json = []
        self.load_config('config')
        self.speedlimit = None

    def set_list(self, episode_id, to_add=-1):
        store = interface.get_object('liststore1')
        spinner = interface.get_object('spinner1')
        spinner.start()
        spinner.show()
        i = 0
        while episode_id != None and (i < to_add or to_add == -1):
            self.ep.append(au.Episode(episode_id))
            self.ep[-1].get_metadata()
            GLib.timeout_add(0, self.update_treestore_from_ep)
            episode_id = self.ep[-1].next_id
            i += 1
        spinner.hide()

    def update_url(self, ep):
        store = interface.get_object('liststore1')
        store[ep.treeiter][4] = ep.episode_url
        return False

    def update_percent(self, ep):
        store = interface.get_object('liststore1')
        store[ep.treeiter][3] = self.percent
        if self.percent == 100:
            return (False)
        return True

    def update_ep_status(self):
        store = interface.get_object('liststore1')
        for ep in self.ep:
            store[ep.treeiter][5] = ep.status
        return True

    def update_treestore(self, ep):
        GLib.timeout_add_seconds(1, self.update_percent, ep)
        GLib.timeout_add(0, self.update_url, ep)
        while ep.dl.get_percent() < 100:
            self.percent = ep.dl.get_percent()
            print('Progress: %.2f%%' % self.percent, end='\r')
            time.sleep(1)
        self.percent = 100

    def dl_episode(self, ep):
        if self.verbose:
            print('Getting link of', ep.title)
        ep.get_url()
        if self.verbose:
            print('Link is', ep.episode_url + '/')
        if self.verbose:
            print('Now downloading', ep.title)
        threading.Thread(target=ep.download, args=(self.speedlimit,)).start()
        self.update_treestore(ep)

    def manage_dl(self, dl_list):
        for dl in dl_list:
            for ep in self.ep:
                if ep.episode_id == dl[0] and ep.status == 'idle':
                    if self.verbose:
                        print('Downloading', ep.title)
                    self.dl_episode(ep)
                    break

    def manage_delete(self, delete_list):
        for delete in delete_list:
            for i in range(0, len(self.ep)):
                if self.ep[i].episode_id == delete[0]:
                    if self.verbose:
                        print('Deleting', self.ep[i].title)
                    del self.ep[i]
                    break
        GLib.timeout_add(0, self.update_treestore_from_ep)

    def update_treestore_from_ep(self):
        store = interface.get_object('liststore1')
        store.clear()
        for i in range(0, len(self.ep)):
            self.ep[i].treeiter = store.append([self.ep[i].episode_id,
                                                self.ep[i].title,
                                                int(self.ep[i].size),
                                                0, self.ep[i].filename,
                                                self.ep[i].status])
        return False

    def load_list(self):
        store = interface.get_object('liststore1')
        for item in self.json:
            ep = au.Episode(item['id'])
            ep.title = item['title']
            ep.size = item['size']
            ep.filename = item['filename']
            self.ep.append(ep)

    def save_config(self, filename):
        store = interface.get_object('liststore1');
        di = [dict(zip(("id", "title", "size", "progress", "filename"), col)) for col in [row for row in store]]
        json.dump(di, open(filename, 'w'), indent=4, separators=(',', ': '))

    def load_config(self, filename):
        try:
            self.json = json.load(open(filename))
        except FileNotFoundError:
            pass
        self.load_list();

class GuiHandler(object):
    def __init__(self, Anime):
        self.Anime = Anime
        self.Anime.update_treestore_from_ep()
        GLib.timeout_add(500, self.Anime.update_ep_status)

    def get_id_from_text(self, text=''):
        try:
            return int(text)
        except ValueError:
            url = urllib.parse.urlparse(text)
            if url.scheme == 'http' and url.path[0:10] == '/info-0-1/':
                try:
                    return int(url.path[10:-1].split('-')[0])
                except ValueError:
                    return -1
        return -1

    def on_find_next_episodes_clicked(self, widget):
        curr_id = self.get_id_from_text(interface.get_object('id_entry').get_text())
        if (curr_id > 0):
            threading.Thread(target=self.Anime.set_list, args=(curr_id,)).start()

    def on_find_episode_clicked(self, widget):
        curr_id = self.get_id_from_text(interface.get_object('id_entry').get_text())
        if (curr_id > 0):
            threading.Thread(target=self.Anime.set_list, args=(curr_id, 1,)).start()

    def on_download_button_clicked(self, widget):
        store = interface.get_object('liststore1')
        sel_model, sel_rows = interface.get_object('treeview1').get_selection().get_selected_rows()
        selection = []
        for row in sel_rows:
            selection.append(list(sel_model[row]))
        if len(selection):
            threading.Thread(target=self.Anime.manage_dl, args=(selection,)).start()

    def on_delete_activate(self, widget):
        store = interface.get_object('liststore1')
        sel_model, sel_rows = interface.get_object('treeview1').get_selection().get_selected_rows()
        selection = []
        for row in sel_rows:
            selection.append(list(sel_model[row]))
        if len(selection):
            threading.Thread(target=self.Anime.manage_delete, args=(selection,)).start()

    def on_speed_button_value_changed(self, widget):
        value = int(widget.get_value()) * 1000
        if value == 0:
            self.Anime.speedlimit = None
        else:
            self.Anime.speedlimit = value
        for ep in self.Anime.ep:
            if ep.dl:
                ep.dl.speedlimit = self.Anime.speedlimit

    def on_mainWindow_destroy(self, widget):
        self.Anime.save_config('config');
        Gtk.main_quit()

if __name__ == "__main__":
    GObject.threads_init()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    interface = Gtk.Builder()
    interface.add_from_file('gui.glade')
    interface.connect_signals(GuiHandler(AnimeDl()))
    Gtk.main()
