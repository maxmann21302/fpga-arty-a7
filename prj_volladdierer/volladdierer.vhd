library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity volladdierer is
    Port (
        x    : in  STD_LOGIC;
        y    : in  STD_LOGIC;
        cin  : in  STD_LOGIC;
        sum  : out STD_LOGIC;
        cout : out STD_LOGIC
    );
end volladdierer;

architecture Behavioral of volladdierer is
begin
    sum  <= x xor y xor cin;
    cout <= (x and y) or (x and cin) or (y and cin);
end Behavioral;