import requests
import db
import bs4
import datetime
import json

TIMEZONE = 0


def update_from_api():
    url = "http://api.openweathermap.org/data/2.5/weather?q=novosibirsk&appid=e9c72570852dda21903080a6ab190d41"
    response = requests.get(url)
    if response.status_code != 200:
        return False
    main = response.json()['weather'][0]['main']
    if main != '':
        return main
    else:
        return False


def update_weather(context=None): # and weather forecast for pe
    url = 'https://www.nsu.ru/n/'
    session = requests.Session()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/83.0.4103.97 Safari/537.36',
        'Accept-Language': 'ru', }
    res = session.get(url=url)
    soup = bs4.BeautifulSoup(res.text, features="html.parser")
    container = soup.select('span.temp')[0].next
    try:
        temp = float(container.split('°')[0])
        res.raise_for_status()
        main = update_from_api()
    except Exception as e:
        return
    db.set_weather(temp=temp, main=main)
    update_forecast_weather()


def update_forecast_weather(context=None):
    x = '54.847250'
    y = '83.093446'
    part = 'minutely'
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={x}&lon={y}&exclude={part}&appid=e9c72570852dda21903080a6ab190d41"
    response = requests.get(url)
    if response.status_code != 200:
        print('CANT UPDATE FORECAST WEATHER!')
        return None
    db.set_forecast_weather(forecast=json.dumps(response.json()))


def __weather_to_emoji__(weather, temp, res=''):
    if weather == 'Clouds':
        res += ' ☁'
    elif weather == 'Thunderstorm':
        res += '⚡'
    elif weather == 'Drizzle':
        res += '☁'
    elif weather == 'Rain':
        res += '☔'
    elif weather == 'Snow':
        res += ' ☃'
    elif float(temp) >= 28:
        res += '🔥'
    else:
        now = datetime.datetime.now().time().hour + TIMEZONE
        if (now >= 22) or (now <= 6):
            res += ' 🌝'
        else:
            res += ' 🌞'
    return res


def get_weather():
    res = ''
    weather = db.get_weather()
    temp = weather[0]
    if temp >= 0:
        res = '+ ' + str(temp)
    else:
        res = '- ' + str(abs(temp))

    res = __weather_to_emoji__(weather=weather[1], temp=temp, res=res)
    return res


def forecast_for_pe(time, day):
    pe_hours, pe_minutes = map(int, time.split(' ')[1].split(':'))
    pe_time = datetime.datetime.combine((datetime.datetime.now() + datetime.timedelta(hours=TIMEZONE) + datetime.timedelta(days=(int(day) - (datetime.datetime.now() + datetime.timedelta(hours=TIMEZONE)).weekday())%7)).date(), datetime.time(pe_hours, pe_minutes))
    hourly_forecast = json.loads(db.get_forecast_weather())['hourly']

    min = 3600
    i = 0
    pe_forecast_hour = None
    for hour in hourly_forecast: # find forecast with min delta time from lesson time
        if (abs(datetime.datetime.fromtimestamp(hour['dt']) + datetime.timedelta(hours=TIMEZONE) - pe_time)).total_seconds() < min:
            min = (abs(datetime.datetime.fromtimestamp(hour['dt']) + datetime.timedelta(hours=TIMEZONE) - pe_time)).total_seconds()
            pe_forecast_hour = i
        i += 1
    try:
        temp = round(float(hourly_forecast[pe_forecast_hour]['temp']) - 273, 1)
        weather_type = hourly_forecast[pe_forecast_hour]['weather'][0]['main']
    except Exception as e:
        return None
    if temp > 0:
        temp = '+' + str(temp)
    res = str(temp)
    res = __weather_to_emoji__(weather_type, temp, res)
    return res


def main():
    pass
    #update_weather()
    #print(forecast_for_pe('🕙 10:50 - 10:35', 5))
    #update_forecast_weather()
    print(update_weather())


if __name__ == '__main__':
    main()


