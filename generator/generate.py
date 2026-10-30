#!/usr/bin/env python3
"""Buat dua PDF bulanan: surat lamaran dan laporan kegiatan.

Pemakaian:
  python3 generate.py              # bulan sebelumnya
  python3 generate.py --bulan 2026-10

Surat lamaran diberi tanggal hari terakhir bulan tersebut.
Laporan kegiatan hanya memuat hari kerja: Minggu, hari libur nasional
dan cuti bersama (diisi di config.json) dilewati.
Foto geotag opsional: taruh foto/YYYY-MM-DD.jpg di folder foto.
"""
import argparse
import calendar
import datetime as dt
import json
import os

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
FONT = "Times-Roman"


def tgl_panjang(d):
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def tgl_pendek(d):
    return d.strftime("%d-%m-%y")


def bulan_lalu():
    t = dt.date.today().replace(day=1) - dt.timedelta(days=1)
    return t.year, t.month


def hari_kerja(year, month, cfg):
    libur = set(cfg.get("hari_libur", [])) | set(cfg.get("cuti_bersama", []))
    hari = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        d = dt.date(year, month, day)
        if d.weekday() == 6 or d.isoformat() in libur:  # 6 = Minggu
            continue
        hari.append(d)
    return hari


def buat_surat(path, year, month, cfg):
    # Surat untuk laporan bulan X diberi tanggal hari terakhir bulan X-1
    last = dt.date(year, month, 1) - dt.timedelta(days=1)
    s = ParagraphStyle("n", fontName=FONT, fontSize=11, leading=15, spaceAfter=7)
    r = ParagraphStyle("r", parent=s, alignment=TA_RIGHT)
    li = ParagraphStyle("li", parent=s, leftIndent=18, spaceAfter=0)

    fields = [
        ["Nama", ":", cfg["nama"]],
        ["Tempat/Tanggal Lahir", ":", f"{cfg['tempat_lahir']}, {cfg['tgl_lahir']}"],
        ["Alamat", ":", cfg["alamat"]],
        ["No. KTP", ":", cfg["ktp"]],
        ["Agama", ":", cfg["agama"]],
        ["No. Telpon", ":", cfg["telp"]],
    ]
    tabel = Table(fields, colWidths=[4.6 * cm, 0.4 * cm, 11 * cm])
    tabel.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    cerita = []
    cerita.append(Paragraph(f"{cfg['kota']}, {tgl_panjang(last)}", r))
    cerita.append(Spacer(1, 8))
    cerita.append(Paragraph("Hal : Lamaran Pekerjaan", s))
    cerita.append(Paragraph("Kepada Yth,", s))
    cerita.append(Paragraph(cfg["kepada"], s))
    cerita.append(Paragraph("Di Tempat", s))
    cerita.append(Spacer(1, 16))
    cerita.append(Paragraph("Dengan Hormat,", s))
    cerita.append(Paragraph("Saya yang bertanda tangan dibawah ini :", s))
    cerita.append(tabel)
    cerita.append(Spacer(1, 8))
    cerita.append(Paragraph(
        f"Bersama ini mengajukan permohonan kerja di {cfg['instansi']} "
        f"sebagai {cfg['jabatan']}. Adapun sebagai bahan pertimbangan, "
        "dengan ini saya lampirkan hal – hal sebagai berikut :", s))
    for i, item in enumerate(cfg["lampiran"], 1):
        cerita.append(Paragraph(f"{i}. {item}", li))
    cerita.append(Spacer(1, 10))
    cerita.append(Paragraph(
        "Demikian surat permohonan ini saya buat dengan penuh kesadaran dan rasa "
        "tanggung jawab yang besar, dengan harapan dapat diterima. Atas perhatian "
        "dan kerjasamanya saya ucapkan terima kasih banyak.", s))
    cerita.append(Spacer(1, 12))
    cerita.append(Paragraph("Hormat Saya", r))

    ttd_path = os.path.join(HERE, cfg["ttd"])
    if os.path.exists(ttd_path):
        cerita.append(Spacer(1, 4))
        img = Image(ttd_path, width=4 * cm, height=2 * cm, kind="proportional")
        img.hAlign = "RIGHT"
        cerita.append(img)
    else:
        cerita.append(Spacer(1, 50))
    cerita.append(Paragraph(cfg["nama"], r))

    SimpleDocTemplate(path, pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                      topMargin=2.5 * cm, bottomMargin=2.5 * cm).build(cerita)


def buat_laporan(path, hari, cfg):
    kepala = [
        ["NO", "NAMA", "HARI", "TANGGAL", "TUPOKSI", "JUMLAH", "", "HASIL FOTO\nGEOTAG"],
        ["", "", "", "", "", "TARGET", "REALISASI", ""],
    ]
    baris = []
    target = cfg["target_harian"]
    sel_style = ParagraphStyle("tp", fontName=FONT, fontSize=9, leading=11, alignment=0)
    for no, d in enumerate(hari, 1):
        # Foto dipakai berurutan dan diulang bila hari kerja lebih banyak
        n = cfg.get("jumlah_foto", 27)
        foto_path = os.path.join(HERE, cfg["foto_dir"], f"{(no - 1) % n + 1}.jpg")
        if os.path.exists(foto_path):
            sel = Image(foto_path, width=3.2 * cm, height=2.2 * cm, kind="proportional")
        else:
            sel = ""
        baris.append([str(no), cfg["nama"], HARI[d.weekday()], tgl_pendek(d),
                      Paragraph(cfg["tupoksi"], sel_style), str(target), str(target), sel])

    data = kepala + baris
    lebar = [0.8, 2.8, 1.5, 1.9, 3.4, 1.5, 2.0, 3.1]
    tabel = Table(data, colWidths=[w * cm for w in lebar], repeatRows=2)
    gaya = [
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (4, 2), (4, -1), "LEFT"),
        ("ALIGN", (1, 2), (1, -1), "LEFT"),
        ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1)),
        ("SPAN", (2, 0), (2, 1)), ("SPAN", (3, 0), (3, 1)),
        ("SPAN", (4, 0), (4, 1)), ("SPAN", (5, 0), (6, 0)),
        ("SPAN", (7, 0), (7, 1)),
        ("TOPPADDING", (0, 2), (-1, -1), 4), ("BOTTOMPADDING", (0, 2), (-1, -1), 4),
    ]
    tabel.setStyle(TableStyle(gaya))

    SimpleDocTemplate(path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm).build([tabel])


def ambil_foto_dari_pdf(pdf, hari, cfg):
    """Ambil gambar geotag dari PDF laporan (urut sesuai hari kerja)."""
    imgs = [img.image for page in PdfReader(pdf).pages for img in page.images]
    if len(imgs) == 0:
        raise SystemExit("PDF tidak punya gambar. Cek PDF-nya.")
    folder = os.path.join(HERE, cfg["foto_dir"])
    os.makedirs(folder, exist_ok=True)
    for k, im in enumerate(imgs, 1):
        im.convert("RGB").save(os.path.join(folder, f"{k}.jpg"), "JPEG", quality=90)
    print(f"Foto diambil dari PDF: {len(imgs)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bulan", help="YYYY-MM, default bulan sebelumnya")
    p.add_argument("--laporan-pdf", help="PDF laporan kegiatan untuk mengambil foto geotag")
    a = p.parse_args()
    if a.bulan:
        year, month = (int(x) for x in a.bulan.split("-"))
    else:
        year, month = bulan_lalu()

    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    out = os.path.join(HERE, cfg["output_dir"])
    os.makedirs(out, exist_ok=True)
    tag = f"{year}-{month:02d}"

    surat = os.path.join(out, f"surat_lamaran_{tag}.pdf")
    laporan = os.path.join(out, f"laporan_kegiatan_{tag}.pdf")
    buat_surat(surat, year, month, cfg)
    hari = hari_kerja(year, month, cfg)
    if a.laporan_pdf:
        ambil_foto_dari_pdf(a.laporan_pdf, hari, cfg)
    buat_laporan(laporan, hari, cfg)

    # Satu PDF gabungan: surat, lampiran (lampiran.pdf), lalu laporan kegiatan
    paket = os.path.join(out, f"{cfg.get('nama_file', cfg['nama'])}.pdf")
    bagian = [surat]
    lamp = os.path.join(HERE, "lampiran.pdf")
    if os.path.exists(lamp):
        bagian.append(lamp)
    bagian.append(laporan)
    gabung = PdfWriter()
    for b in bagian:
        gabung.append(b)
    with open(paket, "wb") as f:
        gabung.write(f)

    print(paket)
    print(f"Hari kerja dilaporkan: {len(hari)}")


if __name__ == "__main__":
    main()
