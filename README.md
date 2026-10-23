Разработано ОТП 2026-2027
Протестировано @olivo4chka @sady91x и иными лицами
Как запустить работу:
powershell
# 1. Распаковал проект (без venv)
# 2. Создал venv
python -m venv venv
.\venv\Scripts\Activate        # Windows PowerShell

# 3. Поставил всё из requirements.txt
pip install -r requirements.txt

# 4. Настроил .env (Отправлю Володе в лс)
# 5. Запустил
python main.py
