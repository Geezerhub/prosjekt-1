"""Build a Windows .exe and installer for the Tkinter app.

Usage (on Windows):
    py -m pip install pyinstaller
    # Install Inno Setup so ISCC is available in PATH
    py build_windows_exe.py
"""

from __future__ import annotations

import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

APP_NAME = "What's cookin'"
APP_VERSION = "1.0.0"
ICON_FILE = Path("chef_hat.ico")
ENTRYPOINT = Path("recipe_app.py")
DIST_DIR = Path("dist")
EXE_FILE = DIST_DIR / f"{APP_NAME}.exe"
INNO_SCRIPT = Path("installer.iss")


def _draw_circle(px: list[list[tuple[int, int, int, int]]], cx: int, cy: int, r: int, color: tuple[int, int, int, int]) -> None:
    r2 = r * r
    size = len(px)
    for y in range(size):
        dy2 = (y - cy) * (y - cy)
        for x in range(size):
            dx2 = (x - cx) * (x - cx)
            if dx2 + dy2 <= r2:
                px[y][x] = color


def _draw_rect(
    px: list[list[tuple[int, int, int, int]]],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: tuple[int, int, int, int],
) -> None:
    size = len(px)
    x1 = max(0, min(size - 1, x1))
    x2 = max(0, min(size, x2))
    y1 = max(0, min(size - 1, y1))
    y2 = max(0, min(size, y2))
    for y in range(y1, y2):
        for x in range(x1, x2):
            px[y][x] = color


def _create_chef_hat_icon(path: Path, size: int = 64) -> None:
    transparent = (0, 0, 0, 0)
    white = (246, 246, 246, 255)
    border = (65, 65, 65, 255)
    shadow = (214, 214, 214, 255)

    pixels = [[transparent for _ in range(size)] for _ in range(size)]

    # Puffy top.
    _draw_circle(pixels, int(size * 0.34), int(size * 0.33), int(size * 0.18), white)
    _draw_circle(pixels, int(size * 0.50), int(size * 0.27), int(size * 0.20), white)
    _draw_circle(pixels, int(size * 0.66), int(size * 0.33), int(size * 0.18), white)

    # Brim.
    _draw_rect(pixels, int(size * 0.22), int(size * 0.42), int(size * 0.78), int(size * 0.62), white)
    _draw_rect(pixels, int(size * 0.22), int(size * 0.58), int(size * 0.78), int(size * 0.62), shadow)

    # Border for contrast.
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            if pixels[y][x][3] == 0:
                continue
            if any(pixels[y + dy][x + dx][3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                pixels[y][x] = border

    # Refill inside border for clean look.
    _draw_circle(pixels, int(size * 0.34), int(size * 0.33), int(size * 0.15), white)
    _draw_circle(pixels, int(size * 0.50), int(size * 0.27), int(size * 0.16), white)
    _draw_circle(pixels, int(size * 0.66), int(size * 0.33), int(size * 0.15), white)
    _draw_rect(pixels, int(size * 0.24), int(size * 0.44), int(size * 0.76), int(size * 0.60), white)

    # Convert RGBA -> BGRA bytes, bottom-up (BMP format in ICO).
    bgra = bytearray()
    for y in reversed(range(size)):
        row = pixels[y]
        for r, g, b, a in row:
            bgra.extend((b, g, r, a))

    # 1-bit AND mask (transparent mask), 32-bit aligned rows.
    mask_row_bytes = ((size + 31) // 32) * 4
    and_mask = bytearray(mask_row_bytes * size)

    # DIB header
    dib_header = struct.pack(
        "<IIIHHIIIIII",
        40,
        size,
        size * 2,
        1,
        32,
        0,
        len(bgra) + len(and_mask),
        0,
        0,
        0,
        0,
    )
    image_data = dib_header + bgra + and_mask

    # ICO header + one directory entry
    ico_header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        0 if size == 256 else size,
        0 if size == 256 else size,
        0,
        0,
        1,
        32,
        len(image_data),
        6 + 16,
    )

    path.write_bytes(ico_header + entry + image_data)


def main() -> int:
    if os.name != "nt":
        print("This build script must be run on Windows to produce a .exe file.")
        return 1

    if not ENTRYPOINT.exists():
        print(f"Missing entrypoint: {ENTRYPOINT}")
        return 1

    _create_chef_hat_icon(ICON_FILE)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        "--name",
        APP_NAME,
        "--icon",
        str(ICON_FILE),
        str(ENTRYPOINT),
    ]

    print("Running:", " ".join(command))
    pyinstaller_exit = subprocess.call(command)
    if pyinstaller_exit != 0:
        return pyinstaller_exit

    if not EXE_FILE.exists():
        print(f"Could not find generated executable: {EXE_FILE}")
        return 1

    inno_compiler = shutil.which("ISCC")
    if not inno_compiler:
        print(
            "Inno Setup compiler (ISCC) not found. Install Inno Setup and run this script again "
            "to build an installable setup with desktop shortcut."
        )
        return 1

    _write_inno_setup_script(INNO_SCRIPT, EXE_FILE, ICON_FILE)
    installer_command = [inno_compiler, str(INNO_SCRIPT)]
    print("Running:", " ".join(installer_command))
    return subprocess.call(installer_command)


def _write_inno_setup_script(script_path: Path, exe_path: Path, icon_path: Path) -> None:
    app_id = "{{2B8D7138-F623-4A6B-B4F1-0EE26A9FA702}}"
    script = f"""[Setup]
AppId={app_id}
AppName=What's Cookin'
AppVersion={APP_VERSION}
DefaultDirName={{autopf}}\\What's Cookin'
DefaultGroupName=What's Cookin'
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=What's_Cookin_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={{app}}\\chef_hat.ico

[Languages]
Name: "norwegian"; MessagesFile: "compiler:Languages\\Norwegian.isl"

[Tasks]
Name: "desktopicon"; Description: "Lag en snarvei på skrivebordet"; GroupDescription: "Ekstra oppgaver:"

[Files]
Source: "{exe_path.resolve()}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{icon_path.resolve()}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\What's Cookin'"; Filename: "{{app}}\\{APP_NAME}.exe"; IconFilename: "{{app}}\\chef_hat.ico"
Name: "{{autodesktop}}\\What's Cookin'"; Filename: "{{app}}\\{APP_NAME}.exe"; IconFilename: "{{app}}\\chef_hat.ico"; Tasks: desktopicon
"""
    script_path.write_text(script, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
