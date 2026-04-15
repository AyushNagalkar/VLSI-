`timescale 1ns/1ps

// ================= MACROS =================
`define DATA_WIDTH 32
`define NUM_CORES 4
`define REG_COUNT 8

// ================= ALU =================
module alu (
    input [`DATA_WIDTH-1:0] a,
    input [`DATA_WIDTH-1:0] b,
    input [2:0] op,
    output reg [`DATA_WIDTH-1:0] out
);
    always @(*) begin
        case(op)
            3'b000: out = a + b;  // ADD
            3'b001: out = a - b;  // SUB
            3'b010: out = a & b;  // AND
            3'b011: out = a | b;  // OR
            3'b100: out = a ^ b;  // XOR
            default: out = 0;
        endcase
    end
endmodule

// ================= REGISTER FILE =================
module register_file (
    input clk,
    input we,
    input [2:0] addr,
    input [`DATA_WIDTH-1:0] data_in,
    output [`DATA_WIDTH-1:0] data_out
);
    reg [`DATA_WIDTH-1:0] regs [`REG_COUNT-1:0];

    assign data_out = regs[addr];

    always @(posedge clk) begin
        if (we)
            regs[addr] <= data_in;
    end
endmodule

// ================= DECODER =================
module decoder (
    input [15:0] instruction,
    output reg [2:0] op,
    output reg [2:0] ra,
    output reg [2:0] rb,
    output reg [2:0] rd
);
    always @(*) begin
        op = instruction[15:13];
        ra = instruction[12:10];
        rb = instruction[9:7];
        rd = instruction[6:4];
    end
endmodule

// ================= COMPUTE CORE =================
module compute_core (
    input clk,
    input [15:0] instruction,
    input [`DATA_WIDTH-1:0] reg_data,
    output [`DATA_WIDTH-1:0] result
);
    wire [2:0] op, ra, rb, rd;
    wire [`DATA_WIDTH-1:0] a, b;

    decoder dec(instruction, op, ra, rb, rd);

    assign a = reg_data;
    assign b = reg_data; // simplified (same input)

    alu alu_unit(a, b, op, result);
endmodule

// ================= SCHEDULER =================
module scheduler (
    input clk,
    input [15:0] instruction,
    output reg [15:0] dispatched_instr [`NUM_CORES-1:0]
);
    integer i;
    always @(posedge clk) begin
        for (i = 0; i < `NUM_CORES; i = i + 1) begin
            dispatched_instr[i] <= instruction; // broadcast
        end
    end
endmodule

// ================= TOP MODULE =================
module mini_gpu (
    input clk,
    input [15:0] instruction,
    input [`DATA_WIDTH-1:0] data_in,
    output [`DATA_WIDTH-1:0] final_out
);

    wire [15:0] instr_bus [`NUM_CORES-1:0];
    wire [`DATA_WIDTH-1:0] core_out [`NUM_CORES-1:0];

    // Scheduler
    scheduler sched(
        .clk(clk),
        .instruction(instruction),
        .dispatched_instr(instr_bus)
    );

    // Register file (shared)
    wire [`DATA_WIDTH-1:0] reg_out;
    register_file rf(
        .clk(clk),
        .we(1'b1),
        .addr(3'b001),
        .data_in(data_in),
        .data_out(reg_out)
    );

    // Generate multiple cores
    genvar i;
    generate
        for(i = 0; i < `NUM_CORES; i = i + 1) begin : GPU_CORES
            compute_core core (
                .clk(clk),
                .instruction(instr_bus[i]),
                .reg_data(reg_out),
                .result(core_out[i])
            );
        end
    endgenerate

    // Simple reduction (like GPU warp result)
    assign final_out = core_out[0];

endmodule