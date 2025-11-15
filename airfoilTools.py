import subprocess
import os
import numpy as np

#! Handle writing out the airfoil with its iter number in the objective function in arifoilOpt
def writeAirfoil(x: np.ndarray, y: np.ndarray, airfoil_header: str, coeffs: dict, out_path: str="data/airfoils/"):
    """
        Writes airfoil coordinates into .dat file for XFOIL use
        
        Args:
            x => x - coordinates
            y => y - coordinates
            airfoil_header => Name of airfoil in the header of the .dat file
            out_path => Path to save output
            coeffs => Add coefficients of airfoil parametrization to the header of the .dat file. If not specified,
                set to empty string
    """
    # If coeffs not specified, keep it empty for file saves
    coeff_str = f"{coeffs}" if any(coeffs) else ""
    
    # Ensure output path exisits and constsruct full filname with path
    os.makedirs(out_path, exist_ok=True)
    full_filepath = os.path.join(out_path, airfoil_header+".dat")
    
    # Write out points
    # First line is header; airfoil name and coeffs if specified
    # Pairs of x, y coords are written with 6 decimals
    with open(full_filepath, 'w+') as f:
        f.write(f"{airfoil_header} {coeff_str}\n")
           
        for xi, yi in zip(x, y):
            f.write(f"{xi:12.6f}  {yi:12.6f}\n")
    
    print(f"{airfoil_header} written to {full_filepath}")

def parsec(input_coeffs: list):
    """
        Uses the PARSEC method of airfoil parametrization to generate an airfoil.
        This is formula is shown in: Della Vecchia et al. (2013)
        
        Returns: x coordinates, y coordinates, input_coefficients

        Args:
            "r_le"          => leading edge radius
            "X_up"          => upper crest position in horizontal coordinates
            "Z_up"          => upper crest pos in vertical coord
            "Z_XXup"        => upper crest curvature
        
            "X_lo"          => lower crest position in horizontal coordinates
            "Z_lo"          => lower crest pos in vertical coord
            "Z_XXlo"        => lower crest curvature
        
            "Z_te"          => TE offset in vertical sense
            "delta_Z_te"    => TE thickness
            "alpha_te"      => TE direction
            "beta_te"       => TE wedge angle
    """
    # Initialize variables
    r_le = input_coeffs[0]
    X_up = input_coeffs[1]
    Z_up = input_coeffs[2]
    Z_XXup = input_coeffs[3]
    
    X_lo = input_coeffs[4]
    Z_lo = input_coeffs[5]
    Z_XXlo = input_coeffs[6]
    
    Z_te = input_coeffs[7]
    delta_Z_te = input_coeffs[8]
    alpha_te = input_coeffs[9]
    beta_te = input_coeffs[10]
    
    # Setup system of equations and solve them
    # We first need to solve a set of equations of the form
    # C_up * a_up = b_up ; similar for lower surface
    # So, lets assign C_up(lo) == A and b_up(lo) == B and solve for a_up(lo) == X
    # Therefore our new system is A * X = B    
    A_upper = np.array([
    [1,                       1,                      1,                      1,                      1,                      1                        ],
    [X_up**(1/2),             X_up**(3/2),            X_up**(5/2),            X_up**(7/2),            X_up**(9/2),            X_up**(11/2)             ],
    [1/2,                     3/2,                    5/2,                    7/2,                    9/2,                    11/2                     ],
    [(1/2) * X_up**(-1/2),    (3/2) * X_up**(1/2),    (5/2) * X_up**(3/2),    (7/2) * X_up**(5/2),    (9/2) * X_up**(7/2),    (11/2) * X_up**(9/2)     ],
    [(-1/4) * X_up**(-3/2),   (3/4) * X_up**(-1/2),   (15/4) * X_up**(1/2),   (35/4) * X_up**(3/2),   (63/4) * X_up**(5/2),   (99/4) * X_up**(7/2)     ],
    [1,                       0,                      0,                      0,                      0,                      0                        ]
    ])   

    B_upper = np.array([
    [Z_te + delta_Z_te/2                            ],
    [Z_up                                           ],
    [np.tan(np.radians(alpha_te - (beta_te/2)))     ], # np.tan expects angle in raidans
    [0                                              ],
    [Z_XXup                                         ],
    [np.sqrt(2 * r_le)                              ]
    ])

    A_lower = np.array([
    [1,                       1,                      1,                      1,                      1,                      1                        ],
    [X_lo**(1/2),             X_lo**(3/2),            X_lo**(5/2),            X_lo**(7/2),            X_lo**(9/2),            X_lo**(11/2)             ],
    [1/2,                     3/2,                    5/2,                    7/2,                    9/2,                    11/2                     ],
    [(1/2) * X_lo**(-1/2),    (3/2) * X_lo**(1/2),    (5/2) * X_lo**(3/2),    (7/2) * X_lo**(5/2),    (9/2) * X_lo**(7/2),    (11/2) * X_lo**(9/2)     ],
    [(-1/4) * X_lo**(-3/2),   (3/4) * X_lo**(-1/2),   (15/4) * X_lo**(1/2),   (35/4) * X_lo**(3/2),   (63/4) * X_lo**(5/2),   (99/4) * X_lo**(7/2)     ],
    [1,                       0,                      0,                      0,                      0,                      0                        ]
    ])   
    
    B_lower = np.array([
    [Z_te - delta_Z_te/2                            ],
    [Z_lo                                           ],
    [np.tan(np.radians(alpha_te + (beta_te/2)))     ], 
    [0                                              ],
    [Z_XXlo                                         ],
    [-np.sqrt(2 * r_le)                              ]
    ])
    
    X_upper = np.linalg.solve(A_upper, B_upper)
    X_lower = np.linalg.solve(A_lower, B_lower)

    # Calc upper and lower points, with normalized chord 0 to 1
    # X[0] to X[5] correspond to the coefficients in a_up(lo)
    # Uniform and cosing spacing available
    # x_upperPts = np.linspace(0, 1, 51) 
    x_upperPts = 0.5 * (1 - np.cos(np.linspace(0, np.pi, 51))) # Calc x points with cosine spacing
    y_upperPts = (X_upper[0]*x_upperPts**(1/2) + 
                    X_upper[1]*x_upperPts**(3/2) + 
                    X_upper[2]*x_upperPts**(5/2) + 
                    X_upper[3]*x_upperPts**(7/2) + 
                    X_upper[4]*x_upperPts**(9/2) + 
                    X_upper[5]*x_upperPts**(11/2)
                    ) 
    
    #x_lowerPts = np.linspace(0, 1, 51) 
    x_lowerPts = 0.5 * (1 - np.cos(np.linspace(0, np.pi, 51)))
    y_lowerPts = (X_lower[0]*x_lowerPts**(1/2) + 
                    X_lower[1]*x_lowerPts**(3/2) + 
                    X_lower[2]*x_lowerPts**(5/2) + 
                    X_lower[3]*x_lowerPts**(7/2) + 
                    X_lower[4]*x_lowerPts**(9/2) + 
                    X_lower[5]*x_lowerPts**(11/2)
                    ) 
    
    # Output airfoil coordinates and coeffs
    # Coord need to go from TE_up -> LE_up -> LE_lower -> TE_lower
    x_upper_TE_LE = x_upperPts[::-1]
    y_upper_TE_LE = y_upperPts[::-1]
    x_lower_LE_TE = x_lowerPts[1:]
    y_lower_LE_TE = y_lowerPts[1:]
    
    # Concatenate upper and lower points before outputting to dat file
    # For lower pts we go from [1:] to avoid a duplicate LE point
    x_conc_airfoil = np.concatenate([x_upper_TE_LE, x_lower_LE_TE])
    y_conc_airfoil = np.concatenate([y_upper_TE_LE, y_lower_LE_TE])

    return x_conc_airfoil, y_conc_airfoil, input_coeffs


def xFoil(params: list, airfoil_name:str ="", mode: str="NACA"):
    """
        Runs xfoil with a txt file input. Programmaticaly generates the txt input
        
        Args:
            params == list containing parameters of airfoil. For NACA based gen,
                list must be formatted as = [first_digit, second_digit, third_and_fourth_digit]
            mode == 'NACA' or 'PARSEC'. Default NACA based gen
    """
    # Global analysis params
    Re = 250000
    alpha_sequence = [0, 15, 1]
    
    # Initial inputs
    # Alpha sequence is [start, end, increment]
    if mode == "NACA":
        # NACA naming format, take  NACA 2412 as example
        # 1st digit, 2 => max camber == 2% of chord
        # 2nd digit, 4 => max camber located at 40% (0.4) chord location from leading edge
        # 3rd and 4th digit, 12 => max thickness == 12% of chord
        naca_code = f"{params[0]}{params[1]}{params[2]}"
        
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
            commands.write(f"./data/output/{naca_code}Polar.txt\n")
            commands.write("\n")
            commands.write(f"ASEQ {alpha_sequence[0]} {alpha_sequence[1]} {alpha_sequence[2]}\n")
            commands.write("PACC\n\n")
            commands.write("QUIT\n")
        
    
    elif mode == "PARSEC":
        # For info on PARSEC parametrization, visit parsec() fn
        airfoil_dir = "data/airfoils/"
        parsec_airfoil_path = os.path.join(airfoil_dir, airfoil_name + ".dat")
        
        # Similar sequence to NACA mode
        if os.path.exists(f"./data/output/{airfoil_name}Polar.txt"):
            os.remove(f"./data/output/{airfoil_name}Polar.txt")
            
        # Create commands
        with open("xfoilCommands.txt", "w") as commands:
            commands.write("LOAD\n")
            commands.write(f"{parsec_airfoil_path}\n")
            commands.write("OPER\n")
            commands.write(f"VISC {Re}\n")
            #commands.write("SEQP\n")
            commands.write("PACC\n")
            commands.write(f"./data/output/{airfoil_name}Polar.txt\n")
            commands.write("\n")
            commands.write(f"ASEQ {alpha_sequence[0]} {alpha_sequence[1]} {alpha_sequence[2]}\n")
            commands.write("PACC\n\n")
            commands.write("QUIT\n")
        
        pass
    else:
        return "mode must be set to NACA or PARSEC for now"
    
    # Run xfoil
    subprocess.call("xfoil < xfoilCommands.txt", shell=True)
    
if __name__ == "__main__":
    pass