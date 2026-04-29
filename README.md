# FasihSM Fetcher

*FasihSM Fetcher* adalah tools berbasis Python yang dirancang untuk mengambil data dari platform Fasih-SM dan menyimpannya ke dalam basis data satuan kerja. Tools ini memadukan otomasi browser untuk autentikasi dan request API untuk pengambilan data skala besar secara cepat.

---

## 🚀 Fitur Utama

- Fast Login dan loading UI.
- *Ekstrak* metadata survei, data petugas berdasar role, dan data sampel berdasar status assignment.
- *Bulk approve* banyak sampel cukup dengan satu tombol.

---

## 🛠️ Persyaratan Sistem

- Python 3.12
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

1. Buat File .env di Root Directory
2. Masukkan informasi berikut:
```
USERNAME=username
PASSWORD=password
```
3. Sesuaikan variabel `USERNAME` dan `PASSWORD` dengan akun SSO BPS Anda.
4. Klik "Import .env" untuk mengimpor SSO anda
5. Klik "Login" untuk login ke Fasih-SM. Tunggu hingga muncul notifikasi "Login sukses. Sesi aktif."
6. Klik tab "Survei" di navigasi atas.
7. Silakan jelajahi sendiri antarmuka yang seperti Fasih-SM ini.

## Untuk Approve assignment secara massal:
1. Pilih survei di kiri dan klik. Tunggu hingga metadata muncul.
2. Klik tab "Daftar Sampel".
3. Klik tombol kuning "Bulk Approve".
4. Akan muncul pop-up konfirmasi jumlah sampel yang ingin di-approve massal. Isi jumlahnya, lalu klik "Lanjut".
5. Muncul lagi pop-up untuk mengonfirmasi approve. klik "Ya, approve"
6. Jangan lupa kopinya diminum sebelum dingin gegara terlalu asyik melihat progres approve yang otomatis ini.

---

## ⚠️ Disclaimer

Tools ini dibuat untuk tujuan efisiensi pengolahan data internal di lingkungan Badan Pusat Statistik. Pengguna bertanggung jawab penuh atas penggunaan kredensial, keamanan data, dan kepatuhan terhadap kebijakan internal instansi.

---

*Copyright © 2026 Gilang Wahyu Prasetyo (BPS Kabupaten Tabalong)*

Licensed under the MIT License.
