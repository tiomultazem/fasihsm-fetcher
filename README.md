# FasihSM Fetcher

*FasihSM Fetcher* adalah tools berbasis Python yang dirancang untuk mengambil data dari platform Fasih-SM dan menyimpannya ke dalam basis data satuan kerja. Tools ini memadukan sinkronisasi browser kustom (melalui ekstensi Chrome) untuk melewati perlindungan WAF F5 BIG-IP dan request API paralel untuk pengambilan data skala besar secara cepat.

---

## 🚀 Fitur Utama

- **Sinkronisasi Sesi Instan**: Lewati validasi Keycloak/WAF secara otomatis dengan sinkronisasi cookie langsung sekali klik menggunakan ekstensi Chrome kustom.
- **Ekstrak Data Komprehensif**: Ambil metadata survei, data petugas berdasar role, dan data sampel berdasar status assignment.
- **Bulk Approve/Reject**: Lakukan persetujuan (*approve*) atau penolakan (*reject*) massal ribuan sampel otomatis hanya dengan satu tombol.
- **Optimasi Anti-Timeout & WAF**: Pembagian kueri otomatis (smart-split) dan optimasi ukuran halaman (*direct length* ke 250) untuk mencegah eror 504 Gateway Time-out dan pemblokiran bot WAF.

---

## 🆕 Fitur Terbaru

- **Ekstensi Chrome Fasih Session Sync (v8.0)**:
  - Mengambil cookie sesi terpartisi (CHIPS) dan cookie tingkat domain apex (`SESSION`, `JSESSIONID`) yang dilindungi flag `HttpOnly` untuk otentikasi aman tanpa copas cURL manual.
- **Deteksi WAF & Otomatisasi Halt**:
  - Sistem mendeteksi otomatis jika request diblokir oleh WAF (Tantangan JavaScript) dan meminta pengguna menyegarkan sesi via ekstensi sebelum melanjutkan agar data tidak korup.
- **Persentase Progres Akurat**:
  - Progres unduhan kini dihitung berdasarkan jumlah data terambil dibagi estimasi total data riil (bukan rasio bagian/bucket selesai).

---

## 🛠️ Persyaratan Sistem

- Python 3.11+
- Brave / Google Chrome Browser (untuk memasang ekstensi lokal)
- Dependencies: silakan cek `requirements.txt`

---

## 📦 Instalasi

```bash
git clone https://github.com/tiomultazem/fasihsm-fetcher.git
cd fasihsm-fetcher
pip install -r requirements.txt
```

---

## 🖥️ Cara Penggunaan

### 1. Jalankan Aplikasi
Jalankan Flask server lokal di direktori proyek:
```bash
python src/app.py
```
Akses aplikasi di browser Anda di: `http://localhost:5000/fasihsm-fetcher`

### 2. Pemasangan Ekstensi Browser (Penting!)
1. Buka tab baru di browser dan akses `brave://extensions/` atau `chrome://extensions/`.
2. Aktifkan **Developer mode** (Mode pengembang) di pojok kanan atas.
3. Klik tombol **Load unpacked** (Muat ekstensi tidak dikemas) di pojok kiri atas.
4. Pilih folder `extension` yang berada di dalam folder proyek ini.
5. Ekstensi **Fasih Session Sync** kini aktif dan siap digunakan.

### 3. Cara Menghubungkan Sesi
1. Buka BPS Portal / Fasih-SM (`https://fasih-sm.bps.go.id/`) di browser Anda dan pastikan sudah login.
2. Klik ikon ekstensi **Fasih Session Sync** di toolbar browser Anda.
3. Tunggu hingga muncul lencana hijau **OK** di ikon ekstensi.
4. Buka kembali halaman fetcher lokal Anda (`http://localhost:5000/fasihsm-fetcher`) dan segarkan/refresh halaman. Sesi kini telah terhubung!

---

## ⚠️ Disclaimer

Tools ini dibuat untuk tujuan efisiensi pengolahan data internal di lingkungan Badan Pusat Statistik. Pengguna bertanggung jawab penuh atas keamanan data, hak akses VPN, dan kepatuhan terhadap kebijakan internal instansi.

---

*Copyright © 2026 Gilang Wahyu Prasetyo (BPS Kabupaten Tabalong)*
