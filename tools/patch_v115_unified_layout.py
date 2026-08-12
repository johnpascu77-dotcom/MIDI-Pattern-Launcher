from pathlib import Path
import re

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

old = "const int editGridHeight = audioProcessor.isMelodyPaintMode() ? 330 : 154;"
new = "const int editGridHeight = 330;"

count = text.count(old)

if count == 0:
    raise SystemExit("ERROR: Did not find dynamic editGridHeight expression")

text = text.replace(old, new)

# Also fix the known remaining hardcoded paint reservation if still present.
paint_start = text.find("void MidiPatternLauncherAudioProcessorEditor::paint")
if paint_start < 0:
    raise SystemExit("ERROR: paint() not found")

resized_start = text.find("void MidiPatternLauncherAudioProcessorEditor::resized", paint_start)
if resized_start < 0:
    raise SystemExit("ERROR: resized() not found after paint()")

paint = text[paint_start:resized_start]

marker = "    // Selected step editor display"
marker_index = paint.find(marker)

if marker_index >= 0:
    before_marker = paint[:marker_index]
    after_marker = paint[marker_index:]

    old_line = "    bounds.removeFromTop(154);"
    last_fixed_index = before_marker.rfind(old_line)

    if last_fixed_index >= 0:
        before_marker = (
            before_marker[:last_fixed_index]
            + "    bounds.removeFromTop(editGridHeight);"
            + before_marker[last_fixed_index + len(old_line):]
        )
        paint = before_marker + after_marker
        text = text[:paint_start] + paint + text[resized_start:]
        print("Fixed remaining paint() hardcoded 154 reservation.")
    else:
        print("No remaining paint() hardcoded 154 before selected-step display.")
else:
    print("WARNING: selected-step marker not found in paint(); skipped hardcoded reservation fix.")

path.write_text(text, encoding="utf-8")

print(f"Replaced {count} dynamic editGridHeight declarations with constant 330.")
print("v1.15.0 unified Matrix/Melody layout patch applied successfully.")
