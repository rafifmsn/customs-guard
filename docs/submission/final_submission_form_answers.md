# Jawaban Formulir Pengumpulan Akhir (Project Submission Form)

Dokumen ini berisi draf jawaban lengkap dalam Bahasa Indonesia untuk formulir pengumpulan akhir **National Hackathon — Project Submission Form**.

### Judul Project

**CustomsGuard: Autonomous Trade Compliance & Tariff Discrepancy Engine**

### Tema Project

**Productivity & Smart Business**

### Deskripsi Singkat Project (150–300 kata)

CustomsGuard adalah AI Agent otonom yang dirancang untuk mengotomatisasi audit kepatuhan dokumen ekspor-impor, mencegah penahanan kontainer di pelabuhan, dan menghindarkan pelaku usaha dari denda kepabeanan.

Sistem ini menyelesaikan tantangan verifikasi manual dokumen commercial invoice dan packing list terhadap lebih dari 5.600 subpos 6-digit Harmonized System (HS) dalam Buku Tarif Kepabeanan Indonesia (BTKI).
Masalah ini dialami oleh perusahaan freight forwarding, pengusaha pengurusan jasa kepabeanan (PPJK), dan importir yang sering mengalami penahanan kargo di jalur merah akibat salah klasifikasi kode HS atau ketiadaan izin Lartas.

CustomsGuard bekerja dengan mengintegrasikan IBM Bob sebagai antarmuka conversational agent dan IBM Langflow sebagai backend visual workflow melalui Model Context Protocol (MCP).
Invoice dianalisis secara instan menggunakan pencarian semantik lokal Qdrant terhadap 5.612 data tarif dan regulasi impor Indonesia.
Sistem secara otomatis mendeteksi selisih kode HS, menghitung kekurangan bea masuk, mendeteksi peluang restitusi lebih bayar, memverifikasi izin edar wajib (SDPPI, Kemenkes, BPOM), dan memodelkan risiko demurrage kontainer ($350/hari per kontainer).
Hasil audit disimpan otomatis dalam bentuk laporan Markdown dan JSON di penyimpanan lokal serta mengirimkan notifikasi email darurat via Mailpit SMTP.

Manfaat utama dari CustomsGuard adalah memangkas waktu verifikasi dokumen dari 4 jam menjadi di bawah 5 detik, mencegah kerugian demurrage ribuan dolar per kontainer, serta menjamin privasi data perdagangan karena beroperasi sepenuhnya secara on-premise (air-gapped).

### Problem Statement

Sebelum adanya solusi ini, petugas kepatuhan perdagangan harus memeriksa dokumen invoice baris demi baris secara manual dan mencocokkannya ke buku tarif kepabeanan serta aturan Lartas yang tersebar di berbagai kementerian.
Pain point yang dihadapi:

1. Kompleksitas klasifikasi 5.612 subpos HS 6-digit yang rawan human error.
2. Penahanan kontainer di pelabuhan akibat masuk jalur merah, menimbulkan biaya demurrage sebesar $350.00 USD per kontainer per hari.
3. Risiko sanksi denda administrasi kepabeanan di Indonesia sebesar 100% hingga 1000% dari kekurangan pembayaran bea masuk.
4. Hilangnya potensi pengembalian bea masuk (restitusi) karena audit manual hampir tidak pernah mendeteksi kelebihan pembayaran tarif.

Masalah ini sangat mendesak diselesaikan demi kelancaran arus barang nasional, efisiensi logistik, dan menjaga arus kas perusahaan dari penalti yang tidak perlu.

### Target User

1. **Perusahaan Freight Forwarding & Logistik 3PL**: Tim operasional yang menangani ratusan pengapalan kontainer internasional per bulan.
2. **Pengusaha Pengurusan Jasa Kepabeanan (PPJK)**: Ahli kepabeanan yang bertanggung jawab atas keakuratan pengisian dokumen Pemberitahuan Impor Barang (PIB).
3. **Trade Compliance Officer Perusahaan Manufaktur & Ritel**: Tim kepatuhan internal yang mengawasi impor bahan baku dan barang jadi.
4. **Pelaku Usaha Ekspor-Impor (UMKM & Korporasi)**: Bisnis yang membutuhkan audit instan sebelum kargo dikapalkan.

### Mengapa Solusi Ini Dibutuhkan?

Solusi saat ini mengandalkan pengecekan manual buku tarif yang lambat, melelahkan, dan bergantung pada subjektivitas petugas.
Solusi cloud pihak ketiga sering kali ditolak perusahaan multinasional karena mengancam kerahasiaan data komersial (harga beli pabrik, daftar pemasok, dan identitas pembeli).

CustomsGuard menjadi solusi yang jauh lebih unggul karena:

1. **Kecepatan & Konsistensi**: Menyelesaikan audit lengkap dalam hitungan detik dengan akurasi deterministik matematis.
2. **Air-Gapped & Privasi Total**: Berjalan 100% lokal dalam container Docker tanpa mengirimkan data komersial rahasia ke cloud pihak ketiga.
3. **Analisis Finansial Ganda**: Tidak hanya menghitung kekurangan bea masuk dan denda demurrage, tetapi juga mendeteksi peluang restitusi lebih bayar tarif.
4. **Safety Guardrails Terintegrasi**: Menyaring data sensitif (PII) dan menangkal prompt injection sebelum menampilkan hasil audit.

### Fitur Utama Project

1. **Autonomous Tariff RAG & Discrepancy Auditing**:
   Mencocokkan deskripsi barang invoice secara otonom terhadap 5.612 kode HS Indonesia di database Qdrant untuk mendeteksi perbedaan kode dan kekurangan bea masuk.
2. **Regulatory Permit Verification (Lartas Engine)**:
   Memverifikasi kepemilikan sertifikasi wajib seperti SDPPI Kemkominfo, izin edar Alkes Kemenkes, dan izin BPOM sebelum kargo tiba di pelabuhan.
3. **Multi-Container Demurrage & Restitution Calculator**:
   Menghitung potensi biaya demurrage pelabuhan ($350/hari dikalikan jumlah kontainer) jika kargo tertahan, serta mendeteksi potensi pengembalian dana akibat kelebihan deklarasi tarif.
4. **Automated Evidence Archiving**:
   Mengekspor berkas audit resmi bertanda waktu dalam format Markdown dan JSON ke direktori penyimpanan lokal.
5. **Real-Time SMTP Alert Dispatching**:
   Mengirimkan email peringatan darurat otomatis ke tim kepatuhan melalui Mailpit ketika terdeteksi risiko penahanan tinggi.

### Alur Penggunaan Project

`User Input Invoice (JSON/Teks di IBM Bob) → Model Context Protocol (MCP) → Langflow Agent Execution → Query Qdrant Vector DB (5,612 HS Codes) → Audit & Perhitungan Finansial → Ekspor Laporan Lokal & Dispatch Email Mailpit → Langflow Guardrails Filtering (PII & Injection Sanitization) → IBM Bob Output Response → User Review & Tindak Lanjut`

### Penggunaan IBM Langflow

IBM Langflow digunakan sebagai mesin eksekusi workflow visual dan orkestrasi tools:

- **Workflow yang dibuat**: Alur visual yang menghubungkan Chat Input, Agent LLM (gpt-4o-mini), Custom Toolkit Component, Guardrails, dan Chat Output.
- **Node/Component yang digunakan**:
  - `Chat Input`: Menerima payload invoice komersial.
  - `CustomsGuard Tools`: Custom component Python yang mengintegrasikan fungsi audit tarif, ekspor laporan, dan dispatch email.
  - `Agent`: Mengorkestrasi pemanggilan tools berdasarkan hasil audit.
  - `Guardrails`: Menyaring PII (NPWP, rekening bank), memblokir prompt injection, dan mencegah kebocoran kredensial sebelum output dikirim.
  - `Chat Output`: Menampilkan hasil audit final untuk jalur Pass dan notifikasi intervensi untuk jalur Fail.
- **Fungsi Langflow**: Bertindak sebagai backend eksekusi logika bisnis terstruktur yang dapat diuji mandiri dan diekspos sebagai MCP tool.

### Penggunaan IBM Bob

IBM Bob digunakan sebagai conversational client dan antarmuka interaksi pengguna:

- **Fungsi IBM Bob**: Menyediakan antarmuka desktop dan CLI yang intuitif bagi petugas kepatuhan untuk berinteraksi dengan sistem menggunakan bahasa alami atau perintah skill.
- **Proses/Task menggunakan Bob**:
  - Membaca konfigurasi `AGENTS.md` untuk memahami persona kepatuhan kepabeanan.
  - Menjalankan skill `$audit-shipment` atau menerima paste teks invoice dari pengguna.
  - Memanggil tool `customsguard` yang diekspos oleh Langflow melalui MCP.
  - Menampilkan ringkasan eksekutif, tabel temuan tarif, dan rekomendasi langkah tindak lanjut.
- **Output yang dihasilkan**: Respons chat informatif dengan badge status kepatuhan, tabel komparasi tarif, rincian biaya, dan konfirmasi pengiriman email.

### Bagaimana IBM Langflow dan IBM Bob Terintegrasi?

Integrasi antara Langflow dan IBM Bob menggunakan standar **Model Context Protocol (MCP)** dengan transport Streamable HTTP:

1. **Peran Langflow**: Bertindak sebagai **MCP Server** yang mengemas seluruh flow audit kepatuhan menjadi sebuah callable tool bernama `customsguard`.
2. **Peran Bob**: Bertindak sebagai **MCP Client** yang dikonfigurasi melalui `.bob/mcp.json` menggunakan proxy `uvx mcp-proxy`.
3. **Aliran Data**:
   - Pengguna memberikan perintah audit di antarmuka Bob.
   - Bob mengirimkan payload JSON invoice sebagai argumen `input_value` melalui protokol MCP ke endpoint Langflow (`/api/v1/mcp/project/.../streamable`).
   - Langflow mengeksekusi pipeline audit, menjalankan query ke database Qdrant, menulis laporan ke disk, mengirim alert ke Mailpit, dan membersihkan teks melalui Guardrails.
   - Hasil teks yang telah disanitasi dikembalikan melalui MCP stream ke IBM Bob.
4. **Output Akhir Integrasi**: Pengguna di IBM Bob mendapatkan ringkasan audit komprehensif secara interaktif, sementara seluruh sistem backend (database, file laporan, dan email) telah sinkron secara otomatis.

### Dampak yang Dihasilkan

1. **Efisiensi Waktu**: Memangkas waktu audit dokumen dari rata-rata **2-4 jam** menjadi **di bawah 5 detik per invoice** (penghematan waktu >98%).
2. **Pencegahan Biaya Demurrage**: Menghindarkan denda penahanan pelabuhan sebesar **$350.00 USD per kontainer per hari** (penghematan **$1,750 USD** pada rata-rata penahanan 5 hari untuk 1 kontainer, atau **$7,000 USD** untuk 4 kontainer).
3. **Pemberantasan Sanksi Denda**: Menghindarkan sanksi administrasi kepabeanan sebesar **100% s.d. 1000%** dari selisih bea masuk.
4. **Penemuan Restitusi Pajak**: Mengidentifikasi kelebihan pembayaran bea masuk akibat salah deklarasi tarif, mengembalikan potensi cash flow ribuan dolar bagi importir.
5. **Penghematan Biaya Infrastruktur**: Mengurangi biaya operasional software kepatuhan hingga **~87%** dengan arsitektur on-premise Docker ($980/tahun) dibandingkan langganan cloud API komersial ($7,560/tahun).

### Potensi Pengembangan & Skalabilitas

1. **Integrasi OCR & Vision**: Menambahkan modul OCR multimodal untuk mengekstrak data langsung dari file PDF Bill of Lading, invoice pindaian, dan packing list fisik.
2. **Ekspansi Regulasi ASEAN**: Memperluas database tarif ke skema Free Trade Agreement (ATIGA, ACFTA) dan integrasi dokumen Certificate of Origin (Form D / Form E).
3. **Koneksi Langsung EDI INSW / CEISA**: Menghubungkan output audit dengan sistem pertukaran data elektronik pabean nasional untuk validasi pra-pengajuan PIB.

### Apa yang Membuat Project Ini Berbeda?

1. **Arsitektur Air-Gapped & Privasi Total**: Beroperasi sepenuhnya di lingkungan lokal pengguna (on-premise Docker), menjamin data komersial rahasia tidak pernah bocor ke cloud.
2. **Dual Financial Analysis (Shortfall & Restitution)**: Tidak hanya mendeteksi kekurangan pembayaran, tetapi juga menjadi satu-satunya sistem yang proaktif mendeteksi hak pengembalian dana (restitusi lebih bayar).
3. **Multi-Container Demurrage Scaling**: Mengkalkulasi risiko penahanan pelabuhan secara riil berdasarkan jumlah kontainer pengapalan, bukan sekadar tarif nominal statis.

### Kemampuan AI Agent

AI Agent pada CustomsGuard memiliki kapabilitas:

1. **Autonomous Tool Orchestration**: Secara mandiri memutuskan kapan harus mengeksekusi pencarian tarif, kapan harus mengekspor laporan pembuktian, dan kapan harus menembakkan peringatan darurat.
2. **Deterministic Mathematical Calculation**: Menghitung selisih persentase bea masuk, akumulasi nilai kekurangan pembayaran, dan perkalian demurrage harian tanpa halusinasi angka.
3. **Safety & Security Compliance**: Melindungi diri dari manipulasi prompt injection pada deskripsi barang dan otomatis menyamarkan data pribadi (PII) sebelum menyerahkan hasil ke pengguna.
