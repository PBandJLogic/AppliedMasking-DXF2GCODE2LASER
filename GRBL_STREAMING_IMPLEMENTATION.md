# GRBL Streaming Implementation Guide

## Problem
The current implementation sends G-code line-by-line and waits for each response, causing halting/jerky motion. This is because GRBL's buffer empties between commands.

## Solution
Implement proper GRBL streaming protocol with:
1. Keep GRBL's buffer full (but not overflowing)
2. Separate status updates every 250ms
3. Update display (WPos/MPos and plot) from status, not from G-code parsing

## Implementation

### 1. Add Variables to `__init__` ✅ (Already done)

```python
# GRBL streaming
self.gcode_buffer = []  # Queue of G-code lines to send
self.buffer_size = 0  # Current size of GRBL's internal buffer (bytes)
self.max_buffer_size = 127  # GRBL's RX buffer size
self.streaming = False
self.status_update_id = None  # Timer ID for status updates
self.command_queue = []  # Track sent commands with their sizes
```

### 2. Add Streaming Functions

Add these methods BEFORE `run_adjusted_gcode`:

```python
def start_status_updates(self):
    """Start periodic status updates (every 250ms)"""
    if not self.is_connected or self.status_update_id is not None:
        return
    
    def update_status():
        if self.is_connected and self.serial_connection:
            try:
                # Send status query
                self.serial_connection.write(b'?')
                # Response will be handled by existing parse_status_response
            except:
                pass
        
        # Schedule next update
        if self.is_connected:
            self.status_update_id = self.root.after(250, update_status)
    
    # Start the updates
    self.status_update_id = self.root.after(250, update_status)

def stop_status_updates(self):
    """Stop periodic status updates"""
    if self.status_update_id is not None:
        self.root.after_cancel(self.status_update_id)
        self.status_update_id = None

def stream_gcode_line(self):
    """Stream next G-code line if buffer has space"""
    if not self.streaming or not self.gcode_buffer:
        return
    
    # Check if we have space in GRBL's buffer
    # Keep some headroom (use 80% of buffer)
    if self.buffer_size >= (self.max_buffer_size * 0.8):
        # Wait for buffer to clear, check again in 10ms
        self.root.after(10, self.stream_gcode_line)
        return
    
    # Get next line
    line_data = self.gcode_buffer.pop(0)
    line = line_data['line']
    line_num = line_data['num']
    
    # Send the line
    try:
        command = line + '\n'
        self.serial_connection.write(command.encode())
        
        # Track command size
        cmd_size = len(command)
        self.buffer_size += cmd_size
        self.command_queue.append({'size': cmd_size, 'line': line})
        
        # Update progress
        if hasattr(self, 'progress_bar'):
            self.sent_lines += 1
            self.progress_bar["value"] = self.sent_lines
            self.status_label.config(text=f"Line {self.sent_lines} / {self.total_lines}")
    
    except Exception as e:
        print(f"Error streaming line: {e}")
        self.stop_streaming()
        return
    
    # Continue streaming if there are more lines
    if self.gcode_buffer:
        self.root.after(1, self.stream_gcode_line)
    else:
        # All lines sent, wait for completion
        self.check_streaming_complete()

def check_streaming_complete(self):
    """Check if streaming is complete (buffer empty)"""
    if not self.streaming:
        return
    
    # If buffer is empty and command queue is empty, we're done
    if self.buffer_size <= 0 and len(self.command_queue) == 0:
        self.stop_streaming()
        if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
            self.progress_window.destroy()
        messagebox.showinfo(
            "Complete",
            f"G-code execution complete!\n\nSent {self.sent_lines} lines.",
        )
    else:
        # Check again in 100ms
        self.root.after(100, self.check_streaming_complete)

def stop_streaming(self):
    """Stop streaming G-code"""
    self.streaming = False
    self.gcode_buffer = []
    self.buffer_size = 0
    self.command_queue = []
    self.is_executing = False

def handle_grbl_ok(self):
    """Handle GRBL 'ok' response - command completed"""
    if self.command_queue:
        # Remove oldest command and reduce buffer
        cmd = self.command_queue.pop(0)
        self.buffer_size = max(0, self.buffer_size - cmd['size'])
```

### 3. Modify send_gcode to handle 'ok' responses

In the `send_gcode` method, after receiving a response:

```python
def send_gcode(self, command):
    """Send a G-code command to GRBL and wait for response"""
    if not self.is_connected or not self.serial_connection:
        return None
    
    try:
        # Send command
        self.serial_connection.write((command + '\n').encode())
        
        # Wait for response
        response = ""
        start_time = time.time()
        while time.time() - start_time < 5.0:  # 5 second timeout
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.readline().decode().strip()
                
                # Handle 'ok' for streaming
                if response.lower() == 'ok' and self.streaming:
                    self.handle_grbl_ok()
                
                break
            time.sleep(0.01)
        
        return response
    except Exception as e:
        print(f"Error sending G-code: {e}")
        return f"error: {str(e)}"
```

### 4. Replace run_adjusted_gcode

```python
def run_adjusted_gcode(self):
    """Send the adjusted G-code to GRBL using streaming protocol"""
    if not self.adjusted_gcode:
        messagebox.showwarning("Warning", "Please adjust the G-code first!")
        return

    if not self.is_connected:
        messagebox.showwarning("Warning", "Please connect to GRBL first!")
        return

    # Confirm with user
    response = messagebox.askyesno(
        "Run Adjusted G-code",
        "This will stream the adjusted G-code to GRBL.\n\n"
        "Make sure:\n"
        "- The machine is properly set up\n"
        "- The work origin is correct\n"
        "- The work area is clear\n\n"
        "Continue?",
    )

    if not response:
        return

    try:
        # Prepare G-code lines
        lines = self.adjusted_gcode.split("\n")
        
        # Filter out empty lines and comments
        filtered_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith(";") and not line.startswith("("):
                filtered_lines.append({'line': line, 'num': i+1})
        
        self.total_lines = len(filtered_lines)
        self.sent_lines = 0
        
        if self.total_lines == 0:
            messagebox.showwarning("Warning", "No G-code to send!")
            return

        # Create progress window
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Streaming G-code")
        self.progress_window.geometry("400x150")
        self.progress_window.transient(self.root)

        # Progress label
        ttk.Label(
            self.progress_window, text="Streaming G-code to GRBL..."
        ).pack(pady=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_window, length=350, mode="determinate"
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar["maximum"] = self.total_lines

        # Status label
        self.status_label = ttk.Label(
            self.progress_window, text=f"Line 0 / {self.total_lines}"
        )
        self.status_label.pack(pady=5)

        # Cancel button
        def cancel_run():
            self.stop_streaming()
            if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
                self.progress_window.destroy()
            messagebox.showinfo("Cancelled", "G-code execution cancelled")

        ttk.Button(
            self.progress_window, text="Cancel", command=cancel_run
        ).pack(pady=5)

        # Initialize execution tracking
        self.is_executing = True
        self.execution_path = [(self.work_pos["x"], self.work_pos["y"])]

        # Start streaming
        self.gcode_buffer = filtered_lines
        self.buffer_size = 0
        self.command_queue = []
        self.streaming = True
        
        # Start the streaming process
        self.stream_gcode_line()
        
        # Start status updates (250ms) if not already running
        if self.status_update_id is None:
            self.start_status_updates()

    except Exception as e:
        self.is_executing = False
        self.streaming = False
        messagebox.showerror("Error", f"Failed to run G-code:\n{str(e)}")
```

### 5. Update parse_status_response to update plot

In `parse_status_response`, after updating work_pos, add:

```python
# Update execution path and plot if executing
if self.is_executing:
    current_pos = (self.work_pos["x"], self.work_pos["y"])
    if not self.execution_path or current_pos != self.execution_path[-1]:
        self.execution_path.append(current_pos)
        # Update plot (but not too frequently)
        if not hasattr(self, '_last_plot_update') or time.time() - self._last_plot_update > 0.25:
            self.plot_toolpath()
            self.canvas.draw_idle()  # Use draw_idle for better performance
            self._last_plot_update = time.time()
```

## Benefits

1. **Smooth Motion**: GRBL's buffer stays full, no pauses
2. **Real-time Position**: Updates every 250ms from actual machine position
3. **Live Visualization**: Plot updates with real position during execution
4. **Non-blocking**: UI remains responsive during execution
5. **Proper Protocol**: Follows GRBL streaming recommendations

## Testing

1. Load G-code
2. Adjust G-code
3. Run adjusted G-code
4. Observe smooth motion
5. Watch WPos/MPos update every 250ms
6. See laser head position on plot update in real-time

## Notes

- GRBL's buffer is typically 127 bytes
- Keeping it 80% full provides smooth motion with headroom
- Status updates are separate from command streaming
- This is the industry-standard approach for GRBL streaming

