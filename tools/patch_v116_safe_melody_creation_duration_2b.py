from pathlib import Path
import re

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")


def replace_function(text, signature_start, next_function_start, replacement):
    start = text.find(signature_start)
    if start < 0:
        raise SystemExit(f"ERROR: Could not find function start: {signature_start}")

    end = text.find(next_function_start, start)
    if end < 0:
        raise SystemExit(f"ERROR: Could not find next function marker after: {signature_start}")

    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


# -----------------------------------------------------------------------------
# 1. Replace setMelodyPaintCellValue()
# -----------------------------------------------------------------------------

set_melody_replacement = r'''void MidiPatternLauncherAudioProcessorEditor::setMelodyPaintCellValue(
    int stepIndex,
    int midiNote,
    bool shouldHaveNote)
{
    static constexpr int melodyLowestMidiNote = 48;
    static constexpr int melodyHighestMidiNote = 71;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return;

    if (midiNote < melodyLowestMidiNote || midiNote > melodyHighestMidiNote)
        return;

    const int patternIndex = getDisplayedPattern();

    if (lastEditedPattern == patternIndex && lastEditedStep == stepIndex && shouldHaveNote)
        return;

    const int existingNoteStart = findMelodyNoteStartAtCell(patternIndex, stepIndex, midiNote);

    if (shouldHaveNote)
    {
        // If the user clicks inside an already-sustained note block, select the
        // original note start instead of creating a duplicate hidden note.
        if (existingNoteStart >= 0)
        {
            selectedEditPattern = patternIndex;
            selectedStep = existingNoteStart;

            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            audioProcessor.updateTargetParametersFromStep();

            lastEditedPattern = patternIndex;
            lastEditedStep = existingNoteStart;

            updateEditPatternButtonHighlights();
            repaint();
            return;
        }

        // Full monophonic overlap protection: do not insert a new note if its
        // start cell is already covered by any existing note duration.
        if (melodyStepRangeOverlapsExistingNote(patternIndex, stepIndex, 1, -1))
            return;

        const int velocity = juce::jlimit(1, 127, audioProcessor.getTargetVelocity());
        const int requestedDuration = juce::jlimit(1, gridStepCount - stepIndex, audioProcessor.getTargetDurationSteps());

        applyMelodyNoteEditSafely(
            patternIndex,
            stepIndex,
            midiNote,
            velocity,
            requestedDuration,
            stepIndex);

        return;
    }

    // Erase behavior: if right-clicking anywhere inside a sustained note block,
    // erase the original note start.
    if (existingNoteStart >= 0)
        stepIndex = existingNoteStart;

    selectedEditPattern = patternIndex;
    selectedStep = stepIndex;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
    audioProcessor.clearStep(patternIndex, stepIndex);
    audioProcessor.updateTargetParametersFromStep();

    lastEditedPattern = patternIndex;
    lastEditedStep = stepIndex;

    updateEditPatternButtonHighlights();
    repaint();
}'''

text = replace_function(
    text,
    "void MidiPatternLauncherAudioProcessorEditor::setMelodyPaintCellValue(",
    "void MidiPatternLauncherAudioProcessorEditor::setMelodyPaintCellAtMousePosition(",
    set_melody_replacement
)


# -----------------------------------------------------------------------------
# 2. Replace startMelodyDurationDrag()
# -----------------------------------------------------------------------------

start_drag_replacement = r'''void MidiPatternLauncherAudioProcessorEditor::startMelodyDurationDrag(
    int stepIndex,
    int midiNote)
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return;

    if (midiNote < 0 || midiNote > 127)
        return;

    melodyDragPattern = getDisplayedPattern();

    const int existingNoteStart = findMelodyNoteStartAtCell(melodyDragPattern, stepIndex, midiNote);

    if (existingNoteStart >= 0)
    {
        melodyDragStartStep = existingNoteStart;
        melodyDragStartNote = audioProcessor.getStepNote(melodyDragPattern, existingNoteStart);
    }
    else
    {
        if (melodyStepRangeOverlapsExistingNote(melodyDragPattern, stepIndex, 1, -1))
        {
            melodyEditDragMode = MelodyEditDragMode::None;
            isDraggingMelodyDuration = false;
            return;
        }

        melodyDragStartStep = stepIndex;
        melodyDragStartNote = midiNote;
    }

    melodyDragOriginalStep = melodyDragStartStep;
    melodyDragOriginalNote = melodyDragStartNote;

    melodyDragOriginalDuration = audioProcessor.stepHasNote(melodyDragPattern, melodyDragStartStep)
        ? juce::jlimit(1, gridStepCount, audioProcessor.getStepDurationSteps(melodyDragPattern, melodyDragStartStep))
        : 1;

    melodyDragOriginalVelocity = audioProcessor.stepHasNote(melodyDragPattern, melodyDragStartStep)
        ? juce::jlimit(1, 127, audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep))
        : juce::jlimit(1, 127, audioProcessor.getTargetVelocity());

    isDraggingMelodyDuration = true;
    melodyEditDragMode = MelodyEditDragMode::CreateOrResize;

    selectedEditPattern = melodyDragPattern;
    selectedStep = melodyDragStartStep;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);

    applyMelodyNoteEditSafely(
        melodyDragPattern,
        melodyDragStartStep,
        melodyDragStartNote,
        melodyDragOriginalVelocity,
        juce::jmax(1, melodyDragOriginalDuration),
        melodyDragStartStep);
}'''

text = replace_function(
    text,
    "void MidiPatternLauncherAudioProcessorEditor::startMelodyDurationDrag(",
    "void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragDurationAtMousePosition(",
    start_drag_replacement
)


# -----------------------------------------------------------------------------
# 3. Replace updateMelodyDragDurationAtMousePosition()
# -----------------------------------------------------------------------------

update_drag_replacement = r'''void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragDurationAtMousePosition(
    juce::Point<int> position)
{
    if (!isDraggingMelodyDuration)
        return;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (melodyDragPattern < 0 || melodyDragPattern >= 3)
        return;

    if (melodyDragStartStep < 0 || melodyDragStartStep >= gridStepCount)
        return;

    int hoverStepIndex = -1;
    int hoverMidiNote = -1;

    if (!getMelodyPaintCellAtPosition(position, hoverStepIndex, hoverMidiNote))
        return;

    juce::ignoreUnused(hoverMidiNote);

    const int endStep = juce::jlimit(melodyDragStartStep, gridStepCount - 1, hoverStepIndex);
    const int requestedDuration = juce::jlimit(
        1,
        gridStepCount - melodyDragStartStep,
        endStep - melodyDragStartStep + 1);

    const int velocity = audioProcessor.stepHasNote(melodyDragPattern, melodyDragStartStep)
        ? juce::jlimit(1, 127, audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep))
        : melodyDragOriginalVelocity;

    applyMelodyNoteEditSafely(
        melodyDragPattern,
        melodyDragStartStep,
        melodyDragStartNote,
        velocity,
        requestedDuration,
        melodyDragStartStep);
}'''

text = replace_function(
    text,
    "void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragDurationAtMousePosition(",
    "void MidiPatternLauncherAudioProcessorEditor::updateSelectedStepFromMousePosition(",
    update_drag_replacement
)


# -----------------------------------------------------------------------------
# 4. Patch mouseDown melody reset block.
# -----------------------------------------------------------------------------

old_mouse_down_reset = '''        isDraggingMelodyDuration = false;
        melodyDragPattern = -1;
        melodyDragStartStep = -1;
        melodyDragStartNote = -1;
'''

new_mouse_down_reset = '''        isDraggingMelodyDuration = false;
        melodyEditDragMode = MelodyEditDragMode::None;
        melodyDragPattern = -1;
        melodyDragStartStep = -1;
        melodyDragStartNote = -1;
        melodyDragOriginalStep = -1;
        melodyDragOriginalNote = -1;
        melodyDragOriginalDuration = 1;
        melodyDragOriginalVelocity = 100;
'''

if old_mouse_down_reset not in text:
    raise SystemExit("ERROR: Could not find mouseDown melody reset block")

text = text.replace(old_mouse_down_reset, new_mouse_down_reset, 1)


# -----------------------------------------------------------------------------
# 5. Patch mouseUp reset block.
# -----------------------------------------------------------------------------

old_mouse_up_reset = '''    isDraggingPatternStepEdit = false;
    isDraggingMelodyDuration = false;

    melodyDragPattern = -1;
    melodyDragStartStep = -1;
    melodyDragStartNote = -1;

    lastEditedPattern = -1;
'''

new_mouse_up_reset = '''    isDraggingPatternStepEdit = false;
    isDraggingMelodyDuration = false;
    melodyEditDragMode = MelodyEditDragMode::None;

    melodyDragPattern = -1;
    melodyDragStartStep = -1;
    melodyDragStartNote = -1;
    melodyDragOriginalStep = -1;
    melodyDragOriginalNote = -1;
    melodyDragOriginalDuration = 1;
    melodyDragOriginalVelocity = 100;

    lastEditedPattern = -1;
'''

if old_mouse_up_reset not in text:
    raise SystemExit("ERROR: Could not find mouseUp melody reset block")

text = text.replace(old_mouse_up_reset, new_mouse_up_reset, 1)


path.write_text(text, encoding="utf-8")

print("v1.16.0 Patch 2b applied: Safe Melody creation and duration drag.")
