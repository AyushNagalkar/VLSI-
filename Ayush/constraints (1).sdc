# ----------------------------------------------------------------
# Basic SDC for UART IP
# ----------------------------------------------------------------
set sdc_version 2.0
set_units -time ns -resistance kOhm -capacitance pF -voltage V -current mA

# 1. Define the Clock (Replace 'clk' with your actual clock port name)
# Assuming a 100MHz clock (10ns period)
create_clock -name "sys_clk" -period 10.0 -waveform {0.0 5.0} [get_ports {clk}]

# 2. Input Delays (Assume data arrives 2ns after clock)
set_input_delay -max 2.0 -clock [get_clocks {sys_clk}] [all_inputs]
set_input_delay -min 0.5 -clock [get_clocks {sys_clk}] [all_inputs]

# 3. Output Delays (Assume 2ns setup time for the next block)
set_output_delay -max 2.0 -clock [get_clocks {sys_clk}] [all_outputs]

# 4. Environment (Optional but recommended)
set_load 0.1 [all_outputs]
