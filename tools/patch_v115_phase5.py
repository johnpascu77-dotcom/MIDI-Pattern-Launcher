from pathlib import Path

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("ERROR: " + message)

def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"Expected exactly one match for {label}, found {count}")
    return text.replace(old, new, 1)

# =============================================================================
# 1. Make getPatternMatrixArea() return a taller rectangle in Melody mode.

old_get_area = '''juce::Rectangle<int> MidiPatternLauncherAudioProcessorEditor::getPatternMatrixArea() const
{
    auto bounds = getLocalBounds().reduced(24);

    bounds.removeFromTop(32);   // title/version row
    bounds.removeFromTop(24);   // compact status row
    bounds.removeFromTop(14);
    bounds.removeFromTop(24);   // matrix title
    bounds.removeFromTop(8);

    return bounds.removeFromTop(154);
}
'''

new_get_area = '''juce::Rectangle<int> MidiPatternLauncherAudioProcessorEditor::getPatternMatrixArea() const
{
    auto bounds = getLocalBounds().reduced(24);

    bounds.removeFromTop(32);   // title/version row
    bounds.removeFromTop(24);   // compact status row
    bounds.removeFromTop(14);
    bounds.removeFromTop(24);   // matrix title
    bounds.removeFromTop(8);

    const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;

    return bounds.removeFromTop(editGridHeight);
}
'''

if old_get_area in text:
    text = replace_once(text, old_get_area, new_get_area, "getPatternMatrixArea dynamic grid height")
else:
    require("const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;" in text,
            "getPatternMatrixArea block not found and not already patched")
    print("SKIP: getPatternMatrixArea already appears patched")

# =============================================================================
# 2. Make resized() reserve the same taller vertical space for Melody mode.

old_resized_line = '''    bounds.removeFromTop(154);  // matrix area
'''

new_resized_line = '''    const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;
    bounds.removeFromTop(editGridHeight);  // matrix/melody area
'''

if old_resized_line in text:
    text = replace_once(text, old_resized_line, new_resized_line, "resized dynamic grid height")
else:
    require("bounds.removeFromTop(editGridHeight);  // matrix/melody area" in text,
            "resized matrix area line not found and not already patched")
    print("SKIP: resized already appears patched")

# =============================================================================
# 3. Make paint() reserve the same taller vertical space if it still has a fixed
#    bounds.removeFromTop(154) after the grid drawing.
#
# We only replace the first remaining exact commentless pattern if present.
# The getPatternMatrixArea() instance has already been replaced above.

old_paint_line = '''    bounds.removeFromTop(154);
    bounds.removeFromTop(14);
    bounds.removeFromTop(62);   // selected step display
'''

new_paint_line = '''    bounds.removeFromTop(editGridHeight);
    bounds.removeFromTop(14);
    bounds.removeFromTop(62);   // selected step display
'''

if old_paint_line in text:
    text = replace_once(text, old_paint_line, new_paint_line, "paint dynamic grid height")
else:
    print("SKIP: paint fixed grid-height block not found; this may be okay")

path.write_text(text, encoding="utf-8")

print("v1.15.0 Phase 5 melody layout patch applied successfully.")
