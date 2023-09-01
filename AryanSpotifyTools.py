import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import base64
from PIL import ImageTk, Image, ImageDraw
from io import BytesIO
import cachetools


class SpotifyToolsApp:
    def __init__(self, window):
        self.window = window
        window.title("Spotify Login")

        self.CLIENT_ID = "58817dcd8cc54baa9dd033ea9ef0f86f"
        self.CLIENT_SECRET = "8fe689bda9e64b3d8b4e111301cf6a44"
        self.REDIRECT_URI = "http://localhost:8888/callback"

        self.playlist_uris = {}

        self.song_cache = cachetools.LRUCache(maxsize=10000)

        self.login_screen()
        self.frame_view_playlist = tk.Frame(self.window, width=500, height=300)
        self.frame_view_playlist.grid_rowconfigure(0, weight=1)
        self.frame_view_playlist.grid_columnconfigure(0, weight=1)
        self.frame_view_playlist.pack_propagate(False)
        self.selected_playlist_label = tk.Label(self.frame_view_playlist)

        self.frame_view_all_playlists = tk.Frame(self.window, width=500, height=300)

        self.playlist_listbox = tk.Listbox(self.frame_view_all_playlists)

        self.back_view_playlist_button = tk.Button(
            self.frame_view_playlist,
            text="Back",
            command=lambda: self.go_back_view_playlists(),
        )

        self.back_home = tk.Button(
            self.frame_view_all_playlists,
            text="Home",
            command=lambda: self.go_back_home(),
        )
        self.progress_dialog = None

    # initialisation method ends here ^^^^^

    def login_screen(self):
        self.frame_login = tk.Frame(self.window, width=500, height=300)
        self.frame_login.grid_rowconfigure(0, weight=1)
        self.frame_login.grid_columnconfigure(0, weight=1)
        self.frame_login.pack_propagate(False)
        self.frame_login.pack(fill=tk.BOTH, expand=True)

        original_image = Image.open("spotify_logo.png")
        resized_image = original_image.resize((333, 100))
        spotify_logo = ImageTk.PhotoImage(resized_image)

        self.logo = tk.Label(self.frame_login, image=spotify_logo)
        self.logo.image = spotify_logo
        self.logo.grid(row=0, column=0, pady=(40, 10), padx=50)

        tk.Label(
            self.frame_login,
            text="Welcome to Aryan's SpotifyTools!",
            font=("Helvetica", 20, "bold"),
            foreground="#1ab26b",
        ).grid(row=1, column=0, pady=(10, 20), padx=30)

        self.login_button = tk.Button(
            self.frame_login,
            text="Login to Spotify",
            command=self.login_to_spotify,
        ).grid(row=2, column=0, pady=(10, 40), padx=30)

    def login_to_spotify(self):
        self.sp_oauth = SpotifyOAuth(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri=self.REDIRECT_URI,
            scope="playlist-modify-private playlist-modify-public",
            open_browser="true",
            show_dialog="true",
        )
        self.access_token = self.sp_oauth.get_access_token()
        self.sp = Spotify(auth=self.access_token["access_token"])
        self.user = self.sp.current_user()

        if self.access_token and "access_token" in self.access_token:
            print(f"Logged in as: {self.user['display_name']}")
            # messagebox.showinfo("Success!", "Connection Successfull!")
            self.frame_login.pack_forget()
            self.home_screen()
        else:
            messagebox.showerror("Error", "Connection Unsuccessfull")

    def logout(self):
        if self.access_token:
            if self.revoke_access_token():
                print("Access token revoked successfully.")
                self.frame_home.pack_forget()
                self.frame_login.pack()
                messagebox.showinfo("Success", "Succesfully logged out!")

            else:
                print("Failed to revoke access token.")

            self.user = None
            self.access_token = None
            self.sp = None

    def revoke_access_token(self):
        if self.access_token:
            revocation_url = "https://accounts.spotify.com/api/token"
            headers = {
                "Authorization": f"Basic {self.get_base64_encoded_credentials()}"
            }
            data = {"token": self.access_token}
            response = requests.post(revocation_url, data=data, headers=headers)
            print(response.status_code)
            return True
        else:
            return False

    def get_base64_encoded_credentials(self):
        credentials = f"{self.CLIENT_ID}:{self.CLIENT_SECRET}"
        return base64.b64encode(credentials.encode()).decode()

    def home_screen(self):
        self.window.title("Home")
        self.frame_home = tk.Frame(self.window, width=500, height=300)
        self.frame_home.grid_rowconfigure(0, weight=1)
        self.frame_home.grid_columnconfigure(0, weight=1)
        self.frame_home.pack_propagate(False)
        self.frame_home.pack(fill=tk.BOTH, expand=True)

        logout_icon = Image.open("logout_icon.png")
        resized_logout_icon = logout_icon.resize((35, 35))
        self.logout_icon = ImageTk.PhotoImage(resized_logout_icon)

        self.logout_button = tk.Button(
            self.frame_home, image=self.logout_icon, command=self.logout
        )
        self.logout_button.image = self.logout_icon

        name, imageurl = self.fetch_user_details()
        self.display_user_profile(name, imageurl)

    def fetch_user_details(self):
        display_name = self.user["display_name"]
        profile_image_url = (
            self.user["images"][0]["url"] if self.user["images"] else None
        )

        return display_name, profile_image_url

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

        self.image_label = tk.Label(self.frame_home, image=self.user_image)
        self.image_label.grid(row=1, column=0, pady=(50), padx=(30, 10))

        tk.Label(
            self.frame_home, text=name, font=("Helvetica", 25), foreground="#000"
        ).grid(row=1, column=1, pady=(50), padx=(10, 10))

        self.button_playlist = tk.Button(
            self.frame_home,
            text="View Playlists",
            command=self.view_playlists,
        ).grid(row=2, column=0, pady=(10, 40), padx=30)

        self.logout_button.grid(row=1, column=3, pady=(50), padx=(10, 30))

    def fetch_playlist_uri(self):
        selected_index = self.playlist_listbox.curselection()

        if selected_index:
            index = selected_index[0]
            selected_item = self.playlist_listbox.get(index)
            selected_playlist_uri = self.playlist_uris.get(selected_item, "")
            return selected_playlist_uri

    def view_playlists(self):
        self.window.title("View Playlists")
        self.frame_home.pack_forget()
        self.frame_view_all_playlists.pack(expand=True)

        self.playlists = self.sp.current_user_playlists()

        for playlist in self.playlists["items"]:
            self.playlist_name = playlist["name"]
            self.playlist_uri = playlist["uri"]
            self.playlist_uris[self.playlist_name] = self.playlist_uri

        for playlist_name in self.playlist_uris.keys():
            self.playlist_listbox.insert(tk.END, playlist_name)

        self.playlist_listbox.pack(
            side="top", fill="both", expand=True, padx=20, pady=20
        )

        self.playlist_listbox.bind("<ButtonRelease-1>", self.on_item_selected)

        self.back_view_playlist_button.pack()
        self.back_home.pack()

    def on_item_selected(self, event):
        self.frame_view_all_playlists.pack_forget()

        selected_index = self.playlist_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            selected_item = self.playlist_listbox.get(index)
            self.playlist_listbox.pack_forget()
            self.frame_view_playlist.pack(fill=tk.BOTH, expand=True)

            playlist_uri = self.fetch_playlist_uri()
            number_of_tracks = self.fetch_all_songs(playlist_uri)

            self.back_view_playlist_button.pack()

            self.selected_playlist_label.config(
                text=f"Number of songs in {selected_item}: {number_of_tracks}"
            )
            self.selected_playlist_label.pack()


        print(f"Number of songs in {selected_item}: {number_of_tracks}")

    def fetch_all_songs(self,playlist_uri):

        if playlist_uri in self.song_cache:
            return len(self.song_cache[playlist_uri])

        all_tracks = []

        playlist_tracks = self.sp.playlist_tracks(playlist_uri)
        self.display_progress_dialog()
        self.progress_dialog.update_idletasks()

        while playlist_tracks:
            all_tracks.extend(playlist_tracks['items'])

            next_page = playlist_tracks['next']
            if not next_page:
                self.close_progress_dialog()
                break

            playlist_tracks = self.sp.next(playlist_tracks)

            loaded_tracks = len(all_tracks)
            self.songs_loaded_label.config(text=f"Loading Songs... {loaded_tracks}")
            self.progress_dialog.update_idletasks()

        self.song_cache[playlist_uri] = all_tracks
        return len(all_tracks)

    def display_progress_dialog(self):
        self.progress_dialog = tk.Toplevel(self.window)
        self.progress_dialog.title("Loading Songs...")
        self.progress_dialog.geometry("300x100")

        self.progress_bar = ttk.Progressbar(self.progress_dialog, orient=tk.HORIZONTAL, length=220, mode="indeterminate")
        self.progress_bar.pack(pady=20)

        self.songs_loaded_label = tk.Label(self.progress_dialog, text="Loading Songs... 0")
        self.songs_loaded_label.pack()

        self.progress_bar.start()

    def close_progress_dialog(self):
        if self.progress_dialog:
            self.progress_dialog.destroy()

    def go_back_view_playlists(self):
        self.frame_view_playlist.pack_forget()
        self.view_playlists()

    def go_back_home(self):
        self.frame_view_all_playlists.pack_forget()
        self.home_screen()

def main():
    window = tk.Tk()
    SpotifyToolsApp(window)
    window.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboard Interrupted Program Execution!")