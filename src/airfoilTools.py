import os
import numpy as np
import subprocess
import warnings
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class parsecParams:
    r_le : float
    X_up : float
    Z_up : float
    Z_XXup : float
    
    X_lo : float
    Z_lo : float
    Z_XXlo : float
    
    Z_te : float
    delta_Z_te : float
    alpha_te : float
    beta_te : float
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)
    
    @classmethod
    def from_array(cls, arr):
        return cls(*arr)
    
    def to_array(self):
        return np.array([self.r_le, self.X_up, self.Z_up, self.Z_XXup, 
                         self.X_lo, self.Z_lo, self.Z_XXlo, 
                         self.Z_te, self.delta_Z_te, self.alpha_te, self.beta_te])
    
    def to_str(self):
        return (
            f"{self.r_le} {self.X_up} {self.Z_up} {self.Z_XXup} "
            f"{self.X_lo} {self.Z_lo} {self.Z_XXlo} "
            f"{self.Z_te} {self.delta_Z_te} {self.alpha_te} {self.beta_te}"
        )
        
    def to_str_labelled(self):
        return (
            f"r_le={self.r_le} X+up={self.X_up} Z_up={self.Z_up} Z_XXup={self.Z_XXup} "
            f"X_lo={self.X_lo} Z_lo={self.Z_lo} Z_XXlo={self.Z_XXlo} "
            f"Z_te={self.Z_te} delta_Z_te={self.delta_Z_te} alpha_te={self.alpha_te} beta_te={self.beta_te}"
        )

class Airfoil:
    def __init__(self, name: str, pid: int,
                 params: parsecParams | None = None, nacaCode: Optional[np.ndarray] = None):
        """
        Airfoil container.

        Args:
            name: descriptive name for the foil (used in temp filenames)
            pid: integer used to create unique temp filenames
            params: `parsecParams` instance for PARSEC parametrization
            nacaCode: numpy array or list for NACA digits (kept for backward compatibility)
        """
        self.name = name
        self.params = params
        self.pid = pid
        # keep backwards-compatible attribute name
        self.nacaCode = nacaCode if nacaCode is not None else []

        self.dat_file = Path(f"data/temp/{name}_pid{pid}.dat")
        self.polar_file = Path(f"data/temp/{name}_pid{pid}Polar.txt")

        # Validate input types
        if self.params is not None and isinstance(self.params, (list, tuple, np.ndarray)):
            raise TypeError(
                "'params' must be a parsecParams instance. "
            )

        # If PARSEC params is used, generate x and y coords
        if self.params is not None:
            self.x, self.y = self._gen_coords()

        # If NACA used, x and y handled by XFOIL, so set here to None
        elif self.nacaCode is not None and len(self.nacaCode) != 0:
            self.x = None
            self.y = None

        # Set default aero data to empty arrays
        self.cl = np.array([])
        self.cd = np.array([])
        self.aoa = np.array([])
        self.efficiency = np.array([])
        
    def _gen_coords(self):
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
            A_upper = np.array([
            [1,                       1,                      1,                      1,                      1,                      1                                                         ],
            [self.params.X_up**(1/2),             self.params.X_up**(3/2),            self.params.X_up**(5/2),            self.params.X_up**(7/2),            self.params.X_up**(9/2),            self.params.X_up**(11/2)             ],
            [1/2,                     3/2,                    5/2,                    7/2,                    9/2,                    11/2                                                                 ],
            [(1/2) * self.params.X_up**(-1/2),    (3/2) * self.params.X_up**(1/2),    (5/2) * self.params.X_up**(3/2),    (7/2) * self.params.X_up**(5/2),    (9/2) * self.params.X_up**(7/2),    (11/2) * self.params.X_up**(9/2)     ],
            [(-1/4) * self.params.X_up**(-3/2),   (3/4) * self.params.X_up**(-1/2),   (15/4) * self.params.X_up**(1/2),   (35/4) * self.params.X_up**(3/2),   (63/4) * self.params.X_up**(5/2),   (99/4) * self.params.X_up**(7/2)     ],
            [1,                       0,                      0,                      0,                      0,                      0                                                                    ]
            ])   

            B_upper = np.array([
            [self.params.Z_te + self.params.delta_Z_te/2                            ],
            [self.params.Z_up                                           ],
            [np.tan(np.radians(self.params.alpha_te - (self.params.beta_te/2)))     ], # np.tan expects angle in raidans
            [0                                              ],
            [self.params.Z_XXup                                         ],
            [np.sqrt(2 * self.params.r_le)                              ]
            ])

            A_lower = np.array([
            [1,                       1,                      1,                      1,                      1,                      1                        ],
            [self.params.X_lo**(1/2),             self.params.X_lo**(3/2),            self.params.X_lo**(5/2),            self.params.X_lo**(7/2),            self.params.X_lo**(9/2),            self.params.X_lo**(11/2)             ],
            [1/2,                     3/2,                    5/2,                    7/2,                    9/2,                    11/2                     ],
            [(1/2) * self.params.X_lo**(-1/2),    (3/2) * self.params.X_lo**(1/2),    (5/2) * self.params.X_lo**(3/2),    (7/2) * self.params.X_lo**(5/2),    (9/2) * self.params.X_lo**(7/2),    (11/2) * self.params.X_lo**(9/2)     ],
            [(-1/4) * self.params.X_lo**(-3/2),   (3/4) * self.params.X_lo**(-1/2),   (15/4) * self.params.X_lo**(1/2),   (35/4) * self.params.X_lo**(3/2),   (63/4) * self.params.X_lo**(5/2),   (99/4) * self.params.X_lo**(7/2)     ],
            [1,                       0,                      0,                      0,                      0,                      0                        ]
            ])   
            
            B_lower = np.array([
            [self.params.Z_te - self.params.delta_Z_te/2                            ],
            [self.params.Z_lo                                           ],
            [np.tan(np.radians(self.params.alpha_te + (self.params.beta_te/2)))     ], 
            [0                                              ],
            [self.params.Z_XXlo                                         ],
            [-np.sqrt(2 * self.params.r_le)                              ]
            ])
            
            X_upper = np.linalg.solve(A_upper, B_upper)
            X_lower = np.linalg.solve(A_lower, B_lower)

            # Calc upper and lower points, with normalized chord 0 to 1
            # X[0] to X[5] correspond to the coefficients in a_up(lo)
            #! Do NOT go beyond ~ 100 total x points, XFOIL will crash otherwise
            x_upperPts = 0.5 * (1 - np.cos(np.linspace(0, np.pi, 51))) # Calc x points with cosine spacing
            y_upperPts = (X_upper[0]*x_upperPts**(1/2) + 
                            X_upper[1]*x_upperPts**(3/2) + 
                            X_upper[2]*x_upperPts**(5/2) + 
                            X_upper[3]*x_upperPts**(7/2) + 
                            X_upper[4]*x_upperPts**(9/2) + 
                            X_upper[5]*x_upperPts**(11/2)
                            ) 

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

            return x_conc_airfoil, y_conc_airfoil
    
    def write_dat_file(self, out_path=None, *, nacaCode: Optional[np.ndarray] = None, 
                       naca_code: Optional[np.ndarray] = None):
        """
        Writes PARSEC airfoil coordinates into .dat file for XFOIL use
        For NACA airfoils, XFOIL handles .dat gen
        Args:
            out_path => Path to save output
        """
        # Write out points
        # First line is header; airfoil name and coeffs if specified
        # Pairs of x, y coords are written with 6 decimals
        
        if self.params is not None:
            header = self.params.to_str()
        else:
            header = ""
        
        output_path = out_path if out_path is not None else self.dat_file

        # Accept either naca Code from the method itself, or from the airfoil attribute
        naca_input = naca_code if naca_code is not None else nacaCode

        if naca_input is None:
            # Write PARSEC coords (if available)
            with open(output_path, 'w+') as f:
                f.write(f"{self.name} {header}\n")

                if self.x is not None and self.y is not None:
                    for xi, yi in zip(self.x, self.y):
                        f.write(f"{xi:12.6f}  {yi:12.6f}\n")
                else:
                    # Nothing to write
                    return
        else:
            # NACA: let XFOIL generate and save the .dat file
            naca_str = f"{naca_input[0]}{naca_input[1]}{naca_input[2]}"
            dat_name = f"NACA{naca_str}.dat"
            output_path = out_path if out_path is not None else Path("postProcess_data") / dat_name

            xfoil_commands = (
                "NACA\n"
                f"{naca_str}\n"
                f"SAVE {output_path}\n"
                "QUIT\n"
            )

            subprocess.run(
                ["xfoil"],
                input=xfoil_commands.encode('utf-8'),
                check=True
            )
        
    def xfoil_analysis(self, mode: str, Re: int = 250000, alpha_sequence: Optional[list] = None):
            """
        Runs xfoil with a txt file input. Programmaticaly generates the txt input
        
        Args:
            mode => NACA or PARSEC airfoil parametrization
            Re => Reynolds number, default = 250000
            alpha_sequence => [start, end, increment] AoA for analysis, default = [0, 15, 1]
            """
            # Path for the xfoil commands txt file
            individual_log_path = Path(f"xfoil_log_{self.pid}.txt")
            
            # Initialize alpha sequence if not provided
            if alpha_sequence is None:
                alpha_sequence = [0, 15, 1]
            
            if mode == "NACA":
                if len(self.nacaCode) == 3:
                    naca_code = f"{self.nacaCode[0]}{self.nacaCode[1]}{self.nacaCode[2]}"
                else:
                    print(f"Invalid NACA code == {self.nacaCode}")
                    return
                                
                # Check if previous save file exists and delete it
                if Path(self.polar_file).exists():
                    os.remove(self.polar_file)
                    
                # Create commands
                xfoil_commands = (
                    "NACA\n"
                    f"{naca_code}\n"
                    "OPER\n"
                    f"VISC {Re}\n"
                    "PACC\n"
                    f"{self.polar_file}\n"
                    "\n"
                    f"ASEQ {alpha_sequence[0]} {alpha_sequence[1]} {alpha_sequence[2]}\n"
                    "PACC\n\n"
                    "QUIT\n"
                    )
        
    
            elif mode == "PARSEC":
                self.write_dat_file()
                
                if Path(self.polar_file).exists():
                    os.remove(self.polar_file)
                    
                # Create commands
                xfoil_commands = (
                    "LOAD\n"
                    f"{self.dat_file}\n"
                    "OPER\n"
                    f"VISC {Re}\n"
                    "PACC\n"
                    f"{self.polar_file}\n"
                    "\n"
                    f"ASEQ {alpha_sequence[0]} {alpha_sequence[1]} {alpha_sequence[2]}\n"
                    "PACC\n\n"
                    "QUIT\n"
                )
        
            else:
                print("Mode must be set to NACA or PARSEC")
                return
            
        
            # Run xfoil and process results        
            try:
                with open(individual_log_path, "w") as log_file:
                    process = subprocess.Popen(
                        ["xfoil"],
                        stdin=subprocess.PIPE,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    # communicate will send input and wait; enforce timeout afterward
                    process.communicate(input=xfoil_commands)
                    process.wait(timeout=30)
            
            except subprocess.TimeoutExpired:
                print(f"XFOIL timed out for {self.name}")
                process.kill() # kill the runaway process
            
            except FileNotFoundError:
                 print(f"XFOIL executable not found. Make sure it's in system's PATH.")
            
            except Exception as e:
                # Catch other potential errors, like from check=True
                print(f"XFOIL failed for {self.name}: {e}")  
                
            self._process_results()

    def _process_results(self):
        """
            Sets AoA, Cl, Cd, L/D data. If polar data file does not exist, return empty list
        """
        if Path(self.polar_file).exists():
            # Ignore the empty file warning message
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                data = np.genfromtxt(self.polar_file, skip_header=12)
            
            if data.size == 0 or len(data.shape) == 1:
               return
            
            self.aoa = data[:, 0]
            self.cl  = data[:, 1]
            self.cd  = data[:, 2]
            self.efficiency = self.cl / self.cd
            
        else:
            return
            

    def cleanup(self):
        """
            Deletes dat file and xfoil commands file
        """
        try:
            self.dat_file.unlink(missing_ok=True)
            self.polar_file.unlink(missing_ok=True)
            
            commands_file = Path(f"xfoilCommands{self.pid}.txt")
            commands_file.unlink(missing_ok=True)
        
        except OSError as error:
            print(f"Encountered error when cleaning up {self.name}: {error}")

if __name__ == "__main__":
    pass