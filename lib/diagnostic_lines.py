# This code is an implementation of the ideas from the plugin lsp_lines.nvim
# (https://github.com/Maan2003/lsp_lines.nvim) for the text editor Sublime Text,
# which was originally written in Lua for Neovim. It has been ported and adapted
# to Python in order to work within the Sublime Text plugin ecosystem.
# While it is based on the original implementation, it may have been refactored,
# adapted or simplified to better suit the current use case.

import re
import sublime
from itertools import chain



class DiagnosticLines:
    # rem units are based on character width now. 1 rem = 1 character width
    CSS = '''
        html {{ font-size: {}px; line-height: 0; }}
    '''.format('7.0')
    

    # Change the font-size back since we changed the font-size in the html tag for the rem units
    # I have no idea why windows/linux needs pt instead of px to get the font-size correct...
    body= ''
    if sublime.platform() == 'osx':
        body = '''
            body {{ font-size: {}px; }}
        '''.format('14')
    else:
        body = '''
            body {{ font-size: {}pt; }}
        '''.format('14')

    CSS += body
    CSS += '''
    .diagnostic_line_error {
            color: var(--redish)
        }
    .diagnostic_line_error_background {
            background-color: color(var(--redish) alpha(0.1))
        }
    .diagnostic_line_warning {
            color: var(--yellowish)
        }
    diagnostic_line_warning_background {
            background-color: color(var(--yellowish) alpha(0.1))
        }
    .diagnostic_line_info {
            color: var(--bluish)
        }
    .diagnostic_line_info_background {
            background-color: color(var(--bluish) alpha(0.1))
        }
    .diagnostic_line_hint {
            color: var(--greenish)
        }
    .diagnostic_line_hint_background {
            background-color: color(var(--greenish) alpha(0.1))
        }
    '''
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

    def __init__(self, view: sublime.View, diagnostics, highlight_line_background: bool = False) -> None:
        self._highlight_line_background = highlight_line_background
        # LSP contains Diagnostics as [(DIAGNOSTIC, SUBLIME)]
        # Which means the Sort isn't working in real world
        self.diagnostics = self.sort_diagnostics(diagnostics)
        self.line_stacks = self._generate_line_stacks(self.diagnostics)
        self.blocks = self._generate_diagnostic_blocks(self.line_stacks)
        self._view = view

    def draw(self) -> None:
        global ps
        ps = sublime.PhantomSet(self._view, 'lsp_lines')
        phantoms = [] # Type: List[sublime.Phantom]
        for block in self.blocks:
            content = self.new_generate_region_html_content(block)
            phantoms.append(sublime.Phantom(sublime.Region(32, 32), content, sublime.LAYOUT_BELOW))
        ps.update(phantoms)

    def sort_diagnostics(self, diagnostics):
        return sorted(diagnostics, key=lambda x: (x['range']['start']['line'], x['range']['start']['character']))

    def _generate_line_stacks(self, diagnostics) -> dict:
        # Initialize an empty dictionary to store line stacks
        line_stacks = {}
        # Set the initial values for the previous line number and previous column
        prev_lnum = -1
        prev_col = 0
        # Iterate over the diagnostics
        for _, diagnostic in enumerate(diagnostics):
            # Create an empty list for the current line if it doesn't already exist in the dictionary
            line_stacks.setdefault(diagnostic['range']['start']['line'], [])
            # Get the current stack for the current line
            stack = line_stacks[diagnostic['range']['start']['line']]
            # Check if the diagnostic is on a new line
            if diagnostic['range']['start']['line'] != prev_lnum:
                # If so, add an empty space to the stack
                stack.append(
                    [ self.SPACE, ""]
                )
            elif diagnostic['range']['start']['character'] != prev_col:
                # If not on a new line but on a new column, add spacing to the stack
                # Calculate the spacing by subtracting the previous column from the current column, minus 1 (to account for 0-based index)
                spacing = (diagnostic['range']['start']['character'] - prev_col) - 1
                stack.append(
                    [self.SPACE, " " * spacing]
                )
            else:
                # If the diagnostic is on the same exact spot as the previous one, add an overlap to the stack
                stack.append([self.OVERLAP, diagnostic['severity']])
            
            # Check if the diagnostic message is blank
            if re.match(r'^\s*$', diagnostic['message']):
                # If so, add a blank diagnostic to the stack
                stack.append([self.BLANK, diagnostic])
            else:
                # If not blank, add the diagnostic to the stack
                stack.append([self.DIAGNOSTIC, diagnostic])
        
            # Update the previous line number and column for the next iteration
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
            if diagnostic_type == self.SPACE:
                if multi == 0:
                    left.append({'class': '', 'content': data})
                else:
                    left.append({
                        'class': self.HIGHLIGHTS[diagnostic['severity']],
                        'content': self.SYMBOLS['HORIZONTAL'] * len(data)
                        })
            elif diagnostic_type == self.DIAGNOSTIC:
                if current_index+1 != len(line) and line[current_index+1][0] != self.OVERLAP:
                    left.append(
                        {
                            "class": self.HIGHLIGHTS[data["severity"]],
                            "content": self.SYMBOLS['VERTICAL'],
                        }
                    )
                overlap = False
            elif diagnostic_type == self.BLANK:
                if multi == 0:
                    left.append(
                        {
                            "class": self.HIGHLIGHTS[data["severity"]],
                            "content": self.SYMBOLS['BOTTOM_LEFT'],
                        }
                    )
                else:
                    left.append(
                        {
                            "class": self.HIGHLIGHTS[data["severity"]],
                            "content": self.SYMBOLS['UPSIDE_DOWN_T'],
                        }
                    )
                multi += 1
            elif diagnostic_type == self.OVERLAP:
                overlap = True
            current_index += 1
        return left, overlap, multi

    def _generate_center(self, overlap, multi, diagnostic):
        """
        Generates the center symbol of the diagnostic block
        """
        center_symbol = ''
        if overlap and multi > 0:
            center_symbol = self.SYMBOLS['MIDDLE_CROSS']
        elif overlap:
            center_symbol = self.SYMBOLS['MIDDLE_RIGHT_CENTER']
        elif multi > 0:
            center_symbol = self.SYMBOLS['UPSIDE_DOWN_T']
        else:
            center_symbol = self.SYMBOLS['BOTTOM_LEFT']
        center = [
            {
                "class": self.HIGHLIGHTS[diagnostic['severity']],
                "content": '{0}{1} '.format(center_symbol, self.SYMBOLS['HORIZONTAL']*4),
            }
        ]
        return center

    def _generate_diagnostic_blocks(self, stacks):
        """
        Generates the diagnostic blocks from the given stacks
        """
        blocks = [] 
        print(stacks)
        for key, line in stacks.items():
            virt_lines = {"line": key, "content": []}
            for i, (diagnostic_type, data) in enumerate(reversed(line)):
                if diagnostic_type == self.DIAGNOSTIC:
                    diagnostic = data
                    index = len(line) - 1 - i
                    left, overlap, multi = self._generate_left_side(line, index, diagnostic)
                    center = self._generate_center(overlap, multi, diagnostic)
                    for msg_line in re.findall('([^\n]+)', diagnostic['message']):
                        virt_lines["content"].append(list(chain(left,center,[{'content': msg_line, 'class': self.HIGHLIGHTS[diagnostic['severity']]}])))
                        if overlap:
                            center = [
                                {
                                    "class": self.HIGHLIGHTS[diagnostic['severity']],
                                    "content": self.SYMBOLS['VERTICAL']
                                },
                                {"class": "", "content": "     "},
                            ]
                        else:
                            center = [{"class": "", "content": "      "}]
            blocks.append(virt_lines)
            print(virt_lines)
        return blocks

    def new_generate_region_html_content(self, blocks) -> str:
        html = '<style>{}</style>'.format(self.CSS)
        for line in blocks["content"]:
            for item in line:
                css_class = 'diagnostic_line_{0}'.format(item.get('class'))
                if self._highlight_line_background:
                    css_class += ' diagnostic_line_{0}_background'.format(item.get('class'))
                html = "{0}<span class='{1}' title='{3}'>{2}</span>".format(
                    html,
                    css_class,
                    item.get("content", '').replace(" ", "&nbsp;"),
                    item.get("tooltip", ""),
                )
            html += '<br>'
        return html
