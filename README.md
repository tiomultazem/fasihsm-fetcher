# FasihSM Fetcher

*FasihSM Fetcher* adalah tools berbasis Python yang dirancang untuk mengambil data dari platform Fasih-SM dan menyimpannya ke dalam basis data satuan kerja. Tools ini memadukan otomasi browser untuk autentikasi dan request API untuk pengambilan data skala besar secara cepat.

---

## 🚀 Fitur Utama

- Fast Login dan loading UI.
- *Ekstrak* metadata survei, data petugas berdasar role, dan data sampel berdasar status assignment.
- *Bulk approve* banyak sampel cukup dengan satu tombol.

---

## 🆕 Fitur Terbaru (Optimasi & Pembaruan Pencarian)

- **Pencarian Multi-Key (Semicolon Split)**:
  - Anda dapat mencari beberapa keyword atau ID Target/SLS sekaligus secara bersamaan dengan memisahkan kata kunci menggunakan tanda titik koma (`;`).
  - Sistem memproses setiap kata kunci pencarian secara cepat dan mandiri untuk memastikan akurasi data tanpa ada baris terlewat.
- **Pilihan Pencarian Cepat ("Fuzzy" Toggle)**:
  - Tombol switch **"Fuzzy"** baru di samping kolom pencarian memberikan kendali atas tipe pencarian:
    - **Fuzzy Mati (Default / Sangat Direkomendasikan untuk ID/SLS)**: Hanya mengambil 3 baris hasil teratas per kata kunci. Cara ini meningkatkan kecepatan pencarian massal hingga 80% dan secara drastis mengurangi risiko error timeout dari server BPS.
    - **Fuzzy Aktif**: Mengambil hingga 100 baris hasil yang mirip, cocok jika Anda mencari berdasarkan nama petugas atau kata kunci umum yang membutuhkan pencarian luas.
- **Notifikasi Kata Kunci Hilang (Missing Keys Alert)**:
  - Jika ada ID SLS atau kata kunci pencarian yang Anda inputkan tidak ditemukan sama sekali di server BPS, aplikasi akan menampilkan kotak peringatan kuning berisi daftar kata kunci yang hilang tepat di atas tabel.

---

## 🛠️ Persyaratan Sistem

- Python 3.11+
- Dependencies: silakan cek requirements.txt

---

## 📦 Instalasi Via CMD

```bash
git clone https://github.com/tiomultazem/fasihsm-fetcher.git
cd fasihsm-fetcher
pip install -r requirements.txt
```

---

## 🖥️ Cara Penggunaan

1. Run di cmd di direktori proyek
```
python app.py
```
2. Akses aplikasi di browser di http://localhost:5000/fasihsm-fetcher (atau sesuaikan port jika diatur berbeda di `.env`, misal jika Anda mengatur `port=5010` maka akses di http://localhost:5010/fasihsm-fetcher)

3. Buat File .env di Root Directory
4. Masukkan informasi berikut:

   ```env
   FASIH_USER=username
   FASIH_PASS=password
   # port=5000 (opsional: jika dikomen, dihapus, atau kosong, default berjalan di port 5000. Untuk mengubah port default, isi dengan nilai lain tanpa tanda komentar #, misal: port=5010)
   ```

5. Sesuaikan variabel `USERNAME` dan `PASSWORD` dengan akun SSO BPS Anda.
6. Klik "Import .env" untuk mengimpor SSO anda
7. Klik "Login" untuk login ke Fasih-SM. Tunggu hingga muncul notifikasi "Login sukses. Sesi aktif."
8. Klik tab "Survei" di navigasi atas.
9. Silakan jelajahi sendiri antarmuka yang seperti Fasih-SM ini.

## Approve Assignment Secara Massal

1. Pilih survei di kiri dan klik. Tunggu hingga metadata muncul.
2. Klik tab "Daftar Sampel".
3. Klik tombol kuning "Bulk Approve".
4. Akan muncul pop-up konfirmasi jumlah sampel yang ingin di-approve massal. Isi jumlahnya, lalu klik "Lanjut".
5. Muncul lagi pop-up untuk mengonfirmasi approve. klik "Ya, approve"
6. Jangan lupa kopinya diminum sebelum dingin gegara terlalu asyik melihat progres approve yang otomatis ini.

### Catatan

ada file Jupyter Notebook yang sebelumnya saya pakai sebagai playground untuk trial-error fungsi, bisa digunakan apabila anda lebih prefer memanfaatkan code saya yang setengah matang tersebut ketimbang UI.

---

## ⚠️ Disclaimer

Tools ini dibuat untuk tujuan efisiensi pengolahan data internal di lingkungan Badan Pusat Statistik. Pengguna bertanggung jawab penuh atas penggunaan kredensial, keamanan data, dan kepatuhan terhadap kebijakan internal instansi.

---

*Copyright © 2026 Gilang Wahyu Prasetyo (BPS Kabupaten Tabalong)*

Licensed under the MIT License.
