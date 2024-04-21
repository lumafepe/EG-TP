import http.server
import socketserver
import webbrowser
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from parse import parse
import threading


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    html_content = None
    
    def __init__(self, *args, **kwargs):
        MyHttpRequestHandler.html_content = kwargs.pop('html_content', None)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.html_content is not None:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(MyHttpRequestHandler.html_content.encode())
        else:
            super().do_GET()

# Function to start the server
def start_server(html_content):
    # Create a server instance
    with socketserver.TCPServer(("", 80), lambda *args, **kwargs: MyHttpRequestHandler(html_content=html_content, *args, **kwargs)) as httpd:
        print("Server started at localhost:80")
        # Open browser to view the page
        webbrowser.open("http://localhost:80")
        # Serve the content indefinitely
        httpd.serve_forever()
    


def getHTML(input_file):
    with open(input_file) as f:
        data = f.read()
        linguagem, errors, maxDepth, counters, main_instructions = parse(data)

    with open('a.html') as f:
        html = f.read().replace(r"{REPLACE}", linguagem.toHTML(errors))
        return html


class MyFileHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.file_path = file_path
        super().__init__()

    def on_modified(self, event):
        print("file")
        if event.src_path == self.file_path:
            with open(self.file_path) as f:
                MyHttpRequestHandler.html_content = getHTML(self.file_path)


def start_server_thread(html_content):
    server_thread = threading.Thread(target=start_server, args=(html_content,))
    server_thread.start()
    return server_thread

def watchdog_thread(input_file):
    event_handler = MyFileHandler(input_file)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()



def main():
    if len(sys.argv) < 2:
        print("Usage: python frontend.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    t = start_server_thread(getHTML(input_file))

    # Start the watchdog thread
    watchdog_thread(input_file)
    
    t.join()

if __name__ == '__main__':
    main()
