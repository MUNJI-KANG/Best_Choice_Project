import os
import json
from openai import OpenAI
from openai import APITimeoutError, APIError, RateLimitError
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone

class AIAnalyticsService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        # 타임아웃 설정: 30초
        self.client = OpenAI(
            api_key=api_key,
            timeout=30.0
        )
        self.model = "gpt-4o-mini"  # 비용 효율적인 모델
        self.request_timeout = 30.0  # API 요청 타임아웃
    
    def analyze_dashboard_stats(self, stats_data):
        """
        대시보드 통계 데이터를 심층 분석하여 구조화된 인사이트 생성
        """
        prompt = f"""
당신은 스포츠 시설 예약 및 커뮤니티 플랫폼의 데이터 분석 전문가입니다. 
다음 통계 데이터를 심층 분석하여 관리자에게 실행 가능한 인사이트를 제공해주세요.

## 통계 데이터
{json.dumps(stats_data, ensure_ascii=False, indent=2)}

## 분석 지침

다음 형식으로 구조화된 분석을 제공해주세요:

### 📊 핵심 요약
- 주요 지표의 현재 상태를 2-3문장으로 요약

### 🔍 주요 발견사항
1. **트렌드 분석**
   - 일별/요일별/시간대별 패턴 분석
   - 증가/감소 추세 및 그 원인 추론
   - 이전 기간 대비 변화율 해석

2. **패턴 분석**
   - 요일별 이용 패턴 (어느 요일에 가장 활발한지)
   - 시간대별 집중도 (피크 타임 분석)
   - 지역별/종목별 선호도 분석
   - 성별 분포와 활동 패턴의 상관관계

3. **문제점 식별**
   - 취소율이 높은 요일/시간대/종목
   - 참여율이 낮은 영역
   - 데이터에서 발견된 비정상적인 패턴

### 💡 개선 제안
각 문제점에 대해 구체적이고 실행 가능한 개선 방안을 제시:
- 즉시 실행 가능한 단기 개선안 (1-2주 내)
- 중장기 전략적 개선안 (1-3개월)
- 예상 효과 및 우선순위

### 📈 예측 및 기회
- 향후 1-2주간 예상되는 트렌드
- 성장 기회가 있는 영역
- 주의해야 할 리스크

### ⚠️ 즉시 조치 필요사항
긴급하게 대응해야 할 이슈가 있다면 명시

## 출력 형식
마크다운 형식을 사용하여 가독성 있게 작성해주세요.
- 제목은 ## 또는 ### 사용
- 중요 내용은 **굵게** 표시
- 리스트는 - 또는 1. 사용
- 숫자나 통계는 명확하게 표시

한국어로 답변하고, 각 섹션을 명확하게 구분해주세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 스포츠 플랫폼 데이터 분석 전문가입니다. 통계 데이터를 심층 분석하여 실용적이고 실행 가능한 인사이트를 제공합니다. 항상 구조화된 형식으로 답변합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500,
                timeout=self.request_timeout
            )
            
            return response.choices[0].message.content
        except APITimeoutError:
            return "⚠️ **요청 시간 초과**\n\nOpenAI API 응답이 30초를 초과했습니다. 잠시 후 다시 시도해주세요."
        except RateLimitError:
            return "⚠️ **API 호출 한도 초과**\n\nOpenAI API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
        except APIError as e:
            return f"⚠️ **API 오류 발생**\n\nOpenAI API 오류: {str(e)}\n\n잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"⚠️ **분석 중 오류 발생**\n\n오류 내용: {str(e)}\n\n관리자에게 문의해주세요."
    
    def analyze_reservation_patterns(self, reservation_data):
        """
        예약 패턴 심층 분석
        """
        prompt = f"""
당신은 예약 시스템 최적화 전문가입니다. 다음 예약 데이터를 심층 분석해주세요.

## 예약 데이터
{json.dumps(reservation_data, ensure_ascii=False, indent=2)}

## 분석 지침

다음 형식으로 구조화된 분석을 제공해주세요:

### 📊 예약 패턴 요약
- 전체 예약 트렌드 요약
- 평균 일일 예약 수와 변동성

### 📅 시간대별 패턴 분석
- 피크 타임 식별 (가장 예약이 많은 시간대)
- 저조한 시간대 분석
- 시간대별 취소율 패턴

### 📆 요일별 패턴 분석
- 가장 활발한 요일과 가장 저조한 요일
- 요일별 취소율 비교
- 주말 vs 평일 패턴

### 🎯 취소율 심층 분석
- 취소율이 높은 요일/시간대/종목 식별
- 취소 패턴의 원인 추론
- 취소율과 예약량의 상관관계

### 💡 최적화 제안
1. **시설 이용률 개선**
   - 저조한 시간대 활성화 방안
   - 피크 타임 분산 전략

2. **취소율 감소 방안**
   - 취소율이 높은 영역에 대한 구체적 대응책
   - 예약 정책 개선 제안

3. **수요 예측 및 대응**
   - 향후 예상 수요 패턴
   - 계절성/이벤트 대응 전략

### 📈 예측
- 다음 주 예상 예약량
- 주의해야 할 리스크

마크다운 형식으로 작성하고, 숫자와 통계를 명확히 표시해주세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 예약 시스템 최적화 전문가입니다. 데이터를 심층 분석하여 실행 가능한 최적화 방안을 제시합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500,
                timeout=self.request_timeout
            )
            
            return response.choices[0].message.content
        except APITimeoutError:
            return "⚠️ **요청 시간 초과**\n\nOpenAI API 응답이 30초를 초과했습니다. 잠시 후 다시 시도해주세요."
        except RateLimitError:
            return "⚠️ **API 호출 한도 초과**\n\nOpenAI API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
        except APIError as e:
            return f"⚠️ **API 오류 발생**\n\nOpenAI API 오류: {str(e)}\n\n잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"⚠️ **예약 패턴 분석 중 오류 발생**\n\n오류 내용: {str(e)}\n\n관리자에게 문의해주세요."
    
    def analyze_member_behavior(self, member_data):
        """
        회원 행동 심층 분석
        """
        prompt = f"""
당신은 회원 행동 분석 및 CRM 전문가입니다. 다음 회원 데이터를 심층 분석해주세요.

## 회원 데이터
{json.dumps(member_data, ensure_ascii=False, indent=2)}

## 분석 지침

다음 형식으로 구조화된 분석을 제공해주세요:

### 📊 회원 현황 요약
- 전체 회원 가입 트렌드
- 신규 가입 vs 기존 회원 비율
- 성별 분포 및 특징

### 📈 가입 패턴 분석
- 일별 가입 추이 및 패턴
- 요일별 가입 선호도
- 가입 급증/감소 시점 분석

### 👥 회원 세그먼트 분석
1. **활성도 기준 세그먼트**
   - 고활성 회원 (빈번한 이용)
   - 중활성 회원
   - 저활성 회원
   - 휴면 회원

2. **가입 시기 기준 세그먼트**
   - 신규 회원 (최근 1개월)
   - 성장 회원 (1-3개월)
   - 안정 회원 (3개월 이상)

3. **성별/연령별 특성**
   - 각 세그먼트별 행동 패턴
   - 선호하는 서비스/종목

### ⚠️ 이탈 위험 분석
- 이탈 징후가 있는 회원군 식별
- 이탈 원인 추론
- 이탈 예방 전략

### 💡 회원 활성화 전략
1. **신규 회원 유지**
   - 온보딩 개선 방안
   - 첫 이용 유도 전략

2. **저활성 회원 재활성화**
   - 재참여 유도 방법
   - 맞춤형 프로모션 제안

3. **고활성 회원 보상**
   - VIP 프로그램 제안
   - 리텐션 전략

### 📅 예측
- 향후 가입 예상 트렌드
- 주의해야 할 회원 이탈 시점

마크다운 형식으로 작성하고, 각 세그먼트에 대한 구체적인 수치와 비율을 포함해주세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 회원 행동 분석 및 CRM 전문가입니다. 데이터를 심층 분석하여 회원 세그먼트별 맞춤 전략을 제시합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500,
                timeout=self.request_timeout
            )
            
            return response.choices[0].message.content
        except APITimeoutError:
            return "⚠️ **요청 시간 초과**\n\nOpenAI API 응답이 30초를 초과했습니다. 잠시 후 다시 시도해주세요."
        except RateLimitError:
            return "⚠️ **API 호출 한도 초과**\n\nOpenAI API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
        except APIError as e:
            return f"⚠️ **API 오류 발생**\n\nOpenAI API 오류: {str(e)}\n\n잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"⚠️ **회원 행동 분석 중 오류 발생**\n\n오류 내용: {str(e)}\n\n관리자에게 문의해주세요."
    
    def detect_anomalies(self, stats_data):
        """
        이상 패턴 심층 탐지
        """
        prompt = f"""
당신은 데이터 이상 탐지 및 리스크 관리 전문가입니다. 다음 통계 데이터에서 비정상적인 패턴을 탐지해주세요.

## 통계 데이터
{json.dumps(stats_data, ensure_ascii=False, indent=2)}

## 분석 지침

다음 형식으로 구조화된 분석을 제공해주세요:

### 🚨 긴급 조치 필요 (우선순위: 높음)
- 즉시 대응이 필요한 심각한 이상 징후
- 급격한 감소/증가가 발생한 지표
- 예상치 못한 패턴 변화

각 항목에 대해:
- 발견된 이상 징후 설명
- 정상 범위 대비 편차 정도
- 가능한 원인 추론
- 권장 조치사항

### ⚠️ 주의 필요 (우선순위: 중간)
- 지속적으로 모니터링이 필요한 패턴
- 점진적 변화 추세
- 잠재적 리스크

### 📊 비정상 패턴 상세 분석
1. **통계적 이상치**
   - 평균 대비 2표준편차 이상 벗어난 값
   - 급격한 증감률 (50% 이상 변화)

2. **패턴 이상**
   - 평소와 다른 요일/시간대 분포
   - 예상과 다른 지역/종목 선호도 변화

3. **트렌드 이상**
   - 갑작스러운 트렌드 반전
   - 계절성 패턴과 다른 변화

### 💡 원인 분석
각 이상 징후에 대한 가능한 원인:
- 외부 요인 (날씨, 이벤트, 경쟁사 등)
- 내부 요인 (시스템 문제, 정책 변경 등)
- 데이터 오류 가능성

### 🎯 대응 전략
- 즉시 조치사항
- 단기 모니터링 계획
- 장기 예방 방안

마크다운 형식으로 작성하고, 우선순위와 심각도를 명확히 표시해주세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 데이터 이상 탐지 및 리스크 관리 전문가입니다. 통계적 방법론을 활용하여 이상 징후를 정확히 식별하고 우선순위를 매깁니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000,
                timeout=self.request_timeout
            )
            
            return response.choices[0].message.content
        except APITimeoutError:
            return "⚠️ **요청 시간 초과**\n\nOpenAI API 응답이 30초를 초과했습니다. 잠시 후 다시 시도해주세요."
        except RateLimitError:
            return "⚠️ **API 호출 한도 초과**\n\nOpenAI API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
        except APIError as e:
            return f"⚠️ **API 오류 발생**\n\nOpenAI API 오류: {str(e)}\n\n잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"⚠️ **이상 탐지 중 오류 발생**\n\n오류 내용: {str(e)}\n\n관리자에게 문의해주세요."
    
    def chat_analysis(self, user_message, stats_data, conversation_history=None):
        """
        사용자 질문에 대한 대화형 분석 (멀티턴 대화 지원)
        
        Args:
            user_message: 사용자 질문
            stats_data: 통계 데이터
            conversation_history: 이전 대화 히스토리 리스트 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Returns:
            AI 응답 텍스트
        """
        # 시스템 프롬프트에 통계 데이터 포함
        system_prompt = f"""당신은 스포츠 시설 예약 및 커뮤니티 플랫폼의 데이터 분석 전문가입니다.
사용자의 질문에 답변하기 위해 다음 데이터를 참고하세요.

## 통계 데이터 및 실제 DB 데이터
{json.dumps(stats_data, ensure_ascii=False, indent=2)}

## 중요 사항
- 제공된 데이터에는 개인정보(이름, 전화번호, 주소, 생년월일)가 제외되어 있습니다
- member_id, user_id(아이디), nickname, gender(성별 통계용)만 포함되어 있습니다
- 실제 예약, 모집글, 시설 데이터를 참고하여 구체적으로 답변할 수 있습니다
- 안전 통계 데이터는 실시간으로 업데이트되며, 최신 점검 정보를 반영합니다

## 역할
- 통계 데이터와 실제 DB 데이터를 기반으로 정확하고 구체적으로 답변
- 숫자와 통계를 명확히 제시
- 실제 데이터 예시를 들어 설명 (예: "최근 예약 중 가장 많은 것은...")
- 필요시 시각화나 차트 제안
- 실행 가능한 인사이트 제공
- 이전 대화 맥락을 고려하여 자연스럽게 대화

## 안전 통계 분석 가이드 (safety_stats 데이터가 있는 경우)

### 안전 등급 체계 이해
- 안전 등급은 시설의 안전 수준을 나타냅니다
- 등급이 높을수록 안전 수준이 높습니다
- 등급별 분포를 분석하여 전체적인 안전 수준을 파악하세요

### 안전 통계 분석 방법
1. **등급별 분포 분석**
   - 각 등급의 시설 수와 비율을 분석
   - 낮은 등급 시설의 비율이 높으면 개선이 필요함을 지적
   - 등급별 트렌드를 파악하여 개선 여부 확인

2. **지역별 안전 수준 비교**
   - 지역별 안전 등급 분포를 비교
   - 안전 등급이 낮은 지역을 식별하고 우선 개선 대상으로 제안
   - 지역별 특성을 고려한 분석 제공

3. **종목별 안전 특성 분석**
   - 종목별 안전 등급 분포를 분석
   - 위험도가 높은 종목을 식별
   - 종목별 안전 관리 방안 제안

4. **연도별 트렌드 분석**
   - 연도별 점검 추세를 분석하여 안전 관리 개선 여부 확인
   - 최근 몇 년간의 트렌드를 파악하여 향후 예측
   - 점검 빈도와 등급 변화를 연관지어 분석

5. **개선 제안 및 전략**
   - 낮은 등급 시설에 대한 구체적인 개선 방안 제시
   - 우선순위별 개선 계획 수립 제안
   - 예방적 안전 관리 전략 제안
   - 데이터 기반의 실행 가능한 권장사항 제공

### 안전 통계 답변 시 포함할 내용
- 등급별 분포와 비율을 명확히 제시
- 문제가 되는 등급이나 지역을 구체적으로 지적
- 개선이 필요한 시설이나 지역에 대한 우선순위 제안
- 데이터 기반의 실행 가능한 개선 방안
- 예방적 안전 관리 전략

## 답변 형식
- 마크다운 형식 사용
- 명확하고 읽기 쉬운 구조
- 필요시 리스트나 표 사용
- 중요한 숫자는 **굵게** 표시
- 실제 데이터 예시를 구체적으로 제시
- 안전 통계의 경우 등급, 지역, 종목별 상세 분석 포함

한국어로 답변해주세요."""
        
        # 메시지 구성
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 대화 히스토리 추가 (최근 10개만 유지하여 토큰 절약)
        if conversation_history:
            # 시스템 메시지 제외하고 최근 10개만
            recent_history = conversation_history[-10:]
            messages.extend(recent_history)
        
        # 현재 사용자 메시지 추가
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                timeout=self.request_timeout
            )
            
            return response.choices[0].message.content
        except APITimeoutError:
            return "⚠️ **요청 시간 초과**\n\nOpenAI API 응답이 30초를 초과했습니다. 잠시 후 다시 시도해주세요."
        except RateLimitError:
            return "⚠️ **API 호출 한도 초과**\n\nOpenAI API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
        except APIError as e:
            return f"⚠️ **API 오류 발생**\n\nOpenAI API 오류: {str(e)}\n\n잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"⚠️ **채팅 분석 중 오류 발생**\n\n오류 내용: {str(e)}\n\n관리자에게 문의해주세요."
    
    def chat_analysis_stream(self, user_message, stats_data, conversation_history=None):
        """
        스트리밍 응답을 위한 채팅 분석 (실시간 타이핑 효과)
        
        Yields:
            응답 텍스트 청크
        """
        system_prompt = f"""당신은 스포츠 시설 예약 및 커뮤니티 플랫폼의 데이터 분석 전문가입니다.
사용자의 질문에 답변하기 위해 다음 데이터를 참고하세요.

## 통계 데이터 및 실제 DB 데이터
{json.dumps(stats_data, ensure_ascii=False, indent=2)}

## 중요 사항
- 제공된 데이터에는 개인정보가 제외되어 있습니다
- 실제 예약, 모집글, 시설 데이터를 참고하여 구체적으로 답변할 수 있습니다
- 안전 통계 데이터는 실시간으로 업데이트되며, 최신 점검 정보를 반영합니다

## 안전 통계 분석 가이드 (safety_stats 데이터가 있는 경우)
- 안전 등급별 분포를 분석하여 전체적인 안전 수준 파악
- 지역별/종목별 안전 수준 비교 및 문제 지역/종목 식별
- 연도별 트렌드 분석으로 안전 관리 개선 여부 확인
- 낮은 등급 시설에 대한 구체적인 개선 방안 제시
- 우선순위별 개선 계획 및 예방적 안전 관리 전략 제안

한국어로 답변하고, 마크다운 형식을 사용해주세요."""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if conversation_history:
            recent_history = conversation_history[-10:]
            messages.extend(recent_history)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                timeout=self.request_timeout,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APITimeoutError:
            yield "⚠️ **요청 시간 초과**\n\nOpenAI API 응답이 30초를 초과했습니다."
        except RateLimitError:
            yield "⚠️ **API 호출 한도 초과**\n\nOpenAI API 호출 한도에 도달했습니다."
        except APIError as e:
            yield f"⚠️ **API 오류 발생**\n\n{str(e)}"
        except Exception as e:
            yield f"⚠️ **채팅 분석 중 오류 발생**\n\n{str(e)}"

