import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from spotipy import Spotify, SpotifyException, SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from spotipy_random import get_random
import requests
import base64
from PIL import ImageTk, Image, ImageDraw
from io import BytesIO
import cachetools
import random
import threading


def revoke_access_token(access_token, client_id, client_secret):
    if access_token:
        revocation_url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {get_base64_encoded_credentials(client_id, client_secret)}"
        }
        data = {"token": access_token} if access_token else {}
        response = requests.post(revocation_url, data=data, headers=headers)
        print(response.status_code)
        return True
    else:
        return False


def get_base64_encoded_credentials(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}"
    return base64.b64encode(credentials.encode()).decode()


class SpotifyToolsApp:
    def __init__(self, window):

        self.colour_background = "#121212"
        self.colour_foreground_green = "#1ED760"

        self.window = window
        self.window.config(background=self.colour_background)
        self.window.title("Spotify Login")

        self.CLIENT_ID = "58817dcd8cc54baa9dd033ea9ef0f86f"
        self.CLIENT_SECRET = "8fe689bda9e64b3d8b4e111301cf6a44"
        self.REDIRECT_URI = "http://localhost:8888/callback"

        spotify_client = Spotify(auth_manager=SpotifyClientCredentials(
                                 client_id=self.CLIENT_ID,
                                 client_secret=self.CLIENT_SECRET))

        self.playlists = {}
        self.playlist_uris = {}
        self.text_num_song = ""
        self.song_cache = cachetools.LRUCache(maxsize=10000)

        self.window.geometry("700x500")
        self.frame_login = tk.Frame(
            self.window, width=700, height=500, background=self.colour_background)
        self.frame_home = tk.Frame(
            self.window, width=700, height=500, background=self.colour_background)
        self.frame_view_playlist = tk.Frame(
            self.window, width=700, height=500, background=self.colour_background)
        self.frame_view_all_playlists = tk.Frame(
            self.window, width=700, height=500, background=self.colour_background)
        self.frame_view_playlist_songs = tk.Frame(
            self.window, width=700, height=500,  background=self.colour_background)
        self.frame_user_profile = tk.Frame(
            self.frame_home, width=700, height=150, background=self.colour_background)
        self.frame_home_buttons = tk.Frame(
            self.window, width=300, height=100, background=self.colour_background)
        self.frame_music_player = tk.Frame(
            self.window, width=500, height=500, background=self.colour_background)
        self.frame_music_player_buttons = tk.Frame(
            self.frame_music_player, width=500, height=50, background=self.colour_background)

        self.progress_dialog = None
        self.progress_bar = None

        self.label_number_of_songs = tk.Label(
            self.frame_view_playlist, background=self.colour_background, foreground="white")
        self.label_playlist_image = tk.Label(
            self.frame_view_playlist, background=self.colour_background, foreground="white")
        self.label_playlist_name = tk.Label(
            self.frame_view_playlist, background=self.colour_background, foreground="white")
        self.label_welcome_title = tk.Label(
            self.frame_login, background=self.colour_background)
        self.label_view_playlist_title = tk.Label(
            self.frame_view_all_playlists, background=self.colour_background, foreground=self.colour_foreground_green)
        self.label_user_profile_image = tk.Label(
            self.frame_home, background=self.colour_background)
        self.label_user_profile_name = tk.Label(
            self.frame_home, background=self.colour_background, foreground="white")
        self.label_image_logo = tk.Label(
            self.frame_login, background=self.colour_background)

        self.player_label_song_name = tk.Label(
            self.frame_music_player, background=self.colour_background, foreground="white", text="")
        self.player_label_album_name = tk.Label(
            self.frame_music_player, background=self.colour_background, foreground="white", text="")
        self.player_label_artist_name = tk.Label(
            self.frame_music_player, background=self.colour_background, foreground="white", text="")
        self.player_label_song_image = tk.Label(
            self.frame_music_player, background=self.colour_background, text="")

        self.listbox_playlists = tk.Listbox(
            self.frame_view_all_playlists, background="#282828", foreground="white", highlightthickness=0, font=("Helvetica", 13))
        self.scrollbar_playlists = tk.Scrollbar(
            self.window, command=self.listbox_playlists.yview)
        self.listbox_playlists.config(
            yscrollcommand=self.scrollbar_playlists.set)

        self.listbox_view_songs = tk.Listbox(
            self.frame_view_playlist_songs, background="#282828", foreground="white")
        self.scrollbar_songs = tk.Scrollbar(
            self.window, command=self.listbox_view_songs.yview)
        self.listbox_view_songs.config(yscrollcommand=self.scrollbar_songs.set)

        self.button_login = tk.Button(self.frame_login, text="Login to Spotify", background=self.colour_foreground_green,
                                      foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))
        self.button_logout = tk.Button(
            self.frame_home, relief="flat", background=self.colour_background)
        self.button_view_playlists = tk.Button(self.frame_home_buttons, text="View Playlists", background=self.colour_foreground_green,
                                               foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))
        # generate song button
        # self.button_view_playlists = tk.Button(self.frame_home_buttons, text="View Playlists", background=self.colour_foreground_green,foreground=self.colour_background,relief="flat",font=("Helvetica","10","bold"))
        self.button_music_player = tk.Button(self.frame_home_buttons, text="Spotify Mini-Player", background=self.colour_foreground_green,
                                             foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))
        self.button_back_home = tk.Button(self.frame_view_all_playlists, text="Home", background=self.colour_foreground_green,
                                          foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))
        self.button_back_view_playlists = tk.Button(self.frame_view_playlist, text="Back", background=self.colour_foreground_green,
                                                    foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))
        self.button_back_view_playlist = tk.Button(self.frame_view_playlist_songs, text="Back to Playlist",
                                                   background=self.colour_foreground_green, foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))
        self.button_shuffle_playlist = tk.Button(self.frame_view_playlist, text="Shuffle Playlist", background=self.colour_foreground_green,
                                                 foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))
        self.button_view_songs = tk.Button(self.frame_view_playlist, text="View Songs", background=self.colour_foreground_green,
                                           foreground=self.colour_background, relief="flat", font=("Helvetica", "10", "bold"))

        self.button_play_pause = tk.Button(self.frame_music_player_buttons, text="▶️", background=self.colour_foreground_green,
                                           foreground=self.colour_background, relief="flat", font=("Helvetica", "15", "bold"))
        self.button_next = tk.Button(self.frame_music_player_buttons, text="⏭️", background=self.colour_foreground_green,
                                     foreground=self.colour_background, relief="flat", font=("Helvetica", "15", "bold"))
        self.button_prev = tk.Button(self.frame_music_player_buttons, text="⏮️", background=self.colour_foreground_green,
                                     foreground=self.colour_background, relief="flat", font=("Helvetica", "15", "bold"))

        self.login_screen()

    # initialisation method ends here ^^^^^

    def login_screen(self):
        self.frame_login.pack_propagate(False)
        self.frame_login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        original_image = Image.open("spotify_logo.png")
        resized_image = original_image.resize((333, 100))
        spotify_logo = ImageTk.PhotoImage(resized_image)

        self.label_image_logo.config(image=spotify_logo)
        self.label_image_logo.image = spotify_logo
        self.label_image_logo.grid(row=0, column=0, pady=(40, 10), padx=50)

        self.label_welcome_title.config(
            text="Welcome to Aryan's SpotifyTools!",
            font=("Helvetica", 20, "bold"),
            foreground=self.colour_foreground_green)
        self.label_welcome_title.grid(row=1, column=0, pady=(10, 20), padx=30)

        self.button_login.config(command=self.login_to_spotify)
        self.button_login.grid(row=2, column=0, pady=(10, 40), padx=30)

    def login_to_spotify(self):
        self.sp_oauth = SpotifyOAuth(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri=self.REDIRECT_URI,
            scope="playlist-modify-private playlist-modify-public user-read-recently-played streaming app-remote-control user-read-playback-state user-modify-playback-state user-top-read",
            open_browser="true",
            show_dialog="true",
        )
        self.access_token = self.sp_oauth.get_cached_token()
        self.sp = Spotify(auth=self.access_token["access_token"])
        self.user = self.sp.current_user()

        if self.access_token and "access_token" in self.access_token:
            print(f"Logged in as: {self.user['display_name']}")
            self.frame_login.place_forget()
            self.home_screen()
        else:
            messagebox.showerror("Error", "Connection Unsuccessful")

    def logout(self):
        if self.access_token:
            if revoke_access_token(self.access_token["access_token"], self.CLIENT_ID, self.CLIENT_SECRET):
                print("Access token revoked successfully.")
                self.frame_home.pack_forget()
                self.frame_login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                messagebox.showinfo("Success", "Successfully logged out!")
            else:
                print("Failed to revoke access token.")

            self.user = None
            self.access_token = None
            self.sp = None

    def home_screen(self):
        self.window.title("Home")
        self.frame_home.pack_propagate(False)
        self.frame_home.pack(anchor='n')

        logout_icon = Image.open("logout_icon.png")
        resized_logout_icon = logout_icon.resize((35, 35))
        self.logout_icon = ImageTk.PhotoImage(resized_logout_icon)
        self.button_logout.config(image=self.logout_icon, command=self.logout)
        self.button_logout.grid(row=1, column=3, pady=(50), padx=(10, 30))

        self.frame_user_profile.pack_propagate(False)
        self.frame_user_profile.pack(anchor='n')
        self.frame_home_buttons.pack(anchor='n')
        self.button_view_playlists.pack(anchor='n', padx=15, pady=15)
        self.button_music_player.config(command=self.music_player)
        self.button_music_player.pack(anchor='n', padx=15, pady=15)

        name, imageurl = self.fetch_user_details()
        self.display_user_profile(name, imageurl)

    def music_player(self):
        self.window.minsize(200, 150)
        self.frame_music_player.pack_propagate(False)
        self.frame_music_player.pack(anchor='n')
        self.frame_home.pack_forget()
        self.frame_home_buttons.pack_forget()

        if self.sp.current_playback() is not None:
            self.update_playback_info()

            self.player_label_song_image.pack(anchor='n', padx=20, pady=20)
            self.player_label_song_name.pack(anchor='n')
            self.player_label_album_name.pack(anchor='n')
            self.player_label_artist_name.pack(anchor='n')

            self.frame_music_player_buttons.pack()
            self.frame_music_player_buttons.grid_columnconfigure(
                index=3, weight=1)
            self.frame_music_player_buttons.grid_rowconfigure(
                index=1, weight=1)

            play_icon = Image.open("icon_play.png")
            r_play_icon = play_icon.resize((35, 35))
            self.play_icon = ImageTk.PhotoImage(r_play_icon)

            pause_icon = Image.open("icon_pause.png")
            r_pause_icon = pause_icon.resize((35, 35))
            self.pause_icon = ImageTk.PhotoImage(r_pause_icon)

            next_icon = Image.open("icon_next.png")
            r_next_icon = next_icon.resize((35, 35))
            self.next_icon = ImageTk.PhotoImage(r_next_icon)

            prev_icon = Image.open("icon_previous.png")
            r_prev_icon = prev_icon.resize((35, 35))
            self.prev_icon = ImageTk.PhotoImage(r_prev_icon)

            self.button_play_pause.configure(
                command=self.play_pause_track, image=self.pause_icon)
            self.button_prev.configure(
                command=self.previous_track, image=self.prev_icon)
            self.button_next.configure(
                command=self.next_track, image=self.next_icon)

            self.button_prev.grid(column=0, row=0, padx=15, pady=15)
            self.button_play_pause.grid(column=1, row=0, padx=15, pady=15)
            self.button_next.grid(column=2, row=0, padx=15, pady=15)

        else:
            print("No current playback information available.")
            self.player_label_song_name.config(text="No PlayBack Information.")
            self.player_label_album_name.config(text="")
            self.player_label_artist_name.config(text="")

            self.player_label_song_image.pack(anchor='n', padx=20, pady=20)
            self.player_label_song_name.pack(anchor='n')
            self.player_label_album_name.pack(anchor='n')
            self.player_label_artist_name.pack(anchor='n')

    def update_playback_info(self):

        if self.sp.current_playback():
            response = requests.get(self.sp.current_playback()[
                                    'item']['album']['images'][0]['url'])
            original_image = Image.open(BytesIO(response.content))
            resized_image = original_image.resize((300, 300))
            self.album_image = ImageTk.PhotoImage(resized_image)

            self.player_label_song_image.config(image=self.album_image)
            self.player_label_song_name.config(text=self.sp.current_playback()[
                                               'item']['name'], font=("Helvetica", 20, "bold"))
            self.player_label_album_name.config(text=self.sp.current_playback()[
                                                'item']['album']['name'], font=("Helvetica", 10, "bold"))
            self.player_label_artist_name.config(text=self.sp.current_playback(
            )['item']['artists'][0]['name'], font=("Helvetica", 13, "bold"))

            self.frame_music_player.update()
            self.frame_music_player.update_idletasks()
            self.frame_music_player_buttons.update()
            self.frame_music_player_buttons.update_idletasks()

            self.frame_music_player.after(1000, self.update_playback_info)
        else:
            self.frame_music_player.after(1000, self.update_playback_info)

            # *Album Name: self.sp.current_playback()['item']['album']['name'])
            # *Album Image: self.sp.current_playback()['item']['album']['images'][0]['url']

            # !Artist Name: self.sp.current_playback()['item']['artists'][0]['name']
            # !Artist Link: self.sp.current_playback()['item']['artists'][0]['external_urls']['spotify']

            # ?Track Name: self.sp.current_playback()['item']['name']
            # ?Track Link: self.sp.current_playback()["item"]['external_urls']['spotify']

    def play_pause_track(self):

        self.device_id = self.sp.current_playback()['device']['id']

        if self.sp.current_playback()['is_playing']:
            self.sp.pause_playback(self.device_id)
            self.button_play_pause.configure(image=self.play_icon)
        else:
            self.sp.start_playback(self.device_id)
            self.button_play_pause.configure(image=self.pause_icon)

    def previous_track(self):
        self.device_id = self.sp.current_playback()['device']['id']
        self.sp.previous_track(self.device_id)
        self.frame_music_player.update()
        self.frame_music_player.update_idletasks()
        self.frame_music_player.pack_forget()
        self.music_player()

    def next_track(self):
        self.device_id = self.sp.current_playback()['device']['id']
        self.sp.next_track(self.device_id)
        self.frame_music_player.update()
        self.frame_music_player.update_idletasks()
        self.frame_music_player.pack_forget()
        self.music_player()

    def display_user_profile(self, name, image_url):
        response = requests.get(image_url)
        profile_image = Image.open(BytesIO(response.content))

        width, height = profile_image.size
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, height), fill=255)

        circular_image = Image.new("RGBA", (width, height))
        circular_image.paste(profile_image, mask=mask)
        self.user_image = ImageTk.PhotoImage(circular_image)

        self.label_user_profile_image.config(image=self.user_image)
        self.label_user_profile_name.config(text=name, font=("Helvetica", 25))

        self.button_view_playlists.config(command=self.view_playlists)

        self.label_user_profile_name.grid(
            row=1, column=1, pady=(30), padx=(10, 10))
        self.label_user_profile_image.grid(
            row=1, column=0, pady=(30), padx=(30, 10))

    def fetch_all_songs(self, playlist_uri, sp, song_cache):
        if playlist_uri in song_cache:
            return len(song_cache[playlist_uri])

        all_tracks = []

        playlist_tracks = sp.playlist_tracks(playlist_uri)
        self.display_progress_dialog("Loading Songs...")
        self.progress_dialog.update_idletasks()

        while playlist_tracks:
            all_tracks.extend(playlist_tracks["items"])

            next_page = playlist_tracks["next"]
            if not next_page:
                self.close_progress_dialog()
                break

            playlist_tracks = sp.next(playlist_tracks)
            number_of_loaded_tracks = len(all_tracks)
            self.label_songs_loaded.config(
                text=f"Loading Songs... {number_of_loaded_tracks}")
            self.progress_dialog.update_idletasks()

        song_cache[playlist_uri] = all_tracks

        return all_tracks

    def fetch_user_details(self):
        display_name = self.user["display_name"]
        profile_image_url = (
            self.user["images"][0]["url"] if self.user["images"] else None
        )

        return display_name, profile_image_url

    def fetch_playlist_uri(self):
        selected_index = self.listbox_playlists.curselection()

        if selected_index:
            index = selected_index[0]
            selected_item = self.listbox_playlists.get(index)
            selected_playlist_uri = self.playlist_uris.get(selected_item, "")
            return selected_playlist_uri

    def view_playlists(self):
        self.window.title("View Playlists")
        self.frame_home.pack_forget()
        self.frame_home_buttons.pack_forget()
        self.frame_view_all_playlists.pack(expand=True)
        self.frame_view_all_playlists.pack_propagate(False)
        self.label_view_playlist_title.config(
            text="Your Playlists", font=("Helvetica", "20", "bold"))
        self.label_view_playlist_title.pack()
        self.listbox_playlists.pack(
            side="top", fill="both", expand=True, padx=20, pady=20
        )

        self.button_back_home.config(command=lambda: self.go_back_home())
        self.button_back_home.pack()

        if not self.playlists:
            fetching_thread = threading.Thread(target=self.fetch_playlists)
            fetching_thread.start()

    def fetch_playlists(self):
        self.playlists = self.sp.current_user_playlists()

        for playlist in self.playlists["items"]:
            playlist_name = playlist["name"]
            playlist_uri = playlist["uri"]
            self.playlist_uris[playlist_name] = playlist_uri

        for playlist_name in self.playlist_uris.keys():
            self.listbox_playlists.insert(tk.END, playlist_name)

        self.scrollbar_playlists.pack(side="right", fill="y")
        self.scrollbar_songs.pack_forget()

        self.listbox_playlists.bind("<ButtonRelease-1>", self.on_item_selected)

        self.close_progress_dialog()

    def on_item_selected(self, event):
        self.frame_view_all_playlists.pack_forget()
        self.scrollbar_playlists.pack_forget()
        self.scrollbar_songs.pack_forget()

        selected_index = self.listbox_playlists.curselection()
        if selected_index:
            index = selected_index[0]
            self.playlist_name = self.listbox_playlists.get(index)
            self.window.title(f"Playlist: {self.playlist_name}")
            self.frame_view_playlist.pack(fill=tk.BOTH, expand=True)
            self.frame_view_playlist.pack_propagate(False)

            self.playlist_uri = self.fetch_playlist_uri()

            self.fetch_and_display_playlist_data(self.playlist_name)

    def fetch_and_display_playlist_data(self, playlist_name):
        all_fetched_tracks = self.fetch_all_songs(
            self.playlist_uri, self.sp, self.song_cache)

        self.results = self.sp.playlist_tracks(self.playlist_uri)
        self.tracks = self.results["items"]
        self.track_uris = [self.track["track"]["uri"]
                           for self.track in self.tracks]

        while self.results["next"]:
            self.results = self.sp.next(self.results)
            self.tracks = self.results["items"]
            self.track_uris.extend([self.track["track"]["uri"]
                                   for self.track in self.tracks])

        self.display_progress_dialog("Loading Playlists...")

        self.playlist_thread = threading.Thread(target=self.display_playlist_information, args=(
            self.playlist_uri, playlist_name, all_fetched_tracks))
        self.playlist_thread.start()

    def method_playlist_image(self):

        self.label_playlist_image.config(image=None)

        self.playlist_image_url = (
            self.playlist["images"][0]["url"] if self.playlist["images"] else None
        )

        response = requests.get(self.playlist_image_url)

        original_image = Image.open(BytesIO(response.content))
        resized_image = original_image.resize((100, 100))
        playlist_image = ImageTk.PhotoImage(resized_image)

        width = playlist_image.width()
        height = playlist_image.height()

        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, height), fill=255)

        circular_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        circular_image.paste(resized_image, mask=mask)

        self.playlist_image = ImageTk.PhotoImage(circular_image)

        self.label_playlist_image.config(image=self.playlist_image)

    def display_playlist_information(self, playlist_uri, playlist_name, num_of_tracks):

        self.close_progress_dialog()

        self.playlist = self.sp.playlist(playlist_uri)

        self.method_playlist_image()

        self.playlist_name = playlist_name

        self.button_shuffle_playlist.config(
            command=lambda: self.shuffle_playlist_songs())
        self.button_back_view_playlists.config(
            command=lambda: self.go_back_view_playlists())
        self.button_view_songs.config(
            command=lambda: self.view_songs_in_playlist())

        self.text_num_songs = "Number of songs: " + str(len(self.track_uris))
        self.label_number_of_songs.config(text=self.text_num_songs)
        self.label_playlist_name.config(
            text=self.playlist_name, font=("Helvetica", 30))

        self.label_playlist_image.pack(anchor="n", pady=(30, 10))
        self.label_playlist_name.pack(anchor="n")
        self.label_number_of_songs.pack(anchor="n", pady=(10, 20))
        self.button_shuffle_playlist.pack(anchor="n", pady=(0, 10))
        self.button_view_songs.pack(anchor="n", pady=(0, 10))
        self.button_back_view_playlists.pack(anchor="n", pady=(0, 20))

    def view_songs_in_playlist(self):
        self.frame_view_playlist_songs.pack(expand=True)
        self.label_playlist_name.pack(anchor='n')
        self.frame_view_playlist_songs.pack_propagate(False)
        self.frame_view_playlist.pack_forget()
        self.listbox_view_songs.pack(
            side="top", fill="both", expand=True, padx=20, pady=20
        )
        self.scrollbar_songs.pack(side="right", fill="y")
        self.scrollbar_playlists.pack_forget()

        self.button_back_view_playlist.config(
            command=lambda: self.go_back_view_playlist_info())

        self.button_back_view_playlist.pack(anchor='n')

        self.listbox_view_songs.delete(0, tk.END)

        def fetch_songs():
            i = 0
            for track_uri in self.track_uris:
                track = self.sp.track(track_uri)
                track_name = track["name"]
                i += 1
                self.listbox_view_songs.insert(tk.END, f"{i}. {track_name}")

        song_thread = threading.Thread(target=fetch_songs)
        song_thread.start()

    def go_back_view_playlist_info(self):
        self.frame_view_playlist_songs.pack_forget()
        self.frame_view_playlist.pack()

    def shuffle_playlist_songs(self):
        batch_size = 100
        batches = [self.track_uris[i:i + batch_size]
                   for i in range(0, len(self.track_uris), batch_size)]

        try:
            random.shuffle(batches[0])
            self.sp.playlist_replace_items(self.playlist_uri, batches[0])

            for batch in batches[1:]:
                random.shuffle(batch)
                self.sp.playlist_add_items(self.playlist_uri, batch)

            self.playlist = self.sp.playlist(self.playlist_uri)

            messagebox.showinfo(
                "Shuffle", f"Playlist {self.playlist_name} successfully shuffled!")

        except SpotifyException as e:
            messagebox.showerror(f"Error updating playlist: {str(e)}")

        self.method_playlist_image()

    def go_back_view_playlists(self):
        self.frame_view_playlist.pack_forget()
        self.frame_view_all_playlists.pack()
        self.frame_view_all_playlists.pack_propagate(False)
        self.playlist_image_url = "https://upload.wikimedia.org/wikipedia/commons/a/ac/Default_pfp.jpg"
        self.playlist_name = None
        self.text_num_songs = None
        self.window.update_idletasks()
        self.view_playlists()

    def go_back_home(self):
        self.frame_view_all_playlists.pack_forget()
        self.home_screen()

    def display_progress_dialog(self, title):
        self.progress_dialog = tk.Toplevel(window)
        self.progress_dialog.title(title)
        self.progress_dialog.geometry("300x100")
        self.progress_dialog.configure(background=self.colour_background)

        self.label_songs_loaded = tk.Label(
            self.progress_dialog, text=title + " 0")
        self.progress_bar = ttk.Progressbar(
            self.progress_dialog, orient=tk.HORIZONTAL, length=220, mode="indeterminate")

        self.progress_bar.pack(pady=20)
        self.progress_bar.start()
        self.label_songs_loaded.pack()

        self.update_progress_dialog()

    def update_progress_dialog(self):
        self.progress_dialog.update_idletasks()
        window.after(100, self.update_progress_dialog)

    def close_progress_dialog(self):
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_dialog.destroy()


def main():
    global window
    window = tk.Tk()
    window.iconbitmap("ALogoSpotify.ico")
    SpotifyToolsApp(window)
    window.state('zoomed')
    window.mainloop()
    print("Running SpotifyTools!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboard Interrupted Program Execution!")
