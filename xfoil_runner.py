import subprocess
import os

def xFoil(params: list, mode: str="NACA"):
    """
        Runs xfoil with a txt file input. Programmaticaly generates the txt input
        
        Args:
            params == list containing parameters of airfoil. For NACA based gen,
                list must be formatted as = [first_digit, second_digit, third_and_fourth_digit]
            mode == 'NACA' or 'PARSEC'. Default NACA based gen
    """
    
    # Initial inputs
    # Alpha sequence is [start, end, increment]
    if mode == "NACA":
        
        # NACA naming format, take  NACA 2412 as example
        # 1st digit, 2 => max camber == 2% of chord
        # 2nd digit, 4 => max camber located at 40% (0.4) chord location from leading edge
        # 3rd and 4th digit, 12 => max thickness == 12% of chord
        
        naca_code = f"{params[0]}{params[1]}{params[2]}"
    
    else:
        return "mode must be set to NACA or PARSEC for now"
    
    
    Re = 250000
    alpha_sequence = [0, 15, 1]
    
    # Check if previous save file exists and delete it
    if os.path.exists(f"./data/output/{naca_code}Polar.txt"):
        os.remove(f"./data/output/{naca_code}Polar.txt")
        
    # Create commands
    with open("xfoilCommands.txt", "w") as commands:
        commands.write("NACA\n")
        commands.write(f"{naca_code}\n")
        commands.write("OPER\n")
        commands.write(f"VISC {Re}\n")
        #commands.write("SEQP\n")
        commands.write("PACC\n")
        commands.write(f"./data/output/NACA{naca_code}Polar.txt\n")
        commands.write("\n")
        commands.write(f"ASEQ {alpha_sequence[0]} {alpha_sequence[1]} {alpha_sequence[2]}\n")
        commands.write("PACC\n\n")
        commands.write("QUIT\n")
    
    # Run xfoil
    subprocess.call("xfoil < xfoilCommands.txt", shell=True)
    
if __name__ == "__main__":
    xFoil([0,6,12])