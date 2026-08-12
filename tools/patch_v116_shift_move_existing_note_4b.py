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
# 1. Make PluginEditor.h changes idempotently.
# -----------------------------------------------------------------------------

if "MoveExistingTime" not in header:
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

if "updateMelodyDragMoveAtMousePosition" not in header:
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

if "melodyDragClickOffsetSteps" not in header:
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
# 2. Insert updateMelodyDragMoveAtMousePosition() in PluginEditor.cpp.
# -----------------------------------------------------------------------------

insert_marker = '''void MidiPatternLauncherAudioProcessorEditor::updateSelectedStepFromMousePosition(juce::Point<int> position)
'''

if insert_marker not in cpp:
    raise SystemExit("ERROR: Could not find insertion marker for move drag function")

if "void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragMoveAtMousePosition(" not in cpp:
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
# 3. Patch mouseDown Alt/Shift existing-note section.
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

if old_mouse_down_section in cpp:
    cpp = cpp.replace(old_mouse_down_section, new_mouse_down_section, 1)
elif "MelodyEditDragMode::MoveExistingTime" in cpp:
    print("mouseDown section already appears patched; continuing.")
else:
    raise SystemExit("ERROR: Could not patch mouseDown Alt/Shift existing-note section")


# -----------------------------------------------------------------------------
# 4. Patch mouseDrag routing.
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

if old_mouse_drag in cpp:
    cpp = cpp.replace(old_mouse_drag, new_mouse_drag, 1)
elif "updateMelodyDragMoveAtMousePosition(event.getPosition())" in cpp:
    print("mouseDrag routing already appears patched; continuing.")
else:
    raise SystemExit("ERROR: Could not patch mouseDrag routing")


# -----------------------------------------------------------------------------
# 5. Add click-offset reset wherever original melody drag reset exists.
# -----------------------------------------------------------------------------

reset_block = '''        melodyDragOriginalStep = -1;
        melodyDragOriginalNote = -1;
        melodyDragOriginalDuration = 1;
        melodyDragOriginalVelocity = 100;
'''

reset_block_with_offset = '''        melodyDragOriginalStep = -1;
        melodyDragOriginalNote = -1;
        melodyDragOriginalDuration = 1;
        melodyDragOriginalVelocity = 100;
        melodyDragClickOffsetSteps = 0;
'''

if reset_block in cpp:
    cpp = cpp.replace(reset_block, reset_block_with_offset)

# Handle mouseUp reset if indentation is 4 spaces instead of 8.
reset_block_4 = '''    melodyDragOriginalStep = -1;
    melodyDragOriginalNote = -1;
    melodyDragOriginalDuration = 1;
    melodyDragOriginalVelocity = 100;
'''

reset_block_4_with_offset = '''    melodyDragOriginalStep = -1;
    melodyDragOriginalNote = -1;
    melodyDragOriginalDuration = 1;
    melodyDragOriginalVelocity = 100;
    melodyDragClickOffsetSteps = 0;
'''

if reset_block_4 in cpp:
    cpp = cpp.replace(reset_block_4, reset_block_4_with_offset)

cpp_path.write_text(cpp, encoding="utf-8")

print("v1.16.0 Patch 4b applied: Shift-drag moves existing Melody notes left/right.")
