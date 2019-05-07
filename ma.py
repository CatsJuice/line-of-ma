import csv
import os
from tqdm import tqdm
import pandas as pd
from pandas import Series, DataFrame
import random

class BuyInfo(object):
    
    def __init__(self, code, buy_arr, sold_arr):
        self.code = code
        self.buy_date = buy_arr[0]
        self.buy_close = buy_arr[2]
        self.sold_date = sold_arr[0]
        self.sold_close = sold_arr[2]
        self.diff = self.sold_close - self.buy_close

    def to_string(self):
        buy_close_ = " "*(6-len(str(self.buy_close))) + str(self.buy_close)
        sold_close_ = " "*(6-len(str(self.sold_close))) + str(self.sold_close)
        diff_ = format(self.diff, '.2f')
        diff_ = " "*(6 - len(diff_)) + diff_
        return "[%s]在%s日买入, 收盘价为%s, %s日卖出, 收盘价为%s, 差价为%s" % (self.code, \
            self.buy_date, buy_close_, self.sold_date, sold_close_, diff_)

class MA(object):

    def __init__(self, file_path_prefix, code, all_n=[5,10], end_date='0000-00-00'):
        self.file_path_prefix = file_path_prefix        # 日线数据文件目录前缀
        self.code = code                                # 股票代码 （可选）
        self.end_date = end_date                        # 最早的日期， 默认无下限
        self.n = 5                                      # 几日的移动平均
        self.all_n = all_n                              # 要求的 MAn 的 n 的取值情况
        self.all_buy_res = []

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

            date_is_end = False
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
                if df.loc[start, '日期'] < self.end_date:
                    date_is_end = True
                ma = block_sum / self.n
                df.loc[start, column_name] = ma
                
            if date_is_end:
                break
        
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
            self.code = filename[0:6]
            self.analyze_one()

    def test_buy(self, n):
        '''
        收盘价低于 n 日均线，即买入， 高于即卖出
        '''
        file_list = os.listdir(self.file_path_prefix)
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            code = filename[0:6]
            print(code)
            try:
                df = pd.read_csv(self.file_path_prefix + filename, encoding='gbk')
            except:
                print('文件'+str(code) + '.csv 打开失败')
                return False
            df = df[df.日期 > self.end_date]
            df = df.iloc[::-1]      # 倒转
            column_name = "ma" + str(n)
            brought = False    # 是否已买入
            buy_arr = []
            sold_arr = []
            for index, row in df.iterrows():
                if not brought:
                    # 未买入， 判断是否小于均线
                    if row['收盘价'] < row[column_name]:
                        # 收盘价小于均线， 买入
                        buy_arr = [row['日期'], row[column_name], row['收盘价']]
                        brought = True
                else:
                    # 已买入， 判断是否大于均线
                    if row['收盘价'] > row[column_name]:
                        # 收盘价大于均线， 卖出
                        sold_arr = [row['日期'], row[column_name], row['收盘价']]
                        buy_info = BuyInfo(code, buy_arr, sold_arr)
                        self.all_buy_res.append(buy_info)
                        brought = False
        self.show_buy_res()
        
    def show_buy_res(self):
        rate = 0
        for item in self.all_buy_res:
            if item.diff > 0:
                rate += 1
            print(item.to_string())
        rate /= len(self.all_buy_res)
        rate = format(rate*100, '.4f') + '%'
        print("总共有%s种满足条件的情况， 盈利的几率为%s" % (len(self.all_buy_res), rate))


if __name__ == '__main__':
    file_path_prefix = 'H:\\sharesDatas\\kline\\'
    # file_path_prefix = 'F:\\files\\sharesDatas\\kline\\'
    ma = MA(file_path_prefix,end_date='2017-01-01', code='000001')
    ma.analyze_all()
    # ma.test_buy(10)
    