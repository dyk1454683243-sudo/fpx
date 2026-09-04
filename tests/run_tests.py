#!/usr/bin/env python3
"""Запускатель тестов fpx.

Как использовать:
    python run_tests.py                 # unit-тесты (быстрые, дефолт)
    python run_tests.py --stress        # только стресс/нагрузочные тесты
    python run_tests.py --all           # unit + stress
    python run_tests.py -v -k chat      # доп. флаги pytest пробрасываются как есть
    python run_tests.py --cov           # unit-тесты + отчёт о покрытии (fpx)

Структура:
    tests/unit/   — быстрые изолированные unit-тесты (мокают сеть/файлы/redis)
    tests/stress/ — нагрузочные тесты (много данных / много конкурентных операций,
                    выполняются дольше и не блокируют обычный CI-прогон)

Требования:
    pip install pytest pytest-asyncio pytest-cov beautifulsoup4 httpx fpx-engine
"""

import subprocess
import sys


def main():
    argv = sys.argv[1:]
    target = "unit"
    cov = False
    passthrough = []

    for arg in argv:
        if arg == "--stress":
            target = "stress"
        elif arg == "--all":
            target = "all"
        elif arg == "--cov":
            cov = True
        else:
            passthrough.append(arg)

    if target == "unit":
        paths = ["unit"]
    elif target == "stress":
        paths = ["stress"]
    else:
        paths = ["unit", "stress"]

    args = [sys.executable, "-m", "pytest", *paths, "-v", "--tb=short"]
    if cov:
        args += ["--cov=fpx", "--cov-report=term-missing"]
    args += passthrough

    print("=" * 60)
    print("Запуск тестов fpx")
    print("=" * 60)
    print(f"Команда: {' '.join(args)}")
    print()
    result = subprocess.run(args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
