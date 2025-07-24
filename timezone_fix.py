import pytz

MSK_TZ = pytz.timezone("Europe/Moscow")
@router.message(CreateNewsletter.waiting_for_schedule_datetime, F.text)
async def schedule_datetime_received(
    message: Message, state: FSMContext, session: AsyncSession
):

    try:
        naive_dt = datetime.datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        msk_dt = MSK_TZ.localize(naive_dt)
        scheduled_dt = msk_dt.astimezone(pytz.UTC)
        print(f"DEBUG: Пользователь ввел: {message.text}")
        print(f"DEBUG: Интерпретировано как MSK: {msk_dt}")
        print(f"DEBUG: Сохраняется в UTC: {scheduled_dt}")
        now_msk = datetime.datetime.now(MSK_TZ)
        if msk_dt <= now_msk:
            await message.answer(
                f"⚠️ Указанное время уже прошло!\n"
                f"Текущее время: {now_msk.strftime('%d.%m.%Y %H:%M')} (МСК)\n"
                f"Укажите время в будущем."
            )
            return
    except ValueError:
        await message.answer(
            "Неверный формат. Пожалуйста, введите дату и время в формате: `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
            "Например: `24.07.2025 21:45`"
        )
        return
    data = await state.get_data()
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Ошибка: не удалось вас идентифицировать.")
        await state.clear()
        return
    audience_str = data.get("audience")
    try:
        if audience_str == "all":
            audience_enum_member = TargetAudienceEnum.ALL
        elif audience_str == "users":
            audience_enum_member = TargetAudienceEnum.USERS
        elif audience_str == "moderators":
            audience_enum_member = TargetAudienceEnum.MODERATORS
        elif audience_str == "admins":
            audience_enum_member = TargetAudienceEnum.ADMINS
        else:
            raise ValueError(f"Неизвестное значение аудитории: {audience_str}")
    except ValueError:
        await message.answer(f"Ошибка: неизвестная аудитория '{audience_str}'.")
        await state.clear()
        return
    newsletter = Newsletter(
        creator_id=user.id,
        text=data.get("text"),
        target_audience=audience_enum_member,
        status=NewsletterStatusEnum.SCHEDULED,
        scheduled_at=scheduled_dt,
    )
    session.add(newsletter)
    try:
        await session.commit()
        print(
            f"DEBUG: Запланированная рассылка успешно сохранена с ID: {newsletter.id}"
        )
    except Exception as e:
        print(f"DEBUG: Ошибка сохранения запланированной рассылки: {e}")
        await message.answer(f"Ошибка при сохранении рассылки: {str(e)}")
        await state.clear()
        return
    await state.clear()
    display_time = msk_dt.strftime("%d.%m.%Y %H:%M")
    await message.answer(
        f"✅ Рассылка запланирована на {display_time} (МСК).\n\n"
        f"<b>Текст:</b> {data.get('text')}\n"
        f"<b>Аудитория:</b> {audience_str}",
        parse_mode="HTML",
    )
