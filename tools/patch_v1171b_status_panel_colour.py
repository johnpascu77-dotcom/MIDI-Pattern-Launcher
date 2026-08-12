from pathlib import Path

cpp_path = Path("Source/PluginEditor.cpp")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

cpp = cpp_path.read_text(encoding="utf-8")


old = '''    auto editorBox = bounds.removeFromTop(42);
    g.fillRoundedRectangle(editorBox.toFloat(), 8.0f);
'''

new = '''    auto editorBox = bounds.removeFromTop(42);
    g.setColour(juce::Colour(0xff1c292d));
    g.fillRoundedRectangle(editorBox.toFloat(), 8.0f);
'''

if old not in cpp:
    if '''    auto editorBox = bounds.removeFromTop(42);
    g.setColour(juce::Colour(0xff1c292d));
    g.fillRoundedRectangle(editorBox.toFloat(), 8.0f);
''' in cpp:
        print("Selected status panel colour already appears fixed; continuing.")
    else:
        raise SystemExit("ERROR: Could not find selected status panel fill block")
else:
    cpp = cpp.replace(old, new, 1)

cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.1b applied: selected status panel colour restored.")
