from pathlib import Path

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

# -----------------------------------------------------------------------------
# 1. Patch setMelodyPaintCellValue() to reject note creation inside occupied ranges.
# -----------------------------------------------------------------------------

old = '''    const int patternIndex = getDisplayedPattern();

    if (!shouldHaveNote)
    {
        audioProcessor.clearStep(patternIndex, stepIndex);
'''

new = '''    const int patternIndex = getDisplayedPattern();

    if (shouldHaveNote)
    {
        const int existingNoteStart = findMelodyNoteStartAtCell(patternIndex, stepIndex, midiNote);

        if (existingNoteStart >= 0 && existingNoteStart != stepIndex)
        {
            selectedEditPattern = patternIndex;
            selectedStep = existingNoteStart;
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            audioProcessor.updateTargetParametersFromStep();
            updateEditPatternButtonHighlights();
            repaint();
            return;
        }

        if (existingNoteStart < 0
            && melodyStepRangeOverlapsExistingNote(patternIndex, stepIndex, 1, -1))
        {
            return;
        }
    }

    if (!shouldHaveNote)
    {
        const int existingNoteStart = findMelodyNoteStartAtCell(patternIndex, stepIndex, midiNote);

        if (existingNoteStart >= 0)
        {
            audioProcessor.clearStep(patternIndex, existingNoteStart);

            selectedEditPattern = patternIndex;
            selectedStep = existingNoteStart;
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            audioProcessor.updateTargetParametersFromStep();
            updateEditPatternButtonHighlights();
            repaint();
            return;
        }

        audioProcessor.clearStep(patternIndex, stepIndex);
'''

if old not in text:
    raise SystemExit("ERROR: Could not patch setMelodyPaintCellValue() creation/erase block")

text = text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 2. Patch startMelodyDurationDrag() to reject starts that overlap existing notes.
# -----------------------------------------------------------------------------

old = '''    melodyDragPattern = getDisplayedPattern();
    melodyDragStartStep = stepIndex;
    melodyDragStartNote = midiNote;
    isDraggingMelodyDuration = true;

    selectedEditPattern = melodyDragPattern;
    selectedStep = melodyDragStartStep;
'''

new = '''    melodyDragPattern = getDisplayedPattern();

    const int existingNoteStart = findMelodyNoteStartAtCell(melodyDragPattern, stepIndex, midiNote);

    if (existingNoteStart >= 0 && existingNoteStart != stepIndex)
    {
        melodyDragStartStep = existingNoteStart;
        melodyDragStartNote = audioProcessor.getStepNote(melodyDragPattern, existingNoteStart);
    }
    else
    {
        if (existingNoteStart < 0
            && melodyStepRangeOverlapsExistingNote(melodyDragPattern, stepIndex, 1, -1))
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
'''

if old not in text:
    raise SystemExit("ERROR: Could not patch startMelodyDurationDrag() drag setup block")

text = text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 3. Patch startMelodyDurationDrag() initial setStepValues to use safe helper.
# -----------------------------------------------------------------------------

old = '''    audioProcessor.setStepValues(
        melodyDragPattern,
        melodyDragStartStep,
        melodyDragStartNote,
        velocity,
        1);

    audioProcessor.updateTargetParametersFromStep();

    lastEditedPattern = melodyDragPattern;
    lastEditedStep = melodyDragStartStep;

    updateEditPatternButtonHighlights();
    repaint();
'''

new = '''    applyMelodyNoteEditSafely(
        melodyDragPattern,
        melodyDragStartStep,
        melodyDragStartNote,
        velocity,
        juce::jmax(1, melodyDragOriginalDuration),
        melodyDragStartStep);
'''

if old not in text:
    raise SystemExit("ERROR: Could not patch startMelodyDurationDrag() initial setStepValues block")

text = text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 4. Patch updateMelodyDragDurationAtMousePosition() to clamp against overlaps.
# -----------------------------------------------------------------------------

old = '''    const int endStep = juce::jlimit(melodyDragStartStep, gridStepCount - 1, hoverStepIndex);
    const int duration = juce::jlimit(1, gridStepCount, endStep - melodyDragStartStep + 1);

    const int velocity = juce::jlimit(1, 127, audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep));

    audioProcessor.setStepValues(
        melodyDragPattern,
        melodyDragStartStep,
        melodyDragStartNote,
        velocity,
        duration);

    selectedEditPattern = melodyDragPattern;
    selectedStep = melodyDragStartStep;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
    audioProcessor.updateTargetParametersFromStep();

    repaint();
'''

new = '''    const int endStep = juce::jlimit(melodyDragStartStep, gridStepCount - 1, hoverStepIndex);
    const int requestedDuration = juce::jlimit(1, gridStepCount - melodyDragStartStep, endStep - melodyDragStartStep + 1);

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
'''

if old not in text:
    raise SystemExit("ERROR: Could not patch updateMelodyDragDurationAtMousePosition() duration block")

text = text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 5. Patch mouseDown reset block to reset melody edit mode/original state.
# -----------------------------------------------------------------------------

old = '''        isDraggingMelodyDuration = false;
        melodyDragPattern = -1;
        melodyDragStartStep = -1;
        melodyDragStartNote = -1;
'''

new = '''        isDraggingMelodyDuration = false;
        melodyEditDragMode = MelodyEditDragMode::None;
        melodyDragPattern = -1;
        melodyDragStartStep = -1;
        melodyDragStartNote = -1;
        melodyDragOriginalStep = -1;
        melodyDragOriginalNote = -1;
        melodyDragOriginalDuration = 1;
        melodyDragOriginalVelocity = 100;
'''

if old not in text:
    raise SystemExit("ERROR: Could not patch mouseDown melody reset block")

text = text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 6. Patch mouseUp reset block to reset melody edit mode/original state.
# -----------------------------------------------------------------------------

old = '''    isDraggingPatternStepEdit = false;
    isDraggingMelodyDuration = false;

    melodyDragPattern = -1;
    melodyDragStartStep = -1;
    melodyDragStartNote = -1;

    lastEditedPattern = -1;
'''

new = '''    isDraggingPatternStepEdit = false;
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

if old not in text:
    raise SystemExit("ERROR: Could not patch mouseUp melody reset block")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("v1.16.0 Patch 2 applied: Safe Melody creation and duration drag.")
