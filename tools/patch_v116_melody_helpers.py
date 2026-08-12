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
# Patch PluginEditor.h
# -----------------------------------------------------------------------------

old_header_block = '''    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
    void setMelodyPaintCellAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void startMelodyDurationDrag(int stepIndex, int midiNote);
    void updateMelodyDragDurationAtMousePosition(juce::Point<int> position);

    void setupButtonCallbacks();
'''

new_header_block = '''    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
    void setMelodyPaintCellAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void startMelodyDurationDrag(int stepIndex, int midiNote);
    void updateMelodyDragDurationAtMousePosition(juce::Point<int> position);

    bool melodyStepRangeOverlapsExistingNote(int patternIndex,
                                             int startStep,
                                             int durationSteps,
                                             int ignoredStepIndex) const;

    int getMaxNonOverlappingMelodyDuration(int patternIndex,
                                           int startStep,
                                           int requestedDuration,
                                           int ignoredStepIndex) const;

    int findMelodyNoteStartAtCell(int patternIndex,
                                  int stepIndex,
                                  int midiNote) const;

    void applyMelodyNoteEditSafely(int patternIndex,
                                   int stepIndex,
                                   int midiNote,
                                   int velocity,
                                   int durationSteps,
                                   int ignoredStepIndex);

    void setupButtonCallbacks();
'''

if old_header_block not in header:
    raise SystemExit("ERROR: Could not find helper declaration insertion point in PluginEditor.h")

header = header.replace(old_header_block, new_header_block, 1)

old_state_block = '''    bool isDraggingMelodyDuration = false;
    int melodyDragPattern = -1;
    int melodyDragStartStep = -1;
    int melodyDragStartNote = -1;

    juce::TextButton editPattern1Button{ "Edit P1" };
'''

new_state_block = '''    enum class MelodyEditDragMode
    {
        None,
        CreateOrResize,
        ResizeExistingDuration,
        MoveExistingPitch,
        MoveExistingPitchAndDuration
    };

    MelodyEditDragMode melodyEditDragMode = MelodyEditDragMode::None;

    bool isDraggingMelodyDuration = false;
    int melodyDragPattern = -1;
    int melodyDragStartStep = -1;
    int melodyDragStartNote = -1;

    int melodyDragOriginalStep = -1;
    int melodyDragOriginalNote = -1;
    int melodyDragOriginalDuration = 1;
    int melodyDragOriginalVelocity = 100;

    juce::TextButton editPattern1Button{ "Edit P1" };
'''

if old_state_block not in header:
    raise SystemExit("ERROR: Could not find melody drag state insertion point in PluginEditor.h")

header = header.replace(old_state_block, new_state_block, 1)

header_path.write_text(header, encoding="utf-8")

# -----------------------------------------------------------------------------
# Patch PluginEditor.cpp
# Insert helper definitions before setMelodyPaintCellValue().
# -----------------------------------------------------------------------------

marker = '''void MidiPatternLauncherAudioProcessorEditor::setMelodyPaintCellValue(
    int stepIndex,
    int midiNote,
    bool shouldHaveNote)
'''

if marker not in cpp:
    raise SystemExit("ERROR: Could not find setMelodyPaintCellValue marker in PluginEditor.cpp")

helper_definitions = r'''
bool MidiPatternLauncherAudioProcessorEditor::melodyStepRangeOverlapsExistingNote(
    int patternIndex,
    int startStep,
    int durationSteps,
    int ignoredStepIndex) const
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    if (patternIndex < 0 || patternIndex >= 3)
        return true;

    if (startStep < 0 || startStep >= gridStepCount)
        return true;

    durationSteps = juce::jlimit(1, gridStepCount, durationSteps);

    const int newStart = startStep;
    const int newEnd = juce::jmin(gridStepCount - 1, startStep + durationSteps - 1);

    for (int stepIndex = 0; stepIndex < gridStepCount; ++stepIndex)
    {
        if (stepIndex == ignoredStepIndex)
            continue;

        if (!audioProcessor.stepHasNote(patternIndex, stepIndex))
            continue;

        const int existingDuration = juce::jlimit(
            1,
            gridStepCount,
            audioProcessor.getStepDurationSteps(patternIndex, stepIndex));

        const int existingStart = stepIndex;
        const int existingEnd = juce::jmin(gridStepCount - 1, existingStart + existingDuration - 1);

        const bool rangesOverlap = newStart <= existingEnd && existingStart <= newEnd;

        if (rangesOverlap)
            return true;
    }

    return false;
}

int MidiPatternLauncherAudioProcessorEditor::getMaxNonOverlappingMelodyDuration(
    int patternIndex,
    int startStep,
    int requestedDuration,
    int ignoredStepIndex) const
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    if (startStep < 0 || startStep >= gridStepCount)
        return 1;

    requestedDuration = juce::jlimit(1, gridStepCount - startStep, requestedDuration);

    int maxDuration = requestedDuration;

    for (int duration = 1; duration <= requestedDuration; ++duration)
    {
        if (melodyStepRangeOverlapsExistingNote(patternIndex, startStep, duration, ignoredStepIndex))
            break;

        maxDuration = duration;
    }

    return juce::jlimit(1, gridStepCount - startStep, maxDuration);
}

int MidiPatternLauncherAudioProcessorEditor::findMelodyNoteStartAtCell(
    int patternIndex,
    int stepIndex,
    int midiNote) const
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    if (patternIndex < 0 || patternIndex >= 3)
        return -1;

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return -1;

    for (int candidateStart = 0; candidateStart < gridStepCount; ++candidateStart)
    {
        if (!audioProcessor.stepHasNote(patternIndex, candidateStart))
            continue;

        const int candidateNote = audioProcessor.getStepNote(patternIndex, candidateStart);

        if (candidateNote != midiNote)
            continue;

        const int candidateDuration = juce::jlimit(
            1,
            gridStepCount,
            audioProcessor.getStepDurationSteps(patternIndex, candidateStart));

        const int candidateEnd = juce::jmin(gridStepCount - 1, candidateStart + candidateDuration - 1);

        if (stepIndex >= candidateStart && stepIndex <= candidateEnd)
            return candidateStart;
    }

    return -1;
}

void MidiPatternLauncherAudioProcessorEditor::applyMelodyNoteEditSafely(
    int patternIndex,
    int stepIndex,
    int midiNote,
    int velocity,
    int durationSteps,
    int ignoredStepIndex)
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    if (patternIndex < 0 || patternIndex >= 3)
        return;

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return;

    midiNote = juce::jlimit(0, 127, midiNote);
    velocity = juce::jlimit(1, 127, velocity);
    durationSteps = juce::jlimit(1, gridStepCount - stepIndex, durationSteps);

    const int safeDuration = getMaxNonOverlappingMelodyDuration(
        patternIndex,
        stepIndex,
        durationSteps,
        ignoredStepIndex);

    if (melodyStepRangeOverlapsExistingNote(patternIndex, stepIndex, safeDuration, ignoredStepIndex))
        return;

    audioProcessor.setStepValues(
        patternIndex,
        stepIndex,
        midiNote,
        velocity,
        safeDuration);

    selectedEditPattern = patternIndex;
    selectedStep = stepIndex;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
    audioProcessor.updateTargetParametersFromStep();

    lastEditedPattern = patternIndex;
    lastEditedStep = stepIndex;

    updateEditPatternButtonHighlights();
    repaint();
}

'''

cpp = cpp.replace(marker, helper_definitions + marker, 1)

cpp_path.write_text(cpp, encoding="utf-8")

print("v1.16.0 Patch 1 applied: Melody edit state and overlap helpers added.")
