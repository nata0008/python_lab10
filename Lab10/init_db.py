import psycopg2
from faker import Faker
import random

# Підключення до БД
conn = psycopg2.connect(
    dbname="hr_department",
    user="admin",
    password="secretpassword",
    host="localhost",
    port="5433"
)
conn.autocommit = True
cursor = conn.cursor()

# 1. Створення таблиць
def create_tables():
    queries = [
        "DROP TABLE IF EXISTS Виконання_проектів CASCADE;",
        "DROP TABLE IF EXISTS Проекти CASCADE;",
        "DROP TABLE IF EXISTS Співробітники CASCADE;",
        "DROP TABLE IF EXISTS Відділи CASCADE;",
        "DROP TABLE IF EXISTS Посади CASCADE;",
        
        """
        CREATE TABLE Відділи (
            Код_відділу SERIAL PRIMARY KEY,
            Назва_відділу VARCHAR(100) NOT NULL,
            Телефон VARCHAR(20) CONSTRAINT chk_dept_phone_mask CHECK (Телефон ~ '^\+380\d{9}$'),
            Номер_кімнати INT CONSTRAINT error_room_must_be_701_to_710 CHECK (Номер_кімнати BETWEEN 701 AND 710)
        );
        """,
        """
        CREATE TABLE Посади (
            Код_посади SERIAL PRIMARY KEY,
            Посада VARCHAR(100) NOT NULL,
            Оклад NUMERIC(10, 2) DEFAULT 0.00,
            Премія_відсоток NUMERIC(5, 2) DEFAULT 0.00
        );
        """,
        """
        CREATE TABLE Співробітники (
            Код_співробітника SERIAL PRIMARY KEY,
            Прізвище VARCHAR(100) NOT NULL,
            Ім_я VARCHAR(100) NOT NULL,
            По_батькові VARCHAR(100),
            Адреса TEXT,
            Телефон VARCHAR(20) CONSTRAINT chk_emp_phone_mask CHECK (Телефон ~ '^\+380\d{9}$'),
            Освіта VARCHAR(50) CONSTRAINT chk_education CHECK (Освіта IN ('спеціальна', 'середня', 'вища')),
            Код_відділу INT REFERENCES Відділи(Код_відділу) ON DELETE SET NULL,
            Код_посади INT REFERENCES Посади(Код_посади) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE Проекти (
            Номер_проекту SERIAL PRIMARY KEY,
            Назва_проекту VARCHAR(200) NOT NULL,
            Термін_виконання DATE,
            Розмір_фінансування NUMERIC(15, 2)
        );
        """,
        """
        CREATE TABLE Виконання_проектів (
            Код_виконання SERIAL PRIMARY KEY,
            Номер_проекту INT REFERENCES Проекти(Номер_проекту) ON DELETE CASCADE,
            Код_відділу INT REFERENCES Відділи(Код_відділу) ON DELETE CASCADE,
            Дата_початку DATE
        );
        """
    ]
    for q in queries:
        cursor.execute(q)
    print("Таблиці успішно створено.")

# 2. Наповнення даними
def seed_data():
    fake = Faker('uk_UA')
    
    # Відділи
    departments = [
        ('програмування', '+380991112233', 701),
        ('дизайну', '+380501112233', 705),
        ('інформаційних технологій', '+380671112233', 710)
    ]
    for d in departments:
        cursor.execute("INSERT INTO Відділи (Назва_відділу, Телефон, Номер_кімнати) VALUES (%s, %s, %s)", d)
        
    # Посади
    positions = [
        ('інженер', 1900.00, 10.0),      # Оклад < 2000 (для перевірки запитів)
        ('редактор', 1800.00, 15.0),
        ('програміст', 3500.00, 25.0)    # Оклад > 2000
    ]
    for p in positions:
        cursor.execute("INSERT INTO Посади (Посада, Оклад, Премія_відсоток) VALUES (%s, %s, %s)", p)

    # Отримання ID відділів та посад
    cursor.execute("SELECT Код_відділу FROM Відділи")
    dept_ids = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT Код_посади FROM Посади")
    pos_ids = [r[0] for r in cursor.fetchall()]

    # 17 Співробітників
    educations = ['спеціальна', 'середня', 'вища']
    for _ in range(17):
        phone = f"+380{fake.numerify('#########')}"
        cursor.execute("""
            INSERT INTO Співробітники (Прізвище, Ім_я, По_батькові, Адреса, Телефон, Освіта, Код_відділу, Код_посади) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            fake.last_name(), fake.first_name(), fake.middle_name(), fake.address().replace('\n', ' '), 
            phone, random.choice(educations), random.choice(dept_ids), random.choice(pos_ids)
        ))

    # 8 Проектів
    for _ in range(8):
        cursor.execute("""
            INSERT INTO Проекти (Назва_проекту, Термін_виконання, Розмір_фінансування) 
            VALUES (%s, %s, %s) RETURNING Номер_проекту
        """, (
            fake.catch_phrase(), fake.date_between(start_date='today', end_date='+1y'), 
            round(random.uniform(50000.0, 500000.0), 2)
        ))
    
    # Виконання проектів
    cursor.execute("SELECT Номер_проекту FROM Проекти")
    project_ids = [r[0] for r in cursor.fetchall()]
    
    for proj_id in project_ids:
        cursor.execute("""
            INSERT INTO Виконання_проектів (Номер_проекту, Код_відділу, Дата_початку) 
            VALUES (%s, %s, %s)
        """, (proj_id, random.choice(dept_ids), fake.date_between(start_date='-1y', end_date='today')))
        
    print("БД успішно заповнена фіктивними даними.")

create_tables()
seed_data()
cursor.close()
conn.close()