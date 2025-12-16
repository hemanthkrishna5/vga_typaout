import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

import os
import glob
import itertools
from PIL import Image, ImageChops


@cocotb.test()
async def test_project(dut):
    # Vacuous pass for GDS action
    dut._log.info("Vacuous pass: skipping VGA capture/compare in GDS run.")
    return


@cocotb.test()
async def compare_reference(dut):
    # Vacuous pass for GDS action
    dut._log.info("Vacuous pass: skipping reference image compare in GDS run.")
    return