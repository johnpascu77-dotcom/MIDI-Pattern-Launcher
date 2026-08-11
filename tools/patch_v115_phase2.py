from pathlib import Path

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("ERROR: " + message)

# Avoid double-applying.
if "Melody Paint / Target Edit" in text and "melodyLowestMidiNote" in text:
    print("SKIP: Phase 2 appears to be already applied.")
    raise SystemExit(0)

# =============================================================================
# 1. Make the title depend on the current editor view mode.

old_title = '''    juce::String matrixTitle;
    matrixTitle << "Pattern Matrix / Target Edit"
        << "    Selected: P" << (displayedPattern + 1)
        << " Step " << (selectedStep + 1);
'''

new_title = '''    juce::String matrixTitle;
    matrixTitle << (audioProcessor.isMelodyPaintMode()
        ? "Melody Paint / Target Edit"
        : "Pattern Matrix / Target Edit")
        << "    Selected: P" << (displayedPattern + 1)
        << " Step " << (selectedStep + 1);
'''

require(text.count(old_title) == 1, f"title block match count was {text.count(old_title)}")
text = text.replace(old_title, new_title, 1)

# =============================================================================
# 2. Wrap the existing Pattern matrix drawing block.
#
# We keep the existing matrix block untouched inside an else branch.
# We insert the Melody Paint display block before it.

start_marker = '''    //==========================================================================
    // Pattern matrix

'''

end_marker = '''    bounds.removeFromTop(154);
    bounds.removeFromTop(14);
'''

start = text.find(start_marker)
end = text.find(end_marker, start)

require(start != -1, "Pattern matrix start marker not found")
require(end != -1, "Pattern matrix end marker not found")

old_matrix_block = text[start:end]

melody_block_prefix = '''    //==========================================================================
    // Pattern matrix / Melody paint grid

    if (audioProcessor.isMelodyPaintMode())
    {
        auto melodyArea = getPatternMatrixArea();

        static constexpr int melodyLowestMidiNote = 48;
        static constexpr int melodyHighestMidiNote = 71;
        static constexpr int melodyNoteCount = melodyHighestMidiNote - melodyLowestMidiNote + 1;

        const int noteLabelWidth = 38;
        const int stepLabelHeight = 16;
        const int stepGap = 3;
        const int noteGap = 1;

        auto noteLabelArea = melodyArea.removeFromLeft(noteLabelWidth);
        juce::ignoreUnused(noteLabelArea);

        auto stepHeaderArea = melodyArea.removeFromTop(stepLabelHeight);
        auto gridArea = melodyArea;

        const int cellWidth = (gridArea.getWidth() - ((gridStepCount - 1) * stepGap)) / gridStepCount;
        const int cellHeight = (gridArea.getHeight() - ((melodyNoteCount - 1) * noteGap)) / melodyNoteCount;

        g.setColour(juce::Colour(0xff1f2d32));
        g.fillRoundedRectangle(gridArea.toFloat(), 6.0f);

        // Step labels
        for (int stepIndex = 0; stepIndex < gridStepCount; ++stepIndex)
        {
            const int x = gridArea.getX() + stepIndex * (cellWidth + stepGap);

            auto stepLabelBox = juce::Rectangle<int>(
                x,
                stepHeaderArea.getY(),
                cellWidth,
                stepHeaderArea.getHeight());

            g.setColour(juce::Colour(0xffcfe8ef));
            g.setFont(10.0f);
            g.drawFittedText(juce::String(stepIndex + 1),
                stepLabelBox,
                juce::Justification::centred,
                1);
        }

        // MIDI note rows: highest note at top, lowest note at bottom.
        for (int noteOffset = 0; noteOffset < melodyNoteCount; ++noteOffset)
        {
            const int midiNote = melodyHighestMidiNote - noteOffset;
            const int y = gridArea.getY() + noteOffset * (cellHeight + noteGap);

            auto noteLabelBox = juce::Rectangle<int>(
                getPatternMatrixArea().getX(),
                y,
                noteLabelWidth - 6,
                cellHeight);

            const bool isReferenceOctaveNote = (midiNote % 12) == 0;

            g.setColour(isReferenceOctaveNote
                ? juce::Colour(0xfff5c542)
                : juce::Colour(0xffcfe8ef));

            g.setFont(isReferenceOctaveNote ? 11.0f : 10.0f);
            g.drawFittedText(juce::String(midiNote),
                noteLabelBox,
                juce::Justification::centredRight,
                1);

            for (int stepIndex = 0; stepIndex < gridStepCount; ++stepIndex)
            {
                const int x = gridArea.getX() + stepIndex * (cellWidth + stepGap);

                auto cellBox = juce::Rectangle<int>(
                    x,
                    y,
                    cellWidth,
                    cellHeight);

                const int loopLength = juce::jmin(audioProcessor.getPatternLoopLength(displayedPattern), gridStepCount);
                const bool isInsideLoop = stepIndex < loopLength;
                const bool stepHasNote = audioProcessor.stepHasNote(displayedPattern, stepIndex);
                const int stepNote = audioProcessor.getStepNote(displayedPattern, stepIndex);
                const bool isNoteCell = stepHasNote && stepNote == midiNote;
                const bool isCurrentStep = activePattern == displayedPattern && currentStep == (stepIndex + 1);
                const bool isSelectedColumn = selectedEditPattern == displayedPattern && selectedStep == stepIndex;

                if (isCurrentStep && isNoteCell)
                    g.setColour(juce::Colour(0xfff5c542));
                else if (isNoteCell)
                    g.setColour(isInsideLoop ? juce::Colour(0xff5aa6b8) : juce::Colour(0xff35545c));
                else if (isCurrentStep)
                    g.setColour(juce::Colour(0xff5a5124));
                else if (isReferenceOctaveNote)
                    g.setColour(isInsideLoop ? juce::Colour(0xff263f45) : juce::Colour(0xff1c292d));
                else
                    g.setColour(isInsideLoop ? juce::Colour(0xff26363b) : juce::Colour(0xff1c292d));

                g.fillRoundedRectangle(cellBox.toFloat(), 2.0f);

                if (isNoteCell)
                {
                    g.setColour(isCurrentStep ? juce::Colours::black : juce::Colours::white);
                    g.drawRoundedRectangle(cellBox.toFloat().reduced(1.0f), 2.0f, 1.0f);
                }
                else
                {
                    g.setColour(juce::Colour(0xff3b5056));
                    g.drawRoundedRectangle(cellBox.toFloat(), 2.0f, 0.5f);
                }

                if (isSelectedColumn && isNoteCell)
                {
                    g.setColour(juce::Colours::white);
                    g.drawRoundedRectangle(cellBox.toFloat().reduced(1.0f), 2.0f, 2.0f);
                }
            }
        }

        g.setColour(juce::Colour(0xffcfe8ef));
        g.setFont(12.0f);

        juce::String melodyInfo;
        melodyInfo << "MIDI notes 48-71    P" << (displayedPattern + 1)
            << "    Grid: " << gridStepCount << " steps";

        g.drawFittedText(melodyInfo,
            getPatternMatrixArea().withTrimmedTop(getPatternMatrixArea().getHeight() - 18),
            juce::Justification::centredRight,
            1);
    }
    else
    {
'''

# Indent the old matrix block by one level, but keep its own marker/comment.
old_matrix_lines = old_matrix_block.splitlines(True)
indented_old_matrix_block = "".join("    " + line if line.strip() else line for line in old_matrix_lines)

new_matrix_block = melody_block_prefix + indented_old_matrix_block + '''    }

'''

text = text[:start] + new_matrix_block + text[end:]

path.write_text(text, encoding="utf-8")

print("v1.15.0 Phase 2 patch applied successfully.")
