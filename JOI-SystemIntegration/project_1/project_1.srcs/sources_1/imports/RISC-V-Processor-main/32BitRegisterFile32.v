// 32-bit Register 
// 32 Registers each of 32 bits
// Two input read ports and one input write port and one input write enable port
// Two output ports

module RegisterFile32Bit(
  input [4:0] ReadPort1,
  input [4:0] ReadPort2,
  input [4:0] WritePort,
  input [31:0] WriteData,
  input WriteEnable,
  input clk,
  output reg [31:0] ReadData1,
  output reg [31:0] ReadData2
);

reg [31:0] Registers[0:31];
integer i=0;

initial begin
  for(i=0;i<32;i=i+1) Registers[i] = 32'd0;
end

always @(posedge clk) begin
  ReadData1 <= Registers[ReadPort1];
  ReadData2 <= Registers[ReadPort2];
  if(WritePort!=5'd0 & WriteEnable) begin
    Registers[WritePort] <= WriteData;
  end
end

endmodule