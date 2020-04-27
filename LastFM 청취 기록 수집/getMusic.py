import mysql.connector
import urllib.request
import simplejson

mydb = mysql.connector.connect(
  host="localhost",
  user="project",
  passwd="비밀번호",
  database="project"
)

TOTAL_COUNT = 0

mycursor = mydb.cursor()

#mycursor.execute("SELECT count(*) FROM user WHERE country is not null AND country != 'Invalid' AND country not in ('United States', 'Canada', 'Australia', 'India') AND collected is null")
mycursor.execute("SELECT count(*) FROM user WHERE country is not null AND country != 'Invalid' AND country in ('Korea, Republic of') AND collected is null")

myresult = mycursor.fetchall()

for user in myresult:
  TOTAL_COUNT = user[0]

for i in range(0, TOTAL_COUNT, 20):
  mycursor = mydb.cursor()

  #mycursor.execute("SELECT * FROM user WHERE country is not null AND country != 'Invalid' AND country not in ('United States', 'Canada', 'Australia', 'India') AND collected is null LIMIT %d, 20"%(i))
  mycursor.execute("SELECT * FROM user WHERE country is not null AND country != 'Invalid' AND country in ('Korea, Republic of') AND collected is null ORDER BY user_id DESC LIMIT %d, 20"%(i))

  myresult = mycursor.fetchall()

  for user in myresult:
      try:
        url_p = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&api_key=184c8d4c23d547bb3bca6cb47b00f4d9&format=json"%(user[1])
        response_p = urllib.request.urlopen(url_p)
        data_p = simplejson.load(response_p)

        totalPages = int(data_p['recenttracks']['@attr']['totalPages'])

        for page in range(1, totalPages + 1):
          url_u = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&api_key=184c8d4c23d547bb3bca6cb47b00f4d9&format=json&page=%d" % (user[1], page)
          response_u = urllib.request.urlopen(url_u)
          data_u = simplejson.load(response_u)

          for history in data_u['recenttracks']['track']:
            mycursor = mydb.cursor()

            mycursor.execute("SELECT music.music_id FROM music, artist WHERE music.artist_id = artist.artist_id AND artist.artist_name = \"%s\" AND music.music_title = \"%s\"" % (history['artist']['#text'].replace("\"", "'"), history['name'].replace("\"", "'")))

            music_result = mycursor.fetchone()

            if music_result is None:
              mycursor.execute(
                "SELECT artist_id FROM artist WHERE artist_name = \"%s\"" % (
                history['artist']['#text'].replace("\"", "'")))

              artist_result = mycursor.fetchone()
              if artist_result is None: # 아티스트랑 노래 정보 둘다 없는 경우
                sql = "INSERT INTO artist (artist_name) VALUES (\"%s\")" % (history['artist']['#text'].replace("\"", "'"))
                mycursor.execute(sql)

                mydb.commit()

                mycursor.execute(
                  "SELECT artist_id FROM artist WHERE artist_name = \"%s\"" % (
                    history['artist']['#text'].replace("\"", "'")))

                artist_result_re = mycursor.fetchone()

                sql = "INSERT INTO music (music_title, artist_id) VALUES (\"%s\", %d)" % (history['name'].replace("\"", "'"), artist_result_re[0])
                mycursor.execute(sql)

                mydb.commit()

                mycursor = mydb.cursor()

                mycursor.execute(
                  "SELECT music.music_id FROM music, artist WHERE music.artist_id = artist.artist_id AND artist.artist_name = \"%s\" AND music.music_title = \"%s\"" % (
                  history['artist']['#text'].replace("\"", "'"), history['name'].replace("\"", "'")))

                music_result_re = mycursor.fetchone()

                sql = "INSERT INTO history (user_id, music_id, play_time, play_time_date) VALUES (%d, %d, %s, DATE_FORMAT(FROM_UNIXTIME(%s), '%%Y%%m%%d'))" % (user[0], music_result_re[0], history['date']['uts'], history['date']['uts'])
                mycursor.execute(sql)
                mydb.commit()
              else: # 노래 정보만 없는 경우
                sql = "INSERT INTO music (music_title, artist_id) VALUES (\"%s\", %d)" % (
                history['name'].replace("\"", "'"), artist_result[0])
                mycursor.execute(sql)

                mydb.commit()

                mycursor = mydb.cursor()

                mycursor.execute(
                  "SELECT music.music_id FROM music, artist WHERE music.artist_id = artist.artist_id AND artist.artist_name = \"%s\" AND music.music_title = \"%s\"" % (
                    history['artist']['#text'].replace("\"", "'"), history['name'].replace("\"", "'")))

                music_result_re = mycursor.fetchone()

                sql = "INSERT INTO history (user_id, music_id, play_time, play_time_date) VALUES (%d, %d, %s, DATE_FORMAT(FROM_UNIXTIME(%s), '%%Y%%m%%d'))" % (
                  user[0], music_result_re[0], history['date']['uts'], history['date']['uts'])
                mycursor.execute(sql)
                mydb.commit()

            else:
              sql = "INSERT INTO history (user_id, music_id, play_time, play_time_date) VALUES (%d, %d, %s, DATE_FORMAT(FROM_UNIXTIME(%s), '%%Y%%m%%d'))" % (
                user[0], music_result[0], history['date']['uts'], history['date']['uts'])
              mycursor.execute(sql)
              mydb.commit()

            #sql = "INSERT INTO history (user_id, music_id, play_time) VALUES (%s, %s, %s)"
            #val = (history['artist']['#text'], history['name'], history['date']['uts'])
            #mycursor.execute(sql, val)
            #print()

      except Exception as e:
        print(e)
      sql = "UPDATE user SET collected = 1 WHERE user_name = '%s'" % (user[1])
      # print(sql)
      mycursor.execute(sql)
      mydb.commit()

