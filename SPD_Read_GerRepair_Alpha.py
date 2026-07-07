#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spd_dump_gui.py  -  DDR4 SPD-EEPROM Dumper mit GUI (Windows, Intel + AMD)
=========================================================================

Liest den kompletten 512-Byte SPD-EEPROM (JEDEC + XMP) jedes bestueckten
DDR4-Moduls ueber den SMBus aus, speichert ihn als .bin und zeigt einen
Decode direkt im Log-Fenster an.

TREIBER (einer davon reicht, im Script-Ordner):
  * inpoutx64.dll   -> installiert seinen Kernel-Treiber selbst (steckt in der
                       DLL). Kommt z.B. aus dem ZenTimings-ZIP. EMPFOHLEN.
  * WinRing0x64.dll + WinRing0x64.sys  -> aus LibreHardwareMonitor / HWiNFO.
Das Tool erkennt automatisch, welcher vorhanden ist.

BENOETIGT SONST: nichts. tkinter + ctypes sind Standard-Python (kein pip).
START: als ADMINISTRATOR (sonst laedt/installiert der Treiber nicht).

Plattformen:
  * Intel  -> SMBus i801/PCH (Class 0C05, Vendor 0x8086), Basis aus PCI-BAR
  * AMD     -> FCH SMBus (AM4: X470 usw.), Basis meist 0x0B00
"""

import ctypes
import os
import queue
import subprocess
import sys
import threading
import time

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# ==========================================================================
#  Branding / Alpha-Disclaimer
# ==========================================================================

APP_AUTHOR = "GerRepair"
APP_NAME = "SPD RAW Dumper"
APP_VERSION = "Alpha"
APP_TITLE = f"{APP_NAME} - {APP_VERSION}"

ALPHA_DISCLAIMER = (
    "ALPHA-VERSION\n\n"
    "Die Nutzung erfolgt auf eigene Verantwortung.\n\n"
    "Aktueller Stand: Diese Version ist nur zum Lesen/Dumpen von DDR4-SPD-Daten "
    "gedacht. Es werden keine SPD-Daten geschrieben.\n\n"
    "Hinweis: Bei Zeiten kann eventuell eine Schreibfunktion hinzukommen. "
    "Das Schreiben von SPD-Daten kann RAM-Module unbrauchbar machen und wird "
    "daher nur mit gesonderten Sicherheitsabfragen umgesetzt.\n\n"
    "Bitte vor dem Start andere Sensor-, RGB- und Monitoring-Tools schliessen "
    "(z.B. HWiNFO, Ryzen Master, ZenTimings, OpenRGB, AIDA64, CPU-Z-Sensoren)."
)

GERREPAIR_LOGO_PNG_BASE64 = """
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
"""


def create_logo_image(master=None):
    """Erzeugt das eingebettete GerRepair-Logo fuer Fenster-Icon und Header."""
    try:
        return tk.PhotoImage(master=master, data=GERREPAIR_LOGO_PNG_BASE64, format="png")
    except Exception:
        return None



# ==========================================================================
#  Admin / Elevation
# ==========================================================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    """Startet das Script per UAC neu (Verb 'runas'). True = Neustart ausgeloest."""
    try:
        if getattr(sys, "frozen", False):
            # gepackte .exe (PyInstaller): sich selbst starten
            exe = sys.executable
            args = sys.argv[1:] + ["--no-elevate"]
            params = subprocess.list2cmdline(args)
        else:
            exe = sys.executable  # python.exe
            script = os.path.abspath(sys.argv[0])
            args = [script] + sys.argv[1:] + ["--no-elevate"]
            params = subprocess.list2cmdline(args)
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        return int(rc) > 32  # >32 = Erfolg (Prozess gestartet)
    except Exception:
        return False


# ==========================================================================
#  Windows Treibersperrliste (Microsoft Vulnerable Driver Blocklist)
# --------------------------------------------------------------------------
#  ACHTUNG: Der Schalter betrifft die GESAMTE Blocklist, nicht nur WinRing0.
#  Ein gezieltes Entfernen einzelner Treiber ist nicht moeglich (signierte
#  CI-Policy). Aenderung wirkt erst nach einem Neustart. InpOut steht NICHT
#  auf der Blocklist - dann ist das hier gar nicht noetig.
# ==========================================================================

_BLK_KEY = r"SYSTEM\CurrentControlSet\Control\CI\Config"
_BLK_VALUE = "VulnerableDriverBlocklistEnable"


def blocklist_state():
    """1 = aktiv, 0 = deaktiviert, None = Wert nicht gesetzt/lesbar."""
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _BLK_KEY)
        try:
            val, _ = winreg.QueryValueEx(k, _BLK_VALUE)
            return int(val)
        finally:
            winreg.CloseKey(k)
    except FileNotFoundError:
        return None
    except OSError:
        return None


def blocklist_set(enable):
    """Setzt den Registry-Schalter. Braucht Admin. Wirkt nach Neustart."""
    import winreg
    k = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, _BLK_KEY, 0,
                           winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(k, _BLK_VALUE, 0, winreg.REG_DWORD, 1 if enable else 0)
    finally:
        winreg.CloseKey(k)


# ==========================================================================
#  Treiber-Abstraktion:  inb / outb / pci_read_dword
# ==========================================================================

class PortDriver:
    name = "base"
    dll_path = ""

    def inb(self, port):
        raise NotImplementedError

    def outb(self, port, value):
        raise NotImplementedError

    def pci_read_dword(self, bus, dev, func, reg):
        raise NotImplementedError

    def close(self):
        pass


def _load_dll(dll_path, candidates):
    """Versucht dll_path zuerst, dann die Kandidaten im Script-Ordner und PATH."""
    here = os.path.dirname(os.path.abspath(__file__))
    tries = ([dll_path] if dll_path else []) + \
        [os.path.join(here, c) for c in candidates] + list(candidates)
    last = None
    for t in tries:
        if not t:
            continue
        try:
            return ctypes.WinDLL(t), t
        except OSError as e:
            last = e
    raise RuntimeError("DLL nicht ladbar (%s). Letzter Fehler: %s"
                       % ("/".join(candidates), last))


class WinRing0Driver(PortDriver):
    name = "WinRing0"
    CANDIDATES = ["WinRing0x64.dll", "WinRing0.dll", "Ring0x64.dll"]

    def __init__(self, dll_path=None):
        self.dll, self.dll_path = _load_dll(dll_path, self.CANDIDATES)
        d = self.dll
        # Existenz der WinRing0-Funktionen erzwingt korrekten Treiber
        d.InitializeOls.restype = ctypes.c_bool
        d.DeinitializeOls.restype = None
        d.GetDllStatus.restype = ctypes.c_uint
        d.ReadIoPortByte.argtypes = [ctypes.c_ushort]
        d.ReadIoPortByte.restype = ctypes.c_ubyte
        d.WriteIoPortByte.argtypes = [ctypes.c_ushort, ctypes.c_ubyte]
        d.WriteIoPortByte.restype = None
        d.ReadPciConfigDword.argtypes = [ctypes.c_uint, ctypes.c_uint]
        d.ReadPciConfigDword.restype = ctypes.c_uint
        if not d.InitializeOls():
            raise RuntimeError("InitializeOls() fehlgeschlagen (Status=%d). "
                               "Admin-Rechte + WinRing0x64.sys noetig."
                               % d.GetDllStatus())
        if d.GetDllStatus() != 0:
            raise RuntimeError("GetDllStatus=%d (0=OK)." % d.GetDllStatus())

    def inb(self, port):
        return int(self.dll.ReadIoPortByte(port & 0xFFFF))

    def outb(self, port, value):
        self.dll.WriteIoPortByte(port & 0xFFFF, value & 0xFF)

    def pci_read_dword(self, bus, dev, func, reg):
        addr = ((bus & 0xFF) << 8) | ((dev & 0x1F) << 3) | (func & 0x07)
        return int(self.dll.ReadPciConfigDword(addr, reg & 0xFF))

    def close(self):
        if self.dll:
            self.dll.DeinitializeOls()
            self.dll = None


class InpOutDriver(PortDriver):
    name = "InpOut"
    CANDIDATES = ["inpoutx64.dll", "InpOutx64.dll"]

    def __init__(self, dll_path=None):
        self.dll, self.dll_path = _load_dll(dll_path, self.CANDIDATES)
        d = self.dll

        # Byte-I/O: bevorzugt DlPort..Uchar, sonst Inp32/Out32
        self._byte_dl = hasattr(d, "DlPortReadPortUchar")
        if self._byte_dl:
            d.DlPortReadPortUchar.argtypes = [ctypes.c_ushort]
            d.DlPortReadPortUchar.restype = ctypes.c_ubyte
            d.DlPortWritePortUchar.argtypes = [ctypes.c_ushort, ctypes.c_ubyte]
            d.DlPortWritePortUchar.restype = None
        elif hasattr(d, "Inp32") and hasattr(d, "Out32"):
            d.Inp32.argtypes = [ctypes.c_short]
            d.Inp32.restype = ctypes.c_short
            d.Out32.argtypes = [ctypes.c_short, ctypes.c_short]
            d.Out32.restype = None
        else:
            raise RuntimeError("Keine passende InpOut-DLL (weder "
                               "DlPortReadPortUchar noch Inp32 vorhanden) - "
                               "vermutlich falsche DLL angegeben.")

        # 32-bit-I/O fuer PCI-Config-Mechanismus #1 (0xCF8/0xCFC) - Pflicht
        if not hasattr(d, "DlPortReadPortUlong"):
            raise RuntimeError("inpoutx64.dll exportiert keine 32-bit Port-"
                               "Funktionen (DlPortReadPortUlong). Bitte eine "
                               "vollstaendige InpOutx64-Version verwenden.")
        d.DlPortReadPortUlong.argtypes = [ctypes.c_uint32]
        d.DlPortReadPortUlong.restype = ctypes.c_uint32
        d.DlPortWritePortUlong.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        d.DlPortWritePortUlong.restype = None

        if hasattr(d, "IsInpOutDriverOpen"):
            d.IsInpOutDriverOpen.restype = ctypes.c_uint32
            if d.IsInpOutDriverOpen() == 0:
                raise RuntimeError("InpOut-Kernel-Treiber nicht geoeffnet. Als "
                                   "Administrator starten (Treiber wird beim "
                                   "ersten Start installiert).")

    def inb(self, port):
        if self._byte_dl:
            return int(self.dll.DlPortReadPortUchar(port & 0xFFFF))
        return int(self.dll.Inp32(port & 0xFFFF)) & 0xFF

    def outb(self, port, value):
        if self._byte_dl:
            self.dll.DlPortWritePortUchar(port & 0xFFFF, value & 0xFF)
        else:
            self.dll.Out32(port & 0xFFFF, value & 0xFF)

    def pci_read_dword(self, bus, dev, func, reg):
        addr = (0x80000000 | ((bus & 0xFF) << 16) | ((dev & 0x1F) << 11) |
                ((func & 0x07) << 8) | (reg & 0xFC))
        self.dll.DlPortWritePortUlong(0xCF8, addr)
        return int(self.dll.DlPortReadPortUlong(0xCFC))


_DLL_KEYWORDS = {"InpOut": ["inpout"], "WinRing0": ["ring0", "winring"]}


def _dll_matches(dll_path, keywords):
    if not dll_path:
        return False
    name = os.path.basename(dll_path).lower()
    return any(k in name for k in keywords)


def open_driver(preferred, dll_path, log):
    if preferred == "winring0":
        order = [WinRing0Driver]
    elif preferred == "inpout":
        order = [InpOutDriver]
    else:  # auto
        order = [InpOutDriver, WinRing0Driver]
    errs = []
    for cls in order:
        # explizite DLL nur an den passenden Treiber geben, sonst dessen
        # eigene Kandidaten im Script-Ordner suchen lassen
        this_dll = dll_path if _dll_matches(dll_path, _DLL_KEYWORDS.get(cls.name, [])) \
            else None
        try:
            drv = cls(this_dll or None)
            log("Treiber: %s  (%s)" % (drv.name, drv.dll_path))
            return drv
        except Exception as e:
            errs.append("%s: %s" % (cls.name, e))
            log("  %s nicht verfuegbar: %s" % (cls.name, e))
    raise RuntimeError("Kein Port-Treiber verfuegbar. Lege inpoutx64.dll neben "
                       "das Script. Details:\n" + "\n".join(errs))


# ==========================================================================
#  Plattform-Erkennung
# ==========================================================================

def find_smbus_controller(drv):
    for dev in range(32):
        for func in range(8):
            vd = drv.pci_read_dword(0, dev, func, 0x00)
            if vd == 0xFFFFFFFF:
                if func == 0:
                    break
                continue
            vendor = vd & 0xFFFF
            device = (vd >> 16) & 0xFFFF
            cls = drv.pci_read_dword(0, dev, func, 0x08)
            if ((cls >> 24) & 0xFF) == 0x0C and ((cls >> 16) & 0xFF) == 0x05:
                return (vendor, device, dev, func)
    return None


def get_intel_base(drv, dev, func):
    return drv.pci_read_dword(0, dev, func, 0x20) & 0xFFE0


def get_amd_base(drv):
    """AMD FCH: DIMM-SPDs haengen am primaeren SMBus (Standard 0x0B00).
    Die PMIO-Erkennung ist auf Zen unzuverlaessig - nur uebernehmen, wenn das
    Ergebnis einer bekannten Basis entspricht, sonst auf 0x0B00 zurueckfallen.
    Der Worker probiert zusaetzlich 0x0B00/0x0B20 automatisch durch."""
    detected = 0
    try:
        drv.outb(0xCD6, 0x00)
        lo = drv.inb(0xCD7)
        drv.outb(0xCD6, 0x01)
        hi = drv.inb(0xCD7)
        detected = ((hi << 8) | lo) & 0xFFE0
    except Exception:
        detected = 0
    if detected in (0x0B00, 0x0B20):
        return detected
    return 0x0B00


def detect_platform(drv, forced="auto", forced_base=None):
    if forced_base is not None:
        return (forced if forced not in (None, "auto") else "manual"), forced_base
    ctrl = find_smbus_controller(drv)
    vendor = ctrl[0] if ctrl else None
    if forced == "intel" or (forced in (None, "auto") and vendor == 0x8086):
        if ctrl and ctrl[0] == 0x8086:
            return "intel", get_intel_base(drv, ctrl[2], ctrl[3])
        return "intel", get_intel_base(drv, 0x1F, 0x03)
    if forced == "amd" or (forced in (None, "auto") and vendor in (0x1022, 0x1002)):
        return "amd", get_amd_base(drv)
    hb = drv.pci_read_dword(0, 0, 0, 0x00) & 0xFFFF
    if hb == 0x1022:
        return "amd", get_amd_base(drv)
    if hb == 0x8086 and ctrl:
        return "intel", get_intel_base(drv, ctrl[2], ctrl[3])
    raise RuntimeError("SMBus-Controller nicht erkannt. Plattform/Basis manuell setzen.")


# ==========================================================================
#  SMBus-Zugriff (PIIX4 / i801 kompatibel)
# ==========================================================================

class SMBus:
    STS, CNT, CMD, ADD, DAT0 = 0x00, 0x02, 0x03, 0x04, 0x05
    PROTO_BYTE = 0x04 | 0x40
    PROTO_BYTE_DATA = 0x08 | 0x40
    ST_BUSY, ST_INTR = 0x01, 0x02
    ST_DEV_ERR, ST_BUS_ERR, ST_FAILED = 0x04, 0x08, 0x10

    def __init__(self, drv, base):
        self.drv = drv
        self.base = base
        self.r_sts = base + self.STS
        self.r_cnt = base + self.CNT
        self.r_cmd = base + self.CMD
        self.r_add = base + self.ADD
        self.r_dat0 = base + self.DAT0

    def _clear(self):
        self.drv.outb(self.r_sts, 0xFF)

    def _wait_free(self, timeout=0.4):
        t = time.time()
        while time.time() - t < timeout:
            if not (self.drv.inb(self.r_sts) & self.ST_BUSY):
                return True
            time.sleep(0.0002)
        return False

    def _wait_done(self, timeout=0.5):
        t = time.time()
        while time.time() - t < timeout:
            sts = self.drv.inb(self.r_sts)
            if not (sts & self.ST_BUSY):
                if sts & (self.ST_INTR | self.ST_DEV_ERR | self.ST_BUS_ERR | self.ST_FAILED):
                    return sts
            time.sleep(0.0002)
        return None

    def _transaction(self, cnt):
        self.drv.outb(self.r_cnt, cnt)
        sts = self._wait_done()
        if sts is None:
            return False
        ok = not (sts & (self.ST_DEV_ERR | self.ST_BUS_ERR | self.ST_FAILED))
        self._clear()
        return ok

    def read_byte(self, dimm_addr, offset):
        if not self._wait_free():
            return None
        self._clear()
        self.drv.outb(self.r_add, (dimm_addr << 1) | 1)
        self.drv.outb(self.r_cmd, offset & 0xFF)
        if not self._transaction(self.PROTO_BYTE_DATA):
            return None
        return self.drv.inb(self.r_dat0)

    def send_byte(self, dev_addr, value=0x00):
        if not self._wait_free():
            return False
        self._clear()
        self.drv.outb(self.r_add, (dev_addr << 1) | 0)
        self.drv.outb(self.r_cmd, value & 0xFF)
        return self._transaction(self.PROTO_BYTE)

    def set_page(self, page):
        return self.send_byte(0x36 if page == 0 else 0x37, 0x00)


def dimm_present(smbus, addr):
    smbus.set_page(0)
    val = None
    for _ in range(3):
        val = smbus.read_byte(addr, 0x02)
        if val is not None:
            break
    return val is not None and val not in (0x00, 0xFF)


def read_spd(smbus, addr, log=None):
    data = bytearray(512)
    for page in (0, 1):
        smbus.set_page(page)
        for i in range(256):
            b = None
            for _ in range(3):
                b = smbus.read_byte(addr, i)
                if b is not None:
                    break
            data[page * 256 + i] = b if b is not None else 0xFF
            if log and (i % 128 == 127):
                log("    Seite %d: %d/256 Byte" % (page, i + 1))
    smbus.set_page(0)
    return bytes(data)


# ==========================================================================
#  DDR4 Decoder
# ==========================================================================

_DENSITY_MBIT = {0: 256, 1: 512, 2: 1024, 3: 2048, 4: 4096,
                 5: 8192, 6: 16384, 7: 32768}
_MODULE_TYPE = {0x01: "RDIMM", 0x02: "UDIMM", 0x03: "SO-DIMM", 0x04: "LRDIMM",
                0x05: "Mini-RDIMM", 0x06: "Mini-UDIMM", 0x08: "72b-SO-RDIMM",
                0x09: "72b-SO-UDIMM", 0x0C: "16b-SO-DIMM", 0x0D: "32b-SO-DIMM"}
_JEDEC_MFR = {(1, 0x4E): "Samsung", (1, 0x2D): "SK Hynix", (1, 0x2C): "Micron",
              (1, 0x0B): "Nanya", (1, 0x1C): "Mitsubishi", (1, 0x4F): "Winbond/Nuvoton",
              (2, 0x98): "Kingston", (3, 0x25): "Kingmax", (5, 0x1F): "Apacer",
              (5, 0x4D): "G.Skill / G.Skill Intl", (6, 0x04): "G.Skill",
              (7, 0x9E): "Corsair", (2, 0x9B): "Crucial (Micron)"}


def _jedec_name(bank_byte, id_byte):
    bank = (bank_byte & 0x7F) + 1
    ident = id_byte & 0x7F
    return _JEDEC_MFR.get((bank, ident),
                          "Unbekannt (Bank %d, ID 0x%02X)" % (bank, ident))


def _signed8(v):
    return v - 256 if v & 0x80 else v


def decode_ddr4(b):
    out = []
    if b[2] != 0x0C:
        return "DRAM Device Type : 0x%02X (kein DDR4)" % b[2]
    out.append("DRAM Device Type : DDR4 SDRAM (0x0C)")
    mt = b[3] & 0x0F
    out.append("Module Type      : %s (0x%02X)" % (_MODULE_TYPE.get(mt, "?"), b[3]))
    sdram_mbit = _DENSITY_MBIT.get(b[4] & 0x0F, 0)
    out.append("SDRAM Die Density: %d Mbit" % sdram_mbit)
    out.append("Addressing       : %d Row-Bits, %d Column-Bits"
               % (12 + ((b[5] >> 3) & 0x07), 9 + (b[5] & 0x07)))
    dev_w = 4 << (b[12] & 0x07)
    ranks = ((b[12] >> 3) & 0x07) + 1
    out.append("Organisation     : x%d, %d Rank(s)" % (dev_w, ranks))
    prim = 8 << (b[13] & 0x07)
    ecc = " + 8b ECC" if ((b[13] >> 3) & 0x03) == 1 else ""
    out.append("Bus Width        : %d bit%s" % (prim, ecc))
    if sdram_mbit and dev_w:
        cap = (sdram_mbit / 8.0) * (prim / float(dev_w)) * ranks
        out.append("Kapazitaet       : %.0f MB (%.2f GB)" % (cap, cap / 1024.0))
    tck = b[18] * 0.125 + _signed8(b[125]) * 0.001
    if tck > 0:
        mtps = int(round((2000.0 / tck) / 100.0) * 100)
        out.append("Geschwindigkeit  : DDR4-%d (%d MT/s, tCK=%.3f ns)" % (mtps, mtps, tck))
    out.append("Modul-Hersteller : %s" % _jedec_name(b[320], b[321]))
    out.append("Herstelldatum    : Jahr 20%02X, Woche %02X" % (b[323], b[324]))
    out.append("Seriennummer     : %s" % bytes(b[325:329]).hex().upper())
    part = bytes(b[329:349]).decode("ascii", errors="replace").strip("\x00 ").strip()
    out.append("Part Number      : %s" % (part or "(leer)"))
    out.append("DRAM-Hersteller  : %s" % _jedec_name(b[350], b[351]))
    if b[384] == 0x0C and b[385] == 0x4A:
        out.append("XMP              : vorhanden (Magic OK)")
    else:
        out.append("XMP              : nicht gefunden")
    return "\n".join(out)


# ==========================================================================
#  Worker (Hintergrund-Thread, loggt via Queue)
# ==========================================================================

def dump_worker(cfg, logq, done_cb):
    def log(msg):
        logq.put(msg)

    drv = None
    try:
        log("Treiber wird geladen ...")
        drv = open_driver(cfg["driver"], cfg["dll"], log)

        name, base = detect_platform(drv, cfg["platform"], cfg["base"])
        log("Plattform: %s" % name.upper())

        addrs = [cfg["addr"]] if cfg["addr"] is not None else list(range(0x50, 0x58))

        # Basis-Kandidaten: bei AMD ohne manuelle Basis die Standardwerte
        # automatisch durchprobieren (PMIO-Erkennung ist auf Zen unzuverlaessig).
        if cfg["base"] is None and name == "amd":
            bases = []
            for b in (base, 0x0B00, 0x0B20):
                if b and b not in bases:
                    bases.append(b)
        else:
            bases = [base]

        smbus = None
        used_base = None
        for b in bases:
            test = SMBus(drv, b)
            if any(dimm_present(test, a) for a in addrs):
                smbus = test
                used_base = b
                break
            if len(bases) > 1:
                log("  keine DIMMs @ SMBus-Basis 0x%04X" % b)

        if smbus is None:
            log("")
            log("Kein DIMM gefunden. Pruefe Basis/Plattform oder schliesse "
                "SMBus-belegende Tools (Ryzen Master, HWiNFO, ZenTimings).")
            return

        log("SMBus-Basis: 0x%04X" % used_base)
        found = 0
        for addr in addrs:
            if not dimm_present(smbus, addr):
                continue
            found += 1
            log("")
            log("DIMM @ 0x%02X gefunden - lese 512 Byte ..." % addr)
            spd = read_spd(smbus, addr, log)

            bin_path = os.path.join(cfg["out"], "spd_dimm_0x%02X.bin" % addr)
            with open(bin_path, "wb") as f:
                f.write(spd)
            log("  gespeichert: %s" % bin_path)

            if cfg["decode"]:
                decoded = decode_ddr4(spd)
                txt_path = os.path.join(cfg["out"], "spd_dimm_0x%02X.txt" % addr)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(decoded + "\n")
                log("  --- Decode ---")
                for line in decoded.split("\n"):
                    log("  " + line)

        log("")
        log("FERTIG - %d Modul(e) ausgelesen." % found)
    except Exception as e:
        log("FEHLER: %s" % e)
    finally:
        if drv is not None:
            drv.close()
        done_cb()


# ==========================================================================
#  GUI
# ==========================================================================

class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("860x650")
        root.minsize(760, 520)

        self.logq = queue.Queue()
        self.running = False

        self.logo_image = create_logo_image(root)
        if self.logo_image is not None:
            try:
                root.iconphoto(True, self.logo_image)
            except Exception:
                pass

        self.driver = tk.StringVar(value="auto")
        self.platform = tk.StringVar(value="auto")
        self.base = tk.StringVar(value="")
        self.addr = tk.StringVar(value="")
        self.outdir = tk.StringVar(value=os.getcwd())
        self.dll = tk.StringVar(value="")
        self.decode = tk.BooleanVar(value=True)

        self._build()
        self._poll_log()

        admin = self._is_admin()
        self.status.set("Admin: %s   |   Bereit" % ("JA" if admin else "NEIN"))
        if not admin:
            self._append("WARNUNG: Nicht als Administrator gestartet - der "
                         "Treiber laedt/installiert vermutlich nicht.\n")
            self._append("Tipp: Menue 'Extras > Als Administrator neu starten'.\n")
        self._append("Bereit. inpoutx64.dll (oder WinRing0x64.dll+.sys) muss im "
                     "Script-Ordner liegen.\n")
        self.root.after(250, self._show_alpha_disclaimer)

    def _build(self):
        # --- Menuebar ---
        menubar = tk.Menu(self.root)
        extras = tk.Menu(menubar, tearoff=0)
        extras.add_command(label="Als Administrator neu starten",
                           command=self._elevate)
        extras.add_separator()
        extras.add_command(label="WinRing0-Treiber testen",
                           command=self._test_winring0)
        blk = tk.Menu(extras, tearoff=0)
        blk.add_command(label="Status anzeigen", command=self._blk_status)
        blk.add_command(label="Deaktivieren (Neustart noetig) ...",
                        command=self._blk_disable)
        blk.add_command(label="Wieder aktivieren ...", command=self._blk_enable)
        extras.add_cascade(label="Windows Treibersperrliste", menu=blk)
        menubar.add_cascade(label="Extras", menu=extras)
        self.root.config(menu=menubar)

        pad = dict(padx=6, pady=4)

        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=8, pady=(8, 4))
        if self.logo_image is not None:
            ttk.Label(header, image=self.logo_image).pack(side="left", padx=(0, 10))
        header_text = ttk.Frame(header)
        header_text.pack(side="left", fill="x", expand=True)
        ttk.Label(header_text, text=APP_NAME,
                  font=("Segoe UI", 15, "bold")).pack(anchor="w")

        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)

        ttk.Label(top, text="Treiber:").grid(row=0, column=0, sticky="w")
        for i, (lbl, val) in enumerate([("Auto", "auto"), ("InpOut", "inpout"),
                                        ("WinRing0", "winring0")]):
            ttk.Radiobutton(top, text=lbl, value=val,
                            variable=self.driver).grid(row=0, column=1 + i, sticky="w")

        ttk.Label(top, text="Plattform:").grid(row=1, column=0, sticky="w")
        for i, (lbl, val) in enumerate([("Auto", "auto"), ("Intel", "intel"),
                                        ("AMD", "amd")]):
            ttk.Radiobutton(top, text=lbl, value=val,
                            variable=self.platform).grid(row=1, column=1 + i, sticky="w")

        ttk.Label(top, text="SMBus-Basis (leer=auto):").grid(row=2, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.base, width=12).grid(row=2, column=1, sticky="w")
        ttk.Label(top, text="z.B. 0x0B00").grid(row=2, column=2, columnspan=2, sticky="w")

        ttk.Label(top, text="DIMM-Adresse (leer=alle):").grid(row=3, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.addr, width=12).grid(row=3, column=1, sticky="w")
        ttk.Label(top, text="0x50 .. 0x57").grid(row=3, column=2, columnspan=2, sticky="w")

        outf = ttk.Frame(self.root)
        outf.pack(fill="x", **pad)
        ttk.Label(outf, text="Zielordner:").pack(side="left")
        ttk.Entry(outf, textvariable=self.outdir).pack(side="left", fill="x",
                                                       expand=True, padx=4)
        ttk.Button(outf, text="...", width=3, command=self._browse_out).pack(side="left")

        dllf = ttk.Frame(self.root)
        dllf.pack(fill="x", **pad)
        ttk.Label(dllf, text="Treiber-DLL (optional):").pack(side="left")
        ttk.Entry(dllf, textvariable=self.dll).pack(side="left", fill="x",
                                                    expand=True, padx=4)
        ttk.Button(dllf, text="...", width=3, command=self._browse_dll).pack(side="left")

        btnf = ttk.Frame(self.root)
        btnf.pack(fill="x", **pad)
        ttk.Checkbutton(btnf, text="Decode erzeugen",
                        variable=self.decode).pack(side="left")
        self.btn_run = ttk.Button(btnf, text="Scan & Dump", command=self._start)
        self.btn_run.pack(side="right")
        ttk.Button(btnf, text="Log speichern",
                   command=self._save_log).pack(side="right", padx=4)
        ttk.Button(btnf, text="Log leeren", command=self._clear_log).pack(side="right")

        self.log = scrolledtext.ScrolledText(self.root, height=18, wrap="word",
                                             font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, padx=6, pady=6)
        self.log.configure(state="disabled")

        self.status = tk.StringVar(value="Bereit")
        ttk.Label(self.root, textvariable=self.status,
                  relief="sunken", anchor="w").pack(fill="x", side="bottom")

    def _show_alpha_disclaimer(self):
        self._append("\n[Alpha-Disclaimer]\n")
        for line in ALPHA_DISCLAIMER.split("\n"):
            self._append(line + "\n")
        self._append("\n")
        messagebox.showwarning("Alpha-Disclaimer", ALPHA_DISCLAIMER, parent=self.root)

    def _is_admin(self):
        return is_admin()

    # ---- Extras: Admin / Treiber / Blocklist ----
    def _elevate(self):
        if self._is_admin():
            messagebox.showinfo("Administrator", "Laeuft bereits als Administrator.")
            return
        if relaunch_as_admin():
            self.root.destroy()  # erhoehte Instanz uebernimmt
        else:
            messagebox.showwarning("Administrator",
                                   "Neustart als Administrator wurde abgelehnt "
                                   "oder ist fehlgeschlagen.")

    def _test_winring0(self):
        self._append("\nTeste WinRing0-Treiber ...\n")
        try:
            drv = WinRing0Driver(self.dll.get().strip() or None)
            drv.close()
            self._append("WinRing0 laedt sauber - nicht blockiert.\n")
            messagebox.showinfo("WinRing0", "WinRing0 laedt sauber (nicht blockiert).")
        except Exception as e:
            self._append("WinRing0 nicht ladbar: %s\n" % e)
            self._append("Falls die Sperrliste die Ursache ist: 'Extras > Windows "
                         "Treibersperrliste'. Oder einfach InpOut nutzen "
                         "(nicht betroffen).\n")
            messagebox.showwarning(
                "WinRing0",
                "WinRing0 laedt nicht:\n%s\n\nMoegliche Ursachen: keine Admin-"
                "Rechte, WinRing0x64.sys fehlt, oder Treibersperrliste blockiert "
                "den Treiber. InpOut ist davon nicht betroffen." % e)

    def _blk_status(self):
        st = blocklist_state()
        txt = {1: "AKTIV (blockiert anfaellige Treiber)",
               0: "DEAKTIVIERT",
               None: "Standard/nicht gesetzt (auf Win11 meist aktiv)"}[st]
        self._append("\nTreibersperrliste: %s\n" % txt)
        messagebox.showinfo("Treibersperrliste", "Aktueller Status: %s" % txt)

    def _blk_disable(self):
        if not self._is_admin():
            messagebox.showwarning("Admin noetig",
                                   "Zum Aendern der Sperrliste als Administrator "
                                   "starten (Extras > Als Administrator neu starten).")
            return
        warn = ("Dies deaktiviert die GESAMTE Microsoft-Treibersperrliste - "
                "nicht nur WinRing0. Damit koennen auch andere bekannt "
                "verwundbare Treiber wieder geladen werden; die Sicherheit "
                "deines Systems sinkt.\n\n"
                "Empfehlung: stattdessen InpOut nutzen - das ist NICHT auf der "
                "Sperrliste, dann ist dieser Schritt unnoetig.\n\n"
                "Die Aenderung wirkt erst nach einem NEUSTART.\n\n"
                "Trotzdem deaktivieren?")
        if not messagebox.askyesno("Warnung - Sperrliste deaktivieren", warn,
                                    icon="warning", default="no"):
            return
        try:
            blocklist_set(False)
            self._append("\nTreibersperrliste auf DEAKTIVIERT gesetzt. Neustart "
                         "noetig, damit es wirkt.\n")
            if messagebox.askyesno("Neustart", "Gesetzt. Jetzt neu starten?"):
                subprocess.Popen(["shutdown", "/r", "/t", "5"])
        except Exception as e:
            self._append("FEHLER beim Setzen: %s\n" % e)
            messagebox.showerror("Fehler", "Konnte Registry nicht schreiben:\n%s\n"
                                 "(Admin-Rechte noetig.)" % e)

    def _blk_enable(self):
        if not self._is_admin():
            messagebox.showwarning("Admin noetig", "Bitte als Administrator starten.")
            return
        try:
            blocklist_set(True)
            self._append("\nTreibersperrliste wieder AKTIVIERT (empfohlen). "
                         "Neustart noetig.\n")
            if messagebox.askyesno("Neustart", "Aktiviert. Jetzt neu starten?"):
                subprocess.Popen(["shutdown", "/r", "/t", "5"])
        except Exception as e:
            self._append("FEHLER beim Setzen: %s\n" % e)
            messagebox.showerror("Fehler", "Konnte Registry nicht schreiben:\n%s" % e)

    def _browse_out(self):
        d = filedialog.askdirectory(initialdir=self.outdir.get() or os.getcwd())
        if d:
            self.outdir.set(d)

    def _browse_dll(self):
        f = filedialog.askopenfilename(title="Treiber-DLL waehlen",
                                       filetypes=[("DLL", "*.dll"), ("Alle", "*.*")])
        if f:
            self.dll.set(f)

    def _append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _save_log(self):
        f = filedialog.asksaveasfilename(defaultextension=".txt",
                                         filetypes=[("Text", "*.txt")])
        if f:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(self.log.get("1.0", "end"))
            self.status.set("Log gespeichert: %s" % f)

    def _poll_log(self):
        try:
            while True:
                self._append(self.logq.get_nowait() + "\n")
        except queue.Empty:
            pass
        self.root.after(80, self._poll_log)

    def _start(self):
        if self.running:
            return
        try:
            base = int(self.base.get(), 0) if self.base.get().strip() else None
        except ValueError:
            messagebox.showerror("Fehler", "SMBus-Basis ungueltig (z.B. 0x0B00).")
            return
        try:
            addr = int(self.addr.get(), 0) if self.addr.get().strip() else None
        except ValueError:
            messagebox.showerror("Fehler", "DIMM-Adresse ungueltig (z.B. 0x50).")
            return
        out = self.outdir.get().strip() or os.getcwd()
        try:
            os.makedirs(out, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Fehler", "Zielordner: %s" % e)
            return

        cfg = {"driver": self.driver.get(), "platform": self.platform.get(),
               "base": base, "addr": addr, "out": out,
               "dll": self.dll.get().strip(), "decode": self.decode.get()}

        self.running = True
        self.btn_run.configure(state="disabled")
        self.status.set("Laeuft ...")
        self._append("\n=== Scan gestartet ===\n")
        threading.Thread(target=dump_worker, args=(cfg, self.logq, self._done),
                         daemon=True).start()

    def _done(self):
        self.root.after(0, self._finish)

    def _finish(self):
        self.running = False
        self.btn_run.configure(state="normal")
        self.status.set("Bereit")


def main():
    if os.name != "nt":
        print("Dieses Tool laeuft nur unter Windows.")
        return

    # Auto-Elevation: ohne Admin per UAC neu starten (ausser --no-elevate).
    if "--no-elevate" not in sys.argv and not is_admin():
        if relaunch_as_admin():
            return  # erhoehte Instanz uebernimmt, diese hier beenden
        # UAC abgelehnt oder fehlgeschlagen -> ohne Admin weiter (Warnung in GUI)

    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
