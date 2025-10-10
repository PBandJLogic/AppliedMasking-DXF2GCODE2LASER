# Single-Step and GRBL Streaming Features

## Overview

The G-code Adjuster now supports both continuous streaming and single-step execution modes for debugging and precision control.

## Button Layout

```
[Run] [Step] [Next] [STOP]  [Save Adjusted G-code]
 8ch   8ch    8ch    red
```

## Execution Modes

### 1. Run Mode (Continuous Streaming)

**Button**: `Run`

**Behavior**:
- Streams G-code continuously to GRBL
- Keeps buffer 80% full for smooth motion
- Updates position every 250ms
- Shows progress bar
- Non-blocking UI

**Use when**: Normal operation, production runs

### 2. Step Mode (Single-Step Debugging)

**Buttons**: `Step` (to start), then `Next` (to advance)

**Behavior**:
- Sends one G-code line at a time
- Pauses automatically after each line
- Click "Next" to send next line
- Shows current line being executed
- Updates position after each step
- Perfect for debugging

**Use when**: 
- Testing new G-code
- Debugging issues
- Learning machine behavior
- Precision verification

### 3. Emergency Stop

**Button**: `STOP` (Red, bold)

**Behavior**:
- Sends Ctrl-X (soft reset) to GRBL
- Clears GRBL's internal buffer immediately
- Turns off laser (M5 command)
- Stops streaming
- Closes progress window
- Machine may need rehoming after

**Use when**: Emergency situations only

## Workflow Examples

### Normal Operation

1. Load G-code file
2. Set reference points (jog + click Set)
3. Click "Adjust G-code"
4. Click **"Run"**
5. Watch smooth execution
6. Position updates every 250ms
7. Plot shows laser path in real-time

### Debugging with Single-Step

1. Load G-code file
2. Set reference points
3. Click "Adjust G-code"
4. Click **"Step"** to start
5. Progress window opens with "Next Step" button
6. First line executes and pauses
7. Click **"Next"** to advance to next line
8. Repeat until satisfied or done
9. Click "Stop" to cancel

### Emergency Stop

If anything goes wrong during execution:
1. Click **"STOP"** button (red)
2. Machine halts immediately
3. Buffer clears
4. Laser turns off
5. May need to home machine

## Technical Details

### GRBL Streaming Protocol

**Buffer Management**:
- GRBL has 127-byte RX buffer
- We keep it 80% full (~100 bytes)
- Commands queue when buffer is full
- 'ok' responses reduce buffer tracking

**Status Updates**:
- Independent 250ms timer
- Sends `?` command to GRBL
- Updates WPos, MPos displays
- Updates plot with current position
- Doesn't interfere with streaming

**Advantages over Line-by-Line**:
- ✅ Smooth, continuous motion
- ✅ No pauses between commands
- ✅ Real-time position feedback
- ✅ Proper GRBL protocol usage
- ✅ Better performance

### Single-Step Implementation

**State Variables**:
- `self.single_step_mode` - Boolean flag
- `self.step_paused` - Currently waiting for user
- `self.current_line_text` - Line being executed

**Control Flow**:
1. User clicks "Step"
2. Sets `single_step_mode = True`
3. Calls `run_adjusted_gcode()`
4. After each line sent, sets `step_paused = True`
5. Enables "Next" buttons
6. Waits for user to click "Next"
7. Continues to next line

## GUI Elements

### Main Control Panel

**Buttons**:
- **Run** (8 chars) - Start continuous streaming
- **Step** (8 chars) - Start single-step mode
- **Next** (8 chars) - Advance to next step (disabled until stepping)
- **STOP** (6 chars, red) - Emergency stop (disabled until running)

### Progress Window

**Normal Mode**:
```
Title: "Streaming G-code"
Header: "Streaming G-code to GRBL..."
Progress: [================] 45/100
Status: Line 45 / 100: G1 X10 Y20
[Stop]
```

**Single-Step Mode**:
```
Title: "Single-Step Mode"
Header: "Single-Step Mode - Click 'Next' to advance"
Progress: [====] 5/100
Status: Line 5 / 100: G0 X0 Y0
[Next Step] [Stop]
```

## Position Updates

### During Execution

**WPos/MPos** (Left Panel):
- Updates every 250ms
- Shows real machine position
- Independent of G-code parsing

**Plot** (Right Panel):
- Shows execution path (red line)
- Updates every 250ms (throttled)
- Uses `draw_idle()` for performance
- Laser position marker updates

### Buffer vs Position

- **Buffer**: Commands queued in GRBL
- **Position**: Where laser actually is
- These can differ (buffer ahead of position)
- Status updates show actual position

## Button States

| Mode | Run | Step | Next | STOP |
|------|-----|------|------|------|
| Idle | Enabled | Enabled | Disabled | Disabled |
| Running | Disabled | Disabled | Disabled | **Enabled** |
| Stepping | Disabled | Disabled | **Enabled** | **Enabled** |
| Paused (step) | Disabled | Disabled | **Enabled** | **Enabled** |

## Error Handling

### GRBL Errors
- Shown in dialog during execution
- Option to continue or stop
- Error logged to console

### Communication Errors
- Automatic streaming stop
- Error dialog shown
- STOP button disabled
- Safe state

### Buffer Overflow Protection
- Monitors buffer size
- Waits when >80% full
- Prevents overflow
- Automatic retry

## Performance Optimizations

1. **Throttled Plot Updates**: Max once per 250ms
2. **draw_idle()**: Non-blocking canvas updates  
3. **Separate Status Thread**: Doesn't block streaming
4. **Smart Buffer Management**: Keeps GRBL fed without overflow

## Tips

### For Smooth Motion
- Use "Run" mode
- Ensure good USB connection
- Keep computer from sleeping
- Close other heavy applications

### For Debugging
- Use "Step" mode
- Watch each command execute
- Verify coordinates
- Check machine response

### For Safety
- Keep hand near STOP button
- Test with laser off first
- Verify work origin before running
- Have emergency stop plan

## Keyboard Shortcuts (Future Enhancement)

Could add:
- `Space` - Next step (when in step mode)
- `Esc` - Emergency stop
- `R` - Run
- `S` - Step mode

## Code Structure

```python
# Streaming functions
start_status_updates()       # Begin 250ms position queries
stream_gcode_line()          # Main streaming loop
handle_grbl_ok()             # Process 'ok' responses
check_streaming_complete()   # Monitor completion

# Single-step functions
run_single_step()            # Start step mode
continue_step()              # Advance one step
stream_gcode_line_with_step() # Streaming with pause support

# Control functions
run_adjusted_gcode()         # Main entry point
emergency_stop()             # Immediate halt
stop_streaming()             # Clean shutdown
```

## Testing Checklist

- [ ] Run mode works smoothly
- [ ] Step mode pauses correctly
- [ ] Next button advances one line
- [ ] STOP button halts immediately
- [ ] Laser turns off on stop
- [ ] WPos/MPos update during execution
- [ ] Plot shows real-time position
- [ ] Progress bar updates correctly
- [ ] Error handling works
- [ ] Completion message appears

## Future Enhancements

Potential improvements:
- Adjustable step rate (auto-step every N seconds)
- Breakpoints on specific lines
- Run to cursor
- Conditional stops (on position/state)
- Command history viewer
- Estimated time remaining
- Feedrate override controls

