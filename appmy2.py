import streamlit as st
import pandas as pd
import mysql.connector
from openai import OpenAI

st.title("학생 답안 제출 양식")
st.header("6문제의 서술형 답안을 제출하세요")

# OpenAI API 키 설정
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# MySQL 연결 설정
db_config = {
    'host': st.secrets["connections"]["mysql"]["host"],
    'user': st.secrets["connections"]["mysql"]["username"],
    'password': st.secrets["connections"]["mysql"]["password"],
    'database': st.secrets["connections"]["mysql"]["database"],
    'port': st.secrets["connections"]["mysql"]["port"]
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# 데이터 읽기 함수
def read_existing_data():
    query = "SELECT * FROM student_responses_1"
    cursor.execute(query)
    result = cursor.fetchall()
    columns = cursor.column_names
    return pd.DataFrame(result, columns=columns)

existing_data = read_existing_data()

example_answers = {
    "1": "이온이 들어 있는 수용액이 전기를 통하는 현상으로 이온이 전하를 띠고 있음을 확인할 수 있다.",
    "2": "원자핵이 띠는 양전하의 양과 전자가 띠는 음전하의 총량이 같기 때문이다.",
    "3": "중성 원자가 전자를 잃거나 얻어 전하를 띠는 입자를 의미한다.",
    "4": "양이온: 원자가 전자를 잃어 형성된 양(+)전하를 띠는 입자.",
    "5": "전자의 수는 10개이다. 산화 이온이라고 한다. 전자의 총 음(-)전하량은 –10이다. 원자가 전자 2개를 잃어 형성된 것이다. 원자핵의 양(+)전하량보다 전자의 총 (-)전하량이 크다. 중 2가지 이상 서술하면 됨.",
    "6": "가)에 전원을 연결하면 전기가 통하지 않는다. 나)에서 이온이 자유롭게 움직이고 있다. 다)에서 이온이 이동하므로 전기가 통한다. 다)에서 (-)극에는 양(+)전하를 띠는 입자가 이동한다. 다)에서 (+)극에는 음(-)전하를 띠는 입자가 이동한다. 이 고체는 물에 녹아 양이온과 음이온을 나누어진다."
}

with st.form(key="Feedback_form"):
    student_id = st.text_input("학번을 입력하세요", placeholder="예: 1학년 1반 5번 -> 10105, 1학년 1반 30번 -> 10130)")
    answer1 = st.text_area("1. 이온이 전하를 띠는 것을 어떻게 확인할 수 있는지 서술하시오.")
    answer2 = st.text_area("2. 원자의 전기적 성질이 왜 중성인지 서술하시오.")
    answer3 = st.text_area("3. 이온이란 무엇인지 서술하시오.")
    answer4 = st.text_area("4. 양이온이나 음이온 중 하나를 선택하여 이온에 대해 설명하시오.")
    answer5 = st.text_area("5. 이온식 O^(2-)에 대해 최소 2가지 이상 설명하시오.")
    answer6 = st.text_area("6. 다음 그림은 어떤 고체 물질을 물에 녹인 후 전원을 연결했을 때의 입자 변화를 모형으로 나타낸 것이다. 이 실험을 통해 알 수 있는 사실을 최소 1가지 이상 서술하시오.")

    submit_button = st.form_submit_button(label='제출하기')

    if submit_button and student_id and answer1 and answer2 and answer3 and answer4 and answer5 and answer6:
        feedbacks = []
        for i, (answer, example_answer) in enumerate(zip([answer1, answer2, answer3, answer4, answer5, answer6], 
                                                         [example_answers["1"], example_answers["2"], example_answers["3"], 
                                                          example_answers["4"], example_answers["5"], example_answers["6"]])):
            prompt = (f"학생 답안: {answer}\n\n"
                      f"예시 답안: {example_answer}\n\n"
                      f"채점 기준: 예시 답안과 비교하여, 학생 답안이 맞는지 확인하고, 틀린 부분이 있다면 어떤 부분을 공부해야 하는지 간단히 설명해 주세요. "
                      f"학생 답안이 예시 답안과 정확히 일치하지 않더라도, 내용이 맞다면 간단히 이유를 설명해 주세요."
                      f"내용 설명은 최대 200자 이내로 요약하여 제한하고, 설명할 때 교사가 학생에게 대하듯 친절하게 설명해 주세요.")

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides feedback based on given criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            feedback = response.choices[0].message.content.strip()
            feedbacks.append(feedback)

        feedback_data = pd.DataFrame(
            [
                {
                    "student_id": student_id,
                    "number1": answer1,
                    "number2": answer2,
                    "number3": answer3,
                    "number4": answer4,
                    "number5": answer5,
                    "number6": answer6,
                    "feedback1": feedbacks[0],
                    "feedback2": feedbacks[1],
                    "feedback3": feedbacks[2],
                    "feedback4": feedbacks[3],
                    "feedback5": feedbacks[4],
                    "feedback6": feedbacks[5]
                }
            ]
        )

        # 학생에게 피드백 보여주기
        st.subheader("제출한 답안에 대한 피드백:")
        for i in range(1, 7):
            st.write(f"문제 {i}: {feedbacks[i-1]}")

        # 기존 데이터에 새로운 데이터 추가
        updated_data = pd.concat([existing_data, feedback_data], ignore_index=True)

        # MySQL 데이터베이스 업데이트
        cursor.execute("DELETE FROM student_responses_1")  # 기존 데이터 삭제
        conn.commit()

        for row in updated_data.itertuples(index=False):
            cursor.execute(
                """
                INSERT INTO student_responses_1 (student_id, number1, number2, number3, number4, number5, number6, feedback1, feedback2, feedback3, feedback4, feedback5, feedback6)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                row
            )
        conn.commit()

        st.success("답안이 성공적으로 제출되었습니다!")

cursor.close()
conn.close()

# 교사용 대시보드
st.title("교사용 대시보드")

password = st.text_input("비밀번호를 입력하세요", type="password")
if password == '1234':
    st.success("비밀번호가 맞습니다. 대시보드를 확인하세요.")
    st.subheader("학생 답안 현황")

    if existing_data.empty:
        st.write("제출된 답안이 없습니다.")
    else:
        st.dataframe(existing_data)
else:
    st.error("비밀번호가 틀렸습니다.")
