from flask import Flask
import sys
from parse import parse
from collections import Counter,defaultdict
from language.issue import IssueType
from bs4 import BeautifulSoup



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
        


def editMessages(messages,index):
    isClass = lambda x: x in ["error","sugestion","warning"]
    submessages = messages.find_all("span", class_=isClass)
    outermessages = list(filter(lambda message: message.find_all("span", class_=isClass) ,submessages))
    s=set()
    for message in list(outermessages):
        message['index']=index
        s.add(message.get('id')[0])
        d = editMessages(message,index+1)
        s = s.union(d)
    for message in submessages:
        if message.get('id')[0] not in s:
            message['index']=index
            s.add(message.get('id')[0])
    return s

def join_messages(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    editMessages(soup,0)
    return str(soup)


class Myserver(Flask):
    def __init__(self,name,input_file):
        super().__init__(name)
        self.input_file = input_file
        
    def getHTML(self):
        with open(self.input_file) as f:
            data = f.read()
            linguagem, errors, maxDepth, counters, main_instructions,svg = parse(data)
            c = Counter()
            for i in errors.values():
                for j in i:
                    c[j.valueType]+=1
            values = errorsTypes(c,{})
            values['Max loops depth'] = maxDepth
            values['Main instructions'] = main_instructions
            values.update(counters)
            HTML =linguagem.toHTML(errors)
            
                    

        with open('a.html') as f:
            html = f.read().replace(r"{REPLACE}", join_messages(HTML))
            html = html.replace(r"{REPLACE_2}", countersHTML(values))
            html = html.replace(r"{REPLACE_SVG}", svg)
            return html



app = Myserver(__name__,sys.argv[1])
    
@app.route('/')
def serve_html():
    return app.getHTML()

if __name__ == '__main__':
    app.run(debug=True,port=8080,extra_files=[sys.argv[1],'a.html'])