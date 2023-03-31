""" Recipes from Python SQLite docs:
    https://rednafi.github.io/reflections/recipes-from-python-sqlite-docs.html
    - Executing individual statements
    - Executing batch statements
    - Applying user-defined callbacks
    - Applying user-defined scalar functions
    - Applying user-defined aggregate functions
    - Printing traceback when a user-defined callback raises an error
    - Transforming types
    - Adapting Python types to SQLite types
    - Converting SQLite types to Python types
    - Implementing authorization control
    - Changing the representation of a row
        Via an arbitrary container object as the row factory
        Via a specialized Row object as the row factory
        Via text factory
    - Creating custom collation
    - Registering trace callbacks to introspect running SQL statements
    - Backing up a database
        Dumping the database iterively
        Copying an on-disk database to another
    - Loading an on-disk database into the memory
    - Copying an in-memory database to an on-disk file
    - Implementing a full text search engine
"""

#from pdb import lasti2lineno

import pandas as pd
from numpy import float64, int64, isnan
import pyperclip
from collections import UserDict
from shutil import copyfile
from queue import Queue
import datetime, sqlite3, sys, os
import logging
from datetime import date
from copy import deepcopy
#
#import data_file
import variables
from dates import sql_format, get_sql_today, get_next_Friday
from dates import should_have_prices_for, convert_date, get_days_ago_date
from dates import get_curtime, get_sql_now, thisMarketIsOpen, get_last_trading_date, get_sql_curtime
import dates
from needs_no_imports import static_vars, myjoe, get_calling_function, variable_in_an_outer_scope
from myMessages import debug_print, debugMsg, warn_print, warnMsg, infoMsg
from variables import DEAD_TICKERS, NEEDS_TO_BE_DONE, DOES_NOT_NEED_TO_BE_DONE, I_AM_NOT_IN_LONDON
from myLogging import mylogger
import telebotTexting


newlogger = mylogger()
TODAY = dates.get_sql_today()
SQL_UTILS_ALLPARAMETERS = {}
DEFINITION_CT = []
MACHINE = os.environ.get("MACHINE")
SAVED_CONNECTION = None


# -------------------------------------------------------------------------------------------------------------------
def create_A_Param(table, fixedDict=None, stayAlive=False):
    """ table     : the table in question, ie, tbl_positions
        fixdDict  : Those values that will stay the same within the function using the parameter
        stayAlive : old code, need to re-implement
    """
    if fixedDict:
        myjoe("2022-10-09 joe = 12  # get rid of 'fixedDict'")

    this_fn, filename, linenum = get_calling_function(withdetails=True)

    if table not in SQL_UTILS_ALLPARAMETERS:
        # Create a new one:
        params = Parameters(table, this_fn, fixedDict, stayAlive, filename, linenum)
        SQL_UTILS_ALLPARAMETERS[table] = params
        return params

    # Get an existing one:
    params = SQL_UTILS_ALLPARAMETERS[table]
    if params.needToProcess is True:
        msg = f"create_A_Param(): Table: '{params.table}', '{params.filename}' line #{params.linenum} did not set 'needToProcess' back to False! (Do not do a 'param' from within a 'param')"
        warn_print(f"\n\t*** {msg}")
        myjoe()

    params.process_a_fixed_dict_NEW(this_fn, fixedDict)
    params.clear_it()

    params.filename = filename
    params.linenum = linenum
    params.needToProcess = True
    return params


# -------------------------------------------------------------------------------------------------------------------
class Parameters:

    def __init__(self, table, fn=None, fixedDict=None, stayAlive=False, filename=None, linenum=None):
        # Parameters:
        self.table = table
        self.DO_NOT_AUTOLOG = (table == "tbl_errors")
        self.last_fn = fn
        #self.fn_startingDicts = {fn: fixedDict,}
        self.STAY_ALIVE = stayAlive
        self.filename = filename
        self.linenum = linenum
        #
        self.param_dict = None  # Set to 'myParamDict()' in self.initialize() below
        self.fixedDict = {}     # Properly set in self.initialize() below
        self.fixedFields = []   # related to 'fixedDict' code
        #
        self.BAD_RESULT = -99999
        self.DEBUG, self.UPDATEONLY, self.flagMissingFields = False, False, False
        self.QUEUE = Queue()
        self.can_not_be_null, self.constraint_arr, self.fieldNotInTable = [], [], []
        self.constraint_query, self.silents, self.only_etrade_tickers = None, None, None
        self.creation_time = get_sql_now()
        self.defaults_dict = {"curtime": get_sql_curtime()}
        self.differences, self.field_types = {}, {}
        self.fields, self.fieldsThisUpdate, self.missingFields = [], [], []
        self.msg, self.ticker, self.update_msg = "", "", ""
        self.needToProcess = True
        self.isNowFalse, self.non_silent_constraints, self.non_silent_param_dict = {}, {}, {}
        self.orig_values_dict, self.was_defaulted_dict = {}, {}
        #
        self.NO_NEW_VARIABLES = True  # <---- leave this as the very last line of the __init__
        #
        self.Parameters_initialize(fixedDict)
        return


    def Parameters_initialize(self, init_fixedDict=None):
        from orderDict import myParamDict
        # self.param_dict = myParamDict(table=table, fields=self.fields)  #  myData()  #   cls_param_dict(self)  # {}   <----------------------------------------
        self.creation_time = get_sql_now()
        self.silents = self.get_silent_updates()
        self.fields = self.get_table_definitions()
        self.param_dict = myParamDict(table=self.table, fields=self.fields)
        if init_fixedDict:
            assert not self.fixedDict  # to make sure I am being called at the right time, and not for an already created Parameter
            assert isinstance(init_fixedDict, dict)
            self.process_a_fixed_dict_INIT(init_fixedDict)
        if self.table == "tbl_positions":
            self.only_etrade_tickers = sql_execute("select distinct ticker from tbl_positions where only_etrade=True")
        return


    def process_a_fixed_dict_INIT(self, init_fixedDict):
        """ When I call this from a Parameters.__init__(), I have set self.fixedDict and then call this via initialize()
            When I call this from a 'used' Parameter, I call 'process_starting_dict' directly, with 'p_startingDict' set
        """
        assert init_fixedDict      # or else why am I being called?
        assert not self.fixedFields   # This is a very first fixedDict, so .fixedFields should be blank
        assert not self.fixedDict  # This is a very first fixedDict, so .fixedFields should be blank
        newlogger.debug(f'process_a_fixed_dict_INIT1) : Calling function: "{self.last_fn}" is processing "{self.table}", with init_startingDict: {init_fixedDict}')

        fixedFields = list(init_fixedDict.keys())
        for field in fixedFields:
            self.param_dict[field] = find_field_type_in_tables()[field]
        self.fixedFields = fixedFields
        self.fixedDict = init_fixedDict
        return


    def process_a_fixed_dict_NEW(self, this_fn, new_fixedDict=None):
        """ When I call this from a Parameters.__init__(), I have set self.fixedDict and then call this via initialize()
            When I call this from a 'used' Parameter, I call 'process_starting_dict' directly, with 'p_startingDict' set
        """
        # -------------------------------------------------------------
        def wipe_it():
            self.fixedDict = {}
            self.fixedFields = []
            if new_fixedDict:
                _fixedFields = list(new_fixedDict.keys())
                for field in _fixedFields:
                    self.param_dict.pop(field)
                self.fixedFields = _fixedFields
            return
        # -------------------------------------------------------------
        if new_fixedDict is None:
            new_fixedDict = {}
        old_fixedDict = self.fixedDict
        table = self.table

        # Case 0: Different function, wipe it, because maybe Fn1 sets broker, but Fn2 doesn't
        last_fn = self.last_fn
        if this_fn != last_fn:
            wipe_it()
        else:
            # Case 1: It's the same function, but are the fixedDicts the same?
            if new_fixedDict == old_fixedDict:
                # Yes, nothing to do
                return
            else:
                myjoe("now what??")  # 2022-10-09

        # Case 2: An existing fixedDict is not being replaced, but for safety its existing values should be reset
        if bool(old_fixedDict) is True and bool(new_fixedDict) is False:
            for field in self.fixedFields:
                tmp = self.param_dict[field]  # Kludge to get default value
                self.no_zeros(field, tmp)
            self.fixedDict = {}
            return

        # Case 3: A blank fixedDict is being replaced with a new one --OR-- the functions have changed, so everything should be blown out
        newlogger.debug(f'process_a_fixed_dict_NEW(0): Fn: "{last_fn}" is processing "{table}", with fixedDict: {new_fixedDict}')
        if old_fixedDict:
            newlogger.info(f'process_a_fixed_dict_NEW(1): Fn: "{last_fn}" is processing "{table}", which had a previous fixedDict of: {old_fixedDict}')
        wipe_it()

        #
        fixedFields = list(new_fixedDict.keys())
        resetList = []
        for key in self.param_dict.keys():
            if key not in fixedFields:
                resetList.append(key)
        for field in resetList:
            self.param_dict.pop(field)
        #
        if new_fixedDict:
            fixedFields = list(new_fixedDict.keys())
            for field in fixedFields:
                self.param_dict[field] = new_fixedDict[field]
        self.fixedFields = fixedFields

        # Note: this is new, first time being hit
        self.fixedDict = new_fixedDict  # <-----

        return


    def clear_it(self):
        """ Blank out old values so it starts fresh
            Note: BECAUSE I CALL THIS FROM WITHIN LOOPS, I DO NOT WANT TO RESET 'FIXEDFIELDS' HERE  ***  2022-09-13!
        """
        self.missingFields = []
        self.non_silent_param_dict = {}
        self.non_silent_constraints = {}
        self.UPDATEONLY = False
        #
        _len_keys_before = len(self.param_dict.keys())
        resetList = []
        for key in self.param_dict.keys():
            if key not in self.fixedFields:
                resetList.append(key)
        for field in resetList:
            self.param_dict.pop(field)
        _len_keys_after = len(self.param_dict.keys())

        #assert set(self.param_dict.keys()) == set(self.fixedFields)
        if set(self.param_dict.keys()) != set(self.fixedFields):
            print(f"clear_it(1): set(self.param_dict.keys()) = '{set(self.param_dict.keys())}'")
            print(f"clear_it(1): set(self.fixedFields)       = '{set(self.fixedFields)}'")
            myjoe("")  # why not?
        return


    def __setattr__(self, key, value):
        if key == "param_dict" and isinstance(value, dict):
            myjoe("do not set param_dict directly")
        super().__setattr__(key, value)
        return

    def __repr__(self):
        return f"'{self.table}' Parameters"

    def __str__(self):
        if "ticker" in self.param_dict:
            ticker = self.param_dict["ticker"]
            return f"'{self.table}' Parameters ({ticker})"
        return f"'{self.table}' Parameters"


    @static_vars(skipped=[])
    def updateFromDict(self, param_dict, can_overlook_fields_not_in_the_table=False):
        """ In general, I'd like to be able to pass in a large dict, and only take the fields from it that I need.
            But I do need to flag when a field I otherwise think is being filled in, is being overlooked because
            it's not in the table
        """
        # can_overlook_fields_not_in_the_table = self.table in ["tbl_IB_stock_contract_details", "tbl_recommendations", "tbl_last_updates"]
        table = self.table
        for field, value in param_dict.items():
            # key = (field, self.table)
            if field in self.field_types:
                self.param_dict[field] = value
            else:
                if can_overlook_fields_not_in_the_table is False:
                    myjoe("do I really want to ignore fields here?")
                    fld = f"'{field}'"
                    fn = get_calling_function()
                    newlogger.warning(f"updateFromDict(1) : '{fn}' is trying to add field {fld:20} to table '{self.table}' which doesn't have it")
                    _key = (field, self.table)
                    if _key not in self.updateFromDict.skipped:
                        self.updateFromDict.skipped.append(_key)
        return

    def get_silent_updates(self):
        """ """
        silent_updates = {
            "tbl_IB_orders": ["is_live"],
            "tbl_last_updates": ["last_update", "time_stamp"],
            "tbl_options": ["get_greeks"],
            "tbl_alerts": ["last", "buy_dip_price"],
            "tbl_prices": ["reqId"],
            "tbl_ALGO_ORDERS": ["last_live_check"],
            "tbl_morning_report": ["value"],
            "tbl_dividends": ["UTC_ex_date", "record_date"],
            "tbl_etrade_balances": ["value"],
            "tbl_etrade_orders": ["orderValue", "estimatedFees", "placedTime2"],
            "tbl_positions": ["last_update", "name", "shortName", "conId", "quoteStatus", "positionId", "last_div_update"],
            "tbl_etrade_positions": ["quoteStatus", "volume", "lastTradeTime", "pctOfPortfolio", "daysGain", "daysGainPct", "marketValue",
                                     "totalGain", "totalGainPct", "pctOfPortfolio", "change", "changePct", "lastTrade", "adjPrevClose"
                                                                                                                        "good_position", "adjPrevClose"],
            "tbl_IB_option_contract_details": ["liquidHours", "tradingHours", "category", "industry", "subcategory", "lastTradeTime"],
        }
        silents = silent_updates.get(self.table, ["table"]) + ["curdate", "curtime", "source", "reqId", "lastUpdate"]
        return silents

    def get_table_definitions(self):
        """ Get the definition of the table """
        MAINFRAME_TABLES = ["tbl_earnings_dates",       "tbl_etrade_balances", "tbl_etrade_orders",
                            "tbl_etrade_portfolio",     "tbl_etrade_prices",   "tbl_exchange_rates",
                            "tbl_historical_data",      "tbl_holidays",        "tbl_option_trades",
                            "tbl_pnl", "tbl_spin_offs", "tbl_strikes",         "tbl_trades_to_do"]
        table = self.table
        if table in MAINFRAME_TABLES:
            myjoe("# FIXME: this needs to be updated for which database the table is in")
        if table in DEFINITION_CT:
            myjoe("# I should not get the same table definition twice!")
        else:
            DEFINITION_CT.append(table)
            fn = get_calling_function()
            #newlogger.debug(f"get_table_definitions(1): Fn: {fn} - Processing '{table}'")

        qry = f"SELECT sql FROM sqlite_master WHERE tbl_name='{table}' AND type='table'"
        sql = sql_fetchone(qry)  # Note: I can't just do 'sql = sql.lower()' as that will clobber the field names too
        assert sql  # spelled table name wrong probably
        #
        all_lines = AllLines(sql)
        for ct in range(len(all_lines)):
            line = all_lines[ct]
            if line.lower().find("constraint ") != -1:
                # WATCH OUT WHEN 'constraint' DOESN'T OCCUR AT THE BEGINNING OF THE LINE!
                # Found a primary key or "unique" constraint
                if line.find("autoincrement") != -1:
                    continue  # not one I can work with
                if line.find("references") != -1:
                    fld, fld_type, *res = line.split()
                    self.constraint_arr.append(fld)
                    self.field_types[fld] = fld_type.lower()
                    continue  # not one I can work with
                pos1 = line.find("(")
                pos2 = line.find(")")
                if pos1 == -1 and pos2 == -1:
                    # Just a single field constraint
                    fld, fld_type, *res = line.split()
                    self.constraint_arr.append(fld)
                    self.field_types[fld] = fld_type.lower()
                    continue
                else:
                    constraint_fields = line[pos1 + 1:pos2]
                    constraint_fields = constraint_fields.replace(",", "")
                    for fld in constraint_fields.split(" "):
                        if fld not in self.constraint_arr:
                            self.constraint_arr.append(fld)
                    continue  # I continue because these fields get repeated later
            # !!!!! CONSTRAINT  CONSTRAINT  CONSTRAINT  CONSTRAINT  CONSTRAINT  CONSTRAINT  CONSTRAINT  CONSTRAINT !!!!!
            else:
                items = line.split(",")
                for xx in items:
                    assert xx != ''
                    arr = xx.split(" ")
                    fld, fld_type = arr[0], arr[1]
                    if fld:
                        self.field_types[fld] = fld_type.lower()

            # -------------------------------------------------------------------------------------------------------------------
            if line.lower().find("default") != -1:
                arr = line.split(" ")
                field = arr[0]
                theDefault = arr[3]
                if theDefault == TODAY:
                    theDefault = get_sql_today()
                if theDefault == "CURRENT_TIME":
                    theDefault = f"{get_sql_today()} {get_sql_now()}"
                if theDefault not in ['', "", "''", '""']:  # != "''":
                    # Don't store '' as a default - the idea is SQL will automatically do this for me
                    self.defaults_dict[field] = theDefault
            # -------------------------------------------------------------------------------------------------------------------
            """ 'NOT NULL LOGIC': Don't do this anymore - let the code crap out where it is missing the value, if the value is missing!
                                  If I make it a 'fake constraint' field, then it screws up the selection/insertion later on if this
                                  'fake constraint' field changes its value
            """
            if line.find("not null") != -1:
                arr = line.split(" ")
                field = arr[0]
                self.can_not_be_null.append(field)
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # if line.find("null") != -1:
            #    # Found a 'not null' constraint
            #    fld, *res = line.split(" ")
            #    if fld not in constraint_arr:
            #        constraint_arr.append(fld)
        if "update_msg" not in self.field_types and table not in ["tbl_exceptions_raised", "z_space_used"]:
            myjoe("why not?")
        return set(self.field_types.keys())

    def sql_fn_call(self, qry, conn):
        try:
            if conn:
                res = sql_execute(qry, conn=conn, commit=False, close=False)
            else:
                try:
                    res = sql_execute(qry)
                except sqlite3.OperationalError:
                    # Do a commit first?
                    raise
        except sqlite3.IntegrityError:
            err = f"{sys.exc_info()[1]}"
            print()
            print(f"sql_fn_call(1): Unexpected error: {sys.exc_info()[1]}")
            print(f"\n\t{qry}")
            print()
            if err.find("NOT NULL constraint failed") != -1:
                print(f"I need the following fields in table '{self.table}' to be filled in:")
                for xx in self.can_not_be_null:
                    if not xx in self.param_dict:
                        print(f"\t{xx} : missing!")
            raise
        return res

    def checkNotNullIsSatisfied(self, raiseError: bool = True, query_used: str = ""):
        """ raiseError: Bool.
            query_used: String
        """
        if self.UPDATEONLY is True:
            return
        for field in self.can_not_be_null:
            if field in self.param_dict.keys() or field in self.defaults_dict:
                continue
            msg = f"checkNotNullIsSatisfied(1): ERROR? Do you need to supply NOT NULL field '{field}' for table '{self.table}'?"
            print(msg)
            newlogger.error(msg)
            if raiseError and query_used:
                print(f"\tcheckNotNullIsSatisfied(2): {query_used}\n")
                raise UserWarning
        return

    def doSimpleErrorChecking(self, I_got_multiples_FLAG=False, updateOnly: bool = False):
        if self.UPDATEONLY != updateOnly:
            myjoe("get rid of the 'updateOnly' parameter?")  # FIXME: get rid of the 'updateOnly' parameter?

        # NOTE: Because I sometimes do 'UpdateOnly()', not all 'obvious' fields may be filled in

        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_IB_option_contract_details():
            if "quarterly_expiration" not in self.param_dict:
                myjoe("please provide!")
        # -------------------------------------------------------------------------------------------------------------------
        def check_table(table, field, for_what):
            if self.table == table:
                if field not in self.param_dict:
                    myjoe()  #
                else:
                    eval_str = f"{field} {for_what}"
                    _res = eval(eval_str)
            return
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_account_summary():
            field = self.param_dict["field"]
            value = self.param_dict["value"]
            if value in ['0', '0.00']:
                myjoe("Do not store no-values anymore!")
            if self.param_dict["RealizedPnL"]:
                myjoe("got an update! check it out!")
            if not self.param_dict["broker"]:
                myjoe("fill it in!")
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_options():
            if "conId" not in self.param_dict:
                myjoe("Can not be null 1!")
            else:
                if not self.param_dict["conId"]:
                    myjoe("Can not be null 2!")
            if "IB_expiry" not in self.param_dict:
                myjoe()
            if self.param_dict["expiry"] < get_sql_today():
                myjoe("")
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_recommendations():
            if self.param_dict["expiry"] and not self.param_dict["IB_expiry"]:  # either both filled in, or neither?
                myjoe("")
            if "optionPrice" in self.param_dict:
                _joe = 12  # check out who does this")
            if "lmtPrice" in self.param_dict:
                _tmp = self.param_dict["lmtPrice"]
                # if not self.param_dict["lmtPrice"]:
                if bool(_tmp) is False:
                    _joe = 12  # for debugging
                else:
                    _joe = 12  # for debugging
            if self.param_dict["secType"] == "STK":
                if self.param_dict["putCall"]:
                    myjoe("'putCall' should be blank for a STK!")
                if self.param_dict["strike"]:
                    myjoe("'strike' should be blank for a STK!")
            if self.param_dict["action"] and self.param_dict["action"] is None:
                myjoe("")
            if self.param_dict["gotGreeks"]:
                _joe = self.param_dict["gotGreeks"]
                # myjoe("check who updates this")  # still?
            if "conId" in self.param_dict:
                # thislogger.warning(f"Function {self.last_fn} is writing 'conId' to tbl_recommendations")
                try:
                    _res = float(self.param_dict["conId"])  # to make sure it is numeric
                except:
                    myjoe()  # check it isn't an object
            if "permId" in self.param_dict:
                if self.param_dict["permId"] == "":
                    raise UserWarning  # get rid of this, why blank it out if it may already be there?
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_pnl():
            # if self.table == "tbl_pnl":
            myjoe("Whoa! Who uses this table??")
            if "income" in self.param_dict:
                raise UserWarning  # check this calculation out
        # -------------------------------------------------------------------------------------------------------------------
        def check_missing_fields(I_got_multiples_FLAG: bool = False):
            # 'I_got_multiples_FLAG' means: An SQL quesry returned multiple rows, which I can not update. So figure out what went wrong
            for field, fldtype in self.field_types.items():
                if field not in self.param_dict and field not in ["curdate"] and field not in self.defaults_dict:
                    if field not in self.missingFields:
                        self.missingFields.append(field)
            if self.UPDATEONLY is False and (self.flagMissingFields is True or I_got_multiples_FLAG is True):
                # if self.missingFields:
                newlogger.info(f"\n\t*** The param_dict for table '{self.table}' is missing fields: {self.missingFields}\n")
                #myjoe()  # raise UserWarning
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_prices():
            # updating tbl_positions.mktval takes place in 'doPostSQLOperations'
            if self.param_dict["ticker"] == "MS PRF" and self.param_dict["conId"] == "MS PRF":
                self.param_dict["conId"] = "139808284"  # this will bleed upwards
            if self.param_dict["secType"] == "OPT" and self.param_dict["conId"] == self.param_dict["ticker"]:
                myjoe("why??")
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_positions():
            ticker = self.param_dict["ticker"]
            #
            if not self.param_dict["machine"]:
                self.param_dict["machine"] = MACHINE
            #
            if self.UPDATEONLY is False and "notes" not in self.param_dict:
                myjoe("make sure I have 'notes' carried forward")
            #
            #if ticker == "WBD":  # TODO: Pay attention to when this gets dividends!
            #    self.param_dict["divYield"] = 0.00001
            #
            if ticker == "MS PRF" and self.param_dict["conId"] == "MS PRF":
                myjoe("set conId to '139808284'")
            #
            if "only_etrade" in self.param_dict:
                if self.param_dict["only_etrade"] != (ticker in self.only_etrade_tickers):
                    myjoe()  # why did this happen?
            #
            if self.param_dict["divYield"] > 7 and ticker not in ["EWG", "QQQX", "T", "MO"]:  # T: 8.3%!  MO: 7.7%!
                msg = f"*** Big divyield!  Ticker: {self.param_dict['ticker']}, divYield: {self.param_dict['divYield']:,.4f}"
                print(f"\n\tcheck_tbl_positions(): {msg}")
                newlogger.critical(msg)
                myjoe("")  #
            #
            if "divYield" in self.param_dict and self.param_dict["divYield"] == 0:
                msg = f"*** Why are you setting a divYield to zero?"
                print(f"\n\t{msg}")
                newlogger.critical(msg)
                myjoe("")  #
            #
            if self.param_dict["good_position"] and self.param_dict["shares"] == 0:
                myjoe("")  # raise UserWarning
            #
            if not self.UPDATEONLY and "trading_notes" not in self.param_dict and get_last_note(ticker, "trading_notes"):
                newlogger.info(f"{self.last_fn} is missing a value for 'trading_notes'..")
                self.param_dict["trading_notes"] = get_last_note(ticker, "trading_notes")
                myjoe("")  # raise UserWarning
        # -------------------------------------------------------------------------------------------------------------------
        def check_ALGO_ORDERS():
            if "is_live" not in self.param_dict:
                raise UserWarning  # error, supply it as TRUE!
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_IB_Orders():
            if "is_live" not in self.param_dict:
                raise UserWarning  # error, supply it as TRUE!
            if self.param_dict["is_live"] is False:
                raise UserWarning  # check that value is TRUE?
            if len(self.param_dict.get("contract", "")) > 50:
                myjoe()
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_dividends():
            ticker = self.param_dict["ticker"]
            dividend = self.param_dict["dividend"]
            for field in ["broker", "pos", "expected_income"]:
                if not self.param_dict[field]:
                    broker = get_broker(ticker)
                    pos = get_position(ticker)
                    if not broker or not pos:
                        myjoe("check_tbl_dividends:595")  # debug first time then remove
                    self.param_dict["broker"] = broker
                    self.param_dict["pos"] = pos
                    self.param_dict["expected_income"] = round(pos * dividend, 4)
            if self.param_dict["split"]:
                myjoe("Make sure it is handling it properly. See 'split_adjust_amazon' code")
            if self.last_fn not in ["storeDividends", "ct_uploadDividends", "nasdaq_download_dividends"]:
                # These functions already check for duplicated dividends, no need to do it again here
                ticker = self.param_dict["ticker"]
                ex_date = self.param_dict["ex_date"]
                dividend = self.param_dict["dividend"]
                ex_div_month_start = f"{ex_date[:7]}-01"
                ex_div_month_end = f"{ex_date[:7]}-31"
                # Make sure I don't already have a dividend for this same month
                qry = f"select split, curtime, ticker, ex_date, dividend, source, record_date, pay_date from tbl_dividends " \
                      f"where ticker='{ticker}' and ex_date>='{ex_div_month_start}' and ex_date<='{ex_div_month_end}' " \
                      f"and not split=True and not (ex_date='{ex_date}' and dividend={dividend}) order by ex_date"
                res = sql_execute(qry)
                if res:
                    qry2 = f"select split, curtime, ticker, ex_date, dividend, source, record_date, pay_date from tbl_dividends " \
                           f"where ticker='{ticker}' and ex_date>='{ex_div_month_start}' and ex_date<='{ex_div_month_end}' " \
                           f"and not split=True order by ex_date"
                    pyperclip.copy(qry2)
                    print(f"\ntbl_dividends: Ticker: {ticker} - I am trying to process a ${dividend:,.4f} for ex_date: {ex_date}")
                    print(f"\tbut there are already these results in tbl_dividends:\n")  # delete bad from table, then accept new dividend down below
                    for row in res:
                        split, curtime, ticker, ex_date, dividend, source, record_date, pay_date = row
                        print(f"\tEx_date: {ex_date}, dividend: {dividend:,.4f}, Source: {source}")
                    print(); myjoe()
                    fromwhere = self.last_fn
                    if self.last_fn == "storeDividends":
                        fromwhere = "ETrade"
                    ans = input(f"Accept entry from {fromwhere}? (y)")  # query copied, delete wrong div from table, hit F9
                    # delete from tbl_dividends where ticker='PG' and ex_date='2022-01-27';
                    if ans.lower() != "y":  # <------------- ACCEPT HERE after deleting
                        raise UserWarning  # Do NOT add additional rows here, figure out on a higher level why I haven't caught the duplication
        # -------------------------------------------------------------------------------------------------------------------
        def misc_checks(table):
            if TODAY < "2022-12-01":
                if table == "tbl_holidays":
                    myjoe("")  # does this get hit anymore? 9/6/2022
            else:
                myjoe("revert")  # get rid of tbl_holidays, I use 'holidays.json' instead
            #
            if self.UPDATEONLY is True and "curdate" in self.param_dict and self.param_dict["curdate"] == "CURRENT_DATE":
                myjoe("")  # huh? Get rid of this value for curdate
            #
            if "timeZoneId" in self.param_dict:
                if self.param_dict["timeZoneId"] == "EST5EDT":
                    myjoe("")  # check this, https://groups.io/g/twsapi/topic/93271054

            if "IB_expiry" in self.param_dict:
                if self.param_dict["IB_expiry"].find("-") != -1:
                    raise UserWarning  # bad value! I need 20211203 here
            for key, value in self.param_dict.items():
                if isinstance(value, (int, float)):
                    if abs(value) in variables.UNSET_VALUES:
                        if key.lower() == "realizedpnl":
                            # The APIs have both 'realizedPnL' as well as 'realizedPNL'
                            value = 0
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_IB_option_contracts_needed():
            # if self.table == "tbl_IB_option_contracts_needed":
            contractMonth = self.param_dict.get("contractMonth", "")
            if len(contractMonth) > 6:
                # Should be "202204", not "20220422"
                self.param_dict["contractMonth"] = contractMonth[:6]
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_last_updates():
            what = self.param_dict.get("what", "")
            if what.find('""') != -1:
                myjoe("what is doing this???")
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_etrade_balances():
            if "accountBalance" in self.param_dict:
                if self.param_dict["accountBalance"] == "0":
                    myjoe("")
        # -------------------------------------------------------------------------------------------------------------------
        def check_tbl_errors():
            if self.param_dict["source"] == "addTitleBar":
                myjoe("")  # Should this be 'checkWidths' instead?
            if self.param_dict["errorCode"] == "checkwidth":
                if "blockName" in self.param_dict:
                    what = self.param_dict["blockName"]
                else:
                    what = self.param_dict["report"]
                errorString = self.param_dict["errorString"]
                print(f"\n\t*** Error! {what=} - {errorString=} !")
                myjoe("debug this! Fix the report right now, it's quicker than later")  # Note: You must have adjusted the data after setting the reportDATA= variable
        # -------------------------------------------------------------------------------------------------------------------
        table = self.table
        ticker = self.param_dict["ticker"]
        if self.param_dict["ticker"] in DEAD_TICKERS:
            myjoe()

        # 1) see if I have a "check_table" function for this table:
        potential_check_function = f"check_{self.table}"
        if potential_check_function in locals():
            fn = locals()[potential_check_function]
            fn()
        check_missing_fields(I_got_multiples_FLAG)

        # 2) Do miscellaneous checks:
        misc_checks(table)

        # 3)
        param_dict_copy = deepcopy(self.param_dict.data)
        #
        for param_field, param_value in param_dict_copy.items():
            if param_field not in self.field_types.keys():
                # TODO: Do I ignore this? Or flag it?
                # find_column_in_tables(col=param_field, justTables=True)
                self.fieldNotInTable.append(param_field)
            if param_value == "0" and self.table == "tbl_account_summary":
                print(f"\n\tNO! DO NOT GIVE ME A '0' as value for field '{param_field}' in 'tbl_account_summary'!")
                raise UserWarning
        if bool(self.fieldNotInTable):
            _msg = f"doSimpleErrorChecking(2): The following fields are not in table '{self.table}': '{', '.join(self.fieldNotInTable)}'"
            warn_print(_msg, printIt=True)
            myjoe("raise AttributeError  # catch this up above in calling function, then")

        # -------------------------------------------------------------------------------------------------------------------
        # 4) curdate/curtime checks:
        # -  when not given, 'curdate' should be TODAY:
        if "curdate" in self.field_types and "curdate" not in self.param_dict:
            self.param_dict["curdate"] = TODAY  # get_sql_today()

        # - this is for debugging, can be removed eventually:  2022-09-22
        if self.table == "tbl_positions":
            curtime = self.param_dict["curtime"]
            _joe = 12  # Fixme: curtime is getting blanked out!
        if self.table == "tbl_positions" and "curtime" not in self.field_types:
            myjoe("")  # how did this happen? Why is curtime not being set?

        # - when updating only, I should not have a curtime value as it won't match the existing record:
        if self.UPDATEONLY is False:
            if "curtime" in self.field_types and "curtime" not in self.param_dict:
                self.param_dict["curtime"] = get_curtime()
        else:
            if "curdate" in self.field_types and "curdate" not in self.param_dict:
                myjoe("")  # now what?
            if "curtime" in self.field_types and "curtime" not in self.param_dict:
                pass  # I do not think this is important when doing an updateOnly()
        # -------------------------------------------------------------------------------------------------------------------
        # 5)
        if "source" in self.field_types:
            if "source" not in self.param_dict:
                if self.last_fn == "nasdaq_download_dividends":
                    self.param_dict["source"] = "nasdaq.com"
                else:
                    self.param_dict["source"] = self.last_fn
        if updateOnly is False:
            self.checkNotNullIsSatisfied()
        return

    def printMembers(self, vals_too=False):
        res = variable_in_an_outer_scope("key")
        if res:
            myjoe("")
        for key, value in self.param_dict.items():
            if vals_too:
                print(f"{key} - {value}")
            else:
                print(key)

    @ staticmethod
    def setupSQLLogging():
        """
        # https://docs.python.org/2/howto/logging-cookbook.html#logging-to-multiple-destinations
        name = "myapp.sqllog"  # (p_name.split("."))[-1]
        # __name__????
        # I create "myapp" logger first, and then hang any new logger off it, just so I can
        # turn off 'propagate' for it so it doesn't go up to any root logging as well
        applogger = logging.getLogger(f"myapp")  # "market_data")
        applogger.propagate = False     # stop anything from going upstream to "root"
        applogger.setLevel(logging.NOTSET)
        applogger.debug("-" * 100)

        #log_filename = time.strftime("Logs/my_log_%Y-%m-%d.txt")
        sql_filename = time.strftime("Logs/SQL/sql_log_%Y-%m-%d.txt")
        recfmt = f"%(asctime)s.%(msecs)03d [{name}] %(levelname)s %(message)s"
        timefmt = '%H:%M:%S'

        sqllogger = logging.getLogger(f"myapp.sqllog.{name}")
        sqllogger.propagate = False
        sqllogger.setLevel(logging.DEBUG)
        sqlfmt = logging.Formatter(recfmt, datefmt=timefmt)

        sqllogger.debug("")
        sqllogger.info(f"setupSQLLogging(): Opened a pipe to: myapp.sqllog.{name} .. **********************************")
        sqllogger.debug("")
        return sqllogger
        """
        sqllogger = logging.getLogger("myapp.sqllog")
        return sqllogger

    def get_nice_value(self, field):
        value = self.param_dict[field]

        mega_default_type = {"table": "text", "ticker": "text", "account": "text", "ask": "float", "bid": "float",
                             "broker": "text", "curdate": "date", "dividend": "float", "ex_date": "date", "exchange": "text",
                             "expiry": "text", "symbol": "text"}
        need_type = self.field_types.get(field, mega_default_type.get(field, "")).lower()

        if need_type == "":
            raise AttributeError

        if isinstance(value, float64):
            if isnan(value):
                return self.BAD_RESULT  # False

        # Was majorly updated July 28, 2021
        res = None
        if need_type == "text":
            value = str(value).replace("\"", "'")
            if str(value).find('"') != -1:
                print("\n\t*** Don't do this! Use single quotes!!!")
                print(f"\n\t*** Value='{value}'")
                raise UserWarning
            if str(value) == "''":
                res = value
            elif str(value).find("'") != -1:
                # Since I construct my queries above using "..."
                res = value
                res = res.replace("'", '"')
                res = f"'{res}'"
            elif value is not None:
                res = f"'{value}'"
            else:
                print(f"\n\t1 Table: {self.table}, Field: {field}, Need_type: {need_type}, Value: {value}, ")
                return self.BAD_RESULT
                # res = ""  # "is NULL"

        elif need_type == "float":
            try:
                if isinstance(value, (float64, float, int64, int)):
                    res = float(value)
                elif not check_is_num(value):
                    # if not f"{value}".isnumeric():
                    print(f"\n2) ERROR! I need a '{need_type}' for field='{field}', you gave me [{value}]!")
                    return self.BAD_RESULT  # False
                else:
                    res = float(value)
            except ValueError as err:
                fn = get_calling_function()
                print(f"\n\t*** Function: '{fn}' is trying to store a non-float of '{value}' to table.field: '{self.table}.{field}'")
                raise

        elif need_type == "int" or need_type == "integer":
            if int(value) == value:
                # new 'Decimal' type?
                value = int(value)
            if isinstance(value, int64) or isinstance(value, int):
                res = int(value)
            elif isinstance(value, float) or isinstance(value, float64):
                if int(value) != value:
                    print(f"\n(3c) WARNING! {self.table}-{field} : Loss of precision converting a float ({value}) to an int ({int(value)})!")
                res = int(value)
            elif isinstance(value, str):
                if value == '':
                    return self.BAD_RESULT
                pos = value.find(".")
                if pos != -1:
                    # Was I given a float?
                    print(f"\n3b) WARNING! Loss of precision converting a float ({value}) to an int ({value[:pos]})!")
                    res = value[:pos]
                else:
                    res = int(value)
            else:
                raise ValueError

        elif need_type == "date":
            if isinstance(value, str):
                if bool(value) is False:
                    return
                res = sql_format(value)
                if res is False:
                    if value.find("CURRENT_") != 0:
                        print(f"\nERROR! I need a valid 'date' for field='{field}', you gave me -->{value}<--!")
                        return self.BAD_RESULT  # False
                    else:
                        return f"{value}"
            else:
                res = value.strftime("%Y-%m-%d")
            res = f"'{res}'"

        elif need_type == "time":
            if isinstance(value, str):
                res = sql_format(value)
                if res is False:
                    if value.find("CURRENT_") != 0:
                        print(f"\nERROR! I need a valid 'time' for field='{field}', you gave me [{value}]!")
                        return self.BAD_RESULT  # False
                    else:
                        return f"{value}"
            else:
                res = value.strftime("%Y-%m-%d")
            res = f"'{res}'"

        elif need_type in ["float", "int", "double"]:
            res = f"{value}"

        elif need_type == "boolean":
            res = f"{bool(value)}"
            _check_itisaboolean = 12

        elif need_type in ["string", "txt"]:
            print("You screwed up, you meant to use 'text' in the table definition. Do a 'modify' on it..")
            myjoe()
        elif need_type == "blob":
            print(f"\n\t2 Table: {self.table}, Field: {field}, Need_type: {need_type}, Value: {value}")
            myjoe()  # now what?

        else:
            print(f"\n\t3 Table: {self.table}, Field: {field}, Need_type: {need_type}, Value: {value}")
            myjoe()
            raise ValueError  # I should never get here again
        return res

    def createSQLStrings(self) -> dict:
        _table = self.table
        # ----------------------------------------------
        # Creat the SQL strings for the param data given
        # ----------------------------------------------
        # 1) Select versus any constraint
        sel_flds = ""
        selection_where = ""
        selection_query = ""
        # constraint_flds = ""
        constraint_where = ""
        ins_flds = ""
        ins_values = ""
        where_clause = ""

        up_qry = f"UPDATE {self.table} SET "
        insertion_qry = f"INSERT INTO {self.table} "
        # ins_flds, ins_values, where_clause = "", "", ""
        # TODO: Expand things so I can do a multiple update. Like, I have PFE in both ETrade and IB and I want
        #       to update divyield
        if self.constraint_arr:
            for field in self.constraint_arr:
                if field not in self.param_dict.keys():
                    if self.UPDATEONLY and field == "curtime":
                        #myjoe("")  # now what?
                        continue
                    if field in self.defaults_dict.keys():
                        self.param_dict[field] = self.defaults_dict[field]
                        self.was_defaulted_dict[self.table] = f"{field}: {self.defaults_dict[field]}"
                    else:
                        continue
                val = self.get_nice_value(field)
                if val != self.BAD_RESULT:
                    if val != "":
                        sel_flds += f"{field}, "
                        ins_flds += f"{field}, "
                        if val != "is NULL":
                            ins_values += f"{val}, "
                            selection_where += f"{field}={val} AND "
                            constraint_where += f"{field}={val} AND "
                            where_clause += f"{field}={val} AND "
                        else:
                            raise UserWarning
                            # ins_values += f"NULL, "
                            # selection_where += f"{field} {val} AND "
                            # constraint_where += f"{field} {val} AND "
                            # where_clause += f"{field} {val} AND "
                    else:
                        # Why am I here? What would return "" as a value???
                        raise UserWarning
                else:
                    print(f"\n\t*** 3b) ERROR! I need a valid value for constrained field '{field}' in table '{self.table}'!\n")
                    raise TypeError

        # 2) Add the rest of the given fields
        for field, value in self.param_dict.items():
            if field in self.constraint_arr:  # look for what happens with curdate-'{TODAY}'
                continue
            #
            val = self.get_nice_value(field)
            #
            if val == self.BAD_RESULT:
                if field in self.defaults_dict:
                    val = self.defaults_dict[field]
                else:
                    print(f'\n\t*** {self.param_dict["ticker"]} bad value! {self.table} - {field} - {value}')
                    myjoe()
                    raise UserWarning
            # Ok, I have some kind of value now
            if field != "curtime":
                sel_flds += f"{field}, "
                selection_where += f"{field}={val} AND "
            ins_flds += f"{field}, "
            ins_values += f"{val}, "
            up_qry += f"{field}={val}, "
        # Chop the ends off (commas, 'AND ')
        sel_flds = sel_flds[:-2]
        selection_where = selection_where[:-5]
        constraint_where = constraint_where[:-5]
        where_clause = where_clause[:-5]
        ins_flds = ins_flds[:-2]
        ins_values = ins_values[:-2]

        # First make a query that selects only using the constraint fields:
        if self.constraint_arr:
            constraint_query = f"SELECT {sel_flds} FROM {self.table} WHERE {constraint_where}"
        elif sel_flds:
            constraint_query = f"SELECT {sel_flds} FROM {self.table} WHERE {selection_where}"
        else:
            raise UserWarning

        # Now, make query to do an INSERT
        if sel_flds:
            selection_query = f"SELECT {sel_flds} FROM {self.table} WHERE {selection_where}"
        insertion_qry += f"({ins_flds}) VALUES ({ins_values})"
        #
        dt = self.param_dict["curdate"]
        if self.table == "tbl_prices" and dt.find("CURRENT") != -1:
            print(f"Check this: tbl_prices.curdate='{dt}'")
            raise UserWarning
        #
        SQL_dict = {"constraint_query": constraint_query,
                    "sel_flds": sel_flds,
                    "insertion_qry": insertion_qry,
                    "selection_query": selection_query,
                    "where_clause": where_clause,
                    "insertion_values": ins_values, }
        return SQL_dict

    def select_or_update(self, updateOnly: bool = False, conn=None):
        """ For table 'tbl', take the "fields" and "values" and:
            1) Check if the entry already exists in the table using the primary key only
            2) Add the entire entry, if it isn't there
            3) If it is there, see if updates to some of the non-primary fields can be made

            I work with local variables, and then return them, so I don't mess with the "self." ones in case there is an error
        """
        # updateOnly: This is for when I'm updating one table (tbl_IB_orders) and I pick up a conId and permId, and I want to
        #             see if this is also a record in tbl_ALGO_ORDERS. If so, update conId and permId, but otherwise DO NOT
        #             add a new record in tbl_ALGO_ORDERS

        # -------------------------------------------------------------------------------------------------------------------
        table = self.table
        self.msg = None
        self.differences = {}
        self.orig_values_dict = {}
        self.update_msg = ""
        ticker = self.param_dict["ticker"]

        #if not self.field_types:
        #    self.get_table_definitions()  # <------------ should have been set above in MASTER call  -----------------------------------------------------
        #    raise UserWarning  # todo: remove at some point (Jan 30, 2022)

        # Do some error checking before anything else:
        self.doSimpleErrorChecking(updateOnly=updateOnly)

        # -------------------------------------------------------------------------------------------------------------------
        # Creat the SQL strings for the param data given
        SQL_strings = self.createSQLStrings()                      # <------------------------------
        constraint_query = SQL_strings["constraint_query"]
        selection_query = SQL_strings["selection_query"]
        sel_flds = SQL_strings["sel_flds"]
        insertion_qry = SQL_strings["insertion_qry"]
        where_clause = SQL_strings["where_clause"]
        _insertion_values = SQL_strings["insertion_values"]
        # -------------------------------------------------------------------------------------------------------------------

        # Let's begin
        # Get results of just using the constraint_query:
        #
        constraint_results = self.sql_fn_call(qry=constraint_query, conn=conn)  # <------------------------------- select constraint
        #
        if len(constraint_results) > 1:  # This is a 'row count' question
            self.doSimpleErrorChecking(I_got_multiples_FLAG=True, updateOnly=updateOnly)
            # I don't (yet) want to do bulk updates
            self.checkNotNullIsSatisfied(query_used=constraint_query)
            #                           (raiseError: bool = True, query_used: str = ""):
            print(f"\n\tself.checkNotNullIsSatisfied(): 'TOO MANY ROWS RETURNED ({len(constraint_results)})' for constraint_query='{constraint_query}'")
            pyperclip.copy(constraint_query)
            raise UserWarning

        if constraint_results and sel_flds.count(",") != 0:
            # If I get more than one field returned, it comes back as a list.
            constraint_results = constraint_results[0]

        if constraint_results == []:  # Nothing found
            if updateOnly is True:
                self.constraint_query = constraint_query
                fn = get_calling_function()
                if fn in ["upload_IB_order", "ct_storeCommissionReport"]:
                    self.msg = "updateOnly found nothing to update"
                else:
                    self.msg = "updateOnly failed"
                    pyperclip.copy(constraint_query)
                    myjoe("")  # Fixme: Do I have a bogus field, like 'account', or 'broker'?
                return
            else:
                _update_msg = self.removeSilents()
                # self.sqllogger.debug(insertion_qry)
                newlogger.sqllog(insertion_qry)
                res_i = self.sql_fn_call(insertion_qry, conn)  # <----------------------------- ADDED ---------------
                if res_i:
                    self.msg = "added"
                    self.update_msg = self.removeSilents()
                    if self.update_msg != _update_msg:
                        myjoe("")
                    self.differences = self.param_dict
                    if "curtime" in self.param_dict:
                        self.param_dict.pop("curtime")
                    return

        # If I'm here, a record for this was found using the constraint_query.
        # If the selection_qery is blank, it means all the fields were constraint fields, and so all values are the same, so nothing to update
        # Now see what, if anything, is different when using the full selection query:
        if selection_query != "":
            #
            res_sel = self.sql_fn_call(selection_query, conn)       # <------------------------------------
            #
            if res_sel != []:  # Do not use 'not res_sel' as it doesn't work
                pyperclip.copy(f"{constraint_query};\n\n\n{selection_query};")
                self.msg = "nothing to change"
            else:
                # Ok, there is a record there by just using the constraints, but not when using all available fields
                # Therefore, something is different and I should update
                #
                CFD_res = self.check_for_differences(self.table, constraint_results, sel_flds, where_clause)  # <------------------------
                #
                if not CFD_res:
                    if "curtime" in self.param_dict:
                        self.param_dict.pop("curtime")  # use a fresh value each time
                    return
                #                                                                             newnewnewnew
                small_update_qry, differences_dict, orig_value_dict, update_msg, silent_flag, up_msg_short = CFD_res
                #                                                    ^^^^^^^^^^
                if small_update_qry:
                    self.sanity_check_query(small_update_qry)
                    newlogger.sqllog(small_update_qry)
                    #
                    res_u = self.sql_fn_call(small_update_qry, conn)  # <--------------------------- UPDATED ---------------
                    if bool(res_u):  # differences_dict must actually contain something, not a silent update
                        self.differences = differences_dict
                        self.orig_values_dict = orig_value_dict
                        self.update_msg = update_msg
                        if differences_dict != {}:
                            self.msg = "updated"
                        elif silent_flag:
                            self.msg = "silent update"
                        else:
                            self.msg = "nothing to change"
                    else:
                        myjoe()  # what does being here mean?
        #if "curdate" in self.param_dict:
        #    curdate = self.param_dict["curdate"]
        #    fn = get_calling_function()
        #    if curdate != TODAY:
        #        newlogger.critical(f'select_or_update(1): Fn "{fn}", table "{table}" - not popping curdate={curdate} from param_dict')  # Did I really want to get rid of it?   2022-09-22
        #        #self.param_dict.pop("curdate")
        #    else:
        #        newlogger.info(f'select_or_update(2): Fn "{fn}", table "{table}" - popping curdate={curdate} from param_dict')
        #        self.param_dict.pop("curdate")
        if "curtime" in self.param_dict:
            # Always freshen this up:
            self.param_dict.pop("curtime")
        return

    def sanity_check_query(self, query):
        tmp = query.lower()
        if tmp.find("update") == -1:
            # Just interested in checking updates for setting curtime to '' at the moment
            return
        where_clause = tmp[tmp.find("where") + 6:]
        tmp = tmp.replace(" ", "")
        if tmp.lower().find("curtime=''") != -1:
            myjoe("")  #
        if tmp.lower().find('curtime=""') != -1:
            myjoe("")  #
        if where_clause.find("curtime=") != -1:
            myjoe("")  # I should not be selecting using 'curtime', that can't be right?
        return


    def check_for_differences(self, table, sql_results, sql_fields_str, where_clause):
        """ Something is different in the table vs. new data. Go through each field and see what is different.
            July 22,2021: Actually get the new/old value and return that too
        """
        orig_value_dict = {}
        new_value_dict = {}
        sql_flds_arr = sql_fields_str.replace(" ", "").split(",")

        if len(sql_flds_arr) == 1:
            raise UserWarning  # What was the point of this? remove?
            # sql_flds = sql_flds[0]

        for ct, field in enumerate(sql_flds_arr):
            if field == "curtime":
                continue
            sql_value = sql_results[ct]
            new_value = self.param_dict[field]
            if not sql_value and new_value:
                # If I didn't have anything before, but do now, then just take what I have now
                orig_value_dict[field] = sql_value
                new_value_dict[field] = new_value
            elif self.field_types[field] in ["int", "float"]:
                if sql_value and abs(sql_value - float(new_value)) > .0001:
                    orig_value_dict[field] = sql_value
                    new_value_dict[field] = new_value
            elif self.field_types[field] == "text" and isinstance(new_value, (float, int)):
                # Now what?
                if abs(float(sql_value) - float(new_value)) > .01:
                    orig_value_dict[field] = sql_value
                    new_value_dict[field] = new_value
            elif field == "contract":
                if new_value.__str__() != sql_value:
                    orig_value_dict[field] = sql_value
                    new_value_dict[field] = new_value.__str__()
            elif new_value != sql_value:
                if self.field_types[field].lower() == "boolean":
                    orig_value_dict[field] = bool(sql_value)
                else:
                    orig_value_dict[field] = sql_value
                new_value_dict[field] = new_value
        if not new_value_dict:
            return None

        # Ok, there is something needing to be updated, so make sure 'curtime' gets updated too:
        if "curtime" in self.field_types:  # and "curtime" not in self.defaults_dict:
            new_value_dict["curtime"] = get_curtime()
            orig_value_dict["curtime"] = new_value_dict["curtime"]

        # Construct a streamlined update query
        update_qry = f'UPDATE {table} SET '
        for field, value in new_value_dict.items():
            val = self.get_nice_value(field)  # <---------------------
            if val != self.BAD_RESULT:
                update_qry += f"{field}={val}, "
            else:
                raise UserWarning
        # Now for the final 'set update_mg=' bit I'm adding:
        update_qry += f"update_msg='"

        # I am doing an update via 'update_qry' anyway, but I want to see if I want to make a logfile entry,
        # or .msg, about it via 'update_msg'
        silent_flag = False
        for field in self.silents:
            if field in new_value_dict:
                silent_flag = True
                orig_value_dict.pop(field)
                new_value_dict.pop(field)

        # Create a message saying what is different:
        update_msg, up_msg_short = "", ""
        dict_keys = list(new_value_dict.keys())
        dict_keys.sort()
        for field in dict_keys:
            if field in ["curdate", "curtime"]:
                myjoe("should I get rid of this?  This is from setting is_live to False")  #  2022-09-23
                continue
            if update_msg != "":
                update_msg += ", "
                up_msg_short += ", "
            update_msg += f"'{field}' from: '{orig_value_dict[field]}' to -> '{new_value_dict[field]}' "
            up_msg_short += f"{field} "
        update_msg = update_msg[:-1]
        up_msg_short = up_msg_short[:-1]
        assert update_msg.find(", , ") == -1

        update_qry += f"{up_msg_short}'"
        update_qry_final = f"{update_qry} WHERE {where_clause}"

        return update_qry_final, new_value_dict, orig_value_dict, update_msg, silent_flag, up_msg_short

    def makeMsgFromDict(self, aDict: dict):
        msg, nextBit = "", ""
        for field, value in aDict.items():
            if bool(value) is False:
                continue
            fieldType = self.field_types[field]
            if fieldType == "text":
                nextBit = f"{field}: '{value}'"
            else:
                nextBit = f"{field}: {value}"
            if not msg:
                msg = nextBit
            else:
                msg += f", {nextBit}"
        return msg

    def removeSilents(self):
        """ Something is different in the table vs. new data. Go through each field and see what is different.
            - when the field is a float, return a rounded #, not xx.yyyyyyyyyyyyyyyyyyyyy
        """
        # -------------------------------------------------------------------------------------------------------------------
        for field, value in self.param_dict.items():
            if field not in self.silents:
                if self.field_types[field] == "float":
                    value = round(float(value), 4)
                self.non_silent_param_dict[field] = value
                if field in self.constraint_arr:
                    self.non_silent_constraints[field] = value
        #
        # Make msg:
        msg = self.makeMsgFromDict(self.non_silent_constraints)
        if not msg or len(msg) > 150:
            msg = self.makeMsgFromDict(self.non_silent_param_dict)
        return msg

    def no_zeros(self, field, value):  # , bad_num=-99999):
        # Zero often gets passed in as a "no-result" value. If so, then ignore that field.
        # If a table is ok with zero as a value, then it can default it to zero in its table definition

        # 1) The actual boolean value of False, do not use "=="
        if value is False:
            self.param_dict[field] = value
            if self.table not in self.isNowFalse.keys():
                self.isNowFalse[self.table] = []
            self.isNowFalse[self.table].append((self.table, field))
            return
        #
        # 2) The actual boolean value of True, do not use "=="
        elif value is True:
            self.param_dict[field] = value
            return
        #
        # 3) Numeric, but not zero, and not 'bad_num':
        elif isinstance(value, (float, int)):
            #if value == bad_num or abs(value) < .001:
            if value in variables.UNSET_VALUES or abs(value) < .001:
                if field in self.param_dict.keys():
                    del self.param_dict[field]  # Gets rid of any previous, good, value
                return
            elif float(value):  # and float(value) not in infinities: # [0, infinities]:
                self.param_dict[field] = round(value, 4)
            return
        #
        # 4) String, but check first it is NOT zero:
        elif isinstance(value, str):
            if bool(value) is False:
                return  # Don't store
            value = value.replace("'", "§")
            if value.isnumeric() and float(value) == 0:
                myjoe(stop=False)  # Ooops! This was always stored before August 3rd!
            else:
                self.param_dict[field] = value
                return
        #
        return

    def updateOnly(self, conn: sqlite3.Connection = None, logIt: bool = False):
        # If it fails, I should report it!
        self.UPDATEONLY = True
        self.processThis(updateOnly=True, conn=conn, logIt=logIt)
        if self.msg == "updateOnly failed":
            # from utils import get_calling_function
            # calling_fn = get_calling_function()
            reqId = self.param_dict["reqId"]
            table = self.table
            if table != "tbl_ALGO_ORDERS":
                pyperclip.copy(self.constraint_query)
                newlogger.warning(f"updateOnly(): {reqId=}, '{table}': Could not do an 'updateOnly' for constraint query:   {self.constraint_query}")
                #newlogger.warning(f"updateOnly(): {self.constraint_query}")
                myjoe("")  #
        return

    def doPostSQLOperations(self):
        """ Things to be done after certain other things are done """
        #
        if self.table == "tbl_positions":
            self.check_tbl_positions_for_blank_curtime()
        if self.table == "tbl_recommendations":
            if self.update_msg.find("permId") != -1 and self.update_msg.find("->[]") != -1:
                myjoe()  # wtf? Don't get rid of a found permId!?
        #
        if self.table == "tbl_prices":
            self.check_Alerts()
            self.check_update_tbl_positions_mktval()
            self.check_tbl_positions_for_blank_curtime()
        return


    def check_tbl_positions_for_blank_curtime(self):
        if TODAY > "2023-01-01":
            myjoe("")  # remove this check I created on 2022-09-23 ?
        if self.table == "tbl_positions":
            qry = "select curtime, curdate, * from tbl_positions where curtime=''"
            res = sql_execute(qry)
            if res:
                pyperclip.copy(qry)
                myjoe("")  # whut??
        return


    def check_update_tbl_positions_mktval(self):
        if not self.table in ["tbl_prices", "tbl_positions"]:
            return
        if self.table == "tbl_prices" and self.param_dict["close"]:
            ticker = self.param_dict["ticker"]
            broker = self.param_dict["broker"]
            secType = self.param_dict["secType"]
            if secType != "STK":
                # myjoe("make sure it updates stocks only, and all the values have values")
                return
            account = get_account(ticker)  #  self.param_dict["account"]
            shares = get_position(ticker)
            if not shares:
                return
            close = self.param_dict["close"]
            mktval = shares * close
            #
            params = create_A_Param("tbl_positions")
            #
            params.updateFromDict({"curdate": TODAY, "ticker": ticker, "secType": secType, "close": close, "mktVal": mktval})
            params.no_zeros("broker", broker)
            if not account:
                myjoe("")  # fix this! I need account here
            params.no_zeros("account", account)
            #
            params.updateOnly()
            #
            _joe = 12
        return

    def isThisADuplicatedDividend(self, newSource, p_ticker, p_ex_date, p_dividend, pricefile):
        """ No matter how often a stock pays, it should never be twice in the same month.
            So, for this ETrade ticker/ex_date, look for all divs I have stored in that month.
            0 : Add it
            1 : Check if it is an IB position, and I should not overwrite what I have with ETrade data
            2+: ERROR!
            Returns: TRUE:  Yes, maybe this is a dupe   FALSE: Probably not
        """
        NOT_A_DUPE = False
        I_THINK_ITS_A_DUPE = True
        CONFIRMED = True

        goodSources = ["storeDividends", "nasdaq_download_dividends", "nasdaq.com", "manualDividendEntry",
                       "get_yfinance_dividends_and_splits", "ct_uploadDividends", "IB-ct_uploadDividends"]
        if newSource not in goodSources:
            myjoe(newSource)  # change it to a good source

        trustworthySources = ["CONFIRMED", "nasdaq_download_dividends", "nasdaq.com", "manualDividendEntry", "storeDividends"]
        ex_div_month_start = f"{p_ex_date[:7]}-01"
        ex_div_month_end = f"{p_ex_date[:7]}-31"
        broker_qry = f"select broker FROM tbl_positions WHERE broker!='' and ticker='{p_ticker}' and secType='STK' order by curdate desc"
        broker = sql_fetchone(broker_qry)

        qry = f"select ex_date, dividend, source " \
              f"from tbl_dividends where ticker='{p_ticker}' and ex_date>='{ex_div_month_start}' and ex_date<='{ex_div_month_end}' " \
              f"and not split order by ex_date"
        #     f"and not (ex_date='{ex_date}' and dividend={dividend}) order by ex_date"
        res = sql_execute(qry)
        if not res:
            return NOT_A_DUPE  # It can't be a dupe if nothing is there at all
        if len(res) != 1:
            print(f"\n\tisThisADuplicatedDividend(): Too many results for '{p_ticker}'. I'm looking for ex_date: {p_ex_date}   (qry copied)")
            pyperclip.copy(qry)
            print(f"\n\t{qry}")
            myjoe("")  #
            return I_THINK_ITS_A_DUPE
        res = res[0]
        sql_ex_date, sql_dividend, sql_Source = res
        # ------------------------------------------
        # check ex_date and dividend vs what's there
        # ------------------------------------------
        if p_ex_date == sql_ex_date and abs(round(p_dividend - sql_dividend, 3) < 0.01):
            return I_THINK_ITS_A_DUPE  # exact-enough match

        if sql_Source == "CONFIRMED":
            return I_THINK_ITS_A_DUPE

        if sql_Source in ["manualDividendEntry", "checkForUpcomingDividends", "made up by my code"]:
            # myjoe("Maybe there's new information? Maybe I typed something wrong the first time?")
            if newSource == "nasdaq.com" or sql_Source == "made up by my code":
                del_qry = f"delete from tbl_dividends where ticker='{p_ticker}' and ex_date='{sql_ex_date}' and dividend={sql_dividend}"
                del_res = sql_execute(del_qry)
                newlogger.info(f"Overwriting '{sql_Source}' dividend for: {p_ticker} - {sql_ex_date} - ${sql_dividend:,.4f} - with {p_ex_date} ${p_dividend:,.4f} from {newSource}")
                return NOT_A_DUPE  # take new data

        if sql_Source == "IB-ct_uploadDividends":
            # IB stocks use IB dividend information, do not overwrite what's there
            return I_THINK_ITS_A_DUPE

        if broker == "ETrade" and sql_Source in ["storeDividends", "manualDividendEntry"]:
            # ETrade stocks use ETrade dividend information, do not overwrite what's there
            return I_THINK_ITS_A_DUPE

        print()
        #print("isThisADuplicatedDividend():")
        #print()
        print(f"'{p_ticker.upper()}' DIVIDEND:")
        print(f"\tToday's ETrade download has a DECLARED ${round(p_dividend, 4):,.4f} dividend with ex_date='{p_ex_date}'")
        print(f"\tBut tbl_dividends has:                 ${round(sql_dividend, 4):,.4f} dividend with ex_date='{sql_ex_date}'")  # (source = '{sql_Source}')")
        print()
        con = input(f"Please confirm this new '{p_ticker}' - '{p_ex_date}' - {p_dividend} dividend from ETrade (y/Yes) ? : ")
        if con and con.lower()[0] == "y":
            u_qry=f"update tbl_dividends set dividend={p_dividend}, ex_date='{p_ex_date}', source='CONFIRMED' where ticker='{p_ticker}' and ex_date='{sql_ex_date}' and dividend={sql_dividend}"
            u_res = sql_execute(u_qry)
            if u_res != 1:
                myjoe("")  # whoops!
            return CONFIRMED
        if sql_Source in trustworthySources:
            # 'nasdaq.com'     : trustworthy source
            # 'manualDividendEntry'   : is from me typing it in by hand, after looking at IB
            # 'storeDividends' : ETrade itself, so obviously newer data from them is better than old
            return I_THINK_ITS_A_DUPE
        return NOT_A_DUPE


    def check_Alerts(self):
        """ 'self' is already a Parameter """
        if self.param_dict["curdate"] != TODAY:
            return False

        if self.param_dict["secType"] != "STK":
            return
        ticker = self.param_dict["ticker"]
        shares = get_position(ticker)
        mktVal = get_mktVal(ticker)
        if shares and shares > 0:
            status = " (is a LIVE POSITION) "
        else:
            status = ""  # flat position"
        if "last" in self.param_dict:
            price = float(self.param_dict["last"])
        elif "close" in self.param_dict:
            price = float(self.param_dict["close"])
        else:
            return
        buy_dip_price = 0.9 * price
        ratio_low = 0.05  # Range: .05, .04, .03, .02, .01
        ratio_high = 0.05  # Range: .05, .04, .03, .02, .01
        old_high = 0
        old_low = 10000
        qry = f"select high, low, ratio_low, ratio_high from tbl_alerts where ticker='{ticker}' order by curdate desc limit 1"
        res = sql_fetchone(qry)
        if res:
            old_high, old_low, ratio_low, ratio_high = map(float, res)
        new_high = old_high
        new_low = old_low
        #
        ADJ_FLAG = False
        msg = ""
        if price > old_high:
            ADJ_FLAG = True
            #newlogger.debug("")
            msg = f"ALERT! {ticker}{status} pos value = ${mktVal:,.0f} price of ${price:,.2f} is above the high alert of ${old_high:,.2f}"
            #newlogger.debug("")
            newlogger.critical(msg)
        elif price < old_low:
            ADJ_FLAG = True
            #newlogger.debug("")
            msg = f"ALERT! {ticker}{status} pos value = ${mktVal:,.0f} price of ${price:,.2f} is below the low alert of ${old_low:,.2f}"
            #newlogger.debug("")
            newlogger.critical(msg)
        if msg:
            telebotTexting.sendTelegramText(msg)
        if ADJ_FLAG:
            # I just tripped a limit, so tighten the bands around it so I can see (e.g.) new highs continually reached, or a pullback
            ratio_high = max(0.01, ratio_high - 0.01)
            ratio_low = max(0.01, ratio_low - 0.01)
            # check
            new_high = price * (1 + ratio_high)
            new_low = price * (1 - ratio_low)
            buy_dip_price = 0.7 * new_low
            #
        new_high = round(new_high, 2)
        new_low = round(new_low, 2)
        buy_dip_price = round(buy_dip_price, 2)

        # this is running ALL the time, for EVERY new price??
        #
        params = create_A_Param("tbl_alerts")
        #
        # todo: handle any broker/account changes?
        # "close": price,
        params.updateFromDict({"ticker": ticker,
                               "last": price,
                               "high": new_high,
                               "low": new_low,
                               "ratio_low": ratio_low,
                               "ratio_high": ratio_high,
                               "buy_dip_price": buy_dip_price})
        #
        params.processThis()
        #
        # As tbl_alerts has CURDATE now, there will always be adds
        if params.msg in ["added", "updated"]:
            msg = f"tbl_alerts: was updated: {params.update_msg}"
            debugMsg("check_Alerts(2)", msg)
            #telebotTexting.sendTelegramText(msg)
        #
        return
    # -------------------------------------------------------------------------------------------------------------------
    def processThis(self, conn: sqlite3.Connection = None, updateOnly: bool = False, logIt: bool = False):
        # 0) Pre-processing:
        if self.table == "tbl_errors" and logIt is True:
            newlogger.critical(f"processThis(0): Do not 'autolog' things to tbl_errors!")
            fn = self.last_fn  # for debugging
            myjoe("")  # 2022-09-25

        # 1) The actual work:
        try:
            self.select_or_update(conn=conn, updateOnly=updateOnly)
        except AttributeError:
            raise
        else:
            self.needToProcess = False
            if logIt:
                self.processLogging()

        # 2) Post-processing:
        self.doPostSQLOperations()
        return

    # -------------------------------------------------------------------------------------------------------------------

    def processLogging(self):
        table = self.table
        WHAT = ""
        for field in ["ticker", "conId", "what", "report", "blockName"]:
            value = self.param_dict[field]
            if value:
                WHAT = f"{field}: '{value}'"
                break
        # conId = self.param_dict["conId"]
        ticker = self.param_dict["ticker"]
        if ticker:
            WHAT = f"Ticker: {ticker}"or self.param_dict["what"]
        if not WHAT:
            myjoe("use what then?")
        #
        if self.msg == "updateOnly failed":
            newlogger.critical(f"autoLog(0): [{self.last_fn}] {self.param_dict['reqId']=} - {table=} - {ticker=} - {self.msg} - {self.update_msg}")
            return
        #
        if "reqId" in self.param_dict and self.msg in ["added", "updated"]:
            # debugMsg(param_dict["reqId"], f"autoLog(1): {table} - {ticker} {self.msg} - {self.update_msg}")
            debugMsg(self.param_dict["reqId"], "processLogging",  f"autoLog(1): [{self.last_fn}] {table=} - {WHAT} - {self.msg} - {self.update_msg}")
        elif self.msg in ["added", "updated"]:
            debugMsg(f"autoLog(2): [{self.last_fn}] {table=} - {WHAT} was {self.msg} - {self.update_msg}")
        # ----------------------------------------------------------------------------------------
        self.checkForbiddenUpdate()
        # ----------------------------------------------------------------------------------------
        return

    def checkForbiddenUpdate(self):
        """ needs to be done after the SQL work, so can't be in 'doSimpleErrorChecking'
        """
        if self.msg == "updated" and self.table == "tbl_positions" and "conId" in self.differences:
            print(f"\n\tYou just updated conId in tbl_positions!\n")
            raise UserWarning
        if self.msg == "updated" and self.table == "tbl_positions" and "good_position" in self.differences:
            print(f"\n\t*** You just updated 'good_position to {self.param_dict['good_position']} in tbl_positions! CONFIRM!\n")
            raise UserWarning
        return
    # -------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------


def file_exists(filename):
    """ File exists, and is not empty.
        This is a duper of the util.py one, done here to avoid circular imports
    """
    return os.path.isfile(filename) and bool(os.path.getsize(filename))

def table_to_dataframe(tbl_name):
    # https://datacarpentry.org/python-ecology-lesson/09-working-with-sql/index.html
    conn = sqlite3.connect("Data/my_portfolio.db")
    df = pd.read_sql_query(f"SELECT * from {tbl_name}", conn, index_col="curdate")
    conn.close()
    return df

def getCostBasis(ticker, secType):
    #from data_file import cost_basis, cost_basis_options
    from data_file import cost_basis_options
    from trading import get_cost_basis

    if secType == "STK":
        cb = get_cost_basis(ticker)
    elif secType == "CASH":
        cb = get_cost_basis(ticker)
    elif secType == "OPT":
        cb = cost_basis_options.get(ticker, None)
    else:
        raise UserWarning

    if cb:
        return cb
    else:
        qry = ""
        _res = sql_fetchone(qry)
        myjoe()

def check_is_num(val):
    if isinstance(val, float64) or isinstance(val, float) or isinstance(val, int64) or isinstance(val, int):
        return True
    if val is None:
        return False
    # Due to the new 'Decimal' type in API_10, I need a workaround
    try:
        _ = val + 1
    except TypeError:
        joe = type(val)
    else:
        return True
    for xx in val:
        if not (xx.isnumeric() or xx == "."):
            return False
    return True

# --------------------------------------------- Class AllLines
class AllLines(object):
    def __init__(self, sql):
        self.data_arr = []
        self.sql = self.processSql(sql)


    def processSql(self, sql):
        while sql.find("  ") != -1:
            sql = sql.replace("  ", " ")
        pos = sql.find("(")
        sql = sql[pos + 1:]  # Removes the initial "CREATE TABLE (" bit
        sql = sql.replace("\t", " ")
        sql = sql.replace("\n", " ")
        sql = sql.replace("\r", " ")
        while sql:
            pos_bracket = sql.find("(")
            pos_comma = sql.find(",")
            pos_right_bracket = sql.find(")")
            if pos_bracket != -1 and pos_bracket < pos_comma:
                # I got a list of fields for a primary key then
                # pos_right_bracket = sql.find(")")
                self + sql[:pos_right_bracket + 1]
                sql = sql[pos_right_bracket + 1:]
            else:
                if pos_comma != -1:
                    self + sql[:pos_comma]
                    sql = sql[pos_comma + 1:]
                else:
                    if pos_right_bracket != -1:
                        self + sql[:pos_right_bracket]
                        sql = sql[pos_right_bracket + 1:]
                    else:
                        self + sql
                        sql = ""
        assert self.data_arr[-1].strip() != ''
        return sql


    def __str__(self):
        return "'AllLines' Class"

    def __add__(self, aline):
        self.add(aline)

    def __getitem__(self, ct):
        _tmp = ""
        if ct <= len(self.data_arr):
            tmp = self.data_arr[ct]
            return tmp
        else:
            return None

    def __len__(self):
        return len(self.data_arr)

    def add(self, aline):
        tmp = aline.lstrip()
        tmp = tmp.replace("\n ", "")
        tmp = tmp.replace("\n", "")
        if tmp:  # Was: if aline
            self.data_arr.append(tmp)
# --------------------------------------------- Class AllLines

def create_table_from_variable(var, tbl_name=""):
    mapper = {
        str: "text",
        float: "float",
        int: "int",
        bool: "boolean",
        date: "date",
    }
    if not tbl_name:
        tbl_name = "FILL_IN_TBL_NAME"
    sql = f"CREATE TABLE {tbl_name} \n(\n"
    for xx in dir(var):
        if xx.find("__") == 0:  # Skip built-ins
            continue
        typ = eval(f"type(var.{xx})")
        sql_type = mapper.get(typ, "blobby check")
        #print(f"{xx} - [{typ}] - [{sql_type}]")
        sql += f"\t{xx} {sql_type},\n"
    sql = sql[:-2]
    sql += ")\n"
    print(sql)
    myjoe()

# -------------------------------------------------------------------------------------------------------------------
class Master_Parameters:
    # todo: Make Parameters a 'mixin" class to MarketData?
    #allParameters = {}  moved up above as a global variable (to sql_utils at least)
    #
    def __str__(self):
        return "Master_Parameters"

    def __setattr__(self, key, value):
        if key.lower() == "debug":
            #thislogger.info(f"{self.last_fn}(): Setting sql_utils.Parameters[{key}] to True!")
            myjoe()  #
        super().__setattr__(key, value)
        return

    def __init__(self, bot):
        self.GLOBAL_BOT = bot
        #self.sqllogger = logging.getLogger("myapp.sqllog")
        self.NO_NEW_VARIABLES = True  # <---- leave this as the very last line of the __init__
        return


    def newParam(self, table:str, fixedDict: dict=None, stayAlive:bool=False):
        #
        #if table not in self.allParameters:
        if table not in SQL_UTILS_ALLPARAMETERS:
            # I need to create a new 'param' for this table
            fn = get_calling_function(levels_back=2)
            params = Parameters(table, fn, fixedDict, stayAlive)
            #params.initialize()  done inside __init__ now
            #self.allParameters[table] = params
            SQL_UTILS_ALLPARAMETERS[table] = params
        else:
            # I already have a 'param' for this table
            #params = self.allParameters[table]
            params = SQL_UTILS_ALLPARAMETERS[table]
            #                    self.fixedDict
            if fixedDict != params.fixedDict:
                myjoe("")  # now what?
            params.process_starting_dict(fixedDict)
            params.clear_it()
            if params.needToProcess is True:
                print(f"\n\t*** newParam(): {params.table}: Do not do a 'param' from within a 'param'")
                print(); myjoe()
                myjoe()
            params.needToProcess = True
        #
        if table == "tbl_positions":
            qry = "select distinct ticker from tbl_positions where only_etrade=True"
            params.only_etrade_tickers = sql_execute(qry)
        #
        params.Master_Params = self  # Fixme: Do I need this variable?
        #
        return params


# -------------------------------------------------------------------------------------------------------------------
GLOBAL_FIND_FIELD="permId"

# -------------------------------------------------------------------------------------------------------------------
class cls_param_dict(UserDict):
    def __init__(self, calling_Parameter):
        if TODAY > "2022-11-01":
            myjoe("")  # does this get hit anymore? 2022-09-9
        super().__init__()  # gets 'self.data' from here
        self.Parameter = calling_Parameter

    def __setattr__(self, key, value):
        if isinstance(key, str) and key.lower() == GLOBAL_FIND_FIELD.lower():
            myjoe("")
        if key.lower() == "ticker":
            self.Parameter.ticker = value
        super().__setattr__(key, value)
        return


    def __missing__(self, key):  # class cls_param_dict
        myjoe("")  # does this get hit anymore? 9/7/2022
        if isinstance(key, str) and key.lower() == GLOBAL_FIND_FIELD.lower():
            myjoe("")
        if key == "divYield":
            return 0
        elif key in ["ticker", "good_position", "value", "gotGreeks", "putCall", "Report",
                     "close", "blockName", "action", "strike", "RealizedPnL", "split"]:
            return False
        elif key in ["curdate", "curtime"]:
            myjoe("")  # really?
            return False  # ""
        elif key in ["secType", "conId"]:
            return ""
        elif key in ["broker", "account"]:
            return None
        else:
            myjoe(key)
        return ""
# -------------------------------------------------------------------------------------------------------------------
def only_wants_one_field(qry):
    # If a query only wants to return one field, there is no need for it to be a tuple
    qry = qry.lower()
    pos1 = qry.find("select ")
    if pos1 == -1:
        return False  # Not even a select qry, so this is irrelevant
    pos2 = qry.find(" from ")
    fields = qry[pos1:pos2]
    pos3 = fields.find(",")
    if pos3 == -1 and fields.find("*") == -1:
        return True
    else:
        return False

def sql_fetchone(qry, zeroIt=False, MUST_RETURN_SOMETHING=False) -> str:
    if qry.lower()[:7] != "select ":
        myjoe("")  # FIXME: Do not close connection
    commit = qry.lower()[:7] != "select "
    close = qry.lower()[:7] != "select "
    res = sql_execute(qry=qry, fetch="fetchone", commit=commit, close=close, zeroIt=zeroIt, MUST_RETURN_SOMETHING=MUST_RETURN_SOMETHING)
    return res


def dataframe_create(qry):
    global SAVED_CONNECTION
    if SAVED_CONNECTION is None:
        SAVED_CONNECTION = sqlite3.connect("Data/my_portfolio.db")
    df = pd.read_sql(qry, SAVED_CONNECTION)
    return df


#@static_vars(saved_connection=None)
def sql_execute(qry, fetch="fetchall", conn=None, commit=True, close=True, zeroIt=False, MUST_RETURN_SOMETHING=False, returnDICT=False):
    MAINFRAME_TABLES = ["tbl_earnings_dates", "tbl_etrade_balances", "tbl_etrade_portfolio",
                        "tbl_etrade_prices", "tbl_exchange_rates", "tbl_historical_data", "tbl_holidays",
                        "tbl_pnl", "tbl_strikes", "tbl_trades_to_do", "yfinance_fields"]
    DB_TO_USE1 = "Data/my_portfolio.db"
    DB_TO_USE2 = "Data/THE_MAINFRAME.db"
    global SAVED_CONNECTION
    for table in MAINFRAME_TABLES:
        if qry.lower().find(f" {table} ") != -1:
            myjoe("")  #
            fn = get_calling_function()
            if fn not in ["xxxCheck_SQL_Tables"]:
                myjoe(table)  # delete and move to using THE_MAINFRAME
    del table
    # -----------------------------------------
    def myClosex():
        global SAVED_CONNECTION
        conn.close()
        #sql_execute.saved_connection = None
        SAVED_CONNECTION = None
    # -----------------------------------------
    def create_dictionary_from_results(cursor, row):
        # cursor.description: (name, type_code, display_size, internal_size, precision, scale, null_ok)
        # row               : (value, value, ...)
        return {
            col[0]: row[idx]
            for idx, col in enumerate(
                cursor.description,
            )
        }
    # -----------------------------------------
    #
    if I_AM_NOT_IN_LONDON is True:
        if qry.UPPER().find("CURRENT_DATE") != -1:
            myjoe("Fix this to a date function? Because it uses UTC as it's default timezone for CURRENT_DATE")
    if not conn:
        #if sql_execute.saved_connection is not None:
        if SAVED_CONNECTION is not None:
            #conn = sql_execute.saved_connection
            conn = SAVED_CONNECTION
        else:
            conn = sqlite3.connect(DB_TO_USE1)  #  "Data/my_portfolio.db")
            #sql_execute.saved_connection = conn
            SAVED_CONNECTION = conn

    NO_TUPLES = only_wants_one_field(qry)
    if NO_TUPLES and returnDICT:
        myjoe("Now what? 1842")
    if NO_TUPLES:
        # (was: no_tuples(qry):
        conn.row_factory = lambda cursor, row: row[0]
    elif returnDICT:        conn.row_factory = create_dictionary_from_results
    else:
        conn.row_factory = None

    # -------------------------------------------------------------------------------------------------------------------
    # SELECTs:
    if (qry.lower())[:6] == "select":
        try:
            res1 = conn.execute(qry)
        except sqlite3.ProgrammingError:
            pyperclip.copy(qry)
            #myjoe("")   Cannot operate on a closed database.
            raise
        except sqlite3.OperationalError:
            pyperclip.copy(qry)
            print()
            print(100 * "!")
            print()
            print(f"\tsql_execute(2): Problem with the qry?  (copied to clipboard)")
            print(f"\t{qry}")
            print()
            print(100 * "!")
            #file.close()
            raise

        if fetch == "fetchone":
            res2 = res1.fetchone()
            if isinstance(res2, list):
                if len(res2) == 1:
                    res2 = res2[0]
        else:
            res2 = res1.fetchall()

        # Note: no need to close or commit a select
        if zeroIt and res2 is None:
            res2 = 0
        if bool(res2) is False and MUST_RETURN_SOMETHING:
            return False
        return res2

    # -------------------------------------------------------------------------------------------------------------------
    # UPDATE, INSERT, DELETE: Actual changes to a table
    # -------------------------------------------------
    if (qry.lower())[:6] in ["update", "insert", "delete", "create", "drop v", "alter "]:
        try:
            res = conn.execute(qry)
            if commit:
                conn.commit()
            if close:
                myClose()
                conn.close()
                #sql_execute.saved_connection = None
                SAVED_CONNECTION = None
            if bool(res) is False and MUST_RETURN_SOMETHING:
                raise UserWarning
            return res.rowcount  # True            <-----------------------------------------
        except sqlite3.IntegrityError:
            raise
        except sqlite3.OperationalError:
            print(f"\n\t{qry}\n")
            raise
        except:
            print(); myjoe()
            print(f"sql_execute(2): Unexpected error: {sys.exc_info()[0]}")
            print(f"\n\t{qry}")
            print(); myjoe()
            raise

    # Compress database
    if qry.lower() == "vacuum":
        try:
            conn.execute("VACUUM")
        except Exception:
            print(f"\n\t*** sql_execute(): Unexpected error: '{sys.exc_info()[0]}' : '{sys.exc_info()[1]}'\n")
            raise
        finally:
            myClose()
        return True
    # -------------------------------------------------------------------------------------------------------------------
    raise UserWarning  # why am I here? A new SQL command, like "CREATE "?


def expand_tickers_for_sql(tickers):
    res = ""
    for ticker in tickers:
        res += f"'{ticker}', "
    res2 = res[:-2]
    return res2

def excel_load_my_positions_to_database():
    # Get, and clean, data from excel:
    df = pd.read_excel("D:/Program Files (x86)/Python38-32/Sudoku/SQL/main_tbl_positions.xlsx")

    #df["IB"] = df["IB"]
    #df["etrade"] = df["etrade"]
    #df["shortName"] = df["shortName"]
    #df["ticker"] = df["ticker"]
    #df["shares"] = df["shares"]
    df["last"] = df["last"].fillna(0)
    #df["cost_basis"] = df["cost_basis"]
    #df["tradedate"] = df["tradedate"].fillna("null")
    #df["commission"] = df["commission"]
    #df["broker"] = df["broker"]
    #df["currency"] = df["currency"]
    #df["exchange"] = df["exchange"]
    #df["notes"] = df["notes"]
    #df["name"] = df["name"]
    #df["last_update"] = df["last_update"]
    #df["close"] = df["close"]
    #df["account_id"] = df["account_id"]

    conn = sqlite3.connect("Data/my_portfolio.db")
    crsr = conn.cursor()

    #fields = "ticker, shares, tradedate, tradedate_mmddyyyy, tradedate_ddmmyyyy, cost_basis, commission, broker, currency, exchange"
    #fields = "IB, etrade, shortName, ticker, shares, last, cost_basis, tradedate, commission, broker, currency, exchange, " \
    #         "notes, name, last_update, close, account_id"

    for row_num, row in df.iterrows():
        IB = row['IB']
        etrade = row['etrade']

        shortName = row['shortName']
        ticker = row['ticker']
        shares = row['shares']
        last = row['last']
        cost_basis = row['cost_basis']
        tradedate = row['tradedate']

        commission = row['commission']
        broker = row['broker']
        currency = row['currency']
        exchange = row['exchange']
        notes = row['notes']
        name = row['name']
        last_update = row['last_update']

        close = row['close']
        account_id = row['account_id']

        qry = f"INSERT INTO tbl_positions IB, etrade, shortName, ticker, shares, last, cost_basis, tradedate, commission, broker, currency, exchange, " \
             "notes, name, last_update, close, account_id " \
              f"VALUES ({IB}, {etrade}, '{shortName}', '{ticker}', {shares}, {last}, {cost_basis}, '{tradedate}', " \
              f"{commission}, '{broker}', '{currency}', '{exchange}', '{notes}', '{name}', '{last_update}', {close}, '{account_id}')"
        print(qry)
        myjoe()
        try:
            crsr.execute(qry)
        except sqlite3.OperationalError:
            print(f"\n{qry}\n")
            myjoe()

    conn.commit()
    conn.close()
    print("\nDone!\n")

def get_last_date(table):
    qry = f"SELECT curdate FROM {table} ORDER BY curdate DESC"
    last_date = sql_fetchone(qry)
    return last_date

def get_option_price(ticker, expiry, strike, putCall):
    # which field is used here?
    expiry = convert_date(expiry)
    qry = f"SELECT optPrice, curdate FROM tbl_options WHERE ticker='{ticker}' AND expiry='{expiry}' AND strike={strike} AND putCall='{putCall}' order by curdate desc"
    res = sql_fetchone(qry)
    if res:
        return res
    # Didn't find anything
    return 0, ""

def get_option_price_ORIG(fields:list, ticker, expiry, strike, putCall):
    if TODAY > "2022-11-01":
        myjoe("")  # delete this method
    expiry = convert_date(expiry)
    if not isinstance(fields, list):
        # Turn it into a list then
        fields = [fields]
    for field in fields:
        qry = f"SELECT {field} FROM tbl_options WHERE ticker='{ticker}' AND expiry='{expiry}' AND strike={strike} " \
              f"AND putCall='{putCall}'"
        res = sql_fetchone(qry)
        if res:
            return res
    # Didn't find anything
    return 0


def get_position(ticker) -> float:
    qry = f"select shares from tbl_positions where ticker='{ticker}' and curdate='{TODAY}' and secType='STK'"
    res = sql_fetchone(qry)
    if res:
        res = float(res)
    return res

def get_mktVal(ticker) -> float:
    qry = f"select mktval from tbl_positions where ticker='{ticker}' and secType='STK' order by curdate desc"
    res = sql_fetchone(qry)
    if res:
        res = float(res)
    return res

def get_account(ticker):
    #qry = f"select account from tbl_positions where ticker='{ticker}' and curdate='{TODAY}' and secType='STK'"
    qry = f"select account from tbl_positions where ticker='{ticker}' and secType='STK' order by curdate desc"
    res = sql_fetchone(qry)
    return res
    #if len(res) != 1:
    #    myjoe("")  # why am I getting multiple accounts for this ticker?
    #else:
    #    return res[0]

def get_last_price(ticker="", conId=""):
    # Options:
    if conId:
        optPrice, close, last, bid, ask = 0, 0, 0, 0, 0
        qry = f"SELECT optPrice, close, last, bid, ask FROM tbl_options WHERE conId='{conId}' and curdate='{TODAY}'"
        res = sql_fetchone(qry)
        if res:
            optPrice, close, last, bid, ask = res
        return optPrice, close, last, bid, ask

    # Stocks:
    qry = f"SELECT last, close FROM tbl_prices WHERE ticker='{ticker}' and secType='STK' ORDER BY curdate DESC"
    res = sql_execute(qry, "fetchall", commit=False, close=False)  # "all" in case there's a bunch of zeros recently
    for row in res:
        last, close = row
        if last:             # in case there's a bunch of zeros recently
            return last
        elif close:          # in case there's a bunch of zeros recently
            return close
    return 0

"""
def get_ALL_last_prices(ticker="", conId=""):
    price_dict = {}
    #
    # Options:
    optPrice, close, last, bid, ask = 0, 0, 0, 0, 0
    oqry = f"SELECT conId, optPrice, close, last, bid, ask FROM tbl_options WHERE curdate='{TODAY}' and conId order by conId"
    ores = sql_execute(oqry)
    for conId, optPrice, close, last, bid, ask in ores:
        price_dict[conId] = optPrice, close, last, bid, ask

    # Stocks
    sqry = f"SELECT ticker, last, close FROM tbl_prices WHERE secType='STK' ORDER BY ticker, curdate DESC"
    sres = sql_execute(sqry)
    for ticker, last, close in sres:
        if ticker in price_dict:
            continue
        if last:
            price_dict[ticker] = last
        elif close:
            price_dict[ticker] = close
    #
    return price_dict
"""

def get_last_conId_price(conId):
    qry = f"SELECT last, close FROM tbl_prices WHERE conId='{conId}' ORDER BY curdate DESC"
    res = sql_execute(qry)  # "all" in case there's a bunch of zeros recently
    for row in res:
        last, close = row
        if last:
            return last
        elif close:
            return close
    return 0

def get_last_two_dates(table, fields, zeros_are_ok=True):
    #
    last_date = get_last_date(table)
    qry = f"SELECT DISTINCT account FROM {table} WHERE curdate='{last_date}' AND field IN {fields}"
    if not zeros_are_ok:
        qry += " AND value != 0"
    qry += " ORDER BY value DESC"
    accounts = sql_execute(qry)

    res_dict = {}
    for account in accounts:
        for field in fields:
            if zeros_are_ok:
                qry = f"SELECT DISTINCT curdate, account, field FROM {table} " \
                      f"WHERE field='{field}' AND account='{account}' " \
                    f"ORDER BY curdate DESC"
            else:
                qry = f"SELECT DISTINCT curdate, account, field FROM {table} " \
                      f"WHERE field='{field}' AND account='{account}' AND value!=0 " \
                      f"ORDER BY curdate DESC"
            all_rows = sql_execute(qry)
            for row in all_rows:
                curdate, account, field = row
                # key2 = f"{field}.{account}"
                key2 = field, account
                if not res_dict.get(key2):
                    res_dict[key2] = []
                    res_dict[key2].append(curdate)
                else:
                    if len(res_dict[key2]) == 1:
                        res_dict[key2].append(curdate)
                    else:
                        # No more for this
                        pass
    return res_dict  # Different return key

def get_latest_exchange_rate(currency):
    if currency.lower() == "usd":
        return 1
    qry = f"SELECT rate FROM tbl_exchange_rates WHERE from_currency='{currency}' ORDER BY curdate DESC"
    res = sql_execute(qry)
    return res[0]

def get_latest_pricing_date():
    qry = "SELECT curdate FROM tbl_prices ORDER BY curdate DESC;"
    latest_date = sql_fetchone(qry)
    return latest_date

def get_divYield(ticker):
    qry = f"select divYield from tbl_positions where ticker='{ticker}' order by curdate desc"
    res = sql_fetchone(qry)
    return res


def get_dividend_income(broker):
    rates_dict = {}
    ret_arr = []
    ALL_date_cutoff = "pos.tradedate"
    YTD_date_cutoff = datetime.datetime.now().strftime("%Y-01-01")
    YTD_date_cutoff = f"'{YTD_date_cutoff}'"
    for cutoff in [ALL_date_cutoff, YTD_date_cutoff]:
        total = 0
        # TODO: This may need to be "last trading date" for tbl_positions?
        qry = f"SELECT pos.ticker, shares, currency, SUM(dividend), shares * SUM(dividend) AS income " \
              f"FROM tbl_positions AS pos, tbl_dividends AS divs WHERE pos.curdate='{TODAY}' AND pos.broker='{broker}' AND pos.ticker = divs.ticker AND good_position=True " \
              f"AND ex_date >= {cutoff} GROUP BY pos.ticker"
        res = sql_execute(qry)
        for xx in res:
            ticker, shares, currency, dividend, income = xx
            if currency in rates_dict:
                rate = rates_dict[currency]
            else:
                rate = get_latest_exchange_rate(currency)
                rates_dict[currency] = rate
            divinc = income * rate
            total += divinc
        ret_arr.append(total)
    return ret_arr


def IB_has_account_data():
    minimum_date = should_have_prices_for()
    accounts = ["U7864219", "U10144028"]  # ETrade: 63460815
    tables = ["tbl_account_summary"]
    arr = []
    for table in tables:
        for account in accounts:
            qry = f"SELECT * FROM {table} WHERE account='{account}' AND curdate>='{minimum_date}'"
            res = sql_execute(qry)
            if not res:
                #print(f"\n*** Missing data for '{account}' in table '{table}' ***\n")
                arr.append(account)
    return arr


def get_last_report_update(what):
    """ return value:
            True : Things are fine, it was properly run within it's cycle timeframe
            False: It needs to run again
    """
    NEEDS_TO_BE_DONE = False
    DOES_NOT_NEED_TO_BE_DONE = True
    #
    qry = f"SELECT curdate FROM tbl_reports WHERE what='{what}'"
    curdate = sql_fetchone(qry)
    if not curdate:
        # Add it
        params = create_A_Param("tbl_reports")
        params.updateFromDict({"what": what})
        params.processThis(logIt=True)
        return NEEDS_TO_BE_DONE
    #
    if curdate != datetime.datetime.today().strftime("%Y-%m-%d"):
        return NEEDS_TO_BE_DONE  # Double check this is actually working correctly

    return DOES_NOT_NEED_TO_BE_DONE


def get_last_update(what, optionalCycle=None):
    """ optionalCycle: Specificy a new time to use, like "Daily", "15_minutes"
        return value:
            True : Things are fine, it was properly run within it's cycle timeframe
            False: It needs to run again
    """
    # NEEDS_TO_BE_DONE = False
    # DOES_NOT_NEED_TO_BE_DONE = True
    #
    if what.lower() != "create all reports" and (what.lower().find("reports") != -1 or what.upper().find("summaries") != -1):
        fn = get_calling_function()
        res = get_last_report_update(what)
        return res

    qry = f"SELECT last_update, curtime, cycle, vacation_cycle, morning_routine, needs_live_market, note, only_after FROM tbl_last_updates WHERE what='{what}'"
    res = sql_fetchone(qry)
    if not res:
        print(f"\n\t*** What tbl_last_updates is this?  '{what}'")
        raise KeyError
    #
    last_update, curtime, cycle, vacation_cycle, morningRoutine, needs_live_market, pause, only_after = res
    curdate, curtime = curtime.split()
    #
    if variables.I_AM_ON_VACATION:
        cycle = vacation_cycle
    #
    if bool(needs_live_market) is True:
        if thisMarketIsOpen("USA") is False:
            return DOES_NOT_NEED_TO_BE_DONE

    datetime_last_update = datetime.datetime.strptime(last_update, '%Y-%m-%d')

    # Daily-->"1 day", Weekly-->"1 week"
    num = 1
    if optionalCycle:
        cycle = optionalCycle
    if cycle.find("_") != -1:
        num, cycle = cycle.split("_")
        num = int(num)
    cycle = cycle.lower()
    if cycle not in ["minutes", "hourly", "hours", "days", "daily", "weekly", "monthly", "optional"]:
        print(f"\n\tget_last_update(ERROR): Bad cycle: [{cycle}]\n")
        raise UserWarning
    # TODO: For 'LOOPER', even if a market is closed, if I just updated a LMT order, I still want to be able to get the new limit price from the API?
    today = datetime.datetime.today()
    one_day = datetime.timedelta(max(1, (today.weekday()+6) % 7 - 3))
    num_MinutesAgo = (datetime.datetime.now() - datetime.timedelta(minutes=num)).strftime("%H:%M:%S")
    num_daysAgo = (today - (num * one_day)).strftime("%Y-%m-%d")
    num_weeksAgo = today - (num * 7 * one_day)
    num_monthsAgo = today - (num * 30 * one_day)
    now = datetime.datetime.now()
    one_hour = datetime.timedelta(hours=1)
    oneHourAgo = (now-one_hour).strftime("%H:%M:%S")

    # -------------------------------------------------------------------------------------------------------------------
    # Easy checks:
    # 1) Annoying things I only want to deal with after any/all morning Kram has been taken care of
    if only_after:
        if get_sql_now() < only_after:
            return DOES_NOT_NEED_TO_BE_DONE
    # 2)
    if cycle in ["minutes", "hourly", "hours", "daily"] and last_update != TODAY:
        return NEEDS_TO_BE_DONE
    # -------------------------------------------------------------------------------------------------------------------
    # Otherwise:
    # -------------------------------------------------------------------------------------------------------------------
    if cycle == "days" and last_update < num_daysAgo:
        return NEEDS_TO_BE_DONE
    elif cycle == "weekly" and datetime_last_update < num_weeksAgo:
        return NEEDS_TO_BE_DONE
    elif cycle == "monthly" and datetime_last_update < num_monthsAgo:
        return NEEDS_TO_BE_DONE
    if cycle == "minutes" and curtime < num_MinutesAgo:
        return NEEDS_TO_BE_DONE
    # -------------------------------------------------------------------------------------------------------------------
    elif cycle in ["hourly", "hours"]:
        if curtime < oneHourAgo:
            return NEEDS_TO_BE_DONE
        else:  # check for 'over midnight' issue
            aa = int(curtime[:2])
            bb = int(oneHourAgo[:2])
            if aa == 23 and bb == 0:
                myjoe("This doesn't work across days, when 'oneHourAgo' is 23:xx:xx and time_stamp is 00:xx:xx ?")
    #elif cycle == "optional" and last_update != today.strftime("%Y-%m-%d"):
    #    return NEEDS_TO_BE_DONE
    # -------------------------------------------------------------------------------------------------------------------
    return DOES_NOT_NEED_TO_BE_DONE


def unset_last_update(what):
    curtime = f"{get_sql_today()} {get_sql_now()}"
    qry = f"UPDATE tbl_last_updates SET last_update='1990-01-01', curtime='{curtime}' WHERE what='{what}'"
    sql_execute(qry)

def reset_last_update(what, note=""):
    YEAR = datetime.datetime.now().strftime("%Y")
    MON = datetime.datetime.now().strftime("%m")
    MON = int(MON) - 1
    if MON == 0:
        MON = 12
        YEAR -= 1
    DAY = int(datetime.datetime.now().strftime("%d"))
    if DAY == 31 and MON in [2, 4, 6, 9, 11]:
        DAY = 30
    newdate = f"{YEAR}-{MON:02d}-{DAY:02d}"
    calling_fn = get_calling_function()  # this works
    #
    TBL_LAST_UPDATES = create_A_Param("tbl_last_updates")
    #
    TBL_LAST_UPDATES.updateFromDict({"what": what,
                                     "last_update": newdate,
                                     "time_stamp": get_sql_now(),
                                     "source": calling_fn,})
    TBL_LAST_UPDATES.no_zeros("note", note)
    #
    TBL_LAST_UPDATES.processThis(logIt=True)
    #
    return


def set_last_report_update(what):
    #
    #timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    #
    params = create_A_Param("tbl_reports")
    params.updateFromDict({"what": what, "curdate": TODAY})
    params.processThis()
    return


def set_last_update(what, frequency="Daily", use_MASTER_PARAMS=True, note=""):
    if what in ["Popup summary logs"]:
        fn = get_calling_function()
        if fn != "popup_summary_logs":
            myjoe("")  # who is calling this?
            res = input(f"\n\t*** Set '{what}', or exit? (y=set it): ")
            if not res or res.lower() != "y":
                return
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    calling_fn = get_calling_function()  # this works
    #
    params = create_A_Param("tbl_last_updates")
    params.updateFromDict({"what": what, "last_update": TODAY, "time_stamp": timestamp, "source": calling_fn})
    params.no_zeros("note", note)
    #
    params.processThis()
    #
    return


def getUnderConId(ticker):
    qry = f"select distinct(underConId) from tbl_IB_option_contract_details where ticker='{ticker}'"
    res = sql_execute(qry)
    return res

def updateTradingNotes(ticker, note):
    qry = f"SELECT trading_notes FROM tbl_positions WHERE curdate='{TODAY}' and ticker='{ticker}'"
    existingNote = sql_fetchone(qry)
    if existingNote.find(note) != -1:
        # I already have this noted
        return
    newNote = f"{note}, {existingNote}"
    qry = f"UPDATE tbl_positions SET trading_notes='{newNote}' WHERE ticker='{ticker}' and curdate='{TODAY}'"
    sql_execute(qry)

def updateReturnNote(ticker, note, conn):
    """ This didn't work because due to the 'conn' it wasn't being committed in between calls.
        I moved this (effectively) upstream to make it a param_dict["returnNote"] entry instead of this function call
    """
    myjoe("Who is still calling this?")
    qry = f"SELECT returnNote FROM tbl_returns WHERE ticker='{ticker}' AND curdate='{TODAY}'"
    existingNote = sql_fetchone(qry)
    if existingNote and existingNote.find(note) != -1:
        # I already have this noted
        return
    if bool(existingNote):
        newNote = f"{existingNote}, {note}"
    else:
        newNote = f"{note}"
    qry = f"UPDATE tbl_returns SET returnNote='{newNote}' WHERE ticker='{ticker}' AND curdate='{TODAY}'"
    res = sql_execute(qry, conn=conn, commit=False, close=False)
    if not res:
        myjoe("")
    return


def get_last_note(ticker, which):
    qry = f"SELECT {which} FROM tbl_positions WHERE ticker='{ticker}' and {which}!='' order by curdate desc"
    res = sql_fetchone(qry)
    return res or ''

def get_notes(which="Notes", ticker=None):
    if ticker:
        qry = f"SELECT {which} FROM tbl_positions WHERE curdate='{TODAY}' AND ticker='{ticker}'"
        res = sql_execute(qry)
        if res:
            return res
        else:
            return ""

    # FIXME: add this to morning code
    qry = f"SELECT ticker, {which} FROM tbl_positions WHERE curdate='{TODAY}' and good_position=True AND {which} != ''"
    res = sql_execute(qry)
    # This doesn't get the last notes and carry them forward
    note_dict = {}
    ignores = []
    if len(res) != 0:
        for ticker, note in res:
            good_note = True
            for ig in ignores:
                if note.lower().find(ig) != -1:
                    good_note = False
            if good_note:
                note_dict[ticker] = note
    return note_dict

def get_return_notes():
    qry = f"SELECT ticker, returnNote FROM tbl_returns WHERE returnNote != ''"
    res = sql_execute(qry)
    ret_note_dict = {}
    ignores = []
    if len(res) != 0:
        for ticker, note in res:
            good_note = True
            for ig in ignores:
                if note.lower().find(ig) != -1:
                    good_note = False
            if good_note:
                ret_note_dict[ticker] = note
    return ret_note_dict

def get_then_set_last_update(what, func):
    # sql_utils.get_then_set_last_update("refresh option data", self.get_option_information)
    if not get_last_update(what):
        try:
            func()
        except:
            print(f"get_then_set_last_update(): Unexpected error: {sys.exc_info()[0]}")
            raise
        else:
            set_last_update(what)

#def create_conId():
#    pass
    """
    qry = "select ticker,contract from tbl_IB_stock_contract_details order by ticker"
    res = sql_execute(qry, "fetchall")
    for row in res:
        ticker, contract = row
        conId, *the_rest = contract.split(",")

        up_qry = f"update tbl_IB_stock_contract_details set conId={conId} where ticker='{ticker}'"
        print(f"{ticker} - {conId} - {up_qry}")
        sql_execute(up_qry)
    """

def updatePriceForDate(ticker, adate):
    last_price = get_last_price(ticker)
    newlogger.debug(f"Please enter a price for '{ticker}' {adate}: .....................")
    print()
    price = input(f"\n\tPlease enter a price for '{ticker}' {adate} (last={last_price}) : ")
    if not price:
        price = last_price
    print()
    price = float(price)
    #
    params = create_A_Param("tbl_prices")
    #
    params.param_dict["curdate"] = adate
    params.param_dict["ticker"] = ticker
    if ticker == "MS PRF":
        params.param_dict["conId"] = "139808284"
    else:
        params.param_dict["conId"] = ticker  # Stocks only!
    params.param_dict["close"] = price
    params.param_dict["price"] = price
    #
    params.processThis(logIt=True)
    #
    return price

def update_tbl_positions_prices(logger):
    qry = f"select pos.ticker, pri.close, pri.last " \
          f"from tbl_positions as pos, tbl_prices as pri " \
          f"where pos.ticker = pri.ticker and pri.curdate='{get_last_trading_date()}' and pos.secType='STK' and good_position " \
          f"order by pos.ticker desc"
    res = sql_execute(qry)
    if not res:
        return None

    logger.debug(f"update_tbl_positions_prices(): START")
    for row in res:
        ticker, close, last = row
        logger.debug(f"update_tbl_positions_prices(1): Processing: '{ticker}'")
        uqry = f"update tbl_positions set close={close}, last={last} where ticker='{ticker}' and secType='STK' and curdate='{TODAY}'"
        _ures = sql_execute(uqry)
    logger.debug(f"update_tbl_positions_prices(): FINISH")
    return True

def fix_ib_contracts():
    _qry = "SELECT conId, realExpirationDate,  tbl_IB_option_contract_details"

@static_vars(table_dict={})  # , last_col="")
def find_column_in_tables(col="", justTables=False):
    # Note: 'tbl_prices' and 'tbl_etrade_prices' should not have a field called 'open' as it is a reserved word
    #---------------------------------------------------------------
    def myprint(msg=""):
        if justTables is False:
            print(msg)
    #---------------------------------------------------------------
    def is_a_skip_line(line):
        SKIPS = ["unique", "primary key", "create index"]
        for skip in SKIPS:
            if line.lower().find(skip) != -1:
                return True
        return False
    # -------------------------------------------------------------------------------------------------------------------
    last_col = ""
    myprint()
    if not col:
        msg = "What column should I search for?  ('curdate', or 'curdate curtime' to compare two)"
        if last_col != "":
            msg += f"(last checked: '{last_col}') "
        col = input(f"{msg}\n")
    comparison = False
    if col.find(" ") != -1:
        comparison = True
        col = col.split()
    else:
        col = [col]
    #
    column = ""
    max_len = None
    res_arr = []
    table_arr = []
    for column in col:
        column_as_word = f" {column.lower()} "
        qry = "SELECT tbl_name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY tbl_name"
        res = sql_execute(qry)
        max_len = 0
        res_arr = []
        table_arr = []
        for row in res:
            table, sql = row
            if sql.upper().find("CREATE VIEW") != -1:
                continue  # goes to 'for row in res:'
            sql = sql.replace("\t", " ")
            if sql.lower().find(column_as_word.lower()) == -1:
                continue  # goes to 'for row in res:'
            all_lines = sql.split("\n")
            for line in all_lines:
                if line.lower().find(column_as_word) == -1:
                    continue  # goes to: 'for line in all_lines:'
                if is_a_skip_line(line):
                    continue  # goes to: 'for line in all_lines:'
                if line.lower().find(column.lower()) != -1:
                    res_arr.append((table, line))
                    table_arr.append(table)
            if len(table) > max_len:
                max_len = len(table)
        if not res_arr and not comparison:
            myprint()
            myprint(f"\nNothing found for: {column}!")
            continue  # return res_arr
        table_set = set(table_arr)

        # FIND DIFFERENCES when checking two columnumns:
        for table in table_set:
            if last_col == "":
                find_column_in_tables.table_dict[table] = find_column_in_tables.table_dict.get(table, 0) + 1
            else:
                find_column_in_tables.table_dict[table] = find_column_in_tables.table_dict.get(table, 0) - 1
        #
        if not comparison:
            myprint()
            myprint(f"\nColumn '{column}' is in:")
            for tbl, line in res_arr:
                myprint(f"\t{tbl} - {line}")
            myprint()
            #
            for table in table_set:
                myprint(table)
            myprint()
        #
        if last_col != "":
            diff = [table for table, val in find_column_in_tables.table_dict.items() if val]
            diff_set = set(diff)
            if diff_set:
                myprint(f"\nDifferences between '{last_col}' and '{column}':\n")
                for table, val in find_column_in_tables.table_dict.items():  # diff_set:
                    if val > 0:
                        myprint(f"table: {table:30}, has '{last_col}' but not '{column}'")
                    elif val < 0:
                        myprint(f"table: {table:30}, has'{column}' but not '{last_col}'")
                myprint()
            else:
                myprint(f"No table differences for '{last_col}' and '{column}'")
        else:
            last_col = column
    #
    if justTables is False:
        _ = input("\nPress <enter> to continue..")
        find_column_in_tables.last_col = column
        return res_arr, max_len
    else:
        return table_arr


def find_field_type_in_tables(field_type=None):
    #import re
    table_dict = {}
    print()
    if not field_type:
        field_type = input("find_field_type_in_tables(): What field type should I search for? ")
    field_type = field_type.lower()
    qry = "SELECT tbl_name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY tbl_name"
    res = sql_execute(qry)
    max_len = 0
    res_arr = []
    for row in res:
        tbl, sql = row
        # I don't think any sql would have something BEFORE the thing?
        if sql.find(f" {field_type}") != -1:
            all_lines = sql.split("\n")
            for line in all_lines:
                if line.find(f" {field_type} ") != -1:
                    res_arr.append((tbl, line))
                    table_dict[tbl] = 1
            if len(tbl) > max_len:
                max_len = len(tbl)
    print()
    if not res_arr:
        print(f"Nothing found for field type '{field_type}' !")
        return res_arr
    print(f"Type '{field_type}' is in:")
    for tbl, line in res_arr:
        print(f"\t{tbl} - {line}")
    print()
    for xx in table_dict.keys():
        print(xx)
    _ = input("\nPress <enter> to continue..")
    return res_arr, max_len


def find_word_in_tables(word=None):
    table_dict = {}
    print()
    if not word:
        word = input("find_word_in_tables(): What word should I search for? ")
    word = word.lower()
    qry = "SELECT tbl_name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY tbl_name"
    res = sql_execute(qry)
    max_len = 0
    res_arr = []
    for row in res:
        tbl, sql = row
        # I don't think any sql would have something BEFORE the thing?
        if sql.find(f" {word}") != -1:
            all_lines = sql.split("\n")
            for line in all_lines:
                if line.find(f" {word} ") != -1:
                    res_arr.append((tbl, line))
                    table_dict[tbl] = 1
            if len(tbl) > max_len:
                max_len = len(tbl)
    print()
    if not res_arr:
        print(f"Nothing found for field type '{word}' !")
        return res_arr
    print(f"Type '{word}' is in:")
    for tbl, line in res_arr:
        print(f"\t{tbl} - {line}")
    print()
    for xx in table_dict.keys():
        print(xx)
    _ = input("\nPress <enter> to continue..")
    return res_arr, max_len


def oneNameAnalysis():
    ticker = "epol"
    ticker = ticker.upper()
    qry = f"SELECT broker, shares, cost_basis, close FROM tbl_positions WHERE curdate='{TODAY}' and ticker='{ticker}'"
    broker, shares, cost_basis, close = sql_fetchone(qry)
    #qry = f"SELECT close FROM tbl_prices WHERE ticker='{ticker}' ORDER BY curdate DESC"
    #close = sql_fetchone(qry)
    cost = cost_basis * shares
    value_now = close * shares
    pnl = value_now - cost
    print(); myjoe()
    print(f"{ticker}: Broker: {broker}, Position: {shares:.0f},  Cost Basis: ${cost_basis:,.2f},  CLOSE: ${close:,.2f},  P&L: ${pnl:,.0f}")

    myjoe()

def getQryWithGenFn(qry, fn):
    """ Run a query. If nothing returns, run the function that generates what's needed
        qry : The query to run
        fn  : The function to run if the query didn't work
    """
    res = sql_execute(qry)
    if not res:
        fn()
    res = sql_execute(qry)
    if not res:
        pyperclip.copy(qry)
        msg = f"ERROR! Even after running function [{fn}], nothing still returned for query: {qry}"
        print(f"\n{msg}")
        logging.warning(msg)
        raise UserWarning
    return res

def process_a_dict(a_dict, final_dict):
    def process_a_key():
        if isinstance(value, str):
            final_dict[key] = "text"
        elif isinstance(value, float):
            final_dict[key] = "float"
        elif isinstance(value, int):
            final_dict[key] = "int"
        elif isinstance(value, bool):
            final_dict[key] = "boolean"
        elif isinstance(value, date):
            final_dict[key] = "date"

    for key, value in a_dict.items():
        if isinstance(value, dict):
            process_a_dict(final_dict, value)
            pass
        else:
            process_a_key()  # final_dict, key, value)
        myjoe()

    myjoe()

def checkForDeltaReferences():
    qry = f"select ticker, executedTime2, placedTime2, expiryDay, expiryMonth, expiryYear from tbl_etrade_orders " \
          f"where curdate='{get_sql_today()}' and status='EXECUTED' and securityType='OPT'"
    res = sql_execute(qry)
    for row in res:
        #
        ticker, executedTime2, placedTime2, expiryDay, expiryMonth, expiryYear = row
        if expiryMonth < 10:
            expiryMonth = f"0{expiryMonth}"
        if expiryDay < 10:
            expiryDay = f"0{expiryDay}"
        expiry = f"{expiryYear}-{expiryMonth}-{expiryDay}"
        #
        delta_qry = f"select curdate, ticker, strategy, delta_reference, strike, expiry, putCall " \
                    f"from tbl_options_trades where ticker='{ticker}' and expiry='{expiry}'"
        delta_res = sql_fetchone(delta_qry)
        if not delta_res:
            print(f"\nNeed to find a delta reference for: {row}", end="")
            print(f"\t{expiry}")
            print("\tSadly, I could not ..")
        #else:
            #print(f"\tI found one! {delta_res}")
        curdate, ticker, strategy, delta_reference, strike, expiry, putCall = delta_res
        if bool(delta_reference) is False:
            print("\tSadly, it doesn't have a delta reference yet! ..")
    #print("\nDONE!")

def findNewAccountFields():
    qry = "select distinct field from tbl_account_summary"
    fields = sql_execute(qry)
    mydict = {}
    for field in fields:
        qry2 = f"select curdate from tbl_account_summary where field='{field}' order by curdate limit 1"
        mydate = sql_fetchone(qry2)
        mydict[field] = mydate
    for fld, dte in mydict.items():
        print(f"{dte}\t{fld}")
    return

def getAccounts(ticker):
    qry = f"select distinct account FROM tbl_positions WHERE curdate='{TODAY}' and ticker='{ticker}'"
    accounts = sql_execute(qry)
    return accounts  # what type?

def getOptionID(ticker, putCall, strike):
    friday = get_next_Friday(forsql=True)
    qry = f"select conId, ticker, putCall, strike, expiry, longName, contract " \
          f"from tbl_IB_option_contract_details where ticker='{ticker}' and expiry='{friday}' and strike={strike} and putCall='{putCall}' " \
          f"order by strike"  #  limit 1"
    res = sql_fetchone(qry)
    if res:
        conId, ticker, putCall, strike, expiry, longName, contract = res
        #res = f"{conId}-{putCall}-{strike:.0f}"
        return conId
    return None  # ""

def getLiveTradeConAndPermIds(ticker, tradeReco, strike):
    tradeReco = tradeReco.upper()
    if tradeReco.find("PUT") != -1:
        putCall = "P"
    elif tradeReco.find("CALL") != -1:
        putCall = "C"
    else:
        return ""
    qry = f"SELECT conId, permId FROM tbl_ALGO_ORDERS WHERE ticker='{ticker}' AND strike={strike} AND putCall='{putCall}' AND is_live=True"
    res = sql_fetchone(qry)
    if not res:
        return "", ""
    conId, permId = res
    return conId, permId


def GET_WHAT_NEEDS_DOING():
    from utils import get_variable
    # Mo:0, Tu:1, We:2, Th:3, Fr:4, St:5, Sn:6
    WEEKDAY = [0, 1, 2, 3, 4]
    #SATURDAY = 6
    today = datetime.datetime.now()
    day = int(today.strftime("%u"))
    needs = {}
    needs["found something"] = []
    #
    qry = "SELECT what, cycle, morning_routine, category FROM tbl_last_updates " \
          "where morning_routine and category not in ('Report') ORDER BY morning_routine desc, what"
    res = sql_execute(qry)
    for what, cycle, morning_routine, category in res:
        if what == "IB get live prices":
            if get_variable("LIVE_PRICES is False"):
                needs[what] = DOES_NOT_NEED_TO_BE_DONE
                myjoe("does this get hit anymore?")
                continue
        if cycle.lower() == "optional":
            val = DOES_NOT_NEED_TO_BE_DONE
        val = not get_last_update(what)
        if bool(morning_routine):
            needs[what] = val
        else:
            needs[what] = DOES_NOT_NEED_TO_BE_DONE
        if bool(needs[what]) and category != "Admin":
            needs["found something"].append(what)
    return needs

def whats_left_to_do():
    res = GET_WHAT_NEEDS_DOING()
    print()
    print("What's left to do:")
    print()
    if not res["found something"]:
        print(f"\tNothing, everything was done")
        print()
    else:
        for what in sorted(res["found something"], key=str.casefold):
            print(f"\t{what}")
    print()
    return


def get_broker(ticker):
        # TODO: Make work for options
        qry = f"select distinct broker from tbl_positions where ticker='{ticker}' and secType='STK'"
        res = sql_execute(qry)
        assert len(res) == 1
        return res[0]

def checkNetDividends():
    filename = "D:/Program Files (x86)/Python38-32/Market Data/Logs/NetDividends.txt"
    with open(filename, "r") as file:
        all_lines = file.read()
        lines = all_lines.splitlines()
    myjoe()  #

    data = {}
    for line in lines:
        line = line.replace(",", "")
        line = line.replace("my_log_", "")
        line = line.replace(".txt", "")
        left, right = line.split("Account:")
        date, *junk = left.split(":")
        account, tag, field, tag2, value, tag3, currency = right.split()
        value = float(value)
        if account == "All":
            continue
        # key2 = f"{date}.{account}.{currency}"
        key2 = date, account, currency
        print(f"{date}: {account}, {currency}, {value}")
        if key2 not in data:
            data[key2] = value
        else:
            if (value - data[key2]) > 5:
                print(f"{date} - {account} - Next: {value}, Former: {data[key2]}")
                myjoe()  #
        myjoe()  #

    print("DONE!")

def get_ETFS():
    # 1) orderDict.py global, 2) ticker_obj.py, 3) trading.py,
    qry = "select distinct ticker FROM tbl_positions WHERE is_an_ETF=True"
    res = sql_execute(qry)
    return res

def get_last_div_update(ticker):
    qry = f"select curdate from tbl_dividends where ticker='{ticker.upper()}' order by curdate desc limit 1"
    res = sql_fetchone(qry)
    return res or ""

"""
def fix_tbl_prices_curdate():
    conn = sqlite3.connect("Data/my_portfolio.db")
    #res1 = conn.execute(qry)

    qry1 = f"SELECT ticker, asofDate, curdate, curtime, conId, osiKey, secType, close " \
          f"FROM tbl_prices " \
          f"where curdate!=curtime order by ticker, curdate desc"
    res1 = sql_execute(qry1)
    lastTicker = ""
    _res = None
    #print(); myjoe() e e e
    for ticker, asofDate, curdate, curtime, conId, osiKey, secType, close in res1:
        print(f"\nfix_tbl_prices_curdate(): Processing: curdate='{curdate}' AND ticker='{ticker}' AND conId='{conId}' AND osiKey='{osiKey}' AND secType='{secType}'",
              end="")
        uqry = f"UPDATE tbl_prices SET curdate=curtime WHERE curdate='{curdate}' AND ticker='{ticker}' AND conId='{conId}' AND osiKey='{osiKey}' AND secType='{secType}'"
        try:
            _ures = conn.execute(uqry)
        except:
            print(f"\t*** DID NOT WORK! ***")
            raise
        #if ures != 1:
        #    raise UserWarning
        if lastTicker != ticker:
            lastTicker = ticker
            myjoe()  #
        myjoe()  #
    conn.commit()
    conn.close()

    return
"""

def fix_tbl_IB_bad_option_specs():
    conn = sqlite3.connect("Data/my_portfolio.db")

    qry1 = f"SELECT ticker, exchange, primary_exchange, fixed, currency, curtime, curdate, contract, source, strike, putCall " \
          f"FROM tbl_IB_bad_option_specs " \
          f"order by curdate desc, contract"
    res1 = sql_execute(qry1)
    print(); myjoe()
    for ticker, exchange, primary_exchange, fixed, currency, curtime, curdate, contract, source, strike, putCall in res1:
        print(f"Processing: Curdate='{curdate}', contract='{contract}'")
        aa, ticker, secType, IB_expiry, strike, putCall, bb, exchange, primary_exchange, currency, *the_rest = contract.split(",")
        print(f"            Curdate='{curdate}', ticker='{ticker:6}', strike={strike}, putCall='{putCall}', secType='{secType}', currency='{currency}', exchange='{exchange}'")
        uqry = f"update tbl_IB_bad_option_specs set ticker='{ticker}', strike={strike}, putCall='{putCall}', " \
               f"IB_expiry='{IB_expiry}', currency='{currency}', exchange='{exchange}', source='fix_tbl_IB_bad_option_specs' " \
               f"where curdate='{curdate}' and contract='{contract}'"
        _ures = sql_execute(uqry)
        print(); myjoe()
    conn.commit()
    conn.close()
    print("DONE!")
    return

def run_a_database_analysis(printResults=False):
    """ https://queirozf.com/entries/python-3-subprocess-examples#run-example-run-command-and-get-return-code
    """
    import subprocess
    debug_print("Run a database analysis .. START")
    DEBUG = False
    output_file = f"db_analysis.txt"
    with open(output_file, "w") as myoutput:
        _sp = subprocess.run(["sqlite3_analyzer.exe", "Data/my_portfolio.db"], stdout=myoutput, stderr=subprocess.PIPE, universal_newlines=True, shell=True, check=True)
    new_inserts = []
    with open(output_file, "r") as file:
        all_lines = file.read().splitlines()
    for line in all_lines:
        if line.find("INSERT") != -1:
            new_inserts.append(line)

    del_qry = f"DELETE from z_space_used where curdate='{TODAY}'"
    del_res = sql_execute(del_qry)
    # Sample line:
    # INSERT INTO space_used VALUES('tbl_returns','tbl_returns',0,0,12239,11662,3,2080432,0,0,341,3,578,0,7639,212943,0,375,2379776);
    #
    params = create_A_Param("z_space_used")  # should error
    #
    #conn = sqlite3.connect("Data/my_portfolio.db")
    #crsr = conn.cursor()
    for line in new_inserts:
        _left, right = line.split("VALUES(")
        right = right.replace(");", "")
        right = right.replace("'", "")
        # name, tblname, is_index, is_without_rowid, nentry, leaf_entries, depth, payload, ovfl_payload, ovfl_cnt, mx_payload, int_pages, leaf_pages, ovfl_pages, int_unused,leaf_unused, ovfl_unused, gap_cnt, compressed_size = right.split(",")
        name, tblname, _is_index, _is_without_rowid, nentry, *the_rest, compressed_size = right.split(",")
        #iqry = f"INSERT INTO z_space_used (curdate, name, tblname, nentry, compressed_size) VALUES ('{TODAY}', {name}, {tblname}, {nentry}, {compressed_size}"
        if name != tblname:
            continue
        params.param_dict["name"] = name
        params.param_dict["tblname"] = tblname
        params.param_dict["nentry"] = nentry
        params.param_dict["compressed_size"] = compressed_size
        #
        params.processThis()
        #
        #crsr.execute(iqry)
    #conn.commit()
    #crsr.close()
    #conn.close()

    if printResults:
        ct = 0
        print(); myjoe()
        qry = f"select curdate, tblname, nentry from z_space_used where name=tblname and curdate='{TODAY}' order by nentry desc"
        res = sql_execute(qry)
        for row in res:
            curdate, tblname, row_ct = row
            print(f"Date: {curdate},  Table: {tblname:30}  :  Rows: {row_ct:,.0f}")
            ct += 1
            if ct == 10:
                break
        print("\nRun a database analysis: DONE!\n")

    set_last_update("Run a database analysis")
    debug_print("Run a database analysis .. FINISH")
    return True


def ticker_change(orig, new):
    """ What needs to be done for a ticker change, like for DTN->AIVL asof January 18, 2022
        - Also update all things in the data_file.py file
        - Do a global REPLACE operation for hardodes on the old ticker
    queries = {
        "tbl_positions": f"update tbl_positions set ticker='{new}', conId='{new}' where ticker='{old}'",
        "tbl_prices": f"update tbl_prices set ticker='{new}', conId='{new}' where ticker='{old}'",
        "tbl_dividends": f"update tbl_dividends set ticker='{new}' where ticker='{old}'",
        "tbl_pnl": .....
    }
    for table, qry in queries.items():
        res = sql_execute(qry)
    """
    ticker_tables, nameLength = find_column_in_tables("ticker")
    queries = []
    print(); myjoe()
    found_something = False
    for table in ticker_tables:
        qry = f"SELECT * FROM {table} WHERE ticker='{orig}'"
        res = sql_execute(qry)
        if not res:
            continue
        if not found_something:
            print("Table                            # Rows       Update SQL")
            print("----------------------------------------------------------------------------------------------------------------------")
            found_something = True
        up_qry = f"UPDATE {table} SET ticker='{new}' WHERE ticker='{orig}'"
        queries.append(up_qry)
        print(f"{table:{nameLength+1}}: {len(res):5,} :      {up_qry}")
    if not found_something:
        print(f"\tNo 'ticker={orig}' found in any table")

    #from data_file import cost_basis, trade_dates
    from data_file import cost_basisxx, trade_datesxx
    for which in orig, new:
        if which in cost_basisxx:
            print(f"'{which}' is in data_files.py cost_basis dict!")
            myjoe("")  #  what is going on??
        if which in trade_datesxx:
            print(f"'{which}' is in data_files.py trade_dates dict!")
            myjoe("")  #  what is going on??
    print(); myjoe()

def exportPositionsToFile():
    qry = f"select broker, ticker, shares from tbl_positions where secType='STK' and curdate='{TODAY}' and shares order by broker, ticker"
    res = sql_execute(qry)
    filename = "DATA/portfolio.csv"
    with open(filename, 'w') as file:
        for broker, ticker, shares in res:
            file.write(f"{broker},{ticker},{shares}\n")
    return


def set_ISLIVE_to_false(table, reason="", actually_do_it=True):
    calling_fn = get_calling_function()
    qry = f"UPDATE {table} set is_live=False where True"
    newlogger = mylogger()
    if actually_do_it:
        sql_execute(qry)
        newlogger.debug(f'set_ISLIVE_to_false(): Fn: "{calling_fn}" just set "is_live" to False in "{table:13}" for reason: "{reason}"')
    else:
        newlogger.debug(f'set_ISLIVE_to_false(): Fn: "{calling_fn}" wanted to set "is_live" to False in "{table:13}" for reason: "{reason}", but I am skipping this for now')
    return

"""
def set_ISLIVE_to_false(table, calling_fn, reason, actually_do_it=True): 
    #
    params = Parameters(table, "set_ISLIVE_to_false", MASTER_OVERRIDE=True,
                        fixedDict={"curdate": TODAY, "is_live": False,})
    #
    qry = f"select permId, conId, reqId from {table} where curdate='{TODAY}' and is_live"
    res = sql_execute(qry)
    for row in res:
        permId, conId, reqId = row
        params.updateFromDict({"permId": permId,
                               "conId": conId,
                               "reqId": reqId})
        params.processThis(logIt=True)
        if params.msg in ["added", "updated"]:
            newlogger.debug(f"set_ISLIVE_to_false(): '{calling_fn}' just set 'is_live' to False in '{table:13}' for reason: '{reason}'")
        #curtime = f"{TODAY} {rightNow()}"
        #qry = f"UPDATE {table} set is_live=False, curtime='{curtime}' where curdate=CURRENT_DATE"
        #print(f"set_ISLIVE_to_false(x): {qry}")
        #if actually_do_it:
        #    sql_execute(qry)
        #    newlogger.debug(f"set_ISLIVE_to_false(): Fn: '{calling_fn}' just set 'is_live' to False in '{table:13}' for reason: '{reason}'")
        #else:
        #    newlogger.debug(f"set_ISLIVE_to_false(): Fn: '{calling_fn}' wanted to set 'is_live' to False in '{table:13}', for reason: '{reason}', but I am skipping this for now")
    return
"""

def set_GET_GREEKS_to_false(calling_fn, reason, actually_do_it=True):
    qry = f"UPDATE tbl_options set get_greeks=False where True"
    newlogger = mylogger()
    if actually_do_it:
        sql_execute(qry)
        newlogger.debug(f"set_GET_GREEKS_to_false(1): Fn: '{calling_fn}' just set 'get_greeks' to False in 'tbl_options' for reason: '{reason}'")
    else:
        newlogger.debug(f"set_GET_GREEKS_to_false(2): Fn: '{calling_fn}' wanted to set 'get_greeks' to False in 'tbl_options', for reason: '{reason}', but I am skipping this for now")
    return

@static_vars(backedUpThisRun=False)
def backUpOrderFile(orderFile):
    if backUpOrderFile.backedUpThisRun is True:
        return
    backUpOrderFile.backedUpThisRun = True
    #
    assert orderFile.find("MY_ORDERS/") != -1
    orderFile = orderFile.replace("MY_ORDERS/", "")
    root, tail = orderFile.split(".")
    ct = 1
    today = get_sql_today()
    backupFile = f"MY_ORDERS/Used_to_send_orders_out/{root}_{today}_{ct}.{tail}"
    while file_exists(backupFile):
        ct += 1
        backupFile = f"MY_ORDERS/Used_to_send_orders_out/{root}_{today}_{ct}.{tail}"
    copyfile(f"MY_ORDERS/{orderFile}", backupFile)
    newlogger = mylogger()
    newlogger.debug(f"Backup up {orderFile} to {backupFile}")
    return


def get_ETrade_tickers_and_osiKeys():
    myjoe("does this get hit anymore? 8/27/2022")
    minimum_date = should_have_prices_for()

    qry = f"SELECT ticker, osiKey FROM tbl_positions WHERE curdate='{minimum_date}' and secType!='CASH' AND good_position=True AND shares!=0 AND only_IB=False "
          # AND (ticker, osiKey) NOT IN (SELECT ticker, tbl_prices.osiKey FROM tbl_prices WHERE curdate>='{minimum_date}') ORDER BY ticker"
    res = sql_execute(qry)
    return res


def get_next_expiration(ticker):
    from data_file import NO_AVAILABLE_OPTIONS
    if variables.USE_QUARTERLY_EXPIRATIONS:
        infoMsg(f"get_next_expiration(): Using {variables.USE_QUARTERLY_EXPIRATIONS=}")
        qry = f"select distinct IB_expiry, expiry from tbl_IB_option_contract_details where quarterly_expiration and ticker='{ticker}' and expiry>='{TODAY}' order by expiry"
    else:
        qry = f"select distinct IB_expiry, expiry from tbl_IB_option_contract_details where ticker='{ticker}' and expiry>='{TODAY}' order by expiry"
    res = sql_fetchone(qry)
    if res:
        IB_expiry, sql_expiry = res
        return IB_expiry, sql_expiry
    elif ticker not in NO_AVAILABLE_OPTIONS:
        #myjoe("I need to get option contract details for a ticker")
        reset_last_update("IB option contract details")
    #else:
    #    myjoe("whut?")
    return "", ""

def find_not_null_fields_with_defaults():
    # TODO: 'tbl_prices' and 'tbl_etrade_prices' should not have a field called 'open' as it is a reserved word
    def is_a_skip_line(line):
        SKIPS = ["unique", "primary key", "create index"]
        for skip in SKIPS:
            if line.lower().find(skip) != -1:
                return True
        return False
    # -------------------------------------------------------------------------------------------------------------------
    #print()
    qry = "SELECT tbl_name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY tbl_name"
    res = sql_execute(qry)
    max_len = 0
    res_arr = []
    table_arr = []
    for row in res:
        table, sql = row
        #if sql.upper().find("CREATE VIEW") != -1:
        #    continue  # goes to 'for row in res:'
        sql = sql.replace("\t", " ")
        if sql.lower().find("not null") == -1:
            continue
        all_lines = sql.split("\n")
        for line in all_lines:
            if line.lower().find("default '' not null") == -1:
                continue
            if is_a_skip_line(line):
                continue
            if line.lower().find("not null") != -1:
                res_arr.append((table, line))
                table_arr.append(table)
            else:
                raise UserWarning
        if len(table) > max_len:
            max_len = len(table)
    if not res_arr:
        return False
    #
    #print()
    #print(f"Tables with a 'not null' field that has a default set:\n")
    #for tbl, line in res_arr:
    #    print(f"\t{tbl:{max_len}} - {line}")
    #print()
    #
    return res_arr, max_len

def fix_conIds():
    adict = {
        2213: "AIVL 95 C",
        2215: "BP 31 C",
        2217: "CSCO 50 C",
        2219: "DHS 89 C",
        2222: "DVY 129 P",
        2224: "ED 95 P",
        2226: "EWG 26 C",
        2228: "EWU 32 C",
        2230: "IBM 135 C",
        2232: "IWM 173 P",
        2234: "KO 65 C",
        2236: "MO 52.5 C",
        2238: "MS 80 C",
        2240: "PFE 50 C",
        2242: "PG 145 P",
        2244: "QQQ 290 P",
        2246: "STT 67.5 C",
        2248: "T 21 P",
        2250: "VWO 43 P",
        2252: "XLF 34 C",
        2254: "XLU 72 C",
        2256: "XOM 90 C"}

    qry = "select reqId, curdate, ticker, conid from tbl_prices where secType='OPT' and conId=ticker order by reqId"
    res = sql_execute(qry)
    for reqId, curdate, ticker, conid in res:
        ticker, strike, putCall = adict[reqId].split()
        #print(reqId, ticker, strike, putCall)
        conqry = f"select conId from tbl_IB_option_contract_details where ticker='{ticker}' and strike={strike} and putCall='{putCall}' and IB_expiry='20220520'"
        conres = sql_execute(conqry)
        if len(conres) != 1:
            print(conqry)
            myjoe("")
        conId = conres[0]
        print(reqId, ticker, strike, putCall, conId)
        sqry = f"select * from tbl_prices                  where ticker='{ticker}' and secType='OPT' and curdate='2022-05-18'"
        sres = sql_execute(sqry)
        if len(sres) != 1:
            myjoe("")
        else:
            uqry = f"update tbl_prices set conId='{conId}' where ticker='{ticker}' and conId=ticker and secType='OPT' and curdate='2022-05-18'"
            ures = sql_execute(uqry)
            if ures != 1:
                myjoe("")
    return

def find_old_tables():
    qry = "SELECT tbl_name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY tbl_name"
    res = sql_execute(qry)
    today = get_sql_today()
    for row in res:
        table, sql = row
        if sql.lower().find("curtime") != -1:
            #print(f"find_old_tables(): {table} is missing column 'update_msg'")
            curqry = f"select curdate, curtime from {table} order by curtime desc"
            curres = sql_execute(curqry)
            for curdate, curtime in curres:
                if curdate == today:
                    break
                print(f"find_old_tables(): {table:30}, {curdate}, {curtime}")
                break
    return

def reset_SOD_done_thus_far(which="", IB_only=True):
    """ Any SOD done so far, reset it like it wasn't done, so I can run SOD again """
    newlogger = mylogger()
    notToday = get_last_trading_date(ct=1)
    #
    if IB_only is False:
        sel_qry = f"SELECT what FROM tbl_last_updates WHERE last_update='{TODAY}' and category not in ('Admin', 'Report') ORDER BY what"
    else:
        sel_qry = f"SELECT what FROM tbl_last_updates WHERE last_update='{TODAY}' and what like '%IB %' and category not in ('Admin', 'Report') ORDER BY what"
    all_whats = sql_execute(sel_qry)
    if not all_whats:
        myjoe("why are you running this, if there's nothing to reset?")
        return
    max_width = max(map(len, all_whats))
    #
    params = create_A_Param("tbl_last_updates")
    #
    for what in all_whats:
        if IB_only is False and which:
            if what.find(which) == -1:
                continue
        msg = f"reset_SOD_done_thus_far(): setting '{what:{max_width}}' back to: {notToday} .."
        print(msg)
        newlogger.debug(msg)
        params.updateFromDict({"what": what, "last_update": notToday})
        params.processThis()
    params.needToProcess = False
    return



def add_column_to_ALL_tables(new_col, field_type, default=""):
    # alter table tbl_account_PnL add update_msg text default ''
    qry = 'SELECT tbl_name, sql FROM sqlite_master WHERE name=tbl_name and tbl_name not in ("sql_master") ORDER BY name'
    res = sql_execute(qry)
    print(); myjoe()
    print("add_column_to_ALL_tables():")
    for table, sql in res:
        if sql.lower().find(new_col.lower()) != -1:
            # table already has column 'new_col'
            continue
        if not default:
            uqry = f"alter table {table} add {new_col} {field_type}"
        else:
            uqry = f"alter table {table} add {new_col} {field_type} default {default}"
        ures = sql_execute(uqry)
        if ures == -1:
            print(f"\t{table:30}: Added '{new_col}'")
        else:
            print(f"********* {table:30}: DID NOT ADD {new_col} to {table}! *********")
            myjoe("")  #
    return


def tables_missing_fields(fields):
    """ Could use 'add_column_to_ALL_tables()' to add the field itself if I want to
    """
    exceptions = {"curdate": ["tbl_IB_stock_matching_symbols", "tbl_etrade_accounts", "tbl_tickers"],
                  "curtime": ["tbl_IB_stock_matching_symbols", "tbl_etrade_accounts", "tbl_tickers"]}
    return_dict = {}
    ignore = ["sqlite_sequence", "z_space_used"]  # "yfinance_fields"
    qry = "SELECT tbl_name, sql FROM sqlite_master WHERE name=tbl_name ORDER BY name"
    res = sql_execute(qry)
    for table, sql in res:
        if table in ignore:
            continue
        if sql.lower().find("create view") != -1:
            continue
        for field in fields:
            if table in exceptions.get(field, []):
                continue
            if sql.lower().find(field.lower()) == -1:
                if field not in return_dict:
                    return_dict[field] = []
                    last_used = ""
                    if table not in ["tbl_IB_stock_matching_symbols"]:
                        last_used = sql_fetchone(f"select curdate from {table} order by curdate desc")
                return_dict[field].append((table, last_used))
    return return_dict


def get_connection_to_database():
    conn = sqlite3.connect("Data/my_portfolio.db")
    if conn.in_transaction:
        myjoe("")
    fn = get_calling_function()
    print(f"get_connection_to_database(): '{fn}' just connected to 'Data/my_portfolio.db'")
    return conn

def carry_forward_prices():
    params = create_A_Param("tbl_prices")
    FROM_DATE = "2022-07-08"
    TO_DATE = "2022-07-09"
    qry = f"select ticker, conId, osiKey, close, price, bid, ask, last from tbl_prices where curdate='{FROM_DATE}' and secType='STK'"
    res = sql_execute(qry)
    for ticker, conId, osiKey, close, price, bid, ask, last in res:
        params.param_dict["curdate"] = TO_DATE         #  <-----------------
        params.param_dict["ticker"] = ticker
        params.param_dict["conId"] = conId
        params.param_dict["osiKey"] = osiKey
        params.param_dict["close"] = close
        params.param_dict["price"] = price
        params.param_dict["bid"] = bid
        params.param_dict["ask"] = ask
        params.param_dict["last"] = last
        #
        params.processThis(logIt=True)
        #
    return

def carry_forward_positions():
    params = create_A_Param("tbl_positions")
    FROM_DATE = "2022-07-05"
    TO_DATE = "2022-07-07"
    qry = f"select ticker, secType, account, broker, conId, osiKey from tbl_positions where curdate='{FROM_DATE}' and secType='STK'"
    res = sql_execute(qry)
    for ticker, conId, osiKey, close, price, bid, ask, last in res:
        params.param_dict["curdate"] = TO_DATE         #  <-----------------
        params.param_dict["ticker"] = ticker

        params.param_dict["conId"] = conId
        params.param_dict["osiKey"] = osiKey
        params.param_dict["close"] = close
        params.param_dict["price"] = price
        params.param_dict["bid"] = bid
        params.param_dict["ask"] = ask
        params.param_dict["last"] = last
        #
        params.processThis(logIt=True)
        #
    return


def check_execIds():
    qry = "select curdate, execId, ticker from tbl_IB_executions"
    res = sql_execute(qry)
    bad_res = []
    for curdate, execId, ticker in res:
        qry2 = f"select curdate, execId, ticker from tbl_IB_executions " \
               f"where curdate='{curdate}' and execId='{execId}' and ticker='{ticker}'"
        res2 = sql_execute(qry2)
        if not res2:
            bad_res.append((curdate, execId, ticker, None))
        if len(res2) > 1:
            bad_res.append((curdate, execId, ticker, len(res2)))
    return bad_res

# -------------------------------------------------------------------------------------------------------------------
def check_missing_orders():
    """ Look for an order that vanished, see that I have an execution for it. If not, flag it """
    # -------------------------------------------------------------------------------------------------------------------
    # --- IB ------------------------------------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------------------------------------
    cutoff = get_days_ago_date(-7)
    qry = f"select distinct curdate, ticker, secType, totalQuantity from tbl_IB_orders " \
          f"where curdate>'{cutoff}' and secType='STK' order by ticker, curdate desc"
    res = sql_execute(qry)
    prev_orders_dict = {}
    todays_orders_dict = {}
    res_arr = []
    for row in res:
        curdate, ticker, secType, totalQuantity = row
        if curdate == TODAY:
            todays_orders_dict[ticker] = (curdate, secType, totalQuantity)
        if ticker in todays_orders_dict:
            continue
        if ticker in prev_orders_dict:
            continue
        prev_orders_dict[ticker] = (curdate, secType, totalQuantity)
    for ticker, value in prev_orders_dict.items():
        curdate, secType, totalQuantity = value
        qry2 = f"select curdate, ticker, shares from tbl_IB_executions where ticker='{ticker}' " \
               f"and shares={totalQuantity} and shares=cumQty and curdate>'{curdate}' order by curdate desc"
        res2 = sql_execute(qry2)
        if not res2:
            warn_print(f"check_missing_orders(): IB: {curdate}, {ticker}, {secType}, {totalQuantity}")
            res_arr.append(("IB", curdate, ticker, secType, totalQuantity))

    # -------------------------------------------------------------------------------------------------------------------
    # --- ETRADE --------------------------------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------------------------------------
    qry = "select distinct curdate, ticker, secType, orderedQuantity, filledQuantity, status " \
          "from tbl_etrade_orders where curdate>'2022-06-01' and orderedQuantity!=filledQuantity and status!='CANCELLED' " \
          "order by curdate desc"
    res = sql_execute(qry)
    for row in res:
        curdate, ticker, secType, orderedQuantity, filledQuantity, status = row
        print(f"ETrade: {curdate}, {ticker}, {secType}, {orderedQuantity}")
        res_arr.append(("ETrade", curdate, ticker, secType, orderedQuantity))

    return res_arr
# -------------------------------------------------------------------------------------------------------------------


def reorderColumns():
    # Note: see 'column_value_counter()' to help figure out the important columns
    """ Assume table_A with    col1 int, col3 int, col2 int
        - You could create a tableB with the columns sorted the way you want:
          create table table_B(
            col1 int, col2 int, col3 int);
        - Then move the data to tableB from tableA:
          insert into tableB SELECT col1, col2, col3 FROM tableA;
        - Then remove the original tableA and rename tableB to TableA:
          DROP table tableA;
          ALTER TABLE tableB RENAME TO tableA;
    """
    """    last_update, what, cycle, vacation_cycle, category, source, update_msg, note, morning_routine, needs_live_market, curtime, curdate 
    """
    qry = f"SELECT last_update, what, cycle, vacation_cycle, category, source, update_msg, note, morning_routine, needs_live_market, curtime, curdate " \
          f"FROM tbl_last_updates where last_update>='2022-08-05' order by what"
    tbl_last_updates = sql_execute(qry)
    #
    params = create_A_Param("tbl_last_updates_new", "reorderColumns")
    #
    for row in tbl_last_updates:
        last_update, what, cycle, vacation_cycle, category, source, update_msg, note, morning_routine, needs_live_market, curtime, curdate = row
        params.param_dict["last_update"] = last_update
        params.param_dict["what"] = what
        params.param_dict["cycle"] = cycle
        params.param_dict["vacation_cycle"] = vacation_cycle
        params.param_dict["category"] = category
        params.param_dict["source"] = source
        params.param_dict["update_msg"] = update_msg
        params.param_dict["note"] = note
        params.param_dict["morning_routine"] = morning_routine
        params.param_dict["needs_live_market"] = needs_live_market
        params.param_dict["curtime"] = curtime
        params.param_dict["curdate"] = curdate
        #
        params.processThis()
        #
    return

def VACUUM():
    sql_execute("VACUUM")

def get_large_database_tables():
    sizes = {25000: ["tbl_IB_option_contract_details"],
             30000: ["tbl_report_timings"],
             90000: ["tbl_prices"],
             100000: ["tbl_account_summary"],
             }
    """ orig = f"select tblname, nentry from z_space_used where name=tblname and curdate='{TODAY}' and (" \
          f"(tblname='tbl_IB_option_contract_details' and nentry>25000) or " \
          f"(tblname='tbl_report_timings' and nentry>25000) or " \
          f"(tblname='tbl_prices' and nentry>90000) or " \
          f"(tblname='tbl_account_summary' and nentry>100000) or " \
          f"tblname not in ('tbl_prices', 'tbl_account_summary') and nentry > 20000 " \
          f") order by nentry desc"
    """
    all_tables = []
    qry = f"select tblname, nentry from z_space_used where name=tblname and curdate='{TODAY}' and ("
    for limit, tables in sizes.items():
        for table in tables:
            all_tables.append(table)
            qry += f"(tblname='{table}' and nentry>{limit}) or "
    table_str = "', '".join(all_tables)  # (sizes.keys())
    qry += f"tblname not in ('{table_str}') and nentry > 20000) order by nentry desc"
    res = sql_execute(qry)
    return res


def backfill(table, date):
    """ Take a row from a table and copy it backward to missing dates
    """
    raise NotImplemented


def look_for_nulls(table=None):
    print()
    if isinstance(table, str):
        tables = [table]
    else:
        tables = sql_execute("select tbl_name from sqlite_master where tbl_name=name order by tbl_name")
    ALL = {}
    #GOOD = ["tbl_ALGO_ORDERS", "tbl_exceptions_raised", "log_messages", "tbl_IB_option_contracts_needed", "tbl_IB_order_status", "tbl_account_PnL", "tbl_account_summary", "tbl_alerts", "tbl_dividends", "tbl_errors",
    #        "tbl_etrade_accounts", "tbl_morning_report", "tbl_report_timings", "tbl_reports", "tbl_returns", "tbl_snapper", "tbl_spin_offs", "tbl_IB_orders", "tbl_telegram", "trade_values", "zero_returns",
    #        "tbl_IB_bad_option_specs", "tbl_IB_commissions", "tbl_IB_executions", "tbl_IB_option_contract_details", "tbl_IB_order_state", "tbl_IB_stock_contract_details", "tbl_IB_stock_matching_symbols",
    #        "tbl_etrade_orders", "tbl_etrade_positions", "tbl_last_updates", "tbl_options", "tbl_options_trades", "tbl_pnl_single", "tbl_positions", "tbl_prices", "tbl_recommendations", "tbl_splits", "z_space_used"]
    GOOD = []
    for table in tables:
        if table in GOOD:
            continue
        qry = f"select * from {table}"
        dict_arr = sql_execute(qry, returnDICT=True)
        fields = []
        for adict in dict_arr:
            for field, value in adict.items():
                if value is None:
                    if field not in fields:
                        fields.append(field)
        if fields:
            ALL[table] = fields
        #else:
            #print(f"look_for_nulls() : '{table}' has no nulls")
    if ALL:
        for table, fields in ALL.items():
            for field in fields:
                print(f"\t{table:40} : {field}")
                uqry = f"update {table} set {field}='' where {field} is NULL"
                sql_execute(uqry)
            print()
        VACUUM()
    set_last_update("Look For Nulls")
    return True


def column_value_counter(table, notOnes=True):
    MANY = 5
    params = create_A_Param(table)
    # ---------------------------------------
    def myprint(rank, field, ct):
        nonlocal notOnes, params
        type_ = params.field_types[field]
        if notOnes is False or rank > 1:
            #if rank >= MANY:
            #    #print(f"{rank:3}     {field}")
            #    print(field)
            #else:
            #    print(field)
            if type_ != "boolean":
                print(field)
            else:
                print(f"{field:40} {type_}")
        return
    # ---------------------------------------
    adict = {}
    for field in params.fields:
        qry = f"select distinct {field} from {table} where {field} is not NULL"
        res = sql_execute(qry)
        ct = len(res)
        if ct not in adict:
            adict[ct] = []
        adict[ct].append(field)
    good_fields = []
    one_fields = []
    null_fields = []
    print(f"\nMANY (>{MANY}) value(s):")
    print(f"---------")
    for rank in sorted(adict.keys(), reverse=True):
        fields = adict[rank]
        fields.sort()
        ct = len(fields)
        if rank < MANY:
            print(f"\n{rank} values:")
            print(f"---------")
        for field in fields:
            myprint(rank, field, ct)
            if ct > 1:
                good_fields.append(field)
            elif ct == 1:
                one_fields.append(field)
            else:
                null_fields.append(field)
    print()
    if notOnes:
        all_fields = good_fields + null_fields
        qry = f"select {', '.join(good_fields)},\n{', '.join(null_fields)} \nfrom {table}"
    else:
        all_fields = good_fields + one_fields + null_fields
        qry = f"select {', '.join(good_fields)},\n{', '.join(null_fields)} \nfrom {table}"
    print(qry)
    pyperclip.copy(qry)
    return



if __name__ == '__main__':
    #find_word_in_tables("current_time")
    #VACUUM()
    #column_value_counter("tbl_IB_orders", notOnes=False)
    run_a_database_analysis()
