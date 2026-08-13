# MIDI Pattern Launcher v1.24.0 Composer Bridge Protocol

The Composer Bridge allows external MIDI tools, DAW MIDI clips, scripts, and controller devices to edit pattern data by sending MIDI SysEx messages to the plugin.

As of v1.24.0, Debug builds include a constructor-time Composer Bridge protocol self-test harness that validates ACK/NACK behavior for valid, malformed, invalid-pattern, invalid-step, and unsupported-command SysEx messages.

Composer Bridge messages are handled only when **Composer Bridge Enabled** is enabled in the plugin UI. This switch is independent from the general **External Control Enabled** setting used for MIDI CC control.

## SysEx packet format

```text
F0 7D 4D 50 4C 01 CMD ... F7
```

## Header

| Byte | Hex | Meaning |
|---:|---:|---|
| 0 | `F0` | SysEx start |
| 1 | `7D` | Non-commercial / educational manufacturer ID |
| 2 | `4D` | ASCII `M` |
| 3 | `50` | ASCII `P` |
| 4 | `4C` | ASCII `L` |
| 5 | `01` | Protocol version |
| 6 | `CMD` | Command |
| Last | `F7` | SysEx end |

JUCE exposes the internal payload to the plugin as:

```text
7D 4D 50 4C 01 CMD ...
```

## Indexing

Patterns and steps are zero-based.

| User-facing name | Protocol value |
|---|---:|
| Pattern 1 | `00` |
| Pattern 2 | `01` |
| Pattern 3 | `02` |
| ... | ... |
| Pattern 8 | `07` |
| Step 1 | `00` |
| Step 16 | `0F` |

## Command `01` - Set step

```text
F0 7D 4D 50 4C 01 01 pattern step enabled note velocity duration F7
```

| Field | Range | Meaning |
|---|---:|---|
| `pattern` | `00`-`07` | Target pattern |
| `step` | `00`-`0F` | Target step |
| `enabled` | `00` or `01` | Whether the step contains a note |
| `note` | `00`-`7F` | MIDI note number |
| `velocity` | `01`-`7F` | MIDI velocity |
| `duration` | `01`-`10` | Duration in steps, 1-16 decimal |

If `enabled` is `00`, the target step is cleared. In that case, `note`, `velocity`, and `duration` are ignored.

### Example: Set Pattern 1 Step 4 to C3 velocity 100 duration 1

```text
F0 7D 4D 50 4C 01 01 00 03 01 3C 64 01 F7
```

Meaning:

```text
Pattern 1
Step 4
Enabled
Note 60
Velocity 100
Duration 1
```

### Example: Clear Pattern 2 Step 8

```text
F0 7D 4D 50 4C 01 01 01 07 00 00 00 00 F7
```

## Command `02` - Clear pattern

```text
F0 7D 4D 50 4C 01 02 pattern F7
```

| Field | Range | Meaning |
|---|---:|---|
| `pattern` | `00`-`07` | Pattern to clear |

### Example: Clear Pattern 1

```text
F0 7D 4D 50 4C 01 02 00 F7
```

## Command `03` - Copy pattern

```text
F0 7D 4D 50 4C 01 03 sourcePattern destinationPattern F7
```

| Field | Range | Meaning |
|---|---:|---|
| `sourcePattern` | `00`-`07` | Pattern to copy from |
| `destinationPattern` | `00`-`07` | Pattern to copy to |

### Example: Copy Pattern 1 to Pattern 2

```text
F0 7D 4D 50 4C 01 03 00 01 F7
```


## Command `04` - Write full pattern

Writes all 16 steps of one pattern in a single SysEx message.

```text
F0 7D 4D 50 4C 01 04 pattern
   step0_enabled step0_note step0_velocity step0_duration
   step1_enabled step1_note step1_velocity step1_duration
   ...
   step15_enabled step15_note step15_velocity step15_duration
F7
```

JUCE exposes the internal payload to the plugin as:

```text
7D 4D 50 4C 01 04 pattern [16 x enabled note velocity duration]
```

| Field | Range | Meaning |
|---|---:|---|
| `pattern` | `00`-`07` | Target pattern |
| `stepN_enabled` | `00`-`7F` | `00` clears the step; any non-zero value writes/enables the step |
| `stepN_note` | `00`-`7F` | MIDI note number for step `N` |
| `stepN_velocity` | `00`-`7F` | MIDI velocity for step `N` |
| `stepN_duration` | `00`-`7F` | Duration in pattern steps for step `N` |

Each of the 16 step records contains 4 bytes:

```text
enabled note velocity duration
```

If `enabled` is `00`, the target step is cleared. In that case, `note`, `velocity`, and `duration` are ignored by the clear operation.

### Example: Write Pattern 1 with notes on steps 1, 5, 9, and 13

```text
F0 7D 4D 50 4C 01 04 00
   01 3C 64 01
   00 3C 64 01
   00 3C 64 01
   00 3C 64 01
   01 40 64 01
   00 3C 64 01
   00 3C 64 01
   00 3C 64 01
   01 43 64 01
   00 3C 64 01
   00 3C 64 01
   00 3C 64 01
   01 48 64 01
   00 3C 64 01
   00 3C 64 01
   00 3C 64 01
F7
```

## Notes

- Unknown commands with a valid Composer Bridge header are consumed and ignored.
- Malformed known commands with valid headers are consumed and ignored.
- SysEx messages with other headers are ignored by the Composer Bridge.
- Composer Bridge uses its own **Composer Bridge Enabled** switch, independent from the general **External Control Enabled** setting.
