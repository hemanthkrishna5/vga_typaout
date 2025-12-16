<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This design generates a standard 640×480 VGA signal using hvsync_generator and draws a simple animated character by checking the current pixel coordinates (pix_x, pix_y) against a set of shape equations (circles/rectangles for head, face, eyes, mouth, body, legs, arms).
A counter (blink_counter) is used to create animation: pupils blink periodically and the two hands alternate up/down to look like waving. Each pixel is assigned an RGB color only when video_on is active, then mapped onto the Tiny Tapeout VGA pinout via uo_out.

## How to test
	1.	Build/flash the project using the Tiny Tapeout FPGA flow as usual.
	2.	Connect a VGA monitor using the TinyVGA PMOD wiring for Tiny Tapeout (HSYNC/VSYNC + RGB).
	3.	Power the board and observe the VGA output: you should see the character on a black background, with blinking eyes and two waving hands.

## External hardware

List external hardware used in your project (e.g. PMOD, LED display, etc), if any
