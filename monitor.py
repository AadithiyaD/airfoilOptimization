import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from airfoilTools import *

"""
Plots the L/D calculated at each iteration of the optimization
"""
log_file_path = "data/optimization_datalog.csv"
fig, ax1 = plt.subplots(1, 1, figsize=(10, 10))

scatter_line, = ax1.plot([], [], 'b.', alpha=0.5, label="L/D")
best_line, = ax1.plot([], [], 'r--', linewidth=2, label="Cumulative best L/D")

ax1.set_ylabel('L/D')
ax1.set_xlabel('Iteration')
ax1_title = ax1.set_title(f"L/D Evolution with Iterations")
ax1.grid(True)
ax1.legend(loc="lower right")

def update(frame):
    try:
        df = pd.read_csv(log_file_path)
    except FileNotFoundError:
        return
    except PermissionError:
        return

    if df.empty:
        return

    # If L/D == 1e6, skip rows
    df = df[df['Score(-L/D)'] != 1e6]
    
    # Convert -ve L/D back to +ve for plots
    df['L/D'] = -df['Score(-L/D)']

    # Find best L/D so far
    df['Best_soFar'] = df['L/D'].cummax()

    # Update plots
    scatter_line.set_data(df['Iteration'], df['L/D'])
    best_line.set_data(df['Iteration'], df['Best_soFar'])
    
    # Dynamically update x y limits and Title
    max_iter = df['Iteration'].max()
    ax1.set_xlim(0, max_iter * 1.05)
    
    max_LD = df['L/D'].max()
    min_LD = df['L/D'].min()
    ax1.set_ylim(min_LD * 0.95, max_LD * 1.05)
    
    ax1_title.set_text(f"L/D Evolution with Iterations\nBest L/D So Far: {df['Best_soFar'].max():.2f}")
    
    return scatter_line, best_line, ax1_title
    
ani = FuncAnimation(fig, update, interval=1000, cache_frame_data=False, blit=True)

plt.tight_layout()
plt.show()