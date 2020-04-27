import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from lightfm import LightFM
from lightfm.evaluation import auc_score
from scipy.sparse import coo_matrix

print("Data loading...")

# 학습 데이터
train_user = []
train_music = []
train_count = []

f = open("./music/u1.base", "r")
lines = f.readlines()
for line in lines:
    line_separated = line.split("\t")
    if int(line_separated[2]) > 0:
        train_user.append(int(line_separated[0])); train_music.append(int(line_separated[1])); train_count.append(int(line_separated[2]))
f.close()

train = coo_matrix((train_count, (train_user, train_music)))

print("Train data loaded.")

ex_train_user = list(set(train_user))
ex_train_music = list(set(train_music))

# 테스트 데이터
test_user = []
test_music = []
test_count = []

f = open("./music/u1.test", "r")
lines = f.readlines()
for line in lines:
    line_separated = line.split("\t")
    if int(line_separated[0]) in ex_train_user and int(line_separated[1]) in ex_train_music and int(line_separated[2]) > 0:
        test_user.append(int(line_separated[0])); test_music.append(int(line_separated[1])); test_count.append(int(line_separated[2]))
f.close()

test = coo_matrix((test_count, (test_user, test_music)))

print(test)

print("Test data loaded.")

alpha = 1e-05
epochs = 70
num_components = 32

for k in range(5, 21, 5):
    warp_model = LightFM(no_components=num_components,
                         loss='warp',
                         learning_schedule='adagrad',
                         max_sampled=100,
                         k=k,
                         user_alpha=alpha,
                         item_alpha=alpha)

    warp_model.fit_partial(train, epochs=10)
    warp_score = auc_score(warp_model, test, train_interactions=train).mean()

    print(warp_score)