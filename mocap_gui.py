#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
from scipy.signal import medfilt
import threading
import time
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class MocapAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Motion Capture Analysis")
        self.root.geometry("1200x800")
        
        # Set default BVH file to bundled resource
        default_bvh = resource_path("take003_chr01.bvh")
        
        # Configuration variables
        self.udp_ip = tk.StringVar(value="127.0.0.1")
        self.udp_port = tk.IntVar(value=7005)
        self.bvh_file = tk.StringVar(value=default_bvh)
        self.selected_joint = tk.StringVar()
        self.window_size = tk.IntVar(value=300)
        self.update_every = tk.IntVar(value=5)
        self.recv_timeout = tk.DoubleVar(value=0.5)
        
        # Data variables
        self.channels = []
        self.frame_time = 0.0
        self.is_running = False
        self.sock = None
        self.thread = None
        
        # Graph data
        self.buffer_x = deque(maxlen=300)
        self.buffers_y = []
        self.lines = []
        self.frame_idx = 0
        self.prev_angles = None
        
        self.setup_ui()
        
        # Auto-parse the default BVH file if it exists
        if os.path.exists(default_bvh):
            self.parse_bvh()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # UDP Configuration
        ttk.Label(config_frame, text="UDP IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(config_frame, textvariable=self.udp_ip, width=15).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(config_frame, text="UDP Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(config_frame, textvariable=self.udp_port, width=10).grid(row=0, column=3, padx=(0, 20))
        
        # BVH File
        ttk.Label(config_frame, text="BVH File:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.bvh_file, width=40).grid(row=1, column=1, columnspan=2, pady=(10, 0))
        ttk.Button(config_frame, text="Browse", command=self.browse_bvh).grid(row=1, column=3, pady=(10, 0))
        
        # Parse BVH button
        ttk.Button(config_frame, text="Parse BVH", command=self.parse_bvh).grid(row=1, column=4, pady=(10, 0), padx=(10, 0))
        
        # Joint Selection
        ttk.Label(config_frame, text="Joint:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.joint_combo = ttk.Combobox(config_frame, textvariable=self.selected_joint, width=30)
        self.joint_combo.grid(row=2, column=1, columnspan=2, pady=(10, 0))
        
        # Advanced settings
        ttk.Label(config_frame, text="Window Size:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.window_size, width=10).grid(row=3, column=1, pady=(10, 0))
        
        ttk.Label(config_frame, text="Update Every:").grid(row=3, column=2, sticky=tk.W, padx=(20, 5), pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.update_every, width=10).grid(row=3, column=3, pady=(10, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Analysis", command=self.start_analysis)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Analysis", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready - Joints loaded from default BVH")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Graph frame
        graph_frame = ttk.LabelFrame(main_frame, text="Real-time Analysis", padding="10")
        graph_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.ax.set_xlabel("Frame")
        self.ax.set_ylabel("Angular Speed (deg/s)")
        self.ax.grid(True)
        
        # Embed matplotlib in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
    def browse_bvh(self):
        filename = filedialog.askopenfilename(
            title="Select BVH file",
            filetypes=[("BVH files", "*.bvh"), ("All files", "*.*")]
        )
        if filename:
            self.bvh_file.set(filename)
            
    def parse_bvh_header(self, file_path):
        """Parse BVH header to extract joint channels"""
        channels = []
        joint_stack = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(('ROOT', 'JOINT')):
                        joint_stack.append(line.split()[1])
                    elif line.startswith('End Site'):
                        joint_stack.append('End Site')
                    elif line.startswith('CHANNELS'):
                        parts = line.split()
                        n = int(parts[1])
                        for ch in parts[2:2 + n]:
                            channels.append((joint_stack[-1], ch))
                    elif line == '}':
                        if joint_stack:
                            joint_stack.pop()
                    elif line == 'MOTION':
                        break
                next(f)  # skip "Frames:"
                ft_line = next(f).strip()
                frame_time = float(ft_line.split()[2])
            return channels, frame_time
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse BVH file: {str(e)}")
            return [], 0.0
            
    def parse_bvh(self):
        """Parse BVH file and populate joint selection"""
        if not self.bvh_file.get():
            messagebox.showwarning("Warning", "Please select a BVH file first")
            return
            
        self.channels, self.frame_time = self.parse_bvh_header(self.bvh_file.get())
        
        if not self.channels:
            return
            
        # Use predefined joint list
        joint_names = [
            'Hips',
            'Spine',
            'Spine1',
            'Spine2',
            'Neck',
            'Head',
            'LeftShoulder',
            'LeftArm',
            'LeftForeArm',
            'LeftHand',
            'RightShoulder',
            'RightArm',
            'RightForeArm',
            'RightHand',
            'LeftUpLeg',
            'LeftLeg',
            'LeftFoot',
            'LeftToeBase',
            'RightUpLeg',
            'RightLeg',
            'RightFoot',
            'RightToeBase'
        ]
        
        # Update combo box
        self.joint_combo['values'] = joint_names
        if joint_names:
            self.selected_joint.set(joint_names[0])
            
        self.status_label.config(text=f"Parsed {len(self.channels)} channels from {len(joint_names)} joints")
        
    def start_analysis(self):
        """Start the analysis thread"""
        if not self.channels:
            messagebox.showwarning("Warning", "Please parse BVH file first")
            return
            
        if not self.selected_joint.get():
            messagebox.showwarning("Warning", "Please select a joint to analyze")
            return
            
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Start analysis thread
        self.thread = threading.Thread(target=self.analysis_loop, daemon=True)
        self.thread.start()
        
        self.status_label.config(text=f"Analyzing {self.selected_joint.get()} on {self.udp_ip.get()}:{self.udp_port.get()}")
        
    def stop_analysis(self):
        """Stop the analysis"""
        self.is_running = False
        if self.sock:
            self.sock.close()
            self.sock = None
            
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Analysis stopped")
        
    def analysis_loop(self):
        """Main analysis loop running in separate thread"""
        joint = self.selected_joint.get()
        axes = ['Xrotation', 'Yrotation', 'Zrotation']
        
        # Find column indices in the stream
        angle_indices = []
        angle_names = []
        for idx, (joint_name, ch) in enumerate(self.channels):
            if joint_name == joint and ch in axes:
                angle_indices.append(idx)
                angle_names.append(f"{joint}_{ch}")
                
        if not angle_indices:
            self.root.after(0, lambda: messagebox.showwarning("Warning", f"No rotation channels found for joint {joint}"))
            self.root.after(0, self.stop_analysis)
            return
            
        expected_floats = len(self.channels)
        fps = 60.0
        dt = 1.0 / fps
        
        # Initialize graph
        self.root.after(0, self.setup_graph, angle_names)
        
        # Initialize buffers
        self.buffer_x = deque(maxlen=self.window_size.get())
        self.buffers_y = [deque(maxlen=self.window_size.get()) for _ in angle_indices]
        
        # Setup UDP socket
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.udp_ip.get(), self.udp_port.get()))
            self.sock.settimeout(self.recv_timeout.get())
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to setup UDP socket: {str(e)}"))
            self.root.after(0, self.stop_analysis)
            return
            
        self.frame_idx = 0
        self.prev_angles = None
        
        while self.is_running:
            try:
                # Receive UDP data
                try:
                    data, addr = self.sock.recvfrom(65536)
                    text = data.decode('utf-8', errors='ignore').strip()
                    tokens = text.split()
                    
                    if len(tokens) < 3:
                        angles_now = [0.0] * len(angle_indices)
                    else:
                        tokens_data = tokens[2:]
                        floats = []
                        for t in tokens_data:
                            t_clean = t.strip().replace("'", "")
                            if t_clean == '':
                                continue
                            try:
                                val = float(t_clean)
                                floats.append(val)
                            except ValueError:
                                continue
                                
                        if len(floats) < expected_floats:
                            angles_now = [0.0] * len(angle_indices)
                        else:
                            angles_now = [floats[i] for i in angle_indices]
                            
                except socket.timeout:
                    angles_now = [0.0] * len(angle_indices)
                
                # Calculate angular speed
                if self.prev_angles is None:
                    angular_speeds = [0.0] * len(angles_now)
                else:
                    angular_speeds = [
                        (angles_now[i] - self.prev_angles[i]) / dt
                        for i in range(len(angles_now))
                    ]
                    
                self.prev_angles = angles_now
                
                # Update buffers
                self.buffer_x.append(self.frame_idx)
                for i, speed in enumerate(angular_speeds):
                    self.buffers_y[i].append(speed)
                    
                # Update graph
                if self.frame_idx % self.update_every.get() == 0:
                    self.root.after(0, self.update_graph)
                    
                self.frame_idx += 1
                
            except Exception as e:
                if self.is_running:  # Only show error if we're still supposed to be running
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis error: {str(e)}"))
                    self.root.after(0, self.stop_analysis)
                break
                
    def setup_graph(self, angle_names):
        """Setup the graph with the appropriate lines"""
        self.ax.clear()
        self.ax.set_xlabel("Frame")
        self.ax.set_ylabel("Angular Speed (deg/s)")
        self.ax.grid(True)
        
        self.lines = []
        for name in angle_names:
            line, = self.ax.plot([], [], label=f"{name} speed [deg/s]")
            self.lines.append(line)
            
        self.ax.legend()
        self.canvas.draw()
        
    def update_graph(self):
        """Update the graph with current data"""
        if not self.lines:
            return
            
        for i, line in enumerate(self.lines):
            if i < len(self.buffers_y):
                arr = np.array(self.buffers_y[i])
                if len(arr) >= 5:
                    arr_filtered = medfilt(arr, kernel_size=5)
                    line.set_xdata(self.buffer_x)
                    line.set_ydata(arr_filtered)
                else:
                    line.set_xdata(self.buffer_x)
                    line.set_ydata(arr)
                    
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = MocapAnalysisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

