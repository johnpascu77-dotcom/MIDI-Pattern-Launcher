from pathlib import Path

header_path = Path("Source/PluginEditor.h")
cpp_path = Path("Source/PluginEditor.cpp")

if not header_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.h not found")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

header = header_path.read_text(encoding="utf-8")
cpp = cpp_path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Patch PluginEditor.h enum: add MoveExistingTime.
# -----------------------------------------------------------------------------

old_enum = '''    enum class MelodyEditDragMode
    {
        None,
        CreateOrResize,
        ResizeExistingDuration,
        MoveExistingPitch,
        MoveExistingPitchAndDuration
    };
'''

new_enum = '''    enum class MelodyEditDragMode
    {
        None,
        CreateOrResize,
        ResizeExistingDuration,
        MoveExistingTime,
        MoveExistingPitch,
        MoveExistingPitchAndDuration
    };
'''

if old_enum not in header:
    raise SystemExit("ERROR: Could not patch MelodyEditDragMode enum in PluginEditor.h")

header = header.replace(old_enum, new_enum, 1)


# -----------------------------------------------------------------------------
# 2. Patch PluginEditor.h declarations: add move helper.
# -----------------------------------------------------------------------------

old_decls = '''    void startMelodyDurationDrag(int stepIndex, int midiNote);
    void updateMelodyDragDurationAtMousePosition(juce::Point<int> position);
    void updateMelodyDragPitchAtMousePosition(juce::Point<int> position);

    bool melodyStepRangeOverlapsExistingNote(int patternIndex,
'''

new_decls = '''    void startMelodyDurationDrag(int stepIndex, int midiNote);
    void updateMelodyDragDurationAtMousePosition(juce::Point<int> position);
    void updateMelodyDragPitchAtMousePosition(juce::Point<int> position);
    void updateMelodyDragMoveAtMousePosition(juce::Point<int> position);

    bool melodyStepRangeOverlapsExistingNote(int patternIndex,
'''

if old_decls not in header:
    raise SystemExit("ERROR: Could not patch move helper declaration in PluginEditor.h")

header = header.replace(old_decls, new_decls, 1)


# -----------------------------------------------------------------------------
# 3. Patch PluginEditor.h state: add click offset.
# -----------------------------------------------------------------------------

old_state = '''    int melodyDragOriginalStep = -1;
    int melodyDragOriginalNote = -1;
    int melodyDragOriginalDuration = 1;
    int melodyDragOriginalVelocity = 100;

    juce::TextButton editPattern1Button{ "Edit P1" };
'''

new_state = '''    int melodyDragOriginalStep = -1;
    int melodyDragOriginalNote = -1;
    int melodyDragOriginalDuration = 1;
    int melodyDragOriginalVelocity = 100;
    int melodyDragClickOffsetSteps = 0;

    juce::TextButton editPattern1Button{ "Edit P1" };
'''

if old_state not in header:
    raise SystemExit("ERROR: Could not patch melody drag state in PluginEditor.h")

header = header.replace(old_state, new_state, 1)

header_path.write_text(header, encoding="utf-8")


# -----------------------------------------------------------------------------
# 4. Insert updateMelodyDragMoveAtMousePosition() before updateSelectedStep...
# -----------------------------------------------------------------------------

insert_marker = '''void MidiPatternLauncherAudioProcessorEditor::updateSelectedStepFromMousePosition(juce::Point<int> position)
'''

if insert_marker not in cpp:
    raise SystemExit("ERROR: Could not find insertion marker for move drag function")

if "void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragMoveAtMousePosition(" in cpp:
    raise SystemExit("ERROR: updateMelodyDragMoveAtMousePosition() already exists")

move_function = r'''void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragMoveAtMousePosition(
    juce::Point<int> position)
{
    if (!isDraggingMelodyDuration)
        return;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (melodyDragPattern < 0 || melodyDragPattern >= 3)
        return;

    if (melodyDragOriginalStep < 0 || melodyDragOriginalStep >= gridStepCount)
        return;

    int hoverStepIndex = -1;
    int hoverMidiNote = -1;

    if (!getMelodyPaintCellAtPosition(position, hoverStepIndex, hoverMidiNote))
        return;

    juce::ignoreUnused(hoverMidiNote);

    const int duration = juce::jlimit(
        1,
        gridStepCount,
        melodyDragOriginalDuration);

    const int maxStartStep = juce::jmax(0, gridStepCount - duration);

    const int requestedStartStep = juce::jlimit(
        0,
        maxStartStep,
        hoverStepIndex - melodyDragClickOffsetSteps);

    if (requestedStartStep == melodyDragStartStep)
        return;

    // Check destination first, ignoring the original note start.
    // This keeps the move monophonic-safe without counting the note against itself.
    if (melodyStepRangeOverlapsExistingNote(
            melodyDragPattern,
            requestedStartStep,
            duration,
            melodyDragOriginalStep))
    {
        return;
    }

    const int note = juce::jlimit(0, 127, melodyDragOriginalNote);
    const int velocity = juce::jlimit(1, 127, melodyDragOriginalVelocity);

    if (melodyDragStartStep >= 0 && melodyDragStartStep < gridStepCount)
        audioProcessor.clearStep(melodyDragPattern, melodyDragStartStep);

    melodyDragStartStep = requestedStartStep;
    melodyDragStartNote = note;

    audioProcessor.setStepValues(
        melodyDragPattern,
        melodyDragStartStep,
        note,
        velocity,
        duration);

    selectedEditPattern = melodyDragPattern;
    selectedStep = melodyDragStartStep;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
    audioProcessor.updateTargetParametersFromStep();

    lastEditedPattern = melodyDragPattern;
    lastEditedStep = melodyDragStartStep;

    updateEditPatternButtonHighlights();
    repaint();
}

'''

cpp = cpp.replace(insert_marker, move_function + insert_marker, 1)


# -----------------------------------------------------------------------------
# 5. Patch mouseDown Alt/Shift logic.
#
# Old behavior:
#   Shift existing note falls through to startMelodyDurationDrag(), then marks
#   ResizeExistingDuration.
#
# New behavior:
#   Shift existing note starts MoveExistingTime.
# -----------------------------------------------------------------------------

old_mouse_down_section = '''            else if (altDown && existingNoteStart >= 0)
            {
                melodyDragPattern = melodyPattern;
                melodyDragStartStep = existingNoteStart;
                melodyDragStartNote = audioProcessor.getStepNote(melodyDragPattern, melodyDragStartStep);

                melodyDragOriginalStep = melodyDragStartStep;
                melodyDragOriginalNote = melodyDragStartNote;
                melodyDragOriginalDuration = juce::jlimit(
                    1,
                    audioProcessor.getGridStepCount(),
                    audioProcessor.getStepDurationSteps(melodyDragPattern, melodyDragStartStep));
                melodyDragOriginalVelocity = juce::jlimit(
                    1,
                    127,
                    audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep));

                isDraggingMelodyDuration = true;
                isDraggingPatternStepEdit = false;
                melodyEditDragMode = shiftDown
                    ? MelodyEditDragMode::MoveExistingPitchAndDuration
                    : MelodyEditDragMode::MoveExistingPitch;

                selectedEditPattern = melodyDragPattern;
                selectedStep = melodyDragStartStep;

                audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
                audioProcessor.updateTargetParametersFromStep();

                updateEditPatternButtonHighlights();
                repaint();
            }
            else
            {
                dragPaintValue = true;
                isDraggingPatternStepEdit = false;

                startMelodyDurationDrag(melodyStepIndex, melodyMidiNote);

                if (shiftDown && existingNoteStart >= 0)
                    melodyEditDragMode = MelodyEditDragMode::ResizeExistingDuration;
            }
'''

new_mouse_down_section = '''            else if ((altDown || shiftDown) && existingNoteStart >= 0)
            {
                melodyDragPattern = melodyPattern;
                melodyDragStartStep = existingNoteStart;
                melodyDragStartNote = audioProcessor.getStepNote(melodyDragPattern, melodyDragStartStep);

                melodyDragOriginalStep = melodyDragStartStep;
                melodyDragOriginalNote = melodyDragStartNote;
                melodyDragOriginalDuration = juce::jlimit(
                    1,
                    audioProcessor.getGridStepCount(),
                    audioProcessor.getStepDurationSteps(melodyDragPattern, melodyDragStartStep));
                melodyDragOriginalVelocity = juce::jlimit(
                    1,
                    127,
                    audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep));

                melodyDragClickOffsetSteps = juce::jlimit(
                    0,
                    juce::jmax(0, melodyDragOriginalDuration - 1),
                    melodyStepIndex - existingNoteStart);

                isDraggingMelodyDuration = true;
                isDraggingPatternStepEdit = false;

                if (altDown)
                {
                    melodyEditDragMode = shiftDown
                        ? MelodyEditDragMode::MoveExistingPitchAndDuration
                        : MelodyEditDragMode::MoveExistingPitch;
                }
                else
                {
                    melodyEditDragMode = MelodyEditDragMode::MoveExistingTime;
                }

                selectedEditPattern = melodyDragPattern;
                selectedStep = melodyDragStartStep;

                audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
                audioProcessor.updateTargetParametersFromStep();

                updateEditPatternButtonHighlights();
                repaint();
            }
            else
            {
                dragPaintValue = true;
                isDraggingPatternStepEdit = false;

                startMelodyDurationDrag(melodyStepIndex, melodyMidiNote);
            }
'''

if old_mouse_down_section not in cpp:
    raise SystemExit("ERROR: Could not patch mouseDown Alt/Shift existing-note section")

cpp = cpp.replace(old_mouse_down_section, new_mouse_down_section, 1)


# -----------------------------------------------------------------------------
# 6. Patch mouseDrag routing.
# -----------------------------------------------------------------------------

old_mouse_drag = '''        if (isDraggingMelodyDuration)
        {
            if (melodyEditDragMode == MelodyEditDragMode::MoveExistingPitch
                || melodyEditDragMode == MelodyEditDragMode::MoveExistingPitchAndDuration)
            {
                updateMelodyDragPitchAtMousePosition(event.getPosition());
                return;
            }

            updateMelodyDragDurationAtMousePosition(event.getPosition());
            return;
        }
'''

new_mouse_drag = '''        if (isDraggingMelodyDuration)
        {
            if (melodyEditDragMode == MelodyEditDragMode::MoveExistingTime)
            {
                updateMelodyDragMoveAtMousePosition(event.getPosition());
                return;
            }

            if (melodyEditDragMode == MelodyEditDragMode::MoveExistingPitch
                || melodyEditDragMode == MelodyEditDragMode::MoveExistingPitchAndDuration)
            {
                updateMelodyDragPitchAtMousePosition(event.getPosition());
                return;
            }

            updateMelodyDragDurationAtMousePosition(event.getPosition());
            return;
        }
'''

if old_mouse_drag not in cpp:
    raise SystemExit("ERROR: Could not patch mouseDrag routing")

cpp = cpp.replace(old_mouse_drag, new_mouse_drag, 1)


# -----------------------------------------------------------------------------
# 7. Reset click offset in mouseDown and mouseUp reset blocks.
# -----------------------------------------------------------------------------

old_reset_a = '''        melodyDragOriginalStep = -1;
        melodyDragOriginalNote = -1;
        melodyDragOriginalDuration = 1;
        melodyDragOriginalVelocity = 100;
'''

new_reset_a = '''        melodyDragOriginalStep = -1;
        melodyDragOriginalNote = -1;
        melodyDragOriginalDuration = 1;
        melodyDragOriginalVelocity = 100;
        melodyDragClickOffsetSteps = 0;
'''

count_a = cpp.count(old_reset_a)
if count_a < 2:
    raise SystemExit(f"ERROR: Expected at least 2 reset blocks, found {count_a}")

cpp = cpp.replace(old_reset_a, new_reset_a)


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.16.0 Patch 4 applied: Shift-drag moves existing Melody notes left/right.")
