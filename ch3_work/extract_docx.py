import zipfile, re, sys, xml.etree.ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def para_text(p):
    parts=[]
    for node in p.iter():
        if node.tag==W+'t':
            parts.append(node.text or '')
        elif node.tag==W+'tab':
            parts.append('\t')
        elif node.tag==W+'br':
            parts.append('\n')
    return ''.join(parts)
def main(path, out):
    z=zipfile.ZipFile(path)
    xml=z.read('word/document.xml')
    root=ET.fromstring(xml)
    body=root.find(W+'body')
    lines=[]
    def walk(el, depth=0):
        for child in el:
            if child.tag==W+'p':
                t=para_text(child).strip()
                lines.append(t)
            elif child.tag==W+'tbl':
                for row in child.findall(W+'tr'):
                    cells=[' '.join(para_text(p).strip() for p in c.findall(W+'p')).strip() for c in row.findall(W+'tc')]
                    lines.append(' | '.join(cells))
            else:
                walk(child, depth+1)
    walk(body)
    with open(out,'w',encoding='utf-8') as f:
        for l in lines:
            f.write(l+'\n')
    print(len(lines),'paragraphs ->',out)
main(sys.argv[1], sys.argv[2])
