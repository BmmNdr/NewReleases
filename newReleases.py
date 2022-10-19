# send a mail with songs and albums released by followed artists on spotify in a range of days
from datetime import date
from email.message import EmailMessage

import smtplib
import spotipy
import ssl
from spotipy.oauth2 import SpotifyOAuth

import psw  # file containing passwords, emails and IDs

client_ID = psw.client_ID  # your spotify API client ID
client_SECRET = psw.client_SECRET  # your spotify API client secret
redirect_url = psw.redirect_url  # your spotify API client redirect url

email = psw.email  # your email
password = psw.password  # your google app password
contacts = psw.contacts  # emails you want to send a mail

deltaDays = 6  # range of days

# todayDate indexing
day = 2
month = 1
year = 0

# Basic Url and Uri
url_album = 'https://open.spotify.com/album/'
uri_album = 'spotify:album:'


# todayDate = [year, month, day]
def subDays(todayDate, daysToSub):
    if daysToSub <= 0:
        return todayDate

    if todayDate[day] > daysToSub:
        todayDate[day] = todayDate[day] - daysToSub
        return todayDate

    daysToSub = daysToSub - todayDate[day]
    todayDate[month] = todayDate[month] - 1

    if todayDate[month] == 0:
        # change of year
        return subDays([todayDate[year] - 1, 12, 31], daysToSub)
    if todayDate[month] == 1 or todayDate[month] == 3 or todayDate[month] == 5 or todayDate[month] == 7 or \
            todayDate[month] == 8 or todayDate[month] == 10 or todayDate[month] == 11:
        # 31
        return subDays([todayDate[year], todayDate[month], 31], daysToSub)
    elif todayDate[month] == 4 or todayDate[month] == 6 or todayDate[month] == 9 or todayDate[month] == 12:
        # 30
        return subDays([todayDate[year], todayDate[month], 30], daysToSub)
    elif (todayDate[month] % 4 == 0 and todayDate[month] % 100 == 0) or todayDate[month] % 400 == 0:
        # 29
        return subDays([todayDate[year], todayDate[month], 29], daysToSub)
    else:
        # 28
        return subDays([todayDate[year], todayDate[month], 28], daysToSub)


def get_WithAlbumType(today, sp, album_type, uri, name):
    albums = sp.artist_albums(uri, album_type=album_type, limit=1)
    for j, album in enumerate(albums['items']):

        albumReleaseDate = album['release_date'].split('-')

        if int(albumReleaseDate[year]) < today[year]:
            return

        if int(albumReleaseDate[month]) < today[month]:
            return

        if int(albumReleaseDate[day]) < today[day]:
            return

        album_name = album['name']
        album_uri = album['uri']
        album_uri = album_uri.replace(uri_album, '')
        album_url = url_album + album_uri

        return [album_name, name, album_url]


def get_artistsReleases(today, sp):
    releases = []
    lastArtistId = None

    while True:
        # Get user followed artists
        results = sp.current_user_followed_artists(limit=50, after=lastArtistId)

        if len(results['artists']['items']) == 0:
            return releases

        # For each artist
        for i, items in enumerate(results['artists']['items']):
            uri = items['uri']
            lastArtistId = items['id']

            # New Albums
            newAlbums = get_WithAlbumType(today, sp, 'album', uri, items['name'])

            if newAlbums is None:
                pass
            else:
                releases.append(newAlbums)

            # New Singles
            newSingle = get_WithAlbumType(today, sp, 'single', uri, items['name'])

            if newSingle is None:
                pass
            else:
                releases.append(newSingle)


def get_releases():
    # Date
    today = date.today()
    today = subDays([today.year, today.month, today.day], deltaDays)

    # Authentication
    scope = "user-follow-read"
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(client_id=client_ID, client_secret=client_SECRET, redirect_uri=redirect_url,
                                  scope=scope))

    releases = get_artistsReleases(today, sp)

    f = ''
    links = []
    for item in releases:
        f = f + item[0] + ' - ' + item[1] + '\n' + item[2] + '\n\n'
        links.append(item[2])

    return f


def sendMail(msgToSend):
    port = 465  # For SSL

    context = ssl.create_default_context()

    # connection is closed automatically
    with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as server:
        server.login(email, password)  # login
        server.send_message(msgToSend)  # send the mail


if __name__ == '__main__':
    msg = EmailMessage()
    msg['Subject'] = 'New Releases'
    msg['From'] = email
    msg['To'] = contacts

    s = get_releases()
    msg.set_content(s)

    if len(s) != 0:
        sendMail(msg)
