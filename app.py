from flask import Flask, render_template, request
from services.api_client import OpenFoodFactsAPI

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    product = None
    if request.method == "POST":
        barcode = request.form.get("barcode")
        product = OpenFoodFactsAPI.get_product_by_barcode(barcode)
    return render_template("index.html", product=product)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)