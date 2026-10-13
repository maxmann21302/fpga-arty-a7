----------------------------------------------------------------------------------
-- Company:
-- Engineer:
--
-- Create Date: 06.10.2026 17:50:59
-- Design Name:
-- Module Name: and_2 - Behavioral
-- Project Name:
-- Target Devices:
-- Tool Versions:
-- Description:
--
-- Dependencies:
--
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
--
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity and_2 is
    Port ( a1 : in STD_LOGIC;
           a2 : in STD_LOGIC;
           a3 : in STD_LOGIC;
           a4 : in STD_LOGIC;
           x1 : in STD_LOGIC;
           x2 : in STD_LOGIC;
           b1 : out STD_LOGIC;
           b2 : out std_logic;
           b3 : out STD_LOGIC;
           b4 : out STD_LOGIC);
end and_2;

architecture Behavioral of and_2 is

begin

b1<=a1 and a2;
b2<=a3 or a4;
b3<=x1;
b4<=x2;
end Behavioral;
