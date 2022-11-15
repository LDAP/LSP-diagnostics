
import re
import functools
from LSP.plugin.core.typing import List, Dict, Union


HIGHLIGHTS = {
    1: "error",
    2: "warning",
    3: "info",
    4: "hint",
} # Type: Dict[int, str]

COLORS = {
    "error": "var(--redish)",
    "warning": "var(--yellowish)",
    "info": "var(--blueish)",
    "hint": "var(--greenish)",
    "": "transparent",
} # Type: Dict[str, str]

BOTTOM_LEFT = '└' # Type: Literal['└']
UPSIDE_DOWN_T = '┴' # Type: Literal['┴']
MIDDLE_CROSS = '┼' # Type: Literal['┼']
MIDDLE_RIGHT_CENTER = '├' # Type: Literal['├']
VERTICAL = '│' # Type: Literal['│']
HORIZONTAL = '─' # Type: Literal['─']

SPACE = "space" # Type: Literal['space']
DIAGNOSTIC = "diagnostic" # Type: Literal['diagnostic']
OVERLAP = "overlap" # Type: Literal['overlap']
BLANK = "blank" # Type: Literal['blank']

def sort_diagnostics(diagnostics: List):
    return sorted(diagnostics, key=functools.cmp_to_key(compare))


def compare(x, y):
    if x['range']['start']['line'] != y['range']['start']['line']:
        return -1 if x['range']['start']['line'] < y['range']['start']['line'] else 1
    else:
        return -1 if x['range']['start']['character'] < y['range']['start']['character'] else 1

def _generate_line_stacks(diagnostics: Union[List, None] = None) -> Union[Dict, None]:
    if diagnostics == None:
        return None
    
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

def generate_diagnostic_blocks(diagnostics) -> List[List[str, str]]:
    sorted_diags = sort_diagnostics(diagnostics)
    stacks = _generate_line_stacks(sorted_diags)
    blocks = [] # Type: List[List[str, str]]
    for key, line in stacks.items():
        virt_lines = {"line": key, "content": []}
        # Iterate List Backward
        index = len(line)-1
        while index > -1:
            if line[index][0] == DIAGNOSTIC:
                diagnostic = line[index][1]
                left = []
                overlap = False
                multi = 0
                i = 0
                while i < index:
                    type = line[i][0]
                    data = line[i][1]
                    if type == SPACE:
                        if multi == 0:
                            left.append([data, ""])
                        else:
                            left.append(["-" * len(data), HIGHLIGHTS[diagnostic['severity']]])
                    elif type == DIAGNOSTIC:
                        if i+1 != len(line) and line[i+1][0] != OVERLAP:
                            left.append([VERTICAL, HIGHLIGHTS[data['severity']]])
                        overlap = False
                    elif type == BLANK:
                        if multi == 0:
                            left.append([BOTTOM_LEFT, HIGHLIGHTS[data['severity']]])
                        else:
                            left.append([UPSIDE_DOWN_T, HIGHLIGHTS[data['severity']]])
                        multi += 1
                    elif type == OVERLAP:
                        overlap = True
                    i += 1
                
                center_symbol = ""
                if overlap and multi > 0:
                    center_symbol = MIDDLE_CROSS
                elif overlap:
                    center_symbol = MIDDLE_RIGHT_CENTER
                elif multi > 0:
                    center_symbol = UPSIDE_DOWN_T
                else:
                    center_symbol = BOTTOM_LEFT
                
                center = [
                   [ '{0}──── '.format(center_symbol), HIGHLIGHTS[diagnostic['severity']]]
                ]
                
                for msg_line in re.findall('([^\n]+)', diagnostic['message']):
                    vline = [] # Type: List[Tuple[str, str]]
                    vline.extend(left)
                    vline.extend(center)
                    vline.extend([[msg_line, HIGHLIGHTS[diagnostic['severity']]]])
                    virt_lines["content"].append(vline)
                    
                    if overlap:
                        center = [
                            [ VERTICAL, HIGHLIGHTS[diagnostic['severity']] ], [ "     ", "" ]
                        ]
                    else:
                        center = [
                                [ "      ", "" ]
                            ]
                        
            index -= 1   
        blocks.append(virt_lines)
    return blocks

def generate_region_html_content(blocks: List[List[str, str]]) -> str:
    block = ''
    for line in blocks['content']:
        for text, typ in line:
            content = text.replace(" ", "&nbsp;")
            block = '{0}<span style="color: {1}">{2}</span>'.format(block, COLORS[typ], content)
        block = '{0}<br>'.format(block)
    return block