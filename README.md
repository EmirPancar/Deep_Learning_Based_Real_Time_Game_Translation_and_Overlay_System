# 🎮 Derin Öğrenme Tabanlı Gerçek Zamanlı Oyun Çeviri ve Overlay Sistemi

> Oyunlardaki yabancı dildeki altyazıları OCR ile anlık olarak okuyup, özel eğitilmiş (fine-tuned) yerel NLP modeliyle çeviren ve ekrana tıklanabilir şeffaf bir katman olarak basan düşük gecikmeli masaüstü uygulaması.

## ✨ Öne Çıkan Özellikler

- **Yerel ve Özelleştirilmiş Çeviri:** Hugging Face üzerinden fine-tune yapılmış özel `MarianMT` modeli sayesinde sıfır API gecikmesi ve oyuna özgü doğru çeviriler.
- **Yüksek Hızlı Ekran Yakalama:** Standart kütüphaneler yerine DirectX tabanlı `DXcam` kullanılarak FPS kaybı yaşanmadan ekran yakalama.
- **Akıllı Metin Sabitleme:** OCR hatalarından kaynaklanan ekran titremelerini önlemek için `difflib` tabanlı benzerlik algoritması (SubtitleStabilizer).
- **Uzamsal Filtreleme :** Ekranın köşelerindeki gereksiz eşya/menü yazılarını yoksayarak sadece merkezdeki diyalog altyazılarını algılayan uzamsal koordinat mantığı.
- **Şeffaf Arayüz:** Windows API (`ctypes`) kullanılarak tasarlanmış, tıklamaları arkadaki oyuna ileten ve oyun deneyimini hiçbir şekilde bölmeyen overlay UI.
- **Önbellek Optimizasyonu:** Aynı kelime ve cümlelerin tekrar çevrilmesini engelleyerek GPU kullanımını minimize eden anlık hafıza sistemi.

## 🛠️ Kullanılan Teknolojiler

- **Dil:** Python 3.8+
- **Doğal Dil İşleme (NLP):** Hugging Face Transformers, PyTorch (CUDA)
- **OCR & Ekran Yakalama:** PaddleOCR, DXcam
- **Arayüz (GUI) & İşletim Sistemi API:** Tkinter, ctypes (Win32 API)

## 📂 Sistem Nasıl Çalışır?

1. **Yakalama:** `DXcam`, oyun ekranının sadece alt %25'lik kısmını (altyazı bölgesini) yakalar.
2. **Karakter Tanıma (OCR):** `PaddleOCR`, bu bölgedeki yazıları algılar. Birbirine yakın kelime grupları (bounding boxes) akıllı bir algoritma ile tek bir satır/paragraf haline getirilir.
3. **Filtreleme:** Merkezden uzak veya güven skoru %85'in altında olan yazılar elenir.
4. **Çeviri:** Metin önce oyun sözlüğünde aranır. Yoksa GPU üzerindeki özel `MarianMT` modeline gönderilir.
5. **Gösterim:** Çevrilen metin, şeffaf Tkinter Canvas'ı üzerinden doğrudan oyun ekranının üzerine arkaplanı karartılmış vurgulu yazılar halinde yansıtılır.

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleyin
Nvidia GPU ve CUDA yüklü olduğundan emin olduktan sonra aşağıdaki komutları çalıştırın:

```bash
# PyTorch GPU versiyonunu yükleyin (Sisteminizdeki CUDA sürümüne göre güncelleyebilirsiniz)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Gerekli diğer kütüphaneleri yükleyin
pip install dxcam paddleocr paddlepaddle-gpu transformers keyboard
```

### 2. Çeviri Modelini Ayarlama
Proje dizininde `opus_mt_game_finetuned_v3` adında kendi eğittiğiniz model klasörü bulunmalıdır. *(Eğer standart bir model denemek isterseniz kod içerisindeki `model_name = "Helsinki-NLP/opus-mt-tc-big-en-tr"` satırını aktif edebilirsiniz).*

> **Not:** Model ağırlıkları (safetensors vb.) büyük boyutlu olduğu için `.gitignore` dosyasına eklenmiş ve repoya yüklenmemiştir. Kendi modelinizi eğitip klasöre dahil etmelisiniz.

### 3. Uygulamayı Başlatma
```bash
python main.py
```
*Uygulama tam ekran ve şeffaf olarak başlar. Kapatmak için klavyenizden `CTRL + Q` kombinasyonunu kullanabilirsiniz.*
