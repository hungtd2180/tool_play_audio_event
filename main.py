import os
import sys
import subprocess
import customtkinter as ctk
from pathlib import Path
import pygame


class MusicPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tool Audio Sự Kiện")
        self.root.geometry("840x600")
        self.root.resizable(False, False)  # Cố định kích cỡ giao diện

        # Khởi tạo pygame mixer
        pygame.mixer.init()
        self.current_song = None
        self.paused = False

        # Lấy đường dẫn thư mục data (hỗ trợ đóng gói .exe)
        if getattr(sys, 'frozen', False):
            self.data_dir = os.path.join(os.path.dirname(sys.executable), 'data')
        else:
            self.data_dir = os.path.join(os.path.dirname(__file__), 'data')

        # Đảm bảo thư mục data tồn tại
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Cấu hình giao diện
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Hàng 1: Thanh âm lượng + Nút dừng
        volume_frame = ctk.CTkFrame(self.root)
        volume_frame.pack(fill='x', padx=10, pady=5)

        ctk.CTkLabel(volume_frame, text="ÂM LƯỢNG:     MIN", width=80).pack(side='left', padx=5)
        self.volume_slider = ctk.CTkSlider(volume_frame, from_=0, to=100, command=self.set_volume, width=200)
        self.volume_slider.set(50)
        self.volume_slider.pack(side='left', padx=5)
        self.volume_label = ctk.CTkLabel(volume_frame, text="50", width=40)
        self.volume_label.pack(side='left', padx=5)
        ctk.CTkLabel(volume_frame, text="MAX", width=80).pack(side='left', padx=5)
        ctk.CTkButton(volume_frame, text="DỪNG PHÁT", width=150, height=40, command=self.stop_music).pack(side='right',
                                                                                                          padx=10)

        # Hàng 2: Tabs (scroll ngang)
        self.tab_frame = ctk.CTkFrame(self.root)
        self.tab_frame.pack(fill='x', padx=10, pady=5)

        self.tab_canvas = ctk.CTkCanvas(self.tab_frame, height=40)
        self.tab_scrollbar = ctk.CTkScrollbar(self.tab_frame, orientation="horizontal", command=self.tab_canvas.xview)
        self.tab_canvas.configure(xscrollcommand=self.tab_scrollbar.set)
        self.tab_scrollbar.pack(side='bottom', fill='x')
        self.tab_canvas.pack(side='top', fill='x')

        self.tab_inner_frame = ctk.CTkFrame(self.tab_canvas)
        self.tab_canvas.create_window((0, 0), window=self.tab_inner_frame, anchor='nw')

        # Hàng 3: Danh sách bài hát (scroll dọc)
        self.song_frame = ctk.CTkFrame(self.root)
        self.song_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.song_canvas = ctk.CTkCanvas(self.song_frame)
        self.song_scrollbar = ctk.CTkScrollbar(self.song_frame, orientation="vertical", command=self.song_canvas.yview)
        self.song_canvas.configure(yscrollcommand=self.song_scrollbar.set)
        self.song_scrollbar.pack(side='right', fill='y')
        self.song_canvas.pack(side='left', fill='both', expand=True)

        self.song_inner_frame = ctk.CTkFrame(self.song_canvas)
        self.song_canvas.create_window((0, 0), window=self.song_inner_frame, anchor='nw')

        # Hàng 4: Nút Cập nhật + Chỉnh sửa
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkButton(button_frame, text="CẬP NHẬT", width=150, command=self.load_data).pack(side='left', padx=5)
        ctk.CTkButton(button_frame, text="CHỈNH SỬA", width=150, command=self.open_data_folder).pack(side='right',
                                                                                                     padx=5)

        # Cập nhật scroll
        self.tab_inner_frame.bind('<Configure>',
                                  lambda e: self.tab_canvas.configure(scrollregion=self.tab_canvas.bbox('all')))
        self.song_inner_frame.bind('<Configure>',
                                   lambda e: self.song_canvas.configure(scrollregion=self.song_canvas.bbox('all')))

    def set_volume(self, val):
        volume = float(val) / 100
        pygame.mixer.music.set_volume(volume)
        self.volume_label.configure(text=str(int(val)))

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_song = None
        self.paused = False

    def load_data(self):
        # Xóa giao diện cũ
        for widget in self.tab_inner_frame.winfo_children():
            widget.destroy()
        for widget in self.song_inner_frame.winfo_children():
            widget.destroy()

        # Quét thư mục data
        self.tabs = []
        self.songs = {}
        for folder in Path(self.data_dir).iterdir():
            if folder.is_dir():
                self.tabs.append(folder.name)
                song_files = [f.name for f in folder.iterdir() if f.suffix.lower() in ['.mp3', '.wav']]
                self.songs[folder.name] = [
                    {"display": f"Bài {i + 1}", "file": fname} for i, fname in enumerate(song_files)
                ]

        # Tạo buttons cho tabs với chữ đen đậm
        self.tab_buttons = {}
        for tab in self.tabs:
            btn = ctk.CTkButton(self.tab_inner_frame, text=tab, width=100, command=lambda t=tab: self.load_songs(t),
                                fg_color="transparent", text_color="black", font=("Arial", 12, "bold"))
            btn.pack(side='left', padx=5)
            self.tab_buttons[tab] = btn

        # Load tab đầu tiên nếu có
        if self.tabs:
            self.load_songs(self.tabs[0])
            self.tab_buttons[self.tabs[0]].configure(fg_color="#3498db",
                                                     text_color="white")  # Nền xanh, chữ trắng khi chọn

    def load_songs(self, tab):
        # Cập nhật trạng thái button tab
        for btn in self.tab_buttons.values():
            btn.configure(fg_color="transparent", text_color="black", font=("Arial", 12, "bold"))
        self.tab_buttons[tab].configure(fg_color="#3498db", text_color="white")  # Nền xanh, chữ trắng khi chọn

        # Xóa danh sách bài hát cũ
        for widget in self.song_inner_frame.winfo_children():
            widget.destroy()

        # Tạo buttons cho bài hát (5 cột)
        song_list = self.songs[tab]
        for i, song in enumerate(song_list):
            btn = ctk.CTkButton(self.song_inner_frame, text=song["display"], width=150, height=40,
                                command=lambda s=song["file"], t=tab: self.play_song(t, s))
            row = i // 5  # Số dòng
            col = i % 5  # Vị trí trong 5 cột
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')

    def play_song(self, tab, song):
        if self.current_song == song and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
        else:
            if self.current_song != song:
                song_path = os.path.join(self.data_dir, tab, song)
                pygame.mixer.music.load(song_path)
                pygame.mixer.music.play()
                self.current_song = song
            else:
                pygame.mixer.music.unpause()
            self.paused = False

    def open_data_folder(self):
        subprocess.run(['explorer', self.data_dir.replace('/', '\\')])

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = ctk.CTk()
    app = MusicPlayerApp(root)
    app.run()