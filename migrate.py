#!/usr/bin/python3
#coding: utf-8

import sys
import json
import time
from traceback import format_exc
from urllib.parse import quote, urlencode

import zhconv
import requests
from pyquery import PyQuery as pq


class Spotify():

    search_track_api = 'https://api.spotify.com/v1/search?q={}&type=track'
    create_playlist_api = 'https://api.spotify.com/v1/users/{}/playlists'
    add_track_to_list_api = 'https://api.spotify.com/v1/users/{}/playlists/{}/tracks?uris={}'

    def __init__(self, access_token, user_id):
        self.access_token = access_token
        self.user_id = user_id
        self.s = requests.session()
        self.s.headers['Authorization'] = 'Bearer '+self.access_token

    def search(self, song, singer, market=None):
        if market:
            url = Spotify.search_track_api.format(quote(song))+'&market='+quote(market)
        else:
            url = Spotify.search_track_api.format(quote(song))
        r = self.s.get(url)
        info = json.loads(r.text)
        if not info.get('tracks'):
            return {'status': True, 'info': info}
        tracks = info['tracks']
        if info.get('error'):
            return {'status': True, 'info': info['error']}
        if len(tracks) == 0:
            return {'status': False, 'info': 'no results'}
        song_uri = ''
        for one in tracks['items']:
            r_singer = one['artists'][0]['name'].lower()
            r_song = one['name'].lower()
            if r_song == song.lower() and r_singer == singer.lower():
                song_uri = one['uri']
                break
        if song_uri == '':
            return {'status': False, 'info': 'no results'}
        return {'status': True, 'info': song_uri}

    def search_songs(self, songs, market=None):
        success_l = []
        fail_l = []
        again_l = []
        for one in songs:
            song = one['song']
            singer = one['singer']
            search = self.search(song, singer, market)
            if search['status'] == 200:
                print(song + ' success')
                one['uri'] = search['info']
                success_l.append(one)
            elif isinstance(search['info'], dict) \
                    and search['info'].get('error') \
                    and search['info']['error']['status'] == 429:
                again_l.append(one)
                print('reach rate limit, sleep 10s ...')
                time.sleep(10)
            else:
                print(song + ' fail: ' + str(search['info']))
                one['error'] = search['info']
                fail_l.append(one)
            time.sleep(0.5)
        if len(again_l) > 0:
            success_ll, fail_ll = self.search_songs(again_l)
            success_l += success_ll
            fail_l += fail_ll
        return success_l, fail_l

    def create_playlist(self, listname):
        url = Spotify.create_playlist_api.format(quote(self.user_id))
        headers = {'Content-Type': 'application/json'}
        data_json = '{"name": "' + listname + '"}'
        r = self.s.post(url, headers=headers, data=data_json)
        info = json.loads(r.text)
        if r.status_code == 200 or r.status_code == 201:
            list_id = info['id']
            return {'status': True, 'info': list_id}
        else:
            return {'status': False, 'info': info['error']}

    def add_track_to_list(self, list_id, song_uris):
        uris = ','.join(map(quote, song_uris))
        url = Spotify.add_track_to_list_api.format(quote(self.user_id),
                                                   quote(str(list_id)),
                                                   uris)
        headers = {'Accept': 'application/json'}
        retry = 0
        while retry < 10:
            r = self.s.post(url, headers=headers)
            if retry >= 2:
                print('no response when adding tracks, retry...')
            if r.text:
                break
            retry += 1
        info = json.loads(r.text)
        if info.get('error'):
            return {'status': False, 'info': info['error']}
        else:
            print('add %s tracks to %s' % (str(len(song_uris)), list_id))
            return {'status': True, 'info': info['snapshot_id']}


def extract_list_from_html(origin_html_name):
    with open(origin_html_name, 'r', encoding='utf8') as f:
        doc = pq(f.read())
    trs = doc('tbody')('tr')
    songs = []
    for one in trs.items():
        name = one('td').eq(1)('b').attr['title'].replace('\xa0', ' ')
        singer = one('td').eq(3)('span').attr['title']
        name = zhconv.convert(name, 'zh-hk')
        singer = zhconv.convert(singer, 'zh-hk')
        songs.append({'song': name, 'singer': singer})
    json_file_name = origin_html_name.split('.')[0] + '.json'
    with open(json_file_name, 'w', encoding='utf8') as f:
        json.dump(songs, f)
    return songs


def migrate(log, user_id, access_token, songs, play_list_name, market=None, add=True):

    spotify = Spotify(access_token, user_id)

    # search songs
    log.write('SEARCH SONGS:\n')
    success_l, fail_l = spotify.search_songs(songs)
    for i, one in enumerate(success_l):
        log.write(str(i+1) + '. ' + one['song'] + ' - ' + one['singer'] + ' success.\n')
    log.write('\n\n')
    for i, one in enumerate(fail_l):
        log.write(str(i+1) + '. ' + one['song'] + ' - ' + one['singer'] + ' fail.\n')
    log.write('\n\n')

    if not add:
        exit_info = 'total: {}\tsuccess: {}\tfail: {}\n'.format(
            len(songs), len(success_l), len(fail_l))
        print(exit_info)
        log.write(exit_info)
        return

    # create play list
    log.write('CREATE PLAY LIST:\n')
    create = spotify.create_playlist(play_list_name)
    if create['status']:
        list_id = create['info']
    else:
        print(create['info'])
        log.write(str(create['info']))
        return
    log.write('\n\n')

    # add to playlist
    log.write('ADD TO PLAYLIST:\n')
    success_num = 0
    for i, one in enumerate(success_l):
        add = spotify.add_track_to_list(list_id, [one['uri']])
        if not add['status']:
            log.write(one['song'] + ' add fail: ' + add['info'] + '\n')
        else:
            log.write(one['song'] + ' add success\n')
            success_num += 1
    log.write('\n\n')
    fail_num = len(songs) - success_num
    exit_info = 'total: {}\tsuccess:{}\tfail:{}\n'.format(len(songs), success_num, fail_num)
    print(exit_info)
    log.write(exit_info)
    log.close()


origin_html_name = sys.argv[1]
user_id = ''  # user id
access_token = ''  # access token
songs = extract_list_from_html(origin_html_name)
playlist_name = origin_html_name.split('.')[0]

log = open('log.txt', 'w', encoding='utf8')
try:
    migrate(log, user_id, access_token, songs, playlist_name, add=False)
except Exception as e:
    print(str(e))
    print(format_exc())
finally:
    log.close()
