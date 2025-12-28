# studio-core

공통 비즈니스 로직 라이브러리 - 인증, 유틸리티, Supabase 연동

## 설치

```bash
pip install studio-core

# Streamlit 연동 시
pip install studio-core[streamlit]
```

## 사용법

### 인증 (Supabase)

```python
from studio_core.auth import SupabaseAuth

auth = SupabaseAuth()

# 회원가입
user = auth.sign_up("user@example.com", "password123")

# 로그인
session = auth.sign_in("user@example.com", "password123")

# 로그아웃
auth.sign_out()

# 현재 사용자
current_user = auth.get_current_user()
```

### Streamlit 연동

```python
from studio_core.auth.streamlit import require_auth, get_session

# 인증 필수 페이지
@require_auth
def protected_page():
    session = get_session()
    st.write(f"환영합니다, {session.user.email}")
```

## 구조

```
studio_core/
├── auth/
│   ├── __init__.py
│   ├── supabase.py      # Supabase Auth 연동
│   ├── session.py       # 세션 관리
│   └── streamlit.py     # Streamlit 헬퍼
└── utils/
    └── __init__.py
```

## 라이선스

MIT
