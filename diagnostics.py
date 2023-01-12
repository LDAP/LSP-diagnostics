# This code is an implementation of the ideas from the plugin lsp_lines.nvim
# (https://github.com/Maan2003/lsp_lines.nvim) for the text editor Sublime Text,
# which was originally written in Lua for Neovim. It has been ported and adapted
# to Python in order to work within the Sublime Text plugin ecosystem.
# While it is based on the original implementation, it may have been refactored,
# adapted or simplified to better suit the current use case.

import re
from itertools import chain
from LSP.plugin.core.typing import List


HIGHLIGHTS = {
    1: "error",
    2: "warning",
    3: "info",
    4: "hint"
} # Type: Dict[int, str]

COLORS = {
    "error": "var(--redish)",
    "warning": "var(--yellowish)",
    "info": "var(--blueish)",
    "hint": "var(--greenish)",
    "": "transparent",
} # Type: Dict[str, str]

SYMBOLS = {
    'BOTTOM_LEFT': '└',
    'UPSIDE_DOWN_T': '┴',
    'MIDDLE_CROSS': '┼',
    'MIDDLE_RIGHT_CENTER': '├',
    'VERTICAL': '│',
    'HORIZONTAL': '─'
} # Type: Dict[str, str]


SPACE = 'space' # Type: Literal['space']
DIAGNOSTIC = 'diagnostic' # Type: Literal['diagnostic']
OVERLAP = 'overlap' # Type: Literal['overlap']
BLANK = 'blank' # Type: Literal['blank']

class DiagnosticLines:
    def __init__(self, diagnostics: List) -> None:
        self.diagnostics = self.sort_diagnostics(diagnostics)
        self.line_stacks = self._generate_line_stacks(self.diagnostics)
        self.blocks = self._generate_diagnostic_blocks(self.line_stacks)

    def sort_diagnostics(self, diagnostics: List) -> List:
        return sorted(diagnostics, key=lambda x: (x['range']['start']['line'], x['range']['start']['character']))

    def _generate_line_stacks(self, diagnostics: List) -> dict:
        line_stacks = {}
        prev_lnum = -1
        prev_col = 0
        for _, diagnostic in enumerate(diagnostics):
            line_stacks.setdefault(diagnostic['range']['start']['line'], [])
            stack = line_stacks[diagnostic['range']['start']['line']]
            if diagnostic['range']['start']['line'] != prev_lnum:
                stack.append(
                    [ SPACE, " " * (diagnostic['range']['start']['character'] - 1)]
                )
            elif diagnostic['range']['start']['character'] != prev_col:
                spacing = (diagnostic['range']['start']['character'] - prev_col) - 1
                stack.append(
                    [SPACE, " " * spacing]
                )
            else:
                stack.append([OVERLAP, diagnostic['severity']])
            
            if re.match("^%s*$", diagnostic['message']):
                stack.append([BLANK, diagnostic])
            else:
                stack.append([DIAGNOSTIC, diagnostic])
        
            prev_lnum = diagnostic['range']['start']['line']
            prev_col = diagnostic['range']['start']['character']
        return line_stacks

    def _generate_left_side(self, line, index, diagnostic):
        """
        Generates the left side of the diagnostic block for a given line
        """
        left = []
        overlap = False
        multi = 0
        current_index = 0
        while current_index < index:
            diagnostic_type = line[current_index][0]
            data = line[current_index][1]
            if diagnostic_type == SPACE:
                if multi == 0:
                    left.append([data, ""])
                else:
                    left.append(["-" * len(data), HIGHLIGHTS[diagnostic['severity']]])
            elif diagnostic_type == DIAGNOSTIC:
                if current_index+1 != len(line) and line[current_index+1][0] != OVERLAP:
                    left.append([SYMBOLS['VERTICAL'], HIGHLIGHTS[data['severity']]])
                overlap = False
            elif diagnostic_type == BLANK:
                if multi == 0:
                    left.append([SYMBOLS['BOTTOM_LEFT'], HIGHLIGHTS[data['severity']]])
                else:
                    left.append([SYMBOLS['UPSIDE_DOWN_T'], HIGHLIGHTS[data['severity']]])
                multi += 1
            elif diagnostic_type == OVERLAP:
                overlap = True
            current_index += 1
        return left, overlap, multi

    def _generate_center(self, overlap, multi, diagnostic):
        """
        Generates the center symbol of the diagnostic block
        """
        center_symbol = ""
        if overlap and multi > 0:
            center_symbol = SYMBOLS['MIDDLE_CROSS']
        elif overlap:
            center_symbol = SYMBOLS['MIDDLE_RIGHT_CENTER']
        elif multi > 0:
            center_symbol = SYMBOLS['UPSIDE_DOWN_T']
        else:
            center_symbol = SYMBOLS['BOTTOM_LEFT']
        center = [['{0}{1} '.format(center_symbol, SYMBOLS['HORIZONTAL']*4), HIGHLIGHTS[diagnostic['severity']]]]
        return center

    def _generate_diagnostic_blocks(self, stacks) -> List[List[str, str]]:
        """
        Generates the diagnostic blocks from the given stacks
        """
        blocks = [] 
        for key, line in stacks.items():
            virt_lines = {"line": key, "content": []}
            for i, (diagnostic_type, data) in enumerate(reversed(line)):
                if diagnostic_type == DIAGNOSTIC:
                    diagnostic = data
                    index = len(line) - 1 - i
                    left, overlap, multi = self._generate_left_side(line, index, diagnostic)
                    center = self._generate_center(overlap, multi, diagnostic)
                    for msg_line in re.findall('([^\n]+)', diagnostic['message']):
                        virt_lines["content"].append(list(chain(left,center,[[msg_line, HIGHLIGHTS[diagnostic['severity']]]])))
                        if overlap:
                            center = [[ SYMBOLS['VERTICAL'], HIGHLIGHTS[diagnostic['severity']] ], ["     ", ""]]
                        else:
                            center = [["      ", ""]]
            blocks.append(virt_lines)
        return blocks

    def generate_region_html_content(self, blocks: List[List[str, str]]) -> str:
        block = ''
        for line in blocks['content']:
            for text, typ in line:
                content = text.replace(" ", "&nbsp;")
                block = '{0}<span style="color: {1};">{2}</span>'.format(block, COLORS[typ], content)
            block += '<br>'
        return block
