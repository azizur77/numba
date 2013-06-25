# -*- coding: UTF-8 -*-

"""
HTML annotation rendering. Heavily based on Cython/Compiler/Annotate.py
"""

from __future__ import print_function, division, absolute_import

import sys
import cgi
import os
import re
from numba.lexing import lex_source
from .annotate import format_annotations, groupdict, A_c_api
from .step import Template

css = u"""
<style type="text/css">

body { font-family: courier; font-size: 12; }

.code  { font-size: 9; color: #444444; display: none; margin-left: 20px; }
.py_c_api  { color: red; }
.py_macro_api  { color: #FF7000; }
.pyx_c_api  { color: #FF3000; }

.error_goto  { color: #FFA000; }

.tag  {  }

.coerce  { color: #008000; border: 1px dotted #008000 }

.py_attr { color: #FF0000; font-weight: bold; }
.c_attr  { color: #0000FF; }

.py_call { color: #FF0000; font-weight: bold; }
.c_call  { color: #0000FF; }

.line { margin: 0em }

</style>
"""

script = u"""
<script>
function toggleDiv(id) {
    theDiv = document.getElementById(id);
    if (theDiv.style.display == 'none') theDiv.style.display = 'block';
    else theDiv.style.display = 'none';
}
</script>
"""

head = u"""
<!-- Generated by Numba %s -->\

<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />

{css}
{script}

</head>
"""

def get_linecolor(annotations):
    adict = groupdict(annotations, "type")
    (_, count), = adict.get(A_c_api, [(A_c_api, 0)])
    score = 5 * count
    return u"FFFF%02x" % int(255/(1+score/10.0))

def render_lines(py_source, llvm_intermediate, emit):
    for lineno, line in sorted(py_source.linemap.iteritems()):
        color = get_linecolor(py_source.annotations.get(lineno, []))
        emit(u"<pre class='line' style='background-color: #%s' "
             u"onclick='toggleDiv(\"line%s\")'>\n" % (color, lineno))

        emit(u" %d: " % lineno)
        # emit(lex_source(line, "python", "html") + u"\n")
        emit(cgi.escape(line) + u"\n")
        emit(u'</pre>\n')

        llvm_lines = [llvm_intermediate.source.linemap[llineno]
                          for llineno in llvm_intermediate.linenomap[lineno]]
        emit(u"<pre id='line%s' class='code' "
             u"style='background-color: #%s'>\n%s</pre>\n" %
                (lineno, color, lex_source(u"\n".join(llvm_lines), "llvm", "html")))

def render(annotation_blocks, emit=sys.stdout.write,
           intermediate_names=(), inline=True):
    """
    Render a Program as html.
    """
    #emit(head.format(css=css, script=script))
    #emit(u"<body>")
    #irs = groupdict(program.intermediates, "name")
    #llvm_intermediate, = irs["llvm"]
    #render_lines(program.python_source, llvm_intermediate, emit)
    #emit(u"</body></html>")

    root = os.path.join(os.path.dirname(__file__))
    if inline:
        templatefile = os.path.join(root, 'annotate_inline_template.html')
    else:
        templatefile = os.path.join(root, 'annotate_template.html')

    with open(templatefile, 'r') as f:
        template = f.read()

    py_c_api = re.compile(u'(Py[A-Z][a-z]+_[A-Z][a-z][A-Za-z_]+)\(')

    data = {'blocks': []}

    for block in annotation_blocks:
        python_source = block['python_source']
        intermediates = block['intermediates']
        data['blocks'].append({'lines':[]})

        for num, source in sorted(python_source.linemap.items()):

            types = {}
            if num in python_source.annotations.keys():
                for a in python_source.annotations[num]:
                    if a.type == 'Types':
                        name = a.value[0]
                        type = a.value[1]
                        types[name] = type
            
            types_str = ','.join(name + ':' + type for name, type in types.items())

            python_calls = 0
            llvm_nums = intermediates[0].linenomap[num]
            llvm_ir = ''
            for llvm_num in llvm_nums:
                ir = intermediates[0].source.linemap[llvm_num]
                if re.search(py_c_api, ir):
                    python_calls += 1
                llvm_ir += ir + '<br/>'

            if python_calls > 4:
                level = 4
            else:
                level = python_calls

            if num == python_source.linemap.keys()[0]:
                firstlastline = 'firstline'
            elif num == python_source.linemap.keys()[-1]:
                firstlastline = 'lastline'
            else:
                firstlastline = 'innerline'
           
            data['blocks'][-1]['func_call'] = block['func_call']
            data['blocks'][-1]['func_call_filename'] = block['func_call_filename']
            data['blocks'][-1]['func_call_lineno'] = block['func_call_lineno']
            data['blocks'][-1]['lines'].append({'num':num,
                                  'python_source':source,
                                  'llvm_source':llvm_ir,
                                  'colorlevel':level,
                                  'types':types_str,
                                  'firstlastline':firstlastline})

    html = Template(template).expand(data)

    emit(html)