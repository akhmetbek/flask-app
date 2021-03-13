from flask import Flask
import asyncio
import datetime
import requests
app = Flask(__name__)

class Ticket:
    def __init__(self, direction = (), price = 0, companyName = "", departure = datetime.datetime, arrival = datetime.datetime, level = ""):
        self.direction = direction
        self.price = price
        self.companyName = companyName
        self.departure = departure
        self.arrival = arrival
        self.level = level


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


#я пока не знаю откуда мне взять билеты и цены, парсер сайтов разрабатывать вроде не самое оптимальное решение и времени не было
async def getFlightsForDate(date = datetime.date, departureCity = "", arrivalCity = ""):
    sDate = date.strftime("%d/%m/%Y")


    jsonData = requests.get("https://api.skypicker.com/flights?fly_from={0}&fly_to={1}&date_from={2}&date_to={3}&adults=1&partner=picky").content
    #допустим этот метод возвращает список билетов в заданном направлении на определенную дату обратившись по какому то API 
    #затем с JSON формата в Ticket класс к примеру десериалищовал и в виде массива данных вернул
    return []#list of flight tickets for certain date for certain direction 



async def getDirectionalCache(dir = ()):
    date = datetime.date.today()
    flightTickets = {}
    tasks = []
    for i in range (30):
        date += datetime.timedelta(days=1)
        task = asyncio.create_task(getFlightsForDate(date, dir[0], dir[1]))
        tasks.append(task)

    tasks.reverse()

    for task in tasks:
        flightTickets[date] = await task
        date -= datetime.timedelta(days=1)
    return dir, flightTickets 

@app.route('/getFlightsCache')
async def getFlightsCache():
    tasks = []
    for dir in directions:
        task = asyncio.create_task(getDateCache(dir))
        tasks.append(task)
    
    for task in tasks:
        dir, cacheForDirection = await task
        flightsCache[dir] = cacheForDirection
    return 'cache updated'

