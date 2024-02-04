#! /usr/bin/env python
# -*- coding=utf-8 -*-
'''
@Author: xiaobaiTser
@Time  : 2024/2/4 22:50
@File  : Download.py
'''
import requests
import threading
import multiprocessing
import time

# 定义下载器类
class Downloader:

    def __init__(self, url, file_path, thread_num=multiprocessing.cpu_count(), callback=None):
        self.url = url
        self.file_path = file_path
        self.thread_num = thread_num
        self.callback = callback

        # 文件总大小
        self.file_size = self._get_file_size()

        # 已下载大小
        self.downloaded_size = 0

        # 下载速度
        self.speed = 0

        # 线程列表
        self.threads = []

    # 获取文件总大小
    def _get_file_size(self):
        response = requests.get(self.url, stream=True)
        if response.status_code == 200:
            return int(response.headers['Content-Length'])
        else:
            raise Exception('文件下载失败')

    # 下载函数
    def _download(self, start, end):
        headers = {'Range': f'bytes={start}-{end}'}
        response = requests.get(self.url, headers=headers, stream=True)
        with open(self.file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                self.downloaded_size += len(chunk)
                if self.callback:
                    self.callback(self.downloaded_size, self.speed)

    # 开始下载
    def start(self):
        # 计算每个线程下载的字节数
        block_size = self.file_size // self.thread_num

        # 创建并启动线程
        for i in range(self.thread_num):
            start = i * block_size
            end = (i + 1) * block_size - 1 if i < self.thread_num - 1 else self.file_size - 1
            thread = threading.Thread(target=self._download, args=(start, end))
            thread.start()
            self.threads.append(thread)

        # 监控下载速度
        while self.downloaded_size < self.file_size:
            time.sleep(1)
            self.speed = self.downloaded_size / 1024 / 1024

        # 等待所有线程完成
        for thread in self.threads:
            thread.join()

        # 下载完成回调
        if self.callback:
            self.callback(self.file_size, self.speed)

# 测试
if __name__ == '__main__':
    url = 'https://download.jetbrains.com/python/pycharm-community-2023.3.2.exe'
    file_path = 'pycharm.exe'

    def callback(downloaded_size, speed):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        download_unit_index = 0
        speed_unit_index = 0
        while downloaded_size >= 1024:
            downloaded_size /= 1024
            download_unit_index += 1
        while speed >= 1024:
            speed /= 1024
            speed_unit_index += 1
        print('', end='\r')
        print(f'已下载: {downloaded_size:.2f} {units[download_unit_index]}, 速度: {speed:.2f} {units[speed_unit_index]}/s', end='')

    downloader = Downloader(url, file_path, callback=callback)
    downloader.start()
