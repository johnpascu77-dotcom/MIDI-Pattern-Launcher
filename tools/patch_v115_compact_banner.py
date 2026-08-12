from pathlib import Path

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

# 1. Reduce selected-step display reservation from 62 to 42.
# This appears in paint():
#     auto editorBox = bounds.removeFromTop(62);
#
# and in resized():
#     bounds.removeFromTop(62);   // selected step display

text = text.replace(
    "auto editorBox = bounds.removeFromTop(62);",
    "auto editorBox = bounds.removeFromTop(42);"
)

text = text.replace(
    "bounds.removeFromTop(62);   // selected step display",
    "bounds.removeFromTop(42);   // selected step display"
)

# 2. Convert selected-step editor text from two lines to one line.
# Current block usually has:
#     editorText << "Inv: ..." << "\\n";
#
# Replace only the first intended newline in the selected-step display text.

old = '''    editorText << "Tr: " << transposeTextFromValue(patternTranspose) << "    ";
    editorText << "Rot: " << rotationTextFromValue(patternRotation) << "    ";
    editorText << "Inv: " << inversionTextFromValue(patternInverted) << "\\n";

    if (selectedHasNote)
'''

new = '''    editorText << "Tr: " << transposeTextFromValue(patternTranspose) << "    ";
    editorText << "Rot: " << rotationTextFromValue(patternRotation) << "    ";
    editorText << "Inv: " << inversionTextFromValue(patternInverted) << "    ";

    if (selectedHasNote)
'''

if old in text:
    text = text.replace(old, new, 1)
    print("Converted selected-step display text to one line.")
else:
    print("WARNING: Could not find exact selected-step newline block. Height was still patched.")

path.write_text(text, encoding="utf-8")

print("v1.15.0 compact selected-step banner patch applied successfully.")
