import sublime
import sublime_plugin

from .diagnostics import generate_region_html_content, generate_diagnostic_blocks

minimal_rust = '''fn foo4(x: &[i8], y: i32) {
    x[0] = y + w;
}'''

minimal_diagnostic = [
    {
        "message": "mismatched types\nexpected `i8`, found `i32`",
        "range": {
            "end": {
                "character": 12,
                "line": 2
            },
            "start": {
                "character": 12,
                "line": 2
            }
        },
        "severity": 1
    },
    {
        "message": "cannot find value `w` in this scope\nnot found in this scope",
        "range": {
            "end": {
                "character": 16,
                "line": 2
            },
            "start": {
                "character": 16,
                "line": 2
            }
        },
        "severity": 1
    },
    {
        "message": "expected due to the type of this binding",
        "range": {
            "end": {
                "character": 5,
                "line": 2
            },
            "start": {
                "character": 5,
                "line": 2
            }
        },
        "severity": 4
    }
]

class DiagnosticCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit) -> None:
        global ps
        ps = sublime.PhantomSet(self.view, 'lsp_lines')

        self.view.erase(edit, sublime.Region(0, len(minimal_rust)))
        self.view.insert(edit, 0, minimal_rust)

        blocks = generate_diagnostic_blocks(minimal_diagnostic)
        make_phantom = [] # Type: List[sublime.Phantom]
        for region in blocks:
            a = generate_region_html_content(region)
            make_phantom.append(sublime.Phantom(sublime.Region(28, 28), a, sublime.LAYOUT_BELOW))
        ps.update(make_phantom)


def plugin_loaded():
	print("plugin loaded")

def plugin_unloaded():
	print("plugin unloaded")