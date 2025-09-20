from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime
import requests
import os
import json
import psycopg2

# File paths
DATA_DIR = '/opt/airflow/data'
RAW_FILE = os.path.join(DATA_DIR, 'posts_raw.json')
TRANSFORMED_FILE = os.path.join(DATA_DIR, 'posts_transformed.json')

# Postgres connection details from environment variables
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'etl_db')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'etl_user')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'etl_pass')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))


def extract():
    url = 'https://jsonplaceholder.typicode.com/posts'
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RAW_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print(f"Extracted {len(data)} records to {RAW_FILE}")


def transform():
    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Simple transform: keep only userId <= 5, add processed_at
    transformed = []
    for r in data:
        if r.get('userId', 0) <= 5:
            r['processed_at'] = datetime.utcnow().isoformat()
            transformed.append(r)

    with open(TRANSFORMED_FILE, 'w', encoding='utf-8') as f:
        json.dump(transformed, f)

    print(f"Transformed -> {len(transformed)} records to {TRANSFORMED_FILE}")


def load():
    # Create table if not exists and insert rows
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts_raw (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            body TEXT,
            processed_at TIMESTAMP
        );
    ''')

    with open(TRANSFORMED_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)

    for r in records:
        cur.execute('''
            INSERT INTO posts_raw (id, user_id, title, body, processed_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE 
            SET user_id=EXCLUDED.user_id,
                title=EXCLUDED.title,
                body=EXCLUDED.body,
                processed_at=EXCLUDED.processed_at;
        ''', (r['id'], r['userId'], r['title'], r['body'], r['processed_at']))

    conn.commit()
    cur.close()
    conn.close()

    print(f"Loaded {len(records)} rows into posts_raw (Postgres)")


def create_dag():
    with DAG(
        'etl_dag',
        start_date=days_ago(1),
        schedule_interval='@once',
        catchup=False
    ) as dag:
        t1 = PythonOperator(task_id='extract', python_callable=extract)
        t2 = PythonOperator(task_id='transform', python_callable=transform)
        t3 = PythonOperator(task_id='load', python_callable=load)

        t1 >> t2 >> t3

        return dag


dag = create_dag()
