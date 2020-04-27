import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from implicit.als import AlternatingLeastSquares as wmf
from sklearn.cluster import KMeans
from implicit.approximate_als import NMSLibAlternatingLeastSquares as NMSLIB

# 설정값
TOP_K = 100 # K
NO_COMPONENT = 32
REGULARIZATION = 0.05
ALPHA = 15
NDCG_COUNT = 0
NDCG_SUM = 0

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

def ndcg_score(model, testdata, users, musics, k=100):

    global NDCG_SUM, NDCG_COUNT

    ndcg_sum = 0.0
    ndcg_count = 0

    # 배열의 row 개수를 구함
    for u in users:

        # 실제값(테스트 데이터)
        testdata_row = np.array(testdata.getrow(u).toarray()[0])
        nonzero_idx = sorted(testdata_row.nonzero()[0])

        # Descending order로 정렬된 값들의 인덱스를 구함 -> eg. [3 4 1 2]이면 [1 0 3 2] 반환
        testdata_order = np.argsort(testdata_row)[::-1][:k]
        t = [i for i in testdata_order if binary_search(i, nonzero_idx) != None]; testdata_order = sorted(t)  # 이진 탐색을 위한 정렬

        # User MF 결과값 추출
        rank = model.rank_items(u, testdata, musics)
        predicted_order = [i[0] for i in rank][:k]
        #predicted_order = top100

        # 테스트 데이터에서 0인 값은 제외시킴
        y_true = [0] * k

        # 예측이 맞으면 1로 바꿔줌
        for i in range(0, k):
            if binary_search(predicted_order[i], testdata_order) != None:
                y_true[i] = 1

        discounts_dcg = np.log2(np.arange(k) + 2)  # log_2(2 ~ K+2) 값들 배열로 저장
        dcg = np.sum(y_true / discounts_dcg)
        discounts_idcg = np.log2(np.arange(len(testdata_order)) + 2)  # log_2(2 ~ 테스트셋사이즈+2) 값들 배열로 저장
        idcg = np.sum([1] * len(testdata_order) / discounts_idcg)
        ndcg = dcg / idcg

        ndcg_sum += ndcg; ndcg_count += 1
        NDCG_SUM += ndcg; NDCG_COUNT += 1
        print("User = %d : Test data size = %d, True = %d, NDCG = %.2f, Cumulative result = %.2f"%(u, len(testdata_order), y_true.count(1), ndcg, NDCG_SUM / NDCG_COUNT))

    return ndcg_sum / ndcg_count

# 학습 데이터
train_user = []
train_music = []
train_count = []
test_user = []
test_music = []
test_count = []
ex_train_user = []
ex_train_music = []
ex_test_user = []
ex_test_music = []

print("Status : Data loading...")

listen_music_count = {}

f = open("./train.txt", "r")
lines = f.readlines()
for line in lines:
    line_separated = line.split(" ")
    if int(line_separated[2]) >= 0:
        if int(line_separated[0]) not in listen_music_count.keys():
            listen_music_count[int(line_separated[0])] = 1
        else:
            listen_music_count[int(line_separated[0])] += 1
        train_user.append(int(line_separated[0])); train_music.append(int(line_separated[1])); train_count.append(1)
f.close()

f = open("./test.txt", "r")
lines = f.readlines()
for line in lines:
    line_separated = line.split(" ")
    if int(line_separated[2]) >= 0:
        test_user.append(int(line_separated[0])); test_music.append(int(line_separated[1])); test_count.append(int(line_separated[2]))
f.close()

train = coo_matrix((train_count, (train_user, train_music))).tocsr()
test = coo_matrix((test_count, (test_user, test_music)))

ex_train_user = sorted(set(train_user))
ex_train_music = sorted(set(train_music))
ex_test_user = sorted(set(test_user))
ex_test_music = sorted(set(test_music))

print("Status : Train data loaded. CV ready.")

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

for n in range(N_CLUSTERS):
    idx = np.where(kmeans == n)[0]
    n_cluster_users = np.take(ex_train_user, idx)

    n_cluster_train_user = []; n_cluster_train_music = []; n_cluster_train_count = []
    n_cluster_test_user = []; n_cluster_test_music = []; n_cluster_test_count = []

    max_music_id = 0

    # Training data cluster 기준으로 분리
    for i in range(len(train_user)):
        idx = binary_search(train_user[i], n_cluster_users)
        if idx != None:
            n_cluster_train_user.append(train_user[i]); n_cluster_train_music.append(train_music[i]); n_cluster_train_count.append(train_count[i])
            if max_music_id < train_music[i]: max_music_id = train_music[i]

    # Test data cluster 기준으로 분리
    for i in range(len(test_user)):
        idx = binary_search(test_user[i], n_cluster_users)
        if idx != None and test_music[i] <= max_music_id:
            n_cluster_test_user.append(test_user[i]); n_cluster_test_music.append(test_music[i]); n_cluster_test_count.append(test_count[i])

    n_cluster_train = coo_matrix((n_cluster_train_count, (n_cluster_train_user, n_cluster_train_music))).tocsr()
    n_cluster_test = coo_matrix((n_cluster_test_count, (n_cluster_test_user, n_cluster_test_music)))

    n_cluster_train_user = sorted(set(n_cluster_train_user))
    n_cluster_train_music = sorted(set(n_cluster_train_music))
    n_cluster_test_user = sorted(set(n_cluster_test_user))
    n_cluster_test_music = sorted(set(n_cluster_test_music))

    model = wmf(factors=NO_COMPONENT, regularization=REGULARIZATION)
    model.fit(n_cluster_train.transpose() * ALPHA)

    ndcg_score(model, n_cluster_test, n_cluster_test_user, n_cluster_test_music, TOP_K)

    if NDCG_COUNT > 0: print("Total = %.6f"%(NDCG_SUM / NDCG_COUNT))

