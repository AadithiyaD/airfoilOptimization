import subprocess
import os
from pathlib import Path
import numpy as np
from dataclasses import dataclass
from typing import Optional

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
        self.name = name
        self.params = params
        self.pid = pid
        self.nacaCode = nacaCode if nacaCode is not None else []
        
        self.dat_file = Path(f"data/airfoils/{name}{pid}.dat")
        self.polar_file = Path(f"data/output/{name}{pid}Polar.txt")

        # If PARSEC params is used, gen x and y coords
        if params is not None:
            self.x, self.y = self._gen_coords()
            
        # If NACA used, x and y handled by XFOIL, so set here to None
        elif nacaCode is not None:
            self.x = None
            self.y = None
                
        # Set default efficiency to a penalty value
        self.peak_efficiency = 1e6
        
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
    
    def write_dat_file(self):
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
        # Write out points
        # First line is header; airfoil name and coeffs if specified
        # Pairs of x, y coords are written with 6 decimals
        
        if self.params is not None:
            header = self.params.to_str()
        elif self.nacaCode is not None and len(self.nacaCode) == 3:
            header = f"{self.nacaCode[0]}{self.nacaCode[1]}{self.nacaCode[2]}"
        else:
            header = ""
        
        with open(self.dat_file, 'w+') as f:
            f.write(f"{self.name} {header}\n")
            
            if self.x is not None and self.y is not None:
                for xi, yi in zip(self.x, self.y):
                    f.write(f"{xi:12.6f}  {yi:12.6f}\n")
                print(f"{self.name} written to {self.dat_file}")
                
            else:
                return
        
        
    def xfoil_analysis(self, mode: str, Re: int = 250000, alpha_sequence: list = [0, 15, 1]):
            """
        Runs xfoil with a txt file input. Programmaticaly generates the txt input
        
        Args:
            mode => NACA or PARSEC airfoil parametrization
            Re => Reynolds number, default = 250000
            alpha_sequence => [start, end, increment] AoA for analysis, default = [0, 15, 1]
            """
            # Initial inputs
            # Alpha sequence is [start, end, increment]
            if mode == "NACA":
                if len(self.nacaCode) == 3:
                    naca_code = f"{self.nacaCode[0]}{self.nacaCode[1]}{self.nacaCode[2]}"
                else:
                    print(f"Invalid NACA code == {self.nacaCode}")
                    self.peak_efficiency = 1e6
                    return
                                
                # Check if previous save file exists and delete it
                if Path(self.polar_file).exists():
                    os.remove(self.polar_file)
                    
                # Create commands
                with open(f"xfoilCommands{self.pid}.txt", "w") as commands:
                    commands.write("NACA\n")
                    commands.write(f"{naca_code}\n")
                    commands.write("OPER\n")
                    commands.write(f"VISC {Re}\n")
                    #commands.write("SEQP\n")
                    commands.write("PACC\n")
                    commands.write(f"{self.polar_file}\n")
                    commands.write("\n")
                    commands.write(f"ASEQ {alpha_sequence[0]} {alpha_sequence[1]} {alpha_sequence[2]}\n")
                    commands.write("PACC\n\n")
                    commands.write("QUIT\n")
        
    
            elif mode == "PARSEC":
                self.write_dat_file()
                
                if Path(self.polar_file).exists():
                    os.remove(self.polar_file)
                    
                # Create commands
                with open(f"xfoilCommands{self.pid}.txt", "w") as commands:
                    commands.write("LOAD\n")
                    commands.write(f"{self.dat_file}\n")
                    commands.write("OPER\n")
                    commands.write(f"VISC {Re}\n")
                    #commands.write("SEQP\n")
                    commands.write("PACC\n")
                    commands.write(f"{self.polar_file}\n")
                    commands.write("\n")
                    commands.write(f"ASEQ {alpha_sequence[0]} {alpha_sequence[1]} {alpha_sequence[2]}\n")
                    commands.write("PACC\n\n")
                    commands.write("QUIT\n")
        
            else:
                return "mode must be set to NACA or PARSEC for now"
            
            # Run xfoil and get result
            subprocess.call(f"xfoil < xfoilCommands{self.pid}.txt", shell=True)            
            self.peak_efficiency = self._process_results_eff()

    def _process_results_eff(self):
        """
            Process the xfoil results and return max L/D as -ve. Can this be combined with the
            get_aeroData() method? Probably, but I'd have to get around to that
        """
        if Path(self.polar_file).exists():
            data = np.genfromtxt(self.polar_file, skip_header=12)
            
            # If data is written but empty, return penalty
            if data.size == 0:
                return 1e6

            # If only one AoA converges, skip
            elif len(data.shape) == 1:
                print (f"{self.name}: Only one AoA converged, skipping")
                return 1e6
            
            cl_data = data[:, 1]
            cd_data = data[:, 2]
            
            efficiency_data = cl_data / cd_data
            peak_efficiency = np.max(efficiency_data)
            
            return -peak_efficiency

        else:
            return 1e6
    
    def get_aeroData(self):
        """
            Returns AoA, Cl, Cd, L/D data
        """
        if Path(self.polar_file).exists():
            data = np.genfromtxt(self.polar_file, skip_header=12)
            
            if data.size == 0 or len(data.shape) == 1:
                return None
            
            aoa_data = data[:, 0]
            cl_data  = data[:, 1]
            cd_data  = data[:, 2]
            efficiency_data = cl_data / cd_data
            
            return aoa_data, cl_data, cd_data, efficiency_data
        
        else:
            return None
        
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