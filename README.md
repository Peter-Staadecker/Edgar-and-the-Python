# Edgar-and-the-Python

**Abstract:**

This is a Python program that extracts selected corporate financial statement information from the SEC's (US Securities Commission) Edgar filings, as well as from other sources. It uses the data to calculate the net present value and internal rate of return for someone purchasing a company's shares today and receiving the company's earnings for a user-determined number of future years. The future earnings are estimated from the past earnings history as represented in the SEC's filings.

**Background:**

The SEC is the USA Securities and Exchange Commission. Publicly traded companies file various reports such as their annual financial statements with the SEC. The SEC makes these reports viewable online through its EDGAR portal: https://www.sec.gov/edgar/searchedgar/companysearch.html

In addition, the SEC makes APIs available for anyone wishing to access this data programmatically. The APIs are described at https://www.sec.gov/edgar/sec-api-documentation .

The SEC's APIs are free of charge but accessing the data programmatically can be daunting (more about this below). For those looking for a simpler route, the information is more easily available through simpler APIs from a number of third party providers. At time of writing, my favourite is Financial Modeling Prep. See their developer documentation at https://site.financialmodelingprep.com/developer/docs/financial-statement-free-api . They provide either paid data access, or free access with limitations such as a maximum of five years of history.

I was interested in more than five years of history, but so infrequently that I didn't want a paid subscription at Financial Modeling Prep. Instead I created this Python program to access more years of history for select items, directly from the SEC, along with selected other items from Financial Modeling Prep where less history was needed.

The program is similar in its goals to the previously posted program I called "Acronym-Symphony-in-the-Keys-of-D-C-F" but allows for more than five years of history. If five years history is sufficient I recommend using "Acronym-Symphony-in-the-Keys-of-D-C-F" as it is simpler in design and execution than "Edgar-and-the-Python" because it gets all its data from Financial Modeling Prep.

**The Goals of Edgar-and-the-Python:**

The program takes a user-defined list of ticker symbols for large US stocks & looks up the corresponding share prices, the stock split histories, and the SEC's  central index keys (CIKs) from Financial Modeling Prep (see https://financialmodelingprep.com/developer/docs/). Access to Financial Modeling Prep is available with a free API key which the user must enter into the program code. The CIK is needed in turn to access the SEC data. SEC data is organized by CIK, and not by stock ticker symbols.

The program takes EPS (earnings per share) data and earnings data (specifically comprehensive net income) from the SEC's APIs for companies' annual reports. The program adjusts the EPS in the first year of history for any subsequent stock splits in order to put the first and last year of history on an equivalent basis. The program then calculates the historic compound annual growth rate for the EPS from the first year of history to the most recent year of history. The program then calculates the internal rate of return (IRR) and net present value (NPV) for someone purchasing a single unit of the stock at the current share price and assuming the EPS growth continues at the historic rate for a user-defined number of years after the purchase. The program also calculates the minimum EPS growth needed for the NPV of the purchaser's future share earnings during the stated number of years to breakeven with the share purchase price.

This last calculation is performed iteratively in a maximum of 20 steps. If no minimmum EPS growth can be found for the NPV to break even, the iteration attempts are output to a .csv file for inspection and a warning is printed.

The user is able to alter the the ticker symbols of interest, the discount rate for the NPV, and the number of years over which the NPV and IRR are calculated. The user alters these parameters directly in the Python code. There is no interactive user interface.

In calculating NPVs and IRRs, the share purchaser's personal taxes are ignored. Terminal values for the stock are ignored. The EPS in the year of purchasea are ignored. Additional assumptions not listed here may be implicit in the code.

The program prints results both to the terminal console and to an Excel file. The file is saved in the same directory as the program. In the case of an early end to the program a partial output file is provided.

Some sections of this program were based on example code provided by Financial Modeling Prep.

**Limitations of the SEC as a Data Source**

Amongst other limitations, I note that

a) The financial reporting taxonomy used by the SEC, i.e. the financial data fields it collects from filers and how it names/defines those data fields changes from year to year. See e.g. https://www.fasb.org/jsp/FASB/Document_C/DocumentPage&cid=1176164142961 as an example of changing taxonomy.

b) The SEC provides latitude to companies as to which financial data fields they choose to file. I assume a company could choose, for instance, to report and file net income as the SEC-provided fields NetIncomeLossAttributableToParentDiluted or as NetIncomeLossAvailableToCommonStockholdersDiluted or as a number of other SEC-provided similar data fields - each with slightly different definitions.

This makes historical data collection from the SEC challenging. For instance, if one attempts to collect a history of net income for the company with ticker WEC, one finds that from 2010 to 2013 the company filed this as an SEC item labelled "NetIncomeLoss". From 2013 onwards, this item disappeared and was replaced by an item called "NetIncomeLossAvailableToCommonStockholder".

To overcome this, I used yet another net income-related measure called "ComprehensiveIncomeNetOfTax". While this does provide a more continuous history in the example of WEC and several other companies, it doesn't work in all cases. Where it fails, the program prints out a warning message.

**Important Disclaimer:**

This program was written as a Python learning exercise and and exercise in understanding the SEC API. The program is not intended for stock trading, trading advice or any other purpose. Nor is it guaranteed to be in any way error-free. Comments, corrections and suggestions are welcome.

