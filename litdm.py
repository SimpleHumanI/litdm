#! /usr/bin/env python3

import http.client
import os.path
from sys import argv
import threading

class litdm:
    @staticmethod
    def request(url:str, method:str, headers:dict={}):
        if not (method or url):
            raise Exception ("method or url or both not passed")
        
        full_url = url
        url = http.client.urlsplit(url)
        port = 443 if url.scheme == "https" else 80

        if port == 443:
            httpconn = http.client.HTTPSConnection(host=url.netloc)
        else:
            httpconn = http.client.HTTPConnection(host=url.netloc, port=port)

        httpconn.request(method=method, url=full_url, headers=headers)
        response = httpconn.getresponse()
        return response

    @staticmethod 
    def content_len(url:str=None) -> int:
        req = litdm.request(url, 'HEAD')
        cl = req.getheader('content-length')
        return int(cl)

    def follow_location(url:str):
        while True:
            response = litdm.request(url, 'HEAD')
            if response.headers['location']:
                url = response.headers['location']
            else:
                break
        return url

    @staticmethod
    def human_readable(size_bytes):
        size_bytes = int(size_bytes)
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        while size_bytes >= 1024 and unit_index < len(units) - 1:
            size_bytes /= 1024
            unit_index += 1
        return size_bytes,units[unit_index]

    @staticmethod
    def get_file_content(url:str, headers:dict):
        response = litdm.request(url=url, method='GET', headers=headers)
        file_bytes = response.read()
        return file_bytes 

    @staticmethod
    def request_and_write(th_count:int ,url:str, file_descriptor, start_byte, end_byte):
        start_byte = str(start_byte)
        end_byte   = str(end_byte)
        
        print(f"thread {th_count} started | ", end='')
        print(f"\tfrom {start_byte} to {end_byte}")
        headers = {
                "Range": f"bytes={start_byte}-{end_byte}"
        }

        file_byte = litdm.get_file_content(url, headers=headers)
        file_descriptor.seek(int(start_byte))
        file_descriptor.write(file_byte)
        
        print(f"thread {th_count} done.")
        
    @staticmethod
    def division_file_byte(filesize:int, ndiv:int) -> list:
        """
        example trace code:
        >>> division_file_byte(filesize = 11, ndiv = 2)  --> 11, 2
        --> div_remain = (filesize  % ndiv)              --> 11 % 2  = 1
        --> no_remain  = (filesize  - div_remain)        --> 11 - 1   = 10
        --> divided    = (no_remain / ndiv)              --> 10 / 2 = 5
        byte list = [ index * divided ] + [ div_remain ] --> [ 5, 5, 1 ]

        in this example we divided number 11 to two part + remain
        """
        div_remain = int(filesize % ndiv)
        no_remain = int(filesize - div_remain)
        divided = int(no_remain / ndiv)

        all_file_byte = []
        for i in range(ndiv):
            all_file_byte.append(divided)
        if div_remain > 0:
            all_file_byte.append(div_remain)

        return all_file_byte

    def __init__(self, url: str, filename: str = None, thread_count:int=None):
        self.url = url
        if thread_count:
            self.thread_count = thread_count 
        else:
            self.thread_count = 5
        if filename:
            self.filename = filename
        else:
            sp_url = http.client.urlsplit(self.url)
            self.filename = os.path.basename(sp_url.path)

    def start_threads(self) -> None:
        direct_link = litdm.follow_location(self.url)
        each_thread = []
        byte_count = 0
        filesize = litdm.content_len(direct_link) 
        all_file_part = litdm.division_file_byte(filesize, self.thread_count)

        each_thread1 = []

        file_descriptor = open(self.filename, 'wb')
        th_count = len(all_file_part)

        for each_part in all_file_part:
            th = threading.Thread(target = litdm.request_and_write,
                                        args=(th_count,
                                              direct_link,
                                              file_descriptor,
                                              byte_count,
                                              byte_count + each_part,
                                              )
                                        )
            byte_count += each_part
            each_thread.append(th)
            th_count -= 1
        
        hr_size = litdm.human_readable(filesize)
        print("size      :", int(hr_size[0]), hr_size[1])
        print("file name :", self.filename)
        print()

        for i in range(len(each_thread)):
            each_thread[i].start()

def main(url):
    x = litdm(url=url)

    print("\n-------------------------------------")
    x.start_threads()
    print("-------------------------------------")

if __name__ == "__main__":
    if len(argv) == 2:
        main(argv[1])
    else:
        print(f"Usage: {os.path.basename(argv[0])} [url]")
