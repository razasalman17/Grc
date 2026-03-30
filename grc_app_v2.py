import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import os

st.set_page_config(page_title='GRC Starter Pro', layout='wide')
if 'role' not in st.session_state:
    st.session_state.role = 'Viewer'
roles = ['Viewer', 'Analyst', 'Admin']
role = st.sidebar.selectbox('Role', roles, index=roles.index(st.session_state.role))
st.session_state.role = role
DB_URL = st.secrets.get('db_url', os.getenv('DB_URL', 'sqlite:///grc.db'))
engine = create_engine(DB_URL, future=True)

@st.cache_resource
def init_db():
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE IF NOT EXISTS risks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, likelihood TEXT, impact TEXT, owner TEXT, status TEXT, created_at TEXT)'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS controls (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, risk_title TEXT, owner TEXT, frequency TEXT, status TEXT, created_at TEXT)'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS issues (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, severity TEXT, due_date TEXT, owner TEXT, status TEXT, created_at TEXT)'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS obligations (id INTEGER PRIMARY KEY AUTOINCREMENT, standard TEXT, clause TEXT, requirement TEXT, mapped_control TEXT, status TEXT, created_at TEXT)'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS evidence (id INTEGER PRIMARY KEY AUTOINCREMENT, control_title TEXT, filename TEXT, uploaded_by TEXT, uploaded_at TEXT)'))
init_db()

st.title('GRC Starter Pro')
page = st.sidebar.radio('Navigate', ['Dashboard', 'Risks', 'Controls', 'Obligations', 'Evidence', 'Issues'])
can_edit = role in ['Analyst', 'Admin']

if page == 'Dashboard':
    with engine.begin() as conn:
        risk_count = conn.execute(text('SELECT COUNT(*) FROM risks')).scalar_one()
        control_count = conn.execute(text('SELECT COUNT(*) FROM controls')).scalar_one()
        issue_count = conn.execute(text('SELECT COUNT(*) FROM issues')).scalar_one()
    c1, c2, c3 = st.columns(3)
    c1.metric('Risks', risk_count)
    c2.metric('Controls', control_count)
    c3.metric('Issues', issue_count)

elif page == 'Risks':
    if can_edit:
        with st.form('risk_form'):
            title = st.text_input('Risk title')
            description = st.text_area('Description')
            likelihood = st.selectbox('Likelihood', ['Low', 'Medium', 'High'])
            impact = st.selectbox('Impact', ['Low', 'Medium', 'High'])
            owner = st.text_input('Owner')
            status = st.selectbox('Status', ['Open', 'Mitigating', 'Accepted', 'Closed'])
            submitted = st.form_submit_button('Save risk')
        if submitted and title:
            with engine.begin() as conn:
                conn.execute(text('INSERT INTO risks (title, description, likelihood, impact, owner, status, created_at) VALUES (:title,:description,:likelihood,:impact,:owner,:status,:created_at)'), dict(title=title, description=description, likelihood=likelihood, impact=impact, owner=owner, status=status, created_at=str(date.today())))
    with engine.begin() as conn:
        df = pd.read_sql(text('SELECT * FROM risks ORDER BY id DESC'), conn)
    st.dataframe(df, use_container_width=True)

elif page == 'Controls':
    if can_edit:
        with st.form('control_form'):
            title = st.text_input('Control title')
            risk_title = st.text_input('Mapped risk')
            owner = st.text_input('Owner')
            frequency = st.selectbox('Frequency', ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annually'])
            status = st.selectbox('Status', ['Planned', 'Active', 'Retired'])
            submitted = st.form_submit_button('Save control')
        if submitted and title:
            with engine.begin() as conn:
                conn.execute(text('INSERT INTO controls (title, risk_title, owner, frequency, status, created_at) VALUES (:title,:risk_title,:owner,:frequency,:status,:created_at)'), dict(title=title, risk_title=risk_title, owner=owner, frequency=frequency, status=status, created_at=str(date.today())))
    with engine.begin() as conn:
        df = pd.read_sql(text('SELECT * FROM controls ORDER BY id DESC'), conn)
    st.dataframe(df, use_container_width=True)

elif page == 'Obligations':
    if can_edit:
        with st.form('obl_form'):
            standard = st.text_input('Standard')
            clause = st.text_input('Clause')
            requirement = st.text_area('Requirement')
            mapped_control = st.text_input('Mapped control')
            status = st.selectbox('Status', ['Mapped', 'Partial', 'Unmapped'])
            submitted = st.form_submit_button('Save obligation')
        if submitted and standard:
            with engine.begin() as conn:
                conn.execute(text('INSERT INTO obligations (standard, clause, requirement, mapped_control, status, created_at) VALUES (:standard,:clause,:requirement,:mapped_control,:status,:created_at)'), dict(standard=standard, clause=clause, requirement=requirement, mapped_control=mapped_control, status=status, created_at=str(date.today())))
    with engine.begin() as conn:
        df = pd.read_sql(text('SELECT * FROM obligations ORDER BY id DESC'), conn)
    st.dataframe(df, use_container_width=True)

elif page == 'Evidence':
    if can_edit:
        control_title = st.text_input('Control title')
        file = st.file_uploader('Upload evidence')
        if file and st.button('Save evidence'):
            save_path = Path('output') / file.name
            save_path.write_bytes(file.getbuffer())
            with engine.begin() as conn:
                conn.execute(text('INSERT INTO evidence (control_title, filename, uploaded_by, uploaded_at) VALUES (:control_title,:filename,:uploaded_by,:uploaded_at)'), dict(control_title=control_title, filename=file.name, uploaded_by=role, uploaded_at=str(date.today())))
    with engine.begin() as conn:
        df = pd.read_sql(text('SELECT * FROM evidence ORDER BY id DESC'), conn)
    st.dataframe(df, use_container_width=True)

elif page == 'Issues':
    if can_edit:
        with st.form('issue_form'):
            title = st.text_input('Issue title')
            severity = st.selectbox('Severity', ['Low', 'Medium', 'High'])
            due_date = st.date_input('Due date')
            owner = st.text_input('Owner')
            status = st.selectbox('Status', ['Open', 'In Progress', 'Resolved', 'Closed'])
            submitted = st.form_submit_button('Save issue')
        if submitted and title:
            with engine.begin() as conn:
                conn.execute(text('INSERT INTO issues (title, severity, due_date, owner, status, created_at) VALUES (:title,:severity,:due_date,:owner,:status,:created_at)'), dict(title=title, severity=severity, due_date=str(due_date), owner=owner, status=status, created_at=str(date.today())))
    with engine.begin() as conn:
        df = pd.read_sql(text('SELECT * FROM issues ORDER BY id DESC'), conn)
    st.dataframe(df, use_container_width=True)
