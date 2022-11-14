import sublime
import sublime_plugin
import functools

from .diagnostics import minimal_diagnostic, compare, _generate_line_stacks, _generate_blocks, generate_region_html_content

class DiagnosticCommand(sublime_plugin.TextCommand):
	def run(self, edit: sublime.Edit) -> None:
		self.view.
		self.view.erase_phantoms("test")
		sorted_l = sorted(minimal_diagnostic, key=functools.cmp_to_key(compare))
		stacks = _generate_line_stacks(sorted_l)
		blocks = _generate_blocks(stacks)
		for region in blocks:
			content = generate_region_html_content(region)
			# print(content)
			self.view.add_phantom("test", sublime.Region(28, 32), content, sublime.LAYOUT_BELOW)
			print(content)


def plugin_loaded():
	print("plugin loaded")

def plugin_unloaded():
	print("plugin unloaded")