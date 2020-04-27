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

# 클러스터별로 처리
CLUSTER_NO_COMPONENT = [64, 32]
CLUSTER_REGULARIZATION = [0.03, 0.03]
CLUSTER_ALPHA = [50, 50]

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

def ndcg_score(rank, testdata, users, musics, k=100):

    global NDCG_SUM, NDCG_COUNT

    testdata_row = np.array(testdata.getrow(u).toarray()[0])
    nonzero_idx = sorted(testdata_row.nonzero()[0])

    testdata_order = np.argsort(testdata_row)[::-1][:k]
    t = [i for i in testdata_order if binary_search(i, nonzero_idx) != None]; testdata_order = sorted(t)

    predicted_order = [i[0] for i in rank][:k]

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

    NDCG_SUM += ndcg; NDCG_COUNT += 1
    print("User = %d : Test data size = %d, True = %d, NDCG = %.2f, Cumulative result = %.6f"%(u, len(testdata_order), y_true.count(1), ndcg, NDCG_SUM / NDCG_COUNT))

    return ndcg

# 학습 데이터
train_user = []
train_music = []
train_count = []
small_train_user = []
small_train_music = []
small_train_count = []
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
        train_user.append(int(line_separated[0])); train_music.append(int(line_separated[1])); train_count.append(int(line_separated[2]))
f.close()

f = open("./test.txt", "r")
lines = f.readlines()
for line in lines:
    line_separated = line.split(" ")
    if int(line_separated[2]) >= 0:
        test_user.append(int(line_separated[0])); test_music.append(int(line_separated[1])); test_count.append(int(line_separated[2]))
f.close()
'''
for i in range(len(train_user)):
    if listen_music_count[train_user[i]] < 4:
        small_train_user.append(train_user[i]); small_train_music.append(train_music[i]); small_train_count.append(train_count[i])
        train_user[i] = 0; train_music[i] = 0; train_count[i] = 0
'''
train = coo_matrix((train_count, (train_user, train_music))).tocsr()
test = coo_matrix((test_count, (test_user, test_music)))

ex_train_user = sorted(set(train_user))
ex_train_music = sorted(set(train_music))
ex_test_user = sorted(set(test_user))
ex_test_music = sorted(set(test_music))

print("Status : Train data loaded. CV ready.")

# ALS 모델 생성
model = wmf(factors=NO_COMPONENT, regularization=REGULARIZATION)
model.fit(train.transpose() * ALPHA)

model_item_factors = model.item_factors
model_user_factors = model.user_factors

N_CLUSTERS = 2

n_cluster_users = []
n_cluster_train_user = []
n_cluster_train_music = []
n_cluster_train_count = []
n_cluster_test_user = []
n_cluster_test_music = []
n_cluster_test_count = []

# K-Means로 클러스터링
kmeans = KMeans(n_clusters=N_CLUSTERS, n_init=1, random_state=1)
kmeans = kmeans.fit(model.user_factors[ex_train_user])
kmeans = np.array(kmeans.predict(model.user_factors[ex_train_user]))

f = open("cluster_user.txt", "w")

for n in range(N_CLUSTERS):
    idx = np.where(kmeans == n)[0]
    for i in idx:
        f.write("%d "%(i))
    f.write("\n")
    print("Cluster %d : size = %d"%(n, len(idx)))
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

    n_cluster_model = wmf(factors=NO_COMPONENT, regularization=REGULARIZATION)
    n_cluster_model.fit(n_cluster_train.transpose() * ALPHA)

    music_idx = [i for i in range(max(n_cluster_test_music))]

    for u in n_cluster_test_user:
        scores = model_item_factors.dot(model_user_factors[u])
        n_cluster_scores = n_cluster_model.item_factors.dot(n_cluster_model.user_factors[u])

        min_length = len(scores) if len(scores) < len(n_cluster_scores) else len(n_cluster_scores)

        n_cluster_scores_exist = np.divide(n_cluster_scores, n_cluster_scores)[:min_length]
        n_cluster_scores_exist = np.nan_to_num(n_cluster_scores_exist)

        scores_exist = np.divide(scores, scores)[:min_length]
        scores_exist = np.nan_to_num(scores_exist)

        divider = scores_exist + n_cluster_scores_exist

        n_cluster_scores = np.divide(scores[:min_length] + n_cluster_scores[:min_length], divider)
        n_cluster_scores = np.nan_to_num(n_cluster_scores)

        rank = sorted(zip(music_idx, n_cluster_scores), key=lambda x: -x[1])

        ndcg_score(rank, n_cluster_test, n_cluster_test_user, n_cluster_test_music, TOP_K)

    if NDCG_COUNT > 0: print("Total = %.6f"%(NDCG_SUM / NDCG_COUNT))

