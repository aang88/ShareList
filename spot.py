from flask import Flask, redirect,url_for,render_template,request,session
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import os
import uuid
import subprocess
import sys
os.environ['SPOTIPY_CLIENT_ID'] = "c3032b421ce9457e80b9a05abcb623da"
os.environ['SPOTIPY_CLIENT_SECRET'] = "32a9c32611dc48bd85b69cf643f7c33e"
os.environ['SPOTIPY_REDIRECT_URI'] = "http://127.0.0.1:8080"
os.environ['FLASK_ENV']="development"
os.environ['FLASK_APP']="C:/Users/Aaron/spotPy"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')

@app.route("/")
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-public user-library-read',
                                                cache_handler=cache_handler, 
                                                show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/")

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template("signin.html",auth_url=auth_url)

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return render_template('index.html')

@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


@app.route("/help")
def help():
    return render_template('help.html')
 
@app.route("/forward/", methods=['POST'])
def createPlaylist():

    user1= request.form["user1"]
    playlistid1=request.form["playlist1"]
    user2=request.form["user2"]
    playlistid2=request.form["playlist2"]
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotifyObject = spotipy.Spotify(auth_manager=auth_manager)
    username =  spotifyObject.current_user()["id"]

    playlist_name = request.form["playlistName"]
    playlist_description = request.form["playlistDesc"]

    spotifyObject.user_playlist_create(user=username,name=playlist_name,public=True,description=playlist_description)

    client_id = 'c3032b421ce9457e80b9a05abcb623da'
    client_secret = '32a9c32611dc48bd85b69cf643f7c33e'

   # client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
   # sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def getTrackIDs(user, playlist_id):
        ids = []
        playlist2 = spotifyObject.user_playlist_tracks(user, playlist_id)
        tracks = playlist2['items']
        while playlist2['next']:    
            playlist2 = spotifyObject.next(playlist2)
            tracks.extend(playlist2['items'])
      
        for item in tracks:
            if item['track'] is None:
                continue
            track = item['track']
            ids.append(track['id'])
        return ids

    ids = getTrackIDs(user1, playlistid1)
    ids2 = getTrackIDs(user2,playlistid2)
    ids3 = list(set(ids).intersection(ids2))
    list_of_songs = []
    prePlaylist = spotifyObject.user_playlists(user=username)
    playlist = prePlaylist['items'][0]['id']
    spotifyObject.user_playlist_add_tracks(user=username,playlist_id=playlist,tracks=ids3)


 
    ids3 = list(set(ids).intersection(ids2))

    return render_template('index.html')


if __name__ == "__main__":
    app.debug = True
    app.run(threaded=True, port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))




    
    