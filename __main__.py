desc = """Автоматически подбирает парсер на основе проверок.

Возможно отделить парсеры для сайтов с рендером JS и без него.

Обрабатывает следующие сайты: delish, bbcgoodfood, foodnetwork"""

import pydantic_argparse
from src.__stable_prepared import url_processing, InputArgs

parser = pydantic_argparse.ArgumentParser(
        model=InputArgs,
        prog="FoodParser",
        description=desc,
        version="v6"
    )

args_model = parser.parse_typed_args()

url_processing(input_args=args_model)