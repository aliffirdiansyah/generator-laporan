import { execFile } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";

const execFileP = promisify(execFile);
const GEN_DIR = path.join(process.cwd(), "generator");

export async function POST(req: Request) {
  const form = await req.formData();
  const bulan = String(form.get("bulan") ?? "");
  if (!/^\d{4}-\d{2}$/.test(bulan)) {
    return NextResponse.json({ error: "Bulan tidak valid" }, { status: 400 });
  }

  const laporan = form.get("laporan");
  const args = ["generate.py", "--bulan", bulan];
  let tmp: string | null = null;

  try {
    if (laporan instanceof File && laporan.size > 0) {
      tmp = path.join(os.tmpdir(), `laporan-${Date.now()}.pdf`);
      await fs.writeFile(tmp, Buffer.from(await laporan.arrayBuffer()));
      args.push("--laporan-pdf", tmp);
    }

    await execFileP(process.env.PYTHON ?? "python3", args, { cwd: GEN_DIR });

    const cfg = JSON.parse(await fs.readFile(path.join(GEN_DIR, "config.json"), "utf8"));
    const name = `${cfg.nama_file ?? cfg.nama}.pdf`;
    const data = await fs.readFile(path.join(GEN_DIR, cfg.output_dir ?? "output", name));

    return new NextResponse(data, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${name}"`,
      },
    });
  } catch (e: unknown) {
    const err = e as { stderr?: string; message?: string };
    return NextResponse.json(
      { error: err.stderr || err.message || "Gagal membuat PDF" },
      { status: 500 },
    );
  } finally {
    if (tmp) await fs.rm(tmp, { force: true });
  }
}
