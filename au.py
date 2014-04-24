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
        url = 'http://www.anime-ultime.net/ddl/authorized_download.php'
        u = urllib.request.urlopen(url, data=data)
        return json.loads(u.read().decode('utf-8'))

    def is_auth(self):
        return self.get_auth()['auth']

    def get_url(self):
        time_slept = 0
        result = self.get_auth()
        to_sleep = result['wait']
        result['auth'] = False
        while result['auth'] == False:
            print('Sleeping {} seconds ({}%)   '.format((to_sleep - time_slept) if (to_sleep - time_slept) > 0 else 0, '%.0f' % ((time_slept / to_sleep) * 100)), end='\r')
            if time_slept > 60:
                raise RuntimeError('Server won\'t give us the url, giving up')
            if time_slept < to_sleep:
                time.sleep(1)
                time_slept += 1
            else:
                result = self.get_auth()
                time.sleep(.5)
                time_slept += .5
        print('Sleeped {} seconds                '.format(time_slept))
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
