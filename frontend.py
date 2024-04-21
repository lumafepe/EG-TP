from flask import Flask
import sys
from parse import parse
from collections import Counter
from language.issue import IssueType


def errorsTypes(counter,d):
    for k,v in counter.items():
        match k:
            case IssueType.Warning:
                d['NºWarnings']=v
            case IssueType.Info:
                d['NºSugestions']=v
            case IssueType.Error:
                d['NºErrors']=v
    return d

def countersHTML(items):
    s=""
    for k,v in items.items():
        s+=f"""<tr><td>{k}</td><td>{v}</td></tr>"""
    return s
        
    


class Myserver(Flask):
    def __init__(self,name,input_file):
        super().__init__(name)
        self.input_file = input_file
        
    def getHTML(self):
        with open(self.input_file) as f:
            data = f.read()
            linguagem, errors, maxDepth, counters, main_instructions = parse(data)
            c = Counter()
            for i in errors.values():
                for j in i:
                    c[j.valueType]+=1
            values = errorsTypes(c,{})
            values['Max loops depth'] = maxDepth
            values['Main instructions'] = main_instructions
            values.update(counters)
            
                    

        with open('a.html') as f:
            html = f.read().replace(r"{REPLACE}", linguagem.toHTML(errors))
            html = html.replace(r"{REPLACE_2}", countersHTML(values))
            return html



app = Myserver(__name__,sys.argv[1])
    
@app.route('/')
def serve_html():
    return app.getHTML()

if __name__ == '__main__':
    app.run(debug=True,port=80)