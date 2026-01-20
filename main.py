from models import (
    User, Role, RoleName, Currency, Gender,
    Balance, TransactionType, Patient,
    PredictTask, Predict, Transaction
)

admin_role = Role(id=1, name=RoleName.ADMIN)
user_role = Role(id=2, name=RoleName.USER)

admin_user = User(
    id=1,
    login="admin",
    email="admin@mail.ru",
    display_name="Admin",
    password_hash="password",
    role=admin_role
)

simple_user = User(
    id=2,
    login="user",
    email="user@mail.ru",
    display_name="User",
    password_hash="password",
    role=user_role
)

balance = Balance(
    id=1,
    value=1000,
    currency=Currency.RUB,
    user_id=simple_user.id,
)

deposit_transaction = Transaction(
    id=1,
    type=TransactionType.DEPOSIT,
    amount=1000,
    currency=Currency.RUB,
    description="Пополнение счета",
    user_id=admin_user.id
)

withdrawal_transaction = Transaction(
    id=2,
    type=TransactionType.WITHDRAWAL,
    amount=500,
    currency=Currency.USD,
    description="Оплата",
    user_id=simple_user.id
)

patient = Patient(
    id=1,
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

task = PredictTask(
    id=1,
    patient=patient,
    user_id=simple_user.id
)

predict = Predict(
    id=1,
    prediction=True,
    probability=0.87
)

print(admin_role)
print(user_role)
print(admin_user)
print(simple_user)
print(deposit_transaction)
print(withdrawal_transaction)
print(balance)
balance.deposit(1000)
print(balance)
balance.withdraw(2000)
print(balance)
print(task)
print(predict)
