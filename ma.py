import csv
import os
from tqdm import tqdm
import pandas as pd
from pandas import Series, DataFrame
import random


class MA(object):

    def __init__(self, file_path_prefix, code, all_n=[5,10], end_date='0000-00-00'):
        self.file_path_prefix = file_path_prefix        # 日线数据文件目录前缀
        self.code = code                                # 股票代码 （可选）
        self.end_date = end_date                        # 最早的日期， 默认无下限
        self.n = 5                                      # 几日的移动平均
        self.all_n = all_n                              # 要求的 MAn 的 n 的取值情况

    def analyze_one(self):
        try:
            df = pd.read_csv(self.file_path_prefix + str(self.code) + '.csv', encoding='gbk')
        except:
            print('文件'+str(self.code) + '.csv 打开失败')
            return False
        for item in self.all_n:
            self.n = item
            column_name = "ma"+str(self.n)
            df[column_name] = ''
            start = 0
            
            # 计算第一个块的均值
            rows = df[start:start+self.n]
            if len(rows) < self.n or rows.values[0][0] < self.end_date:
                break
            flag = True     # 数据是否完整
            block_sum = 0
            for index, row in rows.iterrows():
                if row['最高价'] == 'None' or row['最高价'] == 0 or row['最低价'] == 'None' \
                    or row['最低价'] == 0 or row['收盘价'] == 'None' or row['收盘价'] == 0:
                    flag = False
                if row['收盘价'] != 'None':
                    block_sum += row['收盘价']
            if flag:
                ma = block_sum / self.n
            else:
                ma = 0
            df.loc[start, column_name] = ma

            while True:
                try:
                    new_line_close = df.loc[start+self.n, '收盘价']
                except:
                    break
                if new_line_close == "None" or new_line_close == '0':
                    # 数据不完整
                    block_sum = 0
                else:
                    block_sum = block_sum - df.loc[start, '收盘价'] + new_line_close
                start += 1
                ma = block_sum / self.n
                df.loc[start, column_name] = ma
        
            # 截取块进行枚举， 效率较低
            ####################
            # while True:
            #     # 截取 start ~ start+n行数据
            #     rows = df[start:start+self.n]
            #     if len(rows) < self.n or rows.values[0][0] < self.end_date:
            #         break
            #     flag = True     # 数据是否完整
            #     ma = 0
            #     for index, row in rows.iterrows():
            #         if row['最高价'] == 'None' or row['最高价'] == 0 or row['最低价'] == 'None' \
            #             or row['最低价'] == 0 or row['收盘价'] == 'None' or row['收盘价'] == 0:
            #             flag = False
            #         if row['收盘价'] != 'None':
            #             ma += row['收盘价']
            #     if flag:
            #         ma /= self.n
            #     else:
            #         ma = 0
            #     df.loc[start, column_name] = ma
            #     start += 1
            ####################
            df.to_csv(self.file_path_prefix + str(self.code) + '.csv', index=False, encoding='gbk')

    def analyze_all(self):
        file_list = os.listdir(self.file_path_prefix)
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            print("正在计算%s的MA" % filename)
            self.code = filename[0:6]
            if int(self.code) < 0:
                continue
            self.analyze_one()


if __name__ == '__main__':
    file_path_prefix = 'H:\\sharesDatas\\kline\\'
    # file_path_prefix = 'F:\\files\\sharesDatas\\kline\\'
    ma = MA(file_path_prefix, code='000001')
    ma.analyze_all()
    