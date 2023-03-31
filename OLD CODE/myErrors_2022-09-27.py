
# -------------------------------------------------------------------------------------------------------------------
class MY_IB_FLAGS(Exception):
    FLAG = False
    def __init__(self, msg=None, flag=False):
        # flag: True  - set tbl_last_updates
        #       False - do not set tbl_last_updates
        self.FLAG = flag
        if msg:
            self.msg = msg
        else:
            self.msg = "MY_IB_FLAGS"

    def __repr__(self):
        raise AttributeError  # You need to overwrite this function!
        #return "MY_IB_FLAGS(Exception)"

# -------------------------------------------------------------------------------------------------------------------

class MY_IB_FLAGS_INT(Exception):
    ct = 0
    def __init__(self, msg=None, ct=0):
        self.COUNTER = ct
        if msg:
            self.msg = msg
        else:
            self.msg = "MY_IB_FLAGS_INT"

    def __repr__(self):
        raise AttributeError  # You need to overwrite this function!
        #return "MY_IB_FLAGS_INT(Exception)"
# -------------------------------------------------------------------------------------------------------------------

class IB_FALSE_EXIT(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("IB_FALSE_EXIT")

    def __repr__(self):
        return "IB_FALSE_EXIT(MY_IB_FLAGS)"

class MYJOE_WAS_RAISED(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("MYJOE_WAS_RAISED")

    def __repr__(self):
        return "MYJOE_WAS_RAISED(MY_IB_FLAGS)"

class IB_DONE_PLACING_ORDERS(MY_IB_FLAGS_INT):
    def __init__(self, ct):
        super().__init__("IB_DONE_PLACING_ORDERS", ct)

    def __repr__(self):
        return "IB_DONE_PLACING_ORDERS(MY_IB_FLAGS_INT)"

class HAVE_TO_GET_MORE_OPTION_DATA(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("HAVE_TO_GET_MORE_OPTION_DATA")

    def __repr__(self):
        return "HAVE_TO_GET_MORE_OPTION_DATA(MY_IB_FLAGS)"

class BAD_FIELD_NAME(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("BAD_FIELD_NAME")

    def __repr__(self):
        return "BAD_FIELD_NAME(MY_IB_FLAGS)"

class BAD_FORMATTER(MY_IB_FLAGS):
    def __init__(self, name):
        super().__init__(f"BAD_FORMATTER: '{name}'")

    def __repr__(self):
        return "BAD_FORMATTER(MY_IB_FLAGS)"

class IB_NOT_CONNECTED(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_NOT_CONNECTED", flag)

    def __repr__(self):
        return "IB_NOT_CONNECTED(MY_IB_FLAGS)"

class NO_MORE_ORDERS(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("NO_MORE_ORDERS", flag)

    def __repr__(self):
        return "NO_MORE_ORDERS(MY_IB_FLAGS)"

# --------------------------------------------------------------------
class IB_IS_DONE(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_IS_DONE", flag)

    def __repr__(self):
        return "IB_IS_DONE(MY_IB_FLAGS)"
# --------------------------------------------------------------------

class IB_HAS_ALL_PRICES(MY_IB_FLAGS):
    def __init__(self, flag):
        joe = self.__class__.__name__ g g g
        super().__init__("IB_HAS_ALL_PRICES", flag)

    def __repr__(self):
        return "IB_HAS_ALL_PRICES(MY_IB_FLAGS)"

class IB_ACCOUNT_SUMMARIES_DONE(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_ACCOUNT_SUMMARIES_DONE", flag)

    def __repr__(self):
        return "IB_ACCOUNT_SUMMARIES_DONE(MY_IB_FLAGS)"

class IB_HAS_ALL_GREEKS(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_HAS_ALL_GREEKS", flag)

    def __repr__(self):
        return "IB_HAS_ALL_GREEKS(MY_IB_FLAGS)"

class IB_ALL_REQUESTS_GOT_STALE(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_ALL_REQUESTS_GOT_STALE", flag)

    def __repr__(self):
        return "IB_ALL_REQUESTS_GOT_STALE(MY_IB_FLAGS)"

class IB_ALL_REQUESTS_GOOD_OR_ERRORED(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_ALL_REQUESTS_GOOD_OR_ERRORED", flag)

    def __repr__(self):
        return "IB_ALL_REQUESTS_GOOD_OR_ERRORED(MY_IB_FLAGS)"

class IB_REQUESTS_WERE_STALE(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_REQUESTS_WERE_STALE", flag)

    def __repr__(self):
        return "IB_REQUESTS_WERE_STALE(MY_IB_FLAGS)"

class IB_NOTHING_TO_DO(MY_IB_FLAGS):
    def __init__(self, flag):
        super().__init__("IB_NOTHING_TO_DO", flag)

    def __repr__(self):
        return "IB_NOTHING_TO_DO(MY_IB_FLAGS)"

class IB_GET_GREEKS(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("IB_GET_GREEKS(MY_IB_FLAGS)")

    def __repr__(self):
        return "NO_MORE_ORDERS(MY_IB_FLAGS)"

class IB_PRICES_ARE_HANGING(MY_IB_FLAGS):
    # Used for both greeks and prices, as they both use reqMktData
    def __init__(self, flag):
        super().__init__("IB_PRICES_ARE_HANGING", flag)

    def __repr__(self):
        return "IB_GET_GREEKS(MY_IB_FLAGS)"

class IB_MISSING_PRICES(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("IB_MISSING_PRICES", False)

    def __repr__(self):
        return "IB_MISSING_PRICES(MY_IB_FLAGS)"

class IB_GET_OPTION_DETAILS(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("IB_GET_OPTION_DETAILS")

    def __repr__(self):
        return "IB_GET_OPTION_DETAILS(MY_IB_FLAGS)"

class TWS_DIED_ON_ME(MY_IB_FLAGS):
    def __init__(self, all_requests):
        super().__init__("TWS_DIED_ON_ME")
        self.all_requests = all_requests


    def __repr__(self):
        return "TWS_DIED_ON_ME(MY_IB_FLAGS)"

class MY_SEAL_ERROR(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("SEAL_ERROR")

    def __repr__(self):
        return "MY_SEAL_ERROR(MY_IB_FLAGS)"

"""
class CAUGHT_ERROR_IN_MY_CONTEXT_MANAGER(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("CAUGHT_ERROR_IN_MY_CONTEXT_MANAGER")
"""

"""
class MY_ASSERTION_ERROR(MY_IB_FLAGS):
    def __init__(self):
        super().__init__("MY_ASSERTION_ERROR")
"""

