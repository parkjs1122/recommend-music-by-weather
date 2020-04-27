import urllib.request
import re
import mysql.connector

mydb = mysql.connector.connect(
  host="172.30.1.70",
  user="project",
  passwd="비밀번호",
  database="project"
)

mycursor = mydb.cursor()

# 특정년도, 월에 대한 날씨 정보 조회
def getWeather(year, stn = "108"):
    obs = 1
    x = 24
    y = 9

    # 기상청 조회 url 설정 (python3.5)
    url = "http://www.weather.go.kr/weather/climate/past_table.jsp?stn=" + stn + "&yy=" + year + "&obs=28&x=28&y=16"
    print(url)

    # 읽기 버퍼 설정
    lines = []

    # 자료 읽기
    f = urllib.request.urlopen(url)
    r = f.read()
    f.close()

    # 한글로 디코딩함
    r2 = r.decode('euc-kr', 'ignore')

    # 엔터키 값으로 라인을 구분함
    lines = r2.split('\n')

    # <td class="align_left">평균기온:2.2℃<br />최고기온:3.7℃<br />최저기온:-0.3℃<br />평균운량:9.6<br />일강수량:0.0mm<br /></td>
    regex = '.*<td>(.*?)<\/td>'
    regex2 = '.*<td scope="row">(.*?)<\/td>'

    day = 0
    month = 1
    ok = 0
    for l in lines:
        if '<caption>신적설</caption>' in l:
            ok = 1

        if '<!-- content :End -->' in l:
            break

        if ok == 1:
            if 'scope="row"' in l:
                month = 1
                day += 1

            if day > 31:
                break

            # 정규식 검사를 한다.
            l_reg = re.match(regex, l)
            if 'td' in l and 'scope="row"' not in l:
                snow = l.replace("<td >", "").replace("</td>", "").replace("\t", "")
                if '&nbsp;' not in snow:
                    sql = "UPDATE weather SET snow = %s WHERE date = '%s'" % (snow, str(year) + str(month).zfill(2) + str(day).zfill(2))
                    # print(sql)
                    mycursor.execute(sql)
                    mydb.commit()

                month += 1

stn = 108

# 기온정보 출력: 일자, 평균기온, 최고기온, 최저기온, 평균운량, 일강수량
for year in range(2001, 2019):
    dict_month = getWeather(str(year), str(stn))
