# -*- coding: utf-8 -*-
"""
基本特征包括：
个人信息： 30列 不处理
日志信息： 1. 用户点击次数 1列
          2. 一个月中每个id在每一天的点击次数 31列
          3. 点击模块（如饭票-代金券-门店详情）前两列ont-hot
          4. 浏览类型 2列
          5. 每个用户每次点击间隔 最小值-最大值-均值-方差 4列
          6. 最后7天点击斜率
@author: 肖鹏程
@QQ: 609659119
"""

import pandas as pd
import numpy as np
import time 

# 读取个人信息
train_agg = pd.read_csv('data/train_agg.csv',sep='\t')
test_agg = pd.read_csv('data/test_agg.csv',sep='\t')
agg = pd.concat([train_agg,test_agg],copy=False)
# 用户唯一标识
train_flg = pd.read_csv('data/train_flg.csv',sep='\t')
test_flg = pd.read_csv('data/submit_sample.csv',sep='\t')
test_flg['FLAG'] = -1
del test_flg['RST']
flg = pd.concat([train_flg,test_flg])
#data = pd.merge(agg_normal,flg,on=['USRID'],how='left',copy=False)
data = pd.merge(agg,flg,on=['USRID'],how='left',copy=False)

# 日志信息
train_log = pd.read_csv('data/train_log.csv',sep='\t')
test_log = pd.read_csv('data/test_log.csv',sep='\t')
log = pd.concat([train_log,test_log],copy=False)

# =============================================================================
# 用户点击次数
# =============================================================================
log_usrid_count = log[['USRID']]
log_usrid_count['count'] = 1
log_usrid_count = log_usrid_count.groupby(['USRID'],as_index=False)['count'].sum()
data = pd.merge(data,log_usrid_count,on=['USRID'],how='left',copy=False)

# =============================================================================
# 前一个月统计，点击为1，没有为0
# 统计前2,3,4,5,6,7天的点击量 
# =============================================================================
log_time = log[['USRID','OCC_TIM']]
log_time['day'] = log['OCC_TIM'].apply(lambda x:int(x[8:10]))
log_time = log_time.drop(['OCC_TIM'],axis=1)
days = pd.get_dummies(log_time['day'])
days.columns = ['mooth_day'+str(i+1) for i in range(days.shape[1])]
log_time = pd.concat([log_time[['USRID']],days],axis=1)
log_time = log_time.groupby(['USRID'],as_index=False).sum()
log_time['front_2'] = log_time['mooth_day31']+log_time['mooth_day30']
for i in range(3,8):
    col = 'front_'+str(i)
    col_front = 'front_'+str(i-1)
    col_add = 'mooth_day'+str(32-i)
    log_time[col] = log_time[col_front] + log_time[col_add]  
data = pd.merge(data,log_time,on=['USRID'],how='left',copy=False)

# =============================================================================
# 点击模块名称均为数字编码（形如231-145-18），代表了点击模块的三个级别（如饭票-代金券-门店详情）
# =============================================================================
log_mode = log[['USRID','EVT_LBL']]
log_mode['EVT_LBL_1'] = log_mode['EVT_LBL'].apply(lambda x:int(x.split('-')[0]))
EVT = pd.get_dummies(log_mode['EVT_LBL_1'])
EVT.columns = ['level1_'+str(i+1) for i in range(EVT.shape[1])]
log_mode = pd.concat([log_mode[['USRID']],EVT],axis=1)
log_mode = log_mode.groupby(['USRID'],as_index=False).sum()
data = pd.merge(data,log_mode,on=['USRID'],how='left',copy=False)
log_mode = log[['USRID','EVT_LBL']]
log_mode['EVT_LBL_2'] = log_mode['EVT_LBL'].apply(lambda x:int(x.split('-')[1]))
EVT = pd.get_dummies(log_mode['EVT_LBL_2'])
EVT.columns = ['level2_'+str(i+1) for i in range(EVT.shape[1])]
log_mode = pd.concat([log_mode[['USRID']],EVT],axis=1)
log_mode = log_mode.groupby(['USRID'],as_index=False).sum()
data = pd.merge(data,log_mode,on=['USRID'],how='left',copy=False)

# =============================================================================
# 浏览类型
# =============================================================================
log_type = log[['USRID','TCH_TYP']]  
types = pd.get_dummies(log_type['TCH_TYP']) 
types.columns = ['APP','H5']
log_type = pd.concat([log_type[['USRID']],types],axis=1)
log_type = log_type.groupby(['USRID'],as_index=False).sum()
data = pd.merge(data,log_type,on=['USRID'],how='left',copy=False)

#=============================================================================
# 这个部分将时间转化为秒，之后计算用户下一次的时间差特征
# =============================================================================
log['OCC_TIM'] = log['OCC_TIM'].apply(lambda x:time.mktime(time.strptime(x, "%Y-%m-%d %H:%M:%S")))
log = log.sort_values(['USRID','OCC_TIM'])
log['next_time'] = log.groupby(['USRID'])['OCC_TIM'].diff(-1).apply(np.abs)
log = log.groupby(['USRID'],as_index=False)['next_time'].agg({
        'next_time_mean':np.mean,
        'next_time_std':np.std,
        'next_time_min':np.min,
        'next_time_max':np.max
})
data = pd.merge(data,log,on=['USRID'],how='left',copy=False)
##交换下特征顺序
change = ['front_2','front_3','front_4','front_5','front_6','front_7']
data_front = data[change]
data = data.drop(change,axis=1)
data = pd.concat([data,data_front],axis=1)
data.to_csv('base_line_data.csv',index=False,sep='\t')









