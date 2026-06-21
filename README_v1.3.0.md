# MIDI Pattern Launcher — v1.3.0

## Version Summary

**v1.3.0** introduces **non-destructive per-pattern transpose**.

This version is a stable checkpoint after the earlier pattern-launching, step-editing, and MIDI safety work.

The main musical feature is that each pattern can now be transposed independently without changing the stored step data.

---

## Core Concept

Stored pattern notes remain unchanged.

During playback, the processor reads the stored note and applies the selected pattern transpose value only at note-on generation time.

Playback chain:

```text
host step clock
→ active pattern
→ source step
→ stored note
→ pattern transpose
→ MIDI note-on
→ exact sent MIDI note stored for future note-off
```

This means transpose is a **playback lens**, not a destructive edit.

---

## Important Behavior

If transpose changes while a note is already held:

```text
already-sounding note continues normally
future note-ons use the new transpose value
pending note-offs still match the exact note originally sent
no stuck notes expected
```

This is possible because `PendingNoteOff` stores the actual output MIDI note, not the original untransposed source note.

---

## UI Features

v1.3.0 adds transpose controls:

```text
Tr -12
Tr -
Tr 0
Tr +
Tr +12
```

These affect the currently selected edit pattern.

The UI also displays the current transpose value in:

```text
Editing Pattern line
Selected Step panel
```

Example:

```text
Editing Pattern: 1    Playback Active: Pattern 1    Transpose: +12
```

For selected notes, the UI shows source note and transposed output note:

```text
Note: 60 -> 72
```

---

## Pattern Transpose Range

Each pattern has its own transpose value:

```text
Pattern 1 transpose
Pattern 2 transpose
Pattern 3 transpose
```

Range:

```text
-48 to +48 semitones
```

Values are clamped with `juce::jlimit`.

---

## Main Processor Additions

The processor includes:

```cpp
int getPatternTranspose(int patternIndex) const;
void changePatternTranspose(int patternIndex, int deltaSemitones);
void resetPatternTranspose(int patternIndex);
int getTransposedStepNote(int patternIndex, int stepIndex) const;
```

Internal storage:

```cpp
std::array<int, numPatterns> patternTranspose;
```

Initialization:

```cpp
patternTranspose = { 0, 0, 0 };
```

---

## MIDI Safety

This version keeps the MIDI safety behavior from the previous stable version.

Important safety behavior:

```text
on transport stop:
    send note-off for all 128 notes
    send all-notes-off
    clear pending note-offs

on pattern switch or stop at bar boundary:
    send note-off for all 128 notes
    send all-notes-off
    clear pending note-offs
```

This prevents long notes from hanging when the host stops or when a pattern is stopped/switched.

---

## Pattern Launch Behavior

Incoming MIDI trigger notes:

```text
C1 / note 36 → Pattern 1
D1 / note 38 → Pattern 2
E1 / note 40 → Pattern 3
```

If the requested pattern is already active:

```text
queue stop
```

Otherwise:

```text
queue requested pattern
```

Queued pattern changes are applied only at the next bar start.

---

## Step Editing Behavior

Each step stores:

```cpp
struct Step
{
    int note = -1;
    int velocity = 0;
    int durationSteps = 0;
};
```

Step note values:

```text
note >= 0 means active note
note < 0 means rest
```

Editing controls:

```text
Note -
Note +
Vel -
Vel +
Dur -
Dur +
Clear Step
Make Note
```

Step edits modify the stored pattern data directly.

Transpose does not.

---

## Known Limitations

v1.3.0 does not yet include:

```text
host-visible plugin parameters
Bitwig modulation support
state saving/loading
rotation
inversion
retrograde
randomization
probability
```

`getStateInformation()` and `setStateInformation()` are still placeholders.

---

## Stable Checkpoint Notes

This version should be preserved as:

```text
v1.3.0_non_destructive_pattern_transpose
```

Recommended Git tag:

```bash
git tag v1.3.0
```

Recommended commit message:

```bash
git commit -m "v1.3.0 non-destructive pattern transpose"
```

---

## Files Involved

Main files:

```text
Source/PluginProcessor.h
Source/PluginProcessor.cpp
Source/PluginEditor.h
Source/PluginEditor.cpp
```

---

## Future Direction After v1.3.0

The next logical feature is non-destructive pattern rotation.

Planned concept:

```text
stored pattern data remains unchanged
playback step reads from a rotated source step index
rotation is per-pattern
note-offs remain safe
```

This became the basis for v1.4.0.
