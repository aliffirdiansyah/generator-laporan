"use client";

import { useEffect, useState } from "react";

function bulanLalu(): string {
  const d = new Date();
  d.setDate(1);
  d.setDate(0);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function Home() {
  const [bulan, setBulan] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setBulan(bulanLalu());
  }, []);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const fd = new FormData(e.currentTarget);
    fd.set("bulan", bulan);

    try {
      const res = await fetch("/api/generate", { method: "POST", body: fd });
      if (!res.ok) {
        const j = await res.json();
        throw new Error(j.error ?? "Gagal membuat PDF");
      }
      const disp = res.headers.get("Content-Disposition") ?? "";
      const name = /filename="([^"]+)"/.exec(disp)?.[1] ?? "laporan.pdf";
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: 560, margin: "40px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Laporan Bulanan</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Surat lamaran, lampiran, dan laporan kegiatan jadi satu PDF.
      </p>

      <form onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <label style={{ display: "grid", gap: 4 }}>
          Bulan laporan
          <input
            type="month"
            value={bulan.slice(0, 7)}
            onChange={(e) => setBulan(e.target.value)}
            required
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          PDF laporan kegiatan (opsional, untuk mengambil foto geotag)
          <input name="laporan" type="file" accept="application/pdf" />
        </label>

        <button type="submit" disabled={busy} style={{ padding: "10px 14px", fontSize: 15 }}>
          {busy ? "Membuat PDF..." : "Buat PDF"}
        </button>
      </form>

      {error && (
        <pre style={{ color: "#b00020", whiteSpace: "pre-wrap", marginTop: 16 }}>{error}</pre>
      )}

      <p style={{ color: "#666", fontSize: 13, marginTop: 24 }}>
        Kalau PDF laporan tidak diunggah, foto dari bulan sebelumnya yang dipakai.
      </p>
    </main>
  );
}
