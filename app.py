from flask import Flask, render_template, request, flash, redirect, url_for, session
from services.api_client import OpenFoodFactsAPI
from services.database import Database
from services.calorie_calculator import CalorieCalculator
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
RESET_TOKEN = secrets.token_urlsafe(16)


def get_db_connection():
    return Database()


@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')

    # Инициализация переменных
    product = None
    today_stats = None
    daily_norms = None
    food_history = None

    try:
        # Обработка POST-запросов
        # Получаем настройки пользователя из БД при первом заходе
        if 'user_settings' not in session:
            user_settings = db.get_user_settings()
            if user_settings:
                session['user_settings'] = user_settings
        if request.method == "POST":
            if "search_product" in request.form:
                barcode = request.form.get("barcode")
                product = OpenFoodFactsAPI.get_product_by_barcode(barcode)

            elif "save_entry" in request.form:
                try:
                    product_data = {
                        "name": request.form.get("name"),
                        "barcode": request.form.get("barcode"),
                        "calories": float(request.form.get("calories")),
                        "proteins": float(request.form.get("proteins")),
                        "fats": float(request.form.get("fats")),
                        "carbs": float(request.form.get("carbs"))
                    }

                    grams = float(request.form.get("grams", 100))
                    product_id = db.add_or_update_product(product_data)

                    if db.add_consumption(product_id, grams):
                        flash("Запись успешно добавлена в дневник!", "success")

                except Exception as e:
                    flash(f"Ошибка: {str(e)}", "danger")

        # Получение данных для отображения
        today_stats = db.get_today_nutrition(today)
        food_history = db.get_food_diary()

        # Расчет дневных норм если есть данные пользователя
        if 'user_settings' in session:
            try:
                settings = session['user_settings']
                calories = CalorieCalculator.calculate_daily_calories(
                    weight=settings['weight'],
                    height=settings['height'],
                    age=settings['age'],
                    gender=settings['gender'],
                    activity_level=settings['activity_level']
                )
                daily_norms = CalorieCalculator.get_macronutrients(calories)
                daily_norms['calories'] = calories  # Добавляем калории в нормы
            except Exception as e:
                flash(f"Ошибка расчета норм: {str(e)}", "warning")

    except Exception as e:
        flash(f"Ошибка базы данных: {str(e)}", "danger")
    finally:
        db.close()

    return render_template(
        "index.html",
        product=product,
        food_history=food_history,
        today_stats=today_stats,
        daily_norms=daily_norms,
        reset_token=RESET_TOKEN
    )


@app.route("/save-settings", methods=["POST"])
def save_settings():
    db = get_db_connection()
    try:
        user_data = {
            'weight': float(request.form.get('weight')),
            'height': float(request.form.get('height')),
            'age': int(request.form.get('age')),
            'gender': request.form.get('gender'),
            'activity_level': float(request.form.get('activity_level'))
        }

        # Сохраняем в базу данных
        if db.save_user_settings(user_data):
            # Также сохраняем в сессию для удобства
            session['user_settings'] = user_data
            flash("Настройки успешно сохранены", "success")
        else:
            flash("Ошибка сохранения настроек", "danger")

    except Exception as e:
        flash(f"Ошибка сохранения настроек: {str(e)}", "danger")
    finally:
        db.close()
    return redirect(url_for("index"))


@app.route("/reset-db", methods=["POST"])
def reset_db():
    if request.method == "POST" and request.form.get("token") == RESET_TOKEN:
        db = get_db_connection()
        try:
            if db.reset_database():
                flash("Все данные успешно удалены", "success")
            else:
                flash("Ошибка при очистке базы данных", "danger")
        except Exception as e:
            flash(f"Ошибка: {str(e)}", "danger")
        finally:
            db.close()
    else:
        flash("Неверный запрос на очистку", "danger")
    return redirect(url_for("index"))

@app.route("/clear-settings", methods=["POST"])
def clear_settings():
    db = get_db_connection()
    try:
        if db.clear_user_settings():
            # Удаляем из сессии тоже
            if 'user_settings' in session:
                session.pop('user_settings')
            flash("Пользовательские данные успешно очищены", "success")
        else:
            flash("Ошибка при очистке пользовательских данных", "danger")
    except Exception as e:
        flash(f"Ошибка: {str(e)}", "danger")
    finally:
        db.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)