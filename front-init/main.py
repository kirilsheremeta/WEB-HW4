from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import datetime
import json
import logging
import mimetypes
import pathlib
import socket
import urllib.parse

BASE_DIR = pathlib.Path()
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
HTTP_PORT = 3000


def send_data_to_socket(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(data, (SERVER_HOST, SERVER_PORT))
    client_socket.close()


def run_socket_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            save_server_data(data)
            print(f'Received data: {data.decode()} from: {address}')
            sock.sendto(data, address)
            print(f'Send data: {data.decode()} to: {address}')

    except KeyboardInterrupt:
        logging.info('Destroy server')
    finally:
        sock.close()


def save_server_data(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        dict_parse = {
            str(datetime.datetime.now()): {key: value for key, value in
                                           [el.split('=') for el in parse_data.split('&')]}}
        with open(FILE_STORAGE, 'r+', encoding='utf-8') as f:
            data_file = json.load(f)
            new_record = {str(datetime.datetime.now()): dict_parse}
            data_file.update(new_record)
            with open(FILE_STORAGE, 'w', encoding='utf-8') as file:
                json.dump(data_file, file, ensure_ascii=False, indent=4)

    except ValueError as err:
        logging.debug(f"for data {parse_data} error: {err}")
    except OSError as err:
        logging.debug(f"Write data {parse_data} error: {err}")


def run_http_server():
    server_address = ('0.0.0.0', HTTP_PORT)
    http = HTTPServer(server_address, HTTPHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        http.server_close()


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        send_data_to_socket(data)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        url_path = urllib.parse.urlparse(self.path)
        match url_path.path:
            case "/":
                self.send_html('index.html')
            case "/message.html":
                self.send_html('message.html')
            case _:
                if pathlib.Path().joinpath(url_path.path[1:]).exists():
                    self.send_static(url_path.path[1:])
                else:
                    self.send_html('error.html', 404)

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        # print(mimetypes.guess_type(filename))
        mime_type = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-Type", mime_type[0])
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()

        with open(filename, "rb") as file:
            self.wfile.write(file.read())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")

    STORAGE_DIR = pathlib.Path().joinpath('storage')
    FILE_STORAGE = STORAGE_DIR.joinpath('data.json')
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'w', encoding='utf-8') as fd:
            json.dump({}, fd, ensure_ascii=False, indent=4)
    th_server = Thread(target=run_http_server)
    th_server.start()

    th_socket = Thread(target=run_socket_server, args=(SERVER_HOST, SERVER_PORT))
    th_socket.start()
