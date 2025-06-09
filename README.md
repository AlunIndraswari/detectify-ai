# Detectify AI - Detektor Gambar AI

Detectify AI adalah aplikasi web lengkap yang dibangun dengan Python dan Flask. Aplikasi ini mampu mendeteksi apakah sebuah karya seni digital dibuat oleh manusia (Real Art) atau dihasilkan oleh kecerdasan buatan (AI Art).

Proyek ini tidak hanya sebatas alat deteksi, tetapi juga mencakup sistem manajemen pengguna yang komprehensif, memungkinkan interaksi yang personal dan berkelanjutan untuk meningkatkan akurasi model.

## Fitur Utama

* **Deteksi Gambar**: Pengguna dapat mengunggah file gambar dari perangkat mereka atau memasukkan URL gambar untuk dianalisis oleh model machine learning.
* **Sistem Otentikasi**: Fitur registrasi dan login yang aman untuk membedakan pengguna.
* **Riwayat Analisis**: Setiap pengguna yang login memiliki halaman riwayat pribadi yang menampilkan semua gambar yang pernah mereka analisis sebelumnya.
* **Berbagi Hasil**: Setiap halaman hasil deteksi memiliki URL unik yang dapat disalin dan dibagikan ke media sosial.
* **Siklus Feedback (Human-in-the-Loop)**: Jika pengguna merasa hasil prediksi salah, mereka dapat memberikan masukan (misalnya, "Ini Sebenarnya AI"). Gambar tersebut akan dipindahkan untuk ditinjau.
* **Panel Verifikasi Admin**: Halaman khusus yang hanya dapat diakses oleh admin untuk meninjau, mengonfirmasi, atau menolak masukan dari pengguna. Gambar yang dikonfirmasi dapat digunakan untuk melatih ulang model di masa depan.

## Prasyarat

Sebelum memulai, pastikan Anda telah menginstal perangkat lunak berikut di sistem Anda:

* [Python](https://www.python.org/downloads/) (versi 3.9 atau yang lebih baru direkomendasikan).
* `pip` (manajer paket Python, biasanya sudah terinstal bersama Python).
* `git` (sistem kontrol versi untuk mengkloning repositori).

## Panduan Instalasi dan Implementasi

Ikuti langkah-langkah berikut untuk menjalankan proyek ini di komputer lokal Anda.

### 1. Dapatkan Kode Proyek

Buka terminal atau command prompt Anda, navigasi ke direktori tempat Anda ingin menyimpan proyek, lalu kloning repositori.

```bash
# Ganti URL dengan URL repositori Git Anda
git clone [https://github.com/username/detectify-ai-1.git](https://github.com/username/detectify-ai-1.git)
cd detectify-ai-1
```

### 2. Buat dan Aktifkan Virtual Environment

Menggunakan lingkungan virtual adalah praktik terbaik untuk mengisolasi dependensi proyek.

```bash
# Membuat folder virtual environment bernama 'venv'
python -m venv venv
```

Selanjutnya, aktifkan lingkungan virtual tersebut.

* **Di Windows:**
    ```bash
    venv\Scripts\activate
    ```
* **Di macOS/Linux:**
    ```bash
    source venv/bin/activate
    ```
    Setelah aktif, nama terminal Anda akan diawali dengan `(venv)`.

### 3. Instal Dependensi Proyek

Dengan lingkungan virtual yang aktif, instal semua pustaka yang dibutuhkan menggunakan file `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 4. Siapkan Model Machine Learning

Aplikasi ini memerlukan file model `.h5` untuk berfungsi.

* Buat sebuah folder baru bernama `models` di dalam direktori utama proyek.
* Salin file model Anda (misalnya, `transfer_resnet50_with_report.h5`) ke dalam folder `models` yang baru saja dibuat.

Struktur proyek Anda harus terlihat seperti ini:

```
detectify-ai-1/
├── models/
│   └── transfer_resnet50_with_report.h5
├── static/
├── templates/
├── app.py
└── ...
```

## Menjalankan Aplikasi

Setelah semua persiapan selesai, ikuti dua langkah terakhir ini.

### 1. Inisialisasi Database (Hanya Sekali)

Sebelum menjalankan server untuk pertama kalinya, Anda perlu membuat file database dan semua tabelnya. Jalankan perintah berikut di terminal:

```bash
flask init-db
```

Anda akan melihat pesan konfirmasi: `Database telah diinisialisasi.` Langkah ini hanya perlu dilakukan sekali.

### 2. Jalankan Server Flask

Sekarang, jalankan server pengembangan Flask.

```bash
flask run
```

Aplikasi Anda sekarang berjalan! Buka browser web dan kunjungi alamat berikut:
[**http://127.0.0.1:5000**](http://127.0.0.1:5000)

## Cara Membuat Akun Admin

Aplikasi ini tidak memiliki antarmuka untuk membuat admin. Proses ini harus dilakukan secara manual melalui terminal setelah Anda mendaftarkan akun biasa.

1.  **Daftar Akun**: Gunakan halaman registrasi di web untuk membuat akun yang akan dijadikan admin (misalnya, dengan email `admin@proyek.com`).
2.  **Hentikan Server**: Kembali ke terminal dan tekan `Ctrl + C`.
3.  **Buka Flask Shell**: Jalankan perintah berikut:
    ```bash
    flask shell
    ```
4.  **Jalankan Perintah Python**: Di dalam shell (`>>>`), jalankan kode berikut. **Jangan lupa ganti emailnya dengan email admin Anda.**
    ```python
    from app import db, User
    admin_user = User.query.filter_by(email='admin@proyek.com').first()
    if admin_user:
        admin_user.is_admin = True
        db.session.commit()
        print(f"SUKSES: Pengguna '{admin_user.username}' telah dijadikan admin.")
    else:
        print("GAGAL: Pengguna tidak ditemukan.")
    exit()
    ```
5.  **Jalankan Server Kembali**: Jalankan `flask run` lagi. Sekarang, saat Anda login dengan akun tersebut, link "Admin Verify" akan muncul di navbar.
