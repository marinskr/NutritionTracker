import sqlite3
import os
from typing import Dict, Optional, List, Tuple


class Database:
    def __init__(self, db_name: str = "nutrition.db"):
        db_path = os.path.join(os.path.dirname(__file__), db_name)
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """Создаёт нормализованную структуру таблиц"""
        cursor = self.conn.cursor()

        # Таблица продуктов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT NOT NULL,
            calories_per_100g REAL,
            proteins_per_100g REAL,
            fats_per_100g REAL,
            carbs_per_100g REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Таблица записей потребления
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            date DATE NOT NULL DEFAULT CURRENT_DATE,
            grams REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """)

        # Представление для дневника питания
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS food_diary AS
        SELECT 
            c.id,
            p.name,
            p.barcode,
            c.date,
            c.grams,
            ROUND(p.calories_per_100g * c.grams / 100, 1) AS calories,
            ROUND(p.proteins_per_100g * c.grams / 100, 1) AS proteins,
            ROUND(p.fats_per_100g * c.grams / 100, 1) AS fats,
            ROUND(p.carbs_per_100g * c.grams / 100, 1) AS carbs
        FROM consumption c
        JOIN products p ON c.product_id = p.id
        ORDER BY c.date DESC, c.id DESC
        """)

        self.conn.commit()

    def add_or_update_product(self, product_data: Dict) -> int:
        """Добавляет или обновляет продукт, возвращает ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO products 
        (barcode, name, calories_per_100g, proteins_per_100g, fats_per_100g, carbs_per_100g)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(barcode) DO UPDATE SET
            name = excluded.name,
            calories_per_100g = excluded.calories_per_100g,
            proteins_per_100g = excluded.proteins_per_100g,
            fats_per_100g = excluded.fats_per_100g,
            carbs_per_100g = excluded.carbs_per_100g
        RETURNING id
        """, (
            product_data.get("barcode"),
            product_data["name"],
            product_data["calories"],
            product_data["proteins"],
            product_data["fats"],
            product_data["carbs"]
        ))
        product_id = cursor.fetchone()[0]
        self.conn.commit()
        return product_id

    def add_consumption(self, product_id: int, grams: float) -> bool:
        """Добавляет запись о потреблении"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO consumption (product_id, grams)
            VALUES (?, ?)
            """, (product_id, grams))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления потребления: {e}")
            return False

    def get_food_diary(self, days: int = 30) -> List[Tuple]:
        """Возвращает дневник питания"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT * FROM food_diary
        WHERE date >= date('now', ?)
        """, (f"-{days} days",))
        return cursor.fetchall()

    def reset_database(self) -> bool:
        """Полностью очищает базу данных"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS consumption")
            cursor.execute("DROP TABLE IF EXISTS products")
            cursor.execute("DROP VIEW IF EXISTS food_diary")
            self.conn.commit()
            self._create_tables()  # Воссоздаём структуру
            return True
        except Exception as e:
            print(f"Ошибка сброса БД: {e}")
            return False

    def get_today_nutrition(self, date: str) -> dict:
        """Возвращает сумму КБЖУ за указанную дату"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT 
            COALESCE(SUM(calories), 0) as total_calories,
            COALESCE(SUM(proteins), 0) as total_proteins,
            COALESCE(SUM(fats), 0) as total_fats,
            COALESCE(SUM(carbs), 0) as total_carbs
        FROM food_diary
        WHERE date = ?
        """, (date,))

        result = cursor.fetchone()
        return {
            "total_calories": result[0],
            "total_proteins": result[1],
            "total_fats": result[2],
            "total_carbs": result[3]
        }

    def _create_tables(self):
        """Создаёт нормализованную структуру таблиц"""
        cursor = self.conn.cursor()

        # Таблица пользователей
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            activity_level REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Таблица продуктов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT NOT NULL,
            calories_per_100g REAL,
            proteins_per_100g REAL,
            fats_per_100g REAL,
            carbs_per_100g REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Таблица записей потребления
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            date DATE NOT NULL DEFAULT CURRENT_DATE,
            grams REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """)

        # Удаляем старое представление, если оно существует
        cursor.execute("DROP VIEW IF EXISTS food_diary")

        # Создаем новое представление
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS food_diary AS
        SELECT 
            c.id,
            p.name,
            p.barcode,
            c.date,
            c.grams,
            ROUND(p.calories_per_100g * c.grams / 100, 1) AS calories,
            ROUND(p.proteins_per_100g * c.grams / 100, 1) AS proteins,
            ROUND(p.fats_per_100g * c.grams / 100, 1) AS fats,
            ROUND(p.carbs_per_100g * c.grams / 100, 1) AS carbs
        FROM consumption c
        JOIN products p ON c.product_id = p.id
        ORDER BY c.date DESC, c.id DESC
        """)

        self.conn.commit()

    def save_user_settings(self, user_data: Dict) -> bool:
        """Сохраняет настройки пользователя в базу данных"""
        try:
            cursor = self.conn.cursor()
            # Удаляем старые записи (если они есть) и сохраняем новые
            cursor.execute("DELETE FROM users")
            cursor.execute("""
            INSERT INTO users 
            (weight, height, age, gender, activity_level)
            VALUES (?, ?, ?, ?, ?)
            """, (
                user_data['weight'],
                user_data['height'],
                user_data['age'],
                user_data['gender'],
                user_data['activity_level']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек пользователя: {e}")
            return False

    def get_user_settings(self) -> Optional[Dict]:
        """Получает последние сохранённые настройки пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                return {
                    'weight': result[1],
                    'height': result[2],
                    'age': result[3],
                    'gender': result[4],
                    'activity_level': result[5]
                }
            return None
        except Exception as e:
            print(f"Ошибка получения настроек пользователя: {e}")
            return None

    def reset_database(self) -> bool:
        """Полностью очищает базу данных"""
        try:
            cursor = self.conn.cursor()
            # Удаляем все таблицы и представления
            cursor.execute("DROP TABLE IF EXISTS consumption")
            cursor.execute("DROP TABLE IF EXISTS products")
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("DROP VIEW IF EXISTS food_diary")
            self.conn.commit()

            # Воссоздаём структуру
            self._create_tables()
            return True
        except Exception as e:
            print(f"Ошибка сброса БД: {e}")
            return False

    def clear_user_settings(self) -> bool:
        """Очищает все пользовательские данные"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users")
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка очистки пользовательских данных: {e}")
            return False




    def close(self):
        """Закрывает соединение с БД"""
        self.conn.close()