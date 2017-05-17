#from Benchmark import *

CONTRACT_SIZE_DICT = {'IC': 200, 'IF': 300, 'IH': 300}
INDEX_ID_DICT = {'IC': 'SH000905', 'IF': 'SH000300', 'IH': 'SH000016'}

main_future_id_dict = {}
close_price_df_dict_from_TS = {}
future_settlment_dict_from_TS = {}
all_stock_id_list = []

history_values_series = {}


class Computed_Trading_Days:
    computed_last_days = '2000-01-01'
    trading_days = set() # 保存查询到的结果

rt_prices = {}
current_value_sum = 0.0
stockPositionValueSeries = []
oneMinPricesDict = {}
todayOneMinPricesDict = {}
stock_id_name_map = {}

#benchmark_IC = BenchmarkIndexIC_Future()
#benchmark_IF = BenchmarkIndexIF_Future()
#benchmark_IH = BenchmarkIndexIH_Future()
#benchmark_IC_realtime = BenchmarkIndexIC_Future(history=False)
#benchmark_IF_realtime = BenchmarkIndexIF_Future(history=False)
#benchmark_IH_realtime = BenchmarkIndexIH_Future(history=False)
#
#index_IC = BenchmarkIndexIC()
#index_IF = BenchmarkIndexIF()
#index_IH = BenchmarkIndexIH()
#
#index_IC_realtime = BenchmarkIndexIC(history=False)
#index_IF_realtime = BenchmarkIndexIF(history=False)
#index_IH_realtime = BenchmarkIndexIH(history=False)



    
    