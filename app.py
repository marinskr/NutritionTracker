from flask import Flask, render_template, request, flash, redirect, url_for
from services.api_client import OpenFoodFactsAPI
from services.database import Database
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
RESET_TOKEN = secrets.token_urlsafe(16)


def get_db_connection():
    return Database()


@app.route("/", methods=["GET", "POST"])
def index():
    # Инициализация переменных
    product = None
    today_stats = None
    food_history = None

    try:
        db = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')

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

        # Всегда получаем актуальные данные
        today_stats = db.get_today_nutrition(today)
        food_history = db.get_food_diary()

    except Exception as e:
        flash(f"Ошибка базы данных: {str(e)}", "danger")
    finally:
        if 'db' in locals():
            db.close()

    return render_template(
        "index.html",
        product=product,
        food_history=food_history,
        reset_token=RESET_TOKEN,
        today_stats=today_stats
    )


@app.route("/reset-db", methods=["POST"])
def reset_db():
    if request.method == "POST" and request.form.get("token") == RESET_TOKEN:
        try:
            db = get_db_connection()
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)