from flask import Flask, render_template, request, flash, redirect, url_for
from services.api_client import OpenFoodFactsAPI
from services.database import Database
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Секретный токен для защиты операции сброса
RESET_TOKEN = secrets.token_urlsafe(16)


@app.route("/", methods=["GET", "POST"])
def index():
    db = Database()

    if request.method == "POST":
        if "search_product" in request.form:
            barcode = request.form.get("barcode")
            api_product = OpenFoodFactsAPI.get_product_by_barcode(barcode)
            if api_product:
                return render_template(
                    "index.html",
                    product=api_product,
                    food_history=db.get_food_diary(),
                    reset_token=RESET_TOKEN
                )

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
                else:
                    flash("Ошибка при сохранении записи", "danger")

            except Exception as e:
                flash(f"Ошибка: {str(e)}", "danger")

    food_history = db.get_food_diary()
    db.close()
    return render_template(
        "index.html",
        product=None,
        food_history=food_history,
        reset_token=RESET_TOKEN
    )


@app.route("/reset-db", methods=["POST"])
def reset_db():
    if request.method == "POST" and request.form.get("token") == RESET_TOKEN:
        db = Database()
        try:
            if db.reset_database():
                flash("Все данные успешно удалены", "success")
            else:
                flash("Ошибка при очистке базы данных", "danger")
        finally:
            db.close()
    else:
        flash("Неверный запрос на очистку", "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)