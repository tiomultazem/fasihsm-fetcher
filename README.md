# FasihSM Fetcher

**FasihSM Fetcher** adalah tools internal BPS untuk mempercepat pengelolaan data survei dari platform [Fasih-SM](https://fasih-sm.bps.go.id) — langsung dari browser, tanpa perlu copas manual atau buka portal satu-satu.

---

## Fitur Utama

- **Sinkronisasi Sesi Instan**: Hubungkan sesi Fasih-SM aktif dari browser ke aplikasi hanya dengan satu klik menggunakan ekstensi **Fasih Session Sync**.
- **Daftar Survei**: Lihat seluruh survei pencacahan yang tersedia dan pilih periode yang ingin dikerjakan.
- **Data Petugas per Role**: Tampilkan daftar petugas (pencacah, pengawas, dll.) beserta wilayah penugasannya.
- **Rekap Lapangan Petugas Real-Time**: Unduh rekap progres lapangan per petugas — berisi jumlah dokumen Open, Draft, Submitted, Approved, Rejected, dan Total — langsung dari server.
- **Fetch Sampel dengan Progres Real-Time**: Ambil data sampel berdasarkan filter status, wilayah, atau pencacah dengan streaming langsung; progress bar menampilkan persentase dan estimasi waktu selesai.
- **Unduh Detail Sampel**: Ekspor detail lengkap sampel ke CSV dengan progres unduhan real-time.
- **Snapshot Preview CSV**: Simpan dan muat ulang tampilan tabel saat ini sebagai file CSV tanpa perlu fetch ulang dari server.
- **Bulk Approve / Reject**: Setujui atau tolak ribuan sampel sekaligus hanya dengan satu klik, dengan streaming progres real-time dan tombol Stop kapan saja.
- **Ekspor CSV Petugas**: Unduh daftar petugas — bisa per role yang sedang ditampilkan atau seluruh role sekaligus.
- **Filter Cerdas (Smart-Split)**: Sistem secara otomatis memecah kueri besar agar tidak kena timeout 504 dari server.
- **Dark / Light Mode**: Tema tersimpan otomatis dan berlaku di seluruh sesi.
- **Indikator Status VPN**: Aplikasi mendeteksi koneksi VPN Helper secara langsung dan menampilkan statusnya di navbar.

---

## Persyaratan Sistem

- Python 3.11+
- Brave / Google Chrome (untuk ekstensi Fasih Session Sync)
- Dependencies: lihat `requirements.txt`

---

## Instalasi

```bash
git clone https://github.com/tiomultazem/fasihsm-fetcher.git
cd fasihsm-fetcher
pip install -r requirements.txt
```

---

## Penggunaan

### 1. Pasang Ekstensi Browser

1. Buka `brave://extensions/` atau `chrome://extensions/` di browser.
2. Aktifkan **Developer mode** di pojok kanan atas.
3. Klik **Load unpacked** → pilih folder `extension` di dalam folder proyek.
4. Ekstensi **Fasih Session Sync** kini aktif.

### 2. Jalankan Aplikasi

```bash
python src/app.py
```

Browser akan terbuka otomatis ke `http://localhost:5000/fasihsm-fetcher`.

### 3. Hubungkan Sesi

1. Buka [Fasih-SM](https://fasih-sm.bps.go.id) di browser dan pastikan sudah login.
2. Klik ikon ekstensi **Fasih Session Sync** di toolbar.
3. Tunggu hingga muncul lencana hijau **OK**.
4. Muat ulang halaman fetcher — sesi kini terhubung.

---

## Disclaimer

Tools ini dibuat untuk tujuan efisiensi pengolahan data internal di lingkungan Badan Pusat Statistik. Pengguna bertanggung jawab penuh atas keamanan data, hak akses VPN, dan kepatuhan terhadap kebijakan internal instansi.

---

*Copyright © 2026 Gilang Wahyu Prasetyo (BPS Kabupaten Tabalong)*
