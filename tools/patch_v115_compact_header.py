from pathlib import Path

path = Path("Source/PluginEditor.cpp")

if not path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

text = path.read_text(encoding="utf-8")

replacements = [
    # Shared layout reservations in getPatternMatrixArea() and resized()
    ("bounds.removeFromTop(32);   // title/version row", "bounds.removeFromTop(26);   // title/version row"),
    ("bounds.removeFromTop(24);   // compact status row", "bounds.removeFromTop(18);   // compact status row"),
    ("bounds.removeFromTop(14);", "bounds.removeFromTop(8);"),
    ("bounds.removeFromTop(24);   // matrix title", "bounds.removeFromTop(22);   // matrix title"),
    ("bounds.removeFromTop(8);", "bounds.removeFromTop(4);"),

    # Paint title/status/matrix title rectangles if present with matching removeFromTop calls
    ("bounds.removeFromTop(32)", "bounds.removeFromTop(26)"),
    ("bounds.removeFromTop(24)", "bounds.removeFromTop(22)"),
]

# Do cautious replacements globally. The exact comments help the layout sections;
# the rectangle replacements also compact paint where it draws those rows.
for old, new in replacements:
    if old in text:
        text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("v1.15.0 compact upper header patch applied.")
