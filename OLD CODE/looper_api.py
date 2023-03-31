#pylint: disable=E302
"""
#C0103,C0114,C0115,C0116,C0301,C0410,E1121,R0912,R0914,R1702,W0105,E0303
Copyright (C) 2019 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
 and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""
from json import dump
import collections
import datetime, inspect, logging, sqlite3, sys, time
# import requests  # For Nasdaq web usage
#import sql_utils
import sql_utils
from AvailableAlgoParams import AvailableAlgoParams
from ContractSamples import ContractSamples
from FaAllocationSamples import FaAllocationSamples
from OrderSamples import OrderSamples
from ScannerSubscriptionSamples import ScannerSubscriptionSamples
from copy import deepcopy
#
from defusedxml.ElementTree import parse
#
# Here, 'ibapi' refers to the installed TWS package, which is "C:/TWS API"
from ibapi import utils
from ibapi import wrapper
from ibapi.client import EClient
from ibapi.commission_report import CommissionReport
# types
from ibapi.common import *  # @UnusedWildImport
from ibapi.contract import *  # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.object_implem import Object  # ct
from ibapi.order import *  # @UnusedWildImport
from ibapi.order_condition import *  # @UnusedWildImport
from ibapi.order_state import *  # @UnusedWildImport
from ibapi.scanner import ScanData
from ibapi.tag_value import TagValue
from ibapi.ticktype import *  # @UnusedWildImport
from ibapi.utils import iswrapper
#
import telebotTexting
#
from dates import get_sql_now, get_last_trading_date, makeIBContract  #, getTMinusOne
from myCode import myCode
from utils import next_X_months, file_exists, commatize
import Data.IB_tickTypes
import myLogging
import myRequest
from sql_utils import Parameters, sql_execute, set_last_update, convert_date, get_option_price, get_sql_today  # , set_live_options_to_be_priced
from sql_utils import get_last_price, updateTblPositions, sql_fetchone, reset_last_update
import trading
from dividends import isThisADuplicatedDividend


class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)
        # ! [socket_declare]
        # how many times a method is called to see test coverage
        self.clntMeth2callCount = collections.defaultdict(int)
        self.clntMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nReq = collections.defaultdict(int)
        self.setupDetectReqId()

    #def reqExecutions(self, reqId:int, execFilter:ExecutionFilter):
    #    # https://interactivebrokers.github.io/tws-api/executions_commissions.html
    #    raise NotImplemented


    def countReqId(self, methName, fn):
        def countReqId_(*args, **kwargs):
            self.clntMeth2callCount[methName] += 1
            idx = self.clntMeth2reqIdIdx[methName]
            if idx >= 0:
                sign = -1 if 'cancel' in methName else 1
                self.reqId2nReq[sign * args[idx]] += 1
            return fn(*args, **kwargs)

        return countReqId_

    def setupDetectReqId(self):
        methods = inspect.getmembers(EClient, inspect.isfunction)
        for (methName, meth) in methods:
            if methName != "send_msg":
                # don't screw up the nice automated logging in the send_msg()
                self.clntMeth2callCount[methName] = 0
                # logging.debug("meth %s", name)
                sig = inspect.signature(meth)
                for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                    (paramName, param) = pnameNparam  # @UnusedVariable
                    if paramName == "reqId":
                        self.clntMeth2reqIdIdx[methName] = idx

                setattr(TestClient, methName, self.countReqId(methName, meth))

                # print("TestClient.clntMeth2reqIdIdx", self.clntMeth2reqIdIdx)


# ! [ewrapperimpl]
class TestWrapper(wrapper.EWrapper):
    # ! [ewrapperimpl]
    def __init__(self):
        wrapper.EWrapper.__init__(self)
        self.wrapMeth2callCount = collections.defaultdict(int)
        self.wrapMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nAns = collections.defaultdict(int)
        self.setupDetectWrapperReqId()


    def countWrapReqId(self, methName, fn):
        def countWrapReqId_(*args, **kwargs):
            self.wrapMeth2callCount[methName] += 1
            idx = self.wrapMeth2reqIdIdx[methName]
            if idx >= 0:
                self.reqId2nAns[args[idx]] += 1
            return fn(*args, **kwargs)

        return countWrapReqId_

    def setupDetectWrapperReqId(self):

        methods = inspect.getmembers(wrapper.EWrapper, inspect.isfunction)
        for (methName, meth) in methods:
            self.wrapMeth2callCount[methName] = 0
            # logging.debug("meth %s", name)
            sig = inspect.signature(meth)
            for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                (paramName, param) = pnameNparam # @UnusedVariable
                # we want to count the errors as 'error' not 'answer'
                if 'error' not in methName and paramName == "reqId":
                    self.wrapMeth2reqIdIdx[methName] = idx

            setattr(TestWrapper, methName, self.countWrapReqId(methName, meth))

            # print("TestClient.wrapMeth2reqIdIdx", self.wrapMeth2reqIdIdx)


# this is here for documentation generation
"""
#! [ereader]
        # You don't need to run this in your code!
        self.reader = reader.EReader(self.conn, self.msg_queue)
        self.reader.start()   # start thread
#! [ereader]
"""


# ! [socket_init]
class LOOPER_APP(TestWrapper, TestClient):
    def __str__(self):
        return "'LOOPER_APP' Class"

    def __init__(self, logger):  # reqId, stayAlive, debug=False, which="", bot=None, tickerList=None):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)
        #self.thislogger = logger
        self.statusDict = []
        if (2+2)/4 == 12:
            # Parameters
            #self.reqId = reqId
            #self.STAY_ALIVE = stayAlive
            #self.DEBUG = debug
            #self.which = which
            #self.GLOBAL_BOT_TWS = bot
            #self.tickerList = tickerList
            #self.permIdArr = self.initializeOrderHistory()
            # Variables
            self.DO_NOT_DISCONNECT = False
            self.account = "U7864219"  # todo: Should I get rid of this?
            self.accountSummariesNeeded = {}
            self.allAccounts = None  # Filled in with reqManagedAccts() -> managedAccounts()
            self.allTickersHaveBeenRequested = False
            self.all_requests = {}
            self.badTickers = []
            self.nKeybInt = 0
            self.nextValidOrderId = None
            self.no_tickSize = True  # I don't care about tick size, so don't print them
            self.num_requests = 0
            self.permId2ord = {}
            self.reqId2nErr = collections.defaultdict(int)
            self.simplePlaceOid = None
            self.things_requested = {}
            # Method calls
            self.permIds = self.getAllPermIds()  # Orders I know about from the past
            if not hasattr(self, "thislogger"):
                name = (__name__.split("."))[-1]
                #print(f"*** Creating thislogger({name}) .. ***")
                self.thislogger, self.sqllogger = myLogging.setupMyLogging("MAIN")  # name)
            self.my_code = myCode()


    def nextValidId(self, orderId: int):
        # If I'm the only person using this, the num will always be "1"
        super().nextValidId(orderId)

        logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId

        # we can start now
        self.start()


    def start(self):
        print("Executing requests - START")
        # #thislogger.debug("Executing requests - START")

        # IB account summaries:
        thislogger.debug("self.loop_account_summaries()")
        self.loop_account_summaries()

        # IB positions:
        #self.loop_positions()
        thislogger.debug("self.reqPositions()")
        self.reqPositions()

        # IB get executions:
        thislogger.debug("self.reqExecutions(10002, ExecutionFilter())")
        self.reqExecutions(10002, ExecutionFilter())

        # IB get orders:
        thislogger.debug("self.reqAllOpenOrders()")
        self.reqAllOpenOrders()

        return

    def xorderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining,
                            avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        #if "IB get orders" not in self.things_requested.keys():
        #    # This is the automatic one when IB is connected to
        #    return

        #msg = f"PermId: {permId}, orderId: {orderId}, ParentId: {parentId}, Status: {status}, Filled: {filled}, Remaining: {remaining}, AvgFillPrice: {avgFillPrice}, " \
        #      f"LastFillPrice: {lastFillPrice}, ClientId: {clientId}, WhyHeld: " \
        #     ticker!
        msg = ""
        if permId:
            msg += f"PermId: {permId}, "
        if orderId:
            msg += f"orderId: {orderId}, "
        if parentId:
            msg += f"ParentId: {parentId}, "
        if status:
            msg += f"Status: {status}, "
        if filled:
            msg += f"Filled: {filled}, "
        if remaining:
            msg += f"Remaining: {remaining}, "
        if avgFillPrice:
            msg += f"AvgFillPrice: {avgFillPrice}, "
        if lastFillPrice:
            msg += f"LastFillPrice: {lastFillPrice}, "
        if clientId:
            msg += f"ClientId: {clientId}, "
        if whyHeld:
            msg += f"WhyHeld: {whyHeld}, "
        if mktCapPrice:
            msg += f"MktCapPrice: {mktCapPrice}, "
        msg = msg[:-2]  # Get rid of the final ', '
        if msg in self.statusDict:
            # I already know about this one
            return
        self.statusDict.append(msg)
        thislogger.debug(f"orderStatus(): {msg}")

        params = Parameters("tbl_IB_order_status", "orderStatus", {
            "permId": permId,
            "orderId": orderId,
            "parentId": parentId,
            "status": status,
            "filled": filled,
            "remaining": remaining,
            "avgFillPrice": avgFillPrice,
            "lastFillPrice": lastFillPrice,
            "clientId": clientId,
            "whyHeld": whyHeld,
            "mktCapPrice": mktCapPrice,
            })
        params.processThis()
        if params.msg in ["added", "updated"]:
            debugMsg(orderId, "upload_IB_orderState", f"tbl_IB_orderState was {params.msg}: {params.update_msg}")
        return



    def openOrderEnd(self):
        super().openOrderEnd()
        thislogger.debug(f"looper - openOrderEnd()")
        return


    def loop_orders(self):
        # Obtain those orders created via the TWS API ***regardless of the submitting client application***: Works!
        # -->             openOrder()
        # -->             orderStatus()
        self.reqAllOpenOrders()
        return

    def loop_positions(self):
        # Requesting all accounts' positions.
        #self.things_requested["Positions"] = self.things_requested.get("Positions", 0) + 1
        self.reqPositions()
        return


    @iswrapper
    def error(self, reqId, errorCode, errorString):
        # looper  https://interactivebrokers.github.io/tws-api/message_codes.html
        # -------------------------------------------------------------------------------------------------------------------
        # 1100  : "Connectivity between IB and the TWS has been lost."   Your TWS/IB Gateway has been disconnected from IB servers.
        #          This can occur because of an internet connectivity issue, a nightly reset of the IB servers, or a competing session.
        # 1101  : "Connectivity between IB and TWS has been restored- data lost.*"  The TWS/IB Gateway has successfully reconnected to IB's servers.
        #          Your market data requests have been lost and need to be re-submitted.
        # 1102  : "Connectivity between IB and TWS has been restored- data maintained."  The TWS/IB Gateway has successfully reconnected to IB's servers.
        #          Your market data requests have been recovered and there is no need for you to re-submit them.
        # 1300  : "TWS socket port has been reset and this connection is being dropped. Please reconnect on the new port - <port_num>"
        #          The port number in the TWS/IBG settings has been changed during an active API connection.
        # -------------------------------------------------------------------------------------------------------------------
        # 10167 : "Requested market data is not subscribed. Displaying delayed market data." - ARR.SMART [LSE]"
        # 177   : No security definition has been found for the request
        # 200   : Bad contract description, give more/better data
        # 320   : "Server error when reading an API client request."
        # 430   : "The fundamentals data for the security specified is not available.Not allowed'"
        # 504   : Not connected. You are trying to perform a request without properly connecting and/or after connection to the TWS
        #         has been broken probably due to an unhandled exception within your client application.
        if reqId == -1:
            # I don't care about nice "Market data farm connection is OK" type notifications as they clog up the output
            return

        errorsIKnow = [100, 1002, 10185, 110, 161, 200, 202, 2104, 300, 320, 321, 322, 354, 430, 435, 504]
        if errorCode not in errorsIKnow:
            myjoe()  # A new error!

        #
        params = Parameters("tbl_errors", "error", {"reqId": reqId, "ticker": "", "errorCode": errorCode,
                                                    "errorString": errorString, "contract": ""})
        #errorString = errorString.replace("'", "~")    # check 'curdate'
        if reqId not in self.all_requests.keys():
            super().error(reqId, errorCode, errorString)  # this goes to STDERR, in red
            thislogger.error(f"error(L1): *************** reqId: {reqId}, errorCode: {errorCode}, errorString: '{errorString}'")
            params.processThis(logIt=True)     # todo: check logfile for [looper]?
            return

        the_request = self.all_requests[reqId]
        ticker = the_request.ticker
        contract = the_request.contract
        exchange = the_request.contract.exchange
        primary = the_request.contract.primaryExchange
        currency = the_request.contract.currency
        params.param_dict["ticker"] = ticker
        params.param_dict["contract"] = contract
        params.processThis()

        if errorCode == 300:
            # 300   : "Can't find EId with ticker Id: "  (cancelling a market data request)
            thislogger.warning(f"error(L2): *************** reqId: {reqId}: {ticker:5}: errorCode: 300 [{errorString}] [{self.all_requests[reqId].contract}]")
            # check logfile for [looper]
            return  # should I still set its errorCode and String?  No, because the original request is fine,
                    # it's only the *cancelling* of the request that didn't work

        # If I errror on an option request, keep track of bad ones:
        #currency????
        myjoe()
        if isinstance(the_request, myRequest.timed_OptionContractRequest):
            self.processBadOptionRequest(ticker, exchange, primary, currency)

        # check logfile for [looper]
        thislogger.warning(f"error(L3): *************** reqId: {reqId:4}: errorCode: #{errorCode} - [{errorString}] - ({ticker}.{exchange}.{primary})")
        if ticker not in self.badTickers:
            self.badTickers.append(ticker)

        #if errorCode != 10167:
        self.all_requests[reqId].errorCode = errorCode
        self.all_requests[reqId].errorString = errorString
        self.CHECK_FOR_TIME_TO_DISCONNECT()


class AccountSummaryTags:
    AccountType = "AccountType"
    NetLiquidation = "NetLiquidation"
    TotalCashValue = "TotalCashValue"
    SettledCash = "SettledCash"
    AccruedCash = "AccruedCash"
    BuyingPower = "BuyingPower"
    EquityWithLoanValue = "EquityWithLoanValue"
    PreviousEquityWithLoanValue = "PreviousEquityWithLoanValue"
    GrossPositionValue = "GrossPositionValue"
    ReqTEquity = "ReqTEquity"
    ReqTMargin = "ReqTMargin"
    SMA = "SMA"
    InitMarginReq = "InitMarginReq"
    MaintMarginReq = "MaintMarginReq"
    AvailableFunds = "AvailableFunds"
    ExcessLiquidity = "ExcessLiquidity"
    Cushion = "Cushion"
    FullInitMarginReq = "FullInitMarginReq"
    FullMaintMarginReq = "FullMaintMarginReq"
    FullAvailableFunds = "FullAvailableFunds"
    FullExcessLiquidity = "FullExcessLiquidity"
    LookAheadNextChange = "LookAheadNextChange"
    LookAheadInitMarginReq = "LookAheadInitMarginReq"
    LookAheadMaintMarginReq = "LookAheadMaintMarginReq"
    LookAheadAvailableFunds = "LookAheadAvailableFunds"
    LookAheadExcessLiquidity = "LookAheadExcessLiquidity"
    HighestSeverity = "HighestSeverity"
    DayTradesRemaining = "DayTradesRemaining"
    Leverage = "Leverage"

    AllTags = ",".join((AccountType, NetLiquidation, TotalCashValue,
                        SettledCash, AccruedCash, BuyingPower, EquityWithLoanValue,
                        PreviousEquityWithLoanValue, GrossPositionValue, ReqTEquity,
                        ReqTMargin, SMA, InitMarginReq, MaintMarginReq, AvailableFunds,
                        ExcessLiquidity, Cushion, FullInitMarginReq, FullMaintMarginReq,
                        FullAvailableFunds, FullExcessLiquidity,
                        LookAheadNextChange, LookAheadInitMarginReq, LookAheadMaintMarginReq,
                        LookAheadAvailableFunds, LookAheadExcessLiquidity, HighestSeverity,
                        DayTradesRemaining, Leverage))


def update_table_ALGO_ORDERS(reqId, contract:Contract, order:Order):
    #whatAmI = f"[{contract.__str__()}] - [{order.__str__()}]"
    #
    params = Parameters("ALGO_ORDERS", "update_table_ALGO_ORDERS", {"broker": "IB"})
    #
    params.param_dict["reqId"] = reqId
    ticker = contract.symbol
    params.param_dict["ticker"] = ticker
    params.param_dict["currency"] = contract.currency
    secType = contract.secType
    params.param_dict["secType"] = secType
    params.param_dict["exchange"] = contract.exchange
    params.param_dict["IB_expiry"] = contract.lastTradeDateOrContractMonth
    params.param_dict["expiry"] = convert_date(contract.lastTradeDateOrContractMonth)
    strike = contract.strike
    params.param_dict["strike"] = strike
    params.param_dict["putCall"] = contract.right
    #
    account = order.account
    params.param_dict["account"] = account
    action = order.action
    params.param_dict["action"] = action
    params.param_dict["orderType"] = order.orderType
    totalQuantity = order.totalQuantity
    params.param_dict["quantity"] = totalQuantity
    lmtPrice = order.lmtPrice
    params.param_dict["lmtPrice"] = lmtPrice
    tif = order.tif
    params.param_dict["tif"] = tif
    params.param_dict["transmited"] = order.transmit

    params.param_dict["tradeReco"] = 999999

    #
    params.processThis()
    #
    return params.msg, params.update_msg


if __name__ == "__main__":
    #app = TWS_API_APP(reqId=0, stayAlive=False)
    #app.getOpDefs()
    pass

