#! /usr/bin/env python
# -*- coding=utf-8 -*-
'''
@Author: xiaobaiTser
@Time  : 2024/2/4 23:30
@File  : Download2.py
'''

import requests
import threading
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

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

        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_num)

        # 线程信息字典
        self.thread_info = {}

    # 获取文件总大小
    def _get_file_size(self):
        response = requests.get(self.url, stream=True)
        if response.status_code == 200:
            return int(response.headers['Content-Length'])
        else:
            raise Exception('文件下载失败')

    # 下载函数
    def _download(self, start, end, thread_id):
        headers = {'Range': f'bytes={start}-{end}'}
        response = requests.get(self.url, headers=headers, stream=True)
        with open(self.file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                self.downloaded_size += len(chunk)
                self._update_thread_info(thread_id, len(chunk))
                if self.callback:
                    self.callback(self.file_size, self.downloaded_size, self.speed, self.get_downloaded_percentage(), self.thread_info)

    # 更新线程信息
    def _update_thread_info(self, thread_id, downloaded_size):
        self.thread_info[thread_id] = {
            'downloaded_size': downloaded_size,
            'speed': downloaded_size / 1024 / 1024,
        }

    # 获取已下载占比
    def get_downloaded_percentage(self):
        return self.downloaded_size / self.file_size * 100

    # 开始下载
    def start(self):
        # 计算每个线程下载的字节数
        block_size = self.file_size // self.thread_num

        # 创建并启动线程
        for i in range(self.thread_num):
            start = i * block_size
            end = (i + 1) * block_size - 1 if i < self.thread_num - 1 else self.file_size - 1
            self.thread_info[i] = {'downloaded_size': 0, 'speed': 0}
            self.thread_pool.submit(self._download, start, end, i)

        # 监控下载速度
        while self.downloaded_size < self.file_size:
            time.sleep(1)
            self.speed = self.downloaded_size / 1024 / 1024

        # 等待所有线程完成
        self.thread_pool.shutdown(wait=True)

        # 下载完成回调
        if self.callback:
            self.callback(self.file_size, self.downloaded_size, self.speed, self.get_downloaded_percentage(), self.thread_info)

# 测试
if __name__ == '__main__':
    url = 'https://download.jetbrains.com/python/pycharm-community-2023.3.2.exe'
    file_path = 'pycharm.exe'

    log_row = 0
    def callback(file_size, downloaded_size, speed, downloaded_percentage, thread_info):
        global log_row

        # print(f'文件总大小: {file_size:.2f} MB\n', end='')
        # print(f'已下载大小: {downloaded_size:.2f} MB ({downloaded_percentage:.2f}%)\n', end='')
        # print(f'下载速度: {speed:.2f} MB/s\n', end='')
        log_data = ''
        for thread_id, info in thread_info.items():
            log_row += 1
            log_data += f'线程 {thread_id + 1}: 已下载 {info["downloaded_size"]} MB, 速度 {info["speed"]} MB/s\n'
        if 0 == log_row % multiprocessing.cpu_count():
            print('', end='\r')
            print(log_data, end='')

    downloader = Downloader(url, file_path, callback=callback)
    downloader.start()