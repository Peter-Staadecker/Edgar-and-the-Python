# This  program was written as a Python learning exercise only. It is not guaranteed
# or intended for any other purpose and should not be used for stock trading. Parts of the
# program were based on code samples suggested by financialmodelingprep.com
#
# The program takes a user-defined stock list of large US ticker symbols & looks up both the SEC's CIK (central index
# key), the current stock price, and the stock split history on Financial Modeling Prep (see
# https://financialmodelingprep.com/developer/docs/). Access to Financial Modeling Prep is available with an
# API key which the user must enter into the program code. The user can also vary a number of other program
# parameters (discussed below) in the code.

# For each stock in the stock list, the program calculates the compound annual growth rate (CAGR) for the diluted
# earnings per share (EPS) over the past x (usually 10) years. Because Financial Modeling Prep limits free EPS data to
# five years, the program takes its EPS history from the SEC's Edgar database of company filings. The program then
# calculates the internal rate of return (IRR) and net present value (NPV) for someone purchasing a single unit of the
# stock at the current share price, assuming the EPS growth continues unchanged for a user-defined number of years
# after the purchase. The program also calculates the minimum EPS growth needed for the NPV of the purchaser's
# share earnings to break even with the share purchase.
#
# This last calculation is performed iteratively up to a maximum of 20 steps. If no minimmum EPS growth can be found for
# the NPV to break even, the iteration attempts are output to a .csv file for inspection and a warning is printed.

# The user is able to alter the discount rate for the NPV in the code, and to alter the number of years over which the
# NPV and IRR are calculated.
#
# The share purchaser's personal taxes are ignored. Terminal values for the stock are ignored. The EPS in the year of
# purchase is ignored. Additional assumptions not listed here may be implicit in the code.
#
# The program prints results both to the terminal console and to an Excel file. The file is saved in the same directory
# as the program. In the case of an early end to the program a partial output file is provided.
#
# As mentioned, the program takes some data from financial modeling prep and some from the SEC in order to obtain
# x (usually 10) years EPS history. If 5 years history is sufficient an alternative, simpler Python program is
# available that # takes all data from financial modeling prep without the complications of accessing SEC data.
#
# This program (taking data from both sources) was written as a Python learning exercise and is not intended for
# stock trading, trading advice or any # other purpose. Nor is it guaranteed to be in any way error-free.
# Comments, corrections and suggestions are welcome.

# For Python 3.0 and later
import json
import sys
import numpy as np
import numpy_financial as npf
import pandas as pd
from datetime import datetime
from urllib.request import urlopen
from colorama import Fore
import copy
import ssl
import requests
import time as time


# ---------------------------------------------------------------------------------------------------
def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """

    #   response = urlopen(url, cafile=certifi.where())
    #   in the above line cafile is now deprecated. Have used the below ssl line instead
    #   although the ssl line may not even be needed - I'm merely following documentation.
    delay(oldTimeStamp)  # calls for a delay between repeat calls to data providers.
    myContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    response = urlopen(url, context=myContext)
    data = response.read().decode("utf-8")
    return json.loads(data)


# ---------------------------------------------------------------------------------------------------
def get_sec_json(url):
    """
    Receive the content of ``url``, add SEC-required url headers, parse response as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    string that can be used as dictionary
    """

    errorFlag = False
    head = {"Accept-Encoding": "gzip, deflate", "User-Agent": myEmail, "Host": "data.sec.gov"}
    r = requests.get(url, headers=head)
    if r.status_code == 404:
        errorFlag = True
        print("CIK not found in ", url)
        pdResults.loc[stock, "Warnings if any"] = "CIK not found in " + url
        returnDict: dict = {"error": "error"}
    else:
        returnDict = dict(json.loads(r.text))

    getSecList = [errorFlag, returnDict]
    return getSecList


# --------------------------------------------------------------------------------------------------------
# this sub open the csv file to which the price/book ratios will be saved.
# The "w" parameter means old files are overwritten
def fileopen(filename):
    try:
        file = open(filename, "w")
        return file
    except IOError:
        print("Could not open file! Is it already/still open - please close it.")
        input("Please press enter to confirm you've seen this message.")
        sys.exit()


# --------------------------------------------------------------------------------------------------------------------
# this sub converts a number in string format to a number in floating decimal format
def strToFloat(x):
    try:
        if x == "":
            x = 0
        x = float(x)
        return float(x)

    except Exception as ex1:
        print(ex1)
        template1 = "An exception of type {0} occurred in the function strToFloat. Arguments:\n{1!r}"
        message1 = template1.format(type(ex1).__name__, ex1.args)
        print(message1)
        sys.exit()


#  --------------------------------------------------------------------------------------------------------------------
# subroutine to delay between successive calls to a data source url like SEC or fin mod prep, if needed,
# for using these resource respectfully.
def delay(priorTimeStamp):
    global oldTimeStamp
    elapsedTime = datetime.now() - priorTimeStamp
    elapsedSec = elapsedTime.seconds + elapsedTime.microseconds / 1000000
    if elapsedSec < 1.0:
        addDelay = 1.0 - elapsedSec
        time.sleep(addDelay)
        oldTimeStamp = datetime.now()  # after sleeping update the baseline timestamp


# --------------------------------------------------------------------------------------------------------------------
# A subroutine to lookup a value in a python dictionary previously constructed to contain SEC data.
# Example: in the EPS dictionary find the most recent entry having "frame" = "CY2012" and return the EPS value in
# the associated "val" field. In this example, "frame" is the lookupkey, "CY2012" is the lookupval, "val" is the target
# key. # The message_prefix in this example will likely be stock + "EPS", where stock is the ticker symbol of the
# stock for which the lookup is being conducted. The errorflag will return a value of True if no match is found.
# If a match is found in the i'th dictionary entry, errorflag = False and the value of i is also returned to the
# calling program.

def dictsearch(dictParam, lookupkey, lookupval, targetkey, message_prefix):
    errorFlag = True
    for ii in range(1, len(dictParam)):
        if lookupkey in dictParam[ii]:
            if dictParam[ii][lookupkey] == lookupval:
                errorFlag = False
                break  # once a match is found break out of for loop

    if errorFlag:
        print(Fore.RED, "The SEC data for ", message_prefix, " does not contain ", lookupkey, " with value = ",
              lookupval)
        print(Fore.BLACK, end="")
        pdResults.loc[stock, "Warnings if any"] = "The SEC data for " + message_prefix + " does not contain " + \
                                                  lookupkey + " with value = " + lookupval
    '''else:
        print("The SEC data for ", message_prefix, " with ", lookupkey, " = ", lookupval, " has ",
              targetkey, ' = ', dictParam[ii][targetkey])'''

    list1 = list([ii, dictParam[ii][targetkey], errorFlag])
    return list1


# ---------------------------------------------------------main----------------------------------------------------
# -----------------------------------------------------user input//////////////////////////////////////////////////
# access key for financial modeling prep dot com

myApiKey = "<Insert your API key here>"  # <---- insert your API key here

# ticker list and description.
stockListInput = ['aapl', 'fts', 'wec', 'nvda', 'jpm', 'chd']
listDescription: str = "test data"

# stocks with market cap < minMarketCap will be ignored
minMarketCap: float = 1000000000.0

# years of EPS history to look for in SEC/Edgar
yrsHistory: int = 10

# npv discount factor and years of growth after purchase
disctFactor: float = .06
yrsDiscted: int = 15

# administrator email address to be provided in any programmed url request header going to SEC Edgar, per their request
myEmail = "<Insert your admin email here for inclusion in the SEC/Edgar url request header>"  # <---- insert
# ----------------------------------------------------check and cleanse user input-------------------------------------

if myApiKey == "<Insert your API key here>":
    print("Error. You must obtain a valid API key from financialmodelingprep.com "
          "and insert it into the code input section. The program will end.")
    sys.exit()

if myEmail == "<Insert your admin email here for inclusion in the SEC/Edgar url request header>":
    print("Error. When a program automates access to the SEC/Edgar, it is required to give an admin email in the "
          "URL request header. Please insert the email into the code input section. The program will end.")
    sys.exit()

# stocks must be uppercase
stockList: list = []
for stocks in stockListInput:
    stockList = stockList + [stocks.upper()]

# ----------------------------------------------------initialize misc. variables---------------------------------
currentTime = datetime.now()
currentYear = currentTime.year
currentYearStr = str(int(currentYear))

# prepare a dataframe to hold the results of the caclulations across all stocks in stocklist.
# dataframe row index = stocklist names.
# dataframe column names as follows:

colNames = ["Name", "CIK", "Currency", "Newest yr history", "Oldest yr history", "EPS newest",
            "Comprehensive Net Income gr % pa",
            "EPS gr % pa", "Req gr % pa for NPV break-even", "Share gr % pa",
            "Price", "Shares out-standing", "Mkt Cap", "NPV of Future EPS", "Disct rate %",
            "IRR %", "Warnings if any", "Yrs discounted after purchase"]

# npResults = np.zeros([len(stockList), len(colNames)])
# pdResults = pd.DataFrame(data=npResults, index=stockList, columns=colNames)
pdResults = pd.DataFrame(index=stockList, columns=colNames)

# print gen info
print("CIK provided by Financial Modeling Prep (see https://financialmodelingprep.com/developer/docs/)")
print("This program is a Python learning exercise, not to be used for stock trading or financial advice. ")

# --------------------------------------------loop through each stock--------------------------------------------
for stock in stockList:
    oldTimeStamp = datetime.now()  # baseline, allows a delay to be called later before repeat access to data provider

    # initialize for each stock. EPS[0] is newest year, EPS[1] is oldest year of history series, e.g.
    NetIncome: float = [0, 0]
    EPS: float = [0, 0]
    EPSsplit: float = 1.0
    SharesOut: float = [0, 0]
    Year = [0, 0]
    seriesStart: datetime = datetime(1900, 1, 1)
    seriesEnd: datetime = datetime(1900, 1, 1)
    splitNumerator: float = 1.0
    splitDenominator: float = 1.0

    # print blank line, then ticker
    print("")
    print("Ticker = " + stock)

    # --------------get the SEC CIK (central index key) and current share price from financial modeling prep----------
    urlIncome = "https://financialmodelingprep.com/api/v3/income-statement/" + stock + "?apikey=" + myApiKey + \
                "&limit=1"
    urlSharePrice = "https://financialmodelingprep.com/api/v3/quote-short/" + stock + "?apikey=" + myApiKey
    urlSplitHistory = "https://financialmodelingprep.com/api/v3/historical-price-full/stock_split/" + \
                      stock + "?apikey=" + myApiKey

    # load url for stock income statement
    try:
        bigDict = dict(get_jsonparsed_data(urlIncome)[0])
    except:
        # above will throw an error if e.g. the ticker symbol is invalid
        print(Fore.RED, "Ticker symbol ", stock, " not found in financial modeling prep")
        pdResults.loc[stock, "Warnings if any"] = "Ticker symbol not found in financial modeling prep."
        print(Fore.BLACK, end="")
        continue  # move on to next stock

    # form of bigDict is
    # [{ #   "date" : "2021-09-25", "symbol" : "AAPL", "reportedCurrency" : "USD", "cik" : "0000320193",.....   ...},
    #   { "date" : "2020-09-26", "symbol" : "AAPL", "reportedCurrency" : "USD", "cik" : "0000320193", ......

    if bigDict == {}:
        print(Fore.RED, "No income statement for ", stock, "in financial modeling prep")
        pdResults.loc[stock, "Warnings if any"] = "No income statement found in financial modeling prep."
        print(Fore.BLACK, end="")
        continue  # move on to next stock

    # get the SEC CIK (central index key)
    cikStr = bigDict['cik']

    if cikStr == "":
        print(Fore.RED, "CIK not found in fin. modelling prep for ", stock)
        pdResults.loc[stock, "Warnings if any"] = "CIK not found in financial modelling prep."
        print(Fore.BLACK, end="")
        continue  # move on to next stock

    # ---------------------------------search SEC for most recent full year EPS info-----------------------------------
    # because financial modeling prep only provides 5 years free history.
    # (If 5 years history is sufficent, use the alternative program that is purely financial modeling prep-based.)
    secEPSURL = "https://data.sec.gov/api/xbrl/companyconcept/CIK" + cikStr + "/us-gaap/EarningsPerShareDiluted.json"
    myList2: list = get_sec_json(secEPSURL)
    if myList2[0]:  # element 0 is error flag, if true cikstr was not found, move on to next stock
        continue

    EPSbigDict: dict = myList2[1]  # get_sec_json return list element 1 is the dictionary
    # dictionary format. Format is
    # {"cik": ... ,"units":{"USD/shares":[{"start":"2006-10-01","end":"2007-09-29","val":3.93, ....

    if EPSbigDict == {}:
        print(Fore.RED, "No SEC EPS entry for ", stock, " with CIK = ", cikStr)
        pdResults.loc[stock, "Warnings if any"] = "CIK not found in SEC EPS link."
        print(Fore.BLACK, end="")
        continue  # move on to next stock

    print("CIK = ", cikStr)
    pdResults.loc[stock, "CIK"] = cikStr
    pdResults.loc[stock, "Name"] = EPSbigDict["entityName"]

    # find out which currency/shares is being used
    keylist = list(EPSbigDict["units"].keys())
    currencyPerShare = keylist[0]

    EPSCoreDict: dict = EPSbigDict["units"][currencyPerShare]  # normally this is USD/share, but could be CAD/share etc
    # search for the newest reported full year EPS in SEC. Search from bottom of file backwards (i.e. search from
    # newest entries first) for picking up any amendments following the original filings. Don't know in advance what
    # the newest year will be it could be this yr or this yr -1.

    # Find out what the most recent full year data is. Go to end of file for most recent, search backwards.
    targetFrameMostRecent: str = ""
    for i in range(len(EPSCoreDict) - 1, -1, -1):
        if "frame" in EPSCoreDict[i] and not ("Q" in EPSCoreDict[i]["frame"]):
            targetFrameMostRecent = EPSCoreDict[i]["frame"]
            Year[0] = int(EPSCoreDict[i]["end"][0:4])  # first 4 characters
            EPS[0] = EPSCoreDict[i]["val"]  # EPS newest year
            seriesEnd = datetime.strptime(EPSCoreDict[i]["end"], "%Y-%m-%d")
            break  # break out of for i loop once you have a match

    if targetFrameMostRecent == "":
        print(Fore.RED, "No newest year EPS found in SEC data for", stock, " with CIK = ", cikStr)
        print(Fore.BLACK, end="")
        continue  # move on to next stock

    # print("EPS for ", Year[0], " =  ", EPS[0])

    # --------------------search SEC for most recent full year reported comprehensive net income----------------------
    # taxonomy (reported item, definition and labelling) for net income changes in SEC over the years
    # use comprehensive income instead
    secIncURL = "https://data.sec.gov/api/xbrl/companyconcept/CIK" + \
                cikStr + "/us-gaap/ComprehensiveIncomeNetOfTax.json"

    IncBigDict: dict = get_sec_json(secIncURL)[1]   # returns json.loads(r.text) with r.text a string as dictionary
    # format is
    # {"cik": ... ,"units":{"USD:[{"start":"2006-10-01","end":"2007-09-29","val":3.93, ....

    if IncBigDict == {}:
        print(Fore.RED, "No SEC comprehensive net income entry for ", stock, " with CIK = ", cikStr)
        pdResults.loc[stock, "Warnings if any"] = "Comprehensive net income not found in SEC."
        print(Fore.BLACK, end="")
        continue  # move on to next stock

    # find out which currency is being used
    keylist = list(IncBigDict["units"].keys())
    currency = keylist[0]
    pdResults.loc[stock, "Currency"] = currency
    # print("Currency is ", currency)

    IncCoreDict: dict = IncBigDict["units"][currency]
    # look for comprehensive net income with frame containing CY targetyearmosrecent
    lookUP1: list = dictsearch(IncCoreDict, "frame", targetFrameMostRecent, "val", "comprehensive net income")
    if lookUP1[2]:  # if errorflag returned by dictsearch = True dictsearch failed, possibly no value found
        continue    # move on to next stock

    NetIncome[0] = lookUP1[1]

    # ----------Search SEC for a full year EPS report that is yrshistory (usually 10) years older than the above-------
    Year[1] = Year[0] - yrsHistory  # looking for 10 years history (typically) prior to newest year
    targetFrameOld = "CY" + str(Year[1])
    lookUP2: list = dictsearch(EPSCoreDict, "frame", targetFrameOld, "val", "EPS unadjusted for subsequent splits")
    
    if lookUP2[2]:  # if errorflag returned by dictsearch = True dictsearch failed, possibly no value found
        continue    # move on to next stock
    
    i = lookUP2[0]
    EPS[1] = EPSCoreDict[i]["val"]  # EPS for 10 yrs (or whatever) ago
    seriesStart = datetime.strptime(EPSCoreDict[i]["end"], "%Y-%m-%d")

    # --------------look up stock splits in interval between history seriesStart and seriesEnd------------------------
    # load url for split history as dict
    splitBigDict = get_jsonparsed_data(urlSplitHistory)
    # form of bigDict is
    # { "symbol": "AAPL", "historical": [{
    #        "date": "2020-08-31", ...

    if splitBigDict != {}:
        splitDict = splitBigDict["historical"]
        # get number of dictionary entries and loop through them
        for i in range(0, len(splitDict)):
            splitDate: datetime = datetime.strptime(splitDict[i]["date"], "%Y-%m-%d")
            if seriesEnd > splitDate > seriesStart:
                splitNumerator = splitNumerator * strToFloat(splitDict[i]["numerator"])
                splitDenominator = splitDenominator * strToFloat(splitDict[i]["denominator"])

        if splitDenominator == 0 or splitNumerator == 0:
            print(Fore.RED, "Error in split adj. calculation for ", stock, " CIK ", cikStr)
            print(Fore.BLACK, end="")
            pdResults.loc[stock, "Warnings if any"] = "Error in split adjustment calculation."
            continue  # move on to next stock

        splitMultiplier: float = splitNumerator/splitDenominator
        print("Cumulative stock splits between ", Year[1], " and ", Year[0], "= ", str(splitMultiplier))
        EPS[1] = EPS[1] / splitMultiplier
        # print("EPS in ", Year[1], " adjusted for subsequent splits throught to ", Year[0], " is ", EPS[1])

    # --------------look for the yrshistory (usually 10) years prior for comprehensive net income---------------------
    lookUP3: list = dictsearch(IncCoreDict, "frame", targetFrameOld, "val", " comprehensive net income ")
    if lookUP3[2]:  # dictsearch returns errorflag because fails to find value, move on to next stock
        continue
   
    j = lookUP3[0]
    NetIncome[1] = IncCoreDict[j]["val"]  # EPS for 10 yrs (or whatever) ago

    # print years
    print("..................................Newest Year................Oldest year")
    print("                                     " + str(Year[0]) + "                       " + str(Year[1]))

    # check newest year data
    if EPS[0] < 0:
        print(Fore.RED, "EPS is negative in most recent history in SEC for ",
              stock, " CIK ", cikStr)
        print(Fore.BLACK, end="")
        pdResults.loc[stock, "Warnings if any"] = "EPS is negative in SEC for most recent history year."
        continue

    # if either old or new EPS is non-positive print warning and advance to next stock in stocklist
    if (EPS[0] <= 0) or (EPS[1] <= 0):
        print(Fore.RED, "Oldest or newest comprehensive net income, or both, were non-positive for ", stock,
              " CIK ", cikStr)
        pdResults.loc[stock, "Warnings if any"] = "Oldest or newest EPS was non-positive."
        continue

    # from here on both old and new EPS are positive
    # calculate % compound annual growth rate from oldest year to newest year
    SharesOut[0] = NetIncome[0] / EPS[0]
    SharesOut[1] = NetIncome[1] / EPS[1]

    if SharesOut[0] < 1 or SharesOut[1] < 1:
        print(Fore.RED, "Shares outstanding estimation has resulted in negative shares.")
        print(Fore.BLACK, end="")
        pdResults.loc[stock, "Warnings if any"] = "Estimate of shares outstanding is negative."
        continue  # move on to next stock.

    Sharesgr: float = (SharesOut[0] / SharesOut[1]) ** (1 / (Year[0] - Year[1])) * 100 - 100
    NIgr: float = (NetIncome[0] / NetIncome[1]) ** (1 / (Year[0] - Year[1])) * 100 - 100
    EPSgr: float = (EPS[0] / EPS[1]) ** (1 / (Year[0] - Year[1])) * 100 - 100
    pdResults.loc[stock,
                  ["Newest yr history", "Oldest yr history", "EPS newest", "Comprehensive Net Income gr % pa",
                   "EPS gr % pa", "Shares out-standing", "Share gr % pa"]] = \
        [Year[0], Year[1], EPS[0], NIgr, EPSgr, SharesOut[0], Sharesgr]

    # print new and old values and growth for comprehensive net income, EPS (diluted) and shares outstanding
    print("comprehensive net income ", "${:19,.0f}".format(NetIncome[0]), "    ", "${:19,.0f}".format(NetIncome[1]),
          "    CAGR = ", "{:6.1f}%".format(NIgr))
    print("Dil. EPS adj for spl     ", "${:19,.2f}".format(EPS[0]), "    ", "${:19,.2f}".format(EPS[1]),
          "    CAGR = ", "{:6.1f}%".format(EPSgr))
    print("Shares                    ", "{:19,.0f}".format(SharesOut[0]), "     ", "{:19,.0f}".format(SharesOut[1]),
          "    CAGR = ", "{:6.1f}%".format(Sharesgr))
    print(Fore.BLACK, end="")  # resets printing to black, in case previous was red. no line feed

    if EPSgr < 0:
        print(Fore.RED, "EPS growth during past 5 years was negative.")
        print(Fore.BLACK, end="")  # resets printing to black, in case previous was red. no line feed
        pdResults.loc[stock, "Warnings if any"] = "EPS growth during past 5 years was negative."
        continue  # advance to next stock analysis

    # look up current stock price if income is positive in both oldest and newest year.
    quoteRet = get_jsonparsed_data(urlSharePrice)
    if len(quoteRet) == 0:
        print("no shareprice found for ", stock)
        pdResults[stock, "Warnings if any"] = "No share price found"
        continue

    quoteDic = dict(quoteRet[0])
    if quoteDic == {}:
        print("no shareprice found for ", stock)
        pdResults[stock, "Warnings if any"] = "No share price found"
        continue

    shPrice: float = float(quoteDic["price"])
    # estimate market cap
    mktCap: float = shPrice * SharesOut[0]
    print("price = ", "${:6.2f}".format(shPrice), "and est. market cap = ", "${:,.2f}".format(mktCap))
    pdResults.loc[stock, ["Price", "Mkt Cap"]] = [shPrice, mktCap]
    # form is ticker, price, volume

    if mktCap < minMarketCap:
        print(Fore.RED, "market cap is less than $ ", minMarketCap, " for ", stock)
        print(Fore.BLACK, end="")
        pdResults[stock, "Warnings if any"] = "Market cap is less than $1 Billion."
        continue  # continue with next stock in list

    # project out EPS and share buyer's cashflow for yrsDiscted number of  years
    # after purchase year using the EPS CAGR history
    epsProj = np.zeros(yrsDiscted + 1)
    cashflProj = np.zeros(yrsDiscted + 1)
    epsProj[0] = 0  # conservative assumption, buy shares late in year, no earnings this year
    epsProj[1] = EPS[0] * (1 + EPSgr / 100)  # next years eps is this year times growth
    for count in range(2, yrsDiscted + 1):  # from 2 to 20 or whatever yrsDiscted is
        epsProj[count] = epsProj[count - 1] * (1 + EPSgr / 100)  # grow by EPSgr every year

    # share purchaser's cashflow projection is same as EPS projection except purchase price in year 0
    cashflProj = copy.deepcopy(epsProj)  # the two items are independent after copying
    cashflProj[0] = -shPrice

    epsNPV = npf.npv(disctFactor, epsProj)
    shareIRR = npf.irr(cashflProj)
    print("npv of eps projected out ", yrsDiscted, " years from next yr at gr ", "{:3.1f}%".format(EPSgr),
          " and discounted at ", "{:3.1%}".format(disctFactor), " = ", "${:6.2f}".format(epsNPV))
    print("irr of share purchase with these EPSs and current share price = ", "{:4.2%}".format(shareIRR))
    pdResults.loc[stock, ["NPV of Future EPS", "Disct rate %", "Yrs discounted after purchase", "IRR %"]] = \
        [epsNPV, disctFactor * 100, yrsDiscted, shareIRR * 100]  # as percents

    # find iteratively the min growth needed for an NPV on buyer's cashflow breakeven with the given disct rate
    # iteration will use up to 20 steps, so put into a pdframe of 20 cols by 23 rows
    # the rows will be the purchase price, EPS growth values for the next yrsDiscted years, the trial growth on EPS,
    # the NPV at the given disct rate, and finally the slope (npv2-npv1)/(trial growth2-trial growth1)
    # i.e. slope this col vs. last col
    dfColumns: int = list(range(0, 20))
    dfRows = ["purchase price"] + list(range(1, yrsDiscted + 1)) + ["trial growth", "trial npv", "slope"]
    dfIterate = pd.DataFrame(columns=dfColumns, index=dfRows)
    dfIterate.iloc[:, :] = 0  # initialize to zero each time for new stock in stock list

    # for every col (iteration) the purchase price is the same
    dfIterate.loc["purchase price", :] = -shPrice

    # 1st column of dfIterate is cashflow as previously calculated, EPSgr, and epsNPV as prev calc
    for row in range(0, yrsDiscted + 1):  # stops at yrsDiscted
        dfIterate.iloc[row, 0] = cashflProj[row]
    dfIterate.loc["trial growth", 0] = EPSgr
    dfIterate.loc["trial npv", 0] = epsNPV

    # for 2nd iteration, stored in col 1, use 0.2 times the growth rate of col 0 to project EPS out
    # yrsDisct years beyond the initial purchase year
    dfIterate.loc['trial growth', 1] = EPSgr * 0.2
    dfIterate.loc[1, 1] = EPS[0] * (1 + .2 * EPSgr / 100)  # EPS in 1st yr after share purchase
    for row in range(2, yrsDiscted + 1):  # stops in yrsDiscted
        dfIterate.loc[row, 1] = dfIterate.loc[row - 1, 1] * (1 + 0.2 * EPSgr / 100)

    # note +1 in iloc endpoint below, because endpoint is excluded
    dfIterate.loc["trial npv", 1] = npf.npv(disctFactor, dfIterate.iloc[0:yrsDiscted + 1, 1])
    # calc slope for col 2
    fname = "min req grwth fail for " + stock + ".csv"  # print iterations here in case of failure
    if (dfIterate.loc["trial growth", 1] - dfIterate.loc["trial growth", 0]) != 0:
        dfIterate.loc["slope", 1] = (dfIterate.loc["trial npv", 1] - dfIterate.loc["trial npv", 0]) / \
                                    (dfIterate.loc["trial growth", 1] - dfIterate.loc["trial growth", 0])
    else:
        print("Slope denom. = 0. required growth not found for stock", stock)
        pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Slope denom. = 0"
        dfIterate.to_csv(fname)
        break  # on 0 slope go to next stock

    if dfIterate.loc["slope", 1] == 0:
        print("Slope = 0. Required growth not found for stock", stock)
        pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Slope = 0"
        dfIterate.to_csv(fname)
        break  # min. growth not found, go to next stock

    # with the first two cols in place can iterate to find the required growth for npv to be 0 - breakeven
    # growth
    for col in range(2, 20):  # iterate cols 2 to 19
        if dfIterate.loc["slope", col - 1] == 0:
            print("Minimum required growth could not be found for ", stock)
            pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Prev slope = 0"
            dfIterate.to_csv(fname)
            # print(dfIterate)
            break  # min. growth not found, go to next stock

        dfIterate.loc["trial growth", col] = \
            dfIterate.loc["trial growth", col - 1] - dfIterate.loc["trial npv", col - 1] / dfIterate.loc[
                "slope", col - 1]
        dfIterate.loc[1, col] = EPS[0] * \
                                (1 + dfIterate.loc["trial growth", col] / 100)  # 1st yr of earnings after purchase

        for row in range(2, yrsDiscted + 1):
            dfIterate.iloc[row, col] = dfIterate.iloc[row - 1, col] * \
                                       (1 + dfIterate.loc["trial growth", col] / 100)  # all other earning yrs

        # take the npv of the cashflow at the trial growth, note +1 in iloc because endpoint is excluded
        dfIterate.loc["trial npv", col] = npf.npv(disctFactor, dfIterate.iloc[0:yrsDiscted + 1, col])
        # calc new slope
        if (dfIterate.loc["trial growth", col] - dfIterate.loc["trial growth", col - 1]) == 0:
            print("Slope = 0. Minimum required growth could not be found for ", stock)
            pdResults.loc[stock, "Warnings if any"] = "Required growth not found. Slope = 0"
            dfIterate.to_csv(fname)
            # print(dfIterate)
            break  # slope not found, go to next stock

        dfIterate.loc["slope", col] = \
            (dfIterate.loc["trial npv", col] - dfIterate.loc["trial npv", col - 1]) / \
            (dfIterate.loc["trial growth", col] - dfIterate.loc["trial growth", col - 1])

        if (abs(dfIterate.loc["trial npv", col]) < 0.01) and (col <= 19):  # iteration has come to a successful end
            # dfIterate.to_csv(fname)
            if dfIterate.loc["trial growth", col] <= EPSgr:
                print(Fore.GREEN, end="")
            else:
                print(Fore.RED, end="")
            print("The min. required EPS growth for breakeven is    ",
                  "{:4.1f}".format(dfIterate.loc["trial growth", col]),
                  "% at a dsct rate of ", "{:4.1f}".format(100 * disctFactor), " %")
            print("The actual ", yrsHistory, " year historical comp ann EPS grwth = ", "{:4.1f}".format(EPSgr), "%")
            print(Fore.BLACK, end="")  # reset print to black
            pdResults.loc[stock, "Req gr % pa for NPV break-even"] = dfIterate.loc["trial growth", col]
            break  # no need to iterate further.

        if (abs(dfIterate.loc["trial npv", col]) >= 0.01) and (col == 19):  # iteration ended unsuccessfully
            print("Minimum required EPS growth not found.")
            pdResults.loc[stock, "Warnings if any"] = "Minimum required growth not found after 20th iteration."
            dfIterate.to_csv(fname)


# print(pdResults)

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H-%M.%f)")

fileName: str = "SEC DCF at " + str(disctFactor) + " " + listDescription + " over " + str(yrsDiscted) \
                + " yrs from " + stockList[0] + " to " + stockList[-1] + " on " + timestampStr + ".xlsx"
text2 = "Raw data provided by Financial Modeling Prep (see https://financialmodelingprep.com/developer/docs/) " \
        "and SEC/Edgar (see https://www.sec.gov/edgar/sec-api-documentation). All other data are " \
        "either user inputs or calculated by program. "

text3 = "The program is for Python programming training only, not for trading or stock advice or any other purpose."

writer = pd.ExcelWriter(fileName, engine="xlsxwriter")
pdResults.to_excel(writer, startrow=4, startcol=0, sheet_name='NPV etc. results')
worksheet = writer.sheets['NPV etc. results']
worksheet.write(0, 0, fileName)
worksheet.write(1, 0, text2)
worksheet.write(2, 0, text3)
writer.save()
print("The results have been saved to an Excel file named ", fileName,
      "\nThe file is in the same directory as the program.")
