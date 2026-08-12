from pathlib import Path

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("ERROR: " + message)

paint_start = text.find("void MidiPatternLauncherAudioProcessorEditor::paint")
require(paint_start >= 0, "paint() not found")

resized_start = text.find("void MidiPatternLauncherAudioProcessorEditor::resized", paint_start)
require(resized_start > paint_start, "resized() not found after paint()")

paint = text[paint_start:resized_start]

# 1. Ensure editGridHeight is declared inside paint().
if "const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;" not in paint:
    old = "    const int gridStepCount = audioProcessor.getGridStepCount();\n"
    new = '''    const int gridStepCount = audioProcessor.getGridStepCount();
    const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;
'''
    require(old in paint, "Could not find gridStepCount line inside paint()")
    paint = paint.replace(old, new, 1)
    print("Added editGridHeight inside paint()")
else:
    print("paint() already has editGridHeight")

# 2. Find selected-step display block.
marker = "    // Selected step editor display"
marker_index = paint.find(marker)
require(marker_index >= 0, "Selected step editor display marker not found inside paint()")

before_marker = paint[:marker_index]
after_marker = paint[marker_index:]

old_line = "    bounds.removeFromTop(154);"
last_fixed_index = before_marker.rfind(old_line)
require(last_fixed_index >= 0, "Could not find bounds.removeFromTop(154) before selected-step display inside paint()")

before_marker = (
    before_marker[:last_fixed_index]
    + "    bounds.removeFromTop(editGridHeight);"
    + before_marker[last_fixed_index + len(old_line):]
)

paint = before_marker + after_marker

text = text[:paint_start] + paint + text[resized_start:]

path.write_text(text, encoding="utf-8")

print("v1.15.0 Phase 5c robust paint layout fix applied successfully.")
