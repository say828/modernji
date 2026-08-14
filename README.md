# 모든지 (modernji)

> 세상 모든 지식을 **문제풀이 기반**으로 편찬하는 저장소.
> **모든 지(知)** 이자 **모던 지(modern 知)**. 모든 지식은 문제로 먼저 만난다.
>
> 읽기만 한 지식은 흘러가고 틀려 본 지식은 새겨진다. 근거가 되는 선행연구는
> [vault/about/왜-문제풀이인가.md](vault/about/왜-문제풀이인가.md)에 정리했다. 이 방법론으로 나중에 앱도 만든다.

🌐 [modernji.com](https://modernji.com)

## 왜 만들었나

세상이 어떻게 돌아가는지 알고 싶어서. 책을 다 살 수는 없으니, 배운 것을 내 언어로 다시 써서 여기에 남긴다. 기록하지 않은 지식은 내 것이 아니다.

## 구조

지식은 분야별 폴더로 나누고, 문서 하나는 주제 하나만 다룬다.

```
modernji/
├── philosophy/     철학 (철학과 커리큘럼 순서로 학습 중)
├── science/        과학
├── history/        역사
├── economics/      경제
├── technology/     기술
└── etc/            아직 분류 못 한 것들
```

## 기록 원칙

1. 남의 문장을 복사하지 않고 내 언어로 다시 쓴다.
2. 문서 하나에 주제 하나. 길어지면 쪼갠다.
3. 출처를 남긴다. 어디서 배웠는지 모르는 지식은 검증할 수 없다.
4. 모르는 것을 모른다고 적는 것도 기록이다.

## 사이트

이 볼트는 [modernji.com](https://modernji.com)으로 배포된다.

```bash
# 빌드 (요구: pip install markdown)
python3 scripts/build.py

# 배포 (S3 + CloudFront, AWS 프로필 modernji)
aws s3 sync dist/ s3://modernji.com/ --delete --profile modernji
aws cloudfront create-invalidation --distribution-id E3S8GZD65RELA0 --paths "/*" --profile modernji
```

`vault/`는 옵시디언으로 열어서 편집할 수 있는 마크다운 볼트다. `[[위키링크]]`가 사이트에서 그대로 연결된다.
