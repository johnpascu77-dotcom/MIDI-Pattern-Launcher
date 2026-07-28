# Roadmap

## Project Direction

This project is evolving from a simple MIDI pattern launcher into a **motivic MIDI device**.

The goal is not to recreate generic Bitwig devices such as probability, randomization, LFOs, arpeggiators, or scale tools. Bitwig already does those things very well.

Instead, this device should focus on something more specific:

> Store, launch, transform, compare, and selectively mutate short musical motives.

The plugin should act as a **motivic memory and transformation engine**, while Bitwig remains the modulation and automation environment.

---

## Core Design Principle

Bitwig should provide:

- modulation
- automation
- macros
- random sources
- Steps modulators
- LFOs
- device-chain routing
- performance control

The plugin should provide:

- stored symbolic motives
- pattern launch logic
- motivic transformations
- targeted step editing
- clear visual comparison of motives
- structured musical operations

In short:

> Bitwig decides when and how values move.  
> The plugin decides what musical structure those values affect.

---

# Current Plugin: MIDI Pattern Launcher

## Current State

The MIDI Pattern Launcher currently supports:

- 3 stored patterns
- 16 steps per pattern
- MIDI-triggered pattern launching
- bar-quantized switching
- active/pending pattern display
- per-step note, velocity, and duration editing
- per-pattern transpose
- per-pattern rotation
- per-pattern inversion
- host automation parameters for:
  - Active Pattern
  - P1/P2/P3 Transpose
  - P1/P2/P3 Rotation
  - P1/P2/P3 Inversion
- pattern copy tools
- pattern clear tool

Current version:

```text
v1.9.0 - Pattern tools
```

---

# Conceptual Identity

The MIDI Pattern Launcher should remain focused on:

```text
Motive memory + motive launch + structural motive transformation
```

It should not become a bloated all-in-one sequencer.

It should avoid duplicating features already better handled by Bitwig, such as:

- generic probability
- generic randomization
- internal LFOs
- internal step modulators
- generic velocity humanization
- generic arpeggiation
- generic scale quantization

Future features should be accepted only if they strengthen the plugin as a **motivic transformation device**.

---

# MIDI Note Naming Decision

Because different DAWs use different octave numbering conventions, especially the C3/C4 mismatch, the plugin will continue to display **MIDI note numbers** rather than note names.

Example:

```text
60
64
67
72
```

This avoids ambiguity in Bitwig, where C3 may correspond to MIDI note 60.

---

# Planned MIDI Pattern Launcher Development

---

## v1.10.0 — Target Step Parameters

### Goal

Expose a small, focused set of host-automatable parameters that allow Bitwig to edit or modulate one selected structural point of the motive.

This solves the current editing pain point where changing a pitch requires repeatedly clicking `Note +` or `Note -`.

### Concept

Add a single **Target Step** editing system.

The target represents:

```text
which pattern
which step
which note value
which velocity
which duration
whether the step is enabled
```

This allows Bitwig modulators such as Steps, Random, or square LFOs to modify one musical point in the motive.

Example use case:

```text
Target Pattern = Pattern 1
Target Step = 5
Target Note = modulated by Bitwig Steps
```

Result:

> Only step 5 of Pattern 1 changes pitch over time.

This is not generic randomization. It is targeted motivic mutation.

### Parameters to Add

```text
Target Pattern
Target Step
Target Note
Target Velocity
Target Duration
Target Enabled
```

Suggested ranges:

```text
Target Pattern: Pattern 1 / Pattern 2 / Pattern 3
Target Step: 1-16
Target Note: 0-127
Target Velocity: 1-127
Target Duration: 1-16
Target Enabled: Off/On
```

### Behavior

When Target Pattern or Target Step changes:

- load the selected step into the target parameters
- if the step is a rest:
  - Target Enabled = Off
  - Target Note uses a safe default, probably 60
  - Target Velocity uses a safe default, probably 100
  - Target Duration uses a safe default, probably 1

When Target Note changes:

- if Target Enabled is On, rewrite the selected step note
- if Target Enabled is Off, update the parameter value only

When Target Velocity changes:

- if Target Enabled is On, rewrite the selected step velocity
- if Target Enabled is Off, update the parameter value only

When Target Duration changes:

- if Target Enabled is On, rewrite the selected step duration
- if Target Enabled is Off, update the parameter value only

When Target Enabled turns On:

- create a note at the target step using:
  - Target Note
  - Target Velocity
  - Target Duration

When Target Enabled turns Off:

- clear the target step

### Important Conceptual Distinction

Target Step Parameters rewrite the stored motive.

This is different from transpose, rotation, and inversion, which are non-destructive playback transformations.

Target Step Parameters are **motive editing parameters**.

Transpose, rotation, and inversion are **motive performance/interpretation parameters**.

---

## v1.11.0 — Pattern Matrix UI

### Goal

Redesign the visual interface so all three patterns are visible at once.

The current UI is useful but still centered around one selected pattern. The next visual direction should make the three motives comparable at a glance.

### Proposed Layout

```text
MIDI Pattern Launcher
v1.11.0 - Pattern matrix

Status:
Active: P2 | Pending: P1 | Bar: 16 | Step: 4

Pattern Matrix:
P1  [1][2][3][4][5]...[16]   Tr 0   Rot +2   Inv On
P2  [1][2][3][4][5]...[16]   Tr +7  Rot 0    Inv Off
P3  [1][2][3][4][5]...[16]   Tr -5  Rot +4   Inv Off

Target:
Pattern 1 | Step 5 | Note 67 | Vel 100 | Dur 4 | Enabled

Tools:
Copy Pattern | Clear Pattern | Clear Step | Make Note
```

### UI Principles

- show all three pattern rows stacked vertically
- clicking a step selects:
  - Target Pattern
  - Target Step
- keep MIDI note numbers
- show duration as `d1`, `d2`, `d4`, etc.
- highlight:
  - active playback pattern
  - current playback step
  - selected target step
- show per-pattern transform status next to each row:
  - transpose
  - rotation
  - inversion

### Result

The plugin becomes a **motivic matrix**, not just a single-row step editor.

This supports fast visual evaluation of the rhythmic and pitch relationship between Pattern 1, Pattern 2, and Pattern 3.

---

## v1.12.0 — Direct Visual Editing

### Goal

Make the pattern matrix directly editable with the mouse.

This is a usability improvement after the Target Step system exists.

### Proposed Interactions

```text
Click step:
    select Target Pattern and Target Step

Double-click empty step:
    create note

Double-click note step:
    clear note

Drag step vertically:
    change note

Shift + drag vertically:
    change velocity

Alt + drag vertically:
    change duration

Right-click step:
    clear step

Mouse wheel over step:
    adjust note
```

### Purpose

This makes the plugin feel less like a prototype and more like a playable/editable instrument.

The Bitwig device panel remains useful for modulation, while the plugin UI becomes useful for quick visual editing.

---

## v1.13.0 — Motivic Operations

### Goal

Add operations that are specifically motivic, not generic random utilities.

These operations should manipulate the relationship between rhythm, pitch order, contour, and variation.

### Candidate Operations

#### Copy Operations

```text
Copy full pattern
Copy rhythm only
Copy pitches only
Copy durations only
Copy velocities only
```

#### Transform Operations

```text
Reverse rhythm
Reverse pitch order
Rotate pitch order
Rotate rhythm only
Normalize durations
Compress durations
Expand durations
```

#### More Advanced Possibilities

```text
Interval expansion/compression
Contour preservation with interval remapping
Register folding
Axis-based pitch reflection variants
```

### Important

Avoid turning this into generic randomization.

The question for every operation should be:

> Does this create a meaningful motivic variation?

If yes, it belongs.

If it merely duplicates a generic Bitwig process, it probably does not.

---

# Possible Future Feature — Commit Mode

Target Step automation may eventually need a commit timing mode.

### Problem

If Bitwig modulates Target Note continuously, the stored step can change immediately and possibly mid-pattern.

This may be desirable for some uses, but for motivic mutation, it may be better to commit changes only at musically meaningful boundaries.

### Possible Parameter

```text
Target Commit Mode
```

Options:

```text
Immediate
Next Bar
Next Pattern Loop
```

### Behavior

#### Immediate

Target parameter changes rewrite the motive instantly.

Pros:

- simple
- responsive
- good for manual knob editing

Cons:

- can change mid-loop

#### Next Bar

Changes are stored as pending values and committed at the next bar boundary.

Pros:

- musically stable
- good for one-note-per-loop mutation

Cons:

- more implementation complexity

#### Next Pattern Loop

Changes are committed when the pattern cycle restarts.

Pros:

- strongest motivic coherence

Cons:

- requires more careful pattern timing logic

### Recommendation

Do not implement this immediately.

Start with Immediate mode in v1.10.0.

Consider Commit Mode later if modulation produces musically unstable behavior.

---

# Companion Plugin Concept

## Working Name

```text
Motive Transformer
```

Alternative names:

```text
Motif Processor
MIDI Motive Shaper
Motivic Event Processor
Motive Lens
Motif Mutator
```

Preferred current name:

```text
Motive Transformer
```

---

## Core Concept

Create a second MIDI effect plugin intended to follow MIDI Pattern Launcher in the Bitwig device chain.

Example chain:

```text
MIDI Pattern Launcher -> Motive Transformer -> Instrument
```

The current plugin stores and launches motives.

The companion plugin transforms the resulting MIDI stream.

---

## Architectural Split

### MIDI Pattern Launcher

Role:

```text
Motive memory and launch system
```

Responsibilities:

- store motives
- launch patterns
- switch patterns on bar boundaries
- provide structural per-pattern transforms
- provide target-step editing
- show all motives visually

It knows:

```text
patterns
steps
stored notes
durations
velocities
```

It should not become a complex live stream processor.

---

### Motive Transformer

Role:

```text
Live MIDI stream motivic transformer
```

Responsibilities:

- listen to incoming MIDI
- count note events
- transform selected event positions
- expose transformation parameters
- correctly map transformed note-offs
- reset counters by host bar/cycle

It knows:

```text
incoming MIDI events
event order
host timing
note-on/note-off relationships
```

It does not store full patterns.

---

# Motive Transformer v0.1.0 / v1.0.0 — Target Event Transformer

## Goal

Transform only the Nth note event within a repeating cycle.

This complements Target Step editing in the launcher.

### Conceptual Difference

#### Target Step in MIDI Pattern Launcher

```text
Modify step 5 of Pattern 1.
```

This rewrites a structural grid position in the stored motive.

#### Target Event in Motive Transformer

```text
Modify the 3rd note event in each bar.
```

This transforms the live MIDI stream without rewriting the source motive.

Both are useful and distinct.

---

## Initial Parameters

```text
Target Active
Target Event
Target Transpose
Target Velocity Offset
Cycle Bars
Reset Mode
```

Suggested ranges:

```text
Target Active: Off/On
Target Event: 1-16
Target Transpose: -48 to +48
Target Velocity Offset: -64 to +64
Cycle Bars: 1-8
Reset Mode: Bar / Transport Start / Manual
```

### Example

```text
Target Event = 3
Target Transpose = +2
Target Active = On
Cycle Bars = 1
```

Result:

> The third note event of each bar is transposed up two semitones.

---

## Bitwig Modulation Examples

### Example 1 — One changing note per bar

```text
Target Event = 3
Target Transpose = modulated by Bitwig Steps
```

Result:

> The third event changes interval every bar.

### Example 2 — Moving target event

```text
Target Event = modulated by Bitwig Steps: 1, 3, 2, 4
Target Transpose = +12
```

Result:

> A different note of the motive is octave-shifted each bar.

### Example 3 — Subtle event mutation

```text
Target Event = 2
Target Transpose = Random quantized to -2, 0, +2
```

Result:

> Only the second event receives small melodic variation.

---

## Technical Requirement: Note-Off Mapping

If the transformer changes a note-on pitch, it must also transform the matching note-off.

Example:

```text
Incoming note-on: 67
Output note-on: 70

Incoming note-off: 67
Output note-off: 70
```

The plugin must maintain an active-note mapping table to prevent stuck notes.

Possible key:

```text
channel + original note
```

Stored value:

```text
transformed note
```

This is critical.

---

## v1.0 Scope Limitation

Do not implement duration/gate changes in the first version.

Pitch and velocity transformations are safer and simpler.

Duration changes require rescheduling note-offs and are more complex.

Initial scope:

```text
transpose selected event
offset velocity of selected event
safe note-off mapping
cycle reset
```

Later versions may add duration/gate processing.

---

# Motive Transformer Future Features

## Multiple Target Lanes

Allow several event positions to be transformed independently.

Example:

```text
Lane 1: Event 1, Transpose +0
Lane 2: Event 2, Transpose +7
Lane 3: Event 3, Transpose -2
Lane 4: Event 4, Transpose +12
```

Possible parameters:

```text
Lane 1 Active
Lane 1 Event
Lane 1 Transpose
Lane 1 Velocity Offset

Lane 2 Active
Lane 2 Event
Lane 2 Transpose
Lane 2 Velocity Offset
...
```

Start with one lane. Add more only if musically justified.

---

## Target Modes

Possible future target modes:

```text
Event Index
Grid Step
Pitch Class
Register
Velocity Range
```

### Event Index Mode

Transform the Nth incoming note event in each cycle.

### Grid Step Mode

Transform notes occurring at a specific sixteenth-note grid position.

Requires host timing and PPQ analysis.

### Pitch Class Mode

Transform notes belonging to a selected pitch class.

Example:

```text
Transform all pitch class 0 notes
```

### Register Mode

Transform notes below or above a selected note threshold.

Example:

```text
Transpose only notes below 60
```

---

## Duration/Gate Transformation

Possible later feature:

```text
Target Duration Scale
Target Gate Offset
```

Requires:

- delaying or suppressing incoming note-offs
- scheduling transformed note-offs
- robust stuck-note protection
- transport-stop panic handling

This should be deferred until pitch/velocity transformation is stable.

---

# Ecosystem Vision

The long-term system could become:

```text
MIDI Pattern Launcher -> Motive Transformer -> Instrument
```

or:

```text
Motive memory -> Motive stream transformation -> Sound generation
```

The two plugins should have distinct roles:

## MIDI Pattern Launcher

```text
What the motive is.
```

## Motive Transformer

```text
How one performance of the motive is bent.
```

This split prevents the launcher from becoming overcomplicated and follows the Bitwig philosophy of modular device chains.

---

# Near-Term Next Session Plan

## Primary Goal

Start:

```text
v1.10.0 - Target Step Parameters
```

Branch name:

```text
feature/v1.10.0-target-step-parameters
```

## Steps

1. Ensure `main` contains the completed v1.9.0 work.
2. Create the v1.10.0 branch.
3. Add new APVTS parameters:
   - Target Pattern
   - Target Step
   - Target Note
   - Target Velocity
   - Target Duration
   - Target Enabled
4. Add processor-side sync logic.
5. Connect plugin UI step selection to Target Pattern and Target Step.
6. Connect step editing buttons to target parameter updates.
7. Test Bitwig device panel editing.
8. Test Bitwig modulation of Target Note.
9. Commit as:
   ```text
   Add target step automation parameters
   ```
10. Tag:
   ```text
   v1.10.0
   ```

---

# Guiding Questions for Future Decisions

Before adding any feature, ask:

## Does it strengthen motivic transformation?

If yes, consider it.

## Is it already easier or better in Bitwig?

If yes, probably do not add it.

## Does it belong to stored motive memory or live MIDI stream transformation?

If stored memory:

```text
MIDI Pattern Launcher
```

If live stream processing:

```text
Motive Transformer
```

## Does it preserve clarity?

Avoid parameter explosion unless the musical payoff is high.

## Does it invite compositional control rather than generic randomness?

Prefer structured mutation over random feature accumulation.

---

# Summary

The project direction is now clear:

## MIDI Pattern Launcher

A focused motivic memory and launch device with structural transformation and targeted step mutation.

## Motive Transformer

A future companion MIDI processor that transforms selected note events in the live MIDI stream.

Together, they form a Bitwig-native motivic composition system:

```text
store motives
launch motives
transform motives
mutate specific points
bend live event streams
```

The next implementation target is:

```text
v1.10.0 - Target Step Parameters
```
