from database.config import get_settings
from database.database import get_session, get_database_engine, init_db, session_scope
from models.enums import RoleName, TransactionType, Currency, PredictStatus, Gender
from models.user import Role, User
from models.predict import Patient, PredictTask, Predict
from models.finance import Balance, Transaction

if __name__ == "__main__":
    settings = get_settings()
    print(f'APP_NAME: {settings.APP_NAME}')
    print(f'API_VERSION: {settings.API_VERSION}')
    print(f'DEBUG: {settings.DEBUG}')
    print(f'DB_HOST: {settings.DB_HOST}')
    print(f'DB_PORT: {settings.DB_PORT}')
    print(f'DB_USER: {settings.DB_USER}')
    print(f'DB_NAME: {settings.DB_NAME}')

    init_db(drop_all=True)
    print('Init database has been success')

    with session_scope() as session:
        print(f"\nСоздание ролей:")
        admin_role = Role(name=RoleName.ADMIN)
        user_role = Role(name=RoleName.USER)
        session.add_all([admin_role, user_role])
        session.flush()

        roles_from_db = session.query(Role).all()
        print(f"Роли, сохраненные в базе данных:")
        for role in roles_from_db:
            print(f'{role}')

        print(f"\nСоздание пользователей:")
        admin = User(
            login="admin",
            email="admin@mail.ru",
            display_name="Администратор",
            password="admin12345",
            role_id=admin_role.id
        )

        user = User(
            login="user",
            email="user@mail.ru",
            display_name="Тестовый пользователь",
            password="user12345",
            role_id=user_role.id
        )
        session.add_all([admin, user])
        session.flush()

        users_from_db = session.query(User).all()
        print(f"Пользователи, сохраненные в базе данных:")
        for user in users_from_db:
            print(f'{user}')

        print(f"\nТестирование баланса:")
        print(f"Пополнение баланса:")
        user = session.query(User).filter_by(login="user").first()

        user.balance.deposit(5000)
        user.add_transaction(Transaction(
            type=TransactionType.DEPOSIT, amount=5000, currency=Currency.RUB,
            description="Пополнение баланса", user_id=user.id
        ))

        user.balance.withdraw(1500)
        user.add_transaction(Transaction(
            type=TransactionType.WITHDRAWAL, amount=1500, currency=Currency.RUB,
            description="Оплата подписки", user_id=user.id
        ))

        session.commit()
        session.refresh(user)

        print(f"Пользователь после изменений: {user}")
        print(f"Баланс пользователя после измнений: {user.balance}")
        print(f"Транзакции выполненные пользователем: {user.transactions}")

        print(f"\nСоздание задачи на редсказание:")
        patient = Patient(
            age=35,
            gender=Gender.MALE,
            physical_activity_days_per_week=5,
            stress_level=3,
            bmi=24.2,
            exercise_hours_per_week=6.5,
            sedentary_hours_per_day=7.0,
            sleep_hours_per_day=8.0,
            heart_rate=68.5,
            cholesterol=4.8,
            blood_sugar=5.2,
            triglycerides=1.5,
            smoking=False,
            alcohol_consumption=True,
            diabetes=False,
            obesity=False,
            family_history=True
        )
        session.add(patient)
        session.flush()
        session.refresh(patient)

        task = PredictTask(
            patient_id=patient.id,
            user_id=user.id,
            status=PredictStatus.PROCESSING,
            cost=200
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        tasks_from_db = session.query(PredictTask).all()
        for task in tasks_from_db:
            print(f"Задача на предсказание: {task}")
            print(f"Пациент в задаче на предсказание: {task.patient}")

        print(f"\nСоздание предсказания:")
        predict = Predict(
            prediction=False,
            probability=0.35,
            task_id=task.id
        )
        task.predict = predict
        task.status = PredictStatus.COMPLETED
        session.add(predict)
        session.commit()

        tasks_from_db = session.query(PredictTask).all()
        for task in tasks_from_db:
            print(f"Задача на предсказание: {task}")
            print(f"Пациент в задаче на предсказание: {task.patient}")
            print(f"Результат предсказания: {task.predict}")

        predicts_from_db = session.query(Predict).all()
        for predict in predicts_from_db:
            print(f"Результат предсказания: {predict}")
            print(f"Задача на предсказание: {predict.task}")
