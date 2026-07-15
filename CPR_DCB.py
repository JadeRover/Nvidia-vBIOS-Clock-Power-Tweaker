import struct

CONNECTOR_TYPES = {
    0x00: "unused/unknown",
    # Legacy/Fermi-Kepler-Maxwell connector IDs seen in mobile MXM ROMs.
    # These names are intentionally user-facing/simple; the exact DCB connector
    # subtype can still be checked from the raw bytes shown in the GUI.
    0x30: "DVI-I / analog-digital",
    0x31: "DVI-D / HDMI-style",
    0x38: "HDMI-style",
    0x3f: "HDMI/TMDS-style",
    0x40: "Internal LVDS / legacy panel",
    0x46: "External DisplayPort",
    0x47: "Internal DisplayPort/eDP",
    0x60: "DisplayPort/USB-C related",
    0x61: "DisplayPort/USB-C or special external path",
    0x73: "DisplayPort/USB-C or special external path",
    0xff: "disabled/end",
}

DCB_OUTPUT_TYPES = {
    0x0: "Analog/CRT",
    0x1: "DisplayPort",
    0x2: "TMDS/HDMI",
    0x3: "LVDS",
    0xe: "Skip/disabled",
    0xf: "EOL/disabled",
}


def _hex4(data):
    return " ".join(f"{b:02X}" for b in data)


def connector_pad_name(index):
    """Best-effort connector-index to DP pad name for Pascal-Ada/Blackwell tables.

    Ada 40-series mobile connector tables commonly use 0,1,2,3... for DP_A/B/C/D.
    Some newer tables use 0x20,0x21,... for the same pad sequence. Other values
    such as 0x10/0x14/0x21 on non-internal entries can be USB-C/special paths, so
    they are deliberately labelled as best-effort.
    """
    if 0 <= index <= 15:
        # 0..7 are true pad/link indexes on Pascal-Ada/Blackwell mobile DCBs.
        # Some older Fermi/Kepler/Maxwell connector tables use higher connector
        # numbers; show them instead of hiding useful legacy entries.
        suffix = "" if index <= 7 else " / legacy connector index"
        return f"DP_{chr(ord('A') + index)} / Pad {chr(ord('A') + index)}{suffix}"
    if 0x20 <= index <= 0x27:
        n = index - 0x20
        return f"DP_{chr(ord('A') + n)} / Pad {chr(ord('A') + n)} (0x20-style index)"
    if 0x10 <= index <= 0x17:
        n = index - 0x10
        return f"DP_{chr(ord('A') + n)}? / special 0x10-style index"
    return "special/unknown connector index"


def _connector_role(conn_type):
    return CONNECTOR_TYPES.get(conn_type, f"unknown connector type 0x{conn_type:02X}")



def _role_from_dcb_entry(raw):
    """Best-effort role from an 8-byte DCB output entry.

    For Pascal/Ada mobile VBIOSes we tested, low nibble 0x2 maps to
    TMDS/HDMI and low nibble 0x6 maps to DisplayPort. 0xE/0xF are skip/EOL.
    """
    if len(raw) < 4:
        return None
    t = raw[0] & 0x0F
    if t == 0x2:
        return "HDMI"
    if t == 0x6:
        return "DP"
    if t in (0xE, 0xF):
        return None
    return None


def _pad_from_index_short(index):
    if 0 <= index <= 15:
        return f"DP_{chr(ord('A') + index)}"
    if 0x20 <= index <= 0x27:
        return f"DP_{chr(ord('A') + index - 0x20)}"
    if 0x10 <= index <= 0x17:
        return f"DP_{chr(ord('A') + index - 0x10)}"
    return None


def _connector_role_short(conn_type):
    if conn_type == 0x47:
        return "eDP"
    if conn_type == 0x40:
        return "LVDS"
    if conn_type == 0x46:
        return "DP"
    if conn_type in (0x60, 0x61, 0x73):
        return "DP/USB-C"
    if conn_type in (0x30, 0x31):
        return "DVI/HDMI"
    if conn_type in (0x38, 0x3F):
        return "HDMI"
    if conn_type == 0xFF:
        return "Disabled"
    if conn_type == 0x00:
        return "Unused"
    return f"Type 0x{conn_type:02X}"


def _merge_role(roles, role):
    if not role or role in ("Disabled", "Unused"):
        return
    if role not in roles:
        roles.append(role)


class DCBParser:
    def __init__(self, data):
        self.data = data
        self.dcb_blocks = self.find_dcb_blocks()

    def find_dcb_blocks(self):
        data = self.data
        blocks = []
        seen = set()
        # DCB 4.x/5-ish headers seen on Pascal through current mobile vBIOS dumps:
        # version, header length, entry count, entry length, checksum/reserved.
        for off in range(0, max(0, len(data) - 16)):
            version = data[off]
            hdr_len = data[off + 1]
            entry_count = data[off + 2]
            entry_len = data[off + 3]
            if version not in (0x40, 0x41, 0x42, 0x50):
                continue
            if not (5 <= hdr_len <= 0x30):
                continue
            # Pascal-era secondary DCB/output tables may have fewer than 16 entries
            # (for example Quadro P5000 has 15), while Ada/mobile tables often
            # use 16 or 32.  Keep this wide but still bounded.
            if not (1 <= entry_count <= 0x40):
                continue
            if entry_len not in (4, 8):
                continue
            conn_off = off + hdr_len + entry_count * entry_len
            if conn_off + 5 >= len(data):
                continue
            cv, ch, cc, ce = data[conn_off:conn_off + 4]
            if cv not in (0x40, 0x41, 0x42, 0x50):
                continue
            if not (5 <= ch <= 0x30 and 1 <= cc <= 0x40 and ce in (4, 8)):
                continue
            # Connector entries should usually contain at least one known connector type.
            conn_blob = data[conn_off + 4: conn_off + 4 + min(cc, 16) * ce]
            # Require plausible real connector rows, not just random bytes that
            # happen to contain a connector-type value.  Some Pascal/Ada ROMs have
            # DCB-adjacent subtables that look header-like but are not the actual
            # display connector map.
            plausible_rows = 0
            has_internal = False
            for ri in range(0, max(0, len(conn_blob) - 3), ce):
                row = conn_blob[ri:ri + ce]
                if len(row) < 4:
                    continue
                ctype = row[1]
                cidx = row[2]
                idx_ok = (0 <= cidx <= 7) or (0x10 <= cidx <= 0x17) or (0x20 <= cidx <= 0x27)
                type_ok = ctype in (0x30, 0x31, 0x38, 0x3F, 0x40, 0x46, 0x47, 0x60, 0x61, 0x73)
                if type_ok and idx_ok:
                    plausible_rows += 1
                    if ctype in (0x40, 0x47):
                        has_internal = True
            if plausible_rows < 2 and not has_internal:
                continue
            if off in seen:
                continue
            seen.add(off)
            blocks.append(self.parse_block(off))
        # Prefer unique primary copies and skip obvious duplicate offset copies only if requested by caller.
        return blocks

    def parse_block(self, off):
        data = self.data
        version, hdr_len, entry_count, entry_len = data[off:off + 4]
        entries = []
        entry_start = off + hdr_len
        for i in range(entry_count):
            eoff = entry_start + i * entry_len
            raw = data[eoff:eoff + entry_len]
            if len(raw) < entry_len:
                break
            b0 = raw[0]
            otype = b0 & 0x0F
            entries.append({
                "index": i,
                "offset": eoff,
                "raw": raw,
                "type_code": otype,
                "type": DCB_OUTPUT_TYPES.get(otype, f"type 0x{otype:X}"),
                "is_active": otype not in (0xE, 0xF) and raw != b"\x00" * len(raw),
            })
        conn_off = off + hdr_len + entry_count * entry_len
        cv, ch, cc, ce = data[conn_off:conn_off + 4]
        conns = []
        cstart = conn_off + 4  # connector table entries start immediately after the 4-byte header in these mobile DCB 4.x tables
        for i in range(cc):
            coff = cstart + i * ce
            raw = data[coff:coff + ce]
            if len(raw) < ce:
                break
            flags, ctype, cindex, misc = raw[:4]
            conns.append({
                "index": i,
                "offset": coff,
                "raw": raw,
                "flags": flags,
                "type_code": ctype,
                "type": _connector_role(ctype),
                "connector_index": cindex,
                "pad": connector_pad_name(cindex),
                "misc": misc,
                "is_internal_edp": ctype == 0x47,
                "is_internal_panel": ctype in (0x40, 0x47),
                "is_disabled": ctype == 0xff,
            })
        return {
            "offset": off,
            "version": version,
            "header_length": hdr_len,
            "entry_count": entry_count,
            "entry_length": entry_len,
            "entries": entries,
            "connector_offset": conn_off,
            "connector_version": cv,
            "connector_header_length": ch,
            "connector_count": cc,
            "connector_entry_length": ce,
            "connectors": conns,
        }

    def primary_block(self):
        if not self.dcb_blocks:
            return None
        # Return the first block. For dual-copy ROMs this is the primary copy in the first image.
        return self.dcb_blocks[0]

    def _parse_output_entries_near_connector_table(self, block):
        """Heuristic 8-byte output-path table decode used only for friendly role labels.

        The power/clock tool did not originally parse DCB display output entries.
        For Pascal through Blackwell mobile dumps tested here, the useful output
        entries sit 0x147 bytes before the connector table. This helper decodes
        DP vs HDMI role and connector/pad index for the concise display summary.
        """
        data = self.data
        start = block["connector_offset"] - 0x147
        entries = []
        if start < 0 or start + 8 > len(data):
            return entries
        for i in range(0, 24):
            off = start + i * 8
            raw = data[off:off + 8]
            if len(raw) < 8:
                break
            low = raw[0] & 0x0F
            if low == 0x0F:
                # EOL; there may be padding after this.
                break
            if low == 0x0E:
                continue
            role = _role_from_dcb_entry(raw)
            if role:
                conn_num = raw[2] & 0x7F
                pad = _pad_from_index_short(conn_num)
                entries.append({
                    "index": i,
                    "offset": off,
                    "raw": raw,
                    "role": role,
                    "connector_number": conn_num,
                    "pad": pad,
                })
        return entries

    def build_display_map(self, block=None):
        """Return a friendly DP_A/DP_B/... map for the GUI."""
        if block is None:
            block = self.primary_block()
        display = {f"DP_{chr(ord('A') + i)}": {
            "pad": f"DP_{chr(ord('A') + i)}",
            "roles": [],
            "connector_rows": [],
            "output_rows": [],
            "is_internal_edp": False,
            "is_internal_panel": False,
        } for i in range(16)}

        # Connector table is the source of truth for internal eDP marker 0x47.
        for c in block["connectors"]:
            pad = _pad_from_index_short(c["connector_index"])
            if pad not in display:
                continue
            role = _connector_role_short(c["type_code"])
            if role in ("Disabled", "Unused"):
                continue
            if role == "eDP":
                display[pad]["roles"] = ["eDP"]
                display[pad]["is_internal_edp"] = True
                display[pad]["is_internal_panel"] = True
            elif role == "LVDS":
                # Fermi/Kepler/Maxwell mobile ROMs often expose the built-in panel
                # as legacy LVDS type 0x40 rather than eDP type 0x47.
                if not display[pad]["is_internal_edp"]:
                    display[pad]["roles"] = ["LVDS"]
                display[pad]["is_internal_panel"] = True
            else:
                _merge_role(display[pad]["roles"], role)
            display[pad]["connector_rows"].append(c)

        # Output entries add HDMI/TMDS alternate-path visibility.
        for e in self._parse_output_entries_near_connector_table(block):
            pad = e["pad"]
            if pad in display and not display[pad].get("is_internal_panel"):
                _merge_role(display[pad]["roles"], e["role"])
                display[pad]["output_rows"].append(e)

        return display

    def summarize_compact(self, include_details=False):
        if not self.dcb_blocks:
            return "No DCB display configuration block was found."
        block = self.primary_block()
        dmap = self.build_display_map(block)
        edp_internals = [pad for pad, info in dmap.items() if info["is_internal_edp"]]
        legacy_panels = [pad for pad, info in dmap.items() if info.get("is_internal_panel") and not info["is_internal_edp"]]
        parts = []
        if edp_internals:
            parts.append("eDP " + ", ".join(edp_internals))
        if legacy_panels:
            parts.append("LVDS/legacy " + ", ".join(legacy_panels))
        internal_text = "; ".join(parts) if parts else "not found"
        lines = []
        lines.append("Display Configuration")
        lines.append("=====================")
        lines.append(f"DCB offset: 0x{block['offset']:X}    Connector table: 0x{block['connector_offset']:X}")
        lines.append(f"Internal panel: {internal_text}")
        lines.append("")
        lines.append("Output map:")
        lines.append("Pad   Display type        Connector raw / notes")
        lines.append("----  ------------------  --------------------------------")
        for pad in [f"DP_{chr(ord('A') + i)}" for i in range(10)]:
            info = dmap[pad]
            if not info["roles"] and not info["connector_rows"] and not info["output_rows"]:
                continue
            roles = "+".join(info["roles"]) if info["roles"] else "Unknown"
            raws = []
            for c in info["connector_rows"]:
                if c["type_code"] == 0xFF:
                    continue
                raw_note = f"conn{c['index']} {_hex4(c['raw'])}"
                if c["is_internal_edp"]:
                    raw_note += " *internal eDP*"
                elif c.get("is_internal_panel"):
                    raw_note += " *internal LVDS/legacy*"
                raws.append(raw_note)
            # Mention output alternates only when they add HDMI/DP info not obvious from connector table.
            out_roles = []
            for e in info["output_rows"]:
                if e["role"] not in out_roles:
                    out_roles.append(e["role"])
            if out_roles:
                raws.append("DCB outputs: " + "/".join(out_roles))
            notes = "; ".join(raws) if raws else "—"
            lines.append(f"{pad:<4}  {roles:<18}  {notes}")
        if include_details:
            lines.append("")
            lines.append("Raw connector entries:")
            for c in block["connectors"]:
                if c["is_disabled"] and c["index"] > 7:
                    continue
                lines.append(f"  {c['index']:>2}  0x{c['offset']:06X}  {_hex4(c['raw'])}  {c['type']}")
        return "\n".join(lines)

    def summarize(self, include_duplicates=False):
        # v1.2.4: default GUI output is the concise user-facing map, with
        # Fermi/Kepler/Maxwell legacy connector table support through Blackwell.
        if include_duplicates:
            # Keep the old detailed duplicate scan available for CLI/debugging.
            blocks = self.dcb_blocks
            lines = []
            for bi, block in enumerate(blocks):
                lines.append(f"Copy #{bi}: DCB 0x{block['offset']:X}, connector table 0x{block['connector_offset']:X}")
                lines.append(self.summarize_compact(include_details=True))
                lines.append("")
            return "\n".join(lines)
        return self.summarize_compact(include_details=False)
