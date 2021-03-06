# K-means 및 날씨 데이터를 활용한 WMF 추천시스템 성능 향상
<img src="Info/info_1.png?raw=true" width="600">

## 과제 내용

### User latent factor를 K-means로 클러스터링
* WMF 추천 알고리즘에 K-means를 도입
* 유사한 유저끼리 묶어서 클러스터별로 추천을 수행함으로써 **개별 추천 정확도를 높임**

### 날씨데이터를 추천에 반영
* 날씨를 5가지로 나누어 클러스터를 생성함
* 사용자의 상황을 반영하여 **사용자 상황에 더 가까운 음악을 추천**해줌

### 시연
![시연](Info/info_2.png?raw=true)

## 구현 내용
### Last.fm 데이터 수집
* Last.fm(https://www.last.fm/)은 세계 최대 음악 청취 기록 서비스로 사용자들의 음악 청취기록을 API로 얻을 수 있음
* 약 700만 개의 한국 사용자 청취 기록을 수집

### 서버
* **ALS 연산 및 웹서버** : Ubuntu 18.04 (구글 클라우드 서버 - 35.200.43.235)
* **DB(MySQL) 서버** : Ubuntu 18.04 (자가 서버 - bethebest.online)

### 언어
* **Python** : 서버 프로그램 개발(ALS 연산)
* **MySQL** : 사용자 음악 청취 기록 데이터 저장
* **HTML / Javascript(jQuery)** : 시연 홈페이지 개발

### 활용 라이브러리
* **Implicit** : https://implicit.readthedocs.io/en/latest/als.html
* 이외 Matrix를 다루기 위한 **Numpy, Scikit** 등
