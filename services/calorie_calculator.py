from typing import Dict


class CalorieCalculator:
    @staticmethod
    def calculate_daily_calories(weight: float, height: float, age: int, gender: str, activity_level: float) -> float:
        """
        Рассчитывает дневную норму калорий по формуле Миффлина-Сан Жеора

        Args:
            weight: Вес в кг
            height: Рост в см
            age: Возраст в годах
            gender: Пол ('male' или 'female')
            activity_level: Уровень активности (1.2-1.9)

        Returns:
            Дневная норма калорий
        """
        if gender.lower() == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:  # female
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        return bmr * activity_level

    @staticmethod
    def get_macronutrients(calories: float) -> Dict[str, float]:
        """
        Рассчитывает рекомендуемое количество белков, жиров и углеводов

        Args:
            calories: Дневная норма калорий

        Returns:
            Словарь с нормами БЖУ в граммах
        """
        proteins_g = (calories * 0.3) / 4  # 30% от калорий, 4 ккал/г
        fats_g = (calories * 0.3) / 9  # 30% от калорий, 9 ккал/г
        carbs_g = (calories * 0.4) / 4  # 40% от калорий, 4 ккал/г

        return {
            "proteins": round(proteins_g, 1),
            "fats": round(fats_g, 1),
            "carbs": round(carbs_g, 1)
        }


# Пример использования
if __name__ == "__main__":
    calculator = CalorieCalculator()
    calories = calculator.calculate_daily_calories(
        weight=70, height=175, age=30, gender="male", activity_level=1.55
    )
    print(f"Дневная норма калорий: {calories:.0f} ккал")
    macros = calculator.get_macronutrients(calories)
    print(f"Белки: {macros['proteins']}г, Жиры: {macros['fats']}г, Углеводы: {macros['carbs']}г")