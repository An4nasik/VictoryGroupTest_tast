import asyncio

from sqlalchemy import func, select

from models.database import AsyncSessionLocal
from models.models import Role


async def init_roles():
    async with AsyncSessionLocal() as session:
        try:
            count = await session.scalar(select(func.count(Role.id)))
            if count > 0:
                print(
                    f"Роли уже существуют ({count} записей). Пропускаем инициализацию..."
                )
                return
            roles_data = [
                {
                    "name": "user",
                    "permissions": {
                        "can_receive_newsletters": True,
                        "can_use_start": True,
                    },
                },
                {
                    "name": "moderator",
                    "permissions": {
                        "can_receive_newsletters": True,
                        "can_use_start": True,
                        "can_create_newsletters": True,
                        "can_send_newsletters": True,
                    },
                },
                {
                    "name": "admin",
                    "permissions": {
                        "can_receive_newsletters": True,
                        "can_use_start": True,
                        "can_create_newsletters": True,
                        "can_send_newsletters": True,
                        "can_view_users": True,
                        "can_view_newsletters": True,
                        "can_manage_roles": True,
                    },
                },
            ]
            for role_data in roles_data:
                role = Role(**role_data)
                session.add(role)
            await session.commit()
            print("✅ Базовые роли успешно созданы:")
            for role_data in roles_data:
                print(f"  - {role_data['name']}")
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при создании ролей: {e}")
            raise
if __name__ == "__main__":
    print("🔧 Инициализация базовых ролей...")
    asyncio.run(init_roles())
