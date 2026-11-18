"""Native Windows keyboard layout: C source against kbd.h, plus the resource
file, module definition, and build/install scripts.

Windows dead keys can only produce single characters from the Basic
Multilingual Plane (BMP), so dead-key results outside of it are dropped; a
plain key can still type one as a surrogate pair ("ligature").
"""

from importlib.resources import files
from pathlib import Path

from .model import Char, Dead, Layout

# Columns of the character table (Windows modification numbers):
# 0 plain, 1 Shift, 2 Ctrl, 3 Shift+Ctrl, 4 AltGr, 5 Shift+AltGr
COLUMN_LAYERS = {0: "base", 1: "shift", 4: "option", 5: "shift-option"}

# Control characters of the standard US layout (Ctrl, Shift+Ctrl columns).
CTRL_CHARS = {
    "VK_OEM_4": (0x1B, None), "VK_OEM_6": (0x1D, None),
    "VK_OEM_5": (0x1C, None), "VK_OEM_102": (0x1C, None),
    "VK_SPACE": (0x20, None), "'2'": (None, 0x00), "'6'": (None, 0x1E),
    "VK_OEM_MINUS": (None, 0x1F),
}

C_TEMPLATE = r"""// {name} keyboard layout for Windows
//
// Generated from layout.toml by layoutgen. Do not edit.
//
// {copyright}. MIT License.

#define KBD_TYPE 4

#include <windows.h>
#include <kbd.h>

static VSC_LPWSTR key_names[] = {{
    {{0x01, L"Esc"}},
    {{0x0E, L"Backspace"}},
    {{0x0F, L"Tab"}},
    {{0x1C, L"Enter"}},
    {{0x1D, L"Ctrl"}},
    {{0x2A, L"Shift"}},
    {{0x36, L"Right Shift"}},
    {{0x37, L"Num *"}},
    {{0x38, L"Alt"}},
    {{0x39, L"Space"}},
    {{0x3A, L"Caps Lock"}},
    {{0x3B, L"F1"}},
    {{0x3C, L"F2"}},
    {{0x3D, L"F3"}},
    {{0x3E, L"F4"}},
    {{0x3F, L"F5"}},
    {{0x40, L"F6"}},
    {{0x41, L"F7"}},
    {{0x42, L"F8"}},
    {{0x43, L"F9"}},
    {{0x44, L"F10"}},
    {{0x45, L"Pause"}},
    {{0x46, L"Scroll Lock"}},
    {{0x47, L"Num 7"}},
    {{0x48, L"Num 8"}},
    {{0x49, L"Num 9"}},
    {{0x4A, L"Num -"}},
    {{0x4B, L"Num 4"}},
    {{0x4C, L"Num 5"}},
    {{0x4D, L"Num 6"}},
    {{0x4E, L"Num +"}},
    {{0x4F, L"Num 1"}},
    {{0x50, L"Num 2"}},
    {{0x51, L"Num 3"}},
    {{0x52, L"Num 0"}},
    {{0x53, L"Num Del"}},
    {{0x54, L"Sys Req"}},
    {{0x57, L"F11"}},
    {{0x58, L"F12"}},
    {{0x00, NULL}}
}};

static VSC_LPWSTR key_names_ext[] = {{
    {{0x1C, L"Num Enter"}},
    {{0x1D, L"Right Ctrl"}},
    {{0x35, L"Num /"}},
    {{0x37, L"Prnt Scrn"}},
    {{0x38, L"Right Alt"}},
    {{0x45, L"Num Lock"}},
    {{0x46, L"Break"}},
    {{0x47, L"Home"}},
    {{0x48, L"Up"}},
    {{0x49, L"Page Up"}},
    {{0x4B, L"Left"}},
    {{0x4D, L"Right"}},
    {{0x4F, L"End"}},
    {{0x50, L"Down"}},
    {{0x51, L"Page Down"}},
    {{0x52, L"Insert"}},
    {{0x53, L"Delete"}},
    {{0x54, L"<00>"}},
    {{0x56, L"Help"}},
    {{0x5B, L"Left Windows"}},
    {{0x5C, L"Right Windows"}},
    {{0x5D, L"Application"}},
    {{0x00, NULL}}
}};

static DEADKEY_LPWSTR key_names_dead[] = {{
{dead_names}    NULL
}};

// Scan code -> virtual key (standard US layout)
static USHORT scancode_to_vk[] = {{
    /* 00 */ VK__none_,      /* 01 */ VK_ESCAPE,      /* 02 */ '1',
    /* 03 */ '2',            /* 04 */ '3',            /* 05 */ '4',
    /* 06 */ '5',            /* 07 */ '6',            /* 08 */ '7',
    /* 09 */ '8',            /* 0A */ '9',            /* 0B */ '0',
    /* 0C */ VK_OEM_MINUS,   /* 0D */ VK_OEM_PLUS,    /* 0E */ VK_BACK,
    /* 0F */ VK_TAB,         /* 10 */ 'Q',            /* 11 */ 'W',
    /* 12 */ 'E',            /* 13 */ 'R',            /* 14 */ 'T',
    /* 15 */ 'Y',            /* 16 */ 'U',            /* 17 */ 'I',
    /* 18 */ 'O',            /* 19 */ 'P',            /* 1A */ VK_OEM_4,
    /* 1B */ VK_OEM_6,       /* 1C */ VK_RETURN,      /* 1D */ VK_LCONTROL,
    /* 1E */ 'A',            /* 1F */ 'S',            /* 20 */ 'D',
    /* 21 */ 'F',            /* 22 */ 'G',            /* 23 */ 'H',
    /* 24 */ 'J',            /* 25 */ 'K',            /* 26 */ 'L',
    /* 27 */ VK_OEM_1,       /* 28 */ VK_OEM_7,       /* 29 */ VK_OEM_3,
    /* 2A */ VK_LSHIFT,      /* 2B */ VK_OEM_5,       /* 2C */ 'Z',
    /* 2D */ 'X',            /* 2E */ 'C',            /* 2F */ 'V',
    /* 30 */ 'B',            /* 31 */ 'N',            /* 32 */ 'M',
    /* 33 */ VK_OEM_COMMA,   /* 34 */ VK_OEM_PERIOD,  /* 35 */ VK_OEM_2,
    /* 36 */ VK_RSHIFT | KBDEXT,
    /* 37 */ VK_MULTIPLY | KBDMULTIVK,
    /* 38 */ VK_LMENU,       /* 39 */ VK_SPACE,       /* 3A */ VK_CAPITAL,
    /* 3B */ VK_F1,          /* 3C */ VK_F2,          /* 3D */ VK_F3,
    /* 3E */ VK_F4,          /* 3F */ VK_F5,          /* 40 */ VK_F6,
    /* 41 */ VK_F7,          /* 42 */ VK_F8,          /* 43 */ VK_F9,
    /* 44 */ VK_F10,
    /* 45 */ VK_NUMLOCK | KBDEXT | KBDMULTIVK,
    /* 46 */ VK_SCROLL | KBDMULTIVK,
    /* 47 */ VK_HOME | KBDSPECIAL | KBDNUMPAD,
    /* 48 */ VK_UP | KBDSPECIAL | KBDNUMPAD,
    /* 49 */ VK_PRIOR | KBDSPECIAL | KBDNUMPAD,
    /* 4A */ VK_SUBTRACT,
    /* 4B */ VK_LEFT | KBDSPECIAL | KBDNUMPAD,
    /* 4C */ VK_CLEAR | KBDSPECIAL | KBDNUMPAD,
    /* 4D */ VK_RIGHT | KBDSPECIAL | KBDNUMPAD,
    /* 4E */ VK_ADD,
    /* 4F */ VK_END | KBDSPECIAL | KBDNUMPAD,
    /* 50 */ VK_DOWN | KBDSPECIAL | KBDNUMPAD,
    /* 51 */ VK_NEXT | KBDSPECIAL | KBDNUMPAD,
    /* 52 */ VK_INSERT | KBDSPECIAL | KBDNUMPAD,
    /* 53 */ VK_DELETE | KBDSPECIAL | KBDNUMPAD,
    /* 54 */ VK_SNAPSHOT,    /* 55 */ VK__none_,      /* 56 */ VK_OEM_102,
    /* 57 */ VK_F11,         /* 58 */ VK_F12,         /* 59 */ VK_CLEAR,
    /* 5A */ VK_OEM_WSCTRL,  /* 5B */ VK_OEM_FINISH,  /* 5C */ VK_OEM_JUMP,
    /* 5D */ VK_EREOF,       /* 5E */ VK_OEM_BACKTAB, /* 5F */ VK_OEM_AUTO,
    /* 60 */ VK__none_,      /* 61 */ VK__none_,      /* 62 */ VK_ZOOM,
    /* 63 */ VK_HELP,        /* 64 */ VK_F13,         /* 65 */ VK_F14,
    /* 66 */ VK_F15,         /* 67 */ VK_F16,         /* 68 */ VK_F17,
    /* 69 */ VK_F18,         /* 6A */ VK_F19,         /* 6B */ VK_F20,
    /* 6C */ VK_F21,         /* 6D */ VK_F22,         /* 6E */ VK_F23,
    /* 6F */ VK_OEM_PA3,     /* 70 */ VK__none_,      /* 71 */ VK_OEM_RESET,
    /* 72 */ VK__none_,      /* 73 */ 0x00C1,         /* 74 */ VK__none_,
    /* 75 */ VK__none_,      /* 76 */ VK_F24,         /* 77 */ VK__none_,
    /* 78 */ VK__none_,      /* 79 */ VK__none_,      /* 7A */ VK__none_,
    /* 7B */ VK_OEM_PA1,     /* 7C */ VK_TAB,         /* 7D */ VK__none_,
    /* 7E */ 0x00C2,
}};

static VSC_VK scancode_to_vk_e0[] = {{
    {{0x10, VK_MEDIA_PREV_TRACK | KBDEXT}},
    {{0x19, VK_MEDIA_NEXT_TRACK | KBDEXT}},
    {{0x1D, VK_RCONTROL | KBDEXT}},
    {{0x20, VK_VOLUME_MUTE | KBDEXT}},
    {{0x21, VK_LAUNCH_APP2 | KBDEXT}},
    {{0x22, VK_MEDIA_PLAY_PAUSE | KBDEXT}},
    {{0x24, VK_MEDIA_STOP | KBDEXT}},
    {{0x2E, VK_VOLUME_DOWN | KBDEXT}},
    {{0x30, VK_VOLUME_UP | KBDEXT}},
    {{0x32, VK_BROWSER_HOME | KBDEXT}},
    {{0x35, VK_DIVIDE | KBDEXT}},
    {{0x37, VK_SNAPSHOT | KBDEXT}},
    {{0x38, VK_RMENU | KBDEXT}},
    {{0x47, VK_HOME | KBDEXT}},
    {{0x48, VK_UP | KBDEXT}},
    {{0x49, VK_PRIOR | KBDEXT}},
    {{0x4B, VK_LEFT | KBDEXT}},
    {{0x4D, VK_RIGHT | KBDEXT}},
    {{0x4F, VK_END | KBDEXT}},
    {{0x50, VK_DOWN | KBDEXT}},
    {{0x51, VK_NEXT | KBDEXT}},
    {{0x52, VK_INSERT | KBDEXT}},
    {{0x53, VK_DELETE | KBDEXT}},
    {{0x5B, VK_LWIN | KBDEXT}},
    {{0x5C, VK_RWIN | KBDEXT}},
    {{0x5D, VK_APPS | KBDEXT}},
    {{0x5F, VK_SLEEP | KBDEXT}},
    {{0x65, VK_BROWSER_SEARCH | KBDEXT}},
    {{0x66, VK_BROWSER_FAVORITES | KBDEXT}},
    {{0x67, VK_BROWSER_REFRESH | KBDEXT}},
    {{0x68, VK_BROWSER_STOP | KBDEXT}},
    {{0x69, VK_BROWSER_FORWARD | KBDEXT}},
    {{0x6A, VK_BROWSER_BACK | KBDEXT}},
    {{0x6B, VK_LAUNCH_APP1 | KBDEXT}},
    {{0x6C, VK_LAUNCH_MAIL | KBDEXT}},
    {{0x6D, VK_LAUNCH_MEDIA_SELECT | KBDEXT}},
    {{0x1C, VK_RETURN | KBDEXT}},
    {{0x46, VK_CANCEL | KBDEXT}},
    {{0x00, 0x0000}}
}};

static VSC_VK scancode_to_vk_e1[] = {{
    {{0x1D, VK_PAUSE}},
    {{0x00, 0x0000}}
}};

static VK_TO_BIT vk_to_bits[] = {{
    {{VK_SHIFT,   KBDSHIFT}},
    {{VK_CONTROL, KBDCTRL}},
    {{VK_MENU,    KBDALT}},
    {{0,          0}}
}};

static MODIFIERS char_modifiers = {{
    &vk_to_bits[0],
    7,
    {{
        0,            // 000 = <none>
        1,            // 001 = Shift
        2,            // 010 = Ctrl
        3,            // 011 = Shift Ctrl
        SHFT_INVALID, // 100 = Alt
        SHFT_INVALID, // 101 = Shift Alt
        4,            // 110 = Ctrl Alt (AltGr)
        5,            // 111 = Shift Ctrl Alt (Shift AltGr)
    }}
}};

// Character keys:      plain, Shift, Ctrl, Shift+Ctrl, AltGr, Shift+AltGr
static VK_TO_WCHARS6 vk_to_wchar6[] = {{
{wchar6}    {{0, 0, {{0, 0, 0, 0, 0, 0}}}}
}};

static VK_TO_WCHARS3 vk_to_wchar3[] = {{
    {{VK_BACK,   0, {{0x0008, 0x0008, 0x007F}}}},
    {{VK_ESCAPE, 0, {{0x001B, 0x001B, 0x001B}}}},
    {{VK_RETURN, 0, {{0x000D, 0x000D, 0x000A}}}},
    {{VK_CANCEL, 0, {{0x0003, 0x0003, 0x0003}}}},
    {{0, 0, {{0, 0, 0}}}}
}};

static VK_TO_WCHARS2 vk_to_wchar2[] = {{
    {{VK_TAB,      0, {{0x0009, 0x0009}}}},
    {{VK_ADD,      0, {{L'+', L'+'}}}},
    {{VK_DIVIDE,   0, {{L'/', L'/'}}}},
    {{VK_MULTIPLY, 0, {{L'*', L'*'}}}},
    {{VK_SUBTRACT, 0, {{L'-', L'-'}}}},
    {{0, 0, {{0, 0}}}}
}};

// The numeric keypad must come last, so that VkKeyScan finds digits on the
// main keyboard first.
static VK_TO_WCHARS1 vk_to_wchar1[] = {{
    {{VK_NUMPAD0, 0, {{L'0'}}}},
    {{VK_NUMPAD1, 0, {{L'1'}}}},
    {{VK_NUMPAD2, 0, {{L'2'}}}},
    {{VK_NUMPAD3, 0, {{L'3'}}}},
    {{VK_NUMPAD4, 0, {{L'4'}}}},
    {{VK_NUMPAD5, 0, {{L'5'}}}},
    {{VK_NUMPAD6, 0, {{L'6'}}}},
    {{VK_NUMPAD7, 0, {{L'7'}}}},
    {{VK_NUMPAD8, 0, {{L'8'}}}},
    {{VK_NUMPAD9, 0, {{L'9'}}}},
    {{0, 0, {{0}}}}
}};

static VK_TO_WCHAR_TABLE vk_to_wchar[] = {{
    {{(PVK_TO_WCHARS1)vk_to_wchar6, 6, sizeof(vk_to_wchar6[0])}},
    {{(PVK_TO_WCHARS1)vk_to_wchar3, 3, sizeof(vk_to_wchar3[0])}},
    {{(PVK_TO_WCHARS1)vk_to_wchar2, 2, sizeof(vk_to_wchar2[0])}},
    {{(PVK_TO_WCHARS1)vk_to_wchar1, 1, sizeof(vk_to_wchar1[0])}},
    {{NULL, 0, 0}}
}};

// DEADTRANS(next character, dead character, result, flags)
static DEADKEY dead_keys[] = {{
{deadtrans}    {{0, 0, 0}}
}};

// Keys that produce a surrogate pair (characters outside the BMP)
static LIGATURE2 ligatures[] = {{
{ligatures}    {{0, 0, {{0, 0}}}}
}};

static KBDTABLES kbd_tables = {{
    &char_modifiers,
    vk_to_wchar,
    dead_keys,
    key_names,
    key_names_ext,
    key_names_dead,
    scancode_to_vk,
    ARRAYSIZE(scancode_to_vk),
    scancode_to_vk_e0,
    scancode_to_vk_e1,
    MAKELONG(KLLF_ALTGR, KBD_VERSION),
    2,
    sizeof(ligatures[0]),
    (PLIGATURE1)ligatures,
    0,
    0,
}};

PKBDTABLES KbdLayerDescriptor(VOID)
{{
    return &kbd_tables;
}}
"""

RC_TEMPLATE = r"""#include <windows.h>

VS_VERSION_INFO VERSIONINFO
 FILEVERSION {vcomma}
 PRODUCTVERSION {vcomma}
 FILEFLAGSMASK 0x3fL
 FILEFLAGS 0x0L
 FILEOS VOS_NT_WINDOWS32
 FILETYPE VFT_DLL
 FILESUBTYPE VFT2_DRV_KEYBOARD
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "000004B0"
        BEGIN
            VALUE "CompanyName", "{author}"
            VALUE "FileDescription", "{name} Keyboard Layout"
            VALUE "FileVersion", "{version}"
            VALUE "InternalName", "{dll}"
            VALUE "LegalCopyright", "{copyright_ascii}. MIT License."
            VALUE "OriginalFilename", "{dll}.dll"
            VALUE "ProductName", "{name}"
            VALUE "ProductVersion", "{version}"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x0000, 0x04B0
    END
END

// Display name, referenced as "@%SystemRoot%\system32\{dll}.dll,-1000"
STRINGTABLE
BEGIN
    1000 "{name}"
END
"""

DEF_TEMPLATE = """LIBRARY {dll}

EXPORTS
    KbdLayerDescriptor @1
"""


def wch(c: str) -> str:
    return f"0x{ord(c):04X}"


def c_comment(text: str) -> str:
    shown = "".join(c if c.isprintable() and c not in "\\" else f"U+{ord(c):04X}" for c in text)
    return shown.replace("*/", "* /")


def utf16_units(text: str) -> list[int]:
    data = text.encode("utf-16-le")
    return [int.from_bytes(data[i:i + 2], "little") for i in range(0, len(data), 2)]


def is_bmp_char(text: str) -> bool:
    return len(text) == 1 and ord(text) <= 0xFFFF


def tables(layout: Layout):
    """(dead characters, dead-key translations, report) for the layout.

    dead characters: {dead id: dead character}, only for dead keys that keep
    any results; translations: {dead id: {typed char: result}}.
    """
    report, dead_char, trans = [], {}, {}
    for dead in layout.dead.values():
        table, dropped = {}, 0
        for typed, result in dead.map.items():
            if result == dead.symbol:
                result = dead.windows_symbol
            if not is_bmp_char(typed):
                continue  # can't be typed by a single key
            if is_bmp_char(result):
                table[typed] = result
            else:
                dropped += 1
        if dropped:
            report.append(f"{dead.id}: dropped {dropped} results outside the BMP")
        if not any(t != " " for t in table):
            report.append(f"{dead.id}: no results left, dead key removed")
            continue
        if not is_bmp_char(dead.windows_symbol) or dead.windows_symbol in dead_char.values():
            raise ValueError(f"[dead.{dead.id}] needs a unique BMP windows-symbol")
        dead_char[dead.id] = dead.windows_symbol
        trans[dead.id] = table
    return dead_char, trans, report


def c_source(layout: Layout) -> tuple[str, list]:
    """(C source, report of what native Windows can't do)."""
    dead_char, trans, report = tables(layout)
    rows, ligatures = [], []
    for key in layout.keys:
        vk = key.physical.vk
        cells, notes, dead_cells = [], [], {}
        for col in range(6):
            if col in (2, 3):
                value = CTRL_CHARS.get(vk, (None, None))[col - 2]
                cells.append("WCH_NONE" if value is None else f"0x{value:04X}")
                continue
            binding = layout.binding(key, COLUMN_LAYERS[col], "pc")
            if isinstance(binding, Dead) and binding.id in dead_char:
                cells.append("WCH_DEAD")
                dead_cells[col] = dead_char[binding.id]
                notes.append(f"<{binding.id}>")
            elif isinstance(binding, Char):
                units = utf16_units(binding.text)
                if len(units) == 1:
                    cells.append(f"0x{units[0]:04X}")
                elif len(units) == 2:
                    cells.append("WCH_LGTR")
                    ligatures.append(
                        f"    {{{vk}, {col}, {{{', '.join(f'0x{u:04X}' for u in units)}}}}}, "
                        f"// {c_comment(binding.text)}\n"
                    )
                    report.append(f"{binding.text} on {vk} column {col} is a ligature (surrogate pair)")
                else:
                    cells.append("WCH_NONE")
                    report.append(f"{binding.text!r} on {vk} column {col} is too long; dropped")
                notes.append(c_comment(binding.text))
            else:
                cells.append("WCH_NONE")
                notes.append("-")
        attrs = []
        b = lambda layer: layout.binding(key, layer, "pc")  # noqa: E731
        if b("caps") == b("shift") != b("base"):
            attrs.append("CAPLOK")
        if b("caps-option") == b("shift-option") != b("option"):
            attrs.append("CAPLOKALTGR")
        attr = " | ".join(attrs) or "0"
        rows.append(f"    {{{vk}, {attr}, {{{', '.join(cells)}}}}}, // {' '.join(notes)}\n")
        if dead_cells:
            dcells = [wch(dead_cells[c]) if c in dead_cells else "WCH_NONE" for c in range(6)]
            rows.append(f"    {{VK__none_, 0, {{{', '.join(dcells)}}}}},\n")

    deadtrans, dead_names = [], []
    for dead_id, dc in dead_char.items():
        dead_names.append(f'    L"\\x{ord(dc):04X}" L"{dead_id.upper()}",\n')
        deadtrans.append(f"    // {dead_id} (dead character {c_comment(dc)})\n")
        for typed, result in trans[dead_id].items():
            deadtrans.append(
                f"    DEADTRANS({wch(typed)}, {wch(dc)}, {wch(result)}, 0x0000), "
                f"// {c_comment(typed)} -> {c_comment(result)}\n"
            )
    source = C_TEMPLATE.format(
        name=layout.name,
        copyright=layout.copyright_notice,
        wchar6="".join(rows),
        deadtrans="".join(deadtrans),
        dead_names="".join(dead_names),
        ligatures="".join(ligatures),
    )
    return source, report


def write_source(layout: Layout, outdir: Path) -> list:
    """Write the C source, resource file, module definition, and the build and
    install scripts into `outdir`; return the report."""
    dll = layout.windows_dll
    source, report = c_source(layout)
    fmt = dict(
        name=layout.name,
        author=layout.author,
        version=layout.version,
        vcomma=",".join((layout.version.split(".") + ["0"] * 4)[:4]),
        dll=dll,
        copyright_ascii=f"(c) {layout.copyright} {layout.author}",
    )
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{dll}.c").write_text(source, encoding="utf-8")
    (outdir / f"{dll}.rc").write_text(RC_TEMPLATE.format(**fmt), encoding="ascii")
    (outdir / f"{dll}.def").write_text(DEF_TEMPLATE.format(**fmt), encoding="ascii")
    for script in files("layoutgen").joinpath("templates", "windows").iterdir():
        text = script.read_bytes().decode("utf-8")
        text = text.replace("@@DLL@@", dll).replace("@@NAME@@", layout.name)
        (outdir / script.name).write_bytes(text.encode("utf-8"))
    return report
