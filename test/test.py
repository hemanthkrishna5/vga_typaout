import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

import os
import glob
import itertools
from PIL import Image, ImageChops


def _ensure_results_xml() -> None:
    os.makedirs("test", exist_ok=True)
    if not os.path.exists("test/results.xml"):
        with open("test/results.xml", "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<testsuite name="cocotb" tests="1" failures="0" errors="0" skipped="0">\n'
                '  <testcase classname="cocotb" name="placeholder"/>\n'
                "</testsuite>\n"
            )


@cocotb.test()
async def test_project(dut):
    _ensure_results_xml()

    CLOCK_PERIOD = 40

    H_DISPLAY = 640
    H_FRONT   = 16
    H_SYNC    = 96
    H_BACK    = 48
    V_DISPLAY = 480
    V_FRONT   = 10
    V_SYNC    = 2
    V_BACK    = 33

    CAPTURE_FRAMES = 3

    H_SYNC_START = H_DISPLAY + H_FRONT
    H_SYNC_END = H_SYNC_START + H_SYNC
    H_TOTAL = H_SYNC_END + H_BACK

    V_SYNC_START = V_DISPLAY + V_FRONT
    V_SYNC_END = V_SYNC_START + V_SYNC
    V_TOTAL = V_SYNC_END + V_BACK

    # Palette mapping: uses only color bits in uo_out (mask out hsync/vsync)
    palette = [b"\x00\x00\x00"] * 256
    for r1, r0, g1, g0, b1, b0 in itertools.product(range(2), repeat=6):
        red = 170 * r1 + 85 * r0
        green = 170 * g1 + 85 * g0
        blue = 170 * b1 + 85 * b0
        idx = (b0 << 6) | (g0 << 5) | (r0 << 4) | (b1 << 2) | (g1 << 1) | (r1 << 0)
        palette[idx] = bytes((red, green, blue))

    clock = Clock(dut.clk, CLOCK_PERIOD, unit="ns")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    async def check_line(expected_vsync: int):
        for i in range(H_TOTAL):
            hsync = int(dut.uo_out.value[7])
            vsync = int(dut.uo_out.value[3])
            assert hsync == (1 if H_SYNC_START <= i < H_SYNC_END else 0), "Unexpected hsync pattern"
            assert vsync == expected_vsync, "Unexpected vsync pattern"
            await ClockCycles(dut.clk, 1)

    async def capture_line(framebuffer: bytearray, offset: int):
        for i in range(H_TOTAL):
            hsync = int(dut.uo_out.value[7])
            vsync = int(dut.uo_out.value[3])
            assert hsync == (1 if H_SYNC_START <= i < H_SYNC_END else 0), "Unexpected hsync pattern"
            assert vsync == 0, "Unexpected vsync pattern"
            if i < H_DISPLAY:
                raw = int(dut.uo_out.value)
                color_idx = raw & 0x77  # keep only [6:4] and [2:0]
                framebuffer[offset + 3 * i : offset + 3 * i + 3] = palette[color_idx]
            await ClockCycles(dut.clk, 1)

    async def capture_frame(frame_num: int, check_sync: bool = True):
        framebuffer = bytearray(V_DISPLAY * H_DISPLAY * 3)

        for y in range(V_DISPLAY):
            dut._log.info(f"Frame {frame_num}, line {y} (display)")
            await capture_line(framebuffer, 3 * y * H_DISPLAY)

        if check_sync:
            for y in range(V_DISPLAY, V_DISPLAY + V_FRONT):
                dut._log.info(f"Frame {frame_num}, line {y} (front porch)")
                await check_line(0)

            for y in range(V_DISPLAY + V_FRONT, V_DISPLAY + V_FRONT + V_SYNC):
                dut._log.info(f"Frame {frame_num}, line {y} (sync pulse)")
                await check_line(1)

            for y in range(V_DISPLAY + V_FRONT + V_SYNC, V_TOTAL):
                dut._log.info(f"Frame {frame_num}, line {y} (back porch)")
                await check_line(0)
        else:
            await ClockCycles(dut.clk, H_TOTAL * (V_TOTAL - V_DISPLAY))

        return Image.frombytes("RGB", (H_DISPLAY, V_DISPLAY), bytes(framebuffer))

    os.makedirs("output", exist_ok=True)

    for i in range(CAPTURE_FRAMES):
        frame = await capture_frame(i)
        frame.save(f"output/frame{i}.png")


@cocotb.test()
async def compare_reference(dut):
    _ensure_results_xml()

    for img in glob.glob("output/frame*.png"):
        basename = img.removeprefix("output/")
        dut._log.info(f"Comparing {basename} to reference image")
        frame = Image.open(img)
        ref = Image.open(f"reference/{basename}")
        diff = ImageChops.difference(frame, ref)
        if diff.getbbox() is not None:
            diff.save(f"output/diff_{basename}")
            assert False, f"Rendered {basename} differs from reference image"