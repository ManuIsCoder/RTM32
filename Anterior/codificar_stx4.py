#!/usr/bin/env python3
"""Codifica assembly STX4 según rtm32.pdf (emulador RTM32-0.5)."""

from pathlib import Path
import re
import sys

REGS = {
    "zero": 0, "at": 1, "k0": 2, "k1": 3,
    "a0": 4, "a1": 5, "a2": 6, "a3": 7,
    "v0": 8, "v1": 9,
    "t0": 10, "t1": 11, "t2": 12, "t3": 13, "t4": 14,
    "t5": 15, "t6": 16, "t7": 17, "t8": 18, "t9": 19,
    "s0": 20, "s1": 21, "s2": 22, "s3": 23, "s4": 24,
    "s5": 25, "s6": 26, "s7": 27,
    "fp": 28, "gp": 29, "sp": 30, "ra": 31,
}

R_FUNCT = {
    "sll": 0x00, "srl": 0x01, "sra": 0x02, "and": 0x08, "or": 0x09,
    "xor": 0x0A, "nor": 0x0B, "slt": 0x0C, "jr": 0x0E, "jalr": 0x0F,
    "mul": 0x15, "add": 0x1C, "sub": 0x1D, "trap": 0x20,
}

I_OP = {
    "addi": 0x01, "lw": 0x08, "sw": 0x09, "sh": 0x0A, "sb": 0x0B,
    "lh": 0x0C, "lhu": 0x0D, "lb": 0x0E, "lbu": 0x0F,
    "beq": 0x10, "bne": 0x11, "blt": 0x12, "bgt": 0x13,
    "ble": 0x14, "bge": 0x15, "slti": 0x16,
}

L_OP = {"andi": 0x04, "ori": 0x05, "orh": 0x05, "xori": 0x06, "lui": 0x07}
J_OP = {"j": 0x02, "jal": 0x03}

CHAR_ESC = {"n": 10, "r": 13, "t": 9, "0": 0, "\\": 92, "'": 39, '"': 34}


def parse_reg(tok):
    tok = tok.lower().strip()
    if tok.startswith("$"):
        tok = tok[1:]
    if tok.isdigit():
        return int(tok)
    if tok in REGS:
        return REGS[tok]
    raise ValueError(f"registro desconocido: {tok}")


def parse_imm(tok, labels=None, bits=17):
    tok = tok.strip()
    if labels and tok in labels:
        return labels[tok]
    if tok.startswith(".hi16") or tok.startswith(".lo16"):
        name = tok.split()[-1]
        addr = labels[name]
        return (addr >> 16) & 0xFFFF if tok.startswith(".hi16") else addr & 0xFFFF
    if len(tok) >= 2 and tok.startswith("'") and tok.endswith("'"):
        inner = tok[1:-1]
        if inner.startswith("\\") and len(inner) >= 2:
            return CHAR_ESC[inner[1]]
        if len(inner) != 1:
            raise ValueError(f"carácter inválido: {tok}")
        return ord(inner)
    neg = tok.startswith("-")
    if neg:
        tok = tok[1:]
    if tok.startswith("0x"):
        val = int(tok, 16)
    else:
        val = int(tok, 10)
    if neg:
        val = -val
    return val


def sign_trunc(val, bits):
    mask = (1 << bits) - 1
    return val & mask


def enc_r(funct, rd=0, rs=0, rt=0, aux=0):
    return (rs << 22) | (rt << 17) | (rd << 12) | (aux << 7) | funct


def enc_i(op, rs, rt, imm):
    return (op << 27) | (rs << 22) | (rt << 17) | sign_trunc(imm, 17)


def enc_l(op, rs, rt, imm, h=0):
    return (op << 27) | (rs << 22) | (rt << 17) | (h << 16) | sign_trunc(imm, 16)


def enc_j(op, addr):
    return (op << 27) | ((addr >> 2) & 0x7FFFFFF)


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    lines = []
    for line in text.splitlines():
        if "//" in line:
            line = line[: line.index("//")]
        lines.append(line)
    return "\n".join(lines)


def tokenize_program(text):
    items = []
    section = ".text"
    for raw in strip_comments(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(".section"):
            section = line.split()[1].strip().strip('"')
            if not section.startswith("."):
                section = "." + section
            continue
        while True:
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_.']*):", line)
            if not m:
                break
            items.append(("label", section, m.group(1)))
            line = line[m.end() :].strip()
            if not line:
                break
        if not line:
            continue
        items.append(("stmt", section, line))
    return items


def parse_mem_op(arg):
    m = re.match(r"^(-?(?:0x[0-9A-Fa-f]+|\d+))\((\$[A-Za-z0-9]+)\)$", arg)
    if not m:
        raise ValueError(f"operando de memoria inválido: {arg}")
    return m.group(1), m.group(2)


def first_pass(items):
    pos = {".text": 0, ".data": 0}
    labels = {}
    sized = []
    for kind, section, payload in items:
        addr = pos[section]
        if kind == "label":
            labels[payload] = ("pending", section, addr)
            continue
        size = 4
        if payload.startswith(".asciiz"):
            s = payload.split(None, 1)[1].strip()
            s = bytes(s[1:-1], "utf-8").decode("unicode_escape")
            size = len(s.encode("latin1")) + 1
        elif payload.startswith(".word"):
            size = 4 * len(payload.split()) - 4
        elif payload.startswith(".byte"):
            size = len(payload.split()) - 1
        elif payload.startswith(".pad"):
            nums = [int(x, 0) for x in payload.split()[1:]]
            size = sum(nums)
        pos[section] += size
        sized.append((section, payload, addr, size))
    text_size = (pos[".text"] + 3) & ~3
    resolved = {}
    for name, (_, section, addr) in labels.items():
        resolved[name] = addr if section == ".text" else text_size + addr
    return sized, resolved, text_size


def encode_stmt(stmt, addr, labels):
    parts = [p.strip() for p in stmt.replace(",", " , ").split() if p.strip() != ","]
    op = parts[0].lower()
    args = [p.rstrip(",") for p in parts[1:]]
    if len(args) >= 2 and args[-2] in (".hi16", ".lo16"):
        args = args[:-2] + [args[-2] + " " + args[-1]]

    if op == ".asciiz":
        s = stmt.split(None, 1)[1].strip()
        s = bytes(s[1:-1], "utf-8").decode("unicode_escape")
        return s.encode("latin1") + b"\x00"

    if op in ("add", "sub", "and", "or", "xor", "nor", "slt", "mul"):
        rd, rs, rt = map(parse_reg, args)
        return enc_r(R_FUNCT[op], rd=rd, rs=rs, rt=rt).to_bytes(4, "little")

    if op == "jr":
        rs = parse_reg(args[0])
        return enc_r(R_FUNCT["jr"], rs=rs).to_bytes(4, "little")

    if op == "trap":
        aux = parse_imm(args[0], labels, 5)
        return enc_r(R_FUNCT["trap"], aux=aux).to_bytes(4, "little")

    if op in ("j", "jal"):
        target = parse_imm(args[0], labels)
        return enc_j(J_OP[op], target).to_bytes(4, "little")

    if op in ("beq", "bne", "blt", "bgt", "ble", "bge"):
        rs = parse_reg(args[0])
        rt = parse_reg(args[1])
        target = parse_imm(args[2], labels)
        imm = (target - (addr + 4)) // 4
        return enc_i(I_OP[op], rs, rt, imm).to_bytes(4, "little")

    if op in ("lw", "sw", "lh", "lhu", "lb", "lbu", "sb", "sh"):
        rt = parse_reg(args[0])
        off, rs = parse_mem_op(args[1])
        return enc_i(I_OP[op], parse_reg(rs), rt, parse_imm(off, labels)).to_bytes(4, "little")

    if op == "addi":
        rt, rs = parse_reg(args[0]), parse_reg(args[1])
        return enc_i(I_OP[op], rs, rt, parse_imm(args[2], labels)).to_bytes(4, "little")

    if op in ("ori", "andi", "xori"):
        rt, rs = parse_reg(args[0]), parse_reg(args[1])
        imm = parse_imm(args[2], labels, 16)
        return enc_l(L_OP[op], rs, rt, imm, h=0).to_bytes(4, "little")

    if op == "orh":
        rt, rs = parse_reg(args[0]), parse_reg(args[1])
        imm = parse_imm(args[2], labels, 16)
        return enc_l(L_OP["ori"], rs, rt, imm, h=1).to_bytes(4, "little")

    if op == "lui":
        rt = parse_reg(args[0])
        imm = parse_imm(args[1], labels, 16)
        return enc_l(L_OP["lui"], 0, rt, imm, h=0).to_bytes(4, "little")

    raise ValueError(f"instrucción no soportada: {stmt}")


def assemble(text):
    items = tokenize_program(text)
    sized, labels, text_size = first_pass(items)
    text_blob = bytearray()
    data_blob = bytearray()
    for section, stmt, addr, _size in sized:
        blob = encode_stmt(stmt, addr if section == ".text" else text_size + addr, labels)
        if section == ".text":
            text_blob += blob
        else:
            data_blob += blob
    while len(text_blob) % 4:
        text_blob += b"\x00"
    return bytes(text_blob + data_blob), labels


def write_mdbg(payload, path):
    header = bytearray()
    header += b"MDBG"
    header += (2).to_bytes(4, "little")
    header += (0).to_bytes(4, "little")
    header += len(payload).to_bytes(4, "little")
    header += (0).to_bytes(4, "little")
    header += len(payload).to_bytes(4, "little")
    header += (0).to_bytes(4, "little")
    header += b"RTM32".ljust(16, b"\x00")
    header += b"USER".ljust(16, b"\x00")
    Path(path).write_bytes(header + payload)


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "mover.rtm")
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else "mover.bin")
    payload, labels = assemble(src.read_text(encoding="utf-8"))
    write_mdbg(payload, dst)
    print(f"codificado {src.name} -> {dst} ({len(payload)} bytes)")
    for name, addr in labels.items():
        print(f"  {name}: 0x{addr:08x}")


if __name__ == "__main__":
    main()
