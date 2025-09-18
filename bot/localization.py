LANGUAGES = {
    'en': {
        'hello': '👋 Hello, {user}!',
        'balance': '💰 Balance: {balance} EUR',
        'overpay': '💳 Send the exact amount. Overpayments will be credited.',
        'shop': '🛍 Shop',
        'profile': '👤 Profile',
        'top_up': '💸 Top Up',
        'channel': '📢 Channel',
        'price_list': '💲 Price List',
        'language': '🌐 Language',
        'admin_panel': '🎛 Admin Panel',
        'help': '❓ Help',
        'help_info': (
            'Use the main menu to work with the bot:\n'
            '🛍 Shop – browse categories and choose a product.\n'
            '   • Select an item and confirm to purchase it.\n'
            '👤 Profile – view your balance and purchased items.\n'
            '💸 Top Up – choose a payment method and follow the instructions to add funds.\n'
            '🌐 Language – switch the interface language.\n'
            '🎁 Purchased items – available in Profile after you buy something.\n'
            'If you need assistance, contact {helper}.'
        ),
        'admin_help_info': (
            'Admin panel functions:\n'
            '🛠 Assign assistants – manage assistant accounts.\n'
            '📦 View Stock – browse and delete available product stock.\n'
            '🏪 Parduotuvės valdymas – manage shop categories and items.\n'
            '👥 Vartotojų valdymas – manage user balances and roles.\n'
            '📢 Pranešimų siuntimas – send messages to all users.'
        ),
        'assistant_help_info': (
            'Assistant panel functions:\n'
            '🖼 Assign photos – attach photos to items.\n'
            'Use Back to menu to return.'
        ),
        'choose_language': 'Please choose a language',
        'invoice_message': (
            '🧾 <b>Payment Invoice Created</b>\n\n'
            '<b>Amount:</b> <code>{amount}</code> {currency}\n'
            '🏦 <b>Payment Address:</b>\n<code>{address}</code>\n\n'
            '⏳ <b>Expires At:</b> {expires_at} LT\n'
            '⚠️ <b>Payment must be completed within 30 minutes of invoice creation.</b>\n\n'
            '❗️ <b>Important:</b> Send <u>exactly</u> this amount of {currency}.\n\n'
            '✅ <b>Confirmation is automatic via webhook after network confirmation.</b>'
        ),
        'cancel': 'Cancel',
        'cancel_payment': '❌ Cancel Payment',
        'payment_successful': '✅ Payment confirmed. Balance increased by {amount}€',
        'back_home': 'Back Home',
        'invoice_cancelled': 'Payment failed/expired. Your items are no longer reserved.',
        'total_purchases': '📦 Total Purchases: {count}',
        'note': '⚠️ Note: No refunds. Please ensure you send the exact amount for payments, as underpayments will not be confirmed.',
        'main_menu_text': (
            "🍩👩‍🍳 Welcome to Sugar Chef’s Kitchen, {user}!\n"
            "Where every order is sprinkled with sweetness ✨\n\n"
            "🍬 Candy Balance: {balance} EUR\n"
            "🍪 Goodies Collected: {purchases}\n\n"
            "⚠️ Sugar Alert!\n"
            "No refunds on treats 🍭\n"
            "Make sure to send the exact sprinkle amount - underpayments stay in the mixing bowl and won’t be served 🍰"
        ),
        'feedback_service': '🛎️ How was your experience with the service?\n✍️ Leave a hand review in our group: https://t.me/+QVDtC4t9OglmZDVk',
        'feedback_product': 'Opinion on the product?',
        'thanks_feedback': 'Thanks for your feedback!',
        'confirm_purchase': 'Confirm purchase of {item} for {price}€?',
        'purchase_button': 'Purchase',
        'apply_promo': 'Apply promo code',
        'promo_prompt': 'Send promo code:',
        'promo_invalid': '❌ Invalid or expired promo code',
        'promo_applied': '✅ Promo code applied. New price: {price}€',
        'insufficient_funds': (
            '❌ Insufficient funds to purchase {item}.\n'
            'Price: {price}€\n'
            'Balance: {balance}€\n'
            'You still need {shortfall}€.'
        ),
        'shortfall_choose_method': '💵 You still need {amount}€ to buy {item}. Choose payment method:',
        'pay_shortfall_button': 'Create invoice for {amount}€',

        'choose_subcategory': '🏘️ Choose a district:',
        'select_product': '🏪 Select a product',


        'choose_subcategory': '🏘️ Choose a district:',
        'select_product': '🏪 Select a product',


    },
    'ru': {
        'hello': '👋 Привет, {user}!',
        'balance': '💰 Баланс: {balance} EUR',
        'overpay': '💳 Отправьте точную сумму. Переплаты будут зачислены.',
        'shop': '🛍 Магазин',
        'profile': '👤 Профиль',
        'top_up': '💸 Пополнить',
        'channel': '📢 Канал',
        'price_list': '💲 Прайс-лист',
        'language': '🌐 Язык',
        'admin_panel': '🎛 Админ панель',
        'help': '❓ Помощь',
        'help_info': (
            'Используйте главное меню для работы с ботом:\n'
            '🛍 Магазин – просматривайте категории и выбирайте товар.\n'
            '   • Выберите товар и подтвердите покупку.\n'
            '👤 Профиль – ваш баланс и купленные товары.\n'
            '💸 Пополнить – выберите способ оплаты и следуйте инструкциям.\n'
            '🌐 Язык – сменить язык интерфейса.\n'
            '🎁 Купленные товары – доступны в профиле после покупки.\n'
            'Если нужна помощь, обратитесь к {helper}.'
        ),
        'admin_help_info': (
            'Функции админ-панели:\n'
            '🛠 Назначить ассистентов – управление помощниками.\n'
            '📦 Просмотр склада – список товаров и удаление остатков.\n'
            '🏪 Parduotuvės valdymas – управление магазином.\n'
            '👥 Vartotojų valdymas – управление пользователями.\n'
            '📢 Pranešimų siuntimas – рассылка сообщений.'
        ),
        'assistant_help_info': (
            'Функции панели ассистента:\n'
            '🖼 Привязать фото – добавление фотографий к товарам.\n'
            'Используйте "Назад в меню" для возврата.'
        ),
        'choose_language': 'Пожалуйста, выберите язык',
        'invoice_message': (
            '🧾 <b>Создан инвойс на оплату</b>\n\n'
            '<b>Сумма:</b> <code>{amount}</code> {currency}\n'
            '🏦 <b>Адрес оплаты:</b>\n<code>{address}</code>\n\n'
            '⏳ <b>Действителен до:</b> {expires_at} LT\n'
            '⚠️ <b>Оплата должна быть выполнена в течение 30 минут после создания.</b>\n\n'
            '❗️ <b>Важно:</b> Отправьте <u>ровно</u> это количество {currency}.\n\n'
            '✅ <b>Подтверждение произойдет автоматически через вебхук после подтверждения сети.</b>'
        ),
        'cancel': 'Отмена',
        'cancel_payment': '❌ Отменить оплату',
        'payment_successful': '✅ Платёж подтверждён. Баланс пополнен на {amount}€',
        'back_home': 'Назад домой',
        'invoice_cancelled': 'Оплата не завершена/истекла. Ваши товары больше не зарезервированы.',
        'total_purchases': '📦 Всего покупок: {count}',
        'note': '⚠️ Возврат средств невозможен. Отправляйте точную сумму, недоплаты не подтверждаются.',
        'main_menu_text': (
            '🍩👩‍🍳 Добро пожаловать на кухню Sugar Chef, {user}!\n'
            'Здесь каждый заказ посыпан сладостью ✨\n\n'
            '🍬 Сладкий баланс: {balance} EUR\n'
            '🍪 Собрано вкусняшек: {purchases}\n\n'
            '⚠️ Сахарное предупреждение!\n'
            'Возвратов нет 🍭\n'
            'Отправляйте точную сумму посыпки - недоплаты останутся в миске и не будут поданы 🍰'
        ),
        'feedback_service': '🛎️ Как вам обслуживание?\n✍️ Напишите отзыв вручную в группе: https://t.me/+QVDtC4t9OglmZDVk',
        'feedback_product': 'Мнение о товаре?',
        'thanks_feedback': 'Спасибо за отзыв!',
        'confirm_purchase': 'Подтвердить покупку {item} за {price}€?',
        'purchase_button': 'Купить',
        'apply_promo': 'Применить промокод',
        'promo_prompt': 'Введите промокод:',
        'promo_invalid': '❌ Недействительный или просроченный промокод',
        'promo_applied': '✅ Промокод применён. Новая цена: {price}€',
        'insufficient_funds': (
            '❌ Недостаточно средств для покупки {item}.\n'
            'Цена: {price}€\n'
            'Баланс: {balance}€\n'
            'Необходимо доплатить {shortfall}€.'
        ),
        'shortfall_choose_method': '💵 Необходимо доплатить {amount}€ за {item}. Выберите способ оплаты:',
        'pay_shortfall_button': 'Создать счёт на {amount}€',

        'choose_subcategory': '🏘️ Выберите район:',
        'select_product': '🏪 Выберите товар',


        'choose_subcategory': '🏘️ Выберите район:',
        'select_product': '🏪 Выберите товар',

    },
    'lt': {
        'hello': '👋 Sveiki, {user}!',
        'balance': '💰 Balansas: {balance} EUR',
        'overpay': '💳 Siųskite tikslią sumą. Permokos bus įskaitytos.',
        'shop': '🛍 Parduotuvė',
        'profile': '👤 Profilis',
        'top_up': '💸 Papildyti',
        'channel': '📢 Kanalas',
        'price_list': '💲 Kainoraštis',
        'language': '🌐 Kalba',
        'admin_panel': '🎛 Admin pultas',
        'help': '❓ Pagalba',
        'help_info': (
            'Naudokite pagrindinį meniu darbui su botu:\n'
            '🛍 Parduotuvė – naršykite kategorijas ir pasirinkite prekę.\n'
            '   • Pasirinkite prekę ir patvirtinkite pirkimą.\n'
            '👤 Profilis – jūsų balansas ir nupirktos prekės.\n'
            '💸 Papildyti – pasirinkite mokėjimo būdą ir vykdykite instrukcijas.\n'
            '🌐 Kalba – pakeisti sąsajos kalbą.\n'
            '🎁 Nupirktos prekės – matomos profilyje po pirkimo.\n'
            'Jei reikia pagalbos, susisiekite su {helper}.'
        ),
        'admin_help_info': (
            'Admin pulto funkcijos:\n'
            '🛠 Asistentų priskyrimas – valdykite asistentų paskyras.\n'
            '📦 Peržiūrėti likučius – naršykite prekes ir trinkite likučius.\n'
            '🏪 Parduotuvės valdymas – prekių ir kategorijų valdymas.\n'
            '👥 Vartotojų valdymas – naudotojų balansai ir rolės.\n'
            '📢 Pranešimų siuntimas – siųsti žinutes vartotojams.'
        ),
        'assistant_help_info': (
            'Asistento pulto funkcijos:\n'
            '🖼 Nuotraukų priskyrimas – pridėkite nuotraukas prie prekių.\n'
            'Naudokite „Atgal į meniu“ norėdami grįžti.'
        ),
        'choose_language': 'Pasirinkite kalbą',
        'invoice_message': (
            '🧾 <b>Sukurta mokėjimo sąskaita</b>\n\n'
            '<b>Suma:</b> <code>{amount}</code> {currency}\n'
            '🏦 <b>Mokėjimo adresas:</b>\n<code>{address}</code>\n\n'
            '⏳ <b>Galioja iki:</b> {expires_at} LT\n'
            '⚠️ <b>Mokėjimą reikia atlikti per 30 minučių nuo sąskaitos sukūrimo.</b>\n\n'
            '❗️ <b>Svarbu:</b> Nusiųskite <u>tiksliai</u> tiek {currency} į šį adresą.\n\n'
            '✅ <b>Patvirtinimas vyks automatiškai per webhook po tinklo patvirtinimo.</b>'
        ),
        'cancel': 'Atšaukti',
        'cancel_payment': '❌ Atšaukti mokėjimą',
        'payment_successful': '✅ Mokėjimas patvirtintas. Balansas padidintas {amount}€',
        'back_home': 'Grįžti į pradžią',
        'invoice_cancelled': 'Mokėjimas nepavyko/baigėsi. Jūsų prekės nebėra rezervuotos.',
        'total_purchases': '📦 Viso pirkinių: {count}',
        'note': '⚠️ Pastaba: grąžinimų nėra. Įsitikinkite, kad siunčiate tikslią sumą, nes nepakankamos sumos nebus patvirtintos.',
        'main_menu_text': (
            '🍩👩‍🍳 Sveikas atvykęs į Sugar Chef virtuvę, {user}!\n'
            'Čia kiekvienas užsakymas pabarstytas saldumu ✨\n\n'
            '🍬 Saldainių balansas: {balance} EUR\n'
            '🍪 Surinktų skanumynų: {purchases}\n\n'
            '⚠️ Cukraus įspėjimas!\n'
            'Pinigai negrąžinami 🍭\n'
            'Siųsk tikslų pabarstukų kiekį - nepakankami mokėjimai liks dubenyje ir nebus patiekti 🍰'
        ),
        'feedback_service': '🛎️ Kaip vertinate aptarnavimą?\n✍️ Parašykite atsiliepimą šioje grupėje: https://t.me/+QVDtC4t9OglmZDVk',
        'feedback_product': 'Kokia nuomonė apie prekę?',
        'thanks_feedback': 'Ačiū už atsiliepimą!',
        'confirm_purchase': 'Patvirtinti {item} pirkimą už {price}€?',
        'purchase_button': 'Pirkti',
        'apply_promo': 'Taikyti nuolaidos kodą',
        'promo_prompt': 'Įveskite nuolaidos kodą:',
        'promo_invalid': '❌ Neteisingas arba pasibaigęs kodas',
        'promo_applied': '✅ Kodas pritaikytas. Nauja kaina: {price}€',
        'insufficient_funds': (
            '❌ Nepakanka lėšų įsigyti {item}.\n'
            'Kaina: {price}€\n'
            'Balansas: {balance}€\n'
            'Reikia papildomai {shortfall}€.'
        ),
        'shortfall_choose_method': '💵 Reikia papildomai {amount}€ už {item}. Pasirinkite mokėjimo būdą:',
        'pay_shortfall_button': 'Sukurti sąskaitą {amount}€',

        'choose_subcategory': '🏘️ Pasirinkite rajoną:',
        'select_product': '🏪 Pasirinkite prekę',


        'choose_subcategory': '🏘️ Pasirinkite rajoną:',
        'select_product': '🏪 Pasirinkite prekę',


    },
}

def t(lang: str, key: str, **kwargs) -> str:
    lang_data = LANGUAGES.get(lang, LANGUAGES['en'])
    template = lang_data.get(key, '')
    return template.format(**kwargs)
