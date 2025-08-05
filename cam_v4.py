import ffmpeg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import threading
import time
import tkinter as tk
from tkinter import simpledialog

class StableRTSPViewer:
    def __init__(self):
        self.process = None
        self.rtsp_url = ""
        self.is_running = False
        self.fig = None
        self.setup_ui()

    def setup_ui(self):
        plt.ion()  # Etkileşim modunu aç
        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        self.fig.canvas.manager.set_window_title('Stabil RTSP Görüntüleyici')
        
        # Görüntü alanı
        self.im = self.ax.imshow(np.zeros((720, 1280, 3), dtype=np.uint8))
        self.ax.axis('off')
        
        # Kontrol butonları
        self.url_btn_ax = plt.axes([0.3, 0.05, 0.4, 0.1])
        self.url_btn = Button(self.url_btn_ax, 'RTSP URL Gir', color='lightblue')
        self.url_btn.on_clicked(self.change_url)
        
        self.connect_btn_ax = plt.axes([0.3, 0.15, 0.4, 0.1])
        self.connect_btn = Button(self.connect_btn_ax, 'BAĞLAN', color='lightgreen')
        self.connect_btn.on_clicked(self.toggle_stream)
        
        # Pencere kapatma olayı
        self.fig.canvas.mpl_connect('close_event', self.on_close)

    def change_url(self, event):
        root = tk.Tk()
        root.withdraw()
        try:
            new_url = simpledialog.askstring(
                "RTSP URL",
                "RTSP URL girin:",
                initialvalue=self.rtsp_url or "rtsp://"
            )
            if new_url:
                self.rtsp_url = new_url.strip()
        finally:
            try:
                root.destroy()
            except:
                pass

    def toggle_stream(self, event):
        if not self.is_running:
            self.start_stream()
        else:
            self.stop_stream()

    def start_stream(self):
        if not self.rtsp_url:
            return
            
        self.is_running = True
        self.connect_btn.label.set_text("DURDUR")
        
        try:
            # Daha stabil FFmpeg parametreleri
            self.process = (
                ffmpeg
                .input(self.rtsp_url, 
                      rtsp_transport='tcp',
                      timeout='5000000',
                      fflags='nobuffer',
                      flags='low_delay')
                .output('pipe:',
                       format='rawvideo',
                       pix_fmt='rgb24',
                       s='1280x720',
                       r='25',  # FPS
                       threads='2')
                .run_async(pipe_stdout=True)
            )
            
            self.stream_thread = threading.Thread(target=self.update_frame)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
        except Exception as e:
            print(f"Başlatma hatası: {e}")
            self.is_running = False
            self.connect_btn.label.set_text("BAĞLAN")

    def update_frame(self):
        width, height = 1280, 720
        
        while self.is_running:
            try:
                in_bytes = self.process.stdout.read(width * height * 3)
                if not in_bytes:
                    print("Akış sonlandı: Veri alınamıyor")
                    break
                    
                frame = np.frombuffer(in_bytes, np.uint8).reshape((height, width, 3))
                self.im.set_data(frame)
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                
            except Exception as e:
                if self.is_running:  # Beklenmeyen hataları logla
                    print(f"Görüntü işleme hatası: {e}")
                break

    def stop_stream(self):
        if not self.is_running:
            return
            
        self.is_running = False
        self.connect_btn.label.set_text("BAĞLAN")
        
        if self.process:
            try:
                self.process.stdin.close() if self.process.stdin else None
                self.process.stdout.close() if self.process.stdout else None
                self.process.stderr.close() if self.process.stderr else None
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception as e:
                print(f"Durdurma hatası: {e}")
            finally:
                self.process = None

    def on_close(self, event):
        self.stop_stream()

    def run(self):
        try:
            plt.show(block=True)  # block=True ile ana thread'i kilitle
        except KeyboardInterrupt:
            self.stop_stream()
        finally:
            plt.close('all')

if __name__ == "__main__":
    viewer = StableRTSPViewer()
    viewer.run()