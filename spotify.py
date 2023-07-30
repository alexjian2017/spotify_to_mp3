import spotipy
from pytube import YouTube
from youtube_search import YoutubeSearch
from spotipy.oauth2 import SpotifyClientCredentials
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from secret_key import *


client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def get_playlist_from_spotify(playlist_id: str):

    results = sp.playlist(playlist_id)

    # with open('data.json', 'w') as f:
    #     json.dump(results, f)
    folder = results['name']

    # 單線程
    # for i, track in enumerate(results['tracks']['items']):
    #     song_name = track['track']['name'].strip()
    #     singer = track['track']['artists'][0]['name'].strip()
    #     video_id = youtube_search(f'{song_name} {singer}')
    #     song_name = shorten_song_name(song_name)
    #     download_audio_from_yt(
    #         f'v={video_id}', folder, f'{i+1:02}.{song_name} {singer}.mp3')

    with ThreadPoolExecutor(max_workers=16) as pool:
        for i, track in enumerate(results['tracks']['items']):
            song_name = track['track']['name'].strip()
            singer = track['track']['artists'][0]['name'].strip()
            song_name = shorten_song_name(song_name)

            pool.submit(download_audio_from_yt,
                        f'v={youtube_search(f"{song_name} {singer}")}', folder, f'{singer} - {song_name}.mp3')


def get_album_from_spotify(album_id: str):
    results = sp.album(album_id)
    folder = results['name']
    singer = results['artists'][0]['name']
    with ThreadPoolExecutor(max_workers=16) as pool:
        for i, item in enumerate(results['tracks']['items']):
            song_name = item['name']
            song_name = shorten_song_name(song_name)
            pool.submit(download_audio_from_yt,
                        f'v={youtube_search(f"{song_name} {singer}")}', folder, f'{singer} - {song_name}.mp3')


def get_track_from_spotify(track_id: str):
    results = sp.track(track_id)
    song_name = results['name']
    singer = results['artists'][0]['name']

    video_id = youtube_search(f'{song_name} {singer}')
    song_name = shorten_song_name(song_name)
    download_audio_from_yt(
        f'v={video_id}', './單曲', f'{singer} - {song_name}.mp3')


def check_input_validation(prefix: str, url: str) -> bool:
    # check if input is exist in spotify
    id = url.split(prefix)[1][1:]
    check_url = f'https://open.spotify.com/{prefix}/{id}'
    response = requests.get(check_url)
    return response.status_code == requests.codes.ok


def word_to_filename_word(word: str) -> str:
    # there are some symbol are not available in filename such as \, /, :, *, ?, ", <, >, |
    # just skip them if they appear in filename
    return ''.join([ch for ch in word if ch not in '\/:*?"<>|'])


def shorten_song_name(song_name: str) -> str:
    # reduce the length of song name
    if len(song_name) >= 20:
        song_name = song_name.split('-')[0].split('(')[0].strip()
    if song_name[-1] == '.':
        song_name = song_name[:-1]
    return song_name


def youtube_search(keyword: str) -> str:
    result = YoutubeSearch(keyword, max_results=1).to_dict()
    return result[0].get('id')


def download_audio_from_yt(url: str, folder: str, filename: str) -> None:
    # using pytube to download audio from youtube
    try:
        yt = YouTube(url)
        filename = word_to_filename_word(filename)
        file = yt.streams.filter(only_audio=True).first()
        file.download(f'./{folder}', filename=filename)
    except Exception as e:
        print(e)
    else:
        print(f"'{yt.title}'已經下載完成")


if __name__ == '__main__':
    print("請輸入要下載spotify的網址: ")
    url = input().strip()
    if 'playlist' in url and check_input_validation('playlist', url):
        get_playlist_from_spotify(url)
    elif 'album' in url and check_input_validation('album', url):
        get_album_from_spotify(url)
    elif 'track' in url and check_input_validation('track', url):
        get_track_from_spotify(url)
    else:
        print("這不是一個有效的spotify路徑喔!")
