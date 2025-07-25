import ffmpeg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import threading
import time
import tkinter as tk
from tkinter import simpledialog

class RTSPViewer:
    def __init__(self):
        self.is_running = False
        self.is_testing = False
        self.process = None
        self.rtsp_url = ""
        self.fig = None
        self.setup_ui()
        
    def setup_ui(self):
        self.fig = plt.figure(figsize=(14, 8))
        self.fig.canvas.manager.set_window_title('RTSP Görüntüleyici Pro')
        
        # Hata Mesaj Paneli (üst kısım, daha geniş)
        self.info_ax = self.fig.add_axes([0.05, 0.9, 0.9, 0.08])  # X, Y, Genişlik, Yükseklik
        self.info_ax.axis('off')
        self.info_text = self.info_ax.text(
            0.01, 0.5, 
            "RTSP Görüntüleyici Hazır - Lütfen URL girin ve Başlat'a basın",
            fontsize=10,
            verticalalignment='center',
            bbox=dict(facecolor='#f0f0f0', alpha=0.8, edgecolor='#cccccc')
        )
        
        # Video Görüntü Alanı (hata panelinin altında)
        self.ax = self.fig.add_axes([0.1, 0.15, 0.8, 0.7])  # Yükseklik ayarlandı
        self.im = self.ax.imshow(np.zeros((720, 1280, 3), dtype=np.uint8))
        self.ax.axis('off')
        self.ax.set_title('Kamera Görüntüsü', pad=10)
        
        # Kontrol Butonları (en alt kısım)
        self.url_btn_ax = self.fig.add_axes([0.25, 0.05, 0.2, 0.05])
        self.url_btn = Button(self.url_btn_ax, 'URL Değiştir', color='lightyellow')
        
        self.btn_ax = self.fig.add_axes([0.46, 0.05, 0.2, 0.05])
        self.btn = Button(self.btn_ax, 'Başlat', color='lightgreen')
        
        self.test_ax = self.fig.add_axes([0.67, 0.05, 0.2, 0.05])
        self.test_btn = Button(self.test_ax, 'Bağlantıyı Sına', color='lightblue')
        
        # Kapatma Butonu (sağ üst)
        self.close_ax = self.fig.add_axes([0.92, 0.9, 0.06, 0.06])
        self.close_ax.axis('off')
        self.close_btn = Button(self.close_ax, ' KAPAT ', color='red')
        
        # Etkileşimler
        self.url_btn.on_clicked(self.change_url)
        self.btn.on_clicked(self.toggle_stream)
        self.test_btn.on_clicked(self.start_connection_test)
        self.close_btn.on_clicked(self.close_app)
        
        # Pencere kapatma olayı
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        
    def close_app(self, event):
        self.stop_stream()
        plt.close(self.fig)
        
    def on_close(self, event):
        self.stop_stream()
        
    def change_url(self, event):
        if self.is_running:
            self.stop_stream()
        
        root = tk.Tk()
        root.withdraw()
        try:
            new_url = simpledialog.askstring(
                "RTSP URL Değiştir", 
                "Yeni RTSP URL girin:", 
                initialvalue=self.rtsp_url or "rtsp://"
            )
            if new_url:
                self.rtsp_url = new_url.strip()
                self.update_info(f"URL başarıyla güncellendi: {self.rtsp_url}")
        finally:
            try:
                root.destroy()
            except:
                pass
        
    def update_info(self, message):
        """Hata mesajlarını güncelle (artık üst panelde)"""
        self.info_text.set_text(message)
        
        # Mesaj türüne göre renk ayarla
        if "Hata:" in message or "başarısız" in message.lower():
            self.info_text.set_color('red')
        elif "başarılı" in message.lower() or "bağlandı" in message.lower():
            self.info_text.set_color('green')
        else:
            self.info_text.set_color('black')
            
        self.fig.canvas.draw_idle()
        
    def toggle_stream(self, event):
        if not self.is_running:
            self.start_stream()
        else:
            self.stop_stream()
    
    def start_connection_test(self, event):
        if self.is_testing:
            return
            
        if not self.rtsp_url:
            self.update_info("Hata: Önce bir URL girin!")
            return
            
        if self.is_running:
            self.stop_stream()
            
        self.is_testing = True
        self.test_btn.label.set_text("Test Ediliyor...")
        self.fig.canvas.draw_idle()
        
        test_thread = threading.Thread(target=self.test_connection, daemon=True)
        test_thread.start()
    
    def test_connection(self):
        try:
            self.update_info("Kamera bağlantısı test ediliyor...")
            
            test_process = (
                ffmpeg
                .input(self.rtsp_url, rtsp_transport='tcp', timeout=5000000)
                .output('null', format='null')
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            
            time.sleep(3)  # Test süresi
            _, stderr = test_process.communicate()
            
            if test_process.returncode == 0:
                self.update_info("Bağlantı testi başarılı! Kamera erişilebilir.")
            else:
                error_msg = stderr.decode('utf-8')[:150]  # Uzun hataları kısalt
                self.update_info(f"Bağlantı hatası: {error_msg}")
                
        except Exception as e:
            self.update_info(f"Test sırasında hata oluştu: {str(e)}")
        finally:
            self.is_testing = False
            self.test_btn.label.set_text("Bağlantıyı Sına")
            self.fig.canvas.draw_idle()
    
    def start_stream(self):
        if not self.rtsp_url:
            self.update_info("Hata: Lütfen önce bir RTSP URL girin!")
            return
            
        if self.is_running:
            return
            
        self.is_running = True
        self.btn.label.set_text("Durdur")
        self.update_info("Kameraya bağlanıyor...")
        
        try:
            self.process = (
                ffmpeg
                .input(self.rtsp_url, rtsp_transport='tcp', timeout=5000000)
                .output('pipe:', format='rawvideo', pix_fmt='rgb24', s='1280x720')
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            
            self.stream_thread = threading.Thread(target=self.update_frame, daemon=True)
            self.stream_thread.start()
            
        except Exception as e:
            self.update_info(f"Bağlantı hatası: {str(e)}")
            self.is_running = False
            self.btn.label.set_text("Başlat")
    
    def update_frame(self):
        width, height = 1280, 720
        frame_count = 0
        start_time = time.time()
        
        while self.is_running:
            try:
                in_bytes = self.process.stdout.read(width * height * 3)
                if not in_bytes:
                    self.update_info("Uyarı: Akıştan veri alınamıyor. Bağlantı kesildi.")
                    break
                    
                frame = np.frombuffer(in_bytes, np.uint8).reshape((height, width, 3))
                self.im.set_data(frame)
                
                # FPS hesaplama ve gösterme
                frame_count += 1
                if frame_count % 10 == 0:
                    fps = 10 / (time.time() - start_time)
                    start_time = time.time()
                    self.ax.set_title(f'Canlı Görüntü - {fps:.1f} FPS')
                
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                
            except Exception as e:
                if self.is_running:
                    self.update_info(f"Görüntü aktarım hatası: {str(e)}")
                break
    
    def stop_stream(self):
        if not self.is_running:
            return
            
        self.is_running = False
        self.btn.label.set_text("Başlat")
        self.update_info("Akış durduruldu. Yeni bağlantı için Başlat'a basın.")
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                pass
    
    def run(self):
        try:
            plt.show(block=True)
        except KeyboardInterrupt:
            self.stop_stream()

if __name__ == "__main__":
    viewer = RTSPViewer()
    viewer.run()