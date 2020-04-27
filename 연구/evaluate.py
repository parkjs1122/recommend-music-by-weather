import sys
import numpy as np

test_user = []
test_music = []
test_count = []
ex_test_user = []
ex_test_music = []


def binary_search(target, data):
    start = 0
    end = len(data) - 1

    while start <= end:
        mid = (start + end) // 2

        if data[mid] == target:
            return mid
        elif data[mid] < target:
            start = mid + 1
        else:
            end = mid - 1

    return None


def ndcg_score(recommended_set, test_set, k):
    ndcg_sum = 0.0
    ndcg_count = 0

    for u in recommended_set.keys():
        if u in test_set.keys():
            testdata_row = test_set[u]
            recommended_row = recommended_set[u]

            # 테스트 데이터에서 0인 값은 제외시킴
            y_true = [0] * k

            # 예측이 맞으면 1로 바꿔줌
            for i in range(0, k):
                if binary_search(recommended_row[i], testdata_row) != None:
                    y_true[i] = 1

            discounts_dcg = np.log2(np.arange(k) + 2)  # log_2(2 ~ K+2) 값들 배열로 저장
            dcg = np.sum(y_true / discounts_dcg)
            discounts_idcg = np.log2(np.arange(len(testdata_row)) + 2)  # log_2(2 ~ 테스트셋사이즈+2) 값들 배열로 저장
            idcg = np.sum([1] * len(testdata_row) / discounts_idcg)
            ndcg = dcg / idcg

            ndcg_sum += ndcg;
            ndcg_count += 1

    return ndcg_sum / ndcg_count

recommended_filename = sys.argv[1]
test_filename = sys.argv[2]

recommended = {};
test = {}

# 추천 파일 불러오기
f = open(recommended_filename, "r")
lines = f.readlines()
K = int(lines[0].strip())

for line in range(1, len(lines)):
    line_split = [int(i) for i in lines[line].strip().split(" ") if i.isdigit()]
    if len(line_split) > 0:
        recommended[line_split[0]] = line_split[1:]

# 테스트 파일 불러오기
f = open(test_filename, "r")
lines = f.readlines()
for line in lines:
    line_separated = line.split(" ")
    if int(line_separated[2]) >= 0:
        if int(line_separated[0]) not in test.keys():
            test[int(line_separated[0])] = [(int(line_separated[1]), int(line_separated[2]))]
        else:
            test[int(line_separated[0])].append((int(line_separated[1]), int(line_separated[2])))
f.close()

for key in test.keys():
    test[key] = sorted(test[key], key=lambda x:x[1], reverse=True)[:K]
    test[key] = sorted([i[0] for i in test[key]])

print(round(ndcg_score(recommended, test, K), 6))