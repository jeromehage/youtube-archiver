from yt_dlp import YoutubeDL
import pandas as pd
import os, datetime

# update playlist data
update = True

# metadata
metadata_cols = ['id', 'title', 'uploader', 'uploader_id', 'uploader_url', 'channel_id', 'channel_url', 'duration', 'view_count', 'age_limit', 'webpage_url', 'categories', 'tags', 'like_count', 'channel', 'channel_follower_count', 'upload_date', 'availability', 'original_url', 'playlist_count', 'playlist_id', 'playlist_index', 'duration_string', 'filesize_approx', 'width', 'height', 'resolution', 'fps']
ydl_opts1 = {
    'ignoreerrors': True,
    'no_warnings': True,
    'quiet': True
}

# videos
ydl_opts2 = {
    'postprocessors': [{
        'key': 'FFmpegVideoRemuxer',
        'preferedformat': 'mp4',
    }],
    #'keepvideo': True,
    'embedsubtitles': True,
    'embedthumbnail': True,
    'addmetadata': True,
    'addchapters': True,
    'playliststart': 0,
    'ignoreerrors': True,
    #'no_warnings': True,
}

with open('lists.txt', 'r') as f:
    lists = f.read().split()

# go through list of playlists
for url in lists:
    # read playlist ID from url
    if 'list=' in url:
        pl = url[url.index('list=') + 5:].split('&')[0]
    else:
        pl = url
    if not os.path.isdir(pl):
        os.mkdir(pl)
    # date formatting
    pl_name = 'playlist'
    pl_ext = '.csv'
    pl_date_f = '_%Y-%m-%d_%H-%M-%S'
    pl_info = [f for f in os.listdir(pl) if pl_name in f and f.endswith(pl_ext)]
    # download playlist info
    if update or len(pl_info) == 0:
        print('Fetching playlist info:', pl)
        with YoutubeDL(ydl_opts1) as ydl:
            data = ydl.extract_info(pl, download = False)
            if not data:
                print('Invalid playlist', pl, 'skipping...')
                continue
            pl_path = os.path.join(pl, 'playlist{}.csv'.format(datetime.datetime.now().strftime(pl_date_f)))
            pd.DataFrame([e for e in data['entries'] if e])[metadata_cols].to_csv(pl_path)
    # find latest saved playlist
    pl_info = [f for f in os.listdir(pl) if pl_name in f and f.endswith(pl_ext)]
    pl_date = [f[f.index(pl_name) + len(pl_name): - len(pl_ext)] for f in pl_info]
    pl_date = [-1 if d == '' else datetime.datetime.strptime(d, pl_date_f).timestamp() for d in pl_date]
    pl_latest = pl_info[pl_date.index(max(pl_date))]
    print('Using', pl_latest)
    pl_path = os.path.join(pl, pl_latest)
    meta = pd.read_csv(pl_path, index_col = 0)
    # download videos
    for vid, v in meta.iterrows():
        ch = v['channel']
        for c in '\"*/<>?\\|:': # NTFS
            ch = ch.replace(c, '')
            ch = ch.rstrip()
        ch_path = os.path.join(pl, ch)
        if not os.path.isdir(ch_path):
            os.mkdir(ch_path)
        files = os.listdir(ch_path)
        # check for existing files
        keywords = ['mp4', v['id']] # must be included in file name
        noend = ['.mp4.part']
        if not any([all([k in fn for k in keywords]) and all([fn[-len(ne):] != ne for ne in noend]) for fn in files]):
            ydl_opts = dict(ydl_opts2)
            ydl_opts['paths'] = {'home': ch_path}
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download(v['id'])
    print('done', pl)
