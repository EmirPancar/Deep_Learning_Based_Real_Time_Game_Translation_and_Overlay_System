import dxcam
import time
import os
import torch
import tkinter as tk
import ctypes
import keyboard
import difflib

# ================= UYARILARI TAMAMEN SUSTUR =================
import logging
logging.disable(logging.WARNING) 
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from paddleocr import PaddleOCR
from transformers import MarianMTModel, MarianTokenizer

print("1/2: OCR (Yazı Okuma) modeli yükleniyor...")
ocr = PaddleOCR(lang='en', use_gpu=True, show_log=False, use_angle_cls=False) 

# ================= ÖZEL MODELİN YÜKLENMESİ =================
print("2/2: ÖZEL EĞİTİLMİŞ Çeviri Motorunuz yükleniyor...")
# İndirdiğin klasörün adı. Aynı klasörde olduğu için başına "./" koyuyoruz.
model_name = "./opus_mt_game_finetuned_v3" 

# Eğer henüz modeli indirmediysen veya test etmek istersen üstteki satırı silip alttakini kullanabilirsin:
# model_name = "Helsinki-NLP/opus-mt-tc-big-en-tr"

tokenizer = MarianTokenizer.from_pretrained(model_name)
ceviri_modeli = MarianMTModel.from_pretrained(model_name, torch_dtype=torch.float16).to("cuda")

camera = dxcam.create(output_idx=0)
ceviri_hafizasi = {}

OYUN_SOZLUGU = {
    "SETTINGS": "AYARLAR", "CREDITS": "YAPIMCILAR", "QUIT TO DESKTOP": "MASAÜSTÜNE DÖN",
    "BEGIN THE GAME": "OYUNA BAŞLA", "NEW GAME": "YENİ OYUN", "LOAD GAME": "OYUN YÜKLE",
    "SAVE GAME": "OYUNU KAYDET", "OPTIONS": "SEÇENEKLER", "BACK": "GERİ",
    "EXIT": "ÇIKIŞ", "CONTINUE": "DEVAM ET", "PLAY": "OYNA", "QUIT": "ÇIKIŞ"
}

def ceviri_yap(ingilizce_metin):
    temiz_metin = ingilizce_metin.strip()
    metin_buyuk = temiz_metin.upper()
    
    if metin_buyuk in OYUN_SOZLUGU:
        return OYUN_SOZLUGU[metin_buyuk]
        
    if temiz_metin in ceviri_hafizasi:
        return ceviri_hafizasi[temiz_metin]
    
    try:
        with torch.no_grad():
            inputs = tokenizer(temiz_metin, return_tensors="pt", padding=True).to("cuda")
            translated_tokens = ceviri_modeli.generate(
                **inputs, max_length=100, num_beams=1, do_sample=False
            )
            turkce_metin = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
            
        ceviri_hafizasi[temiz_metin] = turkce_metin
        return turkce_metin
    except Exception:
        return temiz_metin

# ================= TİTREME/SABİTLEME SİSTEMİ =================
class SubtitleStabilizer:
    def __init__(self):
        self.aktif_metinler =[]

    def kararli_ceviri_getir(self, yeni_ingilizce_metin):
        su_an = time.time()
        self.aktif_metinler =[t for t in self.aktif_metinler if su_an - t['zaman'] < 1.5]

        for t in self.aktif_metinler:
            benzerlik = difflib.SequenceMatcher(None, yeni_ingilizce_metin.lower(), t['orijinal'].lower()).ratio()
            if benzerlik > 0.75:
                t['zaman'] = su_an 
                return t['ceviri']
        
        yeni_ceviri = ceviri_yap(yeni_ingilizce_metin)
        self.aktif_metinler.append({'orijinal': yeni_ingilizce_metin, 'ceviri': yeni_ceviri, 'zaman': su_an})
        return yeni_ceviri

stabilizer = SubtitleStabilizer()

def metinleri_birlestir(ham_sonuclar, ekran_yuksekligi, ekran_genisligi):
    if not ham_sonuclar or not ham_sonuclar[0]:
        return[]
        
    satirlar = ham_sonuclar[0]
    satirlar = sorted(satirlar, key=lambda x: min(p[1] for p in x[0]))
    birlestirilmis_bloklar =[]
    
    for satir in satirlar:
        if not satir or len(satir) < 2:
            continue
            
        koordinatlar = satir[0]
        metin = satir[1][0].strip()
        guven = satir[1][1]
        
        min_y = int(min(p[1] for p in koordinatlar))
        max_y = int(max(p[1] for p in koordinatlar))
        min_x = int(min(p[0] for p in koordinatlar))
        max_x = int(max(p[0] for p in koordinatlar))
        yukseklik = max_y - min_y
        
        # ================= MERKEZ FİLTRESİ =================
        metin_merkez_x = (min_x + max_x) / 2
        ekran_merkez_x = ekran_genisligi / 2
        
        # Eşya yazıları vb. için sağdan/soldan merkeze %25'ten uzaksa yoksay!
        if abs(metin_merkez_x - ekran_merkez_x) > (ekran_genisligi * 0.25):
            continue
        
        if guven < 0.85 or len(metin) < 3 or yukseklik < 12 or yukseklik > int(ekran_yuksekligi * 0.15):
            continue
            
        if not birlestirilmis_bloklar:
            birlestirilmis_bloklar.append({
                "text": metin, "min_x": min_x, "max_x": max_x, 
                "min_y": min_y, "max_y": max_y, "yukseklik": yukseklik
            })
        else:
            son_blok = birlestirilmis_bloklar[-1]
            dikey_bosluk = min_y - son_blok["max_y"]
            x_kesisimi = min(son_blok["max_x"], max_x) - max(son_blok["min_x"], min_x)
            tolerans = son_blok["yukseklik"] * 0.4
            
            if -yukseklik <= dikey_bosluk <= tolerans and x_kesisimi > 0:
                son_blok["text"] += " " + metin 
                son_blok["min_x"] = min(son_blok["min_x"], min_x) 
                son_blok["max_x"] = max(son_blok["max_x"], max_x)
                son_blok["max_y"] = max(son_blok["max_y"], max_y)
            else:
                birlestirilmis_bloklar.append({
                    "text": metin, "min_x": min_x, "max_x": max_x,
                    "min_y": min_y, "max_y": max_y, "yukseklik": yukseklik
                })
                
    return birlestirilmis_bloklar

# ================= TKINTER ARAYÜZÜ =================
root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "black")
root.config(bg="black")

root.update_idletasks()
hwnd = int(root.wm_frame(), 16)

style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)

try:
    if not ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 17):
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 1)
except Exception:
    pass

canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

print("\nSistem Hazır! Kendi eğittiğiniz model aktif.")
print("Uygulamadan çıkmak için 'CTRL + Q' tuşlarına basın.\n")

def game_loop():
    if keyboard.is_pressed('ctrl+q'):
        print("Kapatılıyor...")
        root.destroy()
        return

    try:
        frame = camera.grab()
        
        if frame is not None:
            h, w, _ = frame.shape
            kesik_y_baslangic = int(h * 0.75)
            altyazi_bolgesi = frame[kesik_y_baslangic:h, 0:w]
            
            ham_sonuclar = ocr.ocr(altyazi_bolgesi)
            bloklar = metinleri_birlestir(ham_sonuclar, h, w)
            
            canvas.delete("all")
            
            for blok in bloklar:
                ingilizce_tam_metin = blok["text"]
                turkce_ceviri = stabilizer.kararli_ceviri_getir(ingilizce_tam_metin)
                
                if turkce_ceviri:
                    gercek_min_y = blok["min_y"] + kesik_y_baslangic
                    gercek_max_y = blok["max_y"] + kesik_y_baslangic
                    gercek_min_x = blok["min_x"]
                    gercek_max_x = blok["max_x"]
                    
                    # Orijinal Yazının Maksimum Genişliği (Taşmaması için)
                    orijinal_genislik = gercek_max_x - gercek_min_x
                    maksimum_genislik = max(orijinal_genislik, 50)
                    
                    text_id = canvas.create_text(
                        gercek_min_x, gercek_min_y,
                        text=turkce_ceviri, fill="yellow", font=("Arial", 16, "bold"),
                        anchor="nw", width=maksimum_genislik 
                    )
                    
                    x1, y1, x2, y2 = canvas.bbox(text_id)
                    padding = 6
                    
                    kutu_sol = min(x1, gercek_min_x)
                    kutu_sag = max(x2, gercek_max_x)
                    kutu_ust = min(y1, gercek_min_y)
                    kutu_alt = max(y2, gercek_max_y)
                    
                    rect_id = canvas.create_rectangle(
                        kutu_sol - padding, kutu_ust - padding,
                        kutu_sag + padding, kutu_alt + padding,
                        fill="#0f0f0f", outline="#0f0f0f"
                    )
                    
                    canvas.tag_lower(rect_id, text_id)
                    
    except Exception as e:
        pass

    root.after(10, game_loop)

root.after(50, game_loop)

try:
    root.mainloop()
except KeyboardInterrupt:
    print("Konsoldan çıkış yapıldı.")
except Exception as e:
    pass