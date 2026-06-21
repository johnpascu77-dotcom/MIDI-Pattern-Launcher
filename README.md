## v1.5.0 - Pattern Inversion

### Added
- Non-destructive per-pattern pitch inversion.
- Inversion mirrors notes around C4 / MIDI note 60.
- Added Inv Off / Inv On control to the transform row.
- Added inversion state display to the main editor and selected-step panel.

### Transform Pipeline
Stored Note -> Inversion -> Transpose -> MIDI Output

### Preserved
- Stored MIDI step data remains unchanged.
- Existing transpose and rotation behavior remains compatible.
- Pending note-off safety continues to use the exact emitted MIDI note.

# MIDI Pattern Launcher — v1.4.0

## Version Summary

**v1.4.0** introduces **non-destructive per-pattern rotation**.

This version builds directly on v1.3.0 and keeps the transpose system intact.

The main musical feature is that each pattern can now be rhythmically rotated by steps without changing the stored step data.

---

## Core Concept

Stored pattern steps remain unchanged.

During playback, the sequencer clock still advances normally, but the source step is chosen through a rotation offset.

Playback chain:

```text
host step clock
→ active pattern
→ playback step index
→ rotation chooses source step index
→ stored note/velocity/duration
→ transpose applied
→ MIDI note-on
→ exact sent MIDI note stored for future note-off
```

This means rotation is a **playback lens**, not a destructive edit.

---

## Rotation Meaning

Rotation is stored per pattern as an integer:

```text
0 to 15
```

Meaning:

```text
0  = no rotation
+1 = stored material sounds one sixteenth later
+2 = stored material sounds two sixteenths later
...
+15 = stored material sounds fifteen sixteenths later
```

Implementation logic:

```cpp
sourceStepIndex = playbackStepIndex - rotation
```

with wraparound inside:

```text
0..15
```

So if playback is currently at step 5 and rotation is +1, the processor reads from stored step 4.

---

## UI Features

v1.4.0 adds rotation controls:

```text
Rot -
Rot 0
Rot +
```

These affect the currently selected edit pattern.

The UI displays rotation in:

```text
Editing Pattern line
Selected Step panel
```

Example:

```text
Editing Pattern: 1    Playback Active: Pattern 1    Tr: 0    Rot: +1
```

---

## Important UI Note

The step monitor still shows the **stored pattern data**, not the rotated playback result.

This is intentional.

Example:

```text
Stored step 1 contains note 60
Rotation is +1
The note sounds on playback step 2
The UI still shows note 60 on stored step 1
```

This preserves the idea that rotation is a non-destructive playback transformation.

---

## Rotation Range and Wraparound

Each pattern has its own rotation value:

```text
Pattern 1 rotation
Pattern 2 rotation
Pattern 3 rotation
```

Range:

```text
0 to 15
```

Wraparound behavior:

```text
Rot + from +15 → 0
Rot - from 0   → +15
```

This is implemented with positive modulo logic.

---

## Main Processor Additions

The processor includes:

```cpp
int getPatternRotation(int patternIndex) const;
void changePatternRotation(int patternIndex, int deltaSteps);
void resetPatternRotation(int patternIndex);
int getRotatedSourceStepIndex(int patternIndex, int playbackStepIndex) const;
```

Internal storage:

```cpp
std::array<int, numPatterns> patternRotation;
```

Initialization:

```cpp
patternRotation = { 0, 0, 0 };
```

---

## Main Playback Change

v1.3.0 read the active step directly from the pattern:

```cpp
const int stepIndex = ((stepsSincePatternStart % patternLength) + patternLength) % patternLength;
const Step currentStepData = getStepForPattern(activePattern, stepIndex);
```

v1.4.0 separates playback position from source step:

```cpp
const int playbackStepIndex = ((stepsSincePatternStart % patternLength) + patternLength) % patternLength;
const int sourceStepIndex = getRotatedSourceStepIndex(activePattern, playbackStepIndex);
const Step currentStepData = getStepForPattern(activePattern, sourceStepIndex);
```

The playback clock is unchanged.

Only the source step lookup changes.

---

## Interaction With Transpose

Rotation and transpose are both non-destructive.

Order of operations:

```text
1. rotation chooses source step
2. stored note is read
3. transpose is applied
4. MIDI note-on is sent
5. exact output note is stored for note-off
```

This keeps note-offs safe even if transpose or rotation changes while notes are held.

---

## Important Behavior

If rotation changes while a note is already held:

```text
already-sounding note continues normally
future note-ons use the new rotation value
pending note-offs still match the exact note originally sent
no stuck notes expected
```

---

## MIDI Safety

v1.4.0 keeps the same MIDI safety behavior from v1.3.0.

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

Transpose and rotation do not.

---

## Test Checklist Passed

The following behavior was tested successfully:

```text
rotation changes future note-ons
Rot + shifts pattern material later by one sixteenth
Rot 0 resets rotation
Rot - from 0 wraps to +15
Rot + from +15 wraps to 0
each pattern remembers its own rotation
held notes receive correct note-offs
no stuck notes observed
UI displays rotation correctly
transpose still works
pattern triggering still works
```

---

## Known Limitations

v1.4.0 does not yet include:

```text
host-visible plugin parameters
Bitwig modulation support
state saving/loading
inversion
retrograde
randomization
probability
quantized modulation modes
```

`getStateInformation()` and `setStateInformation()` are still placeholders.

---

## Stable Checkpoint Notes

This version should be preserved as:

```text
v1.4.0_non_destructive_pattern_rotation
```

Recommended Git tag:

```bash
git tag v1.4.0
```

Recommended commit message:

```bash
git commit -m "v1.4.0 non-destructive pattern rotation"
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

## Future Direction After v1.4.0

Recommended next steps:

```text
v1.4.1
UI consolidation:
- combine transpose and rotation into one horizontal transform row
- reduce vertical growth
- no engine changes

v1.5.0
Non-destructive inversion:
- per-pattern inversion on/off
- per-pattern pivot note

v1.6.0
Host-visible parameters / APVTS:
- expose transpose and rotation to Bitwig
- enable host automation/modulation
- implement state saving/loading

v1.7.0
Quantized modulation modes:
- immediate
- next step
- next bar
```

---

## Architectural Note

v1.4.0 now has two stable non-destructive transformation layers:

```text
Rotation: changes where pattern material is read from
Transpose: changes pitch at note-on time
```

Current playback transformation order:

```text
playback step
→ rotation
→ stored step
→ transpose
→ MIDI output
```

This architecture is suitable for future transformations such as:

```text
inversion
retrograde
probability
mutation
seeded randomization
host modulation
```
