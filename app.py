import pandas as pd 
from pathlib import Path
import plotly.express as px
import streamlit as st
import numpy as np 
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from io import BytesIO

st.set_page_config(page_title='Цифровая кафедра',
                   page_icon=":bar_chart:",
                   layout="wide")

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False
    
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #0094DA ;
    }
    span[data-baseweb="tag"] {
        background-color: #21B5FC ;
    }
    .sidebar .sidebar-content 
    {{
                width: 500px;
    }}
</style>
""", unsafe_allow_html=True)   

def to_excel(df):

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='База', index=False)
    worksheet = writer.sheets['База']
    for i, col in enumerate(df.columns):
            max_width = max(df[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(i, i, max_width)

    writer.close()
    processed_data = output.getvalue()
    return processed_data

@st.cache_data
def get_data_from_cloud(n_list=0):
    scope = ['https://spreadsheets.google.com/feeds']

    dict_cred = {
    "type": st.secrets['type'],
    "project_id": st.secrets['project_id'],
    "private_key_id": st.secrets['private_key_id'],
    "private_key": st.secrets['private_key'],
    "client_email": st.secrets['client_email'],
    "client_id": st.secrets['client_id'],
    "auth_uri": st.secrets['auth_uri'],
    "token_uri": st.secrets['token_uri'],
    "auth_provider_x509_cert_url": st.secrets['auth_provider_x509_cert_url'],
    "client_x509_cert_url": st.secrets['client_x509_cert_url']}
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(dict_cred, scope)
        
    docid = '1b1jmUTzjnt7aLLSfAftH4Z5Ss_AvkUrwdUFbaaUreuc'
    print(credentials)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(docid)

    for i, worksheet in enumerate(spreadsheet.worksheets()):
        if i == n_list:
            expected_headers = worksheet.row_values(1)
            df = pd.DataFrame(worksheet.get_all_records(expected_headers=expected_headers))
            break
        
    df['Курс'] = df['Курс'].astype('str')
    df = df.replace(['Цифровое моделирование и суперкомпьютерные технологии',
        'Методы искусственного интеллекта и предиктивная аналитика в проектах дефектоскопии',
        'Методы искусственного интеллекта в задачах обработки результатов дистанционного зондирования Земли',
        'Прикладные системы инженерных расчетов',
        'Тестовый прокторинг: Цифровое моделирование и суперкомпьютерные технологии',
        'Интеллектуальные технические системы',
        'Прикладные задачи и фреймворки машинного обучения и анализа больших данных',
        'Тестовый прокторинг: Методы искусственного интеллекта и предиктивная аналитика в проектах дефектоскопии',
        'Тестовый прокторинг: Методы искусственного интеллекта в задачах обработки результатов дистанционного зондирования Земли'],
        ['СКТ', 'ДСК', 'ДЗЗ', 'ПСИР', 'Т_СКТ', 'ИТС', 'ML', 'Т_ДСК', 'Т_ДЗЗ'])
        
    df = df.replace(['Применяет языки программирования для решения профессиональных задач',
        'Применяет принципы и основы алгоритмизации',
        'Применяет интегрированные среды разработки (IDE)',
        'Применяет математический аппарат для решения задач по оценке и разработки моделей',
        'Применяет искусственный интеллект и машинное обучение',
        'Осуществляет сбор и подготовку данных для обучения моделей искусственного интеллекта',
        'Разрабатывает программное обеспечение',
        'Использует большие данные', 'Использует 3D-моделирование',
        'Использует специальные технические программы CAD/CAM проектирования',
        'Применяет СУБД', 'Решает задачи искусственного интеллекта (ИИ)',
        'Разрабатывает и применяет методы машинного обучения (МО) для решения задач',
        'Применяет Искусственный интеллект и машинное обучение'],
        ['ЯП', 'Алгоритмы', 'IDE', 'Математика', 'ИИ', 'Сбор данных', 'ПО', 'BigData', '3D', 'CAD/CAM', 'СУБД', 'практика ИИ', 'ML', 'ИИ'])
        
    df['Результат'] = df['Результат'].apply(lambda x: str(x)[:4]).replace('-', 0).astype(int)/10**4
    df['Институт'] = df['Институт'].astype(str)
    test_ass = ['Т_ДСК', 'Т_ДЗЗ', 'Т_СКТ']
    return df.query("`Наименование курса` != @test_ass[0] & `Наименование курса` != @test_ass[1] & `Наименование курса` != @test_ass[2]")

names = ['Dmitry Sirakov', 'Maria Bulakina', 'Sergey Krylov']
usernames = ['DSSirakov', 'MBBulakina', 'SSkrylov'] 
file_path = Path(__file__).parent / "config.yaml"

with file_path.open('rb') as file:
    credentials = yaml.load(file, Loader=SafeLoader)
authenticator = stauth.Authenticate(credentials,'IT-center_dashboard', 'abcdef', cookie_expiry_days=30)

name, authentication_status, username = authenticator.login('Login', 'main')
if authentication_status == False:
    st.error('Username/password is incorrect')
if authentication_status == None:
    st.warning('Please enter your username and password')
if authentication_status:
    df = get_data_from_cloud()
    #----------------     Sidebar     ----------------#
    st.sidebar.title('Welcome to IT-Dashboard')
    st.sidebar.header('Фильтры:')
    institute = st.sidebar.multiselect(
                "Выберите институт:",
                options=df['Институт'].sort_values().unique(),
                default=df['Институт'].sort_values().unique()
    )

    programms = st.sidebar.multiselect(
                'Выберите программу:',
                options=df['Наименование курса'].sort_values().unique(),
                default=df['Наименование курса'].sort_values().unique()
            )

    course = st.sidebar.multiselect(
                'Выберите курс:',
                options=df['Курс'].sort_values().unique(),
                default=df['Курс'].sort_values().unique()
            )

    level = st.sidebar.multiselect(
                'Выберите уровень обучения:',
                options=df['Уровень обучения'].sort_values().unique(),
                default=df['Уровень обучения'].sort_values().unique()
            )
    final_assessment = st.sidebar.multiselect(
                'Состояние финального ассессмента',
                options=df[df['Этап ассесмента'] == 3]['Статус'].sort_values().unique(),
                default=['Завершено', 'Зарегистрирован']
            )
    st.sidebar.header('Справочник компетенций')
    st.sidebar.text('ЯП - Применяет языки программирования\nдля решения профессиональных задач\nАлгоритмы - Применяет принципы и основы алгоритмизации\nIDE - Применяет интегрированные среды разработки (IDE)\nМатематика - Применяет математический аппарат для решения\nзадач по оценке и разработки моделей\nИИ - Применяет искусственный интеллект и машинное обучение\nСбор данных - Осуществляет сбор и подготовку данных\nдля обучения моделей искусственного интеллекта\nПО - Разрабатывает программное обеспечение\nBigData - Использует большие данные\n3D - Использует 3D-моделирование\nCAD/CAM - Использует специальные технические\nпрограммы CAD/CAM проектирования\nСУБД - Применяет СУБД\nпрактика ИИ - Решает задачи искусственного интеллекта (ИИ)\nML - Разрабатывает и применяет методы машинного обучения (МО) для решения задач')
    assessment=3

    df_selection = df[['Слушатель', 'Институт', 'Наименование курса','Этап ассесмента', 'Статус', 'Уровень обучения', 'Курс', 'Академическая группа', 'ДПП группа', 'Телефон', 'Кол-во академических задолженностей']]\
                .query('Институт == @institute & Курс == @course & `Этап ассесмента` == @assessment & `Наименование курса` == @programms & `Уровень обучения` == @level & Статус == @final_assessment')\
                .drop_duplicates().reset_index().drop(columns=['index']) # & Наименование курса == @programms & Курс == @course
        #----------------     Header     ----------------#
    st.title(":bar_chart: Цифровая кафедра & IT-Center")
    st.text('by Shade')
    st.markdown('##')
    authenticator.logout('Logout', 'sidebar')

    total_students = int(df_selection['Слушатель'].nunique())
    total_kpi_2023 = 1350 
    total_kpi_2024 = 2400
    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Общее количество студентов")
        st.subheader(f'{total_students}')
    with right_column:
        st.subheader('Общее количество поступающих')
        st.subheader(f'Soon')

    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("KPI")
        st.subheader(f'{total_kpi_2023}')
    with right_column:
        st.subheader('KPI')
        st.subheader(f'{total_kpi_2024}')

    st.markdown("---")

            #----------------     Histogramms     ----------------#

    people_by_institute = df_selection[['Институт', 'Слушатель']].drop_duplicates().groupby('Институт').count()['Слушатель']

    fig_people_by_institute = px.bar(
                people_by_institute,
                x=people_by_institute.index,
                y='Слушатель',
                title="<b>Статистика студентов по институтам</b>",
                color_discrete_sequence=["#21B5FC"] * len(people_by_institute),
                template="plotly_white"
            )

    fig_people_by_institute.update_layout(
                xaxis=dict(tickmode='linear'),
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis = (dict(showgrid=False))
            )
            
    people_by_programms = df_selection[['Слушатель','Наименование курса', 'Этап ассесмента', 'Статус']]\
            .query('`Этап ассесмента` == @assessment & Статус == @final_assessment').drop(columns=['Этап ассесмента', 'Статус']).drop_duplicates(subset=['Слушатель'])\
            .groupby('Наименование курса').agg({'Наименование курса':'count'})

    fig_people_by_programms = px.bar(
                people_by_programms,
                x=people_by_programms.index,
                y='Наименование курса',
                title="<b>Статистика студентов по программам</b>",
                color_discrete_sequence=["#21B5FC"] * len(people_by_programms),
                template="plotly_white"
            )

    fig_people_by_programms.update_layout(
                xaxis=dict(tickmode='linear'),
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis = (dict(showgrid=False)),
                xaxis_title="Наименование курса",
                yaxis_title="Количество человек"
            )

    left_column, right_column = st.columns(2)

    with left_column:
                st.plotly_chart(fig_people_by_institute)
    with right_column:
                st.plotly_chart(fig_people_by_programms)

    status = 'Завершено'

    df_3 = df.query('`Этап ассесмента` == 3 & Статус == @status')[['Слушатель', 'Наименование компетенции', 'Результат', 'Этап ассесмента']]\
            .drop_duplicates().groupby(['Наименование компетенции', 'Этап ассесмента'], as_index=False).agg({'Результат':'mean'})
    df_2 = df.query('`Этап ассесмента` == 2 & Статус == @status')[['Слушатель', 'Наименование компетенции', 'Результат', 'Этап ассесмента']]\
            .drop_duplicates().groupby(['Наименование компетенции', 'Этап ассесмента'], as_index=False).agg({'Результат':'mean'})
    df_1 = df.query('`Этап ассесмента` == 1 & Статус == @status')[['Слушатель', 'Наименование компетенции', 'Результат', 'Этап ассесмента']]\
            .drop_duplicates().groupby(['Наименование компетенции', 'Этап ассесмента'], as_index=False).agg({'Результат':'mean'})

    df_competitions = pd.concat([df_3, df_2, df_1])

    fig = px.line_polar(df_competitions,
                                r="Результат",
                                theta="Наименование компетенции",
                                color="Этап ассесмента",
                                line_close=True,
                                color_discrete_sequence=['#20fc03', "#9e09e8", '#cf5132'],
                                template="plotly_dark", 
                                width=1200, height=600)

    fig.update_layout(
                xaxis=dict(tickmode='linear'),
                plot_bgcolor="rgba(1,1,1,1)",
                yaxis = (dict(showgrid=False))
            )


    fig.update_traces(fill='toself')

    st.markdown('##')
            #----------------     PolarBar     ----------------#
    st.subheader("Прогресс студентов по компетенциям(Пока иннополис не починит данные - она будет кривой)")
    st.plotly_chart(fig)
            #----------------     Navigation DataFrame     ----------------#
    text_input = st.text_input(
                    "Введите фамилию студента",
                    key="placeholder",
                )

    df_xlsx = to_excel(df_selection)
    if text_input:
        st.dataframe(df_selection[df_selection['Слушатель'].apply(lambda x: x.split()[0]) == text_input])
    else:
        st.dataframe(df_selection)
            
    st.download_button(label='📥 Сделать выгрузку',
                                        data=df_xlsx,
                                        file_name= 'База.xlsx')
            #----------------     HideStreamlitStyle     ----------------#
    hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
    st.markdown(hide_st_style, unsafe_allow_html=True)