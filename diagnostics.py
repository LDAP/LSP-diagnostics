
import re
from LSP.plugin.core.typing import List, Dict, Union


HIGHLIGHTS = {
    1: "error",
    2: "warning",
    3: "info",
    4: "hint",
}
BOTTOM_LEFT = '└'
UPSIDE_DOWN_T = '┴'
MIDDLE_CROSS = '┼'
MIDDLE_RIGHT_CENTER = '├'
VERTICAL = '│'
HORIZONTAL = '─'

SPACE = "space"
DIAGNOSTIC = "diagnostic"
OVERLAP = "overlap"
BLANK = "blank"

CSS_STYLE = '''

.error {
    color: var(--redish);
    background-color: transparent;
}
.warning {
    color: var(--orangish);
    background-color: transparent;
}
.info {
    color: var(--cyanish);
    background-color: transparent;
}
.hint {
    color: var(--greenish);
    background-color: transparent;
}
'''

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


def _generate_blocks(stacks):
    blocks = []
    for key, line in stacks.items():
        virt_lines = {"line": key, "content": []}
        # Iterate List Backward
        index = len(line)-1
        # for item in reversed(line):
        # print(index)
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
                            [ "│", HIGHLIGHTS[diagnostic['severity']] ], [ "     ", "" ]
                        ]
                    else:
                        center = [
                                [ "      ", "" ]
                            ]
                        
            index -= 1   
        blocks.append(virt_lines)
    return blocks
     
def generate_region_content(blocks: List[List[str, str]]) -> str:
    content = ""
    for line in blocks['content']:
        for struct in line:
            content = '{0}{1}'.format(content, struct[0])
        content = '{0}\n'.format(content)
    return content


def test_block_generation(content_start, content_end, data)-> str:
    content = content_start
    for block in data:
        for line in block['content']:
            for struct in line:
                content = '{0}{1}'.format(content, struct[0])
            content = '{0}\n'.format(content)
    content = '{0}{1}'.format(content, content_end)
    return content


def generate_region_html_content(blocks: List[List[str, str]]) -> str:
    block = '<style>' + CSS_STYLE + '</style>'
    for line in blocks['content']:
        for struct in line:
            content = struct[0].replace(" ", "&nbsp;")
            if struct[1] != "":
                block = '{0}<span class="{1}">{2}</span>'.format(block, struct[1] + ' left-border', content)
            else:
                block = '{0}<span class="space">{1}</span>'.format(block, content)
        block = '{0}<br>'.format(block)
    return block + '</span>'