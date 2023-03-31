raise UserWarning
import i should not be used anymore

# pylint: disable=E302
# C0103,C0114,C0115,C0116,C0301,C0410,E1121,R0912,R0914,R1702,W0105,E0303
import collections, inspect, sqlite3, sys, time
import logging
#
#import myRequest
#import pandas.core.common
from AvailableAlgoParams import AvailableAlgoParams
from ContractSamples import ContractSamples
from FaAllocationSamples import FaAllocationSamples
from OrderSamples import OrderSamples
from ScannerSubscriptionSamples import ScannerSubscriptionSamples
from defusedxml.ElementTree import parse
# Here, 'ibapi' refers to the installed TWS package, which is "C:/TWS API"
from ibapi import utils
from ibapi import wrapper
from ibapi.client import EClient
from ibapi.commission_report import CommissionReport
# types
from ibapi.common import *
from ibapi.contract import *  # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.object_implem import Object  # ct
from ibapi.order import *  # @UnusedWildImport
from ibapi.order_condition import *  # @UnusedWildImport
from ibapi.order_state import *  # @UnusedWildImport
from ibapi.scanner import ScanData
from ibapi.tag_value import TagValue
from ibapi.ticktype import *
from ibapi.utils import iswrapper
import pyperclip
#
#import variables
from dates import dateIsSaturday, dateIsSunday, makeIBContract, get_weeks_from_now, add_new_holiday, upcomingQuarterlyExpirations
from myCode import myCode
from utils import get_variable, next_X_months, file_exists, commatize, file_was_made_today, Run_In_Debug_Mode_only  # , set_last_reqId
import data_file
import IB_tickTypes
from sql_utils import set_last_update, backUpOrderFile, get_last_update
from sql_utils import get_last_div_update, get_last_trading_date, get_last_note
import trading
from dividends import isThisADuplicatedDividend, divsPerYear
from ticker_obj import TickerObj, get_GreeksToGet
from data_file import DO_NOT_TRADE, company_names, USE_BRACKETS_WITH
# from needs_no_imports import mylogger
# from myLogging import mylogger
import variables
from orderDict import *

# newlogger = logging.getLogger("myapp.newlogger")
newlogger = mylogger()
TODAY = get_sql_today()

"""
def sendTelegramText(bot, msg, newlogger, printIt=True):
    # Look in myCode for original pyTelegramBotAPI()
    my_id = 1710461519
    bot.send_message(my_id, msg)
    if printIt:
        newlogger.debug(msg)
"""

def printWhenExecuting(fn):
    def fn2(self):
        fn(self)

    return fn2


def printinstance(reqId, inst):
    attrs = vars(inst)
    msg = ', '.join("%s: %s" % item for item in attrs.items())
    print(f"{reqId:5}: printinstance() : {msg}\n")
    for key, value in attrs.items():
        print(f"{reqId:5} - {attrs['contract']} - {key} == {value}")
    print("\n\n")


class Activity(Object):
    def __init__(self, reqMsgId, ansMsgId, ansEndMsgId, reqId):
        self.reqMsdId = reqMsgId
        self.ansMsgId = ansMsgId
        self.ansEndMsgId = ansEndMsgId
        self.reqId = reqId


class RequestMgr(Object):
    def __init__(self):
        # I will keep this simple even if slower for now: only one list of
        # requests finding will be done by linear search
        self.requests = []

    def addReq(self, req):
        self.requests.append(req)

    def receivedMsg(self, msg):
        pass


# ! [socket_declare]
class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)
        # ! [socket_declare]
        # how many times a method is called to see test coverage
        self.clntMeth2callCount = collections.defaultdict(int)
        self.clntMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nReq = collections.defaultdict(int)
        self.setupDetectReqId()

    # def reqExecutions(self, reqId:int, execFilter:ExecutionFilter):
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


# -------------------------------------------------------------------------------------------------------------------
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
                (paramName, param) = pnameNparam  # @UnusedVariable
                # we want to count the errors as 'error' not 'answer'
                if 'error' not in methName and paramName == "reqId":
                    self.wrapMeth2reqIdIdx[methName] = idx
            setattr(TestWrapper, methName, self.countWrapReqId(methName, meth))
        return
            # print("TestClient.wrapMeth2reqIdIdx", self.wrapMeth2reqIdIdx)
# -------------------------------------------------------------------------------------------------------------------

# this is here for documentation generation
"""
#! [ereader]
        # You don't need to run this in your code!
        self.reader = reader.EReader(self.conn, self.msg_queue)
        self.reader.start()   # start thread
#! [ereader]
"""

"""
def makeError(fn, ticker, errorCode, errorString):
    # fn         : calling function
    #    ticker     :
    #    errirCide  :
    #    errorString:
    
    try:
        dict = {"reqId": -1, "errorCode": errorCode, "errorString": errorString, "ticker": ticker}
        Parameters("tbl_errors", fn, dict).processThis()  # check 'curdate'
    except:
        raise
    else:
        return True
"""

# ! [socket_init]
class TWS_API_APP(TestWrapper, TestClient):
    reqId_ct = 0
    reqId_dict = {}
    all_requests = {}

    def __str__(self):
        return "'TWS_API_APP' Class"

    def __setattr__(self, key, value):
        if key == "reqId":
            self.reqId_ct += 1
            self.reqId_dict[self.reqId_ct] = value
            joe = 12
        if "NO_NEW_VARIABLES" not in self.__dict__ or self.NO_NEW_VARIABLES is False:
            self.__dict__[key] = value
        else:
            if key in self.__dict__:
                self.__dict__[key] = value
                return True
            else:
                print(f"TWS_API_APP.__setattr__() : Attempting to set '{key}' - not allowed!")
                raise UserWarning
        return

    def __init__(self, reqId=0, stayAlive=False, debug=False, which="", bot=None, tickerList=None, MD_obj=None,
                 whiches=None, orders_to_create=None):
        assert MD_obj
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)
        # UserDict.__init__(self)    # gets 'self.data' from here
        self.my_TWS_RESETS = {}
        self.contract_dict = {}
        # Parameters
        self.MD = MD_obj
        self.tickerDATA_TWS = TickerObj("TWS_API_APP")
        self.reqId = reqId
        self.orders_to_create = orders_to_create
        self.STAY_ALIVE = stayAlive
        self.DEBUG = debug
        self.which = which
        self.whiches = whiches
        self.GLOBAL_BOT_TWS = bot
        self.tickerList = tickerList
        # self.permIdArr = self.initializeOrderHistory()
        # Variables
        self.IB_TIMEOUT = variables.IB_TIMEOUT
        self.starting_time = time.time()
        self.account = "U7864219"  # todo: Should I get rid of this?
        self.accountSummariesNeeded = {}
        self.allAccounts = None  # Filled in with reqManagedAccts() -> managedAccounts()
        self.allTickersHaveBeenRequested = False
        # self.all_requests = {}
        self.badTickers = []
        self.nKeybInt = 0
        self.nextValidOrderId = None
        self.no_tickSize = True  # I don't care about tick size, so don't print them
        self.num_requests = 0
        self.permId2ord = {}
        self.reqId2nErr = collections.defaultdict(int)
        self.simplePlaceOid = None
        self.statusDict = []
        self.things_requested = {}
        self.ETFs = get_ETFS()
        self.newholiday = "None"
        # Method calls
        self.permIds = self.getAllPermIds()  # Orders I know about from the past
        #self.sqllogger = logging.getLogger("myapp.sqllog")
        self.my_code = myCode()
        self.QuarterlyExpirations = upcomingQuarterlyExpirations()
        self.NO_NEW_VARIABLES = True  # <---- leave this as the very last line of the __init__


    def computeTimeOutLength(self, fn):
        """ I use these types of requests to make a bunch at a time. If I'm only doing a few requests
            then 'self.seconds_until_stale' doesn't need to be 90 seconds, it can be smaller
            So,
        """
        totalRequests = len(self.all_requests)
        firstReqId = list(self.all_requests.keys())[0]
        MYMAX = self.all_requests[firstReqId].seconds_until_stale
        MYMIN = 10
        # newbit = (MYMAX - MYMIN) / (totalRequests - 1)
        for ct, reqId in enumerate(self.all_requests.keys()):
            # newLIM = MYMIN + (ct * newbit)
            newLIM = MYMIN + ct
            self.all_requests[reqId].seconds_until_stale = min(newLIM, MYMAX)  # newLIM
            debugMsg(self.all_requests[reqId].reqId, f"computeTimeOutLength({fn})",
                     f"Setting timeout to: {int(newLIM):3} seconds")
        return

    @staticmethod
    def initializeOrderHistory():
        qry = f"SELECT DISTINCT permId FROM tbl_IB_orders WHERE curdate='{get_last_trading_date()}'"
        res = sql_execute(qry)
        orders_arr = []
        for permId in res:
            orders_arr.append(permId)
        return orders_arr

    def getAllPermIds(self):
        qry = "SELECT distinct permId from tbl_IB_orders"
        res = sql_execute(qry)
        res_arr = []
        for id in res:
            res_arr.append(id)
        return res_arr

    def TWS_RESET(self, which, tickerList=None):
        self.which = which  # leave here
        if which in self.my_TWS_RESETS:
            val = self.my_TWS_RESETS[which]
            myjoe("WHY?")  # 'IB get positions'
        else:
            #newlogger.info(f"                                                                                         TWS_RESET(): I am adding '{which}' to self.my_TWS_RESETS now..")
            newlogger.info(f"TWS_RESET(0): *** A adding '{which}' to self.my_TWS_RESETS now..")
            self.my_TWS_RESETS[which] = 1
        newlogger.debug(f"TWS_RESET(1): doing a TWS reset ahead of: '{which}'")
        self.things_requested = {}
        self.badTickers = []
        self.tickerList = tickerList
        for key, request in self.all_requests.items():
            if isinstance(request, myRequest.timed_PnlRequest):
                if request.gotGoodPrice:
                    self.all_requests[key].IS_OLD = True
                    debugMsg(request.reqId, "TWS_RESET", f"Setting .ISOLD = True")
            else:
                joe = 12
        return

    def dumpTestCoverageSituation(self):
        for clntMeth in sorted(self.clntMeth2callCount.keys()):
            logging.debug("ClntMeth: %-30s %6d" % (clntMeth,
                                                   self.clntMeth2callCount[clntMeth]))

        for wrapMeth in sorted(self.wrapMeth2callCount.keys()):
            logging.debug("WrapMeth: %-30s %6d" % (wrapMeth,
                                                   self.wrapMeth2callCount[wrapMeth]))

    def dumpReqAnsErrSituation(self):
        logging.debug("%s\t%s\t%s\t%s" % ("ReqId", "#Req", "#Ans", "#Err"))
        for reqId in sorted(self.reqId2nReq.keys()):
            nReq = self.reqId2nReq.get(reqId, 0)
            nAns = self.reqId2nAns.get(reqId, 0)
            nErr = self.reqId2nErr.get(reqId, 0)
            logging.debug("%d\t%d\t%s\t%d" % (reqId, nReq, nAns, nErr))

    @iswrapper
    # ! [connectack]
    def connectAck(self):
        if self.asynchronous:
            self.startApi()

    # ! [connectack]

    @iswrapper
    # ! [nextvalidid]
    def nextValidId(self, orderId: int):
        # If I'm the only person using this, the num will always be "1"
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        # ! [nextvalidid]

        # we can start now
        self.start()

    def completedOrdersEnd(self):
        newlogger.debug("completedOrdersEnd() : Receieved!")

    def start(self):
        """ """
        msg = f'TWS_API_APP.start() : Processing: "{self.which}"'
        newlogger.debug("-" * len(msg))
        newlogger.debug(msg)
        newlogger.debug("-" * len(msg))

        # -------------------------------------------------------------------------------------------------------------------
        if self.which == "GET MULTIPLES":
            if not get_last_update("IB account summaries"):  # self.things_requested[reqId] = 1 for four accounts
                self.GET_ACCOUNT_SUMMARIES()  # sets last update in CHECK_FOR_TIME_TO_DISCONNECT(
            if not get_last_update("IB get orders"):  # self.things_requested["IB get orders"] = 1
                self.GET_ORDERS()
            if not get_last_update("IB get positions"):  # self.things_requested["Positions"]
                self.GET_POSITIONS()
            if not get_last_update("IB get prices"):  # a 'pricereq' with a 'seconds until stale'
                self.GET_PRICES()
            if not get_last_update("IB get executions"):  # Receives execDetailsEnd(     Sets last update there
                self.GET_EXECUTIONS()
            if not get_last_update("IB request PNL"):  # Data goes to     pnl(        Sets last update there
                self.GET_PNL()
            if not get_last_update(
                    "IB option greeks"):  # Not in here, because if nothing to do it needs to raise an error
                try:
                    self.ct_greeksFromConids()  # why different from    def IB_get_option_greeks(    ???
                except IB_NOTHING_TO_DO:
                    raise
            return True
        # -------------------------------------------------------------------------------------------------------------------

        # Matching symbols: "Stock contract search"
        elif self.which == "IB stock contract search":
            self.ct_stock_find_matching_symbols()

        # Options and greeks:
        elif self.which == "IB option prices":
            self.ct_option_prices()

        elif self.which == "IB option greeks":
            self.ct_greeksFromConids()

        elif self.which == "IB option greeks - LIVE":
            self.ct_greeksFromConids()
            # myjoe()  #  was turned off for a long time. Do I need it??

        elif self.which == "IB option contract details":
            self.getOptionDefinitions()  # _chains_ of options

        elif self.which == "IB get specific option definitions":
            self.getSpecificOptionDefinitions()  # _SPECIFIC_ ones!

        elif self.which == "IB get stock holiday details":
            self.get_stock_contract_definitions()

        elif self.which == "IB account summaries":
            self.GET_ACCOUNT_SUMMARIES()

        elif self.which == "IB get orders":
            self.GET_ORDERS()

        elif self.which == "IB get positions":
            self.GET_POSITIONS()

        elif self.which == "IB get prices":
            self.GET_PRICES()

        elif self.which == "IB get completed orders":
            self.ct_get_completed_orders(apiOnly=False)

        elif self.which == "IB get executions":
            self.GET_EXECUTIONS()

        elif self.which == "IB request PNL":
            self.GET_PNL()

        # -------------------------------------------------------------------------------------------------------------------
        elif self.which == "IB get dividends":
            self.ct_getDividends()  # Note: IB deprecated this!!!!!!
            # self.ct_getDividends_priceRequest()
            raise NotImplemented

        elif self.which == "IB_CANCEL_ALGO_ORDERS":
            self.things_requested["IB get executions"] = 1  # because there's no "End()" fn for cancel orders???
            self.ct_cancel_algo_orders()


        # -------------------------------------------------------------------------------------------------------------------
        # self.which in ["CREATE_REMAINING_ORDERS",
        #            "CREATE_ALL_BIDS",
        #            "IB create orders",
        #            "IB create orders from json file",
        #            "CREATE_ORDERS",
        #            "CREATE_CONID_BID_ORDERS",
        #            "CREATE_DIV_CAP_ORDERS",
        #            "CREATE_STOP_LOSSES",
        #            "CREATE_BUY_DIPS"]:
        #
        # elif self.which[:7] == "CREATE_":   # or self.which in ["IB create orders", "IB create orders from json file"]:
        # self.TRADING_CREATE_ORDERS()
        # -------------------------------------------------------------------------------------------------------------------

        elif self.which == "IB_CANCEL_ALL_ORDERS":
            # self.cancelOrder(self.simplePlaceOid)  reqId there
            newlogger.warning("start(2): CANCELLING ALL ORDERS - START")
            self.reqGlobalCancel()
            self.disconnect()
            newlogger.warning("start(3): CANCELLING ALL ORDERS - FINISH")

        elif self.which in ["CREATE_ORDERS"]:
            self.TRADING_CREATE_ORDERS()

        elif self.which in ["CREATE_ORDERS_BY_TICKER"]:
            self.TRADING_CREATE_ORDERS_BY_TICKER()

        elif self.which == "IB historical data":
            self.historicalDataOperations_req()

        else:
            print(f"\n\t*** start(4): Unknown option: '{self.which}'\n")
            raise UserWarning

        # self.tickOptionComputations_req(2000)
        # self.optionsOperations_req()
        # self.contractOperations()
        # self.tickOptionComputations_req()
        # self.optionsOperations_req()
        # self.contractOperations()
        # self.tickDataOperations_req()
        # self.marketDepthOperations_req()
        # self.realTimeBarsOperations_req()us
        # self.marketScannersOperations_req()
        # self.fundamentalsOperations_req()
        # self.bulletinsOperations_req()
        # self.newsOperations_req()
        # self.miscelaneousOperations()
        # self.linkingOperations()
        # self.financialAdvisorOperations()
        # self.rerouteCFDOperations()
        # self.marketRuleOperations()
        # self.histogramOperations_req()
        # self.continuousFuturesOperations_req()
        # self.whatIfOrderOperations()
        # self.historicalTicksOperations()
        # self.tickByTickOperations_req()
        # newlogger.debug("Executing requests - FINISHED")
        return

    def ct_stock_find_matching_symbols(self):
        """ THis is to hopefully find preferred shares for stocks """
        from time import sleep
        # https://interactivebrokers.github.io/tws-api/matching_symbols.html
        #                                                                                                ---->   def symbolSamples
        print(f"ct_stock_find_matching_symbols(): ", end='')              # <-----
        #
        qry = f"select distinct ticker, name from tbl_positions where good_position and secType='STK' and last_got_stock_details!='{TODAY}' " \
              f"order by ticker desc"
        res = sql_execute(qry)
        ct = 0
        for ticker, name in res:
            ct += 1
            self.reqId = self.nextOrderId()
            #
            match_contract = Contract()
            match_contract.symbol = ticker  # note: different from actual request below!
            #
            match_request = myRequest.timed_StockContractRequest(self.reqId, match_contract, "reqMatchingSymbols", None, TWS_obj=self)
            #
            msg = f"is a '{ticker}: {name}' reqMatchingSymbols(myRequest.timed_StockContractRequest) request (1 second pause now)"
            debugMsg(self.reqId, "ct_stock_find_matching_symbols()", msg)
            print(". ", end='')                                           # <-----
            self.all_requests[self.reqId] = match_request
            self.reqMatchingSymbols(self.reqId, name)  # note: different from .symbol above!
            self.reqId += 1
            self.IB_TIMEOUT += 1
            sleep(1)
        print(); myjoe(); myjoe()
        return

    @iswrapper
    # ! [symbolSamples]
    def symbolSamples(self, reqId: int, contractDescriptions: ListOfContractDescription):
        # List of TWS Basic Contracts:
        #   https://interactivebrokers.github.io/tws-api/basic_contracts.html
        super().symbolSamples(reqId, contractDescriptions)  # -->                  def did_I_get_stale(
        the_request = self.all_requests[reqId]
        the_request.gotGoodPrice = True  # they all come at once
        llen = len(contractDescriptions)
        if llen != 0:
            debugMsg(reqId, "symbolSamples(0a)", f"'{the_request.ticker}' Received #{llen} securities")
        else:
            infoMsg(reqId, "symbolSamples(0b)", f"'{the_request.ticker}' Received #{llen} securities??")
        #
        known_secTypes = {"FUT": "Future", "OPT": "Option", "WAR": "Warrant",
                          "FOP": "Futures Options", "BAG": "Straddle, other Combo",
                          "CFD": "Contract for Differences",  "IOPT": "Dutch Warrants and Structured Products",
                          }
        found_something_new = False
        for contractDescription in contractDescriptions:
            the_request.received += 1
            derivSecTypes = ""
            for derivSecType in contractDescription.derivativeSecTypes:
                if derivSecType not in known_secTypes:
                    found_something_new = True
                    myjoe("Found preferred stock yet?")
                derivSecTypes += derivSecType
                derivSecTypes += " "
            conId = contractDescription.contract.conId
            if conId == "139808284":
                myjoe("Got MS PRF!")
            symbol = contractDescription.contract.symbol
            secType = contractDescription.contract.secType
            primaryExchange = contractDescription.contract.primaryExchange
            currency = contractDescription.contract.currency
            putCall = contractDescription.contract.right
            #
            if found_something_new:
                infoMsg(reqId, "symbolSamples(1)", f"Received #{the_request.received}: {symbol=:10}, {conId=:9}, {secType=}, {primaryExchange=}, {currency=}, {derivSecTypes=}")

            # "multiplier", "right", "symbol"
            contract_fields = ["comboLegs", "comboLegsDescrip", "conId", "currency", "deltaNeutralContract", "exchange",
                               "includeExpired", "lastTradeDateOrContractMonth", "localSymbol", "primaryExchange",
                               "secId", "secIdType", "secType", "strike", "tradingClass"]
            #
            params = create_A_Param("tbl_IB_stock_matching_symbols",
                                                    {"contract": contractDescription.contract.__str__(),
                                                     "ticker": symbol,
                                                     "putCall": putCall,
                                                     "derivSecTypes": derivSecTypes})
            for field in contract_fields:
                res = eval(f"contractDescription.contract.{field}")
                if res:
                    params.param_dict[field] = res
            if contractDescription.contract.multiplier:
                params.param_dict["multiplier"] = float(contractDescription.contract.multiplier)
            #
            params.processThis()
            #
            if params.msg == "added":
                msg = f"{symbol=:6}, {conId=:9}, {currency=}, {secType=}, {primaryExchange=}, {derivSecTypes=}"
                debugMsg(reqId, "symbolSamples(2)", f"tbl_IB_stock_matching_symbols added: {msg}")
                joe = 12
            if params.msg == "updated":
                debugMsg(reqId, "symbolSamples(3)",
                         f"tbl_IB_stock_matching_symbols(): Ticker: '{symbol}', conId: '{conId}', was {params.msg} - {params.update_msg}")
                joe = 12
            joe = 12
        return

    def GET_EXECUTIONS(self):
        # NOTE: "Important: only those executions occurring since midnight for that particular account will be delivered.
        #        Older executions will generally not be available via the TWS API with IB Gateway."
        #        See also: reqCompletedOrders(                                  ----->          def execDetails(
        self.things_requested["IB get executions"] = 1
        debugMsg(self.reqId, "GET_EXECUTIONS()", f"Is a 'reqExecutions' request for executions")
        self.reqExecutions(self.reqId, ExecutionFilter())  # Receives an "execDetailsEnd" message
        return

    def ct_cancel_algo_orders(self):
        # https://interactivebrokers.github.io/tws-api/cancel_order.html
        qry = "select reqId, permId, secType, ticker, expiry, strike, putCall, account, action, quantity, lmtPrice " \
              "from ALGO_ORDERS where is_live=True"
        res = sql_execute(qry)
        for reqId, permId, secType, ticker, expiry, strike, putCall, account, action, quantity, lmtPrice in res:
            # self.cancelOrder(orderId)  # Does not work
            whatAmI = f"'{quantity} {ticker} {strike} {expiry} {putCall} @ {lmtPrice:,.2f}' reqId: {reqId} permId: {permId} " \
                      f"secType: {secType} account: {account} action: {action}"
            newlogger.info(f"ct_cancel_algo_orders(1): Cancelling: {whatAmI}")
            self.cancelOrder(reqId)  # works
            uqry = f"update ALGO_ORDERS set is_live=False where reqid={reqId}"
            ures = sql_execute(uqry)
        self.things_requested["IB get executions"] = 0
        myjoe()
        return

    def keyboardInterrupt(self):
        ignores = ["run", "sendMsg", "serverVersion", "setConnState", "startApi", "connect", "isConnected",
                   "logRequest", "msgLoopRec", "msgLoopTmo", "disconnect", "reset"]
        # TODO: Make this part of "All requests good, stale, or errored"? Meaning: When I exit from there, say what fns were called?
        for key, val in self.clntMeth2callCount.items():
            if key in ignores:
                continue
            if val != 0:
                # print(f"keyboardInterrupt(1): {val} - {key}")
                if self.DEBUG:
                    newlogger.debug(f"keyboardInterrupt(1): IB methods used: {val} - {key}")
                # myjoe()  #
        for key, val in self.things_requested.items():
            if val != 0:
                # print(f"keyboardInterrupt(2): {self.things_requested}: Key {key} - {val}")
                if self.DEBUG:
                    newlogger.info(f"keyboardInterrupt(2): My python code request: Key={key} - {val} !")
        # = True
        sys.exit()

    def stop(self):
        """
        print("Executing cancels")
        #self.orderOperations_cancel()
        self.accountOperations_cancel()
        self.tickDataOperations_cancel()
        self.tickOptionComputations_cancel()
        #self.marketDepthOperations_cancel()
        #self.realTimeBarsOperations_cancel()
        #self.historicalDataOperations_cancel()
        self.optionsOperations_cancel()
        #self.marketScanners_cancel()
        #self.fundamentalsOperations_cancel()
        #self.bulletinsOperations_cancel()
        #self.newsOperations_cancel()
        #self.pnlOperations_cancel()
        #self.histogramOperations_cancel()
        #self.continuousFuturesOperations_cancel()
        self.tickByTickOperations_cancel()
        print("Executing cancels ... finished")
        """
        raise NotImplementedError

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    @iswrapper
    def error(self, reqId:TickerId, errorCode:int, errorString:str):
        """ This is my main error code, inside ct_Program.py
            https://interactivebrokers.github.io/tws-api/message_codes.html
        """
        error_dict = {
            177 : "No security definition has been found for the request",
            200 : "Bad contract description, give more/better data",
            300 : "Can't find EId with ticker Id (cancelling a market data request)",
            320 : "Server error when reading an API client request",
            321 : "Server error when validating an API client request. When the local symbol field is empty, please fill the following fields (right, strike, expiry)",
            322 : "Server error",
            430 : "The fundamentals data for the security specified is not available.Not allowed'",
            504 : "Not connected. You are trying to perform a request without properly connecting and/or after connection to the TWS. has been broken probably due to an unhandled exception within your client application",
            1100 : "Connectivity between IB and the TWS has been lost. Your TWS/IB Gateway has been disconnected from IB servers. This can occur because of an internet connectivity issue, a nightly reset of the IB servers, or a competing session",
            1101 : "Connectivity between IB and TWS has been restored- data lost. The TWS/IB Gateway has successfully reconnected to IB's servers. Your market data requests have been lost and need to be re-submitted",
            1102 : "Connectivity between IB and TWS has been restored- data maintained. The TWS/IB Gateway has successfully reconnected to IB's servers. Your market data requests have been recovered and there is no need for you to re-submit them",
            1300 : "TWS socket port has been reset and this connection is being dropped. Please reconnect on the new port - <port_num>",
        }
        connection_ok = {
              -1 : "Market data farm connection is OK",
            2104 : "A notification that connection to the market data server is ok. This is a notification and not a true error condition, and is expected on first establishing connection",
            2105 : "HMDS data farm connection is broken:ushmds",
            2106 : "A notification that connection to the market data server is ok. This is a notification and not a true error condition, and is expected on first establishing connection",
            2108 : "A market data farm connection has become inactive but should be available upon demand",
            2158 : "A notification that connection to the Security definition data server is ok. This is a notification and not a true error condition, and is expected on first establishing connection",
        }
        if errorCode in connection_ok:
            return

        if errorCode in error_dict:
            reason = error_dict[errorCode]
            print(f"\t*** error(0): ErrorCode: {errorCode} : {reason}")
        else:
            # A new (to me) error was tripped, how should I handle it?
            myjoe(errorCode)
        #
        params = create_A_Param("tbl_errors")
        #
        aDict = {"reqId": reqId, "ticker": "", "contract": "", "errorCode": errorCode, "errorString": errorString}
        params.updateFromDict(aDict)
        #
        if reqId not in self.all_requests:
            super().error(reqId, errorCode, errorString)  # this goes to STDERR, in red
            newlogger.error(f"error(1): MISSING reqId: {reqId}, errorCode: {errorCode}, errorString: '{errorString}'")
            params.processThis()
            return

        the_request = self.all_requests[reqId]
        ticker = the_request.ticker
        the_contract = the_request.contract
        exchange = the_request.contract.exchange
        primary = the_request.contract.primaryExchange
        currency = the_request.contract.currency
        params.param_dict["ticker"] = ticker
        params.param_dict["contract"] = the_contract
        params.param_dict["tws_request"] = the_request.calling_func  # ="reqContractDetails"
        #
        params.processThis()
        #
        if errorCode == 300:
            newlogger.error(f"error(2): reqId: {reqId}: {ticker:5}: errorCode: 300 [{errorString}] [{self.all_requests[reqId].contract}]")
            return  # should I still set its errorCode and String?  No, because the original request is fine,
            # it's only the *cancelling* of the request that didn't work

        # If I errror on an option request, keep track of bad ones:
        if isinstance(the_request, myRequest.timed_OptionContractRequest):
            self.processBadOptionRequest(the_request, the_contract, errorCode, errorString)

        if errorCode in [177, 200]:
            myjoe("")  # work on code 200, as STT has no more August contracts, this is ok
            # 177   : No security definition has been found for the request
            # 200   : Bad contract description, give more/better data
            print(f"error(3): reqId: {reqId:4}, errorCode: {errorCode}: {errorString}. Contract: [{the_contract}]")
            newlogger.error(f"error(3): reqId: {reqId:4}, errorCode: {errorCode}: {errorString}. Contract: [{the_contract}]")
            self.processBadOptionRequest(the_request, the_contract, errorCode, errorString)
        else:
            newlogger.error(f"error(4): reqId: {reqId:4}: errorCode: #{errorCode} - [{errorString}] - ({ticker}.{exchange}.{primary})")

        if ticker not in self.badTickers:
            self.badTickers.append(ticker)

        self.all_requests[reqId].errorCode = errorCode
        self.all_requests[reqId].errorString = errorString
        self.CHECK_FOR_TIME_TO_DISCONNECT()
        return

    def processBadOptionRequest(self, request, p_contract, errorCode, errorString):
        contract = request.contract
        if p_contract != contract:
            myjoe("why not?")
        if contract.secType == "STK":
            # not for here, just care about options going into this table
            myjoe("")
            return False
        primary = request.contract.primaryExchange
        if isinstance(contract, Contract):
            contractName = contract.__str__()
        else:
            raise UserWarning
        aa, ticker, secType, expiry, strike, putCall, bb, exchange, p_exch, currency, *the_rest = contractName.split(
            ",")
        #
        params = create_A_Param("tbl_IB_bad_option_specs")
        params.updateFromDict({"ticker": ticker,
                               "contract": contract,
                               "strike": contract.strike,
                               "putCall": contract.right,
                               "errorCode": errorCode,
                               "errorString": errorString,
                               "exchange": exchange,
                               "primary_exchange": primary or p_exch,
                               "currency": currency,
                               "expiry": expiry,
                               "IB_expiry": expiry.replace("-", ""),
                               "fixed": False})
        params.processThis()
        #
        if params.msg == "added":
            infoMsg(
                f"processBadOptionRequest(1): tbl_IB_bad_option_specs(1): [{ticker}] was {params.msg} - {params.update_msg}")
        if params.msg == "updated":
            debugMsg(
                f"processBadOptionRequest(2): tbl_IB_bad_option_specs(1): [{ticker}] was {params.msg} - {params.update_msg}")
        return

    @iswrapper
    def winError(self, text: str, lastError: int):
        super().winError(text, lastError)

    @iswrapper
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):  # HERE
        """ """
        if "IB get orders" not in self.things_requested:
            from_connecting_to_IB = True
        else:
            from_connecting_to_IB = False

        super().openOrder(orderId, contract, order, orderState)
        order.contract = contract
        strike = contract.strike
        QTY = int(order.totalQuantity)
        msg = f"'{contract.symbol}': {order.action} {QTY:3} {contract.secType} {order.orderType} ${order.lmtPrice:.2f} for IB account {order.account} " \
              f"(permId: {order.permId}, conId: {contract.conId}, reqId: {orderId})"
        if contract.secType == "OPT":
            msg += f" ${strike:6,.2f} strike {contract.right}"

        newlogger.debug(f"openOrder(1): Received: {msg}")
        self.upload_IB_order(orderId, order, contract, orderState, from_connecting_to_IB)
        self.upload_IB_orderState(orderId, orderState)
        self.permId2ord[order.permId] = order
        # set_last_update("IB get orders")  note: Do not do this, this gets set in the "openOrderEnd()" call/message
        return

    def upload_IB_order(self, reqId, order: Order, contract: Contract, orderState: OrderState,
                        from_connecting_to_IB: bool):
        # https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
        """ NOTE: For an existing manual order in TWS, if I futz with one of them, and then retrieve orders again
                  THEY WILL BE ASSIGNED A NEW REQID!!!!!!!!!!!!!
        """
        #
        params = create_A_Param("tbl_IB_orders")
        #
        # TODO: Look for some kind of "when placed" date value, then use it in 'Orders and Trades' report
        permId = order.permId
        ticker = contract.symbol
        params.param_dict["ticker"] = ticker  # TODO: How do I know if an order I'm working is using an IB algo?
        params.param_dict["currency"] = contract.currency
        params.param_dict["orderId"] = reqId
        params.param_dict["reqId"] = reqId
        params.param_dict["secType"] = contract.secType
        params.param_dict["exchange"] = contract.exchange
        params.param_dict["lastUpdate"] = get_sql_now()
        params.param_dict["status"] = orderState.status
        params.param_dict["is_live"] = True
        if order.goodAfterTime:
            params.param_dict["goodAfterTime"] = order.goodAfterTime
        # All orders:
        params.no_zeros("conId", str(contract.conId))
        orderFields = ["permId", "account", "action", "orderType", "totalQuantity", "cashQty", "lmtPrice", "auxPrice",
                       "clientId", "lmtPrice"]
        for field in orderFields:
            res = eval(f"order.{field}")
            params.param_dict[field] = res
        totalQuantity = params.param_dict["totalQuantity"]  # 100
        action = params.param_dict["action"]  # BUY

        # OPTIONS:
        if contract.secType == "OPT":
            expiry = convert_date(contract.lastTradeDateOrContractMonth)
            IBcontract = makeIBContract(contract)
            params.no_zeros("contract", IBcontract)
            optionContractFields = ["secType", "strike", "comboLegs", "comboLegsDescrip", "deltaNeutralContract",
                                    "includeExpired", "lastTradeDateOrContractMonth", "localSymbol", "multiplier",
                                    "primaryExchange", "secId", "secIdType", "tradingClass"]
            for field in optionContractFields:
                val = eval(f"contract.{field}")
                if val in variables.UNSET_VALUES:
                    myjoe()
                params.no_zeros(field, eval(f"contract.{field}"))
            params.no_zeros("putCall", contract.right)
            params.no_zeros("symbol", contract.symbol)
            params.param_dict["conId"] = str(contract.conId)
            params.param_dict["expiry"] = convert_date(contract.lastTradeDateOrContractMonth)
            params.param_dict["IB_expiry"] = contract.lastTradeDateOrContractMonth

        # Make sure all order fields are uploaded:
        dodgy_fields = ["adjustedStopLimitPrice", "adjustedStopPrice", "adjustedTrailingAmount", "basisPoints",
                        "delta", "deltaNeutralAuxPrice", "filledQuantity", "lmtPriceOffset", "nbboPriceCap",
                        "percentOffset", "scalePriceAdjustValue", "scalePriceIncrement", "scaleProfitOffset",
                        "startingPrice", "stockRangeLower", "stockRangeUpper", "stockRefPrice",
                        "trailStopPrice", "trailingPercent", "triggerPrice", "volatility"]

        for field in dir(order):
            if field.find("__") != -1:
                continue
            if field not in params.param_dict:
                val = eval(f"order.{field}")
                # FIXME: Use "UNSET_DOUBLE" or "UNSET_INTEGER" or "Double.MAX_VALUE ?  https://groups.io/g/twsapi/topic/92528405
                if val not in variables.UNSET_VALUES:
                    if field in dodgy_fields:
                        _joe = 12
                    if field != "rule80A":  # this is '0'
                        params.no_zeros(field, val)
                    else:
                        if val != '':
                            params.param_dict[field] = val

        # All negative reqIds come from manual orders in IB
        params.param_dict["ALGO_ORDER"] = bool(reqId > 0)
        #
        params.processThis()
        #
        msg = f"IB {order.account}, {order.action} {order.totalQuantity} {contract.symbol:4} {contract.secType} {contract.strike}"
        if params.msg == "added":
            debugMsg(reqId, "upload_IB_order(1)", f"tbl_IB_orders: [{msg}] was added")
        elif params.msg == "updated":
            debugMsg(reqId, "upload_IB_order(2)", f"tbl_IB_orders: [{msg}] was updated: {params.update_msg}")
        if params.msg in ["added", "updated"]:
            if self.which not in ["CREATE_ORDERS"]:
                self.MD.ib_etrade.IB_things["IB get orders"]["got_fresh_data"] = True
        #
        # -------------------------------------------------------------------------------------------------------------------
        # Now check to update ALGO_ORDERS
        # -------------------------------------------------------------------------------------------------------------------
        """
        make a check that yesterday's order has been executed, or cancelled, or SOMETHING!
        this will prevent orders not being downloaded from IB (like on the 13th when it took a 2nd download to get them)
        1) I have orders in ALGO_ORDERS ... so what happened to them?
        2) I get data from IB and into: tbl_IB_orders,
                                        tbl_IB_orders_status
        3) I also have                  tbl_IB_executions
        4) Do this for each day, an ALGO_ORDER can be made on Monday, downloaded from IB tuesday, but then not on Wednesday
        """
        ALGO_ORDERS = create_A_Param("ALGO_ORDERS")  # , {"fn": "upload_IB_order"})
        ALGO_ORDERS.updateFromDict({"reqId": reqId,
                                    "account": order.account,
                                    "is_live": True,
                                    "last_live_check": get_sql_curtime(),
                                    })
        for field in ["ticker", "secType", "action", "conId", "permId", "lmtPrice", "IB_expiry"]:
            if field in params.param_dict:
                ALGO_ORDERS.param_dict[field] = params.param_dict[field]
        if params.param_dict["secType"] == "OPT":
            for opt_field in ["strike", "putCall", "expiry", "IB_expiry"]:
                ALGO_ORDERS.param_dict[opt_field] = params.param_dict[opt_field]
            strike = ALGO_ORDERS.param_dict["strike"]
            putCall = ALGO_ORDERS.param_dict["putCall"]
        ALGO_ORDERS.param_dict["quantity"] = params.param_dict["totalQuantity"]

        assert contract.secType in ["STK", "OPT"]  # , "CASH"]
        if contract.secType == "STK":
            curdate_qry = f"SELECT curdate FROM ALGO_ORDERS WHERE ticker='{ticker}' and secType='STK' and account='{order.account}' and action='{action}' and quantity={totalQuantity} ORDER BY curdate desc"
        #elif contract.secType == "CASH":
        #    curdate_qry = f"SELECT curdate FROM ALGO_ORDERS WHERE ticker='{ticker}' and secType='CASH' and account='{order.account}' " \
        #                  f"and action='{action}' and quantity={totalQuantity} ORDER BY curdate desc"
        else:
            curdate_qry = f"SELECT curdate FROM ALGO_ORDERS WHERE ticker='{ticker}' and secType='OPT' and expiry='{expiry}' and strike={strike} and putCall='{putCall}' and account='{order.account}' " \
                          f"and action='{action}' and quantity={totalQuantity} ORDER BY curdate desc"
        curdate_res = sql_execute(curdate_qry)
        if len(curdate_res) > 1:
            ALGO_ORDERS.param_dict["curdate"] = curdate_res[0]
        elif len(curdate_res) == 1:
            ALGO_ORDERS.param_dict["curdate"] = curdate_res[0]
        elif len(curdate_res) == 0:
            ALGO_ORDERS.param_dict["curdate"] = TODAY
        else:
            print(f"\n\t{curdate_qry}")
            raise UserWarning

        _open_algos = f"select * from ALGO_ORDERS where permId not in (select permId from tbl_IB_executions) order by curtime desc"

        _executed = f"select curdate, ticker, secType, putCall, permId, side, shares, cumQty, shares-cumQty as leaves " \
                    f" from tbl_IB_executions order by curdate desc"

        _CHECK_CODE_QUERY = f"select permid, * from ALGO_ORDERS " \
                            f"where permId not in (select permId from tbl_IB_executions) " \
                            f"and permId not in (select permId from tbl_IB_orders) " \
                            f"order by curtime desc"
        #
        ALGO_ORDERS.DEBUG = True
        ALGO_ORDERS.updateOnly(logIt=True)  #  not from_connecting_to_IB)
        #
        return

    def upload_IB_orderState(self, orderId: OrderId, orderState: OrderState):
        # ticker!
        params = create_A_Param("tbl_IB_orderState")
        params.updateFromDict({"orderId": orderId, "reqId": orderId})

        # 'ticker' / 'contract' info gets returned with the order itself. Here I just have the reqId for it (like -129)
        params.param_dict["status"] = orderState.status
        params.param_dict["warningText"] = orderState.warningText
        params.param_dict["completedTime"] = orderState.completedTime
        params.param_dict["completedStatus"] = orderState.completedStatus
        params.param_dict["commissionCurrency"] = orderState.commissionCurrency
        #
        # FIXME: Use "UNSET_DOUBLE" or "UNSET_INTEGER" or "Double.MAX_VALUE ?  https://groups.io/g/twsapi/topic/92528405
        #
        dodgyFields = ["initMarginBefore", "maintMarginBefore", "equityWithLoanBefore", "initMarginChange",
                       "maintMarginChange", "equityWithLoanChange", "initMarginAfter", "maintMarginAfter", "equityWithLoanAfter"]
        for field in dodgyFields:
            res2 = eval(f"orderState.{field}")
            if res2 not in variables.UNSET_VALUES:  #  != "1.7976931348623157E308":
                myjoe("This is supposed to be a dodgy field, why do I have a good value now?")
                params.param_dict[field] = res2
        #
        floatFields = ["commission", "minCommission", "maxCommission"]
        for field in floatFields:
            res3 = eval(f"orderState.{field}")
            if res3 not in variables.UNSET_VALUES:
                myjoe()
                params.param_dict[field] = res3
        #
        params.processThis()
        if params.msg in ["added", "updated"]:
            debugMsg(orderId, "upload_IB_orderState", f"tbl_IB_orderState was {params.msg}: {params.update_msg}")
        #
        return

    @iswrapper
    def openOrderEnd(self):
        # Fixme: Why does it only get AMZN before turning off?
        #set_last_update("IB get orders")
        super().openOrderEnd()
        if self.things_requested.get("IB get orders", 0) == 0:
            # This is the automatic one when IB is first connected to (only retrieves orders the API sent though, not manual ones)
            newlogger.debug(f"openOrderEnd(1): (received {len(self.permId2ord)} open orders when connecting to IB)")
            newlogger.debug("")
        else:
            self.things_requested["IB get orders"] -= 1
            newlogger.debug(f"openOrderEnd(2): Received {len(self.permId2ord)} open orders")
        return

    @iswrapper
    # ! [orderstatus]
    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining,
                            avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        # if "IB get orders" not in self.things_requested.keys():
        #    # This is the automatic one when IB is connected to
        #    return

        # msg = f"PermId: {permId}, orderId: {orderId}, ParentId: {parentId}, Status: {status}, Filled: {filled}, Remaining: {remaining}, AvgFillPrice: {avgFillPrice}, " \
        #      f"LastFillPrice: {lastFillPrice}, ClientId: {clientId}, WhyHeld: " \
        #  ticker!

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
        #
        params = create_A_Param("tbl_IB_order_status")
        dataDict = {
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
        }
        params.updateFromDict(dataDict)
        params.processThis()
        if params.msg == "added":
            debugMsg(orderId, "orderStatus(1)", msg)
        elif params.msg == "updated":
            # Something changed with the message!
            newlogger.debug(f"orderStatus(2): {msg} was updated:")
            newlogger.debug(f"orderStatus(3): {params.update_msg}")
        return

    # ! [orderstatus]

    def GET_ACCOUNT_SUMMARIES(self):
        # See also: EClient.reqAccountUpdates()
        # Returns data via: updateAccountValue() --> ct_updateAccountValue() --> tbl_account_summary
        # TODO: Can I use 'frozen' prices, ie, only last night's close?
        self.accountSummariesNeeded = {
            9001: "$LEDGER:BASE",
            9002: "$LEDGER:USD",
            9003: "$LEDGER:EUR",
            9004: "$LEDGER:GBP",
        }
        reqId = list(self.accountSummariesNeeded.keys())[0]
        self.things_requested[reqId] = 1
        self.reqAccountSummary(reqId, "All", "$LEDGER:BASE")  # ---> accountSummary()     accountSummaryEnd()
        # --------------------------------------------------------------
        return

    def GET_POSITIONS(self):
        #                                               ---> def position(
        #
        self.things_requested["Positions"] = self.things_requested.get("Positions", 0) + 1
        newlogger.debug("GET_POSITIONS()")  # -->                                  positionEnd(
        self.reqPositions()
        #
        # Turn off old options:
        qry = f"select * from tbl_positions where secType='OPT' and expiry<'{TODAY}' and good_position"
        res = sql_execute(qry)
        if res:
            uqry = f"update tbl_positions set good_position=False where secType='OPT' and expiry<'{TODAY}'"
            ures = sql_execute(uqry)
            #
        return

    @printWhenExecuting
    def accountOperations_cancel(self):
        # ! [cancelaaccountsummary]
        self.cancelAccountSummary(9001)
        self.cancelAccountSummary(9002)
        self.cancelAccountSummary(9003)
        self.cancelAccountSummary(9004)
        # ! [cancelaaccountsummary]

        # ! [cancelaaccountupdates]
        self.reqAccountUpdates(False, self.account)
        # ! [cancelaaccountupdates]

        # ! [cancelaaccountupdatesmulti]
        self.cancelAccountUpdatesMulti(9005)
        # ! [cancelaaccountupdatesmulti]

        # ! [cancelpositions]
        self.cancelPositions()
        # ! [cancelpositions]

        # ! [cancelpositionsmulti]
        self.cancelPositionsMulti(9006)
        # ! [cancelpositionsmulti]

    def GET_PNL(self):
        #                                                        ----->                      EWrapper.pnl()
        # https://groups.io/g/twsapi/topic/92300827
        self.reqId += 1
        reqDict = {7864219: "U7864219"}  # ,           10144028: "U10144028"}
        for reqId, account in reqDict.items():
            pnlRequest = myRequest.timed_PnlRequest(reqId=reqId, account=account, calling_func="pnlOperations_req",
                                                    TWS_obj=self)
            #
            self.all_requests[reqId] = pnlRequest
            debugMsg(reqId, "GET_PNL(2)", f"[is a timed_PnlRequest for account {account}")
            self.reqPnL(reqId, account, "")
        return

    def pnlOperations_cancel(self):
        # ! [cancelpnl]
        self.cancelPnL(17001)
        # ! [cancelpnl]

        # ! [cancelpnlsingle]
        self.cancelPnLSingle(17002)
        # ! [cancelpnlsingle]

    def histogramOperations_req(self):
        # ! [reqhistogramdata]
        self.reqHistogramData(4002, ContractSamples.USStockAtSmart(), False, "3 days")
        # ! [reqhistogramdata]

    def histogramOperations_cancel(self):
        # ! [cancelhistogramdata]
        self.cancelHistogramData(4002)
        # ! [cancelhistogramdata]

    def continuousFuturesOperations_req(self):
        # ! [reqcontractdetailscontfut]
        self.reqContractDetails(18001, ContractSamples.ContFut())
        # ! [reqcontractdetailscontfut]

        # ! [reqhistoricaldatacontfut]
        timeStr = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d %H:%M:%S')
        self.reqHistoricalData(18002, ContractSamples.ContFut(), timeStr, "1 Y", "1 month", "TRADES", 0, 1, False, [])
        # ! [reqhistoricaldatacontfut]

    def continuousFuturesOperations_cancel(self):
        # ! [cancelhistoricaldatacontfut]
        self.cancelHistoricalData(18002)
        # ! [cancelhistoricaldatacontfut]

    @iswrapper
    def managedAccounts(self, accountsList: str):
        # Receives a comma-separated string with the managed account ids. Occurs automatically on initial API client connection.
        super().managedAccounts(accountsList)
        self.allAccounts = accountsList.split(",")
        if accountsList != "U10144028,U7864219,":
            newlogger.debug(f"Account list: [{accountsList}]")
        # self.account = accountsList.split(",")[0]

    @iswrapper
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        super().accountSummary(reqId, account, tag, value, currency)
        self.ct_updateAccountSummary(reqId, account, tag, value, currency)

    def ct_updateAccountSummary(self, reqId: int, account: str, field: str, value: str, currency: str):
        """ MARGIN: Long stock requirement    30%
                    Short stock requirement   30%
                    Naked option requirement: 20%
        """
        if value.isnumeric() and float(value) == 0:
            debugMsg(reqId, "ct_updateAccountSummary()", f"Skipping value=0 for {account}, {field}, {currency}'")
            return
        #
        params = create_A_Param("tbl_account_summary")
        #
        params.param_dict["broker"] = "IB"  # reqId
        params.param_dict["account"] = account
        params.param_dict["field"] = field
        params.param_dict["currency"] = currency
        if field == "InsuredDeposit" and value != '':
            print("\n\t*** ct_updateAccountSummary() : I'm getting 'InsuredDeposit' values now!")
            raise UserWarning
        # params.param_dict["value"] = value
        params.no_zeros("value", value)
        #
        params.processThis()
        #
        if params.msg == "added":
            if value != "0.00":
                debugMsg(reqId, "IB_accountSummary(1)",
                         f"Account: {account:9}, Currency: {currency}, Field: {field}, Value: {value}")
            if account == "U10144028" and isinstance(value, (float, int)) and value != 0:
                myjoe()  # Got data for it!!
        elif params.msg == "updated":
            msg = f"Account: {account:9}, Currency: {currency}, Field: {field}, Currency: {currency} was updated: {params.update_msg}"
            debugMsg(reqId, "IB_accountSummary(2)", msg)
        if params.msg in ["added", "updated"]:
            self.MD.ib_etrade.IB_things["IB account summaries"]["got_fresh_data"] = True
        return

    @iswrapper
    def accountSummaryEnd(self, reqId: int):
        super().accountSummaryEnd(reqId)
        if self.DEBUG and not self.STAY_ALIVE:
            debugMsg(reqId, f"accountSummaryEnd()", f"(cancelling acccountSummary for {reqId:5})")
        debugMsg(reqId, "accountSummaryEnd()", f"(cancelling accountSummary() request #{reqId:5})")
        self.cancelAccountSummary(reqId)

        if reqId in self.things_requested:
            self.things_requested[reqId] -= 1
        self.accountSummariesNeeded.pop(reqId, None)
        if not self.accountSummariesNeeded:
            # All done
            set_last_update("IB account summaries")
            return
        keys = list(self.accountSummariesNeeded.keys())
        reqId = keys[0]
        which = self.accountSummariesNeeded[reqId]
        self.things_requested[reqId] = 1  # why am I setting this ===============1 here?
        newlogger.debug("")
        debugMsg(reqId, "accountSummaryEnd()", f"Making a new reqAccountSummary() reqId #{reqId} of 'All', {which})")
        self.reqAccountSummary(reqId, "All", which)

        return

    @iswrapper
    # ! [updateaccountvalue]
    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        super().updateAccountValue(key, val, currency, accountName)
        if self.ct_updateAccountValue(key, val, currency, accountName):
            pass

    # ! [updateaccountvalue]

    @iswrapper
    # ! [updateportfolio]
    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        super().updatePortfolio(contract, position, marketPrice, marketValue,
                                averageCost, unrealizedPNL, realizedPNL, accountName)
        newlogger.debug(
            f"updatePortfolio() : Symbol: {contract.symbol}, SecType: {contract.secType}, Exchange: {contract.exchange}, "
            f"Position: {position}, MarketPrice: {marketPrice}, MarketValue: {marketValue}, AverageCost: {averageCost}, "
            f"UnrealizedPNL: {unrealizedPNL}, RealizedPNL: {realizedPNL}, AccountName: {accountName}")
        myjoe("")

    # ! [updateportfolio]

    @iswrapper
    # ! [updateaccounttime]
    def updateAccountTime(self, timeStamp: str):
        super().updateAccountTime(timeStamp)

    # ! [updateaccounttime]

    @iswrapper
    # ! [accountdownloadend]
    def accountDownloadEnd(self, accountName: str):
        super().accountDownloadEnd(accountName)
        newlogger.debug(f"AccountDownloadEnd() : Account: {accountName}")
        if "AccountDownload" in self.things_requested:
            self.things_requested["AccountDownload"] -= 1
        self.CHECK_FOR_TIME_TO_DISCONNECT()

    # ! [accountdownloadend]

    @iswrapper
    # ! [position]
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        super().position(account, contract, position, avgCost)
        self.update_tbl_positions(account, contract, position, avgCost, self.STAY_ALIVE)
        return

    def update_tbl_positions(self, account, contract, position, avgCost, stayAlive):
        ticker = contract.symbol
        secType = contract.secType
        conId = contract.conId
        whatAmI = f"{account}.{ticker}.{secType}.{position:,.2f}"
        if ticker == '':
            qry = f"SELECT ticker FROM tbl_tickers WHERE conId={contract.conId}"
            ticker = sql_fetchone(qry)
            if ticker:
                # Just check why I'm here. conId 484941544 == "XOM", the assigned option trade. What is "171945408"??????????
                myjoe()
            else:
                print(f"Add conId={contract.conId} to tbl_tickers")
                raise UserWarning

        # check quantity, do not automatically turn good_position on
        # "tradedate_mmddyyyy": tradedate_mmddyyyy,
        # "tradedate_ddmmyyyy": tradedate_ddmmyyyy,
        # TRADING_NOTES!
        params = create_A_Param("tbl_positions")  # income????
        if ticker == "MS PRF":
            params.param_dict["isin"] = "US61763E2072"
            params.param_dict["conId"] = "139808284"
        else:
            params.param_dict["conId"] = ticker
        params.param_dict["trading_notes"] = get_last_note(ticker, "trading_notes")
        params.param_dict["notes"] = get_last_note(ticker, "notes")
        params.param_dict["last_div_update"] = get_last_div_update(ticker)
        params.param_dict["divsPerYear"] = divsPerYear(ticker)
        params.param_dict["only_IB"] = ticker in ["MS PRF"]
        if int(position) != position:
            myjoe()  # now what? I have fractional shares
        params.param_dict["shares"] = position
        params.param_dict["is_an_ETF"] = ticker in self.ETFs
        params.param_dict["tradedate"] = trading.get_trade_date(ticker)
        params.param_dict["broker"] = "IB"
        params.param_dict["last_update"] = TODAY
        # Fixme: add divYield
        ldu = get_last_div_update(ticker)
        params.param_dict["last_div_update"] = ldu
        params.param_dict["IB"] = True
        params.param_dict["name"] = company_names[ticker]
        params.param_dict["shortName"] = company_names[ticker]

        # if bool(position) is False:
        #    raise UserWarning  # Whut?
        params.param_dict["good_position"] = bool(position)
        params.param_dict["pays_dividends"] = ticker not in ['AMZN', 'GOOG', 'MTCH', 'PYPL', 'KD']
        params.no_zeros("ticker", ticker)
        params.no_zeros("secType", secType)
        if secType == "OPT":
            IB_expiry = contract.lastTradeDateOrContractMonth  # input(f"\nPlease enter the expiration for {whatAmI}: ")
            expiry = f"{IB_expiry[:4]}-{IB_expiry[4:6]}-{IB_expiry[6:8]}"
            params.param_dict["expiry"] = expiry
            params.param_dict["IB_expiry"] = expiry.replace("-", "")
            params.no_zeros("multiplier", float(contract.multiplier))
            params.param_dict["name"] = whatAmI
            params.param_dict["shortName"] = whatAmI
        params.no_zeros("account", account)
        params.no_zeros("currency", contract.currency)
        params.no_zeros("cost_basis", avgCost)
        if secType == "OPT" and contract.conId:
            # I only want conId when it is an option!
            params.param_dict["conId"] = str(contract.conId)
        # params.no_zeros("exchange", contract.exchange)  overwrites "SMART" with "NASDAQ"
        # params.no_zeros("multiplier", float(contract.multiplier))
        params.no_zeros("primary_exchange", contract.primaryExchange)
        params.no_zeros("putCall", contract.right)
        params.no_zeros("strike", contract.strike)
        # params.param_dict["positionId"] = None  positionId is a crap field from ETrade, and no longer part of the Unique Key here
        # params.param_dict["tradedate"] = input(f"Please give me a tradedate for: [{THISPOSITION}] YYYY-MM-DD :    ")
        #
        params.processThis()
        #
        if contract.secType == "CASH":
            return
        if params.msg == "added":
            msg = f"update_tbl_positions(1): tbl_positions {TODAY} Added: Account: {account}, SecType: {contract.secType}, " \
                  f"Symbol: {contract.symbol:6}, Currency: {contract.currency}, Position: {position:5.1f}, Avg cost: {avgCost:5.2f}"
            newlogger.debug(msg)
            # See if I need to get option contract data for this as well:
            qry = f"select * from tbl_IB_option_contract_details where ticker='{ticker}'"
            res = sql_execute(qry)
            if not res:
                reset_last_update("IB option contract details")
        elif params.msg == "updated":
            newlogger.debug(f"update_tbl_positions(2): {whatAmI}: {params.update_msg}")
        if params.msg in ["added", "updated"]:
            self.MD.ib_etrade.IB_things["IB get positions"]["got_fresh_data"] = True

        return

    """
    def sendTelegramText(self, msg, printIt=True):
        # Look in myCode for original pyTelegramBotAPI() 
        my_id = 1710461519
        if self.GLOBAL_BOT_TWS:
            self.GLOBAL_BOT_TWS.send_message(my_id, msg)
        if printIt:
            newlogger.debug(msg)
    """

    def ct_updateAccountValue(self, key, val, currency, accountName):
        """ Called from 'updateAccountValue() """
        if key == 'ExchangeRate' and val != 0:
            self.ct_update_exchange_rates(currency, val)

        params = Parameters("tbl_account_summary", "ct_updateAccountValue")
        params.param_dict["account"] = accountName
        params.param_dict["field"] = key
        params.param_dict["currency"] = currency
        #
        _res = params.processThis()
        #
        # if res:
        #    msg, field_dict, defaults_dict, constraint_arr, differences_dict = res

    @staticmethod
    def ct_update_exchange_rates(from_currency, rate, to_currency=''):
        qry = f"SELECT * from tbl_exchange_rates WHERE curdate='{TODAY}' AND from_currency='{from_currency}' AND to_currency='{to_currency}'"
        res = sql_fetchone(qry)
        if res is None:
            # Add it
            qry = f"INSERT INTO tbl_exchange_rates (curdate, from_currency, rate) " \
                  f"VaLUES ('{TODAY}', '{from_currency}', {rate})"
            sql_execute(qry)

    @iswrapper
    # ! [positionend]
    def positionEnd(self):
        super().positionEnd()
        newlogger.debug("PositionEnd() : received")
        if self.things_requested.get("Positions", 0) != 0:
            self.things_requested["Positions"] -= 1
        self.CHECK_FOR_TIME_TO_DISCONNECT()
        return

    @iswrapper
    # ! [positionmulti]
    def positionMulti(self, reqId: int, account: str, modelCode: str,
                      contract: Contract, pos: float, avgCost: float):
        super().positionMulti(reqId, account, modelCode, contract, pos, avgCost)
        debugMsg(reqId, "PositionMulti()",
                 f"Account: {account}, ModelCode: {modelCode}, Symbol: {contract.symbol}, SecType: {contract.secType}, "
                 f"Currency: {contract.currency}, Position: {pos}, AvgCost: {avgCost}")
        self.cancelPositionsMulti(reqId)

    # ! [positionmulti]

    @iswrapper
    # ! [positionmultiend]
    def positionMultiEnd(self, reqId: int):
        super().positionMultiEnd(reqId)
        newlogger.debug(f"{reqId:5} ct PositionMultiEnd. RequestId: {reqId:5}")
        if "PositionsMulti" in self.things_requested:
            self.things_requested["PositionsMulti"] -= 1
        self.CHECK_FOR_TIME_TO_DISCONNECT()

    # ! [positionmultiend]

    @iswrapper
    # ! [accountupdatemulti]
    def accountUpdateMulti(self, reqId: int, account: str, modelCode: str,
                           key: str, value: str, currency: str):
        super().accountUpdateMulti(reqId, account, modelCode, key, value, currency)
        newlogger.debug(f"AccountUpdateMulti. RequestId: {reqId:5}, Account: {account}, ModelCode: {modelCode}, "
                        f"Key: {key}, Value: {value}, Currency: {currency}")

    # ! [accountupdatemulti]

    @iswrapper
    # ! [accountupdatemultiend]
    def accountUpdateMultiEnd(self, reqId: int):
        super().accountUpdateMultiEnd(reqId)
        newlogger.debug(f"AccountUpdateMultiEnd. RequestId: {reqId:5}")

    # ! [accountupdatemultiend]

    @iswrapper
    # ! [familyCodes]
    def familyCodes(self, familyCodes: ListOfFamilyCode):
        super().familyCodes(familyCodes)
        print("Family Codes:")
        for familyCode in familyCodes:
            print("FamilyCode.", familyCode)

    # ! [familyCodes]

    @iswrapper
    # ! [pnl]
    def pnl(self, reqId: int, dailyPnL: float, unrealizedPnL: float, realizedPnL: float):
        """  came here from:                           def GET_PNL(
            self.reqPnL(17219, "U7864219", "")
            self.reqPnL(17028, "U10144028", "")
        """
        super().pnl(reqId, dailyPnL, unrealizedPnL, realizedPnL)
        if reqId not in self.all_requests:
            print(f"Missing reqId: {reqId}!")
            myjoe()  #
        the_request = self.all_requests[reqId]
        the_request.setGotGoodPrice("pnl")
        debugMsg(reqId, "pnl(1)", f"Setting gotGoodPrice=True")
        if the_request.cancelled is False:
            the_request.cancelled = True
            self.cancelPnL(reqId)
            newlogger.debug(f"Sent cancelPnL for reqId #{reqId}")
            set_last_update("IB request PNL")

        msg = f"pnl() : Daily PnL Received: ReqId: {reqId}, DailyPnL: ${dailyPnL:,.2f}, UnrealizedPnL: ${unrealizedPnL:,.2f}, RealizedPnL: ${realizedPnL:,.2f}"
        if not realizedPnL:
            newlogger.debug(msg)
        else:
            newlogger.warning(msg)
        #
        params = create_A_Param("tbl_account_PnL")
        params.updateFromDict({"account": self.account, "dailyPnL": dailyPnL,
                               "unrealizedPnL": unrealizedPnL, "realizedPnL": realizedPnL})
        params.processThis()

    # ! [pnl]

    @iswrapper
    # ! [pnlsingle]
    def pnlSingle(self, reqId: int, pos: int, dailyPnL: float,
                  unrealizedPnL: float, realizedPnL: float, value: float):
        super().pnlSingle(reqId, pos, dailyPnL, unrealizedPnL, realizedPnL, value)
        print("Daily PnL Single. ReqId:", reqId, "Position:", pos,
              "DailyPnL:", dailyPnL, "UnrealizedPnL:", unrealizedPnL,
              "RealizedPnL:", realizedPnL, "Value:", value)

    # ! [pnlsingle]

    def marketDataTypeOperations(self):
        # https://interactivebrokers.github.io/tws-api/market_data_type.html
        # Switch to:
        #   "1" live
        #   "2" frozen
        #   "3" delayed
        #   "4" delayed frozen
        self.reqMarketDataType(MarketDataTypeEnum.FROZEN)  # DELAYED)
        # ! [reqmarketdatatype]

    @iswrapper
    # ! [marketdatatype]
    def marketDataType(self, reqId: TickerId, marketDataType: int):
        super().marketDataType(reqId, marketDataType)

    # ! [marketdatatype]

    @printWhenExecuting
    def tickDataOperations_req(self, numId):
        self.reqMarketDataType(MarketDataTypeEnum.FROZEN)  # DELAYED)

        # Requesting real time market data

        # ! [reqmktdata]
        self.reqMktData(1000, ContractSamples.USStockAtSmart(), "", False, False, [])
        self.reqMktData(1001, ContractSamples.StockComboContract(), "", False, False, [])
        # ! [reqmktdata]

        # ! [reqmktdata_snapshot]
        self.reqMktData(1002, ContractSamples.FutureComboContract(), "", True, False, [])
        # ! [reqmktdata_snapshot]

        # ! [regulatorysnapshot]
        # Each regulatory snapshot request incurs a 0.01 USD fee
        self.reqMktData(1003, ContractSamples.USStock(), "", False, True, [])
        # ! [regulatorysnapshot]

        # ! [reqmktdata_genticks]
        # Requesting RTVolume (Time & Sales) and shortable generic ticks
        self.reqMktData(1004, ContractSamples.USStockAtSmart(), "233,236", False, False, [])
        # ! [reqmktdata_genticks]

        # ! [reqmktdata_contractnews]
        # Without the API news subscription this will generate an "invalid tick type" error
        self.reqMktData(1005, ContractSamples.USStockAtSmart(), "mdoff,292:BRFG", False, False, [])
        self.reqMktData(1006, ContractSamples.USStockAtSmart(), "mdoff,292:BRFG+DJNL", False, False, [])
        self.reqMktData(1007, ContractSamples.USStockAtSmart(), "mdoff,292:BRFUPDN", False, False, [])
        self.reqMktData(1008, ContractSamples.USStockAtSmart(), "mdoff,292:DJ-RT", False, False, [])
        # ! [reqmktdata_contractnews]

        # ! [reqmktdata_broadtapenews]
        self.reqMktData(1009, ContractSamples.BTbroadtapeNewsFeed(), "mdoff,292", False, False, [])
        self.reqMktData(1010, ContractSamples.BZbroadtapeNewsFeed(), "mdoff,292", False, False, [])
        self.reqMktData(1011, ContractSamples.FLYbroadtapeNewsFeed(), "mdoff,292", False, False, [])
        # ! [reqmktdata_broadtapenews]

        # ! [reqoptiondatagenticks]
        # Requesting data for an option contract will return the greek values
        self.reqMktData(1013, ContractSamples.OptionWithLocalSymbol(), "", False, False, [])
        self.reqMktData(1014, ContractSamples.FuturesOnOptions(), "", False, False, [])

        # ! [reqoptiondatagenticks]

        # ! [reqfuturesopeninterest]
        self.reqMktData(1015, ContractSamples.SimpleFuture(), "mdoff,588", False, False, [])
        # ! [reqfuturesopeninterest]

        # ! [reqmktdatapreopenbidask]
        self.reqMktData(1016, ContractSamples.SimpleFuture(), "", False, False, [])
        # ! [reqmktdatapreopenbidask]

        # ! [reqavgoptvolume]
        self.reqMktData(1017, ContractSamples.USStockAtSmart(), "mdoff,105", False, False, [])
        # ! [reqavgoptvolume]

        # ! [reqsmartcomponents]
        # Requests description of map of single letter exchange codes to full exchange names
        self.reqSmartComponents(1018, "a6")
        # ! [reqsmartcomponents]

        # ! [reqetfticks]
        self.reqMktData(1019, ContractSamples.etf(), "mdoff,576,577,578,623,614", False, False, [])
        # ! [reqetfticks]

    def GET_PRICES(self):
        # -->       tickPrice()             receives the info from IB
        # -->       update_tbl_prices()     gathers up the tick data until has everything
        # -->       updatePrices()          writes to tbl_prices
        """
            https://interactivebrokers.github.io/tws-api/market_data_type.html
            MarketDataTypeEnum = Enum("N/A", "REALTIME", "FROZEN", "DELAYED", "DELAYED_FROZEN")

            REALTIME	1	Live streaming data relayed back in real time
            FROZEN		2	Last data recorded at market close
            DELAYED		3	Free, delayed data is 15 - 20 minutes delayed
            DELAYED FROZEN	4	For a user without market data subscriptions
        """
        if NYSE_is_Open():
            self.reqMarketDataType(MarketDataTypeEnum.REALTIME)
            debugMsg("GET_PRICES() : Using REALTIME prices")
            thingsNeeded = {"close", "last", "bid", "ask"}
        else:
            self.reqMarketDataType(MarketDataTypeEnum.FROZEN)
            debugMsg("GET_PRICES() : Using FROZEN prices")
            thingsNeeded = {"close"}
        # todo: switch to REALTIME?
        newlogger.debug("GET_PRICES() : Requesting Market Data from IB .. START  ***********************************")
        self.no_tickSize = True
        ct = 0
        if not self.tickerList:
            self.tickerList = self.tickerDATA_TWS.get_IB_pricing_tickers()
            if not self.tickerList:
                raise IB_NOTHING_TO_DO(True)

        self.num_requests = len(self.tickerList)
        tickerList = self.tickerList
        if len(self.tickerList) > 50:
            myjoe("Why so many to get??")

        # Get max ticker len for formatting
        max_width = 0
        for row in tickerList:
            ticker, *junk = row
            max_width = max(max_width, len(ticker))
        for row in tickerList:
            self.reqId += 1
            reqId = self.reqId

            ticker, secType, isin, conId, putCall, strike, expiry, currency, exchange, primary = row
            if secType == "OPT" and expiry < TODAY:
                continue

            contract = Contract()
            contract.symbol = ticker  # "IBM"  (must be set even when doign ISIN)
            if conId != ticker:
                contract.conId = conId
            contract.secType = secType  # "STK", "OPT", "FUND"
            contract.currency = currency  # "USD"
            contract.exchange = exchange  # "SMART"
            if primary:
                contract.primaryExchange = primary  # NASDAQ
            if secType == "OPT":
                contract.conId = conId  # 484941544  (XOM call)
                contract.strike = strike
                contract.right = putCall
                contract.lastTradeDateOrContractMonth = expiry  # yyyymmdd
            if currency != "USD":  # or ticker == "MS PRF":
                contract.secIdType = "ISIN"
                contract.secId = isin
            #
            pricereq = myRequest.timed_PriceRequest(reqId, contract, "GET_PRICES", thingsNeeded,
                                                    self)  # <------------------------
            pricereq.note = ticker
            #
            self.all_requests[reqId] = pricereq
            SUS = pricereq.seconds_until_stale
            # msg = f"is a timed_PriceRequest for: {pricereq.what_am_i()} using reqMktData({pricereq.seconds_until_stale}). Looking for: {pricereq.thingsNeeded}"
            _ticker = f"'{ticker}'"
            msg = f"is a timed_PriceRequest({SUS}) for: {_ticker:{max_width}} using reqMktData({pricereq.seconds_until_stale}). " \
                  f"Looking for: {pricereq.thingsNeeded}"
            debugMsg(reqId, "GET_PRICES(1)", msg)
            self.reqMktData(reqId, contract, "", False, False, [])
            ct += 1

        self.allTickersHaveBeenRequested = True
        # self.computeTimeOutLength("GET_PRICES")
        newlogger.debug("GET_PRICES() : Requesting Market Data from IB .. FINISH ***********************************")
        newlogger.debug("")
        if ct == 0:
            raise IB_NOTHING_TO_DO(True)
        return

    def GET_PRICES_live(self):  # , ticker_res):
        """ Original function is: tickDataOperations_req() """
        # -->       tickPrice()             receives the info from IB
        # -->       update_tbl_prices()     gathers up the tick data until has everything
        # -->       updatePrices()          writes to tbl_prices

        self.reqMarketDataType(MarketDataTypeEnum.REALTIME)
        # MarketDataTypeEnum = Enum("N/A", "REALTIME", "FROZEN", "DELAYED", "DELAYED_FROZEN")

        # 'close' stays the same regardless of call, and 'last' updates last
        # if self.which == "IB get prices":
        #    self.reqMarketDataType(MarketDataTypeEnum.FROZEN)  # (REALTIME, FROZEN, DELAYED, DELAYED FROZEN)
        # elif self.which == "IB get live prices":
        #    self.reqMarketDataType(MarketDataTypeEnum.REALTIME)
        # else:
        #    raise UserWarning

        newlogger.debug(
            "GET_PRICES_live() : Requesting Market Data from IB .. START  ***********************************")
        self.no_tickSize = True
        # If bid and ask come in, that's great, but don't wait 30 seconds for them
        ct = 0
        if not self.tickerList:
            # self.tickerList = DataObj("GET_PRICES_live").get_IB_pricing_tickers()
            self.tickerList = self.tickerDATA_TWS.get_IB_pricing_tickers()
        self.num_requests = len(self.tickerList)
        tickerList = self.tickerList
        for row in tickerList:
            ticker, secType, isin, conId, putCall, strike, expiry, currency, exchange, primary = row
            if secType == "OPT" and expiry < TODAY:
                continue

            contract = Contract()
            contract.symbol = ticker  # "IBM"  (must be set even when doign ISIN)
            contract.secType = secType  # "STK", "FUND"
            contract.currency = currency  # "USD"
            contract.exchange = exchange  # "SMART"
            if primary:
                contract.primaryExchange = primary  # NASDAQ
            if secType == "OPT":
                contract.conId = conId  # 484941544  (XOM call)
                contract.strike = strike
                contract.right = putCall
                contract.lastTradeDateOrContractMonth = expiry  # yyyymmdd https://interactivebrokers.github.io/tws-api/classIBApi_1_1Contract.html#a1f8ef7a93e053e20235e9e0ba272b646
            if currency != "USD":  # or ticker == "MS PRF":
                contract.secIdType = "ISIN"
                contract.secId = isin
            #
            reqId = self.reqId
            live_pricereq = myRequest.live_priceRequest(reqId, contract, "GET_PRICES_live",
                                                        self)  # <------------------------
            live_pricereq.note = ticker
            #
            self.all_requests[reqId] = live_pricereq
            debugMsg(reqId, "GET_PRICES_live(1)",
                     f"is a live_priceRequest for: {live_pricereq.what_am_i():26}  using reqMktData().")
            self.reqMktData(reqId, contract, "", False, False, [])
            self.reqId += 1
            ct += 1

        self.allTickersHaveBeenRequested = True
        # self.computeTimeOutLength("GET_PRICES")
        newlogger.debug(
            "GET_PRICES_live() : Requesting Market Data from IB .. FINISH ***********************************")
        newlogger.debug("")
        if ct == 0:
            raise IB_NOTHING_TO_DO(True)
        return

    @printWhenExecuting
    def tickDataOperations_cancel(self):
        # Canceling the market data subscription
        # ! [cancelmktdata]
        self.cancelMktData(1000)
        self.cancelMktData(1001)
        # ! [cancelmktdata]

        self.cancelMktData(1004)

        self.cancelMktData(1005)
        self.cancelMktData(1006)
        self.cancelMktData(1007)
        self.cancelMktData(1008)

        self.cancelMktData(1009)
        self.cancelMktData(1010)
        self.cancelMktData(1011)
        self.cancelMktData(1012)

        self.cancelMktData(1013)
        self.cancelMktData(1014)

        self.cancelMktData(1015)

        self.cancelMktData(1016)

        self.cancelMktData(1017)

        self.cancelMktData(1019)

    # @printWhenExecuting
    def tickOptionComputations_req(self, numId):
        self.reqMarketDataType(MarketDataTypeEnum.FROZEN)  # DELAYED)
        # Requesting options computations
        # self.reqMktData(numId, ContractSamples.OptionWithLocalSymbol(), "", False, False, [])  # 1000
        joe = ContractSamples.OptionWithLocalSymbol()
        #
        # Watch out for the spaces within the local symbol!
        # contract.localSymbol = "C BMW  JUL 20  4800"
        # contract.secType = "OPT"
        # contract.exchange = "DTB"
        # contract.currency = "EUR"
        # contract.localSymbol = "C AMZN  FEB 19  3270"
        #
        # OptionAtBOX():
        # contract.symbol = "GOOG"
        # contract.secType = "OPT"
        # contract.exchange = "BOX"
        # contract.currency = "USD"
        # contract.lastTradeDateOrContractMonth = "20190315"
        # contract.strike = 1180
        # contract.right = "C"
        # contract.multiplier = "100"
        #
        # OptionAtIse:
        # contract.symbol = "COF"
        # contract.secType = "OPT"
        # contract.currency = "USD"
        # contract.exchange = "ISE"
        # contract.lastTradeDateOrContractMonth = "20190315"
        # contract.right = "P"
        # contract.strike = 105
        # contract.multiplier = "100"
        #

        # "When the local symbol field is empty, please fill the following fields (right, strike, expiry)]
        contract = Contract()
        contract.symbol = "AMZN"  # "AMZN210219C03250000"
        contract.secType = "OPT"
        contract.currency = "USD"
        contract.exchange = "SMART"  # ************
        contract.lastTradeDateOrContractMonth = "20210219"
        contract.right = "C"
        contract.multiplier = "100"
        contract.strike = 3250.0

        # cont = myRequest()
        # cont.contract = contract
        # cont.note = "AMZN"
        # self.all_requests[numId] = cont
        self.reqMktData(numId, contract, "", False, False, [])  # 1000

    def ct_myreqMktData(self, reqId: TickerId, contract: Contract,
                        genericTickList: str, snapshot: bool, regulatorySnapshot: bool,
                        mktDataOptions: TagValueList):
        """ Made just so it's easier for me to search for it in code vs sample code """
        self.reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)
        return

    def ct_option_prices(self, seconds_until_stale=30):
        # use 'ct_greeksFromConids' not this
        raise UserWarning # does this get hit anymore? 8/18/2022
        # "IB option prices"
        somethingDone = False
        newlogger.debug("")
        newlogger.debug("ct_option_prices() : Sending requests for greeks to IB - START")

        greeksToGet = get_GreeksToGet()
        optionsToGet = get_GreeksToGet()

        if not seconds_until_stale:
            if NYSE_is_Open():
                seconds_until_stale = 60
            else:
                seconds_until_stale = 60  # 120

        for row in optionsToGet:
            somethingDone = True
            self.reqId += 1
            # self.reqIds(1)
            ticker, account, tradeReco, strike, putCall, expiry, conId, curdate = row
            assert expiry.find("-") == -1
            #
            acontract = Contract()
            acontract.symbol = ticker
            acontract.strike = strike
            acontract.right = putCall[0]  # ie, "C", even if it's "CALL"
            acontract.lastTradeDateOrContractMonth = expiry
            acontract.conId = conId
            acontract.secType = "OPT"
            acontract.exchange = "SMART"
            acontract.currency = "USD"
            acontract.multiplier = "100"

            # 1) Request the price of the option itself from IB (comes back with greeks during market hours!)
            """ 10: "BID_OPTION_COMPUTATION", 
                11: "ASK_OPTION_COMPUTATION",
                12: "LAST_OPTION_COMPUTATION",
                13: "MODEL_OPTION", 
            """
            thingsNeeded = {"delta", "gamma"}  # "close", "LAST_OPTION_COMPUTATION", "MODEL_OPTION"}
            priceRequest = myRequest.timed_PriceRequest(self.reqId, acontract, "reqMktData", thingsNeeded=thingsNeeded,
                                                        TWS_obj=self)
            priceRequest.account = account
            priceRequest.tradeReco = tradeReco
            priceRequest.seconds_until_stale = seconds_until_stale
            priceRequest.curdate = curdate
            #
            self.all_requests[self.reqId] = priceRequest  # Note: PRICE request!
            msg = f"conId: {conId} - '{priceRequest.what_am_i():27}' is a timed_PriceRequest({seconds_until_stale}) for: {thingsNeeded}"
            debugMsg(self.reqId, "ct_greeksFromConids(0a)", msg)
            self.ct_myreqMktData(self.reqId, acontract, "", True, False, [])  # 'True' = Just a snapshot
            #
            # see if reqMktData comes back with a impliedVol?              ---------->    tickOptionComputation( 5 )
            #
            self.reqId += 1

        # if greeksToGet:    # "Sending x requests for greeks to IB")
        #    timed_PriceRequest.printWaitingThread()
        newlogger.debug("ct_option_prices() : Sending requests for greeks to IB - FINISH")
        newlogger.debug("")
        if somethingDone is False:
            raise IB_NOTHING_TO_DO(True)
        else:
            return True

    def set_all_conIds_in_tbl_recommendations(self, cutoff):
        """ If for any reason tbl_recommendations is missing a conId, try to get it from tbl_IB_option_contract_details.
            If that is missing it too, then I need to do a request for more option contract details
        """
        #
        NEED_OPTIONS = False
        NAO = commatize(NO_AVAILABLE_OPTIONS)
        params = create_A_Param("tbl_recommendations")
        #
        missing_conIds_qry = f"select curdate, ticker, secType, putCall, expiry, strike from tbl_recommendations " \
                             f"where ticker not in ({NAO}) and curdate>='{cutoff}' and expiry>='{TODAY}' and secType='OPT' and (conId is NULL or conId='') " \
                             f"order by ticker, curdate"
        missing_conIds_res = sql_execute(missing_conIds_qry)
        for curdate, ticker, secType, putCall, expiry, strike in missing_conIds_res:
            conId_qry = f"select conId from tbl_IB_option_contract_details where ticker='{ticker}' and secType='{secType}' " \
                        f"and putCall='{putCall}' and expiry='{expiry}' and strike={strike}"
            res = sql_execute(conId_qry)
            if not res:
                pyperclip.copy(conId_qry)
                bad_qry = f"select distinct expiry from tbl_IB_bad_option_specs where ticker='{ticker}' and fixed=False and curdate='{TODAY}'"
                bad_expiry = sql_execute(bad_qry)
                if bad_expiry == expiry:
                    _joe = 12  # if I know it is a "bad_expiry" then just go on
                    continue
                newlogger.info(
                    f"Missing a conId for: ticker='{ticker}' and secType='{secType}' and putCall='{putCall}' and expiry='{expiry}' and strike={strike}")
                NEED_OPTIONS = True
                continue
            else:
                conId = res[0]
                ddict = {"curdate": curdate, "conId": conId, "ticker": ticker, "secType": secType, "putCall": putCall,
                         "expiry": expiry, "strike": strike}
                params.updateFromDict(ddict)
                #
                params.updateOnly()
                #
                if params.msg == "added":
                    debugMsg(
                        f"get_conIds_for_tbl_recommendations(1): tbl_recommendations [{ticker}] was {params.msg} - {params.update_msg}")
                if params.msg == "updated":
                    debugMsg(
                        f"get_conIds_for_tbl_recommendations(2): tbl_recommendations [{ticker}] was {params.msg} - {params.update_msg}")
                params.clear_it()
        if NEED_OPTIONS:
            reset_last_update("IB option contract details")
            params.needToProcess = False
            # raise IB_GET_OPTION_DETAILS
        #
        params.needToProcess = False
        return NEED_OPTIONS

    def ct_greeksFromConids(self):
        #myjoe("")  # only do this hourly if the NYSE market is open!
        somethingDone = False
        cutoff = get_weeks_from_now(-1)
        self.set_all_conIds_in_tbl_recommendations(cutoff)

        # data comes from 'tbl_recommendations'
        greeksToGet = get_GreeksToGet()  # cutoff)

        if not greeksToGet:
            newlogger.debug("ct_greeksFromConids() : There are no option greeks I need to get")
            raise IB_NOTHING_TO_DO(False)  # do not set last_update, as maybe recommendations haven't been made yet


        newlogger.debug("ct_greeksFromConids() : Sending requests for greeks to IB - START") Use a 'handle' for each ticker, so that 'XOM' say is always 64--  and BP is always 65-- ...


        tickerReco_arr = []
        for row in greeksToGet:
            self.reqId += 1
            ticker, account, tradeReco, strike, putCall, IB_expiry, conId = row
            if (ticker, tradeReco) in tickerReco_arr:
                myjoe("why the same ticker-Reco again?")
            tickerReco_arr.append((ticker, tradeReco))
            if not conId:
                continue
            assert IB_expiry

            badqry = f"select ticker, strike, putCall, IB_expiry from tbl_IB_bad_option_specs where ticker='{ticker}' and strike={strike} and putCall='{putCall}' and IB_expiry='{IB_expiry}'"
            badres = sql_execute(badqry)
            if badres:
                newlogger.info(
                    f"ct_greeksFromConids(x) : Skipping {ticker, strike, putCall, IB_expiry} as 'tbl_IB_bad_option_specs' knows it is a bad option request")
                continue

            assert IB_expiry.find("-") == -1
            #
            acontract = Contract()
            acontract.symbol = ticker
            acontract.strike = strike
            acontract.right = putCall[0]  # ie, 'C' for 'CALL'
            acontract.lastTradeDateOrContractMonth = IB_expiry
            if conId:
                if conId.isnumeric():
                    acontract.conId = conId
                else:
                    myjoe("why isn't it a number?")
            acontract.secType    = "OPT"
            acontract.exchange   = "SMART"
            acontract.currency   = "USD"
            acontract.multiplier = "100"

            # 1) Request the price of the option itself from IB (comes back with greeks during market hours!)
            thingsNeeded = {"delta", "gamma", "close", "last", "bid", "ask"}
            #
            endReceivedRequest = myRequest.EndReceivedRequest(reqId=self.reqId, IB_Contract=acontract,
                                                              calling_func="reqMktData", TWS_obj=self,
                                                              thingsNeeded=thingsNeeded,
                                                              endReceivedFunction=self.tickSnapshotEnd)        # ---->              def tickSnapshotEnd(
            endReceivedRequest.account = account
            endReceivedRequest.tradeReco = tradeReco
            endReceivedRequest.curdate = "WHAT IS THIS USED FOR?"
            #
            debugMsg(self.reqId, "ct_greeksFromConids(1)",
                     f"conId: {conId} - [{endReceivedRequest.what_am_i():31}] is a 'endReceivedRequest' looking for: {thingsNeeded}")   is this timed? Or can it go on forever?   I sometimes get stuck in a holding pattern...z
            #
            self.all_requests[self.reqId] = endReceivedRequest
            self.ct_myreqMktData(self.reqId, acontract, "", True, False, [])  # 'True' = Just a snapshot
            #
            somethingDone = True
            #
            # see if reqMktData comes back with a impliedVol?              ---------->    tickOptionComputation(
            #
            # self.reqId += 1

        newlogger.debug("ct_greeksFromConids() : Sending requests for greeks to IB - FINISH")
        newlogger.debug("")
        if somethingDone is False:
            raise IB_NOTHING_TO_DO(True)
        # else:
        #    set_last_reqId(self.reqId)
        return True

    def xxxxgetOpDefs(self):
        raise UserWarning  # Who is calling this?
        debug = debug or self.DEBUG
        # DETAILS RETURNED TO --> self.contractDetails()

        # This logic returns EVERY strike there is for each name
        contract_dict = {}
        qry1 = f"SELECT DISTINCT underSymbol, contractMonth FROM tbl_IB_option_contract_details"
        res1 = sql_execute(qry1)
        for row in res1:
            ticker, month = row
            if ticker not in contract_dict:
                contract_dict[ticker] = []
            contract_dict[ticker].append(month)

        next_months = next_X_months(2)

        print("getOpDefs(): Getting option contract definitions ..")
        qry2 = f"SELECT ticker, close, currency, option_exchange, option_primary_exchange, exchange, primary_exchange " \
               f"FROM tbl_positions WHERE curdate='{TODAY}' and curdate='{TODAY}' and getGreeks=True AND has_options=True"
        res2 = sql_execute(qry2)
        debugMsg(0, "getOpDefs()", f" #{len(res2)} tickers to process..")
        for row in res2:
            ticker, close, currency, option_exchange, option_primary_exchange, exchange, primary_exchange = row
            for sm in next_months:
                month, year = sm
                date = f"{year}{month:02d}"
                if ticker in contract_dict:
                    if date in contract_dict[ticker]:
                        # I already successfully did this one today
                        continue

                strike_contract = Contract()
                strike_contract.symbol = ticker
                strike_contract.secType = "OPT"
                strike_contract.exchange = option_exchange or exchange
                strike_contract.primaryExchange = option_primary_exchange or primary_exchange
                strike_contract.currency = currency  # "USD"
                strike_contract.lastTradeDateOrContractMonth = date  # "202104"
                # strike_contract.strike = strike
                strike_contract.right = "C"
                strike_contract.multiplier = "100"

                # It is not recommended to use reqContractDetails to receive complete option chains on an underlying, e.g. all combinations of strikes/rights/expiries.
                acontReq = myRequest.timed_OptionContractRequest(self.reqId, strike_contract, "reqContractDetails",
                                                                 "contract", TWS_obj=self)
                debugMsg(self.reqId, "getOpDefs()",
                         f" is a [{acontReq.what_am_i():25}] '{date}--' reqContractDetails(myRequest.timed_OptionContractRequest) request")
                # debugMsg(self.reqId, "getOpDefs()", f"[{acontReq.what_am_i():25}] is a timed_OptionContractRequest")
                # to get more details, like underConId, use: getOptionDefinitions()
                # Instead use:  (returns data to: securityDefinitionOptionParameter()
                # How do I turn it off? Do I need a +1 -1 parameter?
                # self.reqSecDefOptParams(reqId, ticker, '', "STK", underConId)
                acontReq.contract = strike_contract
                acontReq.note = ticker
                self.all_requests[self.reqId] = acontReq
                self.reqContractDetails(self.reqId, strike_contract)
                #
                self.reqId += 1
        self.computeTimeOutLength("getOpDefs")
        if self.reqId == 0:
            print(f"\ngetOpDefs(): Everything has been requested already, nothing more to do!")
            raise IB_IS_DONE(True)  # raising with '()' now, before I wasn't
        myjoe()

    # @static_vars(alreadyLogged=[])
    def getSpecificOptionDefinitions(self):
        # Reads from          --> tbl_IB_option_contracts_needed
        # DETAILS RETURNED TO --> self.contractDetails()
        #                     --> self.IB_store_contractDetails(reqId, contractDetails)
        # Receives:           contractDetailsEnd()
        # Uses    :           tbl_IB_option_contracts_needed    and    tbl_IB_option_contract_details")
        errReport, bad_requests = None, {}
        #
        bad_qry = f"SELECT ticker, IB_expiry, strike, putCall FROM tbl_IB_bad_option_specs WHERE fixed=False"
        bad_res = sql_execute(bad_qry)
        for ticker, IB_expiry, strike, putCall in bad_res:
            bad_requests[ticker, IB_expiry, strike, putCall] = 1

        IB_curdate = TODAY.replace("-", "")
        qry = f"SELECT pos.ticker, contractMonth, strike, opts.putCall, close, currency, option_exchange, option_primary_exchange, pos.exchange, primary_exchange " \
              f"FROM tbl_positions as pos, tbl_IB_option_contracts_needed as opts " \
              f"WHERE pos.is_an_ETF is False and pos.curdate='{TODAY}' and pos.good_position=True AND pos.secType='STK' AND pos.ticker = opts.ticker AND " \
              f"opts.needData=True AND pos.currency='USD' and contractMonth>='{IB_curdate}' " \
              f"ORDER BY pos.ticker"
        res = sql_execute(qry)
        if res is None:
            raise IB_NOTHING_TO_DO(True)
        somethingWasDone = False
        askedFor = {}
        for row in res:
            self.reqId += 1
            ticker, contractMonth, strike, putCall, close, currency, option_exchange, option_primary_exchange, exchange, primary_exchange = row
            #if len(contractMonth) > len("202204"):
            #    myjoe("I can't request by exact day, just month")
            if (ticker, contractMonth, strike, putCall) in bad_requests:
                continue  #  raise UserWarning  # What got tripped here? Fix it!
            #
            if (ticker, contractMonth, putCall) in askedFor:
                continue
            else:
                askedFor[ticker, contractMonth, putCall] = 1
            #
            contract = Contract()
            contract.symbol = ticker
            contract.secType = "OPT"
            contract.exchange = option_exchange or exchange
            contract.primaryExchange = option_primary_exchange or primary_exchange
            contract.currency = currency
            contract.lastTradeDateOrContractMonth = contractMonth
            contract.right = putCall
            contract.multiplier = "100"
            # contract.strike = strike  <------------------ leave blank, so I get many
            #
            # Check that this is not a known bogus contract definition:
            if self.badDefinition(contract):
                myjoe("getSpecificOptionDefinitions")  # What got tripped here? Fix it!   Uses 'tbl_IB_bad_option_specs'
            #
            # Note: It is not recommended to use reqContractDetails to receive complete option chains on an underlying,
            #       (e.g. all combinations of strikes/rights/expiries)
            # acontractRequest = myRequest.timed_OptionContractRequest(self.reqId, contract, "reqContractDetails", "contract", TWS_obj=self)
            endReceivedRequest = myRequest.EndReceivedRequest(reqId=self.reqId, IB_Contract=contract,
                                                              calling_func="reqContractDetails",
                                                              thingsNeeded={"contract"}, TWS_obj=self,
                                                              endReceivedFunction=self.contractDetailsEnd)
            #
            msg = f" is a [{endReceivedRequest.what_am_i():20}] reqContractDetails() request"
            debugMsg(self.reqId, "getSpecificOptionDefinitions(2)", msg)

            endReceivedRequest.contract = contract
            endReceivedRequest.note = ticker
            self.all_requests[self.reqId] = endReceivedRequest
            self.reqContractDetails(self.reqId, contract)
            #
            somethingWasDone = True
            # -------------------------------------------------------------------------------------------------------------------
        newlogger.debug("")
        if errReport:
            reset_last_update("Create all reports")
        if somethingWasDone is False:
            newlogger.debug(f"getSpecificOptionDefinitions() - nothing to get")
            raise IB_NOTHING_TO_DO(True)
        return

    def badDefinition(self, contract):
        qry = f"select * from tbl_IB_bad_option_specs where contract='{contract}'"
        res = sql_fetchone(qry)
        return bool(res)

    def TRADING_CREATE_ORDERS_BY_TICKER(self):
        """ """
        print(); myjoe(); myjoe()

        # TICKER:
        ticker = input("Which ticker to create an order? (BP)")
        ticker = ticker or "BP"
        ticker = ticker.upper()
        self.which = ticker

        # ACTION:
        action = input("Which direction? (BUY/SELL, 'BUY' is default)")
        action = ticker or "BUY"
        action = action.upper()

        # PUTCALL:
        putCall = input(f"Put or Call? (P/C, 'C' is default) :")
        putCall = putCall or "C"
        putCall = putCall.upper()

        # EXPIRATION:
        expiry_qry = f"select distinct expiry from tbl_IB_option_contract_details " \
                     f"where ticker='{ticker}' and putCall='{putCall}' and expiry>'{TODAY}' order by expiry"
        expiry_res = sql_execute(expiry_qry)
        expiry_one_line = ", ".join(expiry_res)
        print(f"\nExpiries for '{ticker}': {expiry_one_line}")
        # expiry = expiry_res[0]  # revert?
        expiry = input(f"Which expiry? ({expiry_res[0]}) :")
        expiry = expiry or expiry_res[0]

        # STRIKE:
        strike_qry = f"select distinct strike from tbl_IB_option_contract_details " \
                     f"where ticker='{ticker}' and putCall='{putCall}' and expiry='{expiry}' order by strike"
        strike_res = sql_execute(strike_qry)
        strike_one_line = ", ".join(map(str, strike_res))
        print(f"\nStrikes '{ticker}': {strike_one_line}")
        strike = 30  # input(f"Which strike? ({strike_res[0]}) :")
        strike = strike or strike_res[0]

        # CONID:
        conId_qry = f"select conId from tbl_IB_option_contract_details " \
                    f"where ticker='{ticker}' and putCall='{putCall}' and expiry='{expiry}' and strike={strike} order by conId"
        conId_res = sql_execute(conId_qry)
        if len(conId_res) != 1:
            raise UserWarning
        conId = conId_res[0]
        # print(conId_res)

        orderDict = one_OrderDict()
        orderDict.create_orderDict(ticker, putCall, expiry, strike, conId)
        # orderDict.SEAL_ME()
        # This is where getting a price for the option, and all that, would come in
        # TODO: Use 'OD_collection_by_key'

        dict_of_broker_collections = self.MD.ALL_ORDERDICTS.GET_ALL_ORDERDICTS_FROM_FILE()
        orderDicts_arr = self.get_orderDicts_from_dicts(ticker, dict_of_broker_collections)

        print(f"I found the following orders for '{ticker}':")
        for ct, arr in enumerate(orderDicts_arr):
            _name, orderDicts = arr
            for orderDict in orderDicts:
                whatAmI = orderDict["whatAmI"]
                name = f"'{_name}'"
                print(f"{ct + 1:2} : {name:30} : {whatAmI}")
        print(); myjoe();myjoe()
        which = int(input("Which one?")) - 1
        orderDict = orderDicts_arr[which]
        orderDict.SEAL_ME()
        whatAmI = orderDict["whatAmI"]
        print(); myjoe();myjoe()
        print(f"Found order: {whatAmI}")
        print("\t[ENTER] to skip placing this")
        print("\t[any text] to place it")
        res = input("What? ")
        if not res:
            print("\nEXITING WITH NOTHING DONE..")
            return False
        try:
            placed = self.TRADING_CREATE_ONE_IB_ORDER(orderDict)  # <--------------------------------------------
        except ValueError:
            newlogger.warning(f"TRADING_CREATE_ORDERS_BY_TICKER(1): Placing order didn't work!  {orderDict['whatAmI']}")
            newlogger.warning(f"TRADING_CREATE_ORDERS_BY_TICKER(1):                             {sys.exc_info()}")
            print(f"TRADING_CREATE_ORDERS_BY_TICKER(): Placing order didn't work!  {orderDict['whatAmI']}")
            print(f"                                                     {sys.exc_info()}")
            myjoe()
        return

    @staticmethod
    def get_orderDicts_from_dicts(ticker, adict: dict):
        assert isinstance(adict, dict)
        res_arr = []
        for brokercol_name, broker_col in adict.items():
            if ticker in broker_col:
                OD_arr = broker_col.get(ticker)
                res_arr.append((brokercol_name, OD_arr))
        return res_arr

    def TRADING_CREATE_ORDERS(self):
        # TODO: This should be in trading.py ?
        which = self.orders_to_create[7:]  # gets rid of "CREATE_"  self.which[7:]
        #
        GOFORIT_FLAG = False
        #
        assert which.find(".json") != -1
        orderFile = f"MY_ORDERS/{which}"

        newlogger.debug(f"Processing orderFile: {orderFile}")
        if not file_exists(orderFile):
            warnMsg(f"TRADING_CREATE_ORDERS(): File '{orderFile}' doesn't exist! 'Generate Reports again'?")
            raise FileExistsError
        if not file_was_made_today(orderFile):
            raise UserWarning
        # --------------------------------------------->
        orders_ARR = trading.getAndSortForTrading_fromFile(orderFile, which)
        if not orders_ARR:
            print(f"\n\t*** {self.which} - Nothing to do!")
            raise IB_NOTHING_TO_DO(False)
        #
        ct = 1
        if get_variable("PRINT_ORDERS_FIRST"):
            print(); myjoe(); myjoe()
            print("TRADING_CREATE_ORDERS(): Going to put out the following orders:")
            for orderDict in orders_ARR:
                if ct % 5 == 0:
                    print(); myjoe(); myjoe()
                whatAmI = orderDict["whatAmI"]
                print(f"\t{ct}: {whatAmI}")
                ct += 1
            print(); myjoe()
            res = input("Type 'stop' to sys.exit(), anything else will go on to being able to send orders out ..")
            if res == 'stop':
                print("\n\n\t*** Goodbye!  (sys.exit()\n")
                sys.exit()
        print(); myjoe()
        ct = 0
        totalPlaced = 0
        print(f"Processing: {self.which} on file: '{orderFile}':")
        print("[ENTER] to skip an order")
        print("[any text] to place it")
        print("'exit' to go home, or")
        print("'GOFORIT' to let them all rip ..")
        print("--------------------------------")
        ERRORS = []
        for orderDict in orders_ARR:
            ticker = orderDict["ticker"]
            whatAmI = orderDict["whatAmI"]
            #
            trading_msg = trading.checkIfTradingTicker(orderDict)
            #
            if GOFORIT_FLAG is False:
                ct += 1
                FLAG = orderDict["orderType"] == "PEG STK"
                orderDict.SEAL_ME(checkGreeks=FLAG)
                value = 0
                if orderDict["lmtPrice"]:
                    value = orderDict["QTY"] * orderDict["lmtPrice"]
                print(); myjoe()
                print("1 ------------------------------------------------------------------------------------------------------------------------")
                msg = f"(Order #{ct} of #{len(orders_ARR)}) : Value=${value:,.0f} '{whatAmI:40}'"
                if not orderDict.I_WAS_SEALED:
                    ERRORS.append((ct, whatAmI, orderDict.seal_error))
                    newlogger.warning(f"TRADING_CREATE_ORDERS(): Bad SEALING!  Error: {orderDict.seal_error}!")
                    print(msg)
                    print(f"                  : Bad SEALING!  Error: {orderDict.seal_error}!")
                    print(f"                    (skipping)")
                    print("2 ------------------------------------------------------------------------------------------------------------------------")
                    continue
                msg += " .. (type any text now to place it)"
                if bool(trading_msg):
                    msg += trading_msg
                res = input(msg)
                if not res or res.lower() == "skip":
                    print(f"\t(skipping)")
                    print("3 ------------------------------------------------------------------------------------------------------------------------")
                    continue
                if res.lower() in ["exit", "stop"]:
                    raise IB_IS_DONE(True)
                if res == "GOFORIT":
                    GOFORIT_FLAG = True
            else:
                msg = f"(Order #{ct} of #{len(orders_ARR)}) Placing: '{whatAmI:40}' .."
                if bool(trading_msg):
                    msg += trading_msg
                print(msg)
                print("4 ------------------------------------------------------------------------------------------------------------------------")
            #
            self.reqId = self.nextOrderId()
            #
            contract = trading.createContractFromOrder(orderDict)
            mainOrder, good_fields = trading.createOrder(self.reqId, orderDict)
            #
            self.ct_placeOrder_COVER(self.reqId, contract, mainOrder, orderDict, good_fields)                             # <------------------------------------------------------------------------
            totalPlaced += 1

            tradeReco = orderDict["tradeReco"]
            #if tradeReco not in USE_BRACKETS_WITH:
            #    print(f"\n\t*** Add '{tradeReco}' to USE_BRACKETS_WITH!\n")
            #    myjoe("")  #
            if USE_BRACKETS_WITH.get(tradeReco, False):
                takeProfitOrder, stopLossOrder = trading.ct_makeBracketOrders(mainOrder, Order(), Order(), orderDict["BRACKET"])
                self.ct_placeOrder_COVER(self.reqId, contract, takeProfitOrder, orderDict)                             # <------------------------------------------------------------------------
                totalPlaced += 1
                self.ct_placeOrder_COVER(self.reqId, contract, stopLossOrder, orderDict)                             # <------------------------------------------------------------------------
                totalPlaced += 1
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if totalPlaced:
            # Fixme: do this AFTER I exit this TWS call, as otherwise my 'things_requested' is all fucked
            #set_last_update("IB get orders and executions")
            backUpOrderFile(orderFile)

        if ERRORS:
            myjoe("")
            print(); myjoe()
            print("\t*** TRADING_CREATE_ORDERS():  ERRORS:")
            for row in ERRORS:
                ct, whatAmI, orderDict.seal_error = row
                print(row)
            print(); myjoe()

        raise IB_DONE_PLACING_ORDERS(totalPlaced)
        # self.disconnect()  # Note: I need this here otherwise I get caught in the message loop forever?
        # return


    def ct_placeOrder_COVER(self, reqId, contract, order, orderDict, good_fields):
        #
        tradeReco = orderDict["tradeReco"]
        whatAmI = orderDict["whatAmI"]
        #
        self.update_table_ALGO_ORDERS(reqId, contract, order, tradeReco)
        #
        orderreq = myRequest.timed_OrderRequest(reqId, "ct_placeOrder_COVER", order, contract, self)
        self.all_requests[reqId] = orderreq

        debugMsg("")

        # Fixme: How can I reflect whether the data used was able to send an order out? I'd like to keep track of 'Error Files' and 'Good Files'
        orderDict.backupToFile(good_fields)
        debugMsg(reqId, "ct_placeOrder_COVER", f"is an timed_OrderRequest for: [{orderreq.what_am_i():25}] using ct_placeOrder()")
        #
        res = self.ct_placeOrder(reqId, contract, order, whatAmI)  # <------------------------------------------------------------------------
        #

        return
        #

    #@Run_In_Debug_Mode_only
    def ct_placeOrder(self, reqId, contract, order, whatAmI):
        """ - This is the only place I should send orders out from my code
            - Also, ALL it should do is send orders out!
        """
        # Error checking:
        assert "pydevd" in sys.modules

        if contract.symbol in DO_NOT_TRADE:
            debug_print(f"ct_placeOrder(0): {self.reqId} - I am not allowed to trade {contract.symbol}!")
            raise UserWarning
        #
        debugMsg(self.reqId, "ct_placeOrder(1)", f"Placing Order: {order} / Contract: {contract}]")

        res = None
        # Immediately after the order was submitted correctly, the TWS will start sending events concerning the order's activity via IBApi.EWrapper.openOrder and IBApi.EWrapper.orderStatus
        if order.eTradeOnly:
            myjoe("")  # something is fucked
        if order.firmQuoteOnly:
            myjoe("")  # something is fucked
        goodAfterTime = order.goodAfterTime
        goodTillDate = order.goodTillDate
        tif = order.tif
        print(f"ct_placeOrder({reqId}: {goodAfterTime=}")
        print(f"ct_placeOrder({reqId}: {goodTillDate=}")
        print(f"ct_placeOrder({reqId}: {tif=}")
        try:
            res = self.placeOrder(reqId, contract, order)  # <-------------------------------
        except ValueError:
            newlogger.warning(f"ct_placeOrder(2): Placing order didn't work!  {whatAmI}")
            newlogger.warning(f"ct_placeOrder(2):                             {sys.exc_info()[:2]}")
            print(f"ct_placeOrder(3): Placing order didn't work!  {whatAmI}")
            print(f"                                                     {sys.exc_info()[0]}")
            print(f"                                                     {sys.exc_info()[1]}")
            myjoe()
        except Exception as err:
            myjoe("")
            raise

        # Fixme: Can I move this outside this function call?
        if reqId in self.all_requests:
            request = self.all_requests[reqId]
            request.setGotGoodPrice("ct_placeOrder")

        return True



    def TRADING_CREATE_ONE_IB_ORDER(self, myOrder: dict):
        """ https://interactivebrokers.github.io/tws-api/order_submission.html#submission
            https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
            https://interactivebrokers.github.io/tws-api/bracket_order.html
        """
        #Use_Brackets_With = data_file.Use_Brackets_With
        self.reqId = self.nextOrderId()
        #
        contract = trading.createContractFromOrder(myOrder)
        #
        mainOrder = trading.createOrder(self.reqId, myOrder)
        takeProfitOrder = None
        stopLossOrder = None

        tradeReco = myOrder["tradeReco"]
        if myOrder["tradeReco"] not in USE_BRACKETS_WITH:
            print(f"\n\t*** Add '{tradeReco}' to 'data_file.use_brackets_with' ??\n")
            warnMsg(f"TRADING_CREATE_ONE_IB_ORDER(): Add '{tradeReco}' to 'data_file.USE_BRACKETS_WITH' ?")
            raise UserWarning

        if USE_BRACKETS_WITH[tradeReco] is True:
            # Each of these comes with its own
            mainOrder, takeProfitOrder, stopLossOrder = trading.ct_makeBracketOrders(mainOrder, Order(), Order(), myOrder["BRACKET"])
            myjoe("What happens with self.reqId here?")
        #
        for anORDER in [mainOrder, takeProfitOrder, stopLossOrder]:
            if anORDER:
                self.update_table_ALGO_ORDERS(anORDER.orderId, contract, anORDER, tradeReco)
                orderreq = myRequest.timed_OrderRequest(anORDER.orderId, "TRADING_CREATE_ONE_IB_ORDER", anORDER, contract, self)
                self.all_requests[anORDER.orderId] = orderreq
                msg = f"is an timed_OrderRequest for: [{orderreq.what_am_i():25}] using ct_placeOrder()"
                debugMsg(anORDER.orderId, "TRADING_CREATE_ONE_IB_ORDER", msg)
                #
                # -------------------------------------------------------------------------------------------------------------------
                res = self.ct_placeOrder(anORDER.orderId, contract, anORDER)  # <------------------------------------------------------------------------
                # -------------------------------------------------------------------------------------------------------------------
                #
                joe = 12  # check what self.reqId is
            #
        return True


    def update_table_ALGO_ORDERS(self, reqId, contract: Contract, order: Order, tradeReco):
        whatAmI = f"[{contract.__str__()}] - [{order.__str__()}]"
        #
        ALGO_ORDERS = create_A_Param("ALGO_ORDERS")  # HERE
        #
        ALGO_ORDERS.param_dict["tradeReco"] = tradeReco
        ALGO_ORDERS.param_dict["from_algo"] = True
        ALGO_ORDERS.param_dict["reqId"] = reqId
        ALGO_ORDERS.param_dict["ticker"] = contract.symbol
        ALGO_ORDERS.param_dict["currency"] = contract.currency
        ALGO_ORDERS.param_dict["secType"] = contract.secType
        ALGO_ORDERS.param_dict["exchange"] = contract.exchange
        ALGO_ORDERS.param_dict["IB_expiry"] = contract.lastTradeDateOrContractMonth
        ALGO_ORDERS.param_dict["expiry"] = convert_date(contract.lastTradeDateOrContractMonth)
        ALGO_ORDERS.param_dict["strike"] = contract.strike
        ALGO_ORDERS.param_dict["putCall"] = contract.right
        ALGO_ORDERS.param_dict["account"] = order.account
        ALGO_ORDERS.param_dict["action"] = order.action
        ALGO_ORDERS.param_dict["orderType"] = order.orderType
        ALGO_ORDERS.param_dict["quantity"] = order.totalQuantity
        ALGO_ORDERS.param_dict["lmtPrice"] = order.lmtPrice   # PEG STK doesn't seem to use this
        ALGO_ORDERS.param_dict["tif"] = order.tif
        ALGO_ORDERS.param_dict["transmited"] = order.transmit
        ALGO_ORDERS.param_dict["goodAfterTime"] = order.goodAfterTime
        ALGO_ORDERS.param_dict["gtd"] = order.goodTillDate
        ALGO_ORDERS.param_dict["is_live"] = bool(order.transmit)
        #
        ALGO_ORDERS.processThis()
        #
        # Note: the problem with checking if I've already sent an order out to TWS, is that if the order
        #       hasn't been transmitted, there is not way for me to know that.
        #if ALGO_ORDERS.msg in ["silent update", "nothing to change"]:
        #    print("\n\tI think you already have this order out, but not transmitted.")
        #    joe = 12
        #    confirm = input("\tPlease confirm sending this out again? (y)")
        #    if not confirm:
        #        return False
        #    confirm = confirm.lower()
        #    if confirm[0] != "y":
        #        return False
        if ALGO_ORDERS.msg == "silent update":
            # If I restarted IB, then anything not transmitted will vanish
            newlogger.debug(
                f"update_table_ALGO_ORDERS(1): reqId: {reqId}, {whatAmI} - already in ALGO_ORDERS - but is it live??")
            return True
        elif ALGO_ORDERS.msg == "added":
            newlogger.debug(f"update_table_ALGO_ORDERS(2): reqId: {reqId}, {whatAmI} - added to ALGO_ORDERS")
            # Immediately after the order was submitted correctly, the TWS will start sending events
            # concerning the order's activity via IBApi.EWrapper.openOrder and IBApi.EWrapper.orderStatus
            return True
        elif ALGO_ORDERS.msg == "updated":
            newlogger.debug(
                f"update_table_ALGO_ORDERS(3): reqId: {reqId}, whatAmI: {whatAmI} - updated in ALGO_ORDERS: [{ALGO_ORDERS.update_msg}]")
            return 12
        else:
            newlogger.debug(
                f'update_table_ALGO_ORDERS(4): reqId: {reqId}, whatAmI: {whatAmI} - msg: {ALGO_ORDERS.msg}')
            return
        return False
        # return ALGO_ORDERS.msg, ALGO_ORDERS.update_msg

    def ct_cancelCorrect(self, reqId):
        # https://interactivebrokers.github.io/tws-api/modifying_orders.html
        # 1) It is not recommended to try to change order fields aside from order price, size, and tif (for DAY -> IOC modifications)
        #    To change other parameters, it might be preferable to instead cancel the open order, and create a new one.
        """ To modify or cancel an individual order placed manually from TWS, it is necessary to connect with client ID 0 and then bind the order
            before attempting to modify it. The process of binding assigns the order an API order ID; prior to binding it will be returned to the
            API with an API order ID of 0. Orders with API order ID 0 cannot be modified/cancelled from the API. The function reqOpenOrders binds
            orders open at that moment which do not already have an API order ID, and the function reqAutoOpenOrders binds future orders automatically.
            The function reqAllOpenOrders does not bind orders.
        """
        myjoe()  # Get this working so I can change a 0.01 order to something smarter
        return

    # @static_vars(requested_dict={})
    def getOptionDefinitions(self):
        """ gets called by          'IB option contract details'
            receives:               'contractDetailsEnd()'
            https://dimon.ca/dmitrys-tws-api-faq/#h.bmoar1a6tz2e
            conId=0                     symbol="AAPL"
            secType="OPT"               expiry="20110415"
            strike=345                  right="C"
            multiplier=""               exchange="SMART"
            primaryExchange=""          currency="USD"
            localSymbol=""              includeExpired=0
            - Or: -
            conId=0                     symbol="AAPL"
            secType="OPT"               expiry=""
            strike=0                    right=""
            multiplier=""               exchange="SMART"F
            primaryExchange=""          currency="USD"
            localSymbol="AAPL 110416C00345000"
            includeExpired=0
        """
        # DETAILS RETURNED TO -->              def contractDetails(

        contract_dict = {}
        qry = "SELECT distinct ticker, contractMonth, strike from tbl_IB_option_contract_details where secType='OPT'"
        res = sql_execute(qry)
        for row in res:
            ticker, mo, strike = row
            contract_dict[
                f"{ticker}-{mo}-{strike}"] = 1  # Note: these months are what I use to request more contract details: "202204"

        next_months = next_X_months(2)
        cutoff = get_weeks_from_now(-1)

        # First see if positions have been downloaded at all today, let along the tighter query below
        if not sql_execute(f"SELECT ticker FROM tbl_positions WHERE curdate='{TODAY}'"):
            myjoe("Why no positions downloaded yet today?")

        print("\tgetOptionDefinitions(): Getting option contract definitions ..")
        qry = f"SELECT ticker FROM tbl_positions WHERE curdate='{TODAY}' AND good_position=True " \
              f"AND secType='STK' AND has_options=True AND currency='USD' " \
              f"AND ticker not in ('xQQQ', 'xIWM') AND secType='STK' AND has_options=True AND currency='USD' ORDER BY ticker"
        tickers = sql_execute(qry)
        anythingSent = 0
        ticker_arr = []
        needed_requests = {}
        for ticker in tickers:
            ticker_arr.append(ticker)
        for ticker in ticker_arr:
            got_end_receiveds = []
            bad_expiry = []
            if ticker in data_file.NO_AVAILABLE_OPTIONS:
                continue  # <------------------------------------------
            bad_qry = f"select distinct IB_expiry from tbl_IB_bad_option_specs where ticker='{ticker}' and fixed=False and curdate='{TODAY}'"
            bad_expiries = sql_execute(bad_qry)
            for sm in next_months:
                month, year = sm
                date = f"{year}{month:02d}"
                if date in bad_expiries:
                    bad_expiry.append(date)  # <------------------------------------------
                    continue  # <------------------------------------------
                end_was_received_qry = f"select curdate, expiry from tbl_IB_option_contract_details where ticker='{ticker}' and curdate>'{cutoff}' " \
                                       f"and secType='OPT' and contractMonth='{date}' and end_received=True order by curdate"
                ewr_res = sql_fetchone(end_was_received_qry)
                if ewr_res:
                    curdate, expiry = ewr_res
                    got_end_receiveds.append(expiry)  # <-------------------------------------------
                    continue  # <-------------------------------------------
                if ticker not in needed_requests:
                    needed_requests[ticker] = []
                needed_requests[ticker].append(date)
        #for xx in ["xQQQ", "xIWM"]:
        #    if xx in needed_requests:
        #        needed_requests[xx] = [needed_requests[xx][0]]
        #                                                                      ---->       def contractDetails(
        # MAX = 25
        ct = 0
        total = len(needed_requests)
        for ticker, dates in needed_requests.items():
            for date in dates:
                ct += 1
                self.reqId += 1
                strike_contract = Contract()
                strike_contract.symbol = ticker
                strike_contract.lastTradeDateOrContractMonth = date  # eg, "202104"
                strike_contract.secType = "OPT"
                strike_contract.exchange = "SMART"
                strike_contract.currency = "USD"
                strike_contract.right = ""  # get both P/C

                # It is not recommended to use reqContractDetails to receive complete option chains on an underlying, e.g. all combinations of strikes/rights/expiries.
                # to get more details, like underConId, use: getOptionDefinitions()
                # Instead use:  (returns data to: securityDefinitionOptionParameter()
                # self.reqSecDefOptParams(reqId, ticker, '', "STK", underConId)
                # try:
                #
                anOptRequest = myRequest.EndReceivedRequest(reqId=self.reqId, IB_Contract=strike_contract,
                                                            calling_func="reqContractDetails",
                                                            TWS_obj=self, thingsNeeded={"contract"},
                                                            endReceivedFunction=self.contractDetailsEnd)
                anOptRequest.contract = strike_contract
                anOptRequest.ticker = ticker
                anOptRequest.note = f"{ct}/{total}"
                self.all_requests[self.reqId] = anOptRequest
                newlogger.debug(
                    f"getOptionDefinitions(4): reqId: {self.reqId} - is a reqContractDetails() request for '{anOptRequest.what_am_i()}' ")
                # use note to store (3/35)
                self.reqContractDetails(self.reqId, strike_contract)
                #
                anythingSent += 1
            # if ct >= MAX:
            #    newlogger.info(f"getOptionDefinitions(5): Exiting after doing MAX:{MAX} requests..")
            #    break
        if not anythingSent:
            raise IB_NOTHING_TO_DO(True)
        newlogger.debug("")
        return

    def get_stock_contract_definitions(self):
        """ gets called by          'IB get stock holiday details'
            receives:               'contractDetailsEnd()'
            See:                    self.getOptionDefinition() for more details
        """
        # DETAILS RETURNED TO -->              def contractDetails(
        # Used to stay on top of holiday trading schedules
        newlogger.debug("")
        debug_print("get_stock_contract_definitions() : Getting stock definitions ..")
        # qry = f"SELECT distinct ticker FROM tbl_positions WHERE secType='STK' AND currency='USD' and good_position ORDER BY ticker"
        qry = f"SELECT distinct ticker FROM tbl_positions WHERE secType='STK' AND currency='USD' and ticker not in ('JPM Pref', '921ESC042') " \
              f"and ticker not in (select ticker from tbl_IB_stock_contract_details where curdate='{TODAY}') ORDER BY ticker"
        res = sql_execute(qry)
        #
        anythingSent = 0
        self.reqId = self.nextOrderId()
        total = len(res)
        ct = 0
        for ticker in res:
            ct += 1
            self.reqId += 1
            contract = Contract()
            contract.symbol = ticker
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            #   ---->              def contractDetails(
            #   ---->              def contractDetailsEnd(
            endRequest = myRequest.EndReceivedRequest(reqId=self.reqId, IB_Contract=contract,
                                                        calling_func="reqContractDetails",
                                                        thingsNeeded={"contract"}, TWS_obj=self,
                                                        endReceivedFunction=self.contractDetailsEnd)
            endRequest.contract = contract
            endRequest.ticker = ticker
            endRequest.note = ticker
            self.all_requests[self.reqId] = endRequest

            # TODO: can I neaten this up? The log message is very long
            newlogger.debug(
                f"get_stock_contract_definitions(1) [{ct:2}/{total}] : reqId: {self.reqId} - is a EndReceivedRequest (reqContractDetails) (for holiday schedule): {ticker}")
            self.reqContractDetails(self.reqId, contract)
            #
            anythingSent += 1
        if not anythingSent:
            raise IB_NOTHING_TO_DO(True)
        return

    @printWhenExecuting
    def tickOptionComputations_cancel(self):
        # Canceling options computations
        # ! [canceloptioncomputations]
        self.cancelMktData(1000)
        # ! [canceloptioncomputations]

    def print_details(self, which):
        if not self.DEBUG:
            return
        ignores = ["run", "sendMsg", "serverVersion", "setConnState", "startApi", "connect", "isConnected",
                   "logRequest", "msgLoopRec", "msgLoopTmo", "disconnect", "reset"]
        for key, val in self.clntMeth2callCount.items():
            if key in ignores:
                continue
            if val != 0:
                print(f"{which:20} - {val} - {key}")
            """
            if key == "reqMktData":
                #for kk, vv in self.clntMeth2reqIdIdx.items():
                #    if vv != -1:
                #        print(f"{which:20} - reqMktData - clntMeth2reqIdIdx - {kk} - {vv}")
                for qq, ww in self.reqId2nReq.items():
                    #if ww != -1:
                    print(f"{which:20} - reqMktData - reqId2nReq - {qq} - {ww}")
            """
        for key, val in self.things_requested.items():
            print(f"{which:20} - things_requested - {val} - {key}")
        print(f"------------------------------------------------ {which}")


    @static_vars(also_received={})
    @iswrapper
    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        # comes here from                            --------------------->     def reqMktData(
        the_request = self.all_requests[reqId]
        the_contract = the_request.contract
        ticker = the_contract.symbol
        whatAmI = the_request.what_am_i()
        #
        super().tickPrice(reqId, tickType, price, attrib)

        if reqId not in self.all_requests.keys():
            infoMsg(reqId, "tickPrice",
                    f"Received after a TWS Reset was done: [tickType: {tickType}, Price: {price}, Attrib: {attrib}]")
            return

        if price <= 0:
            return  # When do I get this?
        if the_request.gotGoodPrice is True:
            return

        field = IB_tickTypes.tickTypes[tickType].lower()

        DEBUG = False
        if field not in the_request.thingsNeeded:
            # Why is 'close' getting flagged here when 'ct_greeksFromConids' is asking for it!!
            if field not in the_request.ticksReceived_dict:
                if whatAmI not in self.tickPrice.also_received:
                    self.tickPrice.also_received[whatAmI] = 1
                    if DEBUG:
                        debugMsg(reqId, "tickPrice(1)",
                                 f"[{whatAmI:25}] ALSO received: {field:5} = {price:,.4f}")  # ,.4f}")   :31
                self.tickPrice.also_received[whatAmI] = self.tickPrice.also_received.get(whatAmI, 0) + 1
                return

        if self.DEBUG:
            debugMsg(reqId, "tickPrice(2)", f"[{whatAmI:25}] received: {field:5} = ${price:,.2f}")
        #
        self.update_tbl_prices(reqId, tickType, price)
        #
        return

    """
    def update_a_price_cover(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        the_contract = self.all_requests[reqId].contract
        if the_contract.secType == "OPT":
            self.update_tbl_prices(reqId, tickType, price)  # TODO: Why do both update tbl_prices???
        elif the_contract.secType == "STK":
            self.update_tbl_prices(reqId, tickType, price)
        else:
            raise AttributeError
    """

    def update_tbl_options(self, reqId, tickType, price):
        """ At the moment this is just for options, but I should make it generic by changing what table it hits up """
        ticktype_names = {
            9: "close",
            4: "last",
            1: "bid",
            2: "ask",
            6: "high",
            7: "low",
            14: "open",
            75: "delayed close",
            68: "delayed last",
            66: "delayed bid",
            67: "delayed ask",
            72: "delayed high",
            73: "delayed low",
            76: "delayed open",
        }

        the_request = self.all_requests[reqId]
        the_contract = the_request.contract
        # fieldsThisUpdate = []
        # differences_dict = {}
        currentdt = datetime.datetime.now()
        sql_today = currentdt.strftime("%Y-%m-%d")
        ticker = the_contract.symbol
        expiry = the_contract.lastTradeDateOrContractMonth
        expiry = convert_date(expiry)
        strike = the_contract.strike
        right = the_contract.right
        #
        params = Parameters("tbl_options", "update_tbl_options")
        #
        params.updateFromDict({
            "ticker": ticker,
            "expiry": expiry,
            "strike": strike,
            "putCall": right,
            "last_optPrice_update": f"'{sql_today}'",
        })
        if tickType in [9, 75]:
            params.no_zeros("close", price)
        elif tickType in [4, 68]:
            params.no_zeros("last", price)
        elif tickType in [1, 66]:
            params.no_zeros("bid", price)
        elif tickType in [2, 67]:
            params.no_zeros("ask", price)
        elif tickType in [14, 76]:
            params.no_zeros("theopen", price)

        params.processThis()  # I need an expiry!
        if params.msg:
            debugMsg(reqId, "update_tbl_options()",
                     f"[{the_request.what_am_i():25}] was {params.msg} for {ticktype_names[tickType]}={price}  [{params.update_msg}]")

        # Cleanup housekeeping:
        if the_request.thingsNeeded == set():
            if self.DEBUG:
                debugMsg(reqId, "update_tbl_options()",
                         f"[{the_request.what_am_i():25}] turning it off, I got what I needed")
            the_request.setGotGoodPrice("update_tbl_options")
            # self.cancelMktData(reqId)  do not do this, things come afterwards and it generates an error
        self.CHECK_FOR_TIME_TO_DISCONNECT()

    def update_tbl_prices(self, reqId: TickerId, tickType: TickType, price: float):
        """
        """
        # types 66 and up are delayed quote
        tickTypes = data_file.tickTypes
        # { 9: "close", 1: "bid", 2: "ask", 4: "last", 14: "open",
        #  66: "bid", 67: "ask", 69: "last", 75: "close", 76: "open"}

        the_request = self.all_requests[reqId]
        the_contract = the_request.contract
        ticker = the_request.note
        field = IB_tickTypes.tickTypes[tickType].lower()

        # Store everything I get:
        # which = IB_tickTypes.tickTypes[tickType]  #  .lower()
        #
        the_request.ticksReceived_dict[
            field] = price  # <---- Keeps track of everything received, whether looked for or not
        #
        if field == "LAST":
            if self.DEBUG:
                debugMsg(reqId, "update_tbl_prices(0)",
                         f"Ticker: {ticker:4}, received tickType: {tickType}/{field} value ${price}..")
            tbl_alerts_params = create_A_Param("tbl_alerts")
            # New alert levels are done in ---->     def doPostSQLOperations(
            tbl_alerts_params.updateFromDict({"ticker": ticker, "last": price, "close": price})
            tbl_alerts_params.processThis(logIt=True)
        #
        # Special work for the things I'm interested in:
        if tickType in tickTypes:
            # which = tickTypes[tickType]
            if isinstance(the_request, myRequest.TimedRequest):
                # the_request.thingsWaitingOn.discard(field)
                the_request.thingsNeeded.discard(field)

        # See if I should do an update:
        if isinstance(the_request, myRequest.TimedRequest):
            # if the_request.thingsWaitingOn != set():
            if the_request.thingsNeeded != set():
                return

        # If I'm here, I should do an add/update:
        # FIXME: Move all 'updatePrices()' into a higher level class, and just set it the 'source' of the one calling it
        the_request.updatePrices()
        # the_request.gotGoodPrice = True
        return

    @iswrapper
    # ! [ticksize]
    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        if self.no_tickSize:
            # https://dimon.ca/dmitrys-tws-api-faq/#h.6vkhzpjyo34w
            # 'tickSize' always comes after tickPrice, it's a dupe, and I don't care about size anyway
            return
        super().tickSize(reqId, tickType, size)
        debugMsg(reqId, "TickSize()", f"TickType: {tickType}, Size: {size}")

    # ! [ticksize]

    @iswrapper
    # ! [tickgeneric]
    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        super().tickGeneric(reqId, tickType, value)
        if value > 0:
            debugMsg(reqId, "TickGeneric", f"TickType: {tickType}, Value: {value}")

    # ! [tickgeneric]

    @iswrapper
    # ! [tickstring]
    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        super().tickString(reqId, tickType, value)  # look for '59', dividends
        ignores = {45: "LAST_TIMESTAMP",
                   32: "BID_EXCH",
                   33: "ASK_EXCH",
                   84: "LAST_EXCH"}
        if tickType in ignores:
            return
        what = IB_tickTypes.tickTypes[tickType]
        debugMsg(reqId, "TickString", f"tickType: {tickType} ({what}), Value: {value}")

    # ! [tickstring]

    def still_need(self):
        # _still_need = [id for id, xx in self.all_requests.items() if not xx.tickSnapshotEnded]
        res_arr = []
        for reqId, request in self.all_requests.items():
            if isinstance(request, myRequest.EndReceivedRequest):
                if not request.tickSnapshotEnded:
                    res_arr.append(reqId)
        res = ", ".join(map(str, res_arr))
        return res

    @iswrapper
    # ! [ticksnapshotend]
    def tickSnapshotEnd(self, reqId: int):
        # data recived goes to                          -------------------------->   def tickPrice(
        # Note: If I received this message, but I am still looking for fields (like delta, and the market is closed)
        #        then this is not a true 'end' message that should be stored
        the_request = self.all_requests[reqId]
        ticker = the_request.ticker
        #
        if not the_request.tickSnapshotEnded:
            # Can receive two messages - like, one for the stock things, one for the option things?
            debugMsg(reqId, "tickSnapshotEnd(1)", f"Received tickSnapshotEnd() message for '{the_request.what_am_i()}'. Still waiting on reqIds: {self.still_need()}")
        #
        if isinstance(self.all_requests[reqId], myRequest.EndReceivedRequest):
            the_request.endReceived = True
            the_request.tickSnapshotEnded = True
        else:
            myjoe("TODO: improve this code (how?)")  # the_request.endReceived = True
            the_request.tickSnapshotEnded = True
        super().tickSnapshotEnd(reqId)
        if the_request.ticksReceived_dict == {}:
            # code for if an ..End() was received, but no prices were retrieved at all:
            newlogger.info(f"tickSnapshotEnd(2) : Reqid: {reqId} - [{the_request.what_am_i():31}] - Received NO DATA AT ALL before getting 'tickSnapshotEnd()'")
            joe = 12
        conId = the_request.contract.conId
        if "delta" in the_request.ticksReceived_dict and "gamma" in the_request.ticksReceived_dict:
            #myjoe("")  # check first time
            sql_execute(f"update tbl_recommendations set gotGreeks=True where ticker='{ticker}' and conId='{conId}' and curdate='{TODAY}'")
        self.CHECK_FOR_TIME_TO_DISCONNECT()


    def msgLoopTmo(self):
        # For en empty message queue (which gets hit before 'msgLoopRec' does
        #FLAG = False
        #debugMsg(self.reqId, "msgLoopTmo()", "** empty loop message received ***")
        self.CHECK_FOR_TIME_TO_DISCONNECT()
        return  # this should not get hit, no?


    def msgLoopRec(self):
        # Overloaded from "client.py"  Since this runs before I make any requests, I can't 'self.CHECK_FOR_TIME_TO_DISCONNECT()' as a default
        if self.all_requests:
            for reqId, request in self.all_requests.items():
                if request.gotGoodPrice is True or request.got_stale is True:
                    continue  # No need to process this one again
                if isinstance(request, myRequest.TimedRequest):
                    stale = request.did_I_get_stale()
                    if stale:
                        request.got_stale = stale
                        if self.DEBUG:
                            if isinstance(request, myRequest.timed_PriceRequest):
                                received = ", ".join([key for key, value in request.ticksReceived_dict.items() if value])
                                debugMsg(reqId, "msgLoopRec()", f"Request: [{request.what_am_i()}] just got stale .. (received:{received})")
                            else:
                                debugMsg(reqId, "msgLoopRec()", f"Request: [{request.what_am_i()}] just got stale")
        self.CHECK_FOR_TIME_TO_DISCONNECT()
        return

    def CHECK_FOR_TIME_TO_DISCONNECT(self):
        # ----------------------------------------------------
        def myraise(p_which, value):
            # to help with debugging when 'raise' is used here
            if p_which == IB_IS_DONE:
                # This one only gets raised at the very bottom, when absolutely everything has been checked
                raise p_which(value)
            
            if self.which == "IB get prices" and not p_which == IB_HAS_ALL_PRICES:
                newlogger.info(f"CHECK_FOR_TIME_TO_DISCONNECT.myraise(): Ignoring raise call for {p_which} during '{self.which}'")
                myjoe("")  #
                return
            if self.which == "IB request PNL" and not self.all_requests[7864219].gotGoodPrice:
                myjoe("")  #  confirm this disconnect is good  ('IB request PNL'?)
            raise p_which(value)
        # ----------------------------------------------------
        """ Check various things to see if I should disconnect from IB, and let the code continue
            Functions that receive 'End()' callbacks:
                accountUpdateMultiEnd()                     completedOrdersEnd()       positionEnd()
                contractDetailsEnd()                        execDetailsEnd()
                historicalDataEnd()                         historicalNewsEnd()
                replaceFAEnd()                              scannerDataEnd()
                securityDefinitionOptionParameterEnd()      tickSnapshotEnd()
        """
        right_now = time.time()
        time_in_secs = right_now - self.starting_time
        if time_in_secs > self.IB_TIMEOUT:
            time_in_secs = right_now - self.starting_time  # in case there's a delay responding to this too
            if self.which != "IB option contract details":
                joe = 12  # myjoe(f"Are you hanging for some reason? [{self.IB_TIMEOUT}]")
                self.IB_TIMEOUT = time_in_secs + 60
            else:
                self.IB_TIMEOUT = time_in_secs + 120

        # Note: Checking whether a request gotten stale is done in          -->        def msgLoopRec(
        #                                                                   -->        def did_I_get_stale(

        # reqIds still waiting for 'tickSnapshotEnded':
        # [id for id, xx in self.all_requests.items() if not xx.tickSnapshotEnded]

        # 1) Look for good, healthy full executions, that should set "tbl_last_updates"
        things_requested_ct = 0
        ct, SUS, good, stale, errored = 0, 0, 0, 0, 0
        snapshotended, errored = 0, 0
        TOTAL = len(self.all_requests)

        for key, val in self.things_requested.items():
            things_requested_ct += val
        if things_requested_ct:
            # No need to bother with self.all_requests just yet
            return

        #
        for reqId, request in self.all_requests.items():
            if request.IS_OLD:
                # Note: This is an old request that should have died off and been reset. Ignore it
                TOTAL -= 1
                if TOTAL == 0:
                    myraise(IB_IS_DONE, True)
                continue
            ct += 1
            #if hasattr(request, "tickSnapshotEnded"):
            if not SUS and isinstance(request, myRequest.TimedRequest):
                SUS = request.seconds_until_stale
            if isinstance(request, myRequest.EndReceivedRequest):
                if request.tickSnapshotEnded is True:
                    snapshotended += 1
                    continue
            if request.errorCode != 0:
                errored += 1
                continue
            if request.gotGoodPrice:
                good += 1
                continue
            # see if TWS is still connected?
            #    myjoe("improve my code!")
        if (good or snapshotended or errored) and (good + snapshotended + errored) == TOTAL:
            # If none are bad, then they're all good, and hence done
            if ct != good + snapshotended + errored:
                myjoe()
            if good == ct:
                debugMsg(f"CHECK_FOR_TIME_TO_DISCONNECT(1a): ------ Num requests: #{ct}. All are good [{good}]     ({SUS} seconds)")
                _joe = 12  # check it is not messing up getting orders, or something else!
            elif snapshotended == ct:
                debugMsg(f"CHECK_FOR_TIME_TO_DISCONNECT(1b): ------ Num requests: #{ct}. All received an '..End()' message from IB [{snapshotended=}]")
                _joe = 12  # check it is not messing up getting orders, or something else!"
            else:
                # - this gets hit a few times, before the 'raise' can take place, probably due to threading?
                # - Why would the system go on to "IB get orders" if it is still processing something?
                debugMsg(f"CHECK_FOR_TIME_TO_DISCONNECT(1c) : ------ Num requests: #{ct}. All are good ({good}), or 'End()' received ({snapshotended=})     ({SUS} seconds)")
                _joe = 12  # check deal with allrequests
                _joe = 12  # check it is not messing up getting orders, or something else!
            # Fixme: I need to make sure any 'self.things_requested["IB get orders"] = 1' is also good!
            myraise(IB_HAS_ALL_PRICES, True)

        # -------------------------------------------------------------------------------------------------------------------
        # 2) Ok, the regular check that if everything is either good, bad, or stale, then exit.
        # -------------------------------------------------------------------------------------------------------------------
        request = None
        # Checking whether a request gotten stale is done in                  def msgLoopRec(
        ct, good, SUS = 0, 0, 0
        if self.all_requests != {}:
            # 1) See if they're already set as being done:
            either_stale_or_done = True
            for reqId, request in self.all_requests.items():
                if request.IS_OLD:
                    # Note: This is an old request that should have died off and been reset. Ignore it
                    continue
                ct += 1
                if request.gotGoodPrice:
                    good += 1
                elif request.got_stale:  # and request.gotGoodPrice is False:
                    stale += 1
                if request.errorCode:
                    errored += 1
                # if request.gotGoodPrice is False and request.got_stale is False and request.gotEndSignalFromIB is False and request.errorCode == 0:
                if request.gotGoodPrice is False and request.got_stale is False and request.errorCode == 0:
                    either_stale_or_done = False
                    break  # Goes to next statement, 'if either_stale_or_done'
            if ct != 0 and either_stale_or_done is True:
                # Does not add up?
                if ct != good + stale + errored:
                    # where is something like "contractDetailsEnd received" stored?
                    myjoe(f"ct:{ct}, good:{good}, stale:{stale}, errored:{errored}")
                msg = f"------ All requests [{ct}] good [{good}], stale [{stale}], or errored [{errored}] "
                if SUS:
                    msg += f"({SUS} seconds) "
                msg += "------"
                debugMsg("")
                debugMsg("CHECK_FOR_TIME_TO_DISCONNECT(2)", msg)
                debugMsg("")
                if self.badTickers:
                    self.badTickers.sort()
                    infoMsg("CHECK_FOR_TIME_TO_DISCONNECT(3)", f"------ Bad tickers(3): ({commatize(self.badTickers)})")
                #
                if stale == 0:
                    myraise(IB_ALL_REQUESTS_GOOD_OR_ERRORED, True)  # raise IB_ALL_REQUESTS_GOOD_OR_ERRORED(True)
                else:
                    if self.which.find("Option") != -1 or self.which.find("Prices") != -1:
                        myraise(IB_REQUESTS_WERE_STALE, bool(good))  # reflects if the code worked at all, if "good" had a result
                    else:
                        myraise(IB_REQUESTS_WERE_STALE, True)  # raise IB_REQUESTS_WERE_STALE(True)
            #
            # 2) Ok, something is still working. So check/set anything that has gone stale:
            all_requests_got_stale = True
            for reqId, request in self.all_requests.items():
                if request.got_stale is False:  # should be the function call?
                    all_requests_got_stale = False
                    break
            if all_requests_got_stale:
                newlogger.debug(f"All requests got stale ({request.seconds_until_stale} seconds)")
                myraise(IB_ALL_REQUESTS_GOT_STALE, False)  # raise IB_ALL_REQUESTS_GOT_STALE(False)
            """
            #
            # 3) Check if it's a "greek request" and I got all the greeks I'm looking for:
            #
            turn_off_prices = True
            for reqId, request in self.all_requests.items():
                if request.gotGoodPrice is False:
                    turn_off_prices = False  # why wasn't this flagged earlier?
                    break  # I still need data for something
            if turn_off_prices:
                newlogger.debug(f"All requests came back")  # TODO: Not accurate, it can be mixed?
                myjoe("says who??")
                myraise(IB_HAS_ALL_PRICES, True)
            """
        # BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
        else:
            # ------------------------------------------------------------------------------------------------------------
            # If I'm here, I'm not processing contract-by-contract, so check higher-level requests like "Account Summary"
            # ------------------------------------------------------------------------------------------------------------
            if self.things_requested:
                joe = self.things_requested
                ct = 0
                # If I took the effort to keep track of something, make sure something is not left hanging
                for key, val in self.things_requested.items():
                    if val < 0:
                        print(f"CHECK_FOR_TIME_TO_DISCONNECT(4) - Key '{key}' went negative: {val} !")
                        raise UserWarning
                    ct += val
                if ct == 0:
                    myraise(IB_IS_DONE, True)
        # CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
        return

    @iswrapper
    # ! [rerouteMktDataReq]
    def rerouteMktDataReq(self, reqId: int, conId: int, exchange: str):
        super().rerouteMktDataReq(reqId, conId, exchange)
        print("Re-route market data request. ReqId:", reqId, "ConId:", conId, "Exchange:", exchange)

    # ! [rerouteMktDataReq]

    @iswrapper
    # ! [marketRule]
    def marketRule(self, marketRuleId: int, priceIncrements: ListOfPriceIncrements):
        super().marketRule(marketRuleId, priceIncrements)
        print("Market Rule ID: ", marketRuleId)
        for priceIncrement in priceIncrements:
            print("Price Increment.", priceIncrement)
        raise IB_IS_DONE(True)

    # ! [marketRule]

    @printWhenExecuting
    def tickByTickOperations_req(self):
        # Requesting tick-by-tick data (only refresh)
        # ! [reqtickbytick]
        self.reqTickByTickData(19001, ContractSamples.EuropeanStock2(), "Last", 0, True)
        self.reqTickByTickData(19002, ContractSamples.EuropeanStock2(), "AllLast", 0, False)
        self.reqTickByTickData(19003, ContractSamples.EuropeanStock2(), "BidAsk", 0, True)
        self.reqTickByTickData(19004, ContractSamples.EurGbpFx(), "MidPoint", 0, False)
        # ! [reqtickbytick]

        # Requesting tick-by-tick data (refresh + historicalticks)
        # ! [reqtickbytickwithhist]
        self.reqTickByTickData(19005, ContractSamples.EuropeanStock2(), "Last", 10, False)
        self.reqTickByTickData(19006, ContractSamples.EuropeanStock2(), "AllLast", 10, False)
        self.reqTickByTickData(19007, ContractSamples.EuropeanStock2(), "BidAsk", 10, False)
        self.reqTickByTickData(19008, ContractSamples.EurGbpFx(), "MidPoint", 10, True)
        # ! [reqtickbytickwithhist]

    @printWhenExecuting
    def tickByTickOperations_cancel(self):
        # ! [canceltickbytick]
        self.cancelTickByTickData(19001)
        self.cancelTickByTickData(19002)
        self.cancelTickByTickData(19003)
        self.cancelTickByTickData(19004)
        # ! [canceltickbytick]

        # ! [canceltickbytickwithhist]
        self.cancelTickByTickData(19005)
        self.cancelTickByTickData(19006)
        self.cancelTickByTickData(19007)
        self.cancelTickByTickData(19008)
        # ! [canceltickbytickwithhist]

    @iswrapper
    # ! [orderbound]
    def orderBound(self, orderId: int, apiClientId: int, apiOrderId: int):
        super().orderBound(orderId, apiClientId, apiOrderId)
        # print("OrderBound.", "OrderId:", orderId, "ApiClientId:", apiClientId, "ApiOrderId:", apiOrderId)
        debugMsg(f"{orderId:10}", "OrderBound()", f"ApiClientId: {apiClientId:10}, ApiOrderId: {apiOrderId}")

    # ! [orderbound]

    @iswrapper
    # ! [tickbytickalllast]
    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                          size: int, tickAtrribLast: TickAttribLast, exchange: str,
                          specialConditions: str):
        super().tickByTickAllLast(reqId, tickType, time, price, size, tickAtrribLast,
                                  exchange, specialConditions)
        if tickType == 1:
            print("Last.", end='')
        else:
            print("AllLast.", end='')
        print(" ReqId:", reqId,
              "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "Price:", price, "Size:", size, "Exch:", exchange,
              "Spec Cond:", specialConditions, "PastLimit:", tickAtrribLast.pastLimit, "Unreported:",
              tickAtrribLast.unreported)

    # ! [tickbytickalllast]

    @iswrapper
    # ! [tickbytickbidask]
    def tickByTickBidAsk(self, reqId: int, time: int, bidPrice: float, askPrice: float,
                         bidSize: int, askSize: int, tickAttribBidAsk: TickAttribBidAsk):
        super().tickByTickBidAsk(reqId, time, bidPrice, askPrice, bidSize,
                                 askSize, tickAttribBidAsk)
        print("BidAsk. ReqId:", reqId,
              "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "BidPrice:", bidPrice, "AskPrice:", askPrice, "BidSize:", bidSize,
              "AskSize:", askSize, "BidPastLow:", tickAttribBidAsk.bidPastLow, "AskPastHigh:",
              tickAttribBidAsk.askPastHigh)

    # ! [tickbytickbidask]

    # ! [tickbytickmidpoint]
    @iswrapper
    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
        super().tickByTickMidPoint(reqId, time, midPoint)
        print("Midpoint. ReqId:", reqId,
              "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "MidPoint:", midPoint)

    # ! [tickbytickmidpoint]

    @printWhenExecuting
    def marketDepthOperations_req(self):
        # Requesting the Deep Book
        # ! [reqmarketdepth]
        self.reqMktDepth(2001, ContractSamples.EurGbpFx(), 5, False, [])
        # ! [reqmarketdepth]

        # ! [reqmarketdepth]
        self.reqMktDepth(2002, ContractSamples.EuropeanStock(), 5, True, [])
        # ! [reqmarketdepth]

        # Request list of exchanges sending market depth to UpdateMktDepthL2()
        # ! [reqMktDepthExchanges]
        self.reqMktDepthExchanges()
        # ! [reqMktDepthExchanges]

    @printWhenExecuting
    def marketDepthOperations_cancel(self):
        # Canceling the Deep Book request
        # ! [cancelmktdepth]
        self.cancelMktDepth(2001, False)
        self.cancelMktDepth(2002, True)
        # ! [cancelmktdepth]

    @iswrapper
    # ! [updatemktdepth]
    def updateMktDepth(self, reqId: TickerId, position: int, operation: int,
                       side: int, price: float, size: int):
        super().updateMktDepth(reqId, position, operation, side, price, size)
        print("UpdateMarketDepth. ReqId:", reqId, "Position:", position, "Operation:",
              operation, "Side:", side, "Price:", price, "Size:", size)

    # ! [updatemktdepth]

    @iswrapper
    # ! [updatemktdepthl2]
    def updateMktDepthL2(self, reqId: TickerId, position: int, marketMaker: str,
                         operation: int, side: int, price: float, size: int, isSmartDepth: bool):
        super().updateMktDepthL2(reqId, position, marketMaker, operation, side,
                                 price, size, isSmartDepth)
        print("UpdateMarketDepthL2. ReqId:", reqId, "Position:", position, "MarketMaker:", marketMaker, "Operation:",
              operation, "Side:", side, "Price:", price, "Size:", size, "isSmartDepth:", isSmartDepth)

    # ! [updatemktdepthl2]

    @iswrapper
    # ! [rerouteMktDepthReq]
    def rerouteMktDepthReq(self, reqId: int, conId: int, exchange: str):
        super().rerouteMktDataReq(reqId, conId, exchange)
        print("Re-route market depth request. ReqId:", reqId, "ConId:", conId, "Exchange:", exchange)

    # ! [rerouteMktDepthReq]

    @printWhenExecuting
    def realTimeBarsOperations_req(self):
        # Requesting real time bars
        # ! [reqrealtimebars]
        self.reqRealTimeBars(3001, ContractSamples.EurGbpFx(), 5, "MIDPOINT", True, [])
        # ! [reqrealtimebars]

    @iswrapper
    # ! [realtimebar]
    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float, low: float, close: float,
                    volume: int, wap: float, count: int):
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        print("RealTimeBar. TickerId:", reqId, RealTimeBar(time, -1, open_, high, low, close, volume, wap, count))

    # ! [realtimebar]

    @printWhenExecuting
    def realTimeBarsOperations_cancel(self):
        # Canceling real time bars
        # ! [cancelrealtimebars]
        self.cancelRealTimeBars(3001)
        # ! [cancelrealtimebars]

    def historicalDataOperations_req(self):
        """ https://interactivebrokers.github.io/tws-api/historical_bars.html
            Results go to ---> myCode.storeHistoricalData()
        """
        qry = f"SELECT ticker, currency, isin FROM tbl_positions WHERE curdate='{TODAY}' and only_etrade=False"  # AND ticker not in (SELECT DISTINCT ticker FROM tbl_historical_data)"
        ticker_res = sql_execute(qry)
        # tickers = sql_utils.GetTickers().get_tickers(IB=True)
        if not ticker_res:
            return

        self.things_requested["historicalData"] = 0

        for ticker, currency, isin in ticker_res:
            self.reqId += 1

            if currency != "USD":
                debugMsg(0, "historicalDataOperations_req()",
                         f"{ticker} - IB doesn't provide non-US historical data? Ignoring stock..")
                continue
            self.things_requested["historicalData"] += 1

            contract = Contract()
            contract.secType = "STK"
            contract.currency = "USD"
            contract.exchange = "SMART"
            contract.symbol = ticker
            if isin != "":
                # Irrelevant until I figure out if IB does non-USD hist data
                contract.secIdType = "ISIN"
                contract.secId = isin

            """ Types of data to retrieve (one at a time presumably)
                - TRADES, MIDPOINT, BID, ASK, BID_ASK
                - HISTORICAL_VOLATILITY, OPTION_IMPLIED_VOLATILITY, FEE_RATE, REBATE_RATE
            """
            histRequest = myRequest.timed_HistoricalDataRequest(self.reqId, contract, "historicalDataOperations_req",
                                                                "", self)
            histRequest.note = ticker
            self.all_requests[self.reqId] = histRequest
            debugMsg(self.reqId, "historicalDataOperations_req()",
                     f" is a [{histRequest.what_am_i():25}] 1Y histRequest")
            self.reqHistoricalData(self.reqId, contract, "", "1 Y", "1 day", "MIDPOINT", 1, 1, False, [])
            # self.reqHistoricalData(reqId, contract, "", "1 M", "1 day", "MIDPOINT", 1, 1, False, [])

            # Requesting historical data

            # Get the earliest available data point for a given instrument:   For IBM: 19800317
            # self.things_requested["reqHeadTimeStamp-4101"] = 1
            # self.reqHeadTimeStamp(4101, contract, "TRADES", 0, 1)
            """
            queryTime = (datetime.datetime.today() - datetime.timedelta(days=180)).strftime("%Y%m%d %H:%M:%S")  # 20201003
            debugMsg(0, "historicalDataOperations_req()", "IBM - 1 day MIDPOINT False")
            self.things_requested["historicalData-4102"] = 1
            # Daterange that comes back: 20200903 - 20201002.  "1 month of data ending 20201003"
            self.reqHistoricalData(4102, contract, queryTime, "1 M", "1 day", "MIDPOINT", 1, 1, False, [])
    
            # Daterange that comes back:20210302-20210331
            debugMsg(0, "historicalDataOperations_req()", "IBM - 1 day MIDPOINT True")
            self.things_requested["historicalData-4104"] = 1
            self.reqHistoricalData(4104, contract, "", "1 M", "1 day", "MIDPOINT", 1, 1, True, [])
            """
            # ! [reqhistoricaldata]
            # Too many come back
            # debugMsg(0, "historicalDataOperations_req()", "IBM - 1 min TRADES")
            # self.reqHistoricalData(4103, contract, queryTime, "10 D", "1 min", "TRADES", 1, 1, False, [])

        # debugMsg(0, "historicalDataOperations_req()", "- FINISH")
        self.computeTimeOutLength("historicalDataOperations_req")
        return

    @printWhenExecuting
    def historicalDataOperations_cancel(self):
        # ! [cancelHeadTimestamp]
        self.cancelHeadTimeStamp(4101)
        # ! [cancelHeadTimestamp]

        # Canceling historical data requests
        # ! [cancelhistoricaldata]
        self.cancelHistoricalData(4102)
        self.cancelHistoricalData(4103)
        self.cancelHistoricalData(4104)
        # ! [cancelhistoricaldata]

    @printWhenExecuting
    def historicalTicksOperations(self):
        # ! [reqhistoricalticks]
        self.reqHistoricalTicks(18001, ContractSamples.USStockAtSmart(),
                                "20170712 21:39:33", "", 10, "TRADES", 1, True, [])
        self.reqHistoricalTicks(18002, ContractSamples.USStockAtSmart(),
                                "20170712 21:39:33", "", 10, "BID_ASK", 1, True, [])
        self.reqHistoricalTicks(18003, ContractSamples.USStockAtSmart(),
                                "20170712 21:39:33", "", 10, "MIDPOINT", 1, True, [])
        # ! [reqhistoricalticks]

    @iswrapper
    # ! [headTimestamp]
    def headTimestamp(self, reqId: int, headTimestamp: str):
        print("HeadTimestamp. ReqId:", reqId, "HeadTimeStamp:", headTimestamp)

    # ! [headTimestamp]

    @iswrapper
    # ! [histogramData]
    def histogramData(self, reqId: int, items: HistogramDataList):
        print("HistogramData. ReqId:", reqId, "HistogramDataList:", "[%s]" % "; ".join(map(str, items)))

    @iswrapper
    # ! [historicaldata]
    def historicalData(self, reqId: int, bar: BarData):
        ticker = self.all_requests[reqId].ticker
        # debugMsg(reqId, "historicalData()", f"{ticker}: {bar}")
        if self.my_code.storeHistoricalData(reqId, ticker, bar):
            # self.all_requests[reqId].gotGoodPrice = True
            self.all_requests[reqId].setGotGoodPrice("historicalData")
            # self.gotEndSignalFromIB = False
        return

    @iswrapper
    # ! [historicaldataend]
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        ticker = self.all_requests[reqId].ticker
        # super().historicalDataEnd(reqId, start, end)
        debugMsg(reqId, "HistoricalDataEnd", f"{ticker} - historicalDataEnd() received")
        if "historicalData" in self.things_requested:
            self.things_requested["historicalData"] -= 1

    # ! [historicaldataend]

    @iswrapper
    # ! [historicalDataUpdate]
    def historicalDataUpdate(self, reqId: int, bar: BarData):
        print("HistoricalDataUpdate. ReqId:", reqId, "BarData.", bar)

    # ! [historicalDataUpdate]

    @iswrapper
    # ! [historicalticks]
    def historicalTicks(self, reqId: int, ticks: ListOfHistoricalTick, done: bool):
        for tick in ticks:
            print("HistoricalTick. ReqId:", reqId, tick)

    # ! [historicalticks]

    @iswrapper
    # ! [historicalticksbidask]
    def historicalTicksBidAsk(self, reqId: int, ticks: ListOfHistoricalTickBidAsk,
                              done: bool):
        for tick in ticks:
            print("HistoricalTickBidAsk. ReqId:", reqId, tick)

    # ! [historicalticksbidask]

    @iswrapper
    # ! [historicaltickslast]
    def historicalTicksLast(self, reqId: int, ticks: ListOfHistoricalTickLast,
                            done: bool):
        for tick in ticks:
            print("HistoricalTickLast. ReqId:", reqId, tick)

    # ! [historicaltickslast]

    @printWhenExecuting
    def optionsOperations_req(self):
        # ! [reqsecdefoptparams]
        self.things_requested["securityDefinitionOptionParameter"] = 1
        self.reqSecDefOptParams(0, "IBM", "", "STK", 8314)
        # ! [reqsecdefoptparams]

        # Calculating implied volatility
        # ! [calculateimpliedvolatility]
        self.calculateImpliedVolatility(5001, ContractSamples.OptionWithLocalSymbol(), 0.5, 55, [])
        # ! [calculateimpliedvolatility]

        # Calculating option's price
        # ! [calculateoptionprice]
        self.calculateOptionPrice(5002, ContractSamples.OptionWithLocalSymbol(), 0.6, 55, [])
        # ! [calculateoptionprice]

        # Exercising options
        # ! [exercise_options]    no, bad! Not when API access is turned off!
        ####self.exerciseOptions(5003, ContractSamples.OptionWithTradingClass(), 1, 1, self.account, 1)
        # ! [exercise_options]

    @printWhenExecuting
    def optionsOperations_cancel(self):
        # Canceling implied volatility
        self.cancelCalculateImpliedVolatility(5001)
        # Canceling option's price calculation
        self.cancelCalculateOptionPrice(5002)

    @iswrapper
    # ! [securityDefinitionOptionParameter]
    def securityDefinitionOptionParameter(self, reqId: int, exchange: str,
                                          underlyingConId: int, tradingClass: str, multiplier: str,
                                          expirations: SetOfString, strikes: SetOfFloat):
        super().securityDefinitionOptionParameter(reqId, exchange,
                                                  underlyingConId, tradingClass, multiplier, expirations, strikes)
        msg = f"{reqId:5} - ct SecurityDefinitionOptionParameter(): ReqId: {reqId:5}, Exchange: {exchange}, Underlying conId: {underlyingConId}, " \
              f"TradingClass: {tradingClass}, Multiplier: {multiplier}, Expirations: {expirations}, Strikes: {str(strikes)}"
        # print(f"\t20210219 and 3250 in there?: {'20210219' in expirations and 3250 in strikes}")
        newlogger.debug(msg)

    # see if I can search for 20210219 and strike=3250  - I can, they are both there
    # ! [securityDefinitionOptionParameter]

    @iswrapper
    # ! [securityDefinitionOptionParameterEnd]
    def securityDefinitionOptionParameterEnd(self, reqId: int):
        super().securityDefinitionOptionParameterEnd(reqId)
        print("SecurityDefinitionOptionParameterEnd. ReqId:", reqId)
        if "securityDefinitionOptionParameter" in self.things_requested:
            self.things_requested["securityDefinitionOptionParameter"] -= 1

    # ! [securityDefinitionOptionParameterEnd]

    @iswrapper
    # Gets info from 'calculateImpliedVolatility()' as well as 'calculateOptionPrice()'
    # "The option greek values- delta, gamma, theta, vega- are returned by default following a reqMktData() request for the option"
    #  from: ct_greeksFromConids
    def tickOptionComputation(self, reqId: TickerId, tickType: TickType, tickAttrib: int, impliedVol: float,
                              delta: float, optPrice: float, pvDividend: float, gamma: float, vega: float, theta: float,
                              undPrice: float):
        if reqId not in self.all_requests:
            raise UserWarning
        if self.all_requests[reqId].gotGoodPrice:
            return
        super().tickOptionComputation(reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma, vega,
                                      theta, undPrice)
        #
        got_greeks = bool(impliedVol or delta or gamma or vega or theta)
        #
        the_request = self.all_requests[reqId]

        if not (got_greeks or optPrice or pvDividend or undPrice):
            msg = f"TickType: {tickType}, TickAttrib: {tickAttrib}, '{IB_tickTypes.tickTypes[tickType]}' - is not a greek"
            debugMsg(reqId, "tickOptionComputation(1)", msg)
            # myjoe()  # really? exit?
            return
        #
        params = create_A_Param("tbl_options")
        params.param_dict["curdate"] = TODAY
        #
        whatAmI = the_request.what_am_i()
        the_contract = the_request.contract
        ticker = the_contract.symbol
        strike = the_contract.strike
        conId = the_contract.conId
        # right = the_contract.right
        expiry = the_contract.lastTradeDateOrContractMonth  # expiry
        if expiry.find("-") == -1:
            expiry = f"{expiry[:4]}-{expiry[4:6]}-{expiry[6:8]}"
        putCall = the_contract.right
        #
        # "tickType": tickType,
        # params.no_zeros("tickAttrib", tickAttrib)
        conId = the_contract.conId
        params.updateFromDict({"putCall": putCall, "ticker": ticker, "strike": strike, "expiry": expiry,
                               "IB_expiry": expiry.replace("-", ""),
                               "source": "IB-tickOptionComputation", "last_greek_update": TODAY})
        if conId:
            params.param_dict["conId"] = conId
        else:
            myjoe("How could I NOT have a conId here??")
        params.no_zeros("delta", delta)
        params.no_zeros("gamma", gamma)
        params.no_zeros("optPrice", optPrice)
        params.no_zeros("ib_impliedVol", impliedVol)
        params.no_zeros("vega", vega)
        params.no_zeros("theta", theta)
        params.no_zeros("undPrice", undPrice)
        params.no_zeros("pvDividend", pvDividend)

        rounding = 3

        if delta:
            delta = round(delta, rounding)
            the_request.ticksReceived_dict["delta"] = delta
        if gamma:
            gamma = round(gamma, rounding)
            the_request.ticksReceived_dict["gamma"] = gamma
        if optPrice:
            optPrice = round(optPrice, rounding)
            the_request.ticksReceived_dict["optPrice"] = optPrice
        if impliedVol:
            impliedVol = round(impliedVol, rounding)
            the_request.ticksReceived_dict["ib_impliedVol"] = impliedVol
        if vega:
            vega = round(vega, rounding)
            the_request.ticksReceived_dict["vega"] = vega
        if theta:
            theta = round(theta, rounding)
            the_request.ticksReceived_dict["theta"] = theta
        if undPrice:
            undPrice = round(undPrice, rounding)
            the_request.ticksReceived_dict["undPrice"] = undPrice
        if pvDividend:
            pvDividend = round(pvDividend, rounding)
            the_request.ticksReceived_dict["pvDividend"] = pvDividend
        #
        DEBUG = True
        if delta and "delta" in the_request.thingsNeeded:
            if DEBUG:
                debugMsg(reqId, "tickOptionComputation(2d)", f"[{whatAmI:25}] got delta = {delta} greek for tbl_options")
            the_request.thingsNeeded.discard("delta")
        if gamma and "gamma" in the_request.thingsNeeded:
            if DEBUG:
                debugMsg(reqId, "tickOptionComputation(2g)", f"[{whatAmI:25}] got gamma = {gamma} greek for tbl_options")
            the_request.thingsNeeded.discard("gamma")
        #
        params.processThis()
        #
        if DEBUG:
            if params.msg == "added":
                debugMsg(reqId, "tickOptionComputation(4)", f"[{whatAmI:25}] was added to tbl_options")
            if params.msg == "updated":
                msg = params.update_msg.replace('\n', '')
                if self.DEBUG:
                    debugMsg(reqId, "tickOptionComputation(5)", f"[{whatAmI:25}] tbl_options updated: {msg}")
        #
        if the_request.thingsNeeded == set():
            debugMsg(reqId, "tickOptionComputation(6)", f"[{whatAmI:25}] turning it off, I got what I needed")
            self.all_requests[reqId].setGotGoodPrice("tickOptionComputation")
            tbl_recommendations = create_A_Param("tbl_recommendations")
            tbl_recommendations.updateFromDict({"ticker": ticker, "gotGreeks": True, "curdate": the_request.curdate,
                                                "account": the_request.account, "tradeReco": the_request.tradeReco})
            tbl_recommendations.updateOnly()
            if tbl_recommendations.msg == "added":
                debugMsg(reqId,
                         f"(1): tbl_ [{ticker}] was {tbl_recommendations.msg} - {tbl_recommendations.update_msg}")
            if tbl_recommendations.msg == "updated":
                debugMsg(reqId,
                         f"(2): tbl_ [{ticker}] was {tbl_recommendations.msg} - {tbl_recommendations.update_msg}")
            #
        return

    @printWhenExecuting
    def contractOperations(self):
        # ! [reqcontractdetails]
        # self.things_requested["contractDetails"] = 1
        self.reqContractDetails(210, ContractSamples.OptionForQuery())
        self.reqContractDetails(211, ContractSamples.EurGbpFx())
        self.reqContractDetails(212, ContractSamples.Bond())
        self.reqContractDetails(213, ContractSamples.FuturesOnOptions())
        self.reqContractDetails(214, ContractSamples.SimpleFuture())
        self.reqContractDetails(215, ContractSamples.USStockAtSmart())
        # ! [reqcontractdetails]

        # ! [reqmatchingsymbols]
        self.reqMatchingSymbols(211, "IB")
        # ! [reqmatchingsymbols]

    @printWhenExecuting
    def newsOperations_req(self):
        # Requesting news ticks
        # ! [reqNewsTicks]
        self.reqMktData(10001, ContractSamples.USStockAtSmart(), "mdoff,292", False, False, [])
        # ! [reqNewsTicks]

        # Returns list of subscribed news providers
        # ! [reqNewsProviders]
        self.reqNewsProviders()
        # ! [reqNewsProviders]

        # Returns body of news article given article ID
        # ! [reqNewsArticle]
        self.reqNewsArticle(10002, "BRFG", "BRFG$04fb9da2", [])
        # ! [reqNewsArticle]

        # Returns list of historical news headlines with IDs
        # ! [reqHistoricalNews]
        self.reqHistoricalNews(10003, 8314, "BRFG", "", "", 10, [])
        # ! [reqHistoricalNews]

        # ! [reqcontractdetailsnews]
        self.reqContractDetails(10004, ContractSamples.NewsFeedForQuery())
        # ! [reqcontractdetailsnews]

    @printWhenExecuting
    def newsOperations_cancel(self):
        # Canceling news ticks
        # ! [cancelNewsTicks]
        self.cancelMktData(10001)
        # ! [cancelNewsTicks]

    @iswrapper
    # ! [tickNews]
    def tickNews(self, tickerId: int, timeStamp: int, providerCode: str,
                 articleId: str, headline: str, extraData: str):
        print("TickNews. TickerId:", tickerId, "TimeStamp:", timeStamp,
              "ProviderCode:", providerCode, "ArticleId:", articleId,
              "Headline:", headline, "ExtraData:", extraData)

    # ! [tickNews]

    @iswrapper
    # ! [historicalNews]
    def historicalNews(self, reqId: int, time: str, providerCode: str,
                       articleId: str, headline: str):
        print("HistoricalNews. ReqId:", reqId, "Time:", time,
              "ProviderCode:", providerCode, "ArticleId:", articleId,
              "Headline:", headline)

    # ! [historicalNews]

    @iswrapper
    # ! [historicalNewsEnd]
    def historicalNewsEnd(self, reqId: int, hasMore: bool):
        print("HistoricalNewsEnd. ReqId:", reqId, "HasMore:", hasMore)

    # ! [historicalNewsEnd]

    @iswrapper
    # ! [newsProviders]
    def newsProviders(self, newsProviders: ListOfNewsProviders):
        print("NewsProviders: ")
        for provider in newsProviders:
            print("NewsProvider.", provider)

    # ! [newsProviders]

    @iswrapper
    # ! [newsArticle]
    def newsArticle(self, reqId: int, articleType: int, articleText: str):
        print("NewsArticle. ReqId:", reqId, "ArticleType:", articleType,
              "ArticleText:", articleText)

    # ! [newsArticle]

    @iswrapper
    # ! [bondcontractdetails]
    def bondContractDetails(self, reqId: int, contractDetails: ContractDetails):
        super().bondContractDetails(reqId, contractDetails)
        printinstance(reqId, contractDetails)

    # ! [bondcontractdetails]

    @iswrapper
    # ! [contractdetailsend]
    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        # params = self.MD.Master_Params.newParam("tbl_IB_option_contract_details")
        the_request = self.all_requests[reqId]
        the_contract = the_request.contract
        ticker = the_contract.symbol
        expiry = the_contract.lastTradeDateOrContractMonth
        ct = the_request.received
        the_request.thingsNeeded.discard("contract")
        if isinstance(the_request, myRequest.EndReceivedRequest):
            the_request.tickSnapshotEnded = True
            the_request.endReceived = True
        #
        if the_contract.secType == "STK":
            debugMsg(reqId, "contractDetailsEnd(0)", f"ticker: '{the_request.ticker}' received 'contractDetailsEnd()'")
            u_res = sql_execute(f"update tbl_IB_stock_contract_details set end_received=True where ticker='{ticker}'")
        elif the_contract.secType == "OPT":
            # print(f"contractDetailsEnd(): {reqId} - ticker: '{the_request.ticker}' received #{ct:,} contracts for expiry={expiry} .. going to bulk add them now .. ")
            _expiry = f"{expiry[:4]}/{expiry[-2:]}"
            print(f"contractDetailsEnd(): {reqId} - Bulk adding #{ct} contracts for expiry={_expiry}, ticker: '{ticker}'")
            debugMsg(reqId, "contractDetailsEnd(1)",
                     f"ticker: '{the_request.ticker}' received 'contractDetailsEnd()' for expiry={expiry}..  ({ct} contracts received)")
            debugMsg(reqId, "contractDetailsEnd(2)", f"... GOING TO BULK ADD THEM NOW ...")
            #
            expiries_stored = self.bulk_add_contract_details(reqId)
            #
            for expiry in expiries_stored:
                u_qry = f"update tbl_IB_option_contract_details set end_received=True where ticker='{ticker}' and expiry='{expiry}'"
                u_res = sql_execute(u_qry)
                if not u_res:
                    myjoe("")
                debugMsg(reqId, "contractDetailsEnd(3)", f"Setting 'end_received=True' for ticker='{ticker}' and expiry='{expiry}'")
        return

    # ! [contractdetailsend]

    @iswrapper
    def contractDetails(self, reqId: int,
                        contractDetails: ContractDetails):  # make a status log message for every 100 received
        super().contractDetails(reqId, contractDetails)
        #                                                             --->                     def bulk_add_contract_details(
        if contractDetails.contract.secType == "OPT":
            the_request = self.all_requests[reqId]
            ticker = the_request.ticker  # contractDetails.underSymbol
            expiry = contractDetails.contract.lastTradeDateOrContractMonth
            key = f"{ticker} - {expiry}"
            if expiry not in the_request.received_by_expiry:
                # newlogger.debug("")
                debugMsg(reqId, "contractDetails(0)", f"Receiving contracts for: '{key}'  ({the_request.note})")
            # the_request.received += 1
            the_request.received_by_expiry[expiry] = the_request.received_by_expiry.get(expiry, 0) + 1
            if the_request.received and the_request.received % 50 == 0:
                debugMsg(reqId, "contractDetails(0)",
                         f"                       : .. received {the_request.received} so far ..")
            self.all_requests[reqId].received += 1
            self.all_requests[reqId].array_of_contractDetails.append(contractDetails)
            the_request.needToStoreContracts = True
        elif contractDetails.contract.secType == "STK":
            self.IB_store_stock_contract_details(reqId, contractDetails)
        else:
            print(contractDetails.contract.secType)
            myjoe("Huh?")
        return

    def bulk_add_contract_details(self, reqId):
        # Note: If you provide the connection to Parameters, then it is up to you to commit, and close it
        conn = sqlite3.connect("Data/my_portfolio.db", )
        the_request = self.all_requests[reqId]
        params = create_A_Param("tbl_IB_option_contract_details")
        #
        ticker, putCall = "", ""
        expiries_stored = {}
        for contractDetails in the_request.array_of_contractDetails:
            params.clear_it()
            #
            ticker = contractDetails.underSymbol
            expiry = convert_date(contractDetails.contract.lastTradeDateOrContractMonth)
            expiries_stored[expiry] = expiries_stored.get(expiry, 0) + 1
            strike = contractDetails.contract.strike
            putCall = contractDetails.contract.right
            assert putCall in ["C", "P"]
            params.param_dict["putCall"] = putCall
            what_am_I = f"{ticker} {strike} strike {putCall}, expiry={expiry}"

            dict = {"reqId": reqId,
                    "ticker": ticker,
                    "secType": contractDetails.contract.secType,
                    "strike": contractDetails.contract.strike,
                    "expiry": expiry,
                    "IB_expiry": expiry.replace('-', ''),
                    "contract": contractDetails.contract,
                    "conId": contractDetails.contract.conId,
                    "symbol": contractDetails.underSymbol,
                    "exchange": contractDetails.contract.exchange,
                    "primaryExch": contractDetails.contract.primaryExchange, }
            #
            params.updateFromDict(dict)
            #
            all_fields = ["aggGroup", "bondType", "callable", "category", "contractMonth", "convertible", "coupon",
                          "couponType", "cusip",
                          "descAppend", "evMultiplier", "evRule", "industry", "issueDate", "lastTradeTime",
                          "liquidHours", "longName", "marketName",
                          "marketRuleIds", "maturity", "mdSizeMultiplier", "minTick", "nextOptionDate",
                          "nextOptionPartial", "nextOptionType", "notes",
                          "orderTypes", "priceMagnifier", "putable", "ratings", "realExpirationDate", "secIdList",
                          "stockType", "subcategory", "timeZoneId",
                          "tradingHours", "underConId", "underSecType", "underSymbol", "validExchanges"]
            for field in all_fields:
                params.no_zeros(field, eval(f"contractDetails.{field}"))
            #
            params.param_dict["quarterly_expiration"] = expiry in self.QuarterlyExpirations

            params.processThis(conn=conn)
            #
            if params.msg == "added":
                the_request.howManyReceivedFromIB += 1
            elif params.msg == "updated":
                debugMsg(reqId, "tbl_IB_option_contract_details(2)", f"[{what_am_I}] was updated: {params.update_msg}!")
                the_request.howManyReceivedFromIB += 1
        conn.commit()
        conn.close()
        the_request.needToStoreContracts = False
        the_request.tickSnapshotEnded = True
        the_request.endReceived = True
        params.needToProcess = False
        # *IF* this contract is in 'tbl_IB_option_contracts_needed' THEN turn 'needData' to false
        contractMonth = contractDetails.realExpirationDate  # Needs to be like: 20220318
        qry = f"update tbl_IB_option_contracts_needed set needData=FALSE where ticker='{ticker}' and " \
              f"contractMonth='{contractMonth}' and putCall='{putCall}'"
        res = sql_execute(qry)
        #
        return list(expiries_stored.keys())

    def IB_store_contractDetails(self, reqId, contractDetails):
        """ This is an overwritten funcion that gets called when I do:    def my_reqContractDetails(  ???????
                                                                          def getOptionDefinitions(
        """
        # https://www.youtube.com/watch?v=dzOilFBDmJI&feature=emb_rel_pause
        myjoe("does this get hit anymore?")
        the_request = self.all_requests[reqId]
        ticker = contractDetails.underSymbol
        expiry = convert_date(contractDetails.contract.lastTradeDateOrContractMonth)
        if the_request.received == 0:
            newlogger.debug("")
            debugMsg(reqId, "IB_store_contractDetails(0)", f"Receiving contracts for: {expiry} - {ticker}")
        elif the_request.received % 50 == 0:
            debugMsg(reqId, "IB_store_contractDetails(0)",
                     f"                       : .. received {the_request.received} so far ..")
        the_request.received += 1
        # if ticker not in self.IB_store_contractDetails.received_tickers:
        #    debugMsg(reqId, "tbl_IB_option_contract_details(0)", f"Receiving contracts for: '{ticker}'..", self.newlogger)
        #    self.IB_store_contractDetails.received_tickers[ticker] = self.IB_store_contractDetails.received_tickers.get(ticker, 0) + 1

        # expiry = convert_date(contractDetails.contract.lastTradeDateOrContractMonth)
        dict = {"reqId": reqId,
                "ticker": ticker,
                "secType": contractDetails.contract.secType,
                "strike": contractDetails.contract.strike,
                "expiry": expiry,
                "IB_expiry": expiry.replace('-', ''),
                "contract": contractDetails.contract,
                "conId": contractDetails.contract.conId,
                "symbol": contractDetails.underSymbol,
                "exchange": contractDetails.contract.exchange,
                "primaryExch": contractDetails.contract.primaryExchange, }
        #
        params = create_A_Param("tbl_IB_option_contract_details")
        params.updateFromDict(dict)

        # the_request = self.all_requests[reqId]
        # the_request.gotGoodPrice = True  no! this gets a 'contractDetailsEnd()' instruction to end
        # ticker = the_request.contract.symbol
        strike = contractDetails.contract.strike
        putCall = contractDetails.contract.right
        assert putCall in ["C", "P"]
        params.param_dict["putCall"] = putCall
        what_am_I = f"{ticker} {strike} strike {putCall}, expiry={expiry}"

        all_fields = ["aggGroup", "bondType", "callable", "category", "contractMonth", "convertible", "coupon",
                      "couponType", "cusip",
                      "descAppend", "evMultiplier", "evRule", "industry", "issueDate", "lastTradeTime", "liquidHours",
                      "longName", "marketName",
                      "marketRuleIds", "maturity", "mdSizeMultiplier", "minTick", "nextOptionDate", "nextOptionPartial",
                      "nextOptionType", "notes",
                      "orderTypes", "priceMagnifier", "putable", "ratings", "realExpirationDate", "secIdList",
                      "stockType", "subcategory", "timeZoneId",
                      "tradingHours", "underConId", "underSecType", "underSymbol", "validExchanges"]
        for field in all_fields:
            params.no_zeros(field, eval(f"contractDetails.{field}"))
        #
        params.processThis()
        #
        if params.msg == "added":
            # debugMsg(reqId, "tbl_IB_option_contract_details(1)", f"[{what_am_I}] was added!", self.newlogger)
            the_request.howManyReceivedFromIB += 1
        elif params.msg == "updated":
            debugMsg(reqId, "tbl_IB_option_contract_details(2)", f"[{what_am_I}] was updated: {params.update_msg}!")
            the_request.howManyReceivedFromIB += 1

        # *IF* this contract is in 'tbl_IB_option_contracts_needed' THEN turn 'needData' to false
        ticker = contractDetails.underSymbol
        # strike = params.param_dict["strike"]
        contractMonth = contractDetails.realExpirationDate  # Needs to be like: 20220318
        qry = f"update tbl_IB_option_contracts_needed set needData=FALSE where ticker='{ticker}' and " \
              f"contractMonth='{contractMonth}' and putCall='{putCall}'"
        res = sql_execute(qry)
        if not res:
            # no result only means I got utterly new contract details
            pass

        return

    def IB_store_stock_contract_details(self, reqId, contractDetails):
        """ This is an overwritten funcion that gets called when I do:    def get_stock_contract_definitions(
                                                                          def getOptionDefinitions(
        """
        # https://www.youtube.com/watch?v=dzOilFBDmJI&feature=emb_rel_pause
        the_request = self.all_requests[reqId]
        the_contract = contractDetails.contract
        #
        ticker = the_contract.localSymbol
        if the_request.received == 0:
            debugMsg(reqId, "IB_store_stock_contract_details(1)", f"Received holiday schedule for: {ticker}")
        the_request.received += 1

        dict = {"reqId": reqId,
                "ticker": ticker,
                "secType": "STK",
                "contract": the_contract,
                "conId": the_contract.conId,
                "symbol": the_contract.symbol,
                "exchange": the_contract.exchange,
                "primaryExch": the_contract.primaryExchange, }
        #
        params = create_A_Param("tbl_IB_stock_contract_details")
        params.updateFromDict(dict, can_overlook_fields_not_in_the_table=True)

        all_fields = ["aggGroup", "bondType", "callable", "category", "contractMonth", "convertible", "coupon",
                      "couponType", "cusip",
                      "descAppend", "evMultiplier", "evRule", "industry", "issueDate", "lastTradeTime", "liquidHours",
                      "longName", "marketName",
                      "marketRuleIds", "maturity", "mdSizeMultiplier", "minTick", "nextOptionDate", "nextOptionPartial",
                      "nextOptionType", "notes",
                      "orderTypes", "priceMagnifier", "putable", "ratings", "realExpirationDate", "secIdList",
                      "stockType", "subcategory", "timeZoneId",
                      "tradingHours", "underConId", "underSecType", "underSymbol", "validExchanges"]
        for field in all_fields:
            params.no_zeros(field, eval(f"contractDetails.{field}"))

        if params.param_dict["tradingHours"].upper().find("CLOSED") != -1:
            self.check_for_market_holiday(params.param_dict)  # params.param_dict["tradingHours"].upper())
        #
        params.processThis()
        #
        # if params.msg == "added":
        #    debugMsg(reqId, "IB_store_stock_contract_details(2)", f"{ticker}-stock was added!")
        #    the_request.howManyReceivedFromIB += 1
        if params.msg == "updated":
            debugMsg(reqId, "IB_store_stock_contract_details(3)", f"{ticker}-stock was updated: {params.update_msg}!")
            the_request.howManyReceivedFromIB += 1

        return

    def check_for_market_holiday(self, a_param_dict):
        ticker = a_param_dict["ticker"]
        msg = a_param_dict["tradingHours"].upper()
        # 20220513:0400-20220513:2000;20220514:CLOSED;20220515:CLOSED;20220516:0400-20220516:2000
        if msg.find(self.newholiday) != -1:
            return  # I already know about this one
        dinge = msg.split(";")
        for xx in dinge:
            if xx.upper().find("CLOSED") != -1:
                # 20220514:CLOSED
                day, cl = xx.split(":")
                if dateIsSaturday(day) or dateIsSunday(day):
                    continue
                nicedate = f"{day[:4]}-{day[4:6]}-{day[6:8]}"
                dayofweek = datetime.datetime.strptime(day, "%Y%m%d").strftime("%A")  # Sunday through Saturday
                if nicedate != TODAY:
                    if not get_last_update("Upcoming holiday"):
                        if add_new_holiday(day):
                            self.newholiday = xx
                            infoMsg(f"check_for_market_holiday(1): Upcoming holiday: '{xx}'")
                else:
                    infoMsg(f"check_for_market_holiday(2): TODAY {dayofweek} is a holiday!: '{xx}'")
                """
                if not get_last_update("Upcoming holiday"):
                    # this pops up in the background and then hangs the code:
                    # dialogbox.simpleDialogBox(f"{dayofweek} - {nicedate}")
                    if nicedate != TODAY:
                        print(f"\n\t*** Upcoming holiday: {dayofweek} - {nicedate}\n")
                    else:
                        print(f"\n\t*** TODAY ({dayofweek}) IS A HOLIDAY! - {nicedate}\n")
                    myjoe(f"{ticker} - {dayofweek} - {nicedate}")
                    set_last_update("Upcoming holiday", note=nicedate)
                """
        return

    @printWhenExecuting
    def marketScannersOperations_req(self):
        # Requesting list of valid scanner parameters which can be used in TWS
        # ! [reqscannerparameters]
        self.reqScannerParameters()
        # ! [reqscannerparameters]

        # Triggering a scanner subscription
        # ! [reqscannersubscription]
        self.reqScannerSubscription(7001, ScannerSubscriptionSamples.HighOptVolumePCRatioUSIndexes(), [], [])

        # Generic Filters
        tagvalues = []
        tagvalues.append(TagValue("usdMarketCapAbove", "10000"))
        tagvalues.append(TagValue("optVolumeAbove", "1000"))
        tagvalues.append(TagValue("avgVolumeAbove", "10000"))

        self.reqScannerSubscription(7002, ScannerSubscriptionSamples.HotUSStkByVolume(), [],
                                    tagvalues)  # requires TWS v973+
        # ! [reqscannersubscription]

        # ! [reqcomplexscanner]
        AAPLConIDTag = [TagValue("underConID", "265598")]
        self.reqScannerSubscription(7003, ScannerSubscriptionSamples.ComplexOrdersAndTrades(), [],
                                    AAPLConIDTag)  # requires TWS v975+

        # ! [reqcomplexscanner]

    @printWhenExecuting
    def marketScanners_cancel(self):
        # Canceling the scanner subscription
        # ! [cancelscannersubscription]
        self.cancelScannerSubscription(7001)
        self.cancelScannerSubscription(7002)
        self.cancelScannerSubscription(7003)
        # ! [cancelscannersubscription]

    @iswrapper
    # ! [scannerparameters]
    def scannerParameters(self, xml: str):
        super().scannerParameters(xml)
        open('log/scanner.xml', 'w').write(xml)
        print("ScannerParameters received.")

    # ! [scannerparameters]

    @iswrapper
    # ! [scannerdata]
    def scannerData(self, reqId: int, rank: int, contractDetails: ContractDetails,
                    distance: str, benchmark: str, projection: str, legsStr: str):
        super().scannerData(reqId, rank, contractDetails, distance, benchmark,
                            projection, legsStr)
        #        print("ScannerData. ReqId:", reqId, "Rank:", rank, "Symbol:", contractDetails.contract.symbol,
        #              "SecType:", contractDetails.contract.secType,
        #              "Currency:", contractDetails.contract.currency,
        #              "Distance:", distance, "Benchmark:", benchmark,
        #              "Projection:", projection, "Legs String:", legsStr)
        print("ScannerData. ReqId:", reqId,
              ScanData(contractDetails.contract, rank, distance, benchmark, projection, legsStr))

    # ! [scannerdata]

    @iswrapper
    # ! [scannerdataend]
    def scannerDataEnd(self, reqId: int):
        super().scannerDataEnd(reqId)
        print("ScannerDataEnd. ReqId:", reqId)
        # ! [scannerdataend]

    @iswrapper
    # ! [smartcomponents]
    def smartComponents(self, reqId: int, smartComponentMap: SmartComponentMap):
        super().smartComponents(reqId, smartComponentMap)
        print("SmartComponents:")
        for smartComponent in smartComponentMap:
            print("SmartComponent.", smartComponent)

    # ! [smartcomponents]

    @iswrapper
    # ! [tickReqParams]
    def tickReqParams(self, tickerId: int, minTick: float, bboExchange: str, snapshotPermissions: int):
        super().tickReqParams(tickerId, minTick, bboExchange, snapshotPermissions)
        # print(f"{tickerId} - ct TickReqParams. TickerId: {tickerId}, MinTick: {minTick}, BboExchange: {bboExchange}, SnapshotPermissions: {snapshotPermissions}")
        # self.print_details("tickReqParams()")
        # for key, val in self.clntMeth2callCount.items():
        #    if val != 0:
        #        print(f"tickReqParams() - {val} - {key}")
        # print(f"-------------------------------------------------- tickReqParams()")

    # ! [tickReqParams]

    @iswrapper
    # ! [mktDepthExchanges]
    def mktDepthExchanges(self, depthMktDataDescriptions: ListOfDepthExchanges):
        super().mktDepthExchanges(depthMktDataDescriptions)
        print("MktDepthExchanges:")
        for desc in depthMktDataDescriptions:
            print("DepthMktDataDescription.", desc)

    # ! [mktDepthExchanges]

    @printWhenExecuting
    def fundamentalsOperations_req(self):
        # Requesting Fundamentals. Fundamental data is returned at EWrapper::fundamentalData.
        self.reqFundamentalData(8001, ContractSamples.USStock(), "ReportsFinSummary",
                                [])  # (WORKS! - <DividendPerShare>, <Dividend> in html)
        self.reqFundamentalData(8002, ContractSamples.USStock(), "ReportSnapshot",
                                [])  # for company overview   (WORKS!)
        self.reqFundamentalData(8004, ContractSamples.USStock(), "ReportsFinStatements",
                                [])  # for financial statements  (WORKS!)
        self.reqFundamentalData(8005, ContractSamples.USStock(), "RESC", [])  # for analyst estimates  (WORKS!)
        self.reqFundamentalData(8003, ContractSamples.USStock(), "ReportRatios",
                                [])  # for financial ratios   <-- not allowed
        self.reqFundamentalData(8006, ContractSamples.USStock(), "CalendarReport",
                                [])  # for company calendar   <-- not allowed

    def ct_getDividends(self):
        print("\n\t*** IB deprecated this, no longer works!\n")
        if (2 + 2) / 4 == 1:
            raise UserWarning

        """ (from client.py docstring)
            Call this function to receive fundamental data for stocks.
            The appropriate market data subscription must be set up in Account Management before you can receive this data.
            --> Fundamental data will be returned at EWrapper.fundamentalData().

            reqFundamentalData() can handle conid specified in the Contract object, but not tradingClass or multiplier.
            This is because reqFundamentalData() is used only for stocks and stocks do not have a multiplier and
            trading class.
        """
        # timed_DividendRequest = None
        # seconds_until_stale = 30
        qry = f"SELECT ticker, currency, exchange, primary_exchange, secType, isin, conId, putCall, strike, expiry FROM tbl_positions " \
              f"WHERE curdate='{TODAY}' AND good_position=True AND secType='STK' AND pays_dividends=True AND only_ETrade=False " \
              f"AND is_an_ETF=False AND last_div_update!='{TODAY}' ORDER BY ticker"
        # f"AND only_ETrade=False AND last_div_update!='{TODAY}'"
        tickers = sql_execute(qry)
        if tickers == []:
            # Nothing to do, just exit
            raise IB_NOTHING_TO_DO(True)

        newlogger.debug("ct_getDividends() : START")
        for ticker, currency, exchange, primary, secType, isin, conId, putCall, strike, expiry in tickers:
            self.reqId += 1
            contract = Contract()
            contract.symbol = ticker  # "IBM"
            contract.secType = secType  # "STK"
            contract.currency = currency  # "USD"
            contract.exchange = exchange  # "SMART" / "ISLAND"
            if primary:
                contract.primaryExchange = primary  # NASDAQ
            # Requests the contract's fundamental data. Fundamental data is returned at EWrapper::fundamentalData.

            dividendRequest = myRequest.timed_DividendRequest(self.reqId, contract, "dividend", self)
            # timed_DividendRequest.seconds_until_stale = seconds_until_stale  # set above
            SUS = dividendRequest.seconds_until_stale
            whatAmI = dividendRequest.what_am_i()
            dividendRequest.note = ticker
            self.all_requests[self.reqId] = dividendRequest
            # Note: deprecated? Use another function than reqFundamentalData?  HAVE THESE THINGS SAY WHEN TIME WILL BE UP?
            newlogger.debug(
                f"ct_getDividends(): reqId: {self.reqId:4} is a timed_DividendRequest for: '{whatAmI:25}' using reqFundamentalData({SUS})")
            self.reqFundamentalData(self.reqId, contract, "ReportsFinSummary", [])

            # --> self.fundamentalData()

        # self.computeTimeOutLength("ct_getDividends")
        if tickers:
            # timed_DividendRequest.printWaitingThread()  # Msg("Getting IB dividends")
            pass
        else:
            debugMsg(self.reqId, "ct_getDividends():", f"Nothing to get? QRY: '{qry}'")

        newlogger.debug("ct_getDividends() : FINISH (now wait for results from IB..)")
        return

    def ct_getDividends_priceRequest(self):
        """ (from client.py docstring)
            Call this function to receive fundamental data for stocks.
            The appropriate market data subscription must be set up in Account Management before you can receive this data.
            --> Fundamental data will be returned at EWrapper.fundamentalData().

            reqFundamentalData() can handle conid specified in the Contract object, but not tradingClass or multiplier.
            This is because reqFundamentalData() is used only for stocks and stocks do not have a multiplier and
            trading class.
        """
        qry = f"SELECT ticker, currency, exchange, primary_exchange, secType, isin, conId, putCall, strike, expiry FROM tbl_positions " \
              f"WHERE curdate='{TODAY}' AND good_position=True AND secType='STK' AND pays_dividends=True AND only_ETrade=False AND last_div_update!='{TODAY}' ORDER BY ticker"
        # f"AND only_ETrade=False AND last_div_update!='{TODAY}'"
        tickers = sql_execute(qry)
        if tickers == []:
            # Nothing to do, just exit
            raise IB_NOTHING_TO_DO(True)

        newlogger.debug("ct_getDividends_priceRequest() : START")
        for ticker, currency, exchange, primary, secType, isin, conId, putCall, strike, expiry in tickers:
            if ticker != "BLK":
                continue
            contract = Contract()
            contract.symbol = ticker  # "IBM"  # "VGSH" doesn't work for any request
            contract.secType = secType  # "STK"
            contract.currency = currency  # "USD"
            contract.exchange = exchange  # "SMART"  # "ISLAND"
            if primary:
                contract.primaryExchange = primary  # NASDAQ
            # Requests the contract's fundamental data. Fundamental data is returned at EWrapper::fundamentalData.

            field_set = {"IBDividends"}
            dividendRequest = myRequest.timed_PriceRequest(self.reqId, contract, "dividend", field_set, TWS_obj=self)
            dividendRequest.note = ticker
            self.all_requests[self.reqId] = dividendRequest
            debugMsg(self.reqId, "ct_getDividends_priceRequest()",
                     f"is a timed_PriceRequest for: '{dividendRequest.what_am_i():25}' using reqFundamentalData({dividendRequest.seconds_until_stale})")
            self.reqMktData(self.reqId, contract, "", False, False, [])

            # --> self.fundamentalData()
            self.reqId += 1
        # self.computeTimeOutLength("ct_getDividends")
        newlogger.debug("ct_getDividends_priceRequest() : FINISH")
        return

    @printWhenExecuting
    def fundamentalsOperations_cancel(self):
        # Canceling fundamentalsOperations_req request
        # ! [cancelfundamentaldata]
        self.cancelFundamentalData(8001)
        # ! [cancelfundamentaldata]

        # ! [cancelfundamentalexamples]
        self.cancelFundamentalData(8002)
        self.cancelFundamentalData(8003)
        self.cancelFundamentalData(8004)
        self.cancelFundamentalData(8005)
        self.cancelFundamentalData(8006)
        # ! [cancelfundamentalexamples]

    @iswrapper
    # ! [fundamentaldata]
    def fundamentalData(self, reqId: TickerId, data: str):
        # https://docs.python.org/3/library/xml.etree.elementtree.html#module-xml.etree.ElementTree
        # This gets hit by both "ct_getDividends()" as well as "reqContractDetails()" for options
        super().fundamentalData(reqId, data)
        self.ct_uploadDividends(reqId, data)

    # ! [fundamentaldata]

    def ct_uploadDividends(self, reqId, data):
        if reqId not in self.all_requests:
            myjoe()  # Now what?

        the_request = self.all_requests[reqId]
        ticker = the_request.ticker

        today = time.strftime("%Y-%m-%d")
        latest = f"Data/Dividends/IB/{ticker}_latest.xml"
        with open(latest, "w") as file:
            file.write(data)
        filename = f"Data/Dividends/IB/{ticker}_{today}.xml"
        if file_exists(filename):
            # Already processed this
            return
        with open(filename, "w") as file:
            file.write(data)
        parsed = parse(filename)
        root = parsed.getroot()

        params = create_A_Param("tbl_dividends")
        conn = sqlite3.connect("Data/my_portfolio.db")
        for xx in root.iter("Dividend"):
            # fieldsThisUpdate = []
            ex_date = xx.attrib["exDate"]
            dividend = float(xx.text)  # this needs to turn off!
            res = isThisADuplicatedDividend("ct_uploadDividends", ticker, ex_date, dividend, "")
            if res is True:
                # I have something trustworthy there, don't overwrite it
                continue
            #
            params.updateFromDict({
                "ticker": ticker,
                "dividend": dividend,
                "source": "IB-ct_uploadDividends",
            })
            params.no_zeros("ex_date", xx.attrib["exDate"])
            params.no_zeros("record_date", xx.attrib["recordDate"])
            params.no_zeros("pay_date", xx.attrib["payDate"])
            params.no_zeros("announcement_date", xx.attrib["declarationDate"])
            # Also: DividendPerShares, TotalRevenues, Dividends, EPSs
            params.processThis(conn=conn)
            #
            if params.msg == "added":
                debugMsg("ct_uploadDividends(1)", f'Dividend: {ticker} {ex_date} {dividend} was added')
            elif params.msg == "updated":
                debugMsg("ct_uploadDividends(2)",
                         f"{ticker} {ex_date} {dividend} was updated - Diffs: {params.update_msg}")
            elif params.msg not in ['', "silent update"]:
                # what bullshit update_msg do I have?
                print(f"\n\tct_uploadDividends({params.msg}): {ticker} {ex_date} {dividend} : {params.msg}")
        self.all_requests[reqId].thingsNeeded.discard("dividend")
        conn.commit()
        conn.close()
        params.needToProcess = False
        return

    @printWhenExecuting
    def bulletinsOperations_req(self):
        # Requesting Interactive Broker's news bulletinsOperations_req
        # ! [reqnewsbulletins]
        self.reqNewsBulletins(True)
        # ! [reqnewsbulletins]

    @printWhenExecuting
    def bulletinsOperations_cancel(self):
        # Canceling IB's news bulletinsOperations_req
        # ! [cancelnewsbulletins]
        self.cancelNewsBulletins()
        # ! [cancelnewsbulletins]

    @iswrapper
    # ! [updatenewsbulletin]
    def updateNewsBulletin(self, msgId: int, msgType: int, newsMessage: str,
                           originExch: str):
        super().updateNewsBulletin(msgId, msgType, newsMessage, originExch)
        print("News Bulletins. MsgId:", msgId, "Type:", msgType, "Message:", newsMessage,
              "Exchange of Origin: ", originExch)
        # ! [updatenewsbulletin]

    def ocaSample(self):
        # OCA ORDER
        # ! [ocasubmit]
        ocaOrders = [OrderSamples.LimitOrder("BUY", 1, 10), OrderSamples.LimitOrder("BUY", 1, 11),
                     OrderSamples.LimitOrder("BUY", 1, 12)]
        OrderSamples.OneCancelsAll("TestOCA_" + str(self.nextValidOrderId), ocaOrders, 2)
        for o in ocaOrders:
            self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), o)
            # ! [ocasubmit]

    def conditionSamples(self):
        # ! [order_conditioning_activate]
        mkt = OrderSamples.MarketOrder("BUY", 100)
        # Order will become active if conditioning criteria is met
        mkt.conditions.append(
            OrderSamples.PriceCondition(PriceCondition.TriggerMethodEnum.Default,
                                        208813720, "SMART", 600, False, False))
        mkt.conditions.append(OrderSamples.ExecutionCondition("EUR.USD", "CASH", "IDEALPRO", True))
        mkt.conditions.append(OrderSamples.MarginCondition(30, True, False))
        mkt.conditions.append(OrderSamples.PercentageChangeCondition(15.0, 208813720, "SMART", True, True))
        mkt.conditions.append(OrderSamples.TimeCondition("20160118 23:59:59", True, False))
        mkt.conditions.append(OrderSamples.VolumeCondition(208813720, "SMART", False, 100, True))
        self.placeOrder(self.nextOrderId(), ContractSamples.EuropeanStock(), mkt)
        # ! [order_conditioning_activate]

        # Conditions can make the order active or cancel it. Only LMT orders can be conditionally canceled.
        # ! [order_conditioning_cancel]
        lmt = OrderSamples.LimitOrder("BUY", 100, 20)
        # The active order will be cancelled if conditioning criteria is met
        lmt.conditionsCancelOrder = True
        lmt.conditions.append(
            OrderSamples.PriceCondition(PriceCondition.TriggerMethodEnum.Last,
                                        208813720, "SMART", 600, False, False))
        self.placeOrder(self.nextOrderId(), ContractSamples.EuropeanStock(), lmt)
        # ! [order_conditioning_cancel]

    def bracketSample(self):
        # BRACKET ORDER
        # ! [bracketsubmit]
        bracket = OrderSamples.BracketOrder(self.nextOrderId(), "BUY", 100, 30, 40, 20)
        for o in bracket:
            self.placeOrder(o.orderId, ContractSamples.EuropeanStock(), o)
            self.nextOrderId()  # need to advance this we'll skip one extra oid, it's fine
            # ! [bracketsubmit]

    def hedgeSample(self):
        # F Hedge order
        # ! [hedgesubmit]
        # Parent order on a contract which currency differs from your base currency
        parent = OrderSamples.LimitOrder("BUY", 100, 10)
        parent.orderId = self.nextOrderId()
        parent.transmit = False
        # Hedge on the currency conversion
        hedge = OrderSamples.MarketFHedge(parent.orderId, "BUY")
        # Place the parent first...
        self.placeOrder(parent.orderId, ContractSamples.EuropeanStock(), parent)
        # Then the hedge order
        self.placeOrder(self.nextOrderId(), ContractSamples.EurGbpFx(), hedge)
        # ! [hedgesubmit]

    def algoSamples(self):
        # ! [scale_order]
        scaleOrder = OrderSamples.RelativePeggedToPrimary("BUY", 70000, 189, 0.01)
        AvailableAlgoParams.FillScaleParams(scaleOrder, 2000, 500, True, .02, 189.00, 3600, 2.00, True, 10, 40)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), scaleOrder)
        # ! [scale_order]

        time.sleep(1)

        # ! [algo_base_order]
        baseOrder = OrderSamples.LimitOrder("BUY", 1000, 1)
        # ! [algo_base_order]

        # ! [arrivalpx]
        AvailableAlgoParams.FillArrivalPriceParams(baseOrder, 0.1, "Aggressive", "09:00:00 CET", "16:00:00 CET", True,
                                                   True, 100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [arrivalpx]

        # ! [darkice]
        AvailableAlgoParams.FillDarkIceParams(baseOrder, 10, "09:00:00 CET", "16:00:00 CET", True, 100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [darkice]

        # ! [place_midprice]
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), OrderSamples.Midprice("BUY", 1, 150))
        # ! [place_midprice]

        # ! [ad]
        # The Time Zone in "startTime" and "endTime" attributes is ignored and always defaulted to GMT
        AvailableAlgoParams.FillAccumulateDistributeParams(baseOrder, 10, 60, True, True, 1, True, True,
                                                           "20161010-12:00:00 GMT", "20161010-16:00:00 GMT")
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [ad]

        # ! [twap]
        AvailableAlgoParams.FillTwapParams(baseOrder, "Marketable", "09:00:00 CET", "16:00:00 CET", True, 100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [twap]

        # ! [vwap]
        AvailableAlgoParams.FillVwapParams(baseOrder, 0.2, "09:00:00 CET", "16:00:00 CET", True, True, 100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [vwap]

        # ! [balanceimpactrisk]
        AvailableAlgoParams.FillBalanceImpactRiskParams(baseOrder, 0.1, "Aggressive", True)
        self.placeOrder(self.nextOrderId(), ContractSamples.USOptionContract(), baseOrder)
        # ! [balanceimpactrisk]

        # ! [minimpact]
        AvailableAlgoParams.FillMinImpactParams(baseOrder, 0.3)
        self.placeOrder(self.nextOrderId(), ContractSamples.USOptionContract(), baseOrder)
        # ! [minimpact]

        # ! [adaptive]
        AvailableAlgoParams.FillAdaptiveParams(baseOrder, "Normal")
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [adaptive]

        # ! [closepx]
        AvailableAlgoParams.FillClosePriceParams(baseOrder, 0.4, "Neutral", "20180926-06:06:49", True, 100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [closepx]

        # ! [pctvol]
        AvailableAlgoParams.FillPctVolParams(baseOrder, 0.5, "12:00:00 EST", "14:00:00 EST", True, 100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [pctvol]

        # ! [pctvolpx]
        AvailableAlgoParams.FillPriceVariantPctVolParams(baseOrder, 0.1, 0.05, 0.01, 0.2, "12:00:00 EST",
                                                         "14:00:00 EST", True, 100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [pctvolpx]

        # ! [pctvolsz]
        AvailableAlgoParams.FillSizeVariantPctVolParams(baseOrder, 0.2, 0.4, "12:00:00 EST", "14:00:00 EST", True,
                                                        100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [pctvolsz]

        # ! [pctvoltm]
        AvailableAlgoParams.FillTimeVariantPctVolParams(baseOrder, 0.2, 0.4, "12:00:00 EST", "14:00:00 EST", True,
                                                        100000)
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), baseOrder)
        # ! [pctvoltm]

        # ! [jeff_vwap_algo]
        AvailableAlgoParams.FillJefferiesVWAPParams(baseOrder, "10:00:00 EST", "16:00:00 EST", 10, 10, "Exclude_Both",
                                                    130, 135, 1, 10, "Patience", False, "Midpoint")
        self.placeOrder(self.nextOrderId(), ContractSamples.JefferiesContract(), baseOrder)
        # ! [jeff_vwap_algo]

        # ! [csfb_inline_algo]
        AvailableAlgoParams.FillCSFBInlineParams(baseOrder, "10:00:00 EST", "16:00:00 EST", "Patient", 10, 20, 100,
                                                 "Default", False, 40, 100, 100, 35)
        self.placeOrder(self.nextOrderId(), ContractSamples.CSFBContract(), baseOrder)
        # ! [csfb_inline_algo]

        # ! [qbalgo_strobe_algo]
        AvailableAlgoParams.FillQBAlgoInLineParams(baseOrder, "10:00:00 EST", "16:00:00 EST", -99, "TWAP", 0.25, True)
        self.placeOrder(self.nextOrderId(), ContractSamples.QBAlgoContract(), baseOrder)
        # ! [qbalgo_strobe_algo]

    @printWhenExecuting
    def financialAdvisorOperations(self):
        # Requesting FA information
        # ! [requestfaaliases]
        self.requestFA(FaDataTypeEnum.ALIASES)
        # ! [requestfaaliases]

        # ! [requestfagroups]
        self.requestFA(FaDataTypeEnum.GROUPS)
        # ! [requestfagroups]

        # ! [requestfaprofiles]
        self.requestFA(FaDataTypeEnum.PROFILES)
        # ! [requestfaprofiles]

        # Replacing FA information - Fill in with the appropriate XML string.
        # ! [replacefaonegroup]
        self.replaceFA(1000, FaDataTypeEnum.GROUPS, FaAllocationSamples.FaOneGroup)
        # ! [replacefaonegroup]

        # ! [replacefatwogroups]
        self.replaceFA(1001, FaDataTypeEnum.GROUPS, FaAllocationSamples.FaTwoGroups)
        # ! [replacefatwogroups]

        # ! [replacefaoneprofile]
        self.replaceFA(1002, FaDataTypeEnum.PROFILES, FaAllocationSamples.FaOneProfile)
        # ! [replacefaoneprofile]

        # ! [replacefatwoprofiles]
        self.replaceFA(1003, FaDataTypeEnum.PROFILES, FaAllocationSamples.FaTwoProfiles)
        # ! [replacefatwoprofiles]

        # ! [reqSoftDollarTiers]
        self.reqSoftDollarTiers(14001)
        # ! [reqSoftDollarTiers]

    @iswrapper
    # ! [receivefa]
    def receiveFA(self, faData: FaDataType, cxml: str):
        super().receiveFA(faData, cxml)
        print("Receiving FA: ", faData)
        open('log/fa.xml', 'w').write(cxml)

    # ! [receivefa]

    @iswrapper
    # ! [softDollarTiers]
    def softDollarTiers(self, reqId: int, tiers: list):
        super().softDollarTiers(reqId, tiers)
        print("SoftDollarTiers. ReqId:", reqId)
        for tier in tiers:
            print("SoftDollarTier.", tier)

    # ! [softDollarTiers]

    @printWhenExecuting
    def miscelaneousOperations(self):
        # Request TWS' current time
        self.reqCurrentTime()
        # Setting TWS logging level
        self.setServerLogLevel(1)

    @printWhenExecuting
    def linkingOperations(self):
        # ! [querydisplaygroups]
        self.queryDisplayGroups(19001)
        # ! [querydisplaygroups]

        # ! [subscribetogroupevents]
        self.subscribeToGroupEvents(19002, 1)
        # ! [subscribetogroupevents]

        # ! [updatedisplaygroup]
        self.updateDisplayGroup(19002, "8314@SMART")
        # ! [updatedisplaygroup]

        # ! [subscribefromgroupevents]
        self.unsubscribeFromGroupEvents(19002)
        # ! [subscribefromgroupevents]

    @iswrapper
    # ! [displaygrouplist]
    def displayGroupList(self, reqId: int, groups: str):
        super().displayGroupList(reqId, groups)
        print("DisplayGroupList. ReqId:", reqId, "Groups", groups)

    # ! [displaygrouplist]

    @iswrapper
    # ! [displaygroupupdated]
    def displayGroupUpdated(self, reqId: int, contractInfo: str):
        super().displayGroupUpdated(reqId, contractInfo)
        print("DisplayGroupUpdated. ReqId:", reqId, "ContractInfo:", contractInfo)

    # ! [displaygroupupdated]

    @printWhenExecuting
    def whatIfOrderOperations(self):
        # ! [whatiflimitorder]
        whatIfOrder = OrderSamples.LimitOrder("SELL", 5, 70)
        whatIfOrder.whatIf = True
        self.placeOrder(self.nextOrderId(), ContractSamples.USStockAtSmart(), whatIfOrder)
        # ! [whatiflimitorder]
        time.sleep(2)

    @printWhenExecuting
    def orderOperations_req(self):
        # Requesting the next valid id
        # ! [reqids]
        # The parameter is always ignored.
        self.reqIds(-1)
        # ! [reqids]

        # https://interactivebrokers.github.io/tws-api/open_orders.html

        # Requesting all open orders
        # ! [reqallopenorders]
        # Obtain those orders created via the TWS API ***regardless of the submitting client application***:
        if False:
            self.reqAllOpenOrders()
        # ! [reqallopenorders]

        # Taking over orders to be submitted via TWS
        # ! [reqautoopenorders]
        # reqAutoOpenOrders can only be invoked by client with ID 0. It will cause future orders placed from TWS to be 'bound', i.e.
        # assigned an order ID such that they can be accessed by the cancelOrder or placeOrder (for modification) functions by client ID 0."
        if False:
            self.reqAutoOpenOrders(True)
        # ! [reqautoopenorders]

        # Requesting this API client's orders
        # ! [reqopenorders]
        # obtain all active orders submitted by the client application connected with the exact same client Id with which the order was sent to the TWS.
        self.reqOpenOrders()
        # ! [reqopenorders]

        # Placing/modifying an order - remember to ALWAYS increment the
        # nextValidId after placing an order so it can be used for the next one!
        # Note if there are multiple clients connected to an account, the
        # order ID must also be greater than all order IDs returned for orders
        # to orderStatus and openOrder to this client.

        # ! [order_submission]
        self.simplePlaceOid = self.nextOrderId()
        self.placeOrder(self.simplePlaceOid, ContractSamples.USStock(),
                        OrderSamples.LimitOrder("SELL", 1, 50))
        # ! [order_submission]

        # ! [faorderoneaccount]
        faOrderOneAccount = OrderSamples.MarketOrder("BUY", 100)
        # Specify the Account Number directly
        faOrderOneAccount.account = "DU119915"
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(), faOrderOneAccount)
        # ! [faorderoneaccount]

        # ! [faordergroupequalquantity]
        faOrderGroupEQ = OrderSamples.LimitOrder("SELL", 200, 2000)
        faOrderGroupEQ.faGroup = "Group_Equal_Quantity"
        faOrderGroupEQ.faMethod = "EqualQuantity"
        self.placeOrder(self.nextOrderId(), ContractSamples.SimpleFuture(), faOrderGroupEQ)
        # ! [faordergroupequalquantity]

        # ! [faordergrouppctchange]
        faOrderGroupPC = OrderSamples.MarketOrder("BUY", 0)
        # You should not specify any order quantity for PctChange allocation method
        faOrderGroupPC.faGroup = "Pct_Change"
        faOrderGroupPC.faMethod = "PctChange"
        faOrderGroupPC.faPercentage = "100"
        self.placeOrder(self.nextOrderId(), ContractSamples.EurGbpFx(), faOrderGroupPC)
        # ! [faordergrouppctchange]

        # ! [faorderprofile]
        faOrderProfile = OrderSamples.LimitOrder("BUY", 200, 100)
        faOrderProfile.faProfile = "Percent_60_40"
        self.placeOrder(self.nextOrderId(), ContractSamples.EuropeanStock(), faOrderProfile)
        # ! [faorderprofile]

        # ! [modelorder]
        modelOrder = OrderSamples.LimitOrder("BUY", 200, 100)
        modelOrder.account = "DF12345"
        modelOrder.modelCode = "Technology"  # model for tech stocks first created in TWS
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(), modelOrder)
        # ! [modelorder]

        self.placeOrder(self.nextOrderId(), ContractSamples.OptionAtBOX(),
                        OrderSamples.Block("BUY", 50, 20))
        self.placeOrder(self.nextOrderId(), ContractSamples.OptionAtBOX(),
                        OrderSamples.BoxTop("SELL", 10))
        self.placeOrder(self.nextOrderId(), ContractSamples.FutureComboContract(),
                        OrderSamples.ComboLimitOrder("SELL", 1, 1, False))
        self.placeOrder(self.nextOrderId(), ContractSamples.StockComboContract(),
                        OrderSamples.ComboMarketOrder("BUY", 1, True))
        self.placeOrder(self.nextOrderId(), ContractSamples.OptionComboContract(),
                        OrderSamples.ComboMarketOrder("BUY", 1, False))
        self.placeOrder(self.nextOrderId(), ContractSamples.StockComboContract(),
                        OrderSamples.LimitOrderForComboWithLegPrices("BUY", 1, [10, 5], True))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.Discretionary("SELL", 1, 45, 0.5))
        self.placeOrder(self.nextOrderId(), ContractSamples.OptionAtBOX(),
                        OrderSamples.LimitIfTouched("BUY", 1, 30, 34))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.LimitOnClose("SELL", 1, 34))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.LimitOnOpen("BUY", 1, 35))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.MarketIfTouched("BUY", 1, 30))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.MarketOnClose("SELL", 1))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.MarketOnOpen("BUY", 1))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.MarketOrder("SELL", 1))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.MarketToLimit("BUY", 1))
        self.placeOrder(self.nextOrderId(), ContractSamples.OptionAtIse(),
                        OrderSamples.MidpointMatch("BUY", 1))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.MarketToLimit("BUY", 1))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.Stop("SELL", 1, 34.4))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.StopLimit("BUY", 1, 35, 33))
        self.placeOrder(self.nextOrderId(), ContractSamples.SimpleFuture(),
                        OrderSamples.StopWithProtection("SELL", 1, 45))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.SweepToFill("BUY", 1, 35))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.TrailingStop("SELL", 1, 0.5, 30))
        self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
                        OrderSamples.TrailingStopLimit("BUY", 1, 2, 5, 50))
        self.placeOrder(self.nextOrderId(), ContractSamples.USOptionContract(),
                        OrderSamples.Volatility("SELL", 1, 5, 2))

        self.bracketSample()

        self.conditionSamples()

        self.hedgeSample()

        # NOTE: the following orders are not supported for Paper Trading
        # self.placeOrder(self.nextOrderId(), ContractSamples.USStock(), OrderSamples.AtAuction("BUY", 100, 30.0))
        # self.placeOrder(self.nextOrderId(), ContractSamples.OptionAtBOX(), OrderSamples.AuctionLimit("SELL", 10, 30.0, 2))
        # self.placeOrder(self.nextOrderId(), ContractSamples.OptionAtBOX(), OrderSamples.AuctionPeggedToStock("BUY", 10, 30, 0.5))
        # self.placeOrder(self.nextOrderId(), ContractSamples.OptionAtBOX(), OrderSamples.AuctionRelative("SELL", 10, 0.6))
        # self.placeOrder(self.nextOrderId(), ContractSamples.SimpleFuture(), OrderSamples.MarketWithProtection("BUY", 1))
        # self.placeOrder(self.nextOrderId(), ContractSamples.USStock(), OrderSamples.PassiveRelative("BUY", 1, 0.5))

        # 208813720 (GOOG)
        # self.placeOrder(self.nextOrderId(), ContractSamples.USStock(),
        #    OrderSamples.PeggedToBenchmark("SELL", 100, 33, True, 0.1, 1, 208813720, "ISLAND", 750, 650, 800))

        # STOP ADJUSTABLE ORDERS
        # Order stpParent = OrderSamples.Stop("SELL", 100, 30)
        # stpParent.OrderId = self.nextOrderId()
        # self.placeOrder(stpParent.OrderId, ContractSamples.EuropeanStock(), stpParent)
        # self.placeOrder(self.nextOrderId(), ContractSamples.EuropeanStock(), OrderSamples.AttachAdjustableToStop(stpParent, 35, 32, 33))
        # self.placeOrder(self.nextOrderId(), ContractSamples.EuropeanStock(), OrderSamples.AttachAdjustableToStopLimit(stpParent, 35, 33, 32, 33))
        # self.placeOrder(self.nextOrderId(), ContractSamples.EuropeanStock(), OrderSamples.AttachAdjustableToTrail(stpParent, 35, 32, 32, 1, 0))

        # Order lmtParent = OrderSamples.LimitOrder("BUY", 100, 30)
        # lmtParent.OrderId = self.nextOrderId()
        # self.placeOrder(lmtParent.OrderId, ContractSamples.EuropeanStock(), lmtParent)
        # Attached TRAIL adjusted can only be attached to LMT parent orders.
        # self.placeOrder(self.nextOrderId(), ContractSamples.EuropeanStock(), OrderSamples.AttachAdjustableToTrailAmount(lmtParent, 34, 32, 33, 0.008))
        self.algoSamples()

        self.ocaSample()

        # Request the day's executions
        # ! [reqexecutions]
        self.reqExecutions(10001, ExecutionFilter())
        # ! [reqexecutions]

        # Requesting completed orders
        # ! [reqcompletedorders]
        self.reqCompletedOrders(False)
        # ! [reqcompletedorders]

    def ct_get_completed_orders(self, apiOnly):
        newlogger.debug(f"Requesting completed orders (apiOnly={apiOnly}) .. START")  # -->       def completedOrder(
        self.things_requested["IB get CompletedOrders"] = 1
        self.reqCompletedOrders(apiOnly=apiOnly)
        newlogger.debug(f"Requesting completed orders (apiOnly={apiOnly}) .. FINISH")
        return

    # @printWhenExecuting
    def GET_ORDERS(self):
        """ This function is a kludge - at the moment all open orders sent by this API are automatically requested from IB upon connection
            (but NOT orders I manually sent!)
            So I don't need to do anything?
            https://interactivebrokers.github.io/tws-api/open_orders.html

            Not perfectly sure how reqOpenOrders(), reqAllOpenOrders(), and reqAutoOpenOrders() all relate, given
            IB downloading orders upon connection.
            --> this is the main one: self.reqAllOpenOrders()                               ---------------------->   def openOrderEnd(
        """
        # Obtain those orders created via the TWS API ***regardless of the submitting client application***: Works!
        # -->             def openOrder(
        # -->             def orderStatus(
        # Pay attention to 'CHECK_FOR_TIME_TO_DISCONNECT(1c)'
        self.things_requested["IB get orders"] = 1
        newlogger.debug("GET_ORDERS(1) : Requesting open orders using 'self.reqOpenOrders()'")
        self.reqOpenOrders()  # BINDS ORDERS MADE MANUALLY, ASSIGNS A reqId to them   <--------------------------------------------------
        # Taking over orders to be submitted via TWS
        # reqAutoOpenOrders can only be invoked by client with ID 0. It will cause future orders placed from TWS to be 'bound', i.e.
        # assigned an order ID such that they can be accessed by the cancelOrder or placeOrder (for modification) functions by client ID 0."
        # This works the same as the automatic-downloading of orders does when I do anything with IB/TWS from here
        # self.reqAutoOpenOrders(True)
        return

    def orderOperations_cancel(self):
        if self.simplePlaceOid is not None:
            self.cancelOrder(self.simplePlaceOid)

        # Cancel all orders for all accounts
        self.reqGlobalCancel()

    def rerouteCFDOperations(self):
        # ! [reqmktdatacfd]
        self.reqMktData(16001, ContractSamples.USStockCFD(), "", False, False, [])
        self.reqMktData(16002, ContractSamples.EuropeanStockCFD(), "", False, False, [])
        self.reqMktData(16003, ContractSamples.CashCFD(), "", False, False, [])
        # ! [reqmktdatacfd]

        # ! [reqmktdepthcfd]
        self.reqMktDepth(16004, ContractSamples.USStockCFD(), 10, False, [])
        self.reqMktDepth(16005, ContractSamples.EuropeanStockCFD(), 10, False, [])
        self.reqMktDepth(16006, ContractSamples.CashCFD(), 10, False, [])
        # ! [reqmktdepthcfd]

    def marketRuleOperations(self):
        self.reqContractDetails(17001, ContractSamples.USStock())
        self.reqContractDetails(17002, ContractSamples.Bond())

        # ! [reqmarketrule]
        self.reqMarketRule(26)
        self.reqMarketRule(239)
        # ! [reqmarketrule]

    @iswrapper
    # ! [execdetails]
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        # comes from            def reqExecutions
        super().execDetails(reqId, contract, execution)
        debugMsg(reqId, "execDetails()",
                 f"Symbol:, {contract.symbol}, SecType: {contract.secType}, Currency: {contract.currency}, {execution}")
        self.ct_storeExecutions(reqId, contract, execution)

    # ! [execdetails]

    def ct_storeExecutions(self, reqId, contract, execution):
        # https://www.youtube.com/watch?v=dzOilFBDmJI&feature=emb_rel_pause
        ticker = contract.symbol
        account = execution.acctNumber
        strike = contract.strike
        expiry = convert_date(contract.lastTradeDateOrContractMonth)
        putCall = contract.right
        if contract.secType != "OPT":
            _what_am_I = f"{ticker:4}, Shares: {execution.shares}, CumQty: {execution.cumQty}, AvgPrice: {execution.avgPrice}"
        else:
            _what_am_I = f"{ticker:4}, Strike: {strike}, PutCall: {putCall}, Expiry: {expiry}, Shares: {execution.shares}, CumQty: {execution.cumQty}, AvgPrice: {execution.avgPrice}"

        # "right"      : stored as 'putCall' below
        # "multiplier" : processed below
        # TODO: store _ALL_ available fields?
        contract_fields = ["comboLegs", "comboLegsDescrip", "conId", "currency", "deltaNeutralContract", "exchange",
                           "includeExpired",
                           "lastTradeDateOrContractMonth", "localSymbol", "primaryExchange", "secId", "secIdType",
                           "secType",
                           "strike", "symbol", "tradingClass"
                           ]
        execution_fields = ["side", "shares", "time", "acctNumber", "cumQty", "price", "avgPrice", "exchange",
                            "clientId", "evMultiplier",
                            "evRule", "execId", "lastLiquidity", "liquidation", "modelCode", "orderId", "orderRef",
                            "permId"]
        # check why multiplier comes back as ''
        params = create_A_Param("tbl_IB_executions")
        params.updateFromDict({"contract": contract.__str__(),
                               "conId": contract.conId,
                               "ticker": contract.symbol,
                               "putCall": contract.right,
                               "execIdMain": "",
                               "execIdSub": ""})
        #
        res = None
        for field in contract_fields:
            try:
                res = eval(f"contract.{field}")
            except:
                myjoe("")
            if res is None:
                continue
            params.param_dict[field] = res

        if execution.lastLiquidity > 2 or execution.lastLiquidity in variables.UNSET_VALUES:
            lastLiquidity = 0  # crap! Don't store!  2147483647 == weekend expiration?

        for field in execution_fields:  # check if price/avgPrice really are ints
            # params.no_zeros(field, eval(f"execution.{field}"))
            res = eval(f"execution.{field}")
            if res is None:
                continue
            params.param_dict[field] = res

        if contract.multiplier:
            params.param_dict["multiplier"] = float(contract.multiplier)

        # Parse tricky returned fields
        date, mytime = execution.time.replace("  ", " ").split(" ")
        date = convert_date(date)
        params.param_dict["time"] = f"{date} {mytime}"

        execIdMain, execIdSub, *junk = execution.execId.split(".")
        # what is execId here?
        params.param_dict["execIdMain"] = execIdMain
        params.param_dict["execIdSub"] = execIdSub
        params.param_dict["executionDate"] = convert_date(execution.time)
        #
        params.processThis(logIt=True)
        #
        if params.msg in ["added", "updated"]:
            self.GET_POSITIONS()  # request positions again
            self.MD.ib_etrade.IB_things["IB get executions"]["got_fresh_data"] = True

        return

    @iswrapper
    # ! [execdetailsend]
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        if self.things_requested.get("IB get executions", 0) != 0:
            self.things_requested["IB get executions"] -= 1
            set_last_update("IB get executions")
            debugMsg(reqId, "execDetailsEnd()", "execDetailsEnd received")
        reset_last_update("IB get positions", note="Just downloaded executions, got an execDetailsEnd message")

    # ! [execdetailsend]

    @iswrapper
    def commissionReport(self, commissionReport: CommissionReport):
        """ https://interactivebrokers.github.io/tws-api/executions_commissions.html
            When an order is filled either fully or partially, the IBApi.EWrapper.execDetails and IBApi.EWrapper.commissionReport events will deliver
            IBApi.Execution and IBApi.CommissionReport objects. This allows to obtain the full picture of the order's execution
            and the resulting commissions.
        """
        super().commissionReport(commissionReport)
        self.ct_storeCommissionReport(commissionReport)
        return

    def ct_storeCommissionReport(self, commissionReport):
        # FIXME: Look at infinity fields 'realizedPNL'
        newlogger.debug("ct_storeCommissionReport() - START")
        execId = commissionReport.execId
        main, sub, *junk = commissionReport.execId.split(".")
        # qry = f"SELECT ticker, acctNumber FROM tbl_IB_executions WHERE execIdMain='{main}'"
        qry = f"SELECT ticker, acctNumber FROM tbl_IB_executions WHERE execId='{execId}'"
        ticker, account = sql_fetchone(qry)
        #
        tbl_IB_commissions = create_A_Param("tbl_IB_commissions")
        #
        tbl_IB_commissions.updateFromDict({"ticker": ticker, "execId": execId, "execIdMain": main, "execIdSub": sub, })
        fields = ["commission", "currency", "realizedPNL"]
        for field in fields:
            res = eval(f"commissionReport.{field}")
            # params.no_zeros(field, eval(f"commissionReport.{field}"))
            tbl_IB_commissions.param_dict[field] = res
        tbl_IB_commissions.processThis()

        # TRADING_NOTES!
        tbl_positions_params = create_A_Param("tbl_positions")
        tbl_positions_params.updateFromDict({"ticker": ticker,
                                             "account": account,
                                             "commission": tbl_IB_commissions.param_dict["commission"], })
        tbl_positions_params.param_dict["trading_notes"] = get_last_note(ticker, "trading_notes")
        secType_qry = f"select secType from tbl_IB_executions where execId='{commissionReport.execId}'"
        secType = sql_fetchone(secType_qry)
        tbl_positions_params.param_dict["secType"] = secType
        #
        tbl_positions_params.calling_fn = "ct_storeCommissionReport"
        tbl_positions_params.updateOnly()
        #
        if tbl_positions_params.msg == "added":
            newlogger.debug(f"ct_storeCommissionReport(1):  was added to {tbl_positions_params.table}")
            myjoe()
        elif tbl_positions_params.msg == "updated":
            newlogger.debug(
                f"ct_storeCommissionReport(2): tbl_positions was updated for ticker={ticker}, account={account}: {tbl_positions_params.update_msg}")
            # myjoe()

        newlogger.debug("ct_storeCommissionReport() - FINISH")
        return

    @iswrapper
    # ! [currenttime]
    def currentTime(self, time: int):
        super().currentTime(time)
        print("CurrentTime:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"))

    # ! [currenttime]

    @iswrapper
    # ! [completedorder]
    def completedOrder(self, contract: Contract, order: Order,
                       orderState: OrderState):
        super().completedOrder(contract, order, orderState)
        print("CompletedOrder. PermId:", order.permId, "ParentPermId:", utils.longToStr(order.parentPermId), "Account:",
              order.account,
              "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:", contract.exchange,
              "Action:", order.action, "OrderType:", order.orderType, "TotalQty:", order.totalQuantity,
              "CashQty:", order.cashQty, "FilledQty:", order.filledQuantity,
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status,
              "Completed time:", orderState.completedTime, "Completed Status:" + orderState.completedStatus)

    # ! [completedorder]

    @iswrapper
    def completedOrdersEnd(self):
        if "IB get CompletedOrders" in self.things_requested:
            self.things_requested["IB get CompletedOrders"] -= 1
        else:
            raise UserWarning
        super().completedOrdersEnd()
        self.CHECK_FOR_TIME_TO_DISCONNECT()

    @iswrapper
    # ! [replacefaend]
    def replaceFAEnd(self, reqId: int, text: str):
        super().replaceFAEnd(reqId, text)
        print("ReplaceFAEnd.", "ReqId:", reqId, "Text:", text)
    # ! [replacefaend]


if __name__ == "__main__":
    # app = TWS_API_APP(reqId=0, stayAlive=False)
    # app.getOpDefs()
    pass
