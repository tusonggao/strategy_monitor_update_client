from __future__ import print_function

from WindPy import *
import time

rt_prices = {}

def demoWSQCallback111(indata):
    print('Intrigged by Call back of wind')
    string = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    string += ' indata.Codes is ' + str(indata.Codes)
    for k in range(0,len(indata.Fields)):
        string += ' indata.Fields[k] is ' + str(indata.Fields[k]) + \
                  ' value is ' + str(indata.Data[k][0])
        if(indata.Fields[k] == "RT_TIME"):
            pass
        if(indata.Fields[k] == "RT_LAST"):
            if len(indata.Codes)==1:
                rt_prices[indata.Codes[0]] = round(indata.Data[k][0], 2)
                print('price is ', rt_prices[indata.Codes[0]])

if __name__=='__main__':
    w.start()
    print('start w.start()')
    test_b = w.isconnected()
    print('test connected is ', test_b)
	
    data = w.wsq("600000.SH, 000001.SZ","rt_time, rt_last", func=demoWSQCallback111)
	
    count = 0
    while True:
        count = (count + 1)%1001
        if count%25==0:
            print('current count is ', count)
            print('now rt_prices is', rt_prices)
        time.sleep(1)