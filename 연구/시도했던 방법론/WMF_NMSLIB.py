import sys
from scipy.sparse import coo_matrix
from implicit.als import AlternatingLeastSquares as wmf
from implicit.approximate_als import NMSLibAlternatingLeastSquares as NMSLIB

training_filename = sys.argv[1]
output_filename = sys.argv[2]

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
            end = mid -1

    return None

# 설정값
NO_COMPONENT = 32
REGULARIZATION = 0.05
ALPHA = 15

# 학습 데이터
train_user = []
train_music = []
train_count = []
train_user_small = []
train_music_small = []
train_count_small = []
ex_train_user = []
ex_train_music = []

listen_music_count = {}

f = open(training_filename, "r")
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

# 청취 음악 수가 5개 이하인 유저 분리
for user in listen_music_count.keys():
    if listen_music_count[user] <= 5:
        idx = binary_search(user, train_user)
        train_user_small.append(train_user[idx]); train_music_small.append(train_music[idx]); train_count_small.append(train_count[idx])
        train_user[idx] = 0; train_music[idx] = 0; train_count[idx] = 0

train = coo_matrix((train_count, (train_user, train_music))).tocsr()
train_small = coo_matrix((train_count_small, (train_user_small, train_music_small))).tocsr()

print(train_small)

ex_train_user = sorted(set(train_user))
ex_train_music = sorted(set(train_music))
ex_train_user_small = sorted(set(train_user_small))
ex_train_music_small = sorted(set(train_music_small))

# WMF 모델 생성
model = wmf(factors=NO_COMPONENT, regularization=REGULARIZATION)
model.fit(train.transpose() * ALPHA)

# NMSLIB 모델 생성
model_nmslib = NMSLIB()
model_nmslib.fit(train.transpose() * ALPHA)

item_factors = model.item_factors
user_factors = model.user_factors

f = open(output_filename, "w")

# User 출력
f.write("%d\n"%(len(ex_train_user)))
for user in ex_train_user:
    f.write("%d " % (user))
f.write("\n")

# Item 출력
f.write("%d\n"%(len(ex_train_music)))
for item in ex_train_music:
    f.write("%d " % (item))
f.write("\n")

# User factors 출력
f.write("%d %d\n"%(len(user_factors), len(user_factors[0])))
for line in user_factors:
    for element in line:
        f.write("%f "%(element))
    f.write("\n")

# Item factors 출력
f.write("%d %d\n"%(len(item_factors), len(item_factors[0])))
for line in item_factors:
    for element in line:
        f.write("%f "%(element))
    f.write("\n")

f.close()