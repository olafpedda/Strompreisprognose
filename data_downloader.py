import urllib.request
import xml.etree.ElementTree as ET
from io import BytesIO
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
from zipfile import ZipFile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import os.path
import time
import pandas as pd
import datetime


##############################################################################################################
###############################################Strompreis#####################################################
##############################################################################################################
def get_empty(x):
    newVal = x.replace(',', ".")
    if x == "-":
        newVal = x.replace("-", "")
    return newVal


def update_power_price():
    path = sys.path[0]
    data_path = "{}\\Data".format(path)
    getNewData = True

    milliseconds_since_epoch = datetime.datetime.now().timestamp() * 1000

    if getNewData:
        print("opening URL")
        URL = "https://www.smard.de/home/downloadcenter/download_marktdaten/726#!?" \
              "downloadAttributes=%7B%22" \
              "selectedCategory%22:3,%22" \
              "selectedSubCategory%22:8,%22" \
              "selectedRegion%22:%22DE%22,%22" \
              "from%22:1538352000000,%22" \
              "to%22:{},%22" \
              "selectedFileType%22:%22CSV%22%7D".format(milliseconds_since_epoch)
        options = Options()
        options.add_argument('headless')
        options.add_experimental_option('prefs', {
            "download": {
                "default_directory": data_path
            }
        })
        driver = webdriver.Chrome("./selenium_web_driver/chromedriver.exe", options=options)  #
        driver.get(URL)
        button = driver.find_element_by_xpath(
            "//button[@name='button'][@type='button'][contains(text(), 'Datei herunterladen')]")
        print("downloading")

        button.click()

        while not [filename for filename in os.listdir(data_path) if filename.startswith("Tabellen_Daten")]:
            print("not there yet")
            time.sleep(2)
        print("finished")

        driver.quit()
    print("reading ZIP")
    for filename in os.listdir(data_path):
        if filename.startswith("Tabellen_Daten"):
            zip_filename = "{}\\{}".format(data_path, filename)
            with ZipFile(zip_filename) as zipFile:
                power_frame = pd.read_csv(zipFile.open(zipFile.namelist()[-1]), sep=';')
                power_frame['MESS_DATUM'] = power_frame['Datum'].str.cat(power_frame['Uhrzeit'], sep=" ")
                power_frame.rename(columns={"Deutschland/Luxemburg[Euro/MWh]": "Price"},
                                   inplace=True)
                power_frame = pd.DataFrame(power_frame[["Price","MESS_DATUM"]])
                power_frame["MESS_DATUM"] = pd.to_datetime(power_frame["MESS_DATUM"],format="%d.%m.%Y %H:%M")
                power_frame.set_index("MESS_DATUM", inplace=True)

                power_frame["Price"] = power_frame["Price"].apply(lambda x: get_empty(x))
                power_frame["Price"] = pd.to_numeric(power_frame["Price"])
                power_frame["Price"].interpolate(method='linear',inplace=True)
    print("finished")
    remove_path = zip_filename
    # os.remove(remove_path)
    power_frame.to_csv("Data/price.csv")
    return power_frame

    # print("downloading power prices")
    # value_frame = pd.DataFrame()
    # for year in range(16, 20):
    #     for month in range(1, 13):
    #         if (month < 10):
    #             month = "0" + str(month)
    #         url = "https://energy-charts.de/price/month_20{}_{}.json".format(year, month)
    #         json = urllib.request.urlopen(url)
    #         data = pd.read_json(json)
    #         value_series = pd.Series(data["values"].iloc[5])
    #         value_frame = value_frame.append(pd.DataFrame(value_series.values.tolist()))
    # print("Writing to powerpriceData.csv")
    # value_frame.columns = ["Date", "Price"]
    # value_frame.to_csv('Data/powerpriceData.csv', index=False)


##############################################################################################################
###############################################Wetterhistory##################################################
##############################################################################################################
def updateWeatherHistory( shortform=("TT_TU", " V_N", "SD_SO", "   F")):
    i = 0
    weather_frame = pd.DataFrame(
        pd.date_range(start=datetime.datetime(2019, 1, 1), end=datetime.datetime(2019, 1, 2), freq="H"),
        columns=["MESS_DATUM"])
    weather_frame.set_index("MESS_DATUM", inplace=True)
    for param in ("air_temperature", "cloudiness", "sun", "wind"):
        temp_frame = pd.DataFrame(columns=["MESS_DATUM", shortform[i]])
        temp_frame.set_index("MESS_DATUM", inplace=True)
        _URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/{}/recent/".format(
            param)
        r = urlopen(_URL)
        soup = bs(r.read(), features="html.parser")
        links = soup.findAll('a')[4:]
        maximum = len(links)
        for j, link in enumerate(links):
            print("\r{} :{}/{}".format(param, j + 1, maximum), sep=' ', end='', flush=True)
            _FULLURL = _URL + link.get('href')
            resp = urlopen(_FULLURL)
            zipfile = ZipFile(BytesIO(resp.read()))
            file = zipfile.namelist()[-1]
            tempdf = pd.read_csv(zipfile.open(file), sep=';', index_col="MESS_DATUM",na_values="-999")
            tempdf.index = pd.to_datetime(tempdf.index, format='%Y%m%d%H')

            temp_frame[shortform[i].strip()] = pd.concat([temp_frame, tempdf[shortform[i]]], axis=1).mean(axis=1)
        weather_frame = pd.concat([weather_frame, temp_frame], axis=1)
        i += 1
    weather_frame.drop([" V_N", "   F"], inplace=True, axis=1)
    weather_frame.columns = ['Temperature', 'Clouds', 'Sun', 'Wind']
    weather_frame.to_csv("Data/weather.csv")
    return weather_frame


##############################################################################################################
###############################################Vorhersage#####################################################
##############################################################################################################
def updateForecast(properties=["FF", "N", "SunD1", "TTT"], updateGermanCities=False, ):
    print("downloading Forecast")
    resp = urllib.request.urlopen(
        "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_S/all_stations/kml/MOSMIX_S_LATEST_240.kmz")
    print("downloaded")
    kmz = ZipFile(BytesIO(resp.read()), 'r')
    kml = kmz.open(kmz.namelist()[0], 'r').read()
    root = ET.fromstring(kml)

    namespace = {"kml": "http://www.opengis.net/kml/2.2",
                 "dwd": "https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd"}
    cities = pd.read_csv("Data/germanCities.csv")
    cities = cities["Ort"].astype(str).values

    print("reading XML")
    last_frame = pd.DataFrame()

    index_list = []
    for time_step in root.iter('{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}TimeStep'):
        index_list.append(time_step.text)
    for prop in properties:
        for placemark in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
            city = placemark.find("kml:description", namespace).text
            if city in cities:  # stadt in DE
                df = pd.DataFrame()
                forecast = placemark.find("./kml:ExtendedData/dwd:Forecast[@dwd:elementName='{}']".format(prop),
                                          namespace)
                df[city] = list(map(float, forecast[0].text.replace("-", "-999").split()))
                last_frame[prop] = df.mean(axis=1)
    last_frame["Date"] = index_list
    last_frame["Date"] = pd.to_datetime(last_frame['Date'])
    last_frame.set_index("Date", inplace=True)
    print("writing to forecast.csv")
    last_frame.to_csv("Data/forecast.csv")

    if (updateGermanCities):
        print("updating germanCities.csv")
        elemts = root[0].findall("./kml:Placemark/kml:description", namespace)
        cityList = []
        for element in elemts:
            cityList.append(element.text)
        citiesDWD = pd.DataFrame(cityList, columns=["Ort"])
        citiesDWD['Ort'] = citiesDWD["Ort"].apply(lambda x: x.upper())

        cities = pd.DataFrame(pd.read_csv("deCitiescompare.csv", delimiter=";")["Ort"], columns=["Ort"])
        cities['Ort'] = cities["Ort"].apply(lambda x: x.upper())

        mergedStuff = pd.merge(cities, citiesDWD, on=['Ort'], how='inner')
        mergedStuff = mergedStuff.drop_duplicates()
        mergedStuff.to_csv("Data/germanCities.csv", index=False)
