import numpy as np
import mysql.connector
import http.server, json
import urllib.request
from scipy.sparse import coo_matrix
from implicit.als import AlternatingLeastSquares as wmf
from xml.etree.ElementTree import parse
from urllib.parse import urlparse, quote
from sklearn.cluster import KMeans

# 설정값
TOP_K = 100 # K
NO_COMPONENT = 32
REGULARIZATION = 0.05
ALPHA = 15
NDCG_COUNT = 0
NDCG_SUM = 0

# MySQL 접속을 위한 변수 선언
mycursor = 0

def binary_search(target, data):
    start = 0
    end = len(data) - 1

    while start <= end:
        mid = (start + end) // 2

        if data[mid] == target:
            return mid # 함수를 끝내버린다.
        elif data[mid] < target:
            start = mid + 1
        else:
            end = mid -1

    return None

def printJSON(result):
    # JSON 인코딩
    jsonString = json.dumps(result)

    # 문자열 반환
    return jsonString

# HTTP 통신 처리 클래스
class Handler(http.server.BaseHTTPRequestHandler):
    """HTTP 요청을 처리하는 클래스"""

    def do_GET(self):
        """요청 메시지의 메서드가 GET 일 때 호출되어, 응답 메시지를 전송한다."""
        # 응답 메시지의 상태 코드를 전송한다
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')

        # 응답 메시지의 헤더를 전송한다
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

        # 응답 메시지의 본문을 전송한다
        query = urlparse(self.path).query
        query_components = dict(qc.split("=") for qc in query.split("&"))

        TYPE = query_components['type']

        if TYPE == "recommend":
            WEATHER = query_components['weather']
            USER = query_components['user']
            TOP_K = int(query_components['top_k'])

            mydb = mysql.connector.connect(
                host="bethebest.online",
                user="project",
                passwd="비밀번호",
                database="project"
            )
            
            # ID로 유저 검색
            sql = "SELECT user_id FROM user WHERE user_name = \"%s\"" % (USER)

            mycursor = mydb.cursor()
            mycursor.execute(sql)
            myresult = mycursor.fetchall()

            # 결과 전송을 위한 딕셔너리 선언
            result = {}
            
            if len(myresult) == 0: # ID가 존재하지 않는 경우
                result['result'] = "nouser"
            else:
                USER = myresult[0][0]

                # 필요한 변수 선언
                train_user = []
                train_music = []
                train_count = []
                ex_train_user = []
                ex_train_music = []
                sql = ""

                # 요청한 날씨별로 SQL 분기
                if WEATHER == 'hot':
                    sql = "SELECT user_id, music_id, count(*) as play_count FROM `history`, weather WHERE history.play_time_date=weather.date and weather.high_temp >= 30 group by user_id, music_id"

                elif WEATHER == 'cold':
                    sql = "SELECT user_id, music_id, count(*) as play_count FROM `history`, weather WHERE history.play_time_date=weather.date and weather.low_temp <= 10 group by user_id, music_id"

                elif WEATHER == 'rainy':
                    sql = "SELECT user_id, music_id, count(*) as play_count FROM `history`, weather WHERE history.play_time_date=weather.date and weather.rain >= 0 group by user_id, music_id"

                elif WEATHER == 'snowy':
                    sql = "SELECT user_id, music_id, count(*) as play_count FROM `history`, weather WHERE history.play_time_date=weather.date and weather.snow >= 0 group by user_id, music_id"

                elif WEATHER == 'cool':
                    sql = "SELECT user_id, music_id, count(*) as play_count FROM `history`, weather WHERE history.play_time_date=weather.date and weather.high_temp < 30 and weather.low_temp > 10 group by user_id, music_id"

                mycursor = mydb.cursor()
                mycursor.execute(sql)
                myresult = mycursor.fetchall()
                
                # 사용자와, 음악 ID, 청취횟수 데이터 저장
                for x in myresult:
                    train_user.append(int(x[0]))
                    train_music.append(int(x[1]))
                    train_count.append(int(x[2]))
                
                # 중복이 제거된 사용자와 음악 ID
                ex_train_user = sorted(set(train_user))
                ex_train_music = sorted(set(train_music))

                if binary_search(USER, ex_train_user): # 추천 요청한 날씨에 해당 유저의 청취데이터 존재하는지 확인
                    train = coo_matrix((train_count, (train_user, train_music))).tocsr()

                    print("[Status] Train data %d loaded. CV ready." % (len(myresult)))

                    # WMF 모델 생성
                    model = wmf(factors=NO_COMPONENT, regularization=REGULARIZATION)
                    model.fit(train.transpose() * ALPHA)

                    N_CLUSTERS = 2

                    n_cluster_users = []
                    n_cluster_train_user = []
                    n_cluster_train_music = []
                    n_cluster_train_count = []
                    n_cluster_test_user = []
                    n_cluster_test_music = []
                    n_cluster_test_count = []

                    # K-Means로 클러스터링
                    kmeans = KMeans(n_clusters=N_CLUSTERS)
                    kmeans = kmeans.fit(model.user_factors[ex_train_user])
                    kmeans = np.array(kmeans.predict(model.user_factors[ex_train_user]))

                    print("[Status] %d clusters created." % (N_CLUSTERS))

                    for n in range(N_CLUSTERS):
                        idx = np.where(kmeans == n)[0]
                        n_cluster_users = np.take(ex_train_user, idx)

                        n_cluster_train_user = [];
                        n_cluster_train_music = [];
                        n_cluster_train_count = []
                        n_cluster_test_user = [];
                        n_cluster_test_music = [];
                        n_cluster_test_count = []

                        max_music_id = 0

                        # Training data cluster 기준으로 분리
                        for i in range(len(train_user)):
                            idx = binary_search(train_user[i], n_cluster_users)
                            if idx != None:
                                n_cluster_train_user.append(train_user[i]);
                                n_cluster_train_music.append(train_music[i]);
                                n_cluster_train_count.append(train_count[i])
                                if max_music_id < train_music[i]: max_music_id = train_music[i]

                        n_cluster_train = coo_matrix(
                            (n_cluster_train_count, (n_cluster_train_user, n_cluster_train_music))).tocsr()

                        n_cluster_train_user = sorted(set(n_cluster_train_user))
                        n_cluster_train_music = sorted(set(n_cluster_train_music))

                        if binary_search(USER, n_cluster_train_user):
                            model = wmf(factors=NO_COMPONENT, regularization=REGULARIZATION)
                            model.fit(n_cluster_train.transpose() * ALPHA)

                            recommendations = model.recommend(USER, train.tocsr(), N=TOP_K)

                            print("[Status] Recommendation process is completed.")

                            result['result'] = "ok"
                            result['recommendations'] = {}

                            print("[Status] Requesting album arts trough ManiaDB.")

                            for i in range(len(recommendations)):
                                sql = "SELECT music_title, artist_name, img FROM music, artist WHERE music.artist_id = artist.artist_id and music_id = %d" % (recommendations[i][0])
                                mycursor = mydb.cursor()
                                mycursor.execute(sql)
                                myresult = mycursor.fetchall()

                                result['recommendations'][str(i + 1)] = {}

                                # 앨범아트 검색 - ManiaDB 사용
                                if myresult[0][2] == None: # 앨범아트 정보가 DB에 존재하지 않는 경우
                                    img_src = ""
                                    result_src = ""

                                    try:
                                        url = "http://www.maniadb.com/api/search/" + quote(
                                            myresult[0][0]) + "/?sr=song&display=30&key=ak136@naver.com&v=0.5"
                                        response_p = urllib.request.urlopen(url)
                                        tree = parse(response_p)
                                        note = tree.getroot()

                                        for parent in tree.getiterator():
                                            for child in parent:
                                                if child.tag == 'image':
                                                    img_src = child.text

                                                if child.tag.strip() == 'name':
                                                    if str(child.text).find(myresult[0][1].strip()) > -1:
                                                        result_src = img_src
                                                        break

                                    except Exception as e:
                                        print(e)

                                    if result_src != "":
                                        mycursor = mydb.cursor()
                                        sql = "UPDATE music SET img = '%s' WHERE music_id = '%d'" % (result_src, recommendations[i][0])
                                        mycursor.execute(sql)
                                        mydb.commit()

                                    result['recommendations'][str(i + 1)]['artist'] = myresult[0][1]
                                    result['recommendations'][str(i + 1)]['title'] = myresult[0][0]
                                    result['recommendations'][str(i + 1)]['img'] = result_src
                                else: # 앨범아트 정보가 DB에 존재하는 경우
                                    result['recommendations'][str(i + 1)]['artist'] = myresult[0][1]
                                    result['recommendations'][str(i + 1)]['title'] = myresult[0][0]
                                    result['recommendations'][str(i + 1)]['img'] = myresult[0][2]
                else: # 추천 요청한 날씨에 해당 유저의 청취데이터가 존재하지 않을 경우
                    result['result'] = "nodata"
            
            # JSON 전송
            print(result)
            self.wfile.write(bytes(printJSON(result), 'utf-8'))

        elif TYPE == "register":
            LASTFM_ID = query_components['lastfm_id']

if __name__ == "__main__":
    #init()

    # 요청받을 주소 (요청을 감시할 주소)
    address = ('', 8070)

    # 요청 대기하기
    listener = http.server.HTTPServer(address, Handler)
    print('Recommendation Engine Started.')
    listener.serve_forever()
