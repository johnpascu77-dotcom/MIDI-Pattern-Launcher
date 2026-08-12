from pathlib import Path

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("ERROR: " + message)

# Add editGridHeight inside paint() after gridStepCount.
old_intro = '''void MidiPatternLauncherAudioProcessorEditor::paint(juce::Graphics& g)
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    if (selectedStep >= gridStepCount)
'''

new_intro = '''void MidiPatternLauncherAudioProcessorEditor::paint(juce::Graphics& g)
{
    const int gridStepCount = audioProcessor.getGridStepCount();
    const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;

    if (selectedStep >= gridStepCount)
'''

if old_intro in text:
    text = text.replace(old_intro, new_intro, 1)
else:
    require("const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;" in text,
            "Could not add editGridHeight to paint(); intro block not found")
    print("SKIP: paint() editGridHeight already present")

# Replace the fixed 154 reservation after grid drawing.
old_reserve = '''    bounds.removeFromTop(154);
    bounds.removeFromTop(14);

    //==============================================================================
    // Selected step editor display
'''

new_reserve = '''    bounds.removeFromTop(editGridHeight);
    bounds.removeFromTop(14);

    //==============================================================================
    // Selected step editor display
'''

if old_reserve in text:
    text = text.replace(old_reserve, new_reserve, 1)
else:
    require("bounds.removeFromTop(editGridHeight);" in text,
            "Could not replace paint() fixed 154 grid reservation")
    print("SKIP: paint() grid reservation already uses editGridHeight")

path.write_text(text, encoding="utf-8")

print("v1.15.0 Phase 5b paint overlap fix applied successfully.")
