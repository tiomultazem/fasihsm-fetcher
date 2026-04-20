\# FasihSM Scraper



\*\*FasihSM Scraper\*\* adalah tools berbasis Python yang dirancang untuk mengulik (scraping) data dari platform Fasih-SM dan menyimpannya ke dalam basis data satuan kerja. Tools ini memadukan kekuatan otomasi browser untuk autentikasi dan efisiensi API request untuk pengambilan data skala besar secara cepat.



\## 🚀 Fitur Utama



\*   \*\*Hybrid Authentication\*\*: Menggunakan Selenium untuk menangani alur login SSO BPS yang kompleks, lalu memindahkan sesi autentikasi ke library Requests.

\*   \*\*Metadata Extractor\*\*: Mengambil informasi detail metadata survei, periode aktif, hingga pemetaan level wilayah kerja.

\*   \*\*Petugas Scraper\*\*: Menarik daftar petugas (Pencacah/Pengawas) secara massal lengkap dengan ID dan wilayah tugas dalam format tabel (Pandas DataFrame).

\*   \*\*Smart Security Bypass\*\*: Penanganan otomatis terhadap proteksi CSRF Token (`X-XSRF-TOKEN`) dan Bearer Auth yang dinamis dari LocalStorage.



\## 🛠️ Persyaratan Sistem



\*   \*\*Python 3.8+\*\*

\*   \*\*Google Chrome Browser\*\* (Versi terbaru disarankan)

\*   \*\*Dependencies\*\*: 

&#x20;   ```bash

&#x20;   pip install selenium requests pandas webdriver-manager

&#x20;   ```



\## 📦 Instalasi



1\.  Clone repositori ini:

&#x20;   ```bash

&#x20;   git clone \[https://github.com/username/fasihsm-scraper.git](https://github.com/username/fasihsm-scraper.git)

&#x20;   cd fasihsm-scraper

&#x20;   ```

2\.  Install library pendukung:

&#x20;   ```bash

&#x20;   pip install -r requirements.txt

&#x20;   ```



\## 🖥️ Cara Penggunaan



1\.  Buka file script utama.

2\.  Sesuaikan variabel `USERNAME` serta `PASSWORD` dengan akun SSO BPS Anda.

3\.  Jalankan rangkaian script per bagian (chunk):

&#x20;   \*   \*\*Bagian 1-2\*\*: Import dan Prosedur Login.

&#x20;   \*   \*\*Bagian 3\*\*: Penarikan Daftar Survei ke variabel `surveys`.

&#x20;   \*   \*\*Bagian 4\*\*: Penarikan Metadata detail survei ke variabel `settings`.

&#x20;   \*   \*\*Bagian 5\*\*: Penarikan Daftar Petugas ke variabel `df\_petugas`.

4\.  Data dapat diekspor langsung ke Excel:

&#x20;   ```python

&#x20;   df\_petugas.to\_excel("daftar\_petugas.xlsx", index=False)

&#x20;   ```



\## ⚠️ Disclaimer



Tools ini dibuat murni untuk tujuan efisiensi pengolahan data internal di lingkungan Badan Pusat Statistik (khususnya bagi Pranata Komputer). Pengguna bertanggung jawab penuh atas penggunaan kredensial, kerahasiaan data, dan kepatuhan terhadap kebijakan internal BPS terkait keamanan informasi.



\---



\*\*Copyright © 2026 Gilang Wahyu Prasetyo (BPS Kabupaten Tabalong)\*\*



Licensed under the \[MIT License](LICENSE).

