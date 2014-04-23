#!/usr/bin/python

import urllib.request, urllib.error, urllib.parse
import json
import time
import re
from bs4 import BeautifulSoup

class Episode(object):
    def __init__(self, episode_id, url = "", filename = ""):
        self.episode_id = episode_id
        self.episode_url = url
        self.filename = filename
        self.next_id = None
        self.size = 0
        self.title = ""
        self.treeiter = 0

    def get_auth(self):
        data = [('idfile', self.episode_id), ('type','orig')]
        data = urllib.parse.urlencode(data)
        data = data.encode('utf-8')
        u = urllib.request.urlopen('http://www.anime-ultime.net/ddl/authorized_download.php',
                                   data = data)
        return json.loads(u.read().decode('utf-8'))

    def is_auth(self):
        return (self.get_auth()['auth'])

    def get_url(self):
        condition = True
        time_slept = 0
        to_sleep = 0
        while True:
            if time_slept > 60:
                raise RuntimeError('Server won\'t give us the url, giving up')
            result = self.get_auth()
            if result['auth']:
                break
            if (to_sleep == 0):
                to_sleep = result['wait'] + 2
                for i in range(0, 10):
                    result = self.get_auth()
                    if result['auth']:
                        break
            if (time_slept >= result['wait']):
                to_sleep = .1
            if not result['auth']:
                print ('Sleeping', to_sleep, 'seconds ({} slept)'.format(time_slept))
                time.sleep(to_sleep)
                time_slept += to_sleep
            else:
                break
        self.episode_url = 'http://www.anime-ultime.net' + result['link']
        self.filename = result['link'].split('/')[-1]
        return self.episode_url

    def get_metadata(self):
        url = 'http://www.anime-ultime.net/info-0-01/' + str(self.episode_id)
        u = urllib.request.urlopen(url)
        soup = BeautifulSoup(u.read().decode('ISO-8859-1'))
        self.title = ' '.join(soup.find_all(text=re.compile('Info : '))[0].split(' ')[2:])
        self.size = float(soup.find_all(text=re.compile('Taille : '))[0].split(' ')[-2])
        self.next_id = None
        try:
            self.next_id = int(soup.find_all('a', text='Episode Suivant')[0]['href'].split('/')[1])
        except:
            try:
                self.next_id = int(soup.find_all('a', text='OAV Suivant')[0]['href'].split('/')[1])
            except:
                self.next_id = None
        return [self.episode_id, self.title]

class Download(object):
    def __init__(self, url, filename = None):
        self.url = url
        self.filename = filename
        if self.filename == None:
            self.filename = self.url.split('/')[-1]
        self.file_size = 0
        self.file_size_dl = 0

    def dl_start(self):
        u = urllib.request.urlopen(self.url)
        retry = 0
        for attempt in range(0, 10): # Try to download 10 times
            try:
                self.file_size = int(u.headers['Content-Length'])
            except TypeError:
                print('Retrying to download because getting an html page in 1s (', attempt, 'attempt)')
                time.sleep(1)
                u = urllib.request.urlopen(self.url)
            else:
                break
        else:
            raise RuntimeError('Download of', self.url, 'failed after', attempt + 1, 'attempts')
        f = open(self.filename, 'wb')
        block_sz = 1024 * 1024
        while True: # Here we start the download by reading the request
            buffer = u.read(block_sz)
            if not buffer: # if the read fails (aka the file is downloaded), break
                break
            self.file_size_dl += len(buffer) # We update the amount of downloaded data
            f.write(buffer)
        f.close()
        print('Finished: 100%    ')

    def get_percent(self):
        if self.file_size == 0:
            return 0
        return self.file_size_dl * 100 / self.file_size


if __name__ == "__main__":
    print ('You should try ./gui.py instead')
