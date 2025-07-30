import ffmpeg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import threading
import time
import tkinter as tk
from tkinter import simpledialog

class DualRTSPViewer:
    def __init__(self):
        self.cameras = [
            {"name": "Kamera 1", "url": "", "process": None, "frame": None, "fps": 0, "frame_count": 0, "last_time": time.time()},
            {"name": "Kamera 2", "url": "", "process": None, "frame": None, "fps": 0, "frame_count": 0, "last_time": time.time()}
        ]
        self.is_running = False
        self.fig = None
        self.setup_ui()

    def setup_ui(self):
        self.fig = plt.figure(figsize=(16, 8))
        self.fig.canvas.manager.set_window_title('Çift RTSP Görüntüleyici - FPS Göstergeli')
        
        # Kamera 1 Görüntü Alanı (Sol)
        self.ax1 = self.fig.add_axes([0.02, 0.15, 0.47, 0.75])
        self.im1 = self.ax1.imshow(np.zeros((720, 1280, 3), dtype=np.uint8))
        self.ax1.axis('off')
        self.ax1.set_title('Kamera 1 - FPS: 0.0', pad=10)
        
        # Kamera 2 Görüntü Alanı (Sağ)
        self.ax2 = self.fig.add_axes([0.51, 0.15, 0.47, 0.75])
        self.im2 = self.ax2.imshow(np.zeros((720, 1280, 3), dtype=np.uint8))
        self.ax2.axis('off')
        self.ax2.set_title('Kamera 2 - FPS: 0.0', pad=10)
        
        # Bilgi Paneli (Üst Orta)
        self.info_ax = self.fig.add_axes([0.3, 0.9, 0.4, 0.05])
        self.info_ax.axis('off')
        self.info_text = self.info_ax.text(
            0.5, 0.5, 
            "Her iki kamera için URL girin ve Başlat'a basın",
            fontsize=10,
            horizontalalignment='center',
            verticalalignment='center'
        )
        
        # Kontrol Butonları (Alt Kısım)
        self.url1_btn_ax = self.fig.add_axes([0.1, 0.05, 0.15, 0.05])
        self.url1_btn = Button(self.url1_btn_ax, 'Kamera 1 URL', color='lightyellow')
        self.url1_btn.on_clicked(lambda x: self.change_url(0))
        
        self.url2_btn_ax = self.fig.add_axes([0.3, 0.05, 0.15, 0.05])
        self.url2_btn = Button(self.url2_btn_ax, 'Kamera 2 URL', color='lightyellow')
        self.url2_btn.on_clicked(lambda x: self.change_url(1))
        
        self.btn_ax = self.fig.add_axes([0.5, 0.05, 0.15, 0.05])
        self.btn = Button(self.btn_ax, 'Başlat', color='lightgreen')
        self.btn.on_clicked(self.toggle_stream)
        
        self.test_ax = self.fig.add_axes([0.7, 0.05, 0.15, 0.05])
        self.test_btn = Button(self.test_ax, 'Bağlantıları Sına', color='lightblue')
        self.test_btn.on_clicked(self.test_connections)
        
        # Pencere kapatma olayı
        self.fig.canvas.mpl_connect('close_event', self.on_close)

    def change_url(self, cam_index):
        """Kamera URL'sini değiştir"""
        root = tk.Tk()
        root.withdraw()
        try:
            new_url = simpledialog.askstring(
                "RTSP URL Değiştir",
                f"{self.cameras[cam_index]['name']} için yeni URL:",
                initialvalue=self.cameras[cam_index]["url"] or "rtsp://"
            )
            if new_url:
                self.cameras[cam_index]["url"] = new_url.strip()
                self.update_info(f"{self.cameras[cam_index]['name']} URL güncellendi")
        finally:
            try:
                root.destroy()
            except:
                pass

    def update_info(self, message):
        """Bilgi panelini güncelle"""
        self.info_text.set_text(message)
        self.fig.canvas.draw_idle()

    def update_fps(self, cam_index):
        """FPS bilgisini güncelle ve başlıkta göster"""
        cam = self.cameras[cam_index]
        current_time = time.time()
        time_diff = current_time - cam['last_time']
        
        if time_diff > 0.5:  # Her 0.5 saniyede bir FPS güncelle
            cam['fps'] = cam['frame_count'] / time_diff
            cam['frame_count'] = 0
            cam['last_time'] = current_time
            
            if cam_index == 0:
                self.ax1.set_title(f'Kamera 1 - FPS: {cam["fps"]:.1f}')
            else:
                self.ax2.set_title(f'Kamera 2 - FPS: {cam["fps"]:.1f}')

    def test_connections(self, event):
        """Her iki kameranın bağlantısını test et"""
        test_thread = threading.Thread(target=self._test_connections, daemon=True)
        test_thread.start()

    def _test_connections(self):
        """Bağlantı testi için thread fonksiyonu"""
        results = []
        for cam in self.cameras:
            if not cam["url"]:
                results.append(f"{cam['name']}: URL girilmedi")
                continue
                
            try:
                process = (
                    ffmpeg
                    .input(cam["url"], rtsp_transport='tcp', timeout=5000000)
                    .output('null', format='null')
                    .run_async(pipe_stderr=True)
                )
                
                time.sleep(2)
                _, stderr = process.communicate()
                
                if process.returncode == 0:
                    results.append(f"{cam['name']}: Bağlantı başarılı")
                else:
                    error = stderr.decode('utf-8')[:100]
                    results.append(f"{cam['name']}: Hata - {error}")
            except Exception as e:
                results.append(f"{cam['name']}: Hata - {str(e)}")
        
        self.update_info(" | ".join(results))

    def toggle_stream(self, event):
        """Akışı başlat/durdur"""
        if not self.is_running:
            self.start_stream()
        else:
            self.stop_stream()

    def start_stream(self):
        """Her iki kameradan akış başlat"""
        if not all(cam["url"] for cam in self.cameras):
            self.update_info("Hata: Her iki kamera için URL girin!")
            return
            
        self.is_running = True
        self.btn.label.set_text("Durdur")
        self.update_info("Akış başlatılıyor...")
        
        try:
            # Kamera 1 için akış
            self.cameras[0]["process"] = (
                ffmpeg
                .input(self.cameras[0]["url"], rtsp_transport='tcp', timeout=5000000)
                .output('pipe:', format='rawvideo', pix_fmt='rgb24', s='1280x720')
                .run_async(pipe_stdout=True)
            )
            
            # Kamera 2 için akış
            self.cameras[1]["process"] = (
                ffmpeg
                .input(self.cameras[1]["url"], rtsp_transport='tcp', timeout=5000000)
                .output('pipe:', format='rawvideo', pix_fmt='rgb24', s='1280x720')
                .run_async(pipe_stdout=True)
            )
            
            # Frame güncelleme thread'i
            self.stream_thread = threading.Thread(target=self.update_frames, daemon=True)
            self.stream_thread.start()
            
        except Exception as e:
            self.update_info(f"Başlatma hatası: {str(e)}")
            self.is_running = False
            self.btn.label.set_text("Başlat")

    def update_frames(self):
        """Her iki kameradan gelen görüntüleri güncelle"""
        width, height = 1280, 720
        
        while self.is_running:
            try:
                # Kamera 1'den görüntü al
                bytes1 = self.cameras[0]["process"].stdout.read(width * height * 3)
                if bytes1:
                    frame1 = np.frombuffer(bytes1, np.uint8).reshape((height, width, 3))
                    self.im1.set_data(frame1)
                    self.cameras[0]['frame_count'] += 1
                    self.update_fps(0)
                
                # Kamera 2'den görüntü al
                bytes2 = self.cameras[1]["process"].stdout.read(width * height * 3)
                if bytes2:
                    frame2 = np.frombuffer(bytes2, np.uint8).reshape((height, width, 3))
                    self.im2.set_data(frame2)
                    self.cameras[1]['frame_count'] += 1
                    self.update_fps(1)
                
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                time.sleep(0.01)
                
            except Exception as e:
                if self.is_running:
                    self.update_info(f"Görüntü alma hatası: {str(e)}")
                break

    def stop_stream(self):
        """Akışı durdur ve kaynakları temizle"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.btn.label.set_text("Başlat")
        self.update_info("Akış durduruldu")
        
        for cam in self.cameras:
            if cam["process"]:
                try:
                    cam["process"].terminate()
                    cam["process"].wait(timeout=1)
                    cam["process"] = None
                except:
                    pass

    def on_close(self, event):
        """Pencere kapatıldığında temizlik yap"""
        self.stop_stream()

    def run(self):
        """Uygulamayı çalıştır"""
        try:
            plt.show(block=True)
        except KeyboardInterrupt:
            self.stop_stream()

if __name__ == "__main__":
    viewer = DualRTSPViewer()
    viewer.run()