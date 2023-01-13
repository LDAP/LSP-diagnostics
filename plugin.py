
import sublime
import sublime_plugin

from .lib.diagnostic_lines import DiagnosticLines

minimal_rust = '''fn foo4(x: &[i8], y: i32) {
    x[0] = y + w;
}'''

minimal_diagnostic = [
    ({
            "message": "Overlap testing with\nmultiple lines",
            "range": {
                "end": {
                    "character": 12,
                    "line": 1
                },
                "start": {
                    "character": 12,
                    "line": 1
                }
            },
            "severity": 1
        }, ''),
    ({
            "message": "mismatched types\nexpected `i8`, found `i32`",
            "range": {
                "end": {
                    "character": 12,
                    "line": 1
                },
                "start": {
                    "character": 12,
                    "line": 1
                }
            },
            "severity": 1
        }, ''),
    ({
            "message": "cannot find value `w` in this scope\nnot found in this scope\ncheck passed variable for correctness",
            "range": {
                "end": {
                    "character": 16,
                    "line": 1
                },
                "start": {
                    "character": 16,
                    "line": 1
                }
            },
            "severity": 1
        }, ''),
    ({
            "message": "expected due to the type of this binding",
            "range": {
                "end": {
                    "character": 5,
                    "line": 1
                },
                "start": {
                    "character": 5,
                    "line": 1
                }
            },
            "severity": 4
        }, ''),
    ({
            "message": "unexpected `}` closing brace",
            "range": {
                "end": {
                    "character": 2,
                    "line": 2
                },
                "start": {
                    "character": 2,
                    "line": 2
                }
            },
            "severity": 1
        }, '')
]

class DiagnosticCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit) -> None:
        global ps
        ps = sublime.PhantomSet(self.view, 'lsp_lines')

        self.view.erase(edit, sublime.Region(0, len(minimal_rust)))
        self.view.insert(edit, 0, minimal_rust)
        diagnostic_lines = DiagnosticLines(self.view, minimal_diagnostic, True)
        diagnostic_lines.draw()


def plugin_loaded():
	print("plugin loaded")

def plugin_unloaded():
	print("plugin unloaded")
