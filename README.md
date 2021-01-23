# SuperLabeler
대규모 이미지 레이블링에 사용하는 툴입니다.

![이미지 1096](https://user-images.githubusercontent.com/20436037/105574672-54760480-5d66-11eb-8bd4-258f300480dc.png)

* Youtube 링크
https://youtu.be/TP4-BqY_Dbw

# 개발 목적
* 개발자 혹은 대학원 생을 위한 이미지 레이블링 툴입니다. 
* 양질의 이미지 데이터 확보는 우리에게 중요한 자산으로 우리 제품의 성능을 높여주는 아군이자, 
우리의 손목을 아프게하는 주요 원인일수 있습니다. 
* 이미지 레이블링 작업을 조금 더 효율적으로 할 수 없을까, 고민 끝에 이 레이블링 툴을 개발하게 되었습니다. 
* 이 툴은 딥러닝 학습을 위한 대규모 이미지 레이블링 작업에서 반복 작업의 횟수를 줄여주어 우리의 손목과 눈을 보호해줍니다. 
* 각각의 이미지 파일 별로 학습을 위한 사각형(객체의 위치)과 속성(객체의 이름)을 부여할수 있습니다.
* 사각형을 다른 이미지로 복사가 가능하여 반복되는 작업을 방지해줍니다. (아주 중요)


# 권장 폴더 구조
권장 폴더 구조는 아래와 같습니다. 현재 Github에 샘플 폴더가 포함되어있습니다. 

1. Root (이미지 루트 폴더)
가장 상위에 위치한 루트폴더 입니다. 이곳에는 이미지들이 담겨있는 SubFolder가 속하게 됩니다.

2. SubFolder
이미지를 실제적으로 담고 있는 서브 폴더입니다. 정지 카메라로 같은 구도로 찍은 여러장의 사진이 이 폴더에 포함이 됩니다. 물론 사진들이 반드시 같은 구도로 찍혀야 할 필요는 없습니다. 
주로 SubFolder의 이름은 해당 이미지가 촬영된 장소로 네이밍합니다.
```sh
Root
├── SubFolder01
│   └── Image_SubFolder01_01.jpg
│   └── Image_SubFolder01_02.jpg
├── SubFolder02
│   └── Image_SubFolder02_01.jpg
│   └── Image_SubFolder02_02.jpg
```

# 실행 방법
* 라이브러리가 설치되어있다는 가정
* 현재 테스트를 윈도우에서만 해보았습니다. 리눅스에서 동작 확인은 추후 예정입니다.
```sh
- RUN.bat을 실행 (혹시 모를 실행 오류 확인을 위해 CMD 창을 따로 켜서 RUN.bat을 실행시켜주세요.)
- 정상적으로 실행된다면 왼쪽 상단 네모박스에 Root폴더의 경로를 입력 후 Refresh 버튼을 눌러주세요.
- 왼쪽 하단에 이미지 리스트와 폴더 리스트를 눌러보며 이미지가 제대로 읽히는지 확인합니다.
- w를 눌러 사각형을 하나 생성 후 레이블링을 해봅니다.
- 레이블링을 진행하면, 이미지와 같은 경로에 이미지와 같은 이름의 xml 파일이 생성됩니다.
- 학습 시 이 xml 파일의 내용을 바탕으로 이미지에서 어디에 객체가 위치하는지 파악하여 학습에 반영합니다.
```


# 단축키
```sh
a: 이전 이미지로
d: 다음 이미지로
z: 이전 폴더로
x: 다음 폴더로
e: 선택된 사각형(들) 삭제
c: 선택된 사각형(들) 복사
v: 선택된 사각형(들) 붙여넣기
w: 새로운 사각형 생성
f: 해당 이미지를 전경(foreground) 이미지로 설정 --> 무시
b: 해당 이미지를 배경(background) 이미지로 설정 --> 무시
r: 해당 사각형을 NG(Not Good)로 설정 --> 하위 추가 설명
: 해당 사각형을 정상(Good) 이미지로 설정 --> 하위 추가 설명
h: 특정 기능을 위한 핫키 (e.g. 선택된 사각형들의 레이블을 모두 일괄 변경 등)
space, 더블클릭: 해당 사각형의 속성을 변경 할 수 있는 창을 팝업
crtl+z: 실행 취소
crrl+a: 사각형(들) 전체 선택
```

# 추가 설명란
```sh
* NG 사각형
학습을 위한 완벽한 이미지를 찾는 것은 어려운 일입니다. 해당 이미지 속에 학습에 부적절한 이미지가 섞여있을수 있습니다. 
부적절한 이미지라함은 이게 학습에 포함된다면 인식률에 에러를 줄 것 같은 이미지를 뜻합니다. 
예를 들면 이미지에서 사람 검출을 위해서 사람을 학습 중이라고 가정합시다. 
근데 이미지에 사람이 등을 돌린채로 쭈구려 앉아있거나, 구도상의 문제로 사람의 극히 일부만 나오는 이미지가 존재합니다.
이들을 사람이라고 판단 해야할지 말지 애매한 영역이기 때문에 이를 NG 사각형이라고 칭했습니다. 
네트워크에 따라서 해당 이미지가 필요할지 말지 결정 후 학습에 포함시키거나 학습에서 제외시키기 위한 키워드입니다.

* 정상(Good) 사각형
정상 사각형은 말 그대로 인식함에 있어 분명하여 학습에 포함시키면 인식률이 향상될것 같은 사각형을 칭합니다. 
```

# 사용 분야
컴퓨터 비전이라는 분야가 워낙 넓다보니 이 툴이 유용하게 쓰일 수 있는 곳도 있고, 그렇지 않은 곳도 있습니다. 
귀하에게 이 툴이 도움이 될지 안될지 판단해볼수 있는 문진표를 작성해보았습니다.
```sh
* 도움 가능성 多
: 이미지 하나에서 여러 개의 사물 혹은 사람에 사각형 속성을 부여한다.
: 같은 구도의 이미지들이 같은 폴더에 속한다. e.g. 고정 CCTV 영상

* 도움 가능성 小
: 이미지 하나에서 여러 개의 사물 혹은 사람에 세그멘테이션으로 속성을 부여한다(이 툴은 세그멘테이션을 지원하지 않습니다.)
: 특정 이미지 하나에, 하나의 속성을 부여하는 작업을 한다. (예를 들면 이미지 분류기)
```

# 주의 사항
* 기능 구현에 목적을 둔 프로그램이라 많은 버그가 존재할 수 있습니다.



