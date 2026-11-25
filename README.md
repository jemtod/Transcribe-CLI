# transcribe-cli

**Dari rekaman rapat, kuliah, atau podcast menjadi teks dan subtitle di komputer sendiri.**

Local audio and video transcription with Whisper. Indonesian defaults, an interactive terminal guide, and exports to TXT, SRT, VTT, JSON, and Markdown.

`transcribe-cli` adalah aplikasi baris perintah (CLI) untuk mengubah ucapan dalam file audio atau video menjadi tulisan. Anda menjalankannya melalui terminal. Tool ini menggunakan model Whisper lokal melalui **faster-whisper**, dengan bahasa Indonesia sebagai pengaturan awal.

Mulai dari panduan interaktif:

```bash
transcribe
```

Atau langsung berikan nama file:

```bash
transcribe "rapat tim.mp4"
```

Secara bawaan, perintah tersebut membuat file teks dan subtitle SRT menggunakan model `small`.

> **Sebelum pemakaian pertama:** koneksi internet diperlukan untuk mengunduh model. CLI akan menyebut nama model, perkiraan ukurannya, dan pemberitahuan “unduhan satu kali”. Setelah model lengkap tersimpan, transkripsi menggunakan model tersebut berjalan secara lokal.

[Instalasi](#instalasi) · [Cara menggunakan](#cara-menggunakan) · [Contoh perintah](#contoh-perintah) · [Hasil transkripsi](#hasil-transkripsi) · [Konfigurasi](#konfigurasi) · [Pemecahan masalah](#pemecahan-masalah)

## Untuk apa tool ini?

Gunakan `transcribe-cli` ketika Anda ingin:

- Membaca kembali pembahasan rapat melalui transkrip yang bisa dicari dan diedit.
- Mengubah rekaman kuliah menjadi bahan catatan dalam format teks atau Markdown.
- Membuat file subtitle pendamping untuk video.
- Mentranskripsikan banyak rekaman dalam satu folder, termasuk subfoldernya.
- Menghasilkan data JSON dengan waktu per kata untuk pemrosesan lanjutan.

Tool ini menghasilkan transkrip ucapan, bukan ringkasan otomatis atau notula yang menyusun keputusan rapat. Hasilnya tetap perlu diperiksa, terutama nama, istilah khusus, dan angka.

### Mengapa diproses secara lokal?

Audio dan transkrip tetap berada di perangkat Anda. Aplikasi tidak mengirim audio, teks, atau telemetri ke layanan transkripsi. Tidak ada tarif layanan per menit; kecepatan pemrosesan bergantung pada komputer dan model yang dipilih.

Akses jaringan saat aplikasi berjalan hanya digunakan untuk mengunduh model melalui faster-whisper. Memilih model lain memerlukan unduhan model tersebut. Pemasangan paket melalui pip atau pipx juga memerlukan koneksi tersendiri.

## Instalasi

### 1. Siapkan Python dan FFmpeg

Anda membutuhkan:

| Komponen | Kebutuhan |
| --- | --- |
| Python | Versi 3.10 atau lebih baru |
| FFmpeg | Perintah `ffmpeg` dan `ffprobe` tersedia di terminal |
| Ruang penyimpanan | Cukup untuk model dan file hasil transkripsi |
| GPU NVIDIA | Opsional; CPU juga dapat digunakan |

Periksa versi Python:

```bash
python --version
```

Pada Linux/macOS, gunakan `python3` bila perintah `python` tidak tersedia. Pada Windows, Anda juga bisa menggunakan `py`.

Pasang FFmpeg sesuai sistem operasi Anda:

<details>
<summary>Windows</summary>

Jalankan salah satu perintah berikut, sesuai pengelola paket yang tersedia:

```powershell
winget install Gyan.FFmpeg
```

Atau melalui Chocolatey:

```powershell
choco install ffmpeg
```

Buka terminal baru setelah pemasangan agar perubahan PATH terbaca.

</details>

<details>
<summary>macOS</summary>

Jika Homebrew sudah tersedia:

```bash
brew install ffmpeg
```

</details>

<details>
<summary>Linux (Debian / Ubuntu)</summary>

```bash
sudo apt install ffmpeg
```

Untuk distribusi lain, gunakan pengelola paket distribusi Anda.

</details>

Pastikan keduanya bisa dijalankan:

```bash
ffmpeg -version
ffprobe -version
```

### 2. Pasang aplikasi dari repository ini

Unduh atau clone repository, lalu buka terminal di folder yang berisi `pyproject.toml`.

Jika `pipx` sudah tersedia:

```bash
pipx install .
```

Jika belum, pasang pipx melalui pengelola paket sistem Anda atau, bila lingkungan Python Anda mengizinkan pemasangan paket pengguna:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

Buka terminal baru, masuk kembali ke folder proyek, lalu jalankan `pipx install .`.

> Perintah instalasinya adalah `pipx install .` dari folder proyek. Nama paket proyek adalah `transcribe-cli`, sedangkan perintah yang dijalankan setelah instalasi adalah `transcribe`.

<details>
<summary>Alternatif: gunakan virtual environment</summary>

Dari folder proyek, buat lingkungan Python terpisah:

```bash
python -m venv .venv
```

Aktifkan pada Linux/macOS:

```bash
source .venv/bin/activate
```

Atau pada Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Kemudian pasang aplikasinya:

```bash
python -m pip install .
```

Aktifkan lingkungan ini kembali setiap kali membuka terminal baru sebelum menjalankan `transcribe`.

</details>

### 3. Periksa pemasangan

```bash
transcribe doctor
```

Perintah ini memeriksa Python, FFmpeg, backend transkripsi, ketersediaan CUDA, dan lokasi cache model. Belum ada model pada pemasangan baru adalah kondisi normal; model diunduh saat transkripsi pertama.

Backend menggunakan faster-whisper dan CTranslate2, tanpa kebutuhan PyTorch. Jika CUDA terdeteksi, mode otomatis memilih GPU dengan `float16`; jika tidak, aplikasi menggunakan CPU dengan `int8`. Penggunaan GPU memerlukan driver serta CUDA/cuDNN yang cocok dengan CTranslate2 yang terpasang.

## Cara menggunakan

### Panduan interaktif untuk pemakaian pertama

Jalankan tanpa argumen:

```bash
transcribe
```

1. Masukkan path file atau folder. Anda bisa menyeretnya ke terminal; panduan menerima tanda kutip dan spasi pada path.
2. Pilih kualitas: **Cepat**, **Seimbang**, atau **Akurat**. Pilihan awalnya Seimbang.
3. Pilih hasil: teks, subtitle, teks + subtitle, atau semua format. Pilihan awalnya teks + subtitle.
4. Periksa ringkasan file, durasi, perkiraan waktu, dan format hasil. Jawab `y` atau tekan Enter pada `Mulai? [Y/n]` untuk memulai.

Estimasi waktu hanya perkiraan kasar, belum termasuk unduhan model. Proses dapat lebih lama bergantung pada perangkat, model, dan rekamannya.

### Langsung proses satu file

```bash
transcribe "rekaman rapat.mp4"
```

Pengaturan bawaan:

| Pengaturan | Nilai |
| --- | --- |
| Bahasa | Indonesia (`id`) |
| Kualitas | Seimbang (`small`) |
| Hasil | Teks `.txt` dan subtitle `.srt` |
| Lokasi | Folder `<nama-file>_transkrip` di samping media |
| Filter keheningan | Aktif |

Config dapat mengubah pengaturan bawaan tersebut. Bungkus path dengan tanda kutip jika mengandung spasi.

### Pilih kualitas dan format sendiri

```bash
transcribe kuliah.m4a --quality akurat --output all
```

Versi singkatnya:

```bash
transcribe kuliah.m4a -q akurat -o all
```

Perintah langsung segera memproses file. Di terminal interaktif, aplikasi meminta keputusan jika hasil sudah ada atau kualitas Akurat dipilih pada CPU. Dalam pipe/non-TTY, aplikasi tidak menampilkan pertanyaan dan melewati file hasil yang sudah ada.

## Contoh perintah

| Kebutuhan | Perintah |
| --- | --- |
| Teks saja dari rapat | `transcribe rapat.mp4 -o text` |
| Subtitle untuk video | `transcribe video.mp4 -o subtitle` |
| Seluruh format untuk rekaman kuliah | `transcribe kuliah.m4a -o all` |
| Draf cepat | `transcribe wawancara.wav -q cepat` |
| Podcast berbahasa Inggris | `transcribe podcast.mp3 -l en` |
| Deteksi bahasa otomatis | `transcribe wawancara.wav -l auto` |
| Terjemahkan ucapan ke bahasa Inggris | `transcribe diskusi.mp4 --translate` |
| Gunakan glosarium nama dan istilah | `transcribe rapat.mp4 -t istilah.txt` |
| Proses folder beserta subfolder | `transcribe "Rekaman semester"` |

Pada `--lang auto`, aplikasi melaporkan bahasa yang terdeteksi dan tingkat keyakinannya. Jika keyakinannya di bawah 60%, aplikasi menyarankan pemeriksaan hasil atau pemilihan bahasa secara eksplisit.

### Opsi CLI

```bash
transcribe --help
```

Enam opsi utama tersedia; pengaturan lanjutan berada di config.

| Opsi | Nilai yang diterima | Default bawaan |
| --- | --- | --- |
| `-q`, `--quality` | `fast` / `cepat`, `balanced` / `seimbang`, `best` / `akurat` | `balanced` |
| `-l`, `--lang` | `id`, `en`, `auto` | `id` |
| `-o`, `--output` | `text`, `subtitle`, `both`, `all` | `both` |
| `-t`, `--terms` | Path file glosarium UTF-8 | Tidak ada |
| `--translate` | Terjemahkan hasil ke Inggris | Nonaktif |
| `--version` | Tampilkan versi aplikasi | |

Perintah pendamping:

```bash
transcribe models       # Lihat pilihan model dan status unduhan
transcribe config       # Lihat lokasi config dan nilai efektif
transcribe config edit  # Buka config di editor bawaan
transcribe doctor       # Periksa lingkungan dan dependensi
```

### Format media yang didukung

**Audio:** MP3, WAV, M4A, AAC, OGG, OPUS, FLAC.  
**Video:** MP4, MKV, MOV, WEBM, AVI.

Aplikasi memakai FFprobe untuk memeriksa durasi dan aliran audio sebelum transkripsi. Video tanpa audio akan dilaporkan sebagai error. File media masukan tidak diubah.

## Hasil transkripsi

### Di mana file hasil disimpan?

Dengan pengaturan bawaan, contoh susunannya:

```text
rekaman/
├── rapat.mp4
└── rapat_transkrip/
    ├── rapat.txt
    └── rapat.srt
```

Jika Anda memilih satu format, misalnya `-o text`, hasilnya langsung berada di samping sumber sebagai `rapat.txt`. Jika memilih beberapa format, aplikasi membuat folder `<nama>_transkrip`.

### Pilihan format

| Pilihan `--output` | File yang dihasilkan | Kegunaan |
| --- | --- | --- |
| `text` | `.txt` | Membaca, mencari, dan mengedit transkrip |
| `subtitle` | `.srt` | Subtitle pendamping video |
| `both` | `.txt`, `.srt` | Transkrip dan subtitle sekaligus |
| `all` | `.txt`, `.srt`, `.vtt`, `.json`, `.md` | Seluruh format, termasuk data terstruktur dan catatan |

Contoh di bawah hanya ilustrasi format, bukan hasil uji akurasi model.

<details>
<summary>Lihat contoh teks, subtitle, dan Markdown</summary>

TXT berisi teks tanpa timestamp, dengan paragraf berdasarkan jeda ucapan:

```text
Selamat pagi. Kita mulai rapat hari ini.
```

SRT memakai nomor blok dan timestamp dengan koma untuk milidetik:

```srt
1
00:00:00,000 --> 00:00:03,000
Selamat pagi. Kita mulai rapat hari ini.
```

VTT memakai isi subtitle yang sama, dengan header `WEBVTT` dan pemisah titik:

```vtt
WEBVTT

1
00:00:00.000 --> 00:00:03.000
Selamat pagi. Kita mulai rapat hari ini.
```

Markdown memakai nama file sebagai judul, metadata tanggal/durasi/model/bahasa, dan penanda waktu sekitar setiap 30 detik pada awal segmen yang tersedia. Bagian isi, misalnya:

```markdown
[00:00] Selamat pagi. Kita mulai rapat hari ini.

[00:31] Berikut pembahasan agenda berikutnya.
```

</details>

<details>
<summary>Aturan subtitle dan isi JSON</summary>

Subtitle secara bawaan dibatasi hingga 42 karakter per baris, 2 baris per blok, dan 7 detik per blok, dengan durasi minimum 0,8 detik. Pemisahan mengikuti batas kata dan mengutamakan tanda baca jika memungkinkan. Blok tidak tumpang tindih.

Pada ucapan sangat padat, caption dapat diperpanjang melampaui segmen asal untuk menjaga keterbacaan. Pembagian waktu teks merupakan perkiraan. Kata tunggal yang lebih panjang dari lebar baris ditolak; sesuaikan `max_line_chars` jika diperlukan.

JSON mencatat:

- `schema_version`, saat ini `"1.0"`.
- `language`, `language_probability`, `duration`, dan `model`.
- `settings`, yaitu pengaturan yang dipakai.
- `segments`, berisi `id`, `start`, `end`, `text`, `avg_logprob`, dan `no_speech_prob`.
- `words` pada setiap segmen saat timestamp kata aktif, berisi `start`, `end`, `word`, dan `probability`.

Timestamp kata otomatis aktif untuk `--output all`, yang mencakup JSON. Setelah filtering, ID segmen tetap mengikuti ID asal.

</details>

### Jika file hasil sudah ada

Aplikasi tidak menimpa hasil secara diam-diam.

- Pada terminal interaktif, jawab pertanyaan `File sudah ada, timpa? [y/N]`. Menekan Enter berarti melewati file tersebut.
- Pada non-TTY atau pipe, aplikasi melewati hasil yang sudah ada dan melaporkan `dilewati`.
- Aplikasi tetap membuat format lain yang belum ada.

Tekan `Ctrl+C` untuk menghentikan proses. Aplikasi membersihkan tulisan parsial dari proses penulisan yang terputus dan mempertahankan hasil file sebelumnya.

## Pilihan model dan unduhan

Untuk kebanyakan pemakaian pertama, gunakan **Seimbang**. Pilih Cepat untuk draf, atau Akurat jika Anda bersedia menunggu lebih lama.

```bash
transcribe models
```

Ukuran unduhan dan RAM di bawah adalah **perkiraan**, bukan hasil pengukuran pada perangkat Anda. Kebutuhan aktual dapat berbeda.

| Kualitas | Model | Unduhan sekitar | RAM kerja sekitar | Catatan |
| --- | --- | --- | --- | --- |
| Pengujian melalui config | `tiny` | 75 MB | 1 GB | Gunakan `model_override` |
| Cepat / `fast` | `base` | 145 MB | 1 GB | Draf; periksa nama dan angka |
| Seimbang / `balanced` | `small` | 485 MB | 2 GB | Default aplikasi |
| Akurat / `best` | `turbo` | 1,6 GB | 4 GB | Berat di CPU |
| Akurat, CUDA dengan ≥10 GB VRAM bebas | `large-v3` | 3,1 GB | 8 GB atau lebih | Memerlukan memori lebih besar |

Mode Akurat untuk terjemahan menggunakan `large-v3`, karena turbo ditujukan untuk transkripsi. Pada CPU, aplikasi memperingatkan bahwa kualitas Akurat dapat lambat; di terminal interaktif Anda dapat memilih beralih ke Seimbang.

Setiap model yang lengkap disimpan di cache lokal dan digunakan kembali tanpa pemeriksaan pembaruan jaringan. Backend dapat melanjutkan unduhan yang terputus. Jalankan `transcribe doctor` untuk melihat lokasi cache aktual.

<details>
<summary>Menggunakan model pada komputer offline</summary>

Siapkan model pada komputer yang terhubung ke internet, lalu salin folder model CTranslate2 yang lengkap ke perangkat tujuan. Folder harus memuat `model.bin`, `config.json`, dan `tokenizer.json`, serta file kosakata dan konfigurasi preprocessing bila tersedia.

Arahkan `model_override` ke folder tersebut melalui config:

```toml
model_override = "/lokasi/model-lokal"
```

Path di atas adalah contoh; ganti dengan lokasi folder model Anda.

</details>

## Glosarium untuk nama dan istilah

Glosarium membantu memberikan konteks nama orang, merek, singkatan, atau jargon kepada Whisper lokal.

Buat file `istilah.txt`, satu istilah per baris:

```text
Prambanan
BPJS
```

Gunakan saat transkripsi:

```bash
transcribe wawancara.mp3 --terms istilah.txt
```

Contoh harapan, bukan jaminan hasil: model mungkin menulis `b p j s` tanpa konteks; istilah `BPJS` dapat membantu model memilih ejaan `BPJS`.

Aplikasi meneruskan daftar ini sebagai `initial_prompt`, bukan sebagai aturan penggantian kata. Gunakan daftar ringkas dan tetap periksa istilah penting pada hasilnya.

## Konfigurasi

Untuk melihat lokasi file dan pengaturan efektif:

```bash
transcribe config
```

Untuk mengeditnya:

```bash
transcribe config edit
```

Pada edit pertama, aplikasi membuat file default dengan komentar, lalu membukanya melalui editor bawaan sistem. File memakai format TOML.

Contoh pengaturan:

```toml
default_quality = "seimbang"
default_output = "all"
clean_text = true
output_dir = "/home/anda/Transkrip"
```

Ganti `output_dir` dengan folder tujuan Anda. Pada Windows, tulis backslash ganda dalam string TOML berpetik ganda, misalnya `output_dir = "C:\\Users\\Anda\\Transkrip"`.

Urutan prioritas: **opsi CLI > file config > default bawaan**. Pilihan yang Anda ubah lewat wizard berlaku untuk proses tersebut.

<details>
<summary>Referensi seluruh kunci config</summary>

| Kunci | Default | Fungsi |
| --- | --- | --- |
| `default_quality` | `"balanced"` | Kualitas; alias Indonesia diterima |
| `default_lang` | `"id"` | `id`, `en`, atau `auto` |
| `default_output` | `"both"` | `text`, `subtitle`, `both`, `all` |
| `model_override` | `""` | `tiny`, `base`, `small`, `turbo`, `large-v3`, atau folder model lokal lengkap |
| `device` | `"auto"` | `auto`, `cpu`, `cuda` |
| `compute_type` | `"auto"` | `float16` di CUDA, `int8` di CPU; pilihan eksplisit: `float16`, `float32`, `int8`, `int8_float16`, `int8_float32` |
| `max_line_chars` | `42` | 8..200 karakter per baris subtitle |
| `max_lines` | `2` | 1..4 baris per blok subtitle |
| `vad` | `true` | Filter keheningan |
| `clean_text` | `false` | Rapikan spasi, spasi sebelum tanda baca, dan kapital awal kalimat |
| `word_timestamps` | `false` | Otomatis aktif untuk JSON |
| `output_dir` | `""` | Kosong berarti di samping media; isi untuk mengganti folder induk hasil |

`output_dir` mengganti folder induk. Jika ada beberapa format, aplikasi tetap membuat subfolder `<nama>_transkrip` di dalamnya. File dengan nama sama dari subfolder sumber berbeda dapat berbenturan jika memakai satu `output_dir`; aturan konfirmasi/lewati tetap berlaku.

Pada Python 3.11+, config dibaca dengan `tomllib`. Pada Python 3.10, pembaca bawaan mendukung subset TOML untuk config datar ini: key/nilai skalar satu baris, string berpetik, integer, boolean, dan komentar. Tabel dan string multiline tidak didukung pada Python 3.10.

</details>

### Filter dan cleanup teks

Hallucination guard selalu aktif. Aplikasi menyusutkan runtunan minimal tiga segmen identik menjadi satu, serta membuang segmen dengan `no_speech_prob > 0.9` sekaligus `avg_logprob < -1.0`. Ringkasan menampilkan jumlah segmen yang dibuang. Pengulangan yang memang diucapkan juga bisa tersaring.

`clean_text` bersifat opsional dan nonaktif secara default. Saat aktif, aplikasi merapikan spasi dan kapital awal kalimat tanpa menulis ulang kosakata.

## Pemecahan masalah

| Masalah | Langkah yang bisa dicoba |
| --- | --- |
| `transcribe` tidak dikenali | Buka terminal baru setelah `pipx ensurepath`. Jika memakai virtual environment, aktifkan `.venv` terlebih dahulu. |
| FFmpeg atau FFprobe tidak ditemukan | Pastikan keduanya terpasang dan tersedia di PATH, lalu jalankan `transcribe doctor`. |
| Model belum tersedia saat offline | Unduh model saat terhubung internet atau gunakan folder model lokal lengkap melalui `model_override`. |
| Proses terlalu lama | Coba `-q cepat` atau `-q seimbang`. Kualitas Akurat dapat berat di CPU. |
| Video tidak memiliki audio | Pilih media yang memiliki aliran audio. Video tanpa audio tidak bisa ditranskripsikan. |
| File hasil dilaporkan `dilewati` | Hasil sudah ada. Jalankan dari terminal interaktif jika ingin mengonfirmasi penimpaan. |
| Keyakinan deteksi bahasa rendah | Pilih `-l id` atau `-l en` secara eksplisit dan tinjau hasilnya. |
| Kata lebih panjang dari batas subtitle | Naikkan `max_line_chars` di config. |
| Hasil kosong | Tidak ada ucapan yang terdeteksi. Periksa suara rekaman dan pengaturan filter keheningan. |

Jika masalah masih terjadi, sertakan versi dari `transcribe --version`, sistem operasi, perintah yang dijalankan, dan pesan error saat membuka issue di repository. Hindari melampirkan rekaman atau transkrip sensitif.

## Batasan yang perlu diketahui

- Tool belum memisahkan identitas pembicara (*speaker diarization*).
- Kebisingan, suara yang bertumpuk, aksen daerah yang kuat, dan pergantian bahasa dapat menurunkan akurasi.
- Terjemahan menghasilkan bahasa Inggris. Hasil transkrip dan waktu subtitle tetap perlu ditinjau sebelum dipublikasikan atau dijadikan catatan resmi.
- Estimasi waktu dan kebutuhan memori tidak menjamin kinerja pada perangkat tertentu.
- Penulisan hasil baru memerlukan filesystem yang mendukung hard link, misalnya NTFS, APFS, atau ext4.

<details>
<summary>Perilaku batch, terminal, dan penulisan hasil</summary>

Error pada satu file tidak menghentikan batch. Aplikasi mencatatnya, melanjutkan file lain, lalu menampilkan ringkasan.

| Kode keluar | Arti |
| --- | --- |
| `0` | Selesai, termasuk jika hasil yang sudah ada dilewati |
| `1` | Ada error pemrosesan atau lingkungan |
| `2` | Penggunaan/config tidak valid, format tidak didukung, atau folder tanpa media yang didukung |
| `130` | Proses dihentikan melalui interupsi |

Aplikasi merender isi dan menulisnya ke file staging sebelum memublikasikan hasil. Pembuatan file baru memakai hard link eksklusif untuk mencegah penimpaan jika file lain muncul pada lokasi yang sama.

Pada interupsi, staging dan file baru dari penulisan yang belum selesai dibersihkan. Hasil sebelumnya tetap tersimpan. Penggantian yang sudah selesai tetap berupa file lengkap; penggantian beberapa format bukan satu transaksi atomik.

`NO_COLOR=1` menonaktifkan warna. Output ke file/pipe berupa baris teks tanpa progress bar. Wizard dan konfirmasi hanya berjalan jika stdin dan stdout merupakan terminal; memanggil tanpa PATH pada non-TTY mengembalikan kode 2. Konfirmasi menerima `y`, `ya`, `yes`, `n`, `tidak`, dan `no`.

</details>

## Pengembangan

Aktifkan virtual environment, lalu dari folder proyek:

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

Tes default menggunakan engine palsu dan tidak mengunduh model. Audio uji dibuat dengan FFmpeg; tes yang memerlukannya dilewati bila FFmpeg tidak tersedia.

Untuk menjalankan tes integrasi opsional, siapkan model `tiny` di cache terlebih dahulu:

```bash
python -m pytest -m slow -q
```

Tes tersebut juga tidak mengunduh model dan dilewati jika model lokal belum tersedia.

<details>
<summary>Susunan kode</summary>

| Modul | Tanggung jawab |
| --- | --- |
| `cli.py` | Antarmuka Typer dan penerimaan argumen |
| `wizard.py` | Alur panduan dan konfirmasi |
| `media.py` | Penemuan file dan validasi FFprobe |
| `engine.py` | Pembungkus faster-whisper |
| `presets.py` | Pemetaan kualitas, model, format, dan alias Indonesia |
| `config.py` | Pembacaan, validasi, dan prioritas config |
| `segmenter.py` | Pembagian teks serta waktu subtitle |
| `formatters.py` | Pembentukan isi TXT, SRT, VTT, JSON, dan Markdown |
| `postprocess.py` | Hallucination guard dan cleanup opsional |
| `service.py` | Orkestrasi pemrosesan batch |
| `output.py` | Perencanaan lokasi dan penulisan file hasil |
| `commands.py` | Tindakan `models`, `config`, dan `doctor` |

Formatter dan segmenter berupa fungsi murni yang tidak mengakses filesystem atau mengimpor faster-whisper.

</details>

## Lisensi

Proyek ini menggunakan [lisensi MIT](LICENSE). Anda dapat menggunakan, memodifikasi, dan mendistribusikannya sesuai ketentuan lisensi tersebut.
