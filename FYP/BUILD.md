# Building & Packaging ClearSkyRFI

---

## Linux

### Prerequisites

- PyInstaller installed in the project venv
- `ffmpeg` available on the target system (declared as a `.deb` dependency)
- Icon assets present at `GUI/icons/`
- Linux icon set present at `GUI/icons/linux_icon/hicolor/`

### Step 1 — Build the binary

Run from the project root with the venv active:

```bash
pyinstaller --onefile --clean \
  --distpath ~/rfi-dist \
  --workpath ~/rfi-build \
  --name ClearSkyRFI \
  --icon GUI/icons/icon.ico \
  --add-data "visualisation/spinner.gif;visualisation" \
  --additional-hooks-dir=hooks \
  app.py
```

Output binary: `~/rfi-dist/ClearSkyRFI`

### Step 2 — Package as a `.deb`

#### 2a. Clean previous build artifacts

```bash
rm -rf ~/clearskyrfi-deb
rm -f ~/clearskyrfi-1.0.0-amd64.deb
```

#### 2b. Create directory structure

```bash
mkdir -p ~/clearskyrfi-deb/DEBIAN
mkdir -p ~/clearskyrfi-deb/usr/bin
mkdir -p ~/clearskyrfi-deb/usr/share/applications
mkdir -p ~/clearskyrfi-deb/usr/share/icons/hicolor
```

#### 2c. Copy files into staging directory

```bash
# Binary
cp ~/rfi-dist/ClearSkyRFI ~/clearskyrfi-deb/usr/bin/
chmod 755 ~/clearskyrfi-deb/usr/bin/ClearSkyRFI

# Icons (full hicolor theme)
cp -r ~/PUCV-CIIRID-IDEA/FYP/GUI/icons/linux_icon/hicolor/* \
      ~/clearskyrfi-deb/usr/share/icons/hicolor/
```

#### 2d. Write package metadata

```bash
cat > ~/clearskyrfi-deb/DEBIAN/control << EOF
Package: clearskyrfi
Version: 0.0.1
Section: science
Priority: optional
Architecture: amd64
Maintainer: Jackson Green <jacksonuea@gmail.com>
Depends: ffmpeg
Description: Satellite RFI Predictor
 Predicts radio frequency interference from satellite constellations
 during radio astronomy observations.
EOF

chmod 644 ~/clearskyrfi-deb/DEBIAN/control
```

#### 2e. Write desktop entry

```bash
cat > ~/clearskyrfi-deb/usr/share/applications/clearskyrfi.desktop << EOF
[Desktop Entry]
Name=ClearSkyRFI
Comment=Satellite RFI Predictor
Exec=/usr/bin/ClearSkyRFI
Icon=ClearSkyRFI
Terminal=false
Type=Application
Categories=Science;
EOF

chmod 644 ~/clearskyrfi-deb/usr/share/applications/clearskyrfi.desktop
```

#### 2f. Build the package

```bash
dpkg-deb --build ~/clearskyrfi-deb ~/clearskyrfi-1.0.0-amd64.deb
```

### Step 3 — Install

```bash
sudo dpkg -i ~/clearskyrfi-1.0.0-amd64.deb
```

### Uninstall & full clean

```bash
# Remove installed package
sudo dpkg -r clearskyrfi

# Remove any leftover binaries
sudo rm -f /usr/bin/ClearSkyRFI
sudo rm -f /usr/local/bin/ClearSkyRFI

# Remove desktop integration artifacts
sudo rm -f /usr/share/applications/clearskyrfi.desktop
sudo rm -f /usr/share/icons/hicolor/*/apps/ClearSkyRFI.png
sudo rm -f /usr/share/icons/hicolor/scalable/apps/ClearSkyRFI.svg
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

# Remove build artifacts
rm -rf ~/clearskyrfi-deb
rm -rf ~/clearskyrfi-1.0.0-amd64.deb
rm -rf ~/rfi-build
rm -rf ~/rfi-dist

# Optional: remove user runtime state (full reset)
rm -rf ~/.clearskyrfi

# Clear shell command cache
hash -r
```

---

## Windows

### Prerequisites

- PyInstaller installed in the project venv
- [Inno Setup](https://jrsoftware.org/isinfo.php) installed
- FFmpeg Windows build placed at `vendor\ffmpeg\` in the project root
  (the installer bundles it — ffmpeg is not required to be pre-installed)
- Icon asset present at `GUI\icons\icon.ico`

### Step 1 — Build the executable

Run from the project root in a Command Prompt or PowerShell with the venv active:

```bat
pyinstaller --onefile --clean ^
  --distpath dist ^
  --workpath build ^
  --name ClearSkyRFI ^
  --icon GUI\icons\icon.ico ^
  --add-data "visualisation\spinner.gif;visualisation" ^
  --additional-hooks-dir=hooks ^
  app.py
```

Output executable: `dist\ClearSkyRFI.exe`

### Step 2 — Build the installer

Open `ClearSkyRFI.iss` in Inno Setup Compiler and click **Build → Compile**,
or run from the command line:

```bat
iscc ClearSkyRFI.iss
```

Output installer: `installer\ClearSkyRFI-Setup.exe`

The installer:
- Installs to `%ProgramFiles%\ClearSkyRFI` by default
- Bundles FFmpeg from `vendor\ffmpeg\` into the install directory (no separate FFmpeg install required)
- Creates a Start Menu group and a desktop shortcut
- Offers to launch the app immediately after install

### Uninstall

Use **Add or Remove Programs** in Windows Settings, or run the uninstaller
from `%ProgramFiles%\ClearSkyRFI`.
