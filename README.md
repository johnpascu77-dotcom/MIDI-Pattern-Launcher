# MIDI Pattern Launcher

A JUCE-based MIDI effect plugin for launching, editing, transforming, and performing MIDI step patterns inside a DAW.

The plugin provides a compact 3-pattern MIDI pattern launcher with per-pattern transformations, matrix editing, melody editing, DAW automation support, and full state save/restore.

## Current Version

**v1.17.5b — Matrix Gesture Editing Complete**

## Main Features

### Pattern Launcher

- Three independent MIDI patterns.
- Pattern selection and launching from the plugin UI.
- Host-synced step playback.
- Support for multiple grid lengths, including ternary 12-step mode.
- Per-pattern length handling.
- Safe MIDI note-off management.

### Per-Pattern Transformations

Each pattern has independent, non-destructive transformations:

- Transpose
- Rotation
- Inversion

The transform pipeline is:

```text
Stored Step Data
? Inversion
? Transpose
? MIDI Output
```

Rotation is applied as a playback source-step offset and does not modify stored step data.

### Matrix View

The Matrix view provides fast target editing for all three patterns.

Supported Matrix gestures:

```text
Left drag   = create/keep note and paint pitch vertically
Right drag  = erase notes
Alt drag    = pitch-paint existing notes only
Ctrl drag   = velocity-paint existing notes only
Shift drag  = move existing step horizontally within the same pattern row
```

Matrix cells display:

```text
Step number
MIDI note
Velocity and duration
```

Example:

```text
12
56
v93 d1
```

### Melody View

The Melody view provides a piano-roll-style editor for note placement and duration editing.

Supported Melody gestures:

```text
Left drag on empty area       = create note / set length
Right click note              = erase note
Shift drag note               = move note in time
Alt drag note                 = edit pitch
Alt + Shift drag note         = edit pitch and length
Ctrl drag note                = edit velocity
```

### DAW Automation

The plugin exposes explicit per-pattern automation parameters for:

- Pattern 1 transpose
- Pattern 1 rotation
- Pattern 1 inversion
- Pattern 2 transpose
- Pattern 2 rotation
- Pattern 2 inversion
- Pattern 3 transpose
- Pattern 3 rotation
- Pattern 3 inversion

This avoids ambiguity between UI edit selection and DAW automation targets.

### State Save / Restore

The plugin saves and restores:

- Pattern step notes
- Step velocities
- Step durations
- Pattern lengths
- Pattern transpose values
- Pattern rotation values
- Pattern inversion states
- Selected edit state where applicable

Playback remains stopped after restore to avoid unexpected MIDI output.

## Build

This project is built with JUCE and CMake.

Example build command:

```powershell
cmake --build build-cmake --config Release
```

## Project Status

The core plugin feature set is complete.

The latest development milestone completed Matrix gesture editing and improved visibility of note velocity and duration directly inside Matrix cells.

## License

Add your preferred license here.

## Composer Bridge Protocol

MIDI Pattern Launcher includes a Composer Bridge SysEx protocol for external tools, scripts, and hardware controllers.

Composer Bridge supports:

- Writing individual pattern steps.
- Clearing patterns.
- Copying patterns.
- Writing complete 16-step patterns.
- Requesting full pattern dumps from the plugin.
- ACK/NACK feedback for external commands.

Protocol documentation is available here:

- `Docs/ComposerBridgeProtocol.md`

A Python reference client is available here:

- `tools/composer_bridge_client.py`

The reference client requires:

    pip install mido python-rtmidi

Example commands:

    python tools/composer_bridge_client.py list
    python tools/composer_bridge_client.py dump --out "MIDI Pattern Launcher" --in "MIDI Pattern Launcher" --pattern 0
    python tools/composer_bridge_client.py set-step --out "MIDI Pattern Launcher" --pattern 0 --step 0 --enabled 1 --note 60 --velocity 100 --duration 1

Composer Bridge must be enabled in the plugin before external SysEx commands are handled.
