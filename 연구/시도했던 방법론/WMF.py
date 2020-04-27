import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from implicit.als import AlternatingLeastSquares as wmf
from implicit.approximate_als import NMSLibAlternatingLeastSquares as NMSLIB

# 설정값
TOP_K = 100 # K
NO_COMPONENT = 32
REGULARIZATION = 0.05
ALPHA = 15

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

    ndcg_sum = 0.0
    ndcg_count = 0

    # 배열의 row 개수를 구함
    for u in users:
        # User MF 결과값 추출
        rank = model.rank_items(u, testdata, musics)

        # 실제값(테스트 데이터)
        testdata_row = np.array(testdata.getrow(u).toarray()[0])
        nonzero_idx = sorted(testdata_row.nonzero()[0])

        # Descending order로 정렬된 값들의 인덱스를 구함 -> eg. [3 4 1 2]이면 [1 0 3 2] 반환
        predicted_order = [i[0] for i in rank][:k]
        testdata_order = np.argsort(testdata_row)[::-1][:k]

        # 테스트 데이터에서 0인 값은 제외시킴
        t = [i for i in testdata_order if binary_search(i, nonzero_idx) != None]; testdata_order = sorted(t) # 이진 탐색을 위한 정렬
        y_true = [0] * k

        # 예측이 맞으면 1로 바꿔줌
        for i in range(0, k):
            if binary_search(predicted_order[i], testdata_order) != None: y_true[i] = 1

        discounts = np.log2(np.arange(len(y_true)) + 2) # log_2(2 ~ K+2) 값들 배열로 저장
        dcg = np.sum(y_true / discounts)
        idcg = np.sum([1] * len(y_true) / discounts)
        ndcg = dcg / idcg
        if(len(testdata_order) >= TOP_K * 0.8):
            ndcg_sum += ndcg; ndcg_count += 1
            print("User = %d : Test data size = %d, True = %d, NDCG = %.2f, Cumulative result = %.2f"%(u, len(testdata_order), y_true.count(1), ndcg, ndcg_sum / ndcg_count))

    return ndcg_sum / ndcg_count

# 학습 데이터
train_user = []
train_music = []
train_count = []
train_user_small = []
train_music_small = []
train_count_small = []
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
# 청취 음악 수가 5개 이하인 유저 분리
for user in listen_music_count.keys():
    if listen_music_count[user] <= 5:
        idx = binary_search(user, train_user)
        train_user_small.append(train_user[idx]); train_music_small.append(train_music[idx]); train_count_small.append(train_count[idx])
        train_user[idx] = 0; train_music[idx] = 0; train_count[idx] = 0
'''
train = coo_matrix((train_count, (train_user, train_music))).tocsr()
#train_small = coo_matrix((train_count_small, (train_user_small, train_music_small))).tocsr()
test = coo_matrix((test_count, (test_user, test_music)))

ex_train_user = sorted(set(train_user))
ex_train_music = sorted(set(train_music))
#del ex_train_user[0]; del ex_train_music[0]
#ex_train_user_small = sorted(set(train_user_small))
#ex_train_music_small = sorted(set(train_music_small))
ex_test_user = sorted(set(test_user))
ex_test_music = sorted(set(test_music))

print("Status : Train data loaded. CV ready.")

# WMF 모델 생성
#model = wmf(factors=NO_COMPONENT, regularization=REGULARIZATION)
#model.fit(train.transpose() * ALPHA)

# NMSLIB 모델 생성
model_nmslib = NMSLIB()
model_nmslib.fit(train.transpose() * ALPHA)

print("Status : Model trained. (No. users = %d, No. component = %d, Regularization = %.2f, Top K = %d)"%(len(ex_train_user), NO_COMPONENT, REGULARIZATION, TOP_K))

ndcg_score(model_nmslib, test, ex_test_user, ex_test_music, TOP_K)
#ndcg_score(model_nmslib, test, ex_train_user_small, ex_train_music_small, TOP_K)