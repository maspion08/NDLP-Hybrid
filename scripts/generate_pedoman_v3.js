/**
 * Validasi_Pedoman_Anotasi_TA_Arga_v3.docx generator
 *
 * Perubahan besar dari v2:
 *  - Tool: Doccano/Label-Studio-CLI -> HumanSignal (labelstud.io) dengan setup Overlap 100%, minimal 2 anotator
 *  - Metrik IAA: DIPERLUAS jadi tiga komplementer (Span-level pairwise F1 sebagai UTAMA,
 *    token-level Cohen's Kappa tanpa "O" sebagai pelengkap, Gwet's AC1 sebagai paradox-resistant)
 *  - Section baru: prosedur adjudikasi formal bila kesepakatan di bawah target
 *  - Section E.4/F: aturan disambiguasi JABATAN vs nama institusi diperkuat & dipisah eksplisit
 *  - Section G: ditambah tahap kalibrasi (5-10 sampel) sebelum 200 sampel penuh
 *  - Section H: contoh perintah diganti ke setup HumanSignal (Cloud Trial / Community OSS)
 *  - Section K: referensi tambahan (Hripcsak & Rothschild 2005; Gwet 2008; Feinstein & Cicchetti 1990;
 *    Tjong Kim Sang & De Meulder 2003 untuk seqeval; Peraturan Pemerintah 40/2019 untuk NIK)
 *
 * Run: node generate.js
 * Output: Validasi_Pedoman_Anotasi_TA_Arga_v3.docx
 */

const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  ShadingType,
  Header,
  Footer,
  PageNumber,
  PageBreak,
  LevelFormat,
  convertInchesToTwip,
  TabStopType,
  TabStopPosition,
} = require("docx");
const fs = require("fs");

// ────────────────────── Konstanta gaya ──────────────────────
const FONT = "Times New Roman";
const SIZE = 24; // 12pt
const SIZE_SMALL = 22; // 11pt
const SIZE_H1 = 28; // 14pt
const SIZE_H2 = 26; // 13pt

const NAVY = "1F3864";
const NAVY_LIGHT = "D9E2F3";
const ACCENT_YELLOW = "FFF2CC";
const ACCENT_GREEN = "E2EFDA";
const ACCENT_RED = "FCE4D6";
const GRAY_LIGHT = "F2F2F2";

// ────────────────────── Helper konten ──────────────────────
const tnr = (text, opts = {}) =>
  new TextRun({ text, font: FONT, size: SIZE, ...opts });
const tnrB = (text, opts = {}) => tnr(text, { ...opts, bold: true });
const tnrI = (text, opts = {}) => tnr(text, { ...opts, italics: true });

const p = (text, opts = {}) =>
  new Paragraph({
    children: Array.isArray(text) ? text : [tnr(text)],
    alignment: opts.alignment || AlignmentType.JUSTIFIED,
    spacing: { before: opts.before || 0, after: opts.after || 120, line: 360 },
    ...opts,
  });

const h1 = (text) =>
  new Paragraph({
    children: [
      new TextRun({ text, font: FONT, size: SIZE_H1, bold: true, color: NAVY }),
    ],
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 200 },
  });

const h2 = (text) =>
  new Paragraph({
    children: [
      new TextRun({ text, font: FONT, size: SIZE_H2, bold: true, color: NAVY }),
    ],
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 140 },
  });

const numberedP = (text, ref = "list-main") =>
  new Paragraph({
    children: Array.isArray(text) ? text : [tnr(text)],
    numbering: { reference: ref, level: 0 },
    spacing: { before: 40, after: 60, line: 340 },
    alignment: AlignmentType.JUSTIFIED,
  });

const bulletP = (text, ref = "bullet-main") =>
  new Paragraph({
    children: Array.isArray(text) ? text : [tnr(text)],
    numbering: { reference: ref, level: 0 },
    spacing: { before: 40, after: 60, line: 340 },
    alignment: AlignmentType.JUSTIFIED,
  });

const code = (text) =>
  new Paragraph({
    children: [new TextRun({ text, font: "Consolas", size: SIZE_SMALL })],
    shading: { type: ShadingType.CLEAR, color: "auto", fill: GRAY_LIGHT },
    border: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" },
    },
    spacing: { before: 40, after: 40 },
  });

// ────────────────────── Helper tabel ──────────────────────
const cellStd = (children, opts = {}) =>
  new TableCell({
    children: Array.isArray(children) ? children : [p(children)],
    width: { size: opts.width || 2000, type: WidthType.DXA },
    shading: opts.fill
      ? { type: ShadingType.CLEAR, color: "auto", fill: opts.fill }
      : undefined,
    verticalAlign: opts.valign || "top",
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
  });

const cellH = (text, width, fill = NAVY) =>
  cellStd(
    [
      new Paragraph({
        children: [
          new TextRun({
            text,
            bold: true,
            color: "FFFFFF",
            font: FONT,
            size: SIZE,
          }),
        ],
        alignment: AlignmentType.CENTER,
      }),
    ],
    { width, fill },
  );

const stdTable = (headers, rows, columnWidths) =>
  new Table({
    width: { size: 9600, type: WidthType.DXA },
    columnWidths,
    rows: [
      new TableRow({
        children: headers.map((h, i) => cellH(h, columnWidths[i])),
        tableHeader: true,
      }),
      ...rows.map(
        (row) =>
          new TableRow({
            children: row.map((c, i) =>
              cellStd(
                typeof c === "string"
                  ? [p(c, { after: 0 })]
                  : Array.isArray(c)
                    ? c
                    : [p(c, { after: 0 })],
                { width: columnWidths[i] },
              ),
            ),
          }),
      ),
    ],
  });

// ────────────────────── Cover ──────────────────────
const cover = [
  new Paragraph({
    children: [
      new TextRun({
        text: "PEDOMAN ANOTASI",
        font: FONT,
        size: 40,
        bold: true,
        color: NAVY,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { before: 1200, after: 200 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "INTER-ANNOTATOR AGREEMENT (IAA)",
        font: FONT,
        size: 32,
        bold: true,
        color: NAVY,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 100 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Versi 3.0 (Revisi Metrik dan Tool)",
        font: FONT,
        size: 22,
        italics: true,
        color: "595959",
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 800 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Validasi Reliabilitas Anotasi Held-Out Naturalistic Test Set",
        font: FONT,
        size: 26,
        bold: true,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
  }),
  new Paragraph({
    children: [
      new TextRun({ text: "Penelitian Tugas Akhir", font: FONT, size: 24 }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 100 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Pengembangan Sistem NDLP dengan Metode Hibrida Rule-Based dan Machine Learning pada Data Kependudukan",
        font: FONT,
        size: 24,
        italics: true,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 1200 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Peneliti:", font: FONT, size: 24 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Arga Ariyuda Avian",
        font: FONT,
        size: 24,
        bold: true,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "NIM: 2221101774", font: FONT, size: 22 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Program Studi Rekayasa Keamanan Siber",
        font: FONT,
        size: 22,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Politeknik Siber dan Sandi Negara (PoltekSSN)",
        font: FONT,
        size: 22,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
  }),
  new Paragraph({
    children: [
      new TextRun({ text: "Dosen Pembimbing:", font: FONT, size: 22 }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Tiyas Yulita, M.Si.",
        font: FONT,
        size: 22,
        bold: true,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── A. Landasan ──────────────────────
const sectionA = [
  h1("A. Landasan Panduan Anotasi"),
  p(
    "Dokumen ini menyusun pedoman baku pelaksanaan anotasi manual pada held-out naturalistic test set penelitian ini, guna memperoleh reliabilitas anotasi (ground truth) yang dapat dipertanggungjawabkan secara akademik dan menjadi dasar validitas evaluasi model deteksi PII.",
  ),
  p([
    tnr("Pedoman ini disusun mengacu pada tiga fondasi utama: "),
    tnrB("(1)"),
    tnr(
      " standar skema pelabelan sekuensial CoNLL-2003 (Tjong Kim Sang & De Meulder, 2003) yang menjadi standar de-facto untuk tugas ",
    ),
    tnrI("Named Entity Recognition"),
    tnr(" (NER); "),
    tnrB("(2)"),
    tnr(" praktik pengukuran "),
    tnrI("Inter-Annotator Agreement"),
    tnr(
      " (IAA) pada NER yang direkomendasikan literatur (Hripcsak & Rothschild, 2005; Artstein & Poesio, 2008), dengan mempertimbangkan keterbatasan Cohen's Kappa pada distribusi label yang timpang (Feinstein & Cicchetti, 1990; Gwet, 2008); dan ",
    ),
    tnrB("(3)"),
    tnr(
      " regulasi Indonesia terkait perlindungan data pribadi (UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi) dan tata kelola NIK (PP No. 40 Tahun 2019; Permendagri No. 137 Tahun 2017).",
    ),
  ]),
  p([
    tnrB("Ringkasan Perubahan dari Versi 2 ke Versi 3: "),
    tnr(
      "(a) Perluasan metrik IAA menjadi tiga metrik komplementer (Span-level Pairwise F1 sebagai metrik utama, Cohen's Kappa token-level tanpa label O sebagai pelengkap, dan Gwet's AC1 sebagai metrik ",
    ),
    tnrI("paradox-resistant"),
    tnr(
      "); (b) Perubahan tool anotasi dari Label Studio CLI/Doccano menjadi HumanSignal (labelstud.io) dengan konfigurasi ",
    ),
    tnrB("Overlap of Annotations = 100%, minimum 2 annotator per task"),
    tnr(
      "; (c) Penambahan Bagian G.1 tentang tahap kalibrasi pra-anotasi; (d) Penambahan Bagian I.4 tentang prosedur adjudikasi formal apabila kesepakatan berada di bawah target; (e) Klarifikasi eksplisit aturan disambiguasi JABATAN vs nama institusi pada Bagian E.4 dan Bagian F.",
    ),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── B. Identitas Anotator ──────────────────────
const sectionB = [
  h1("B. Identitas Anotator"),
  h2("B.1 Anotator A (Peneliti)"),
  stdTable(
    ["Atribut", "Rincian"],
    [
      ["Nama Lengkap", "Arga Ariyuda Avian"],
      ["NIM", "2221101774"],
      ["Institusi", "Politeknik Siber dan Sandi Negara (PoltekSSN)"],
      ["Peran", "Peneliti utama sekaligus Anotator A"],
      [
        "Bidang Keahlian",
        [
          p("Rekayasa keamanan siber, khususnya:", { after: 40 }),
          bulletP("Network-based Data Leakage Prevention (NDLP)"),
          bulletP(
            "Named Entity Recognition (NER) untuk PII kependudukan Indonesia",
          ),
          bulletP("Model hibrida rule-based + Conditional Random Fields (CRF)"),
        ],
      ],
    ],
    [2600, 7000],
  ),
  h2("B.2 Anotator B (Independen)"),
  stdTable(
    ["Atribut", "Rincian"],
    [
      ["Nama Lengkap", "Muhammad Abdul Aziz Ghazali, S.T."],
      [
        "Latar Belakang Pendidikan",
        "Alumni Institut Teknologi Bandung (ITB), Program Studi Teknik Informatika",
      ],
      [
        "Bidang Keahlian",
        "Machine Learning (ML), Natural Language Processing (NLP), dan Named Entity Recognition (NER)",
      ],
      [
        "Hubungan dengan Peneliti",
        "Rekan profesional; bertindak sebagai anotator independen tanpa keterlibatan pada tahap desain penelitian, pembangkitan dataset, maupun pelatihan model",
      ],
      [
        "Justifikasi Pemilihan",
        "Ghazali memiliki latar belakang formal Teknik Informatika dari institusi terkemuka dan familiar dengan skema BIO tagging untuk tugas NER, sehingga dinilai kompeten untuk melakukan anotasi entitas PII pada teks berbahasa Indonesia secara mandiri.",
      ],
    ],
    [2600, 7000],
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── C. Ruang Lingkup ──────────────────────
const sectionC = [
  h1("C. Ruang Lingkup dan Tujuan Anotasi"),
  p([
    tnr("Anotasi dilakukan terhadap "),
    tnrB("200 sampel"),
    tnr(" yang dipilih secara "),
    tnrI("stratified random sampling"),
    tnr(" dari "),
    tnrI("held-out naturalistic test set"),
    tnr(
      " dengan SEED=42, merepresentasikan 20% dari total 1.000 sampel held-out. Seluruh sampel mencakup tujuh format payload representatif dari penggunaan PII di dunia nyata.",
    ),
  ]),
  h2("C.1 Lima Entitas PII yang Dianotasi"),
  stdTable(
    ["Label", "Nama Lengkap", "Deskripsi"],
    [
      [
        "NIK",
        "Nomor Induk Kependudukan",
        [
          p(
            "Nomor identitas penduduk Indonesia 16 digit sesuai Permendagri No. 137/2017.",
            { after: 40 },
          ),
          p("Format: PP-KK-CC-DD-MM-YY-NNNN.", { after: 40 }),
          p("Laki-laki: DD = tanggal lahir asli (01–31).", { after: 40 }),
          p("Perempuan: DD = tanggal lahir + 40 (41–71).", { after: 0 }),
        ],
      ],
      [
        "PHONE",
        "Nomor Telepon Indonesia",
        "Nomor telepon dengan prefix +62 atau 0, total 10-13 digit, diawali dengan kode operator (011x, 012x, 013x, 014x, 015x, 08xx).",
      ],
      [
        "NAMA",
        "Nama Lengkap Orang",
        "Nama dapat terdiri dari satu hingga beberapa kata. Gelar akademik (S.Kom., M.Si., dr., dll.) dan gelar kebangsawanan yang berdiri sendiri tidak termasuk dalam anotasi.",
      ],
      [
        "JABATAN",
        "Jabatan Formal",
        "Jabatan resmi dalam struktur organisasi pemerintahan (Camat, Lurah, Kepala Dinas, Gubernur, dll.) maupun swasta/akademik (Direktur, Manajer, CEO, Dosen, Rektor, dll.). Nama institusi (Dinas Pendidikan, ITB, PoltekSSN) BUKAN JABATAN — lihat Bagian E.4 dan Bagian F.",
      ],
      [
        "LOKASI",
        "Wilayah Geografis Indonesia",
        'Nama wilayah geografis Indonesia: provinsi, kabupaten, kota, kecamatan, kelurahan/desa, nama jalan. Kata "Kota" yang berdiri sendiri tanpa nama wilayah TIDAK dianotasi sebagai LOKASI.',
      ],
    ],
    [1400, 2600, 5600],
  ),
  h2("C.2 Tujuh Format Payload Dataset"),
  stdTable(
    ["No.", "Format Payload", "Karakteristik"],
    [
      [
        "1",
        "Email Signature",
        "Tanda tangan email formal berisi nama, jabatan, nomor telepon, dan lokasi instansi",
      ],
      [
        "2",
        "Database Export",
        "Data tabular hasil ekspor basis data, sering berisi NIK, nama, dan nomor telepon dalam format terstruktur",
      ],
      [
        "3",
        "Customer Service Log",
        "Log percakapan layanan pelanggan; PII muncul dalam konteks naratif dan tidak terstruktur",
      ],
      [
        "4",
        "Government Letter",
        "Surat resmi pemerintahan berisi identitas pejabat, jabatan, dan wilayah administratif",
      ],
      [
        "5",
        "JSON Streaming Log",
        "Log sistem dalam format JSON; PII tertanam sebagai nilai field",
      ],
      [
        "6",
        "Tabular CSV/TSV",
        "Data tabular dipisah koma atau tab; setiap baris merepresentasikan satu record",
      ],
      [
        "7",
        "Multi-PII Context",
        "Teks bebas yang mengandung kombinasi beberapa entitas PII sekaligus",
      ],
    ],
    [800, 2600, 6200],
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── D. Skema BIO ──────────────────────
const sectionD = [
  h1("D. Skema Pelabelan BIO Tagging"),
  p([
    tnr("Anotasi menggunakan skema BIO ("),
    tnrI("Beginning-Inside-Outside"),
    tnr(
      ") yang merupakan standar dalam tugas Named Entity Recognition (NER) sesuai CoNLL-2003 (Tjong Kim Sang & De Meulder, 2003).",
    ),
  ]),
  stdTable(
    ["Prefiks", "Kepanjangan", "Makna", "Contoh Token"],
    [
      [
        "B-",
        "Beginning",
        "Token pertama (atau satu-satunya) dari sebuah entitas",
        'B-NAMA pada token "Budi"',
      ],
      [
        "I-",
        "Inside",
        "Token lanjutan dari entitas yang sama (setelah B-)",
        'I-NAMA pada token "Santoso" (setelah "Budi")',
      ],
      [
        "O",
        "Outside",
        "Token yang bukan bagian dari entitas PII manapun",
        'O pada token "adalah", "di", tanda baca',
      ],
    ],
    [1200, 1800, 3600, 3000],
  ),
  p(""),
  p([tnrB("Daftar Lengkap Label (11 Label):")]),
  stdTable(
    ["Label", "Entitas", "Deskripsi"],
    [
      ["B-NIK", "NIK", "Token pertama atau token tunggal NIK (16 digit)"],
      ["B-PHONE", "PHONE", "Token pertama atau token tunggal nomor telepon"],
      [
        "I-PHONE",
        "PHONE",
        "Token lanjutan nomor telepon bila dipisah spasi/hubung",
      ],
      ["B-NAMA", "NAMA", "Token pertama dari nama orang"],
      [
        "I-NAMA",
        "NAMA",
        "Token lanjutan dari nama orang (kata kedua, ketiga, dst.)",
      ],
      ["B-JABATAN", "JABATAN", "Token pertama dari jabatan formal"],
      ["I-JABATAN", "JABATAN", "Token lanjutan dari jabatan formal"],
      ["B-LOKASI", "LOKASI", "Token pertama dari wilayah geografis"],
      ["I-LOKASI", "LOKASI", "Token lanjutan dari wilayah geografis"],
      [
        "O",
        "(bukan entitas)",
        "Token di luar semua entitas PII, termasuk nama institusi, tanda baca, konjungsi, preposisi",
      ],
    ],
    [1800, 2200, 5600],
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── E. Aturan Per Entitas ──────────────────────
const sectionE = [
  h1("E. Aturan Anotasi Per Entitas"),

  h2("E.1 Anotasi NIK"),
  numberedP(
    "NIK terdiri dari 16 digit angka, mengikuti format PP-KK-CC-DD-MM-YY-NNNN sesuai Permendagri No. 137 Tahun 2017.",
  ),
  numberedP(
    "Meskipun format ideal NIK dipisah dengan tanda hubung, dalam dataset ini NIK ditulis berurutan tanpa pemisah (contoh: 3271014507890001) sebagai satu token tunggal, sehingga dianotasi B-NIK.",
  ),
  numberedP(
    "Bila NIK dipisah spasi karena kesalahan format sumber data, seluruh fragmen dianotasi sebagai satu entitas dengan skema B-NIK + I-NIK.",
  ),
  numberedP(
    "Angka 16 digit yang jelas BUKAN NIK (misal Order ID, Invoice Number, Tracking Number) diberi label O — lihat kasus 1 pada Bagian F.",
  ),
  p([tnrB("Contoh:")]),
  p([tnr('"NIK saya 3271014507890001, tolong dicatat"')]),
  bulletP("NIK → O"),
  bulletP("saya → O"),
  bulletP("3271014507890001 → B-NIK"),
  bulletP(", → O"),
  bulletP("tolong → O"),
  bulletP("dicatat → O"),

  h2("E.2 Anotasi PHONE"),
  numberedP(
    "Nomor telepon Indonesia dengan prefix +62 atau 0, panjang 10-13 digit, dan kode operator resmi Kominfo (contoh: 0811-0813 Telkomsel, 0821-0823 Telkomsel, 0851-0858 Indosat).",
  ),
  numberedP(
    "Nomor yang ditulis utuh tanpa pemisah dianotasi sebagai B-PHONE tunggal (contoh: 081234567890 → B-PHONE).",
  ),
  numberedP(
    "Nomor yang dipisah spasi atau tanda hubung dianotasi sebagai B-PHONE + I-PHONE (contoh: 0812 3456 7890 → B-PHONE I-PHONE I-PHONE).",
  ),
  numberedP(
    "Nomor telepon internasional non-Indonesia (contoh: +1-, +44-, +65-) diberi label O karena di luar cakupan PII kependudukan Indonesia.",
  ),

  h2("E.3 Anotasi NAMA"),
  numberedP(
    "Nama lengkap orang, dapat terdiri dari satu hingga beberapa kata. Token pertama diberi label B-NAMA, token lanjutan I-NAMA.",
  ),
  numberedP(
    "Gelar akademik yang berdiri sendiri (S.Kom., M.Si., dr., Ir., dan sejenisnya) TIDAK dianotasi sebagai bagian NAMA — beri label O.",
  ),
  numberedP(
    "Gelar kebangsawanan yang berdiri sendiri (H., Hj., R., R.A., dan sejenisnya) TIDAK dianotasi sebagai bagian NAMA — beri label O.",
  ),
  numberedP(
    'Bila gelar menyatu tanpa spasi dengan nama (contoh: "H.Ahmad"), pisahkan secara mental: hanya bagian nama yang dianotasi. Lihat kasus 6 pada Bagian F.',
  ),
  numberedP(
    'Inisial (contoh: "A. Sudrajat") dianotasi B-NAMA + I-NAMA apabila konteks jelas merujuk pada nama orang.',
  ),
  p([tnrB("Contoh:")]),
  p([tnr('"Ditandatangani oleh dr. Budi Santoso, M.Kes."')]),
  bulletP("Ditandatangani → O"),
  bulletP("oleh → O"),
  bulletP("dr. → O"),
  bulletP("Budi → B-NAMA"),
  bulletP("Santoso → I-NAMA"),
  bulletP(", → O"),
  bulletP("M.Kes. → O"),

  h2("E.4 Anotasi JABATAN"),
  p([
    tnrB("Prinsip dasar: "),
    tnr("JABATAN adalah "),
    tnrB("posisi/jabatan formal yang dapat dijabat seseorang"),
    tnr(
      ', bukan nama organisasi/institusi itu sendiri. Kesalahan paling umum pada tugas ini adalah menandai nama instansi ("Dinas Pendidikan", "Politeknik Siber dan Sandi Negara", "ITB") sebagai JABATAN — hal ini keliru dan harus dilabeli O.',
    ),
  ]),
  p(""),
  numberedP(
    "Jabatan pemerintahan (Camat, Lurah, Kepala Desa, Kepala Dinas, Kepala Bidang, Gubernur, Bupati, Walikota, Sekretaris Daerah, dan sejenisnya).",
  ),
  numberedP(
    "Jabatan swasta dan akademik (Direktur Utama, Direktur, Manajer, CEO, CFO, CTO, Dosen, Profesor, Rektor, Dekan, Kepala Program Studi, dan sejenisnya).",
  ),
  numberedP(
    'Jabatan multi-kata dianotasi penuh sampai batas akhir jabatan tersebut. Contoh: "Kepala Dinas Pendidikan" — jika "Dinas Pendidikan" berperan sebagai kualifikasi jabatan (menjelaskan Kepala apa), maka "Kepala" (B-JABATAN), "Dinas" (I-JABATAN), "Pendidikan" (I-JABATAN).',
  ),
  numberedP(
    'Kata jabatan generik tanpa konteks yang jelas (misal kata "Kepala" yang merujuk pada bagian tubuh atau kepala dokumen) diberi label O.',
  ),
  p([tnrB("Contoh penerapan aturan disambiguasi JABATAN vs Institusi:")]),
  stdTable(
    ["Kalimat", "Anotasi Benar", "Alasan"],
    [
      [
        '"selaku Kepala Dinas Kependudukan"',
        "Kepala (B-JABATAN), Dinas (I-JABATAN), Kependudukan (I-JABATAN)",
        '"Dinas Kependudukan" adalah kualifikasi dari Kepala. Frasa utuh adalah jabatan orang tersebut.',
      ],
      [
        '"bekerja di Dinas Kependudukan"',
        "bekerja (O), di (O), Dinas (O), Kependudukan (O)",
        '"Dinas Kependudukan" berdiri sendiri sebagai nama institusi tempat kerja, bukan jabatan.',
      ],
      [
        '"Dinas Pendidikan Kota Bogor" (sebagai nama instansi surat)',
        "Dinas (O), Pendidikan (O), Kota (B-LOKASI), Bogor (I-LOKASI)",
        'Nama instansi lepas → O. "Kota Bogor" tetap LOKASI.',
      ],
      [
        '"Direktur PT Semen Indonesia"',
        "Direktur (B-JABATAN); PT (O), Semen (O), Indonesia (O)",
        'Hanya "Direktur" yang jabatan. "PT Semen Indonesia" adalah nama perusahaan → O.',
      ],
      [
        '"Ketua Program Studi Teknik Informatika ITB"',
        "Ketua (B-JABATAN), Program (I-JABATAN), Studi (I-JABATAN), Teknik (I-JABATAN), Informatika (I-JABATAN); ITB (O)",
        '"Ketua Program Studi Teknik Informatika" adalah jabatan utuh. "ITB" adalah nama institusi → O.',
      ],
    ],
    [3200, 3400, 3000],
  ),

  h2("E.5 Anotasi LOKASI"),
  numberedP(
    "Cakupan: nama provinsi, kabupaten, kota, kecamatan, kelurahan/desa, nama jalan, nama gedung (sebagai penanda lokasi).",
  ),
  numberedP(
    'Kata "Kota" yang tidak diikuti nama wilayah (contoh: "di kota ini", "pemerintah kota") diberi label O. Namun "Kota Bogor", "Kota Bandung" dianotasi sebagai B-LOKASI + I-LOKASI.',
  ),
  numberedP(
    "Singkatan wilayah yang diakui resmi (DKI, DIY, NTB, NTT, dst.) dianotasi sebagai B-LOKASI.",
  ),
  numberedP(
    'Nama jalan yang menyertakan nomor dianotasi sebagai satu entitas: "Jalan" (B-LOKASI) "Merdeka" (I-LOKASI) "No." (I-LOKASI) "10" (I-LOKASI).',
  ),
  numberedP(
    'Kata "Indonesia" yang berdiri sendiri sebagai nama negara TIDAK dianotasi sebagai LOKASI dalam konteks penelitian ini, karena penelitian berfokus pada wilayah administratif di dalam Indonesia.',
  ),
  p([tnrB("Contoh:")]),
  p([tnr('"berdomisili di Kecamatan Bogor Utara, Kota Bogor"')]),
  bulletP("berdomisili → O"),
  bulletP("di → O"),
  bulletP("Kecamatan → B-LOKASI"),
  bulletP("Bogor → I-LOKASI"),
  bulletP("Utara → I-LOKASI"),
  bulletP(", → O"),
  bulletP("Kota → B-LOKASI"),
  bulletP("Bogor → I-LOKASI"),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── F. Kasus Khusus ──────────────────────
const sectionF = [
  h1("F. Penanganan Kasus Khusus dan Ambigu"),
  p(
    "Tabel berikut mendefinisikan aturan untuk sepuluh edge case yang berpotensi ambigu dalam proses anotasi. Anotator wajib merujuk tabel ini apabila menemukan kasus serupa selama proses anotasi.",
  ),
  stdTable(
    ["No.", "Kasus", "Aturan Penanganan"],
    [
      [
        "1",
        "Angka 16 digit sebagai order_id / invoice / tracking",
        "Periksa konteks nama field. Jika bukan NIK kependudukan (contoh: order_id, invoice_no, tracking_no) → label O.",
      ],
      [
        "2",
        "Nama yang identik dengan kata jabatan",
        'Contoh: orang bernama "Camat". Tentukan berdasarkan konteks kalimat apakah merujuk pada identitas orang atau jabatan.',
      ],
      [
        "3",
        "Singkatan nama (inisial)",
        'Anotasi B-NAMA + I-NAMA apabila konteks jelas menunjukkan nama orang (contoh: "atas nama A. Sudrajat").',
      ],
      [
        "4",
        "Nomor telepon dengan pemisah spasi/tanda hubung",
        "Anotasi seluruh token sebagai satu entitas PHONE (B-PHONE untuk token pertama, I-PHONE untuk berikutnya).",
      ],
      [
        "5",
        "LOKASI yang juga bagian nama instansi",
        'Contoh: "Dinas Pendidikan Kota Bogor". "Dinas Pendidikan" → O (nama instansi). "Kota Bogor" → LOKASI. Anotasi terpisah.',
      ],
      [
        "6",
        "Nama dengan gelar yang menyatu (tanpa spasi)",
        'Contoh: "H.Ahmad Yani". Anotasi hanya bagian nama inti: "Ahmad" (B-NAMA), "Yani" (I-NAMA). "H." → O.',
      ],
      [
        "7",
        "Nama institusi/organisasi bukan nama orang",
        'Contoh: "Politeknik Siber dan Sandi Negara", "Institut Teknologi Bandung", "PT Bank Mandiri" adalah nama institusi → label O (tidak termasuk entitas PII yang dianotasi).',
      ],
      [
        "8",
        "Entitas PII yang terpotong / tidak lengkap",
        "NIK atau PHONE yang tidak lengkap (kurang digit) karena redaksi dokumen tetap diberi label sesuai konteks yang menunjukkan jenis entitas, dengan catatan pada kolom komentar.",
      ],
      [
        "9",
        "Jabatan diikuti nama institusi tanpa preposisi",
        'Contoh: "Direktur Bank Mandiri". "Direktur" adalah JABATAN inti; "Bank Mandiri" adalah nama institusi tempat menjabat, dilabeli O — karena bukan bagian dari titel jabatan formal seseorang.',
      ],
      [
        "10",
        "Ambiguitas gelar kehormatan/keagamaan",
        'Gelar seperti "Pak", "Ibu", "Bapak", "Ustadz", "KH" TIDAK dianotasi sebagai bagian NAMA. Beri label O. Contoh: "Pak Budi" → "Pak" (O), "Budi" (B-NAMA).',
      ],
    ],
    [700, 3000, 5900],
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── G. Prosedur ──────────────────────
const sectionG = [
  h1("G. Prosedur Pelaksanaan Anotasi"),
  p(
    "Anotasi dilakukan secara terpisah dan independen oleh Anotator A dan Anotator B menggunakan data sampel yang identik (SEED=42). Prosedur dilakukan dalam dua tahap: tahap kalibrasi (Bagian G.1) dan tahap anotasi utama (Bagian G.2).",
  ),

  h2("G.1 Tahap Kalibrasi (Wajib, Sebelum Anotasi Utama)"),
  p([
    tnrB("Tujuan: "),
    tnr(
      "menyamakan persepsi kedua anotator terhadap pedoman ini sebelum mengerjakan 200 sampel resmi, sehingga potensi kesalahpahaman aturan dapat dideteksi dan diperbaiki di awal — bukan setelah 200 sampel selesai dan ternyata κ rendah karena beda interpretasi.",
    ),
  ]),
  numberedP(
    "Anotator A menyiapkan 10 sampel kalibrasi yang mewakili variasi tujuh format payload dan kelima entitas. Sampel kalibrasi INI TIDAK termasuk 200 sampel utama.",
    "list-calib",
  ),
  numberedP(
    "Kedua anotator melabel 10 sampel tersebut secara independen di HumanSignal.",
    "list-calib",
  ),
  numberedP(
    "Setelah selesai, kedua anotator SALING BERDISKUSI secara terbuka membandingkan hasilnya. Diskusi terfokus pada sumber ketidaksepakatan dan interpretasi aturan.",
    "list-calib",
  ),
  numberedP(
    "Bila ditemukan aturan pedoman yang ambigu atau belum tercakup, Anotator A merevisi dokumen pedoman ini dan menerbitkan versi baru.",
    "list-calib",
  ),
  numberedP(
    "Setelah pedoman final disepakati kedua pihak, tahap kalibrasi ditutup dan tahap anotasi utama (G.2) dapat dimulai. TIDAK ADA DISKUSI SETELAH TAHAP INI hingga seluruh 200 sampel selesai dianotasi.",
    "list-calib",
  ),

  h2("G.2 Tahap Anotasi Utama"),
  numberedP(
    "Anotator A menerbitkan proyek HumanSignal berisi 200 sampel identik untuk kedua anotator. Konfigurasi proyek WAJIB: Overlap of Annotations = 100%, minimum annotators per task = 2.",
    "list-main",
  ),
  numberedP(
    'Anotator B menerima undangan akses ke proyek dengan role "Annotator" (BUKAN role Manager/Reviewer/Admin) sehingga tidak dapat melihat hasil anotasi Anotator A selama proses berlangsung (blind annotation).',
    "list-main",
  ),
  numberedP(
    "Kedua anotator membaca ulang Bagian E dan F pedoman ini secara menyeluruh sebelum memulai anotasi.",
    "list-main",
  ),
  numberedP(
    "Anotasi dilakukan secara mandiri. DILARANG mendiskusikan atau membandingkan hasil anotasi antara Anotator A, Anotator B, atau pihak lain SELAMA seluruh 200 sampel belum selesai dianotasi kedua pihak.",
    "list-main",
  ),
  numberedP(
    "Kasus ambigu yang ditemui dicatat pada kolom komentar HumanSignal per task, dilengkapi alasan keputusan yang diambil. Catatan ini digunakan untuk analisis kualitatif pelengkap nilai IAA.",
    "list-main",
  ),
  numberedP(
    "Setelah kedua anotator menyelesaikan seluruh 200 sampel, Anotator A mengekspor hasil kedua anotator dari HumanSignal (format JSON-MIN atau JSON default) dan menjalankan skrip perhitungan IAA (Bagian I.3).",
    "list-main",
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── H. Tool ──────────────────────
const sectionH = [
  h1("H. Spesifikasi Tool Anotasi"),

  h2("H.1 Tool yang Digunakan: HumanSignal (Label Studio)"),
  p([
    tnr("Tool anotasi resmi yang digunakan dalam penelitian ini adalah "),
    tnrB("HumanSignal"),
    tnr(
      " (URL: https://labelstud.io — sebelumnya dikenal sebagai Label Studio). Pemilihan tool ini didasarkan pada:",
    ),
  ]),
  bulletP(
    "Dukungan native untuk skema BIO tagging pada tugas NER dengan interface visual span-selection",
  ),
  bulletP(
    "Dukungan multi-annotator dengan konfigurasi Overlap of Annotations yang dapat disesuaikan",
  ),
  bulletP(
    "Dukungan role-based access control (RBAC) yang memungkinkan blind annotation dengan pemberian role Annotator kepada Anotator B",
  ),
  bulletP(
    "Format ekspor JSON dan CoNLL yang kompatibel dengan pipeline evaluasi seqeval (Python)",
  ),
  bulletP(
    "Fitur komentar per task untuk mendokumentasikan kasus ambigu selama anotasi",
  ),

  h2("H.2 Prinsip Metodologis Konfigurasi Tool"),
  stdTable(
    ["No.", "Prinsip", "Konfigurasi HumanSignal"],
    [
      [
        "1",
        "Blind Annotation",
        'Anotator B diberi role "Annotator" (bukan Reviewer/Manager), sehingga tidak dapat melihat anotasi Anotator A pada task yang sama',
      ],
      [
        "2",
        "Overlap 100%",
        'Settings → Annotation → "Overlap of Annotations" = 100%; "Minimum annotators per task" = 2. Setiap dari 200 task wajib dianotasi oleh kedua anotator.',
      ],
      [
        "3",
        "Token-level Granularity",
        "Label configuration menggunakan tag <Labels> pada tag <Text> dengan lima entitas: NIK, PHONE, NAMA, JABATAN, LOKASI",
      ],
      [
        "4",
        "Reproducible Sampling",
        "Dataset diambil dari held-out set dengan SEED=42; kedua anotator mengerjakan file JSON impor yang identik",
      ],
      [
        "5",
        "Audit Trail",
        "HumanSignal mencatat timestamp submit setiap annotation; export JSON menyertakan created_at dan updated_at per annotation",
      ],
      [
        "6",
        "Komentar Inline",
        'Fitur "Add annotation comment" pada UI HumanSignal digunakan untuk mendokumentasikan alasan pada kasus ambigu',
      ],
      [
        "7",
        "Progress Tracking",
        'Data Manager menampilkan kolom "Task State" (Annotating/Submitted) dan progress agregat pada footer',
      ],
    ],
    [800, 2400, 6400],
  ),

  h2("H.3 Label Configuration HumanSignal"),
  p([
    tnr(
      "Label configuration berikut disalin ke Settings → Labeling Interface → Code:",
    ),
  ]),
  code(`<View>`),
  code(`  <Labels name="label" toName="text">`),
  code(`    <Label value="NIK" background="#FF6B6B"/>`),
  code(`    <Label value="PHONE" background="#4ECDC4"/>`),
  code(`    <Label value="NAMA" background="#FFE66D"/>`),
  code(`    <Label value="JABATAN" background="#95E1D3"/>`),
  code(`    <Label value="LOKASI" background="#C9B1FF"/>`),
  code(`  </Labels>`),
  code(`  <Text name="text" value="$text"/>`),
  code(`</View>`),

  h2("H.4 Konfigurasi Wajib pada Project Settings"),
  p([
    tnr("Setelah membuat proyek, konfigurasi berikut "),
    tnrB("WAJIB"),
    tnr(" diperiksa pada menu "),
    tnrI("Settings → Annotation"),
    tnr(":"),
  ]),
  bulletP("Overlap of Annotations: 100%"),
  bulletP("Minimum annotators per task: 2"),
  bulletP("Annotation instruction: link ke dokumen pedoman ini"),
  bulletP(
    "Reveal preannotations interactively: OFF (tidak diperlukan; tidak ada model predictions)",
  ),

  h2("H.5 Prosedur Ekspor Hasil"),
  p(
    "Setelah kedua anotator menyelesaikan seluruh 200 sampel, Anotator A melakukan ekspor melalui:",
  ),
  numberedP("Buka Data Manager proyek.", "list-export"),
  numberedP("Klik tombol Export.", "list-export"),
  numberedP(
    "Pilih format JSON (default) — bukan JSON-MIN, karena JSON-MIN kehilangan informasi annotator per hasil label.",
    "list-export",
  ),
  numberedP("Simpan file sebagai anotasi_raw_export.json.", "list-export"),
  numberedP(
    "Jalankan skrip 31_compute_inter_kappa.py (versi terbaru) untuk menghitung Span-F1, Cohen's Kappa, dan Gwet's AC1 secara otomatis.",
    "list-export",
  ),

  p([
    tnrB("Catatan penting: "),
    tnr(
      'Angka "Agreement" yang muncul pada UI HumanSignal (kolom Agreement pada Data Manager) hanya tersedia pada edisi Starter Cloud/Enterprise, dan mekanisme perhitungannya berbasis ',
    ),
    tnrI("consensus score"),
    tnr(" internal — "),
    tnrB("BUKAN"),
    tnr(
      " nilai Cohen's Kappa, Span-F1, atau Gwet's AC1 yang standar akademik. Oleh karena itu, penelitian ini ",
    ),
    tnrB("tidak menggunakan"),
    tnr(
      " angka Agreement bawaan HumanSignal, melainkan menghitung tiga metrik IAA komplementer secara mandiri dari hasil ekspor JSON menggunakan skrip Python yang transparan dan dapat direproduksi.",
    ),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── I. IAA ──────────────────────
const sectionI = [
  h1("I. Metrik Inter-Annotator Agreement dan Target"),

  h2("I.1 Pemilihan Metrik: Tiga Metrik Komplementer"),
  p([
    tnr(
      "Berbeda dengan tugas klasifikasi biasa, tugas NER memiliki dua karakteristik yang membuat Cohen's Kappa tunggal tidak memadai sebagai metrik IAA:",
    ),
  ]),
  numberedP(
    [
      tnrB("Ketidakjelasan definisi kasus negatif. "),
      tnr(
        'NER adalah tugas sequence tagging; jumlah "kasus negatif" bergantung pada tokenizer yang digunakan (Hripcsak & Rothschild, 2005). Bila dihitung pada semua token termasuk label O, label O yang mendominasi (74% pada dataset ini per Tabel 4.9) akan membanjiri statistik dan menghasilkan κ yang menyesatkan.',
      ),
    ],
    "list-metric",
  ),
  numberedP(
    [
      tnrB("Kappa Paradox pada Distribusi Timpang. "),
      tnr(
        "Feinstein dan Cicchetti (1990) menunjukkan bahwa κ dapat jatuh drastis meskipun observed agreement (Pₒ) tinggi, apabila distribusi marginal timpang. Gwet (2008) menawarkan AC1 sebagai koefisien ",
      ),
      tnrI("paradox-resistant"),
      tnr(" yang lebih stabil pada distribusi timpang."),
    ],
    "list-metric",
  ),
  p(
    "Mengikuti praktik penelitian NER terkini (mis. PrionNER 2026, Chinese-SkillSpan 2026, CrudeOilNews 2022), penelitian ini melaporkan tiga metrik komplementer:",
  ),
  stdTable(
    ["Metrik", "Level", "Sumber", "Fungsi"],
    [
      [
        [
          p([tnrB("Span-level Pairwise F1")], { after: 40 }),
          p([tnrI("(strict + relaxed)")], { after: 0 }),
        ],
        "Entitas",
        "Tjong Kim Sang & De Meulder (2003); Hripcsak & Rothschild (2005)",
        "Metrik UTAMA — mengukur kesepakatan pada batas dan tipe entitas, standar de-facto untuk NER",
      ],
      [
        'Cohen\'s Kappa (tanpa "O")',
        "Token",
        "Cohen (1960); Artstein & Poesio (2008)",
        "Metrik PELENGKAP — dilaporkan karena umum dikenal, dihitung hanya pada token bertag entitas (bukan O) agar tidak kena kappa paradox",
      ],
      [
        "Gwet's AC1",
        "Token",
        "Gwet (2008)",
        "Metrik PARADOX-RESISTANT — jaring pengaman bila κ turun akibat distribusi timpang; lebih stabil pada prevalensi kelas ekstrem",
      ],
    ],
    [2600, 1400, 2400, 3200],
  ),

  h2("I.2 Formula Metrik"),
  p([tnrB("(a) Span-level Pairwise F1 (Strict)")]),
  p(
    "Sebuah entitas dianggap disepakati kedua anotator apabila (1) tipe entitas sama DAN (2) batas awal-akhir span identik. Perhitungan menggunakan library seqeval Python yang mengimplementasikan aturan CoNLL-2003.",
  ),
  code("F1_strict = 2 × Precision × Recall / (Precision + Recall)"),
  p([
    tnr("dengan Anotator A diperlakukan sebagai "),
    tnrI("gold"),
    tnr(" dan Anotator B sebagai "),
    tnrI("predicted"),
    tnr(" (F1 pairwise bersifat simetris)."),
  ]),
  p([tnrB("(b) Span-level Pairwise F1 (Relaxed)")]),
  p(
    "Sama dengan strict, tetapi kesepakatan diberikan apabila kedua span memiliki overlap ≥ 1 token dengan tipe entitas yang sama (mengukur kesepakatan tipe entitas terpisah dari kesepakatan boundary). Selisih strict vs relaxed mengungkap kontribusi boundary error terhadap total ketidaksepakatan.",
  ),
  p([tnrB('(c) Cohen\'s Kappa (Token-level, tanpa "O")')]),
  code("κ = (Pₒ - Pₑ) / (1 - Pₑ)"),
  p(
    "dihitung hanya pada subset token yang di-tag sebagai entitas (bukan O) oleh setidaknya satu anotator, mengikuti pola CrudeOilNews (2022) dan Tweebank (2022) untuk menghindari bias dari kelas mayoritas O.",
  ),
  p([tnrB("(d) Gwet's AC1")]),
  code("AC1 = (Pₐ - Pₑ_gwet) / (1 - Pₑ_gwet)"),
  p([
    tnr("dengan Pₑ_gwet = "),
    tnrI("2 × π × (1 - π)"),
    tnr(
      " (untuk klasifikasi biner; formula multiclass menggunakan generalisasi Gwet 2008), di mana π adalah proporsi kesepakatan positif marginal. Perbedaan utama dari κ terletak pada perhitungan expected agreement yang tidak bergantung pada prevalensi kelas.",
    ),
  ]),

  h2("I.3 Perhitungan Otomatis dengan Skrip"),
  p([
    tnr(
      "Ketiga metrik dihitung otomatis dari file ekspor JSON HumanSignal menggunakan skrip ",
    ),
    tnrB("scripts/31_compute_inter_kappa.py"),
    tnr(
      " (versi terbaru pada repositori NDLP-Hybrid). Skrip ini menggunakan library:",
    ),
  ]),
  bulletP("seqeval (Nakayama, 2018) untuk Span-level Pairwise F1"),
  bulletP("scikit-learn cohen_kappa_score untuk Cohen's Kappa token-level"),
  bulletP("irrCAC atau kustom implementasi Gwet AC1"),

  h2("I.4 Interpretasi Nilai (Landis & Koch, 1977)"),
  p(
    "Kedua metrik (Cohen's Kappa dan Gwet's AC1) menggunakan skala interpretasi Landis & Koch. Span-F1 tidak memiliki interpretasi Landis-Koch resmi tetapi dapat ditafsirkan menggunakan skala yang sama secara konvensional.",
  ),
  stdTable(
    ["Rentang Nilai", "Kategori", "Keterangan"],
    [
      ["< 0,00", "Poor", "Kesepakatan di bawah peluang acak"],
      ["0,00 – 0,20", "Slight", "Kesepakatan sangat lemah"],
      ["0,21 – 0,40", "Fair", "Kesepakatan lemah"],
      ["0,41 – 0,60", "Moderate", "Kesepakatan cukup"],
      ["0,61 – 0,80", "Substantial", "Kesepakatan baik"],
      ["0,81 – 1,00", "Almost Perfect", "Target penelitian"],
    ],
    [2200, 3000, 4400],
  ),

  h2("I.5 Target Penelitian"),
  p([
    tnrB(
      "Target primer: Span-level Pairwise F1 (strict) ≥ 0,75 DAN Gwet's AC1 ≥ 0,80.",
    ),
  ]),
  p("Justifikasi pemilihan target:"),
  bulletP([
    tnr(
      "Span-F1 strict ≥ 0,75 mencerminkan tingkat kesepakatan wajar untuk NER pada teks naturalistik dengan boundary ambiguity, sejalan dengan penelitian NER terkini (Chinese-SkillSpan 2026 melaporkan 0,532; PrionNER 2026 melaporkan 0,818). Nilai 0,75 dipilih sebagai kompromi antara realisme empiris dan integritas metodologis.",
    ),
  ]),
  bulletP([
    tnr("Gwet's AC1 ≥ 0,80 digunakan sebagai metrik "),
    tnrI("paradox-resistant"),
    tnr(
      " utama pada level token karena distribusi label O yang mendominasi (74%) berpotensi memicu kappa paradox pada Cohen's Kappa konvensional.",
    ),
  ]),
  bulletP(
    "Cohen's Kappa tanpa \"O\" dilaporkan sebagai referensi silang; nilainya diharapkan berada pada rentang Substantial-Almost Perfect (0,61-1,00) dan digunakan untuk memvalidasi konsistensi dengan Gwet's AC1.",
  ),

  h2("I.6 Prosedur Adjudikasi bila Target Tidak Tercapai"),
  p([
    tnr(
      "Apabila salah satu atau kedua metrik primer di bawah target, dilakukan tahap ",
    ),
    tnrB("adjudikasi formal"),
    tnr(
      " untuk menghasilkan ground truth final. Prosedur ini WAJIB dilaksanakan agar dataset held-out tetap dapat digunakan sebagai referensi evaluasi model:",
    ),
  ]),
  numberedP(
    "Anotator A mengidentifikasi seluruh token dan/atau span di mana Anotator A dan B berbeda pendapat menggunakan output skrip perhitungan.",
    "list-adj",
  ),
  numberedP(
    "Kasus-kasus tidak sepakat dikategorikan ke dalam empat kelompok: (a) boundary disagreement (kedua anotator setuju tipe entitas, beda batas span), (b) type disagreement (batas sama, tipe entitas beda), (c) missing detection (satu anotator menandai, satu tidak), (d) genuine ambiguity (kasus yang memang tidak tercakup pedoman).",
    "list-adj",
  ),
  numberedP(
    "Anotator A dan B melakukan diskusi terarah untuk setiap kasus tidak sepakat, dengan merujuk pada Bagian E dan F pedoman ini. Diskusi dicatat dalam log adjudikasi.",
    "list-adj",
  ),
  numberedP(
    [
      tnr("Bila diskusi mencapai kesepakatan, label yang disepakati menjadi "),
      tnrI("gold standard"),
      tnr(" final untuk token/span tersebut."),
    ],
    "list-adj",
  ),
  numberedP(
    [
      tnr(
        "Bila diskusi tidak mencapai kesepakatan (mis. kasus benar-benar ambigu di luar pedoman), Dosen Pembimbing berperan sebagai ",
      ),
      tnrB("adjudicator ketiga"),
      tnr(
        " untuk memutuskan label final. Keputusan ini dicatat sebagai preseden untuk kasus serupa.",
      ),
    ],
    "list-adj",
  ),
  numberedP(
    [
      tnr(
        "Setelah adjudikasi selesai, hasil final digunakan sebagai ground truth held-out set. Nilai IAA ",
      ),
      tnrB("pra-adjudikasi"),
      tnr(
        " tetap dilaporkan di laporan penelitian sebagai bukti proses reliabilitas, disertai catatan proporsi kasus yang diadjudikasi.",
      ),
    ],
    "list-adj",
  ),

  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── J. Surat Pernyataan ──────────────────────
const sectionJ = [
  h1("J. Surat Pernyataan Anotator B"),

  new Paragraph({
    children: [
      new TextRun({
        text: "SURAT PERNYATAAN ANOTATOR INDEPENDEN",
        font: FONT,
        size: 28,
        bold: true,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 40 },
  }),
  new Paragraph({
    children: [
      new TextRun({
        text: "Pedoman Anotasi Inter-Annotator Agreement (IAA)",
        font: FONT,
        size: 24,
        italics: true,
      }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
  }),
  p(
    [
      tnr("Penelitian Tugas Akhir: "),
      tnrI(
        "Pengembangan Sistem NDLP dengan Metode Hibrida Rule-Based dan Machine Learning pada Data Kependudukan",
      ),
    ],
    { alignment: AlignmentType.JUSTIFIED, after: 200 },
  ),
  p("Saya yang bertanda tangan di bawah ini:", { after: 100 }),
  stdTable(
    ["Atribut", "Rincian"],
    [
      ["Nama Lengkap", "Muhammad Abdul Aziz Ghazali, S.T."],
      ["Latar Belakang Pendidikan", "Alumni Institut Teknologi Bandung (ITB)"],
      [
        "Bidang Keahlian",
        "Machine Learning (ML), Natural Language Processing (NLP), dan Named Entity Recognition (NER)",
      ],
      ["Hubungan dengan Peneliti", "Bertindak sebagai anotator independen"],
    ],
    [2800, 6800],
  ),
  p("dengan ini menyatakan bahwa:", { before: 200, after: 100 }),
  numberedP(
    "Saya telah membaca dan memahami seluruh isi Pedoman Anotasi ini sebelum melakukan proses anotasi.",
    "list-decl",
  ),
  numberedP(
    "Saya telah menyelesaikan tahap kalibrasi (10 sampel) bersama Anotator A dan menyepakati versi final Pedoman Anotasi sebelum memulai anotasi utama.",
    "list-decl",
  ),
  numberedP(
    "Saya melakukan anotasi utama secara independen dan mandiri, tanpa mendiskusikan atau membandingkan hasil anotasi dengan Anotator A (peneliti) maupun pihak lain yang terlibat dalam penelitian, selama proses anotasi 200 sampel utama berlangsung.",
    "list-decl",
  ),
  numberedP(
    "Saya menjaga kerahasiaan data yang dianotasi dan tidak menyebarluaskan isi dataset kepada pihak lain di luar keperluan penelitian ini.",
    "list-decl",
  ),
  numberedP(
    "Hasil anotasi yang saya berikan merupakan penilaian saya sendiri berdasarkan pemahaman terhadap pedoman ini, tanpa tekanan atau pengaruh dari pihak manapun.",
    "list-decl",
  ),
  numberedP(
    "Saya memahami bahwa hasil anotasi ini digunakan untuk menghitung tiga metrik Inter-Annotator Agreement (Span-level Pairwise F1, Cohen's Kappa, dan Gwet's AC1) sebagai bagian dari validasi reliabilitas dataset penelitian tugas akhir.",
    "list-decl",
  ),
  numberedP(
    "Apabila hasil pengukuran IAA menunjukkan kesepakatan di bawah target penelitian, saya bersedia mengikuti tahap adjudikasi (Bagian I.6) untuk menghasilkan ground truth final.",
    "list-decl",
  ),

  p("Demikian surat pernyataan ini saya buat dengan sebenar-benarnya.", {
    before: 200,
    after: 400,
  }),

  new Paragraph({
    children: [tnr("Jakarta/Bandung, ______________________________ 2026")],
    spacing: { after: 600 },
  }),
  p("Yang membuat pernyataan,", { after: 800 }),
  p([tnrB("_________________________________")], { after: 40 }),
  p([tnrB("Muhammad Abdul Aziz Ghazali, S.T.")], { after: 40 }),
  p("Alumni Institut Teknologi Bandung (ITB)", { after: 80 }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ────────────────────── K. Referensi ──────────────────────
const refItems = [
  [
    "Artstein, R., & Poesio, M. (2008). ",
    "Inter-coder agreement for computational linguistics. ",
    "Computational Linguistics, 34",
    "(4), 555–596. https://doi.org/10.1162/coli.07-034-R2",
  ],
  [
    "Cohen, J. (1960). ",
    "A coefficient of agreement for nominal scales. ",
    "Educational and Psychological Measurement, 20",
    "(1), 37–46. https://doi.org/10.1177/001316446002000104",
  ],
  [
    "Feinstein, A. R., & Cicchetti, D. V. (1990). ",
    "High agreement but low kappa: I. The problems of two paradoxes. ",
    "Journal of Clinical Epidemiology, 43",
    "(6), 543–549. https://doi.org/10.1016/0895-4356(90)90158-L",
  ],
  [
    "Gwet, K. L. (2008). ",
    "Computing inter-rater reliability and its variance in the presence of high agreement. ",
    "British Journal of Mathematical and Statistical Psychology, 61",
    "(1), 29–48. https://doi.org/10.1348/000711006X126600",
  ],
  [
    "Hripcsak, G., & Rothschild, A. S. (2005). ",
    "Agreement, the F-measure, and reliability in information retrieval. ",
    "Journal of the American Medical Informatics Association, 12",
    "(3), 296–298. https://doi.org/10.1197/jamia.M1733",
  ],
  [
    "Lafferty, J., McCallum, A., & Pereira, F. (2001). ",
    "Conditional random fields: Probabilistic models for segmenting and labeling sequence data. ",
    "Proceedings of the 18th International Conference on Machine Learning (ICML 2001)",
    ", 282–289.",
  ],
  [
    "Landis, J. R., & Koch, G. G. (1977). ",
    "The measurement of observer agreement for categorical data. ",
    "Biometrics, 33",
    "(1), 159–174. https://doi.org/10.2307/2529310",
  ],
  [
    "Nakayama, H. (2018). ",
    "seqeval: A Python framework for sequence labeling evaluation. ",
    "",
    "https://github.com/chakki-works/seqeval",
  ],
  [
    "Peraturan Menteri Dalam Negeri Republik Indonesia Nomor 137 Tahun 2017 ",
    "tentang Kode dan Data Wilayah Administrasi Pemerintahan. ",
    "Berita Negara Republik Indonesia Tahun 2017 Nomor 1955",
    ".",
  ],
  [
    "Peraturan Pemerintah Republik Indonesia Nomor 40 Tahun 2019 ",
    "tentang Pelaksanaan Undang-Undang Nomor 23 Tahun 2006 tentang Administrasi Kependudukan sebagaimana telah diubah dengan Undang-Undang Nomor 24 Tahun 2013. ",
    "Lembaran Negara Republik Indonesia Tahun 2019 Nomor 102",
    ".",
  ],
  [
    "Tjong Kim Sang, E. F., & De Meulder, F. (2003). ",
    "Introduction to the CoNLL-2003 shared task: Language-independent named entity recognition. ",
    "Proceedings of the 7th Conference on Natural Language Learning at HLT-NAACL 2003 (CoNLL-2003)",
    ", 142–147. https://doi.org/10.3115/1119176.1119195",
  ],
  [
    "Undang-Undang Republik Indonesia Nomor 27 Tahun 2022 ",
    "tentang Perlindungan Data Pribadi. ",
    "Lembaran Negara Republik Indonesia Tahun 2022 Nomor 196, Tambahan Lembaran Negara Nomor 6820",
    ".",
  ],
];

const sectionK = [
  h1("K. Daftar Referensi"),
  ...refItems.map(
    (parts) =>
      new Paragraph({
        children: parts.map((seg, i) => {
          if (i === 1) return tnrI(seg); // judul (italic)
          if (i === 2) return tnrI(seg); // jurnal/venue (italic)
          return tnr(seg);
        }),
        indent: {
          left: convertInchesToTwip(0.5),
          hanging: convertInchesToTwip(0.5),
        },
        spacing: { before: 80, after: 80, line: 320 },
        alignment: AlignmentType.JUSTIFIED,
      }),
  ),
];

// ────────────────────── Dokumen ──────────────────────
const doc = new Document({
  creator: "Arga Ariyuda Avian",
  title: "Pedoman Anotasi IAA v3.0",
  description:
    "Pedoman anotasi Inter-Annotator Agreement untuk validasi held-out naturalistic test set (versi 3, revisi metrik dan tool)",
  styles: {
    default: {
      document: {
        run: { font: FONT, size: SIZE },
        paragraph: { spacing: { line: 340 } },
      },
    },
  },
  numbering: {
    config: [
      {
        reference: "list-main",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "list-calib",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "list-export",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "list-metric",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "list-adj",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "list-decl",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      {
        reference: "bullet-main",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "\u2022",
            alignment: AlignmentType.START,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          margin: {
            top: convertInchesToTwip(1),
            right: convertInchesToTwip(1),
            bottom: convertInchesToTwip(1),
            left: convertInchesToTwip(1),
          },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: "Pedoman Anotasi IAA – Penelitian TA Arga Ariyuda Avian",
                  font: FONT,
                  size: 20,
                  italics: true,
                  color: "595959",
                }),
              ],
              alignment: AlignmentType.RIGHT,
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({
                  text: "Hal. ",
                  font: FONT,
                  size: 20,
                  color: "595959",
                }),
                new TextRun({
                  children: [PageNumber.CURRENT],
                  font: FONT,
                  size: 20,
                  color: "595959",
                }),
                new TextRun({
                  text: " / ",
                  font: FONT,
                  size: 20,
                  color: "595959",
                }),
                new TextRun({
                  children: [PageNumber.TOTAL_PAGES],
                  font: FONT,
                  size: 20,
                  color: "595959",
                }),
              ],
            }),
          ],
        }),
      },
      children: [
        ...cover,
        ...sectionA,
        ...sectionB,
        ...sectionC,
        ...sectionD,
        ...sectionE,
        ...sectionF,
        ...sectionG,
        ...sectionH,
        ...sectionI,
        ...sectionJ,
        ...sectionK,
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  const outputPath = "Validasi_Pedoman_Anotasi_TA_Arga_v3.docx";
  fs.writeFileSync(outputPath, buffer);
  console.log(`✅ Berhasil dibuat: ${outputPath}`);
  console.log(`   Ukuran: ${(buffer.length / 1024).toFixed(1)} KB`);
});
