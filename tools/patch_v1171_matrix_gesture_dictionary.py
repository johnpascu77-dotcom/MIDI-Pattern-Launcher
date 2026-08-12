from pathlib import Path

cpp_path = Path("Source/PluginEditor.cpp")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

cpp = cpp_path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Update version text
# -----------------------------------------------------------------------------

old_version = '"v1.15.0 - Melody Paint Mode"'
new_version = '"v1.17.1 - Matrix Gesture Editing"'

if old_version in cpp:
    cpp = cpp.replace(old_version, new_version, 1)
elif new_version in cpp:
    print("Version text already appears updated; continuing.")
else:
    raise SystemExit("ERROR: Could not find version text to update")


# -----------------------------------------------------------------------------
# 2. Insert Matrix-only gesture dictionary before selected-step status panel.
#
# Robust marker: auto editorBox = bounds.removeFromTop(42);
# -----------------------------------------------------------------------------

marker = '''    auto editorBox = bounds.removeFromTop(42);
'''

dictionary_code = r'''    if (!audioProcessor.isMelodyPaintMode())
    {
        auto dictionaryArea = getPatternMatrixArea();

        const int rowHeight = 64;
        const int rowGap = 8;

        const int dictionaryTop = dictionaryArea.getY() + (3 * rowHeight) + (2 * rowGap) + 18;
        const int availableHeight = dictionaryArea.getBottom() - dictionaryTop - 6;
        const int dictionaryHeight = juce::jlimit(72, 108, availableHeight);

        auto dictionaryBox = juce::Rectangle<int>(
            dictionaryArea.getX(),
            dictionaryTop,
            dictionaryArea.getWidth(),
            dictionaryHeight).reduced(2, 0);

        if (dictionaryBox.getHeight() > 64)
        {
            g.setColour(juce::Colour(0xff1c292d).withAlpha(0.92f));
            g.fillRoundedRectangle(dictionaryBox.toFloat(), 8.0f);

            g.setColour(juce::Colour(0xff3b5056));
            g.drawRoundedRectangle(dictionaryBox.toFloat(), 8.0f, 1.0f);

            auto textBox = dictionaryBox.reduced(14, 8);

            g.setFont(juce::Font(13.0f, juce::Font::bold));
            g.setColour(juce::Colour(0xffcfe8ef));
            g.drawFittedText("Gesture Dictionary",
                textBox.removeFromTop(18),
                juce::Justification::centredLeft,
                1);

            g.setFont(12.0f);
            g.setColour(juce::Colour(0xffedf6f8));

            g.drawFittedText(
                "Matrix: Left drag paint+pitch  |  Right drag erase  |  Alt drag pitch existing only",
                textBox.removeFromTop(17),
                juce::Justification::centredLeft,
                1);

            g.drawFittedText(
                "Matrix: Ctrl drag velocity refine  |  Ctrl+Shift velocity paint  |  Shift drag move step",
                textBox.removeFromTop(17),
                juce::Justification::centredLeft,
                1);

            g.setColour(juce::Colour(0xffb8cbd0));

            g.drawFittedText(
                "Melody: Left empty create/length  |  Right note erase  |  Shift note move",
                textBox.removeFromTop(17),
                juce::Justification::centredLeft,
                1);

            g.drawFittedText(
                "Melody: Alt note pitch  |  Alt+Shift pitch+length  |  Ctrl note velocity",
                textBox.removeFromTop(17),
                juce::Justification::centredLeft,
                1);
        }
    }

'''

if "Gesture Dictionary" in cpp:
    print("Gesture dictionary already appears inserted; continuing.")
else:
    if marker not in cpp:
        raise SystemExit("ERROR: Could not find editorBox insertion marker")

    cpp = cpp.replace(marker, dictionary_code + marker, 1)


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.1 applied: Matrix-only gesture dictionary and version text update.")
