`default_nettype none

module tt_um_vga_example (
    input wire [7:0] ui_in,    // Dedicated inputs (unused)
    output wire [7:0] uo_out,  // VGA output
    input wire [7:0] uio_in,   // IOs: Unused input path
    output wire [7:0] uio_out, // IOs: Unused output path
    output wire [7:0] uio_oe,  // IOs: Unused enable path
    input wire ena,            // Enable (unused)
    input wire clk,            // System clock
    input wire rst_n           // Active-low reset
);

    // VGA signal wires
    wire hsync;
    wire vsync;
    wire video_on;
    wire [9:0] pix_x;
    wire [9:0] pix_y;

    // RGB signals
    wire [1:0] R;
    wire [1:0] G;
    wire [1:0] B;

    assign uo_out = {hsync, B[0], G[0], R[0], vsync, B[1], G[1], R[1]};

    // Set unused IO outputs to zero
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Instantiate the existing hvsync_generator module
    hvsync_generator hvsync_gen(
        .clk(clk),
        .reset(~rst_n),
        .hsync(hsync),
        .vsync(vsync),
        .display_on(video_on),
        .hpos(pix_x),
        .vpos(pix_y)
    );

    // Blink counter
    reg [24:0] blink_counter;
    wire blink_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            blink_counter <= 0;
        end else begin
            blink_counter <= blink_counter + 1;
        end
    end

    // Blink state toggled every second or so (adjust bit as needed)
    assign blink_state = blink_counter[24];

    // Wave animation (uses the same counter)
    wire wave_state = blink_counter[23];

    // Monkey feature definitions
    wire head  = ((pix_x - 320) * (pix_x - 320) + (pix_y - 340) * (pix_y - 240)) <= (100 * 100);
    wire face  = ((pix_x - 320) * (pix_x - 320) + (pix_y - 250) * (pix_y - 250)) <= (70 * 70);

    wire eye_left  = ((pix_x - 290) * (pix_x - 290) + (pix_y - 230) * (pix_y - 230)) <= (9 * 9);
    wire eye_right = ((pix_x - 350) * (pix_x - 350) + (pix_y - 230) * (pix_y - 230)) <= (9 * 9);

    wire pupil_left  = ~blink_state && (((pix_x - 290) * (pix_x - 290) + (pix_y - 230) * (pix_y - 230)) <= (3 * 3));
    wire pupil_right = ~blink_state && (((pix_x - 350) * (pix_x - 350) + (pix_y - 230) * (pix_y - 230)) <= (3 * 3));

    wire mouth = (((pix_x - 320) * (pix_x - 320) + (pix_y - 270) * (pix_y - 270)) <= (12 * 12)) &&
                 (((pix_x - 320) * (pix_x - 320) + (pix_y - 270) * (pix_y - 270)) >= (10 * 10));

    // Body feature definitions
    wire body  = ((pix_x - 320) * (pix_x - 320) + (pix_y - 370) * (pix_y - 370)) <= (85 * 85);
    wire belly = ((pix_x - 320) * (pix_x - 320) + (pix_y - 380) * (pix_y - 380)) <= (55 * 55);

    wire leg_left  = (pix_x > 285 && pix_x < 305 && pix_y > 420 && pix_y < 470);
    wire leg_right = (pix_x > 335 && pix_x < 355 && pix_y > 420 && pix_y < 470);

    // 2 waving hands (left up when right down)
    wire arm_left  = (pix_x > 245 && pix_x < 285) &&
                     (pix_y > (320 + (wave_state ? -30 : 0)) && pix_y < (360 + (wave_state ? -30 : 0)));

    wire arm_right = (pix_x > 355 && pix_x < 395) &&
                     (pix_y > (320 + (wave_state ? 0 : -30)) && pix_y < (360 + (wave_state ? 0 : -30)));

    // Color the monkey parts
    wire [8:0] monkey_color = {2'b01, 2'b10, 2'b00}; // Brown
    wire [8:0] face_color   = {2'b01, 2'b11, 2'b10}; // Lighter Brown
    wire [8:0] eye_color    = {2'b11, 2'b11, 2'b11}; // White
    wire [8:0] pupil_color  = {2'b00, 2'b00, 2'b00}; // Black
    wire [8:0] mouth_color  = {2'b11, 2'b11, 2'b00}; // Yellow-ish
    wire [8:0] body_color   = monkey_color;          // same brown
    wire [8:0] belly_color  = face_color;            // lighter

    reg [8:0] pixel_color;

    // Determine the color of each pixel
    always @* begin
        pixel_color = 9'b000000000; // Default to black
        if (video_on) begin
            if (head)  pixel_color = monkey_color;
            if (face)  pixel_color = face_color;

            if (arm_left || arm_right) pixel_color = monkey_color;

            if (body)  pixel_color = body_color;
            if (belly) pixel_color = belly_color;
            if (leg_left || leg_right) pixel_color = body_color;

            if (eye_left || eye_right)     pixel_color = eye_color;
            if (pupil_left || pupil_right) pixel_color = pupil_color;

            if (mouth) pixel_color = mouth_color; // keep last so it doesn't get overwritten
        end
    end

    assign R = pixel_color[8:7];
    assign G = pixel_color[6:5];
    assign B = pixel_color[4:3];

endmodule