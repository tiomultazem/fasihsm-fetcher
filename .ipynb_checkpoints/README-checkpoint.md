# FasihSM Fetcher

**FasihSM Fetcher** adalah tools berbasis Python yang dirancang untuk mengambil data dari platform Fasih-SM dan menyimpannya ke dalam basis data satuan kerja. Tools ini memadukan otomasi browser untuk autentikasi dan request API untuk pengambilan data skala besar secara cepat.

---

## 🚀 Fitur Utama

- **Hybrid Authentication**: Menggunakan Selenium untuk menangani alur login SSO BPS yang kompleks, lalu memindahkan sesi autentikasi ke library Requests.
- **Metadata Extractor**: Mengambil informasi detail metadata survei, periode aktif, hingga pemetaan level wilayah kerja.
- **Petugas Data Collector**: Menarik daftar petugas (Pencacah/Pengawas) secara massal lengkap dengan ID dan wilayah tugas dalam format tabel (Pandas DataFrame).
- **Dynamic Token Handling**: Penanganan otomatis terhadap CSRF Token (`X-XSRF-TOKEN`) dan Bearer Token dari LocalStorage.

---

## 🛠️ Persyaratan Sistem

- Python 3.8+
- Google Chrome (versi terbaru disarankan)
- Dependencies:

```bash
pip install selenium requests pandas webdriver-manager
```

---

## 📦 Instalasi

```bash
git clone https://github.com/username/fasihsm-fetcher.git
cd fasihsm-fetcher
pip install -r requirements.txt
```

---

## 🖥️ Cara Penggunaan

1. Buka file script utama.
2. Sesuaikan variabel `USERNAME` dan `PASSWORD` dengan akun SSO BPS Anda.
3. Jalankan script per bagian:
   - **Bagian 1-2**: Import dan proses login.
   - **Bagian 3**: Ambil daftar survei → `surveys`.
   - **Bagian 4**: Ambil metadata survei → `settings`.
   - **Bagian 5**: Ambil data petugas → `df_petugas`.
4. Ekspor data:

```python
df_petugas.to_excel("daftar_petugas.xlsx", index=False)
```

---

## ⚠️ Disclaimer

Tools ini dibuat untuk tujuan efisiensi pengolahan data internal di lingkungan Badan Pusat Statistik. Pengguna bertanggung jawab penuh atas penggunaan kredensial, keamanan data, dan kepatuhan terhadap kebijakan internal instansi.

---

**Copyright © 2026 Gilang Wahyu Prasetyo (BPS Kabupaten Tabalong)**

Licensed under the MIT License.
