// A module to check if the condition is met for a jump instruction

`include "./Funct3Parameters.vh"

module JumpController(
  input [2:0] funct3,
  input Eq,
  input Gt,
  input GtU,
  output reg jump
);

reg [1:0] instType;

always @(*) begin

    case(funct3)
        `BEQFunct3 : jump = Eq;
        `BNEFunct3 : jump = ~Eq;
        `BLTFunct3 : jump = ~Eq & ~Gt;
        `BLTUFunct3 : jump = ~Eq & ~GtU;
        `BGEFunct3 : jump = Eq | Gt;
        `BGEUFunct3 : jump = Eq | GtU;
    endcase

    // zr = $signed(ALUOut) == 32'b0;
    // instType = opcode[1:0];

    // case(opcode)
    //     2'b10: begin // S-Type
    //         case(funct3)
    //             3'b000: jump = zr; // BEQ
    //             3'b111: jump = ~zr; // BNE
    //             default: jump = ALUOut[0]; // BLT, BLTU, BLE, BLEU, BGT, BGTU, BGE, BGEU
    //         endcase
    //     end
    //     2'b11: jump = 1'b1; // U-Type
    //     default: jump = 1'b0;
    // endcase 
end

endmodule