# Jawaban Formulir Ideasi & Progres Hackathon

Dokumen ini berisi draf jawaban lengkap dalam Bahasa Indonesia untuk formulir pengumpulan ide/progres hackathon.

### 1. Tuliskan ide project hackathon kamu

_Ceritakan secara singkat ide project yang ingin kamu kembangkan, termasuk masalah yang ingin diselesaikan dan solusi yang ditawarkan._

**Jawaban**:
CustomsGuard adalah AI Agent otonom untuk audit kepatuhan ekspor-impor dan deteksi anomali tarif bea cukai secara on-premise (air-gapped).

Masalah yang diselesaikan:
Proses verifikasi dokumen pengapalan (commercial invoice dan packing list) terhadap lebih dari 5.600 subpos 6-digit Harmonized System (HS) di Buku Tarif Kepabeanan Indonesia (BTKI) saat ini masih dilakukan secara manual dan lambat.
Kesalahan klasifikasi tarif memicu penahanan kontainer di jalur merah pelabuhan dengan biaya demurrage mencapai $350 USD per kontainer per hari, serta ancaman denda administrasi kepabeanan sebesar 100% hingga 1000% dari kekurangan bea masuk.

Solusi yang ditawarkan:
CustomsGuard mengotomatisasi audit kepatuhan dengan menghubungkan IBM Bob sebagai conversational orchestrator dengan workflow eksekusi Langflow melalui Model Context Protocol (MCP).
Sistem secara instan mencocokkan deskripsi barang dengan database lokal Qdrant berisi 5.612 subpos tarif HS-6 Indonesia, menghitung selisih bea masuk dan peluang restitusi lebih bayar, memverifikasi izin edar regulasi (Lartas seperti sertifikasi SDPPI Kemkominfo dan izin edar Kemenkes), memodelkan risiko penahanan kontainer pelabuhan, mengarsipkan laporan resmi (Markdown dan JSON) ke penyimpanan lokal, serta mengirimkan notifikasi peringatan real-time via SMTP Mailpit.

### 2. Tema Project

_Pilihan: Healthcare & Wellbeing, Productivity & Smart Business, Public Services, Education & Future of Work, Financial_

**Pilihan**:
**Productivity & Smart Business**

### 3. Tuliskan kesulitan yang kamu alami di dalam kelas/ketika membuat project

**Jawaban**:

1. Menyelaraskan kontrak komunikasi data antara runtime eksekusi Langflow dengan antarmuka Model Context Protocol (MCP) pada IBM Bob, khususnya memastikan component toolkit kustom menghasilkan objek callable Tool yang kompatibel secara native dengan Agent LangChain tanpa memodifikasi core component.
2. Mengatasi dependensi environment host lokal (seperti instalasi binary uvx dan konfigurasi transport streamable HTTP) agar IBM Bob dapat mengenali dan menjalankan tool kustom dari Langflow secara stabil dan deterministik.
