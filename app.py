from quart import Quart
import asyncio
import datetime
import requests
import json

app = Quart(__name__)

class Ticket:
    def __init__(self, direction = (), price = 0, companyName = "", departure = "", arrival = "", bookingToken = ""):
        self.direction = direction
        self.price = price
        self.companyName = companyName
        self.departure = departure
        self.arrival = arrival
        self.bookingToken = bookingToken
    
    def __str__(self):
        return '{"from":"{0}","to":"{1}","price":{2},"companyName":"{3}","departure":"{4}","arrival":{5},"bookingToken":"{6}}"'.format(self.direction[0], self.direction[1], self.price, self.companyName, self.departure, self.arrival, self.bookingToken)

def obj_dict(obj):
    return obj.__dict__

flightsCache = {}

directions = (
    ("ALA", "TSE"),
    ("TSE", "ALA"),
    ("ALA", "MOW"),
    ("MOW", "ALA"),
    ("ALA", "CIT"),
    ("CIT", "ALA"),
    ("TSE", "MOW"),
    ("MOW", "TSE"),
    ("TSE", "LED"),
    ("LED", "TSE")
    )

async def checkFlight(ticket=Ticket):
    loop = asyncio.get_event_loop()
    url = 'https://booking-api.skypicker.com/api/v0.1/check_flights?v=2&booking_token={0}&bnum=1&pnum=1&affily=picky_{{market}}&adults=1'.format(ticket.bookingToken)
    checkCounter = 0
    while checkCounter < 30 :
        response = await loop.run_in_executor(None, requests.get, url)
        dictData = json.loads(response.content)
        ticket.price = dictData["flights_price"]
        if dictData["flights_checked"] is True:
            return True
        elif dictData["flights_invalid"] is True:
            return False
        else:
            checkCounter += 1
            await asyncio.sleep(30)
    return False


@app.route("/checkFlights")
async def checkFlights():
    tasks = []
    for dir in flightsCache:
        for day in flightsCache[dir]:
            if len(flightsCache[dir][day]) > 0:
                tasks.append(asyncio.create_task(checkFlight(flightsCache[dir][day][0])))
    
    #возможно ждать придется 15 минут
    results = await asyncio.gather(*tasks)
    #можно добавить по желанию пост-фактум обработку кэша в зависимости от результатов проверки

    return str(results)
    
@app.route("/")
async def mainForDebug():
    return "dummy"#str(checkFlight("BqdiRYhZlKkOVC009Eof5nSSWzP0SXbcJXSkGbApupJ2rhu8FwsYEe_Rk3ldEalkBY1w9yPBKpL_2wOJT28TzWZiqr8ihFztPxMqerxojzwtaU-YkZkfg_iafJNIb3X7YEYraQ6hcdpIUtZXg4fv6QZr1iUm8lVcgTf9EUnG4_oODvKbJo55q-sjxTeDXlr5tnLAsIMjJJ_dlf9y_iQyhhF9CTorsyEihSYP9qY2MNRH_EcMNG8vyBTi7GFP9JTjJemVpC9STl1vepV0HXmeFw15PmHIY_sUb7FX-4K1fcl_lkv-QHoo19rNJR2QJewTVGpZ8XEr3LZGxq-YBgHrffoW7YPBP0LOJtbcczn0bfVNqKrP841E_Si7tKMHZq1e_8KskHf517e8w1Azw92BTyKC6h1KNAAVaSegTxRdBILH2lr_37u-KnIBBxIIoP-uQwgcnr1ZsrBQqHaTw1Qk5r-TKyBiPGpVf3H2FyyBtj83vp9fISueNtoV4NA9boVUfxuliRfhQp8gzC7ePodN3jiDknXIWOFg7-HTMaOfhWZVnGRkhQyrxAFUjyvM0__QInkwGDJSKB54-puvGPMS9_Y4qnAfmnuJ93bMSWbFiQElYJcQph-q1lWgktsM4XCVoF2fstvM6Bx3GaSLuh4crK-Nav8lT3chpY7dM_7UgqYh1s4TH0p-dTtP_vP46kS4kgPPw72ZXWMC1tWgngH9kmg-VF1tJg3_BqDEj8fViuD1ITggpqNYPJh9CP7PVtCEVB8hl86Tin6uuUcLj0dnA04a31GdpavmVlb1Vnll_rrPXrh12YvV0XEBiv-EfxZ0P"))

async def getFlightsForDate(date = datetime.date, departureCity = "", arrivalCity = ""):
    sDate = date.strftime("%d/%m/%Y")
    print(sDate)
    loop = asyncio.get_event_loop()
    #здесь использовал executor потому что по обычному requests.get блочит и все последовательно работало. Данный способ надо поменять на обработку через aiohttp
    try:
        response = await loop.run_in_executor(None, requests.get, "https://api.skypicker.com/flights?fly_from={0}&fly_to={1}&date_from={2}&date_to={3}&adults=1&partner=picky".format(departureCity, arrivalCity, sDate, sDate))
        response.encoding = "utf-8"
        jsonData = response.content
        structuredData = json.loads(jsonData)
        tickets = structuredData["data"]
        tickets.sort(key = lambda ticket: ticket["price"])
    except:
        print(departureCity + "-" + arrivalCity + " for "+ sDate + ": not ok")
        return []
    return   tickets[0:2]



async def getDirectionalCache(dir = ()):
    date = datetime.date.today()
    flightTickets = {}
    tasks = []
    for i in range (30):
        date += datetime.timedelta(days=1)
        task = asyncio.create_task(getFlightsForDate(date, dir[0], dir[1]))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)

    date -= datetime.timedelta(days=30)
    for result in results:
        date += datetime.timedelta(days=1)
        tickets = []
        for ticket in result:
            tickets.append(Ticket(dir, ticket["price"], ticket["airlines"][0], datetime.datetime.fromtimestamp(ticket["dTime"]).strftime("%d/%m/%Y-%H:%M"), datetime.datetime.fromtimestamp(ticket["aTime"]).strftime("%d/%m/%Y-%H:%M"), ticket["booking_token"]))
        flightTickets[date.strftime("%d/%m%Y")] = tickets
    print(dir[0] + "-" + dir[1] + ":ok")
    return dir, flightTickets 

@app.route('/getFlightsCache')
async def getFlightsCache():
    tasks = []
    for dir in directions:
        task = asyncio.create_task(getDirectionalCache(dir))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    for dir, cacheForDirection in results:
        flightsCache[dir[0] + "-" + dir[1]] = cacheForDirection
    return json.dumps(flightsCache, default=obj_dict)

if __name__ == "__main__":
    app.run()

