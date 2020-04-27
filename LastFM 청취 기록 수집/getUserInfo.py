import mysql.connector
import urllib.request
import simplejson

mydb = mysql.connector.connect(
  host="bethebest.online",
  user="project",
  passwd="비밀번호",
  database="project"
)

TOTAL_COUNT = 0

mycursor = mydb.cursor()

mycursor.execute("SELECT count(*) FROM user WHERE country is null OR country != 'Invalid'")

myresult = mycursor.fetchall()

for x in myresult:
  TOTAL_COUNT = x[0]

for i in range(0, TOTAL_COUNT, 20):

  print(i)

  mycursor = mydb.cursor()

  mycursor.execute("SELECT * FROM user WHERE country is null LIMIT %d, 20"%(i))

  myresult = mycursor.fetchall()

  for x in myresult:
    if x[2] == None:
      try:
        url_p = "http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user=%s&api_key=184c8d4c23d547bb3bca6cb47b00f4d9&format=json"%(x[1])
        response_p = urllib.request.urlopen(url_p)
        data_p = simplejson.load(response_p)

        country = data_p['user']['country']
        gender = data_p['user']['gender']
        age = data_p['user']['age']

        query = ""

        if country != 'None':
          query = "country = '%s'"%(country)

        if int(age) > 0:
          query = query + ", age = %d" % (age)

        if gender != 'n':
          query = query + ", gender = '%s'" % (gender)

        if len(query) > 0:
          mycursor = mydb.cursor()
          sql = "UPDATE user SET %s WHERE user_name = '%s'"%(query, x[1])
          #print(sql)
          mycursor.execute(sql)
          mydb.commit()
        else:
          mycursor = mydb.cursor()
          sql = "UPDATE user SET country = 'Invalid' WHERE user_name = '%s'"%(x[1])
          # print(sql)
          mycursor.execute(sql)
          mydb.commit()
      except Exception as e:
        print("Error Occured. %s"%(x[1]))
        mycursor = mydb.cursor()
        sql = "UPDATE user SET country = 'Invalid' WHERE user_name = '%s'" % (x[1])
        # print(sql)
        mycursor.execute(sql)
        mydb.commit()
