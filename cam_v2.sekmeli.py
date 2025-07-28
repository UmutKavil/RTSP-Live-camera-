import ffmpeg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
import threading
import time
import tkinter as tk
from tkinter import simpledialog

class RTSPViewer:
    def __init__(self):
        self.cameras = [
            {"name": "Kamera 1", "url": "", "active": True, "process": None},
            {"name": "Kamera 2", "url": "", "active": False, "process": None}
        ]
        self.is_running = False
        self.current_cam = 0
        self.fig = None
        self.setup_ui()

    def setup_ui(self):
        self.fig = plt.figure(figsize=(16, 9))
        self.fig.canvas.manager.set_window_title('Çoklu RTSP Görüntüleyici')
        
        # Ana görüntü alanı
        self.ax = self.fig.add_axes([0.1, 0.15, 0.8, 0.75])
        self.im = self.ax.imshow(np.zeros((720, 1280, 3), dtype=np.uint8))
        self.ax.axis('off')
        
        # Kamera seçim radyo butonları (sekmeler)
        self.cam_select_ax = self.fig.add_axes([0.1, 0.05, 0.3, 0.08])
        self.cam_selector = RadioButtons(
            self.cam_select_ax, 
            [cam["name"] for cam in self.cameras],
            activecolor='lightblue'
        )
        self.cam_selector.on_clicked(self.switch_camera)
        
        # Bilgi paneli (sol üst)
        self.info_ax = self.fig.add_axes([0.02, 0.85, 0.3, 0.1])
        self.info_ax.axis('off')
        self.info_text = self.info_ax.text(
            0.01, 0.5, 
            "Kamera seçin ve URL ayarlayın",
            fontsize=10,
            verticalalignment='top',
            bbox=dict(facecolor='white', alpha=0.7)
        )
        
        # Kontrol butonları
        self.url_btn_ax = self.fig.add_axes([0.45, 0.05, 0.15, 0.05])
        self.url_btn = Button(self.url_btn_ax, 'URL Değiştir', color='lightyellow')
        self.url_btn.on_clicked(self.change_url)
        
        self.btn_ax = self.fig.add_axes([0.62, 0.05, 0.15, 0.05])
        self.btn = Button(self.btn_ax, 'Başlat', color='lightgreen')
        self.btn.on_clicked(self.toggle_stream)
        
        self.test_ax = self.fig.add_axes([0.79, 0.05, 0.15, 0.05])
        self.test_btn = Button(self.test_ax, 'Bağlantıyı Sına', color='lightblue')
        self.test_btn.on_clicked(self.start_connection_test)
        
        # Çift görünüm butonu
        self.dual_view_ax = self.fig.add_axes([0.45, 0.11, 0.3, 0.03])
        self.dual_view_btn = Button(self.dual_view_ax, 'Çift Görünüm Aç/Kapat', color='lightgray')
        self.dual_view_btn.on_clicked(self.toggle_dual_view)
        self.dual_view = False
        
        # Çift görünüm için ikinci eksen
        self.ax2 = self.fig.add_axes([0.55, 0.25, 0.4, 0.4])
        self.im2 = self.ax2.imshow(np.zeros((360, 640, 3), dtype=np.uint8))
        self.ax2.axis('off')
        self.ax2.set_title('İkinci Kamera', fontsize=10)
        self.ax2.set_visible(False)
        
        # Pencere kapatma olayı
        self.fig.canvas.mpl_connect('close_event', self.on_close)

    def switch_camera(self, label):
        """Aktif kamerayı değiştir"""
        for i, cam in enumerate(self.cameras):
            if cam["name"] == label:
                self.current_cam = i
                self.update_display()
                break

    def toggle_dual_view(self, event):
        """Çift görünümü aç/kapat"""
        self.dual_view = not self.dual_view
        self.ax2.set_visible(self.dual_view)
        self.update_info(f"Çift görünüm {'açıldı' if self.dual_view else 'kapandı'}")
        self.fig.canvas.draw_idle()

    def update_display(self):
        """Görüntüyü güncelle"""
        if self.is_running:
            self.stop_stream()
            self.start_stream()
        self.update_info(f"Aktif kamera: {self.cameras[self.current_cam]['name']}")

    def change_url(self, event):
        """Seçili kameranın URL'sini değiştir"""
        root = tk.Tk()
        root.withdraw()
        try:
            current_url = self.cameras[self.current_cam]["url"]
            new_url = simpledialog.askstring(
                "RTSP URL Değiştir",
                f"{self.cameras[self.current_cam]['name']} için yeni URL:",
                initialvalue=current_url or "rtsp://"
            )
            if new_url:
                self.cameras[self.current_cam]["url"] = new_url.strip()
                self.update_info(f"{self.cameras[self.current_cam]['name']} URL güncellendi")
        finally:
            try:
                root.destroy()
            except:
                pass

    def update_info(self, message):
        """Bilgi panelini güncelle"""
        self.info_text.set_text(f"{self.cameras[self.current_cam]['name']}\n{message}")
        self.fig.canvas.draw_idle()

    def start_connection_test(self, event):
        """Bağlantı testini başlat"""
        if not self.cameras[self.current_cam]["url"]:
            self.update_info("Hata: Önce bir URL girin!")
            return
            
        self.test_btn.label.set_text("Test Ediliyor...")
        self.fig.canvas.draw_idle()
        
        test_thread = threading.Thread(target=self.test_connection, daemon=True)
        test_thread.start()

    def test_connection(self):
        """Kamera bağlantısını test et"""
        url = self.cameras[self.current_cam]["url"]
        try:
            self.update_info(f"{self.cameras[self.current_cam]['name']} bağlantı testi...")
            
            test_process = (
                ffmpeg
                .input(url, rtsp_transport='tcp', timeout=5000000)
                .output('null', format='null')
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            
            time.sleep(3)
            _, stderr = test_process.communicate()
            
            if test_process.returncode == 0:
                self.update_info(f"{self.cameras[self.current_cam]['name']} bağlantı başarılı!")
            else:
                error_msg = stderr.decode('utf-8')[:200] + "..." if len(stderr) > 200 else stderr.decode('utf-8')
                self.update_info(f"{self.cameras[self.current_cam]['name']} bağlantı hatası:\n{error_msg}")
                
        except Exception as e:
            self.update_info(f"{self.cameras[self.current_cam]['name']} test hatası: {str(e)}")
        finally:
            self.test_btn.label.set_text("Bağlantıyı Sına")
            self.fig.canvas.draw_idle()

    def toggle_stream(self, event):
        """Akışı başlat/durdur"""
        if not self.is_running:
            self.start_stream()
        else:
            self.stop_stream()

    def start_stream(self):
        """Akışı başlat"""
        if not self.cameras[self.current_cam]["url"]:
            self.update_info("Hata: Önce bir URL girin!")
            return
            
        self.is_running = True
        self.btn.label.set_text("Durdur")
        self.update_info(f"{self.cameras[self.current_cam]['name']} bağlanıyor...")
        
        try:
            # Ana kamera için akış
            self.cameras[self.current_cam]["process"] = (
                ffmpeg
                .input(self.cameras[self.current_cam]["url"], rtsp_transport='tcp', timeout=5000000)
                .output('pipe:', format='rawvideo', pix_fmt='rgb24', s='1280x720')
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            
            # Çift görünüm aktifse ikinci kamera için akış
            if self.dual_view:
                other_cam = 1 if self.current_cam == 0 else 0
                if self.cameras[other_cam]["url"]:
                    self.cameras[other_cam]["process"] = (
                        ffmpeg
                        .input(self.cameras[other_cam]["url"], rtsp_transport='tcp', timeout=5000000)
                        .output('pipe:', format='rawvideo', pix_fmt='rgb24', s='640x360')
                        .run_async(pipe_stdout=True, pipe_stderr=True)
                    )
            
            self.stream_thread = threading.Thread(target=self.update_frame, daemon=True)
            self.stream_thread.start()
            
        except Exception as e:
            self.update_info(f"Başlatma hatası: {str(e)}")
            self.is_running = False
            self.btn.label.set_text("Başlat")

    def update_frame(self):
        """Görüntüyü sürekli güncelle"""
        width, height = 1280, 720
        small_width, small_height = 640, 360
        
        while self.is_running:
            try:
                # Ana kameradan görüntü al
                in_bytes = self.cameras[self.current_cam]["process"].stdout.read(width * height * 3)
                if not in_bytes:
                    self.update_info("Ana kameradan veri alınamıyor")
                    break
                    
                frame = np.frombuffer(in_bytes, np.uint8).reshape((height, width, 3))
                self.im.set_data(frame)
                self.ax.set_title(self.cameras[self.current_cam]["name"], fontsize=12)
                
                # Çift görünüm aktifse ikinci kameradan görüntü al
                if self.dual_view:
                    other_cam = 1 if self.current_cam == 0 else 0
                    if self.cameras[other_cam]["process"]:
                        try:
                            small_bytes = self.cameras[other_cam]["process"].stdout.read(small_width * small_height * 3)
                            if small_bytes:
                                small_frame = np.frombuffer(small_bytes, np.uint8).reshape((small_height, small_width, 3))
                                self.im2.set_data(small_frame)
                                self.ax2.set_title(self.cameras[other_cam]["name"], fontsize=10)
                        except:
                            pass
                
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                
            except Exception as e:
                if self.is_running:
                    self.update_info(f"Görüntü alma hatası: {str(e)}")
                break

    def stop_stream(self):
        """Akışı durdur"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.btn.label.set_text("Başlat")
        self.update_info("Akış durduruldu")
        
        for cam in self.cameras:
            if cam["process"]:
                try:
                    cam["process"].terminate()
                    cam["process"].wait(timeout=2)
                    cam["process"] = None
                except:
                    pass

    def on_close(self, event):
        """Pencere kapatıldığında kaynakları serbest bırak"""
        self.stop_stream()

    def run(self):
        """Uygulamayı çalıştır"""
        try:
            plt.show(block=True)
        except KeyboardInterrupt:
            self.stop_stream()

if __name__ == "__main__":
    viewer = RTSPViewer()
    viewer.run()