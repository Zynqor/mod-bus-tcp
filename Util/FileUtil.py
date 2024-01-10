# -*- coding: UTF-8 -*
import os

class FileUtil:

    # 这是获取目录下所有的文件,包括子文件夹的文件
    @staticmethod
    def list_files(dir_path):
        """
        列出目录下的所有文件
        """
        file_list = []
        for filename in os.listdir(dir_path):
            # 拼接文件路径
            file_path = os.path.join(dir_path, filename)
            if os.path.isfile(file_path):
                # 如果是文件，则将其添加到列表中
                file_list.append(file_path)
            else:
                # 如果是目录，则递归调用该函数
                sub_file_list = FileUtil.list_files(file_path)
                file_list.extend(sub_file_list)
        return file_list

    @staticmethod
    def list_files_and_dirs(dir_path):
        """
        列出指定目录下的一级文件和目录,返回值时文件和目录的数组
        """
        files = []
        dirs = []
        for f in os.listdir(dir_path):
            full_path = os.path.join(dir_path, f)
            if os.path.isfile(full_path):
                files.append(full_path)
            elif os.path.isdir(full_path):
                dirs.append(full_path)
        return files, dirs

