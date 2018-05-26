#!/usr/bin/python

import time
import hmac
import urllib
import requests
import hashlib
import base64
import math
import json
import datetime

API_KEY = 'YOURKEY'
API_SECRET = 'SECRET'
minOrder=float(0.00051)
#tradePairId=5121
tradePairId=5643
#currencyId = "XBY"
currencyId = "LUX"
#5121 XBY
volLimit=int(0.5)
operationMode='Buy'
mode='Dual'
lastExecutedAmount=int(20)
lastExecutedValue=float(0.00002550)
orderNumber = str(0)
balance = 0


def api_query( method, req = None ):
 if not req:
         req = {}
 #print "def api_query( method = " + method + ", req = " + str( req ) + " ):"
 time.sleep( 1 )
 public_set = set([ "GetCurrencies", "GetTradePairs", "GetMarkets", "GetMarket", "GetMarketHistory", "GetMarketOrders" ])
 private_set = set([ "GetBalance", "GetDepositAddress", "GetOpenOrders", "GetTradeHistory", "GetTransactions", "SubmitTrade", "CancelTrade", "SubmitTip" ])
 if method in public_set:
         url = "https://www.cryptopia.co.nz/api/" + method
         if req:
             for param in req:
                 url += '/' + str( param )
         r = requests.get( url )
 elif method in private_set:
          url = "https://www.cryptopia.co.nz/Api/" + method
          nonce = str( int( time.time() ) )
          post_data = json.dumps( req );
          m = hashlib.md5()
          m.update(post_data.encode('utf-8')) 
          requestContentBase64String = base64.b64encode(m.digest()).decode('utf-8')
          signature = API_KEY + "POST" + urllib.parse.quote_plus( url ).lower() + nonce + requestContentBase64String
          hmacsignature = base64.b64encode(hmac.new(base64.b64decode( API_SECRET ), signature.encode('utf-8'), hashlib.sha256).digest())
          header_value = "amx " + API_KEY + ":" + hmacsignature.decode('utf-8') + ":" + nonce
          headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
          r = requests.post( url, data = post_data, headers = headers )
 response = r.text
 return response

def validateOrderExecution():
    global orderNumber
    try:
        myOpenOrders=json.loads(api_query("GetOpenOrders",{'TradePairId':tradePairId}))
        newBalance = json.loads(api_query("GetBalance", {'Currency':currencyId}))["Data"][0]["Total"]
        for i in myOpenOrders['Data']:
            if (str(i['OrderId']) == orderNumber and newBalance==balance):
                print("Orden aun abierta")
                return 0
                break
            elif(newBalance!=balance):
                print("Balance distinto si ordenes")
                return 2
            elif(newBalance==balance and str(i['OrderId']) != orderNumber):
                print("valid1")
                return 3
        if(newBalance!=balance):
            print("Balance distinto no ordenes")
            return 2
        elif(newBalance==balance):
            print("Mismo Balance no ordenes")
            return 1
    except IndexError:
        if(newBalance!=balance):
            print("Balance distinto no ordenes")
            return 2
        elif(newBalance==balance):
            print("Mismo Balance no ordenes")
            return 1
    
    

def cancelAllOrder():
    myCancelledOrders=json.loads(api_query("CancelTrade",{'Type':'TradePair','TradePairId':tradePairId}))
    print("Cancelar todas las ordenes"+str(myCancelledOrders))
    return 0

def calcRateValue():
    marketOrders=json.loads(api_query("GetMarketOrders",[ tradePairId, 20 ]))
    maxOperVal=str(marketOrders['Data'][operationMode][0]['Price'])
    for i in marketOrders['Data'][operationMode]:
        currentOrderValue=i['Price']
        operVolume=int(i['Volume'])
        print("Rate de Orden: "+"{:.8f}".format(float(currentOrderValue))+' Volumen:'+str(operVolume))
        if(operationMode=='Buy'):
            porcentaje=float(currentOrderValue)/float(maxOperVal)
            print("Resultado buy: "+str(porcentaje))
            if(porcentaje<0.9999999999 and operVolume>volLimit):
                orderVal=float(currentOrderValue)         
                break
        else:
            porcentaje=float(currentOrderValue)/float(maxOperVal)
            print("Resultado sell: "+str(porcentaje) +"current vs buy"+str(currentOrderValue)+" vs "+ str(lastExecutedValue))
            if(porcentaje>1.0001 and operVolume>volLimit and float(currentOrderValue)>lastExecutedValue):
                orderVal=float(currentOrderValue)
                print("Val: "+ str(orderVal))
                break
    return orderVal

def submitBuyOrder(orderVal):
    global orderNumber
    global lastExecutedValue
    global lastExecutedAmount
    orderAmount = math.ceil(float(minOrder/float(orderVal)))
    myOpenOrderRate="{:.8f}".format(orderVal)     
    lastExecutedValue =       orderVal
    lastExecutedAmount = orderAmount
    print("Rate a crear: "+str(myOpenOrderRate) +" Cantidad a crear: "+str(orderAmount))
    submitedTrades=json.loads(api_query("SubmitTrade",{'Type':'Buy','TradePairId':tradePairId,'Rate':myOpenOrderRate,'Amount':orderAmount}))
    print(submitedTrades)
    orderNumber=str(submitedTrades['Data']['OrderId'])
    return orderNumber
 
def submitSellOrder(orderVal):
    global orderNumber 
    global lastExecutedAmount
    #sellBalance = json.loads(api_query("GetBalance", {'Currency':currencyId}))["Data"][0]["Total"]
    myOpenOrderRate="{:.8f}".format(orderVal)    
    lastExecutedAmount=lastExecutedAmount
    print("Rate a Vender: "+str(myOpenOrderRate)+" Cantidad a Vender: "+str(lastExecutedAmount))
    submitedTrades=json.loads(api_query("SubmitTrade",{'Type':'Sell','TradePairId':tradePairId,'Rate':myOpenOrderRate,'Amount':lastExecutedAmount}))
    print(submitedTrades)
    orderNumber=str(submitedTrades['Data']['OrderId'])
    return orderNumber

def buyOrder():
    global orderNumber
    myOpenOrders=json.loads(api_query("GetOpenOrders",{'TradePairId':tradePairId}))
    orderVal=calcRateValue()
    if(len(myOpenOrders['Data'])>0):
         print("Orden Abierta: "+ str(myOpenOrders['Data'][0]['OrderId'])+ " Orden anterior? " + str(orderNumber))
         if(str(myOpenOrders['Data'][0]['OrderId'])==orderNumber):
             myOpenOrderRate=myOpenOrders['Data'][0]['Rate']
             print("Rate:"+str(myOpenOrderRate))
             if(myOpenOrderRate>orderVal):
                 print("Rate mayor al esperado")
                 cancelAllOrder()
                 if(validateOrderExecution()==1):
                     orderNumber=submitBuyOrder(orderVal)
                     print(str(datetime.datetime.now().time())+": Orden que yo abri: "+ orderNumber)
             elif(myOpenOrderRate==orderVal):
                 print("Rate Igual, la dejo")
             else:
                 print("Rate menor al esperado")
                 cancelAllOrder()
                 if(validateOrderExecution()==1):
                     orderNumber=submitBuyOrder(orderVal)
                     print(str(datetime.datetime.now().time())+": Orden que yo abri: "+ orderNumber)   
         else: 
            cancelAllOrder()
    else:
        print("No tenemos ordenes abiertas")
        if(validateOrderExecution()==1):
            orderNumber=submitBuyOrder(orderVal)
            print("Orden que yo abri: "+ orderNumber)
    return 0

def sellOrder():
    global orderNumber
    myOpenOrders=json.loads(api_query("GetOpenOrders",{'TradePairId':tradePairId}))
    orderVal=calcRateValue()
    if(len(myOpenOrders['Data'])>0):
         print("Orden Abierta encontrada "+ str(myOpenOrders['Data'][0]['OrderId']))
         print("Orden anterior? " +orderNumber)
         if(str(myOpenOrders['Data'][0]['OrderId'])==orderNumber):
             print("Sigue abierta la orden "+str(orderNumber))
             myOpenOrderRate=myOpenOrders['Data'][0]['Rate']
             print("Rate:"+str(myOpenOrderRate))
             if(myOpenOrderRate>orderVal or myOpenOrderRate<orderVal):
                 print("Rate mayor al esperado")
                 cancelAllOrder()
                 if(validateOrderExecution()==1):
                     orderNumber=submitSellOrder(orderVal)
                     print("Orden que yo abri: "+ orderNumber)
             elif(myOpenOrderRate==orderVal):
                 print("Rate Igual, la dejo")        
         else: 
            cancelAllOrder()
    else:
        print("No tenemos ordenes abiertas")
        if(validateOrderExecution()==1):
            orderNumber=submitSellOrder(orderVal)
            print("Orden que yo abri: "+ orderNumber)
    return 0

ciclo=0     
print(datetime.datetime.now().time())
balance = json.loads(api_query("GetBalance", {'Currency':currencyId}))["Data"][0]["Total"]
print("balance: "+ str(balance))

while (mode=='Dual'):
    print("*")
    val=validateOrderExecution()
    print(operationMode + " -Resultado validacion y ciclo:"+ str(val)+" - "+str(ciclo))
    if(orderNumber=="0"):
        buyOrder()
    elif(operationMode=='Buy'):
        if(val==2):
            operationMode='Sell'
            #operationMode='Buy'
            ciclo=ciclo+1          
            balance = json.loads(api_query("GetBalance", {'Currency':currencyId}))["Data"][0]["Total"]
        else:
             buyOrder()
    elif(operationMode=='Sell'):
         if(val==2):
             operationMode='Buy'
             ciclo=ciclo+1           
             balance = json.loads(api_query("GetBalance", {'Currency':currencyId}))["Data"][0]["Total"]
         else:
             sellOrder()
