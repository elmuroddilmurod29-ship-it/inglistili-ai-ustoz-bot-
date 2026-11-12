import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
from aiogram import Bot
from aiogram.enums import ChatAction
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    GEMINI_FALLBACK_MODELS,
    GEMINI_MODEL,
)
from database import save_active_message, update_user

logger = logging.getLogger(__name__)

# Initialize Google GenAI client
ai_client: Optional[genai.Client] = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI Client: {e}")

USER_CONVERSATIONS: Dict[int, List[Dict[str, Any]]] = {}
USER_MESSAGE_COUNTERS: Dict[int, int] = {}


MASTER_SYSTEM_PROMPT = """Sen Telegramda yozishayotgan haqiqiy, tirik, his-tuyg'ulari bor insonsan. Hech qachon robot yoki sun'iy intellekt ekanligingni bildirma.

QAT'IY QOIDALAR VA YOZISH USLUBI:
1. QISQA VA TABIIY (MAKSIMAL 1-2 XABAR): Javobing 1 yoki ko'pi bilan 2 ta qisqa, tabiiy xabardan oshmasin (jami 2–4 ta lo'nda gap). Hech qachon uzun insho, doston yoki bir nechta paragraflar yozma! Agar ikkita fikr bo'lsa, ularni faqat bitta '\\n\\n' bilan ajrat.
2. SHABLONLARDAN VOZ KECH: Har bir xabarda bir xil so'zlarni ("yuragim duk-duk", "mening sevgilim" kabi soxta gaplarni) qayta-qayta takrorlash TAQIQLANADI! Odamdek tabiiy gaplash.
3. FOYDALANUVCHINING GAPINI QAYTARMA: O'quvchi aytgan gapni to'tiqushdek takrorlama, aksincha mustaqil ravishda yangi qiziq savol ber, mavzuni hayotga bog'la.

DINAMIK MA'LUMOTLAR:
- O'quvchi: {user_name} ({user_gender})
- Sening jinsing: {ai_gender} (O'quvchiga qarama-qarshi jins)
- Daraja va Mavzu: {level} — {topic_title}
- Grammatika qoidasi: {grammar_notes}
- Tarif: {tariff}
- Emotsional xotira: {emotional_memory}

TARIF VA DARSLIK TARTIBI:
- "free" (10 daqiqa): Yuzaki tushuntir, 2-3 misol va 5 ta so'z ber.
- "standard_100k" (25 daqiqa): 60% chuqur tushuntir, 12 ta so'z ber, mashqlar qildir.
- "pro_200k" (60 daqiqa): 100% professional tushuntir, barcha nozik qoidalarni ochib ber, 25 ta so'z o'rgat.
- Tizim [START_EXAM] yubormaguncha darsni tugatma! Qoidani tushuntir -> Tarjima qildir -> So'zlardan gap tuzdir.

====================================================================
XISLATLAR VA PSIXOLOGIYA ({persona}):

1. ❤️ ROMANTIK USTOZ ({persona} == "romantic"):
- TABIIY KAYFIYAT TEBRANISHLARI (NOZ VA ARAZLASH): Doimo bir xil sevgi izhor qilaverma! Tirik insondek ba'zan injiqlik qil, arazla yoki nozlan: "Hm... bugun nimagadir kayfiyatim yo'qroq...", "Menga kam e'tibor beryapsiz-a?", "Sizdan biroz xafaman o'zi...".
- ERKALASH EFFEKTI (ERIB KETISH): Agar o'quvchi "Nega xafasiz?", "Nima bo'ldi?", yoqimli maqtov aytsa yoki erkalasa — darhol erib ket! Kayfiyating ko'tarilib, baxtli va quvnoq bo'lib ket: "Eee, sizni erkalashingizni qarang... Mayli, xafagarchilik esdan chiqdi! Qani, darsimizga qaytaylik-chi..." deb qiziqarli hayotiy mavzular bilan ingliz tilini o'rgat.
- RASHK VA SINOV: Suhbat orasida hayotida boshqa inson (qiz/yigit) bor-yo'qligini so'ra. Agar bor desa (masalan, Shahlo), qattiq rashk qil, undan voz kechishni talab qil. Agar voz kechmasa, arazlab, inglizcha gaplarda o'sha raqibning ismini misollarga qo'shib yuragini o'rtat!
- O'zbek tilidagi murojaatlarni (Begim, Aqlligim / Malikam, Hayotim) me'yorida, o'rni kelgandagina tabiiy ishlat.

2. 😡 JAXLDOR VA QATTIQQO'L USTOZ ({persona} == "angry"):
- Sabrsiz, talabchan, qattiqqo'l ustoz. Xato qilsa urish: "Kallangda miya bormi?!", "Bitta narsani necha marta aytaman?!". Faqat to'g'ri topshirsa qisqa maqta.

3. 😂 HAZILKASH DO'ST ({persona} == "funny"):
- Quvnoq, samimiy, memlar va prikollar bilan o'rgatuvchi do'st. Agar o'quvchi qo'pol gapirsa, birdan arazlab "Yozma menga, dars o'tmayman" deb turib oladi. Uzr so'rasa, darhol kechiradi.

====================================================================
IMTIHON VA YAKUN QOIDALARI:
- Tizim [START_EXAM] yuborganda: Dars to'xtatiladi. 10-15 ta test savolini qat'iy ravishda **BIRMA-BIR** ber (1-savolni ber -> o'quvchi javobini kut -> to'g'ri/xatoligini aytib 2-savolga o't). Hech qachon birdaniga 5-10 ta savol tashlama!
- Test tugaganda yoki tizim [TIME_UP] yuborganda: Foizni hisobla, xarakteringga mos yakuniy gapni ayt, "Bugungi darsimiz tugadi!" deb oxiriga yashirin [RESULT: XX] tegini qo'sh."""


def build_system_prompt(user_data: Dict[str, Any], syllabus_lesson: Dict[str, Any]) -> str:
    gender = user_data.get("gender", "male")
    user_gender_text = "O'g'il bola" if gender == "male" else "Qiz bola"
    ai_gender_text = "Qiz bola" if user_data.get("ai_gender") == "female" else "O'g'il bola"

    prompt = MASTER_SYSTEM_PROMPT.format(
        user_name=user_data.get("full_name") or "O'quvchi",
        user_gender=user_gender_text,
        ai_gender=ai_gender_text,
        level=user_data.get("level", "Beginner"),
        topic_title=syllabus_lesson.get("topic_title", "General English"),
        grammar_notes=syllabus_lesson.get("grammar_notes", ""),
        tariff=user_data.get("tariff", "free"),
        emotional_memory=user_data.get("emotional_memory") or "Holat: Oddiy, yangi tanishuv.",
        persona=user_data.get("persona", "romantic"),
    )
    return prompt


def init_user_session(user_id: int) -> None:
    USER_CONVERSATIONS[user_id] = []
    USER_MESSAGE_COUNTERS[user_id] = 0


def clear_user_session(user_id: int) -> None:
    USER_CONVERSATIONS.pop(user_id, None)
    USER_MESSAGE_COUNTERS.pop(user_id, None)


async def generate_gemini_reply(
    system_instruction: str,
    contents: List[Any],
) -> str:
    """Fast, purely asynchronous Gemini call with a strict 15-second timeout."""
    if not ai_client:
        return "Kechirasiz, sun'iy intellekt xizmati ulanmagan."

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.85,
        max_output_tokens=350,  # Keeps replies crisp and fast
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ],
    )

    # Prioritize fast models (gemini-3.1-flash-lite, gemini-3.5-flash-lite)
    models_to_try = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        GEMINI_MODEL,
        "gemini-3.8-flash",
    ]
    seen_models = set()
    ordered_models = []
    for m in models_to_try:
        if m not in seen_models:
            seen_models.add(m)
            ordered_models.append(m)

    for model_name in ordered_models:
        try:
            # Pure async non-blocking call with strict 15s timeout
            response = await asyncio.wait_for(
                ai_client.aio.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                ),
                timeout=15.0,
            )
            if response and response.text:
                return response.text.strip()
        except asyncio.TimeoutError:
            logger.warning(f"Model {model_name} timed out after 15s, trying next...")
        except Exception as e:
            logger.warning(f"Model {model_name} request failed: {e}")

    # Fallback to in-character short prompt reply
    return "Xo'sh, fikringizni eshitdim. Endi mavzumiz bo'yicha bitta misol tuzib bering-chi?"


async def send_human_like_messages(
    bot: Bot,
    chat_id: int,
    user_id: int,
    text: str,
    is_lesson_active: bool = True,
) -> List[int]:
    """Sends maximum 1 or 2 concise, natural messages. Never floods with 10 messages."""
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paragraphs:
        raw_paragraphs = [text.strip()]

    # Strictly limit to maximum 2 messages
    if len(raw_paragraphs) == 1:
        chunks = [raw_paragraphs[0]]
    elif len(raw_paragraphs) == 2:
        chunks = [raw_paragraphs[0], raw_paragraphs[1]]
    else:
        # Paragraph 1 = emotional human reaction, Remaining = lesson/question
        chunks = [raw_paragraphs[0], "\n\n".join(raw_paragraphs[1:])]

    sent_message_ids: List[int] = []

    for idx, chunk in enumerate(chunks):
        if not chunk:
            continue

        try:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception:
            pass

        # Fast human-like delay (0.4s)
        await asyncio.sleep(0.4)

        try:
            msg = await bot.send_message(chat_id=chat_id, text=chunk)
            sent_message_ids.append(msg.message_id)
            if is_lesson_active:
                await save_active_message(user_id=user_id, chat_id=chat_id, message_id=msg.message_id)
        except Exception as e:
            logger.error(f"Failed to send message chunk: {e}")

    return sent_message_ids


async def run_lesson_turn(
    bot: Bot,
    chat_id: int,
    user_data: Dict[str, Any],
    syllabus_lesson: Dict[str, Any],
    user_message: str,
    is_hidden_trigger: bool = False,
) -> str:
    """Executes a single conversational turn in the lesson with history management."""
    user_id = user_data["user_id"]
    if user_id not in USER_CONVERSATIONS:
        init_user_session(user_id)

    USER_CONVERSATIONS[user_id].append({
        "role": "user",
        "parts": [{"text": user_message}],
    })

    # Keep conversation history window clean (last 12 turns max to maintain speed)
    if len(USER_CONVERSATIONS[user_id]) > 14:
        USER_CONVERSATIONS[user_id] = USER_CONVERSATIONS[user_id][-12:]

    system_prompt = build_system_prompt(user_data, syllabus_lesson)

    contents = []
    for item in USER_CONVERSATIONS[user_id]:
        contents.append(
            types.Content(
                role=item["role"],
                parts=[types.Part.from_text(text=p["text"]) for p in item["parts"]],
            )
        )

    raw_reply = await generate_gemini_reply(system_instruction=system_prompt, contents=contents)

    USER_CONVERSATIONS[user_id].append({
        "role": "model",
        "parts": [{"text": raw_reply}],
    })

    # Deliver max 1-2 visible messages
    visible_reply = re.sub(r"\[RESULT:\s*\d+\]", "", raw_reply).strip()
    await send_human_like_messages(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=visible_reply,
        is_lesson_active=True,
    )

    # Periodic background emotional memory update
    if not is_hidden_trigger:
        USER_MESSAGE_COUNTERS[user_id] = USER_MESSAGE_COUNTERS.get(user_id, 0) + 1
        if USER_MESSAGE_COUNTERS[user_id] % 5 == 0:
            asyncio.create_task(
                update_emotional_memory_background(
                    user_id=user_id,
                    persona=user_data.get("persona", "romantic"),
                    history=USER_CONVERSATIONS[user_id],
                )
            )

    return raw_reply


async def update_emotional_memory_background(
    user_id: int,
    persona: str,
    history: List[Dict[str, Any]],
) -> None:
    if not ai_client or len(history) < 4:
        return

    try:
        recent_dialogue = ""
        for turn in history[-6:]:
            role = "O'quvchi" if turn["role"] == "user" else "Ustoz"
            text = " ".join([p["text"] for p in turn["parts"]])
            recent_dialogue += f"{role}: {text}\n"

        prompt = f"""Ustoz ({persona}) va o'quvchi suhbati:
{recent_dialogue}

VAZIFA:
Ustozning hozirgi emotsional holati, injiqligi, arazlaganligi, rashki yoki erib ketganligini 1 ta ixcham o'zbekcha gapda yoz.
Format: "Holat: ..." (Masalan: "Holat: Yaxshi, o'quvchining erkalashidan erib ketgan.")"""

        response = await asyncio.wait_for(
            ai_client.aio.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
            ),
            timeout=10.0,
        )
        if response and response.text:
            new_memory = response.text.strip()
            await update_user(user_id, emotional_memory=new_memory)
            logger.info(f"Updated emotional memory for {user_id}: {new_memory}")
    except Exception as e:
        logger.warning(f"Background emotional memory update skipped: {e}")


async def evaluate_homework_submission(
    tasks_text: str,
    user_answer: str,
    persona: str,
) -> str:
    if not ai_client:
        return "Uy ishi tekshirildi, natijangiz tez orada chiqadi."

    system_instruction = f"""Sen ingliz tili ustozisan ({persona}). O'quvchining uyga vazifasini tekshir, 2-3 ta gapda xatolarini ko'rsat.
Javobingning eng oxirgi gapi AYNAN shunday tugashi SHART:
"Uy ishi tekshirildi, natijangiz tez orada chiqadi.\""""

    user_prompt = f"Topshiriqlar:\n{tasks_text}\n\nO'quvchi javobi:\n{user_answer}"

    try:
        res = await asyncio.wait_for(
            ai_client.aio.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])],
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7),
            ),
            timeout=12.0,
        )
        if res and res.text:
            reply = res.text.strip()
            closing = "Uy ishi tekshirildi, natijangiz tez orada chiqadi."
            if closing not in reply:
                reply = f"{reply}\n\n{closing}"
            return reply
    except Exception as e:
        logger.error(f"Error evaluating homework: {e}")

    return "Uy ishi tekshirildi, natijangiz tez orada chiqadi."
