import time
from pymongo import MongoClient
import pandas as pd
import threading
import pymongo
import numpy as np
from bs4 import BeautifulSoup as soup
from urllib.request import urlopen
from flask import Flask, make_response, jsonify,render_template
from flask_mongoengine import MongoEngine
url = "https://www.flipkart.com/search?q=iphone&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&as-pos=1&as-type=HISTORY&page=1"

urls = []
for var in range(1,10):
    url = ["https://www.flipkart.com/search?q=iphone&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&as-pos=1&as-type=HISTORY&page=%i"%(var)]
    urls.append(url[0])


def connect(ur):
    myClient = urlopen(ur)
    page_html = myClient.read()

    myClient.close()

    page_soup = soup(page_html, "html.parser")

    container = page_soup.find_all("div", {"class": "_2kHMtA"})
    return container


def dataframe(containers):
    data = {"Product_name": [], "Sale price": [], "Actual Price": [], "Rating": [], "Person Rating": [], "Offer": []}
    for i in range(0, 8):
        con = connect(containers[i])
        for container in con:
            # Product Name
            product_name = container.div.img["alt"]
            data["Product_name"].append(product_name)

            # Sale price
            sle_price = container.findAll("div", {"class": "_30jeq3 _1_WHN1"})
            s_p = sle_price[0].text
            data["Sale price"].append(s_p)

            # Actual Price
            try:
                actual_price = container.findAll("div", {"class": "_3I9_wc _27UcVY"})
                act_p = actual_price[0].text
                data["Actual Price"].append(act_p)
            except IndexError:

                data["Actual Price"].append("Same Price")

            # Rating
            try:
                rating = container.findAll("div", {"class": "_3LWZlK"})
                r = rating[0].text
                data["Rating"].append(r)
            except IndexError:
                data["Rating"].append("No Rating")

            # No of person given rating
            try:
                p_rating = container.findAll("span", {"class": "_2_R_DZ"})
                p_r = p_rating[0].text
                data["Person Rating"].append(p_r)
            except IndexError:
                data["Person Rating"].append("No Rating")

            # Offer
            try:
                offer = container.findAll("div", {"class": "_3Ay6Sb"})
                off = offer[0].text
                data["Offer"].append(off)
            except IndexError:
                data["Offer"].append("No offer this product")
    return data

def scheduling():
    dataset = dataframe(urls)
    df= pd.DataFrame(dataset)
    df["Rating"] = pd.to_numeric(df["Rating"])
    df[["No of Rating","No of Reviews"]] = df["Person Rating"].str.split("&",1,expand=True)
    df["No of Rating"] = df["No of Rating"].str.split(" ").str[0]
    df["No of Reviews"] = df["No of Reviews"].str.split(" ").str[0]
    df = df.drop(["Person Rating","No of Reviews"],axis=1)

    print(df.columns)
    from pymongo import MongoClient
    client = MongoClient('mongodb+srv://vinayak28:Vinayak28@cluster0.ln9qrat.mongodb.net/?retryWrites=true&w=majority')
    da= client.get_database('DataProg')
    db= da.DataPro

    for (row,rs) in df.iterrows():
            #print(row)
            #r = rs
            Product_Name = rs[0]
            Sale_Price = rs[1]
            Actual_Price = rs[2]
            Rating = rs[3]
            Offer = rs[4]
            n_rating = rs[5]

            d = {"Product_Name":Product_Name,"Rating":Rating,"Sale_Price":Sale_Price,
                 "Actual_Price":Actual_Price,"Offer":Offer,"No of Rating":n_rating}
            db.DataProg.insert_one(d)
    time.sleep(86400)


t= threading.Thread(target=scheduling)
t.start()


# scheduling() # Run the whole data scraping process
# time.sleep(100)


def get_database():
    from pymongo import MongoClient
    import pymongo

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb+srv://vinayak28:Vinayak28@cluster0.ln9qrat.mongodb.net/?retryWrites=true&w=majority"

    # Create a connection using MongoClient
    from pymongo import MongoClient
    client = MongoClient(CONNECTION_STRING)
    # Create the database for our example (we will use th
    return client["DataProg"]

app = Flask(__name__)

@app.route('/')
def show_home():
    return render_template("index.html")
@app.route('/data')
def show_data():

    dbname = get_database()
    ls = dbname['DataProg.DataProg']
    lsd = ls.find()
    df = pd.DataFrame(lsd)
    return render_template("myproject.html", tables=[df.to_html()], titles=df.columns.values)

@app.route('/chart')
def show_medata():
    data = get_database()
    dbname = get_database()
    ls = dbname['DataProg.DataProg']
    lsd = ls.find()
    df = pd.DataFrame(lsd)
    df1 = df[df["Product_Name"].str.contains('Midnight, 256 G', na=False)]
    df2 = df1[['Product_Name', 'Rating']]
    mydata = df2.values.tolist()
    data= mydata
    #[
    #     ("01-01-2020",1597),
    #     ("02-01-2020", 1545),
    #     ("03-01-2020", 453),
    #     ("04-01-2020", 597),
    #     ("05-01-2020", 159)
    #
    # ]
    labels= [row[0] for row in data]
    values= [row[1] for row in data]
    return render_template("graph.html", labels= labels, values=values)


if __name__ == '__main__':
    app.run()
