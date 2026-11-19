# WalkMate

기존 Jupyter Notebook의 카카오 장소 검색, OpenStreetMap 기반 도보 경로, 개인별 보행시간 계산을 Streamlit 웹 앱으로 옮긴 프로젝트입니다.

## 실행 방법

1. Python을 설치합니다.
2. 터미널에서 프로젝트 폴더로 이동합니다.
3. 가상환경을 만들고 활성화합니다(선택).

   Windows:
   ```
   python -m venv .venv
   .venv\\Scripts\\activate
   ```

4. 라이브러리를 설치합니다.

   ```
   pip install -r requirements.txt
   ```

5. `.streamlit/secrets.example.toml`을 같은 폴더에서 `secrets.toml`로 복사한 뒤 실제 카카오 REST API 키를 입력합니다.
6. 실행합니다.

   ```
   streamlit run app.py
   ```

7. 브라우저에서 `http://localhost:8501`을 엽니다.

## API 키 보안

- 실제 `secrets.toml` 파일을 GitHub에 올리지 마세요.
- 공개 배포 시 호스팅 서비스의 Secrets 설정에 `KAKAO_REST_API_KEY`를 등록하세요.
- REST API 키는 브라우저 코드에 넣지 않고 Streamlit 서버에서만 사용합니다.

## 참고

- 카카오 Local API: 장소 키워드 검색
- OpenStreetMap 기반 routed-foot 서비스: 도보 경로
- 이동 시간은 원본 노트북의 보행 추정식 결과이며 실시간 교통·신호·경사·혼잡을 반영한 내비게이션 ETA가 아닙니다.
- 외부 무료 경로 서비스는 사용량 제한이나 일시적인 장애가 있을 수 있습니다.
