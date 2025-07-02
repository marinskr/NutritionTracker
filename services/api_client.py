import requests
from typing import Optional, Dict


class OpenFoodFactsAPI:
    BASE_URL = "https://world.openfoodfacts.org/api/v2"

    @classmethod
    def get_product_by_barcode(cls, barcode: str) -> Optional[Dict]:
        """
        Получает информацию о продукте по штрих-коду

        Args:
            barcode: Штрих-код продукта

        Returns:
            Словарь с информацией о продукте или None, если продукт не найден
        """
        url = f"{cls.BASE_URL}/product/{barcode}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 1:  # Продукт найден
                product = data.get("product", {})
                return {
                    "name": product.get("product_name", "Неизвестный продукт"),
                    "barcode": barcode,
                    "calories": product.get("nutriments", {}).get("energy-kcal_100g"),
                    "proteins": product.get("nutriments", {}).get("proteins_100g"),
                    "fats": product.get("nutriments", {}).get("fat_100g"),
                    "carbs": product.get("nutriments", {}).get("carbohydrates_100g"),
                    "weight": 100  # По умолчанию данные на 100г продукта
                }
            return None
        except requests.exceptions.RequestException:
            return None


# Пример использования
if __name__ == "__main__":
    api = OpenFoodFactsAPI()
    product = api.get_product_by_barcode("4680019560922")  # Пример штрих-кода Nutella
    print(product)