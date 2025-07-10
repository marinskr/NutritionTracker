from typing import List, Dict
from services.database import Database
import numpy as np


class RecommendationEngine:
    def __init__(self, db_path: str = "nutrition.db"):
        self.db = Database(db_path)

    def _get_all_products(self) -> List[Dict]:
        """Получает все продукты из базы данных."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, name, barcode, 
                   calories_per_100g, proteins_per_100g, 
                   fats_per_100g, carbs_per_100g 
            FROM products
        """)
        return [
            {
                'id': row[0], 'name': row[1], 'barcode': row[2],
                'calories': row[3], 'proteins': row[4],
                'fats': row[5], 'carbs': row[6]
            }
            for row in cursor.fetchall()
        ]

    def _calculate_nutrient_balance(self, daily_norms: Dict, today_stats: Dict) -> Dict:
        """Рассчитывает баланс нутриентов в абсолютных и процентных значениях."""
        balance = {
            'proteins': daily_norms['proteins'] - today_stats.get('total_proteins', 0),
            'fats': daily_norms['fats'] - today_stats.get('total_fats', 0),
            'carbs': daily_norms['carbs'] - today_stats.get('total_carbs', 0),
            'calories': daily_norms['calories'] - today_stats.get('total_calories', 0)
        }
        percent_balance = {
            'proteins': balance['proteins'] / daily_norms['proteins'] * 100 if daily_norms['proteins'] > 0 else 0,
            'fats': balance['fats'] / daily_norms['fats'] * 100 if daily_norms['fats'] > 0 else 0,
            'carbs': balance['carbs'] / daily_norms['carbs'] * 100 if daily_norms['carbs'] > 0 else 0,
            'calories': balance['calories'] / daily_norms['calories'] * 100 if daily_norms['calories'] > 0 else 0
        }
        return {'absolute': balance, 'percent': percent_balance}

    def _calculate_recommended_mass(self, product: Dict, daily_norms: Dict, abs_balance: Dict) -> float:
        """Рассчитывает рекомендуемую массу продукта в граммах для нормализации баланса."""
        max_mass = 500.0  # Максимальная масса порции
        min_mass = 10.0   # Минимальная масса порции
        nutrient_masses = []

        for nutrient in ['proteins', 'fats', 'carbs', 'calories']:
            nutrient_value = product.get(nutrient, 0)
            if nutrient_value <= 0:  # Избегаем деления на ноль
                continue

            # Если есть дефицит, рассчитываем массу для его закрытия
            if abs_balance[nutrient] > 0:
                mass = (abs_balance[nutrient] / nutrient_value) * 100
                nutrient_masses.append(mass)
            elif abs_balance[nutrient] < -10:  # Если переизбыток, ограничиваем добавление
                max_nutrient_addition = daily_norms[nutrient] * 0.05  # Допускаем 5% от нормы
                mass = (max_nutrient_addition / nutrient_value) * 100
                nutrient_masses.append(mass)
            else:
                # Нейтральный случай: допускаем максимальную массу
                nutrient_masses.append(max_mass)

        # Берём минимальную массу, чтобы не превысить нормы
        if nutrient_masses:
            recommended_mass = min(nutrient_masses)
            return max(min_mass, min(max_mass, recommended_mass))
        return min_mass  # Значение по умолчанию

    def recommend_products(self, daily_norms: Dict, today_stats: Dict, n_recommendations: int = 5) -> List[Dict]:
        """Рекомендует продукты с процентом соответствия (0-100%) и массой в граммах."""
        try:
            products = self._get_all_products()
            if not products:
                return []

            # Получаем баланс нутриентов
            balance = self._calculate_nutrient_balance(daily_norms, today_stats)
            abs_balance = balance['absolute']
            percent_balance = balance['percent']

            # Определяем веса для нутриентов на основе их дефицита
            priorities = {
                'proteins': max(0.1, abs_balance['proteins'] / daily_norms['proteins']) if abs_balance['proteins'] > 0 and daily_norms['proteins'] > 0 else 0.1,
                'fats': max(0.1, abs_balance['fats'] / daily_norms['fats']) if abs_balance['fats'] > 0 and daily_norms['fats'] > 0 else 0.1,
                'carbs': max(0.1, abs_balance['carbs'] / daily_norms['carbs']) if abs_balance['carbs'] > 0 and daily_norms['carbs'] > 0 else 0.1
            }

            # Нормализуем веса
            total_priority = sum(priorities.values())
            if total_priority > 0:
                priorities = {k: v / total_priority for k, v in priorities.items()}

            scored_products = []
            for product in products:
                match_score = 0.0

                # Рассчитываем вклад каждого нутриента
                for nutrient in ['proteins', 'fats', 'carbs']:
                    nutrient_value = product.get(nutrient, 0)
                    norm = daily_norms.get(nutrient, 1)
                    if norm <= 0:
                        norm = 1  # Избегаем деления на ноль

                    if abs_balance[nutrient] > 0:
                        nutrient_contribution = (nutrient_value / norm) * 100
                        match_score += priorities[nutrient] * nutrient_contribution
                    elif abs_balance[nutrient] < -10:
                        penalty = (nutrient_value / norm) * 100 * 0.75
                        match_score -= penalty

                # Учитываем калории
                calorie_contribution = (product.get('calories', 0) / daily_norms.get('calories', 1)) * 100
                if abs_balance['calories'] > 0:
                    match_score += calorie_contribution * 0.1
                else:
                    match_score -= calorie_contribution * 0.2

                if match_score > 0:
                    scored_products.append((match_score, product))

            # Сортируем продукты по убыванию оценки
            scored_products.sort(reverse=True, key=lambda x: x[0])

            # Нормализуем оценки в диапазон 0-100%
            max_score = scored_products[0][0] if scored_products else 1
            recommendations = [
                {
                    **product,
                    'match_score': min(100.0, max(0.0, score / max(1.0, max_score) * 100)),
                    'recommended_mass': round(self._calculate_recommended_mass(product, daily_norms, abs_balance), 1)
                }
                for score, product in scored_products[:n_recommendations]
            ]

            return recommendations

        except Exception as e:
            print(f"Ошибка в рекомендациях: {e}")
            return []

    def close(self):
        self.db.close()