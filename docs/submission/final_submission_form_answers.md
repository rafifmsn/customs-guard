# Jawaban Formulir Pengumpulan Akhir (Project Submission Form)

Dokumen ini berisi draf jawaban lengkap dalam Bahasa Indonesia untuk formulir pengumpulan akhir National Hackathon - Project Submission Form.
Teks jawaban di bawah setiap pertanyaan disusun dalam format teks bersih agar dapat langsung disalin dan ditempel ke dalam kolom Google Form.

### Judul Project

Tuliskan nama project yang singkat, jelas, dan menggambarkan solusi yang dikembangkan.

CustomsGuard: Autonomous Trade Compliance & Tariff Discrepancy Engine

### Tema Project

- Healthcare & Wellbeing
  Productivity & Smart Business
  Public Services
  Education & Future of Work
  Financial

Productivity & Smart Business

### Deskripsi Project

- Jelaskan project secara menyeluruh dalam 150-300 kata.
  Pastikan menjelaskan:

* Apa project yang dibuat?
* Masalah apa yang ingin diselesaikan?
* Siapa yang mengalami masalah tersebut?
* Bagaimana solusi bekerja?
* Apa manfaat utama solusi?

CustomsGuard adalah AI Agent otonom yang dirancang untuk mengotomatisasi audit kepatuhan dokumen kepabeanan dan perdagangan internasional, mencegah penahanan kontainer di pelabuhan, serta menghindarkan pelaku usaha dari sanksi denda kepabeanan.

Masalah utama yang diselesaikan adalah lambatnya proses verifikasi manual dokumen commercial invoice dan packing list terhadap 5.612 subpos kode HS (Harmonized System) Indonesia bersumber dari dataset resmi WTO/UNCTAD ITC Market Access Map serta ratusan regulasi izin impor (Lartas) lintas kementerian.
Masalah ini dialami secara langsung oleh praktisi rantai pasok global, perusahaan freight forwarding, Pengusaha Pengurusan Jasa Kepabeanan (PPJK), dan importir yang sering menghadapi penahanan kargo di jalur merah pelabuhan akibat salah klasifikasi tarif atau dokumen izin edar yang belum lengkap.

Solusi ini bekerja dengan mengintegrasikan antarmuka AI conversational agent berbasis IBM Bob dan visual workflow engine IBM Langflow melalui Model Context Protocol (MCP).
Dokumen manifes perdagangan dianalisis secara instan menggunakan pencarian semantik vektor lokal Qdrant terhadap 5.612 data tarif dan regulasi impor.
Sistem secara otomatis mendeteksi diskrepansi kode HS, menghitung kekurangan bea masuk, mendeteksi potensi restitusi lebih bayar tarif, memverifikasi izin edar wajib (SDPPI Kemkominfo, Alkes Kemenkes, BPOM), dan memodelkan eksposur penahanan kontainer berbasis tarif resmi CMA CGM Indonesia (5 free days dan day-slabs progresif dengan standar 40ft Dry).
Berkas audit resmi diekspor otomatis dalam format Markdown dan JSON, serta mengirimkan email darurat via Mailpit SMTP saat terdeteksi risiko tinggi.

Manfaat utama CustomsGuard adalah memangkas waktu verifikasi dokumen dari 4 jam menjadi di bawah 5 detik, menghemat ribuan dolar biaya demurrage kontainer dan sanksi denda administrasi pabean, serta menjamin 100% kedaulatan data komersial karena beroperasi secara lokal on-premise (air-gapped).

### Fitur Utama (Key Features)

- Fitur-fitur utama yang tersedia dan fungsi masing-masing fitur.
- Bagaimana pengguna berinteraksi dengan solusi.
- Bagaimana AI digunakan dalam solusi, termasuk peran IBM Bob dan/atau Langflow jika relevan.

Fitur-fitur Utama yang Tersedia dan Fungsinya:

1. Autonomous Tariff RAG & Discrepancy Auditing: Mencocokkan deskripsi barang komersial secara otonom terhadap 5.612 kode HS Indonesia di database vektor Qdrant untuk mendeteksi salah klasifikasi tarif dan menghitung kekurangan bea masuk secara matematis.
2. Regulatory Permit Verification (Lartas Engine): Mendeteksi regulasi barang larangan atau pembatasan secara otomatis dan memverifikasi izin kementerian wajib (SDPPI Kemkominfo, Izin Edar Kemenkes, BPOM) sebelum kargo sandar di pelabuhan.
3. Carrier Demurrage & Restitution Calculator: Menghitung risiko biaya penahanan kontainer harian dan kumulatif berdasarkan tarif resmi CMA CGM Indonesia (5 hari bebas biaya dan tier progresif per ukuran kontainer), serta mendeteksi hak pengembalian dana (restitusi lebih bayar tarif).
4. Automated Evidence Archiving & Alert Dispatching: Mengekspor berkas audit resmi bertanda waktu dalam format Markdown dan JSON ke direktori lokal, serta mengirimkan email peringatan darurat otomatis via Mailpit SMTP saat kargo terindikasi risiko tinggi.
5. Enterprise Guardrails Sanitization: Menyaring data pribadi (PII) seperti nomor NPWP dan rekening bank serta menangkal manipulasi prompt injection sebelum hasil audit ditampilkan.

Bagaimana Pengguna Berinteraksi dengan Solusi:
Pengguna dapat berinteraksi melalui dua moda fleksibel:

1. Antarmuka Percakapan (Conversational Interface): Petugas berinteraksi secara interaktif melalui IBM Bob Shell CLI atau Desktop menggunakan bahasa alami atau perintah skill $audit-shipment dengan menyertakan ID pengapalan atau teks invoice komersial.
2. Dasbor Web Mandiri (Streamlit Dashboard): Petugas mengunggah file invoice (JSON, DOCX, TXT) atau memilih sampel shipment untuk melihat ringkasan visual, kartu metrik kepatuhan, tabel komparasi tarif, dan tautan arsip berkas audit secara real-time.

Bagaimana AI Digunakan dalam Solusi:

1. Peran IBM Bob: Bertindak sebagai MCP Client cerdas yang membaca persona kepabeanan pada AGENTS.md, menerima input bahasa alami pengguna, memicu skill audit kepatuhan, dan menyajikan ringkasan eksekutif secara interaktif.
2. Peran IBM Langflow: Bertindak sebagai backend eksekusi visual dan MCP Server.
   Langflow mengorkestrasi alur data antara Chat Input, model LLM untuk penalaran kontekstual, Custom Component Python untuk pencarian vektor Qdrant dan kalkulasi tarif deterministik, Guardrails untuk sanitasi data, dan Chat Output.
3. Penerapan AI: Model embedding (all-minilm 384-dimensi) digunakan untuk pencarian semantik vektor di Qdrant, sementara LLM (Ollama Qwen 2.5 3B) digunakan untuk ekstraksi dokumen dan penalaran kepatuhan, dipadukan dengan aturan deterministik agar kalkulasi finansial 100% akurat tanpa halusinasi angka.

### Impact & Business Potential

Jelaskan manfaat dan dampak yang diharapkan bagi target pengguna dan peluang keberlanjutan atau model bisnis jika relevan.

Manfaat dan Dampak bagi Target Pengguna:

1. Efisiensi Operasional: Memangkas durasi verifikasi dokumen dari 2 hingga 4 jam menjadi di bawah 5 detik per invoice (efisiensi waktu lebih dari 98%), memungkinkan satu petugas memproses puluhan pengapalan sekaligus.
2. Pencegahan Kerugian Finansial: Menghindarkan pembengkakan biaya demurrage kontainer di pelabuhan (menghemat USD 101 per hari per kontainer 40ft pasca-free time, atau USD 2.020 pada penahanan 4 kontainer selama 5 hari).
3. Mitigasi Risiko Hukum dan Denda: Menghindarkan importir dari sanksi administrasi pabean sebesar 100% hingga 1000% dari kekurangan pembayaran bea masuk sesuai Undang-Undang Kepabeanan Indonesia.
4. Pemulihan Arus Kas (Restitusi): Menemukan peluang pengembalian bea masuk akibat kelebihan bayar tarif yang selama ini terlewat oleh audit manual.
5. Keamanan dan Kedaulatan Data: Arsitektur 100% on-premise menjamin data harga beli pabrik dan identitas pemasok tidak keluar ke server pihak ketiga.

Peluang Keberlanjutan dan Model Bisnis:

1. Model Lisensi B2B SaaS On-Premise: Berlangganan tahunan untuk perusahaan freight forwarding, PPJK, dan importir enterprise dengan tier berbasis volume kontainer atau jumlah seat pengguna.
2. Efisiensi Biaya Operasional: Berjalan secara mandiri menggunakan kontainer Docker lokal dengan biaya infrastruktur sekitar USD 980 per tahun, jauh lebih ekonomis dibandingkan langganan API komersial cloud yang mencapai USD 7.500 lebih per tahun.
3. Potensi Pasar yang Besar: Pasar jasa kepabeanan di Indonesia bernilai USD 2,23 miliar pada 2025 dan diproyeksikan mencapai USD 3,32 miliar pada 2031 (Mordor Intelligence) dengan pertumbuhan segmen digital 15,34% CAGR, seiring mandatori sistem CEISA 4.0 Bea Cukai dan Single Submission (SSm).
4. Integrasi Enterprise: Peluang integrasi langsung melalui webhook atau REST API ke sistem ERP logistik enterprise (seperti SAP, CargoWise) dan portal pertukaran data kepabeanan nasional.

### Bukti Validasi Pengguna (Evidence of User Validation)

Jelaskan bagaimana tim telah melakukan validasi terhadap masalah yang diangkat dan/atau solusi yang dikembangkan kepada calon pengguna atau pihak terkait.
Sertakan informasi berikut jika tersedia:

- Metode validasi yang digunakan, seperti wawancara, survei, observasi, atau pengujian prototype.
- Jumlah dan karakteristik pengguna atau responden yang dilibatkan.
- Temuan utama atau umpan balik yang diperoleh.
- Bagaimana hasil validasi memengaruhi solusi atau rencana pengembangan project.
- Boleh tautkan juga link to drive jika ada dokumentasi (opsional)

Metode Validasi:
Wawancara semi-terstruktur untuk menguji alur audit invoice, kalkulasi tarif, serta kegunaan antarmuka.

Jumlah dan Karakteristik Responden:
Melibatkan 3 responden:

1. Responden 1: Karyawan swasta data analyst dengan latar belakang Machine Learning dan nalar kritis.
2. Responden 2: Mahasiswa IT yang peka terhadap estetika visual antarmuka dan berlatar belakang Machine Learning.
3. Responden 3: Mahasiswi IT pengembang web yang memahami konteks operasional logistik pelabuhan (demurrage dan detention).

Temuan Utama dan Umpan Balik:

1. Input Data: Kebutuhan integrasi OCR (EasyOCR atau PaddleOCR) agar invoice fisik atau gambar dapat diubah otomatis menjadi format JSON terstruktur.
2. Desain Antarmuka: Konsep minimalis dinilai sudah tepat, disarankan menjaga tampilan tetap bersih tanpa ornamen berlebihan yang terkesan artifisial (AI slop).
3. Keterbacaan dan Tema: Teks laporan audit dinilai terlalu padat sehingga perlu penyajian yang lebih visual, serta usulan opsi Light Mode selain tema gelap.

Pengaruh Hasil Validasi terhadap Solusi dan Rencana Pengembangan:

1. Penyempurnaan Visual Terimplementasi: Mengadopsi masukan Responden 2 dan 3, dasbor antarmuka saat ini telah menerapkan kartu metrik ringkas, badge status kepatuhan, dan tabel komparasi tarif terstruktur sehingga hasil audit langsung terbaca tanpa beban teks padat, dengan tetap mempertahankan estetika minimalis bebas AI slop.
2. Keputusan Terkait Light Mode: Permintaan tema terang (Light Mode) saat ini diputuskan untuk ditiadakan guna menjaga konsistensi visual, meskipun secara teknis konfigurasi tema Streamlit sangat fleksibel dan memungkinkan untuk diaktifkan sewaktu-waktu.
3. Rencana Pengembangan (Roadmap OCR): Masukan Responden 1 mengenai ekstraksi dokumen pindaian dimasukkan ke dalam roadmap pengembangan berikutnya untuk mengintegrasikan pipeline OCR multimodal (EasyOCR atau PaddleOCR) pada alur ingest.

### Perkembangan dan Status Project (Project Development & Current Progress)

Jelaskan perkembangan project sejak tahap preliminary hingga tahap semifinal.
Uraikan:

- Pengembangan atau perbaikan yang telah dilakukan.
- Fitur yang sudah tersedia dan dapat digunakan.
- Status prototype saat ini.
- Keterbatasan yang masih ditemukan serta rencana perbaikan selanjutnya.

Pengembangan dan Perbaikan yang Dilakukan (Preliminary ke Semifinal):

1. Migrasi dan Peningkatan Mesin Pencarian Tarif: Dari pencarian leksikal dasar menjadi dense semantic vector search (all-minilm 384-dimensi) di Qdrant mencakup seluruh 5.612 subpos HS Indonesia dari dataset resmi WTO/UNCTAD ITC MAcMap.
2. Penyempurnaan Model Finansial Demurrage: Menggantikan estimasi flat-rate dengan matriks progresif resmi CMA CGM Indonesia (efektif 1 Juli 2026) dengan perhitungan free days, slab harian per jenis kontainer (Dry vs Reefer, ukuran 20ft/40ft/45ft), dan graceful default 40ft Dry Standard.
3. Peningkatan Ketahanan Pipeline MCP: Menambahkan penanganan input polimorfik (string JSON, dict objek, atau mixed prompt) pada tools Langflow dan agen IBM Bob untuk mencegah kegagalan validasi skema.
4. Peningkatan Stabilitas Eksekusi: Mengoptimalkan timeout embedding lokal dari 2.0s menjadi 5.0s untuk mengatasi cold-start GPU/CPU dan menjamin konsistensi hasil pencarian.
5. Pengujian Empiris Menyeluruh: Mengimplementasikan automated test suite (36 unit dan integrasi test lulus 100%), load test k6 dengan performa p95 = 36.93 ms, serta benchmark akurasi klasifikasi pada 50 sampel ground truth.

Fitur yang Sudah Tersedia dan Dapat Digunakan:

1. Audit kepatuhan manifes pabean otomatis via REST API FastAPI, Web Dashboard Streamlit, dan IBM Bob Shell CLI.
2. Kalkulasi otomatis kekurangan bea masuk dan deteksi peluang restitusi lebih bayar.
3. Verifikasi izin edar kementerian (Lartas SDPPI, Kemenkes, BPOM).
4. Kalkulasi demurrage progresif CMA CGM Indonesia.
5. Ekspor berkas audit Markdown dan JSON ke direktori penyimpanan lokal.
6. Notifikasi email darurat otomatis via Mailpit SMTP.
7. Sanitasi data pribadi (PII) dan proteksi prompt injection melalui Guardrails.

Status Prototype Saat Ini:
Status prototype saat ini berada pada tahap Functional Working Prototype (TRL 6-7).
Seluruh microservices backend (Qdrant, Langflow, PostgreSQL, Mailpit, FastAPI, Streamlit) telah terintegrasi penuh dan berjalan stabil dalam kontainer Docker lokal.
Sistem telah diverifikasi melalui 36 automated unit dan integration test pada root repository dengan tingkat kelulusan 100%.

Keterbatasan yang Masih Ditemukan dan Rencana Perbaikan:

1. Keterbatasan: Pada agen percakapan berbasis model lokal ringan (seperti qwen2.5:3b), model terkadang menghasilkan teks analisis yang akurat tetapi melewatkan pemanggilan tool sekunder secara mandiri (seperti dispatch email alert) karena limitasi multi-step tool calling pada model 3B.
2. Keterbatasan: Input saat ini diutamakan untuk dokumen digital berbasis teks dan JSON terstruktur.
   Dokumen pindaian fisik (scanned PDF atau foto dokumen) belum didukung secara langsung.
3. Rencana Perbaikan: Menambahkan modul Document OCR multimodal (seperti Docling) untuk ekstraksi otomatis dari berkas PDF atau gambar pindaian Bill of Lading dan invoice fisik.
4. Rencana Perbaikan: Memperluas database tarif untuk mencakup skema Free Trade Agreement (ATIGA, ACFTA) dan integrasi verifikasi Surat Keterangan Asal (Form D / Form E).
5. Rencana Perbaikan: Menambahkan adapter API untuk maskapai pelayaran global lainnya seperti Maersk, MSC, Hapag-Lloyd, dan ONE.

### Product Pitching Video (End-to-End Journey)

insert youtube video link here (7 mins max)

https://youtu.be/zaiTPeZeazU

### Product Demo Project (End-to-End Journey)

insert youtube video link here (2 mins max)

https://youtu.be/OBHL-cSZEY8

### Silahkan upload slides presentasi (Pitching Deck) dalam format PDF

Upload 1 supported file.
Max 10 MB.

Berkas presentasi telah disiapkan dalam format PDF:
CustomsGuard.pdf (tersedia pada folder docs/submission/CustomsGuard.pdf dengan ukuran 1.3 MB, memenuhi batas maksimal 10 MB).

### Link Prototype / documentation

Cantumkan tautan repository GitHub yang berisi source code dan/atau dokumentasi teknis project

https://github.com/rafifmsn/customs-guard
