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
        self.root.geometry("900x600")  # Điều chỉnh kích thước giao diện
        self.root.resizable(False, False)  # Cố định kích cỡ giao diện

        # Khởi tạo pygame mixer
        pygame.mixer.init()
        self.current_song = None
        self.paused = False
        self.current_position = 0  # Thời gian đã phát (ms)
        self.total_duration = 0  # Tổng thời gian (ms)

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
        # Hàng 1: Thanh âm lượng + Nút dừng/phát + Thanh timeline
        volume_frame = ctk.CTkFrame(self.root)
        volume_frame.pack(fill='x', padx=10, pady=5)

        ctk.CTkLabel(volume_frame, text="ÂM LƯỢNG:     MIN", width=80).pack(side='left', padx=5)
        self.volume_slider = ctk.CTkSlider(volume_frame, from_=0, to=100, command=self.set_volume, width=200)
        self.volume_slider.set(50)
        self.volume_slider.pack(side='left', padx=5)
        self.volume_label = ctk.CTkLabel(volume_frame, text="50", width=40)
        self.volume_label.pack(side='left', padx=5)
        self.max_label = ctk.CTkLabel(volume_frame, text="MAX", width=40)
        self.max_label.pack(side='left', padx=5)
        self.time_played_label = ctk.CTkLabel(volume_frame, text="00:00", width=60)
        self.time_played_label.pack(side='left', padx=2)
        self.timeline_slider = ctk.CTkSlider(volume_frame, from_=0, to=100, width=200, state="disabled")  # Không tương tác
        self.timeline_slider.set(0)
        self.timeline_slider.pack(side='left', padx=2)
        self.time_remaining_label = ctk.CTkLabel(volume_frame, text="- 00:00", width=60)
        self.time_remaining_label.pack(side='left', padx=2)
        self.play_pause_button = ctk.CTkButton(volume_frame, text="TẠM DỪNG", width=150, height=40, command=self.toggle_play_pause)
        self.play_pause_button.pack(side='right', padx=10)

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
        ctk.CTkButton(button_frame, text="CHỈNH SỬA", width=150, command=self.open_data_folder).pack(side='right', padx=5)

        # Cập nhật scroll
        self.tab_inner_frame.bind('<Configure>',
                                  lambda e: self.tab_canvas.configure(scrollregion=self.tab_canvas.bbox('all')))
        self.song_inner_frame.bind('<Configure>',
                                   lambda e: self.song_canvas.configure(scrollregion=self.song_canvas.bbox('all')))

    def set_volume(self, val):
        volume = float(val) / 100
        pygame.mixer.music.set_volume(volume)
        self.volume_label.configure(text=str(int(val)))

    def toggle_play_pause(self):
        if self.current_song:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_pause_button.configure(text="TẠM DỪNG")
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.play_pause_button.configure(text="PHÁT LẠI")
        else:
            # Nếu không có bài hát nào đang chơi, không làm gì
            pass

    def stop_music(self):
        # Phương thức này giờ không còn được dùng trực tiếp, giữ lại để tương thích
        pass

    def format_time(self, ms):
        # Chuyển đổi mili giây thành định dạng MM:SS, ép kiểu thành số nguyên
        if ms < 0:
            ms = 0
        minutes = int(ms // 60000)  # Ép thành số nguyên
        seconds = int((ms % 60000) // 1000)  # Ép thành số nguyên
        return f"{minutes:02d}:{seconds:02d}"

    def set_position(self, val):
        # Phương thức này không còn được dùng, giữ lại để tương thích
        pass

    def update_time(self):
        # Cập nhật thanh timeline và thời gian
        if self.current_song and not self.paused and self.total_duration > 0:
            self.current_position = pygame.mixer.music.get_pos()
            if self.current_position < 0:  # Xử lý trường hợp âm (có thể xảy ra khi kết thúc)
                self.current_position = self.total_duration
            progress = (self.current_position / self.total_duration) * 100
            self.timeline_slider.set(progress)
            time_played = self.format_time(self.current_position)
            time_remaining = self.format_time(self.total_duration - self.current_position)
            self.time_played_label.configure(text=time_played)
            self.time_remaining_label.configure(text="- " + time_remaining)
        self.root.after(1000, self.update_time)  # Cập nhật mỗi giây

    def wrap_text(self, text, max_chars=45):
        # Tách tên bài hát thành nhiều dòng, giữ nguyên ý nghĩa, xuống dòng tại khoảng trắng
        if len(text) <= max_chars:
            return text
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            # Thêm độ dài từ hiện tại + 1 (khoảng trắng)
            word_length = len(word)
            if current_length + word_length + 1 > max_chars and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length + 1

        if current_line:
            lines.append(" ".join(current_line))

        # Giới hạn tối đa 2 dòng
        if len(lines) > 2:
            return "\n".join(lines[:2]) + "..."
        return "\n".join(lines)

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
                    {"display": self.wrap_text(fname), "file": fname} for fname in song_files  # Hiển thị tên đã tách
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

        # Tạo buttons cho bài hát (2 cột)
        song_list = self.songs[tab]
        for i, song in enumerate(song_list):
            btn = ctk.CTkButton(self.song_inner_frame, text=song["display"], width=415, height=80,  # Độ rộng 400px, hỗ trợ 2 dòng
                                command=lambda s=song["file"], t=tab: self.play_song(t, s))
            row = i // 2  # Số dòng
            col = i % 2   # Vị trí trong 2 cột
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')

    def play_song(self, tab, song):
        if self.current_song == song and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
            self.play_pause_button.configure(text="PHÁT LẠI")
        else:
            if self.current_song != song:
                if self.current_song:
                    pygame.mixer.music.stop()
                song_path = os.path.join(self.data_dir, tab, song)
                pygame.mixer.music.load(song_path)
                pygame.mixer.music.play()
                self.current_song = song
                self.current_position = 0
                try:
                    sound = pygame.mixer.Sound(song_path)
                    self.total_duration = sound.get_length() * 1000  # Tổng thời gian (ms)
                except pygame.error:
                    self.total_duration = 0
                self.paused = False
                self.play_pause_button.configure(text="TẠM DỪNG")
            else:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_pause_button.configure(text="TẠM DỪNG")

    def open_data_folder(self):
        subprocess.run(['explorer', self.data_dir.replace('/', '\\')])

    def run(self):
        self.update_time()  # Bắt đầu cập nhật thanh timeline và thời gian
        self.root.mainloop()


if __name__ == "__main__":
    root = ctk.CTk()
    app = MusicPlayerApp(root)
    app.run()