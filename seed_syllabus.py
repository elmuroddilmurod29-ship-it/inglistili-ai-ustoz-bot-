import asyncio
import logging
from database import add_syllabus_lesson, init_db, count_syllabus_lessons

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Complete structured curriculum data for all 6 levels (10 rich lessons each, 25 word pairs each = 1,500 words)

SYLLABUS_DATA = [
    # =========================================================================
    # 1. BEGINNER (A1)
    # =========================================================================
    {
        "level": "Beginner",
        "lesson_order": 1,
        "topic_title": "To Be fe'li (am, is, are) va Shaxs olmoshlari",
        "grammar_notes": "To be fe'li 'bo'lmoq' ma'nosini bildiradi. I -> am, He/She/It -> is, We/You/They -> are bilan ishlatiladi. Masalan: I am a student. He is a teacher. They are friends. Inkor shaklida 'not' qo'shiladi: I am not tired.",
        "target_words": [
            {"en": "hello", "uz": "salom"}, {"en": "name", "uz": "ism"}, {"en": "student", "uz": "talaba"},
            {"en": "teacher", "uz": "o'qituvchi"}, {"en": "friend", "uz": "do'st"}, {"en": "family", "uz": "oila"},
            {"en": "father", "uz": "ota"}, {"en": "mother", "uz": "ona"}, {"en": "brother", "uz": "aka-uka"},
            {"en": "sister", "uz": "opa-singil"}, {"en": "doctor", "uz": "shifokor"}, {"en": "happy", "uz": "baxtli"},
            {"en": "tired", "uz": "charchagan"}, {"en": "hungry", "uz": "och"}, {"en": "thirsty", "uz": "chanqagan"},
            {"en": "cold", "uz": "sovuq"}, {"en": "hot", "uz": "issiq"}, {"en": "city", "uz": "shahar"},
            {"en": "country", "uz": "mamlakat"}, {"en": "home", "uz": "uy"}, {"en": "work", "uz": "ish"},
            {"en": "school", "uz": "maktab"}, {"en": "today", "uz": "bugun"}, {"en": "morning", "uz": "tong"},
            {"en": "night", "uz": "tun"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 2,
        "topic_title": "Artikllar: A / An va The",
        "grammar_notes": "A va An noaniq artikllari faqat birlikdagi sanaladigan otlar oldidan keladi. Undosh tovush oldidan 'a' (a book), unli tovush oldidan 'an' (an apple) ishlatiladi. 'The' aniq artikli esa suhbatdoshga ma'lum bo'lgan aniq narsalar uchun ishlatiladi.",
        "target_words": [
            {"en": "book", "uz": "kitob"}, {"en": "apple", "uz": "olma"}, {"en": "pen", "uz": "ruchka"},
            {"en": "pencil", "uz": "qalam"}, {"en": "orange", "uz": "apelsin"}, {"en": "umbrella", "uz": "soyabon"},
            {"en": "bag", "uz": "sumka"}, {"en": "car", "uz": "mashina"}, {"en": "table", "uz": "stol"},
            {"en": "chair", "uz": "stul"}, {"en": "door", "uz": "eshik"}, {"en": "window", "uz": "deraza"},
            {"en": "room", "uz": "xona"}, {"en": "house", "uz": "hovli/uy"}, {"en": "sun", "uz": "quyosh"},
            {"en": "moon", "uz": "oy"}, {"en": "sky", "uz": "osmon"}, {"en": "dog", "uz": "it"},
            {"en": "cat", "uz": "mushuk"}, {"en": "egg", "uz": "tuxum"}, {"en": "ice", "uz": "muz"},
            {"en": "ocean", "uz": "okean"}, {"en": "computer", "uz": "kompyuter"}, {"en": "phone", "uz": "telefon"},
            {"en": "key", "uz": "kalit"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 3,
        "topic_title": "Ko'plik shakli (-s, -es) va Ko'rsatish olmoshlari (This/That/These/Those)",
        "grammar_notes": "Otlar ko'pligi odatda '-s' yoki '-es' qo'shish bilan yasaladi (cat -> cats, box -> boxes). Yaqindagi bitta narsaga 'This', uzoqdagi bitta narsaga 'That'. Yaqindagi ko'p narsalarga 'These', uzoqdagi ko'p narsalarga 'Those' ishlatiladi.",
        "target_words": [
            {"en": "box", "uz": "quti"}, {"en": "watch", "uz": "qo'l soati"}, {"en": "glass", "uz": "stakan"},
            {"en": "bus", "uz": "avtobus"}, {"en": "child", "uz": "bola"}, {"en": "children", "uz": "bolalar"},
            {"en": "man", "uz": "erkak"}, {"en": "men", "uz": "erkaklar"}, {"en": "woman", "uz": "ayol"},
            {"en": "women", "uz": "ayollar"}, {"en": "foot", "uz": "oyoq kafti"}, {"en": "feet", "uz": "oyoqlar"},
            {"en": "tooth", "uz": "tish"}, {"en": "teeth", "uz": "tishlar"}, {"en": "street", "uz": "ko'cha"},
            {"en": "shop", "uz": "do'kon"}, {"en": "picture", "uz": "rasm"}, {"en": "tree", "uz": "daraxt"},
            {"en": "flower", "uz": "gul"}, {"en": "bird", "uz": "qush"}, {"en": "near", "uz": "yaqin"},
            {"en": "far", "uz": "uzoq"}, {"en": "here", "uz": "bu yerda"}, {"en": "there", "uz": "u yerda"},
            {"en": "thing", "uz": "narsa"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 4,
        "topic_title": "Have got / Has got (Egalik ifodalash)",
        "grammar_notes": "Biror narsaga egalikni bildirish uchun I/You/We/They bilan 'have got', He/She/It bilan 'has got' ishlatiladi. Masalan: I have got a car. She has got a blue bag. Inkor: I haven't got, He hasn't got. Savol: Have you got a pen?",
        "target_words": [
            {"en": "have", "uz": "ega bo'lmoq"}, {"en": "money", "uz": "pul"}, {"en": "time", "uz": "vaqt"},
            {"en": "problem", "uz": "muammo"}, {"en": "idea", "uz": "g'oya"}, {"en": "question", "uz": "savol"},
            {"en": "sister", "uz": "singil"}, {"en": "bicycle", "uz": "velosiped"}, {"en": "pet", "uz": "uy hayvoni"},
            {"en": "ticket", "uz": "chipta"}, {"en": "passport", "uz": "pasport"}, {"en": "hair", "uz": "soch"},
            {"en": "eyes", "uz": "ko'zlar"}, {"en": "face", "uz": "yuz"}, {"en": "jacket", "uz": "kurtka"},
            {"en": "shoes", "uz": "poyabzal"}, {"en": "camera", "uz": "kamera"}, {"en": "guitar", "uz": "gitara"},
            {"en": "wallet", "uz": "hamyon"}, {"en": "glasses", "uz": "ko'zoynak"}, {"en": "lesson", "uz": "dars"},
            {"en": "job", "uz": "kasb"}, {"en": "flat", "uz": "kvartira"}, {"en": "garden", "uz": "bog'"},
            {"en": "laptop", "uz": "noutbuk"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 5,
        "topic_title": "Possessive Adjectives (My, Your, His, Her, Our, Their)",
        "grammar_notes": "Egalik sifatlari ot oldidan keladi: my (mening), your (sening/sizning), his (uning - erkak), her (uning - ayol), its (uning - jonsiz/hayvon), our (bizning), their (ularning). Masalan: This is my brother. What is your phone number?",
        "target_words": [
            {"en": "parent", "uz": "ota-ona"}, {"en": "son", "uz": "o'g'il farzand"}, {"en": "daughter", "uz": "qiz farzand"},
            {"en": "wife", "uz": "rafiqasi"}, {"en": "husband", "uz": "eri"}, {"en": "uncle", "uz": "tog'a/amaki"},
            {"en": "aunt", "uz": "xola/amma"}, {"en": "cousin", "uz": "amakivachcha"}, {"en": "address", "uz": "manzil"},
            {"en": "email", "uz": "elektron pochta"}, {"en": "number", "uz": "raqam"}, {"en": "country", "uz": "yurt"},
            {"en": "language", "uz": "til"}, {"en": "hobby", "uz": "qiziqish"}, {"en": "favorite", "uz": "sevimli"},
            {"en": "color", "uz": "rang"}, {"en": "red", "uz": "qizil"}, {"en": "blue", "uz": "ko'k"},
            {"en": "green", "uz": "yashil"}, {"en": "black", "uz": "qora"}, {"en": "white", "uz": "oq"},
            {"en": "yellow", "uz": "sariq"}, {"en": "desk", "uz": "parta"}, {"en": "office", "uz": "idora"},
            {"en": "colleague", "uz": "hamkasb"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 6,
        "topic_title": "Present Simple: I / You / We / They bilan ijobiy va inkor gaplar",
        "grammar_notes": "Present Simple doimiy takrorlanuvchi ish-harakatlar va faktlar uchun ishlatiladi. I/You/We/They uchun asosiy fe'l o'zgarmaydi: I live in Tashkent. They speak English. Inkor shaklda 'do not' (don't) ishlatiladi: We don't smoke.",
        "target_words": [
            {"en": "live", "uz": "yashamoq"}, {"en": "speak", "uz": "gapirmoq"}, {"en": "work", "uz": "ishlamoq"},
            {"en": "study", "uz": "o'qimoq"}, {"en": "play", "uz": "o'ynamoq"}, {"en": "like", "uz": "yoqtirmoq"},
            {"en": "love", "uz": "sevmoq"}, {"en": "eat", "uz": "yemoq"}, {"en": "drink", "uz": "ichmoq"},
            {"en": "coffee", "uz": "qahva"}, {"en": "tea", "uz": "choy"}, {"en": "water", "uz": "suv"},
            {"en": "bread", "uz": "non"}, {"en": "meat", "uz": "go'sht"}, {"en": "breakfast", "uz": "nonushta"},
            {"en": "lunch", "uz": "tushlik"}, {"en": "dinner", "uz": "kechki ovqat"}, {"en": "morning", "uz": "ertalab"},
            {"en": "afternoon", "uz": "tushdan keyin"}, {"en": "evening", "uz": "oqshom"}, {"en": "night", "uz": "kechasi"},
            {"en": "always", "uz": "har doim"}, {"en": "usually", "uz": "odatda"}, {"en": "often", "uz": "tez-tez"},
            {"en": "sometimes", "uz": "ba'zan"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 7,
        "topic_title": "Present Simple: He / She / It va So'roq shakli (Do / Does)",
        "grammar_notes": "He, She, It bilan fe'lga '-s' yoki '-es' qo'shiladi: He works hard. She teaches English. Inkor shaklda 'doesn't' ishlatiladi va fe'ldan -s tushib qoladi: He doesn't know. Savolda Do / Does oldinga chiqadi: Do you speak English? Does she live here?",
        "target_words": [
            {"en": "know", "uz": "bilmoq"}, {"en": "think", "uz": "o'ylamoq"}, {"en": "understand", "uz": "tushunmoq"},
            {"en": "remember", "uz": "eslamoq"}, {"en": "forget", "uz": "unutmoq"}, {"en": "teach", "uz": "o'rgatmoq"},
            {"en": "learn", "uz": "o'rganmoq"}, {"en": "read", "uz": "o'qimoq"}, {"en": "write", "uz": "yozmoq"},
            {"en": "listen", "uz": "tinglamoq"}, {"en": "music", "uz": "musiqa"}, {"en": "news", "uz": "yangiliklar"},
            {"en": "newspaper", "uz": "gazeta"}, {"en": "letter", "uz": "xat"}, {"en": "message", "uz": "xabar"},
            {"en": "help", "uz": "yordam bermoq"}, {"en": "open", "uz": "ochmoq"}, {"en": "close", "uz": "yopmoq"},
            {"en": "start", "uz": "boshlamoq"}, {"en": "finish", "uz": "tugatmoq"}, {"en": "sleep", "uz": "uxlamoq"},
            {"en": "wake up", "uz": "uyg'onmoq"}, {"en": "early", "uz": "erta"}, {"en": "late", "uz": "kech"},
            {"en": "never", "uz": "hech qachon"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 8,
        "topic_title": "Can va Can't (Qobiliyat va Ruxsat)",
        "grammar_notes": "Can jismoniy yoki aqliy qobiliyatni bildiradi. Barcha shaxslar uchun bir xil: I can swim. She can drive. Inkor: cannot / can't: He can't cook. Savol: Can you help me? Javob: Yes, I can / No, I can't.",
        "target_words": [
            {"en": "swim", "uz": "suzmoq"}, {"en": "drive", "uz": "haydamoq"}, {"en": "cook", "uz": "pishirmoq"},
            {"en": "sing", "uz": "kuylamoq"}, {"en": "dance", "uz": "raqsqa tushmoq"}, {"en": "run", "uz": "yugurmoq"},
            {"en": "fast", "uz": "tez"}, {"en": "slowly", "uz": "sekin"}, {"en": "well", "uz": "yaxshi"},
            {"en": "badly", "uz": "yomon"}, {"en": "fluently", "uz": "ravon"}, {"en": "easily", "uz": "osongina"},
            {"en": "difficult", "uz": "qiyin"}, {"en": "easy", "uz": "oson"}, {"en": "ride", "uz": "minmoq"},
            {"en": "horse", "uz": "ot"}, {"en": "fly", "uz": "uchmoq"}, {"en": "plane", "uz": "samolyot"},
            {"en": "chess", "uz": "shaxmat"}, {"en": "football", "uz": "futbol"}, {"en": "repair", "uz": "tuzatmoq"},
            {"en": "draw", "uz": "chizmoq"}, {"en": "paint", "uz": "bo'yamoq"}, {"en": "hear", "uz": "eshitmoq"},
            {"en": "see", "uz": "ko'rmoq"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 9,
        "topic_title": "Vaqt va Soatni aytish (Telling the Time)",
        "grammar_notes": "Vaqtni so'rash: What time is it? Javob: It is 5 o'clock (soat 5). It is half past five (besh yarim). It is a quarter past five (beshdan 15 daqiqa o'tdi). It is a quarter to six (oltiga 15 daqiqa qoldi).",
        "target_words": [
            {"en": "clock", "uz": "soat (devor)"}, {"en": "minute", "uz": "daqiqa"}, {"en": "second", "uz": "soniya"},
            {"en": "hour", "uz": "soat (muddat)"}, {"en": "half", "uz": "yarim"}, {"en": "quarter", "uz": "chorak"},
            {"en": "past", "uz": "o'tdi"}, {"en": "to", "uz": "qoldi"}, {"en": "midnight", "uz": "yarim tun"},
            {"en": "noon", "uz": "peshin"}, {"en": "alarm", "uz": "budilnik"}, {"en": "meeting", "uz": "uchrashuv"},
            {"en": "appointment", "uz": "belgilangan vaqt"}, {"en": "schedule", "uz": "jadval"}, {"en": "calendar", "uz": "taqvim"},
            {"en": "Monday", "uz": "dushanba"}, {"en": "Tuesday", "uz": "seshanba"}, {"en": "Wednesday", "uz": "chorshanba"},
            {"en": "Thursday", "uz": "payshanba"}, {"en": "Friday", "uz": "juma"}, {"en": "Saturday", "uz": "shanba"},
            {"en": "Sunday", "uz": "yakshanba"}, {"en": "weekend", "uz": "dam olish kunlari"}, {"en": "weekday", "uz": "ish kuni"},
            {"en": "month", "uz": "oy"}
        ]
    },
    {
        "level": "Beginner",
        "lesson_order": 10,
        "topic_title": "O'rin-joy va Vaqt predloglari (In, On, At)",
        "grammar_notes": "Vaqt uchun: At aniq soatda (at 5:00, at night); On kunlar va sanalarda (on Monday, on May 5); In oylar, fasllar, yillarda (in May, in summer, in 2026). Joy uchun: At aniq nuqtada (at home, at school); On yuzada (on the table); In ichida (in the room, in Tashkent).",
        "target_words": [
            {"en": "place", "uz": "joy"}, {"en": "corner", "uz": "burchak"}, {"en": "center", "uz": "markaz"},
            {"en": "hospital", "uz": "shifoxona"}, {"en": "bank", "uz": "bank"}, {"en": "station", "uz": "vokzal/bekat"},
            {"en": "airport", "uz": "aeroport"}, {"en": "restaurant", "uz": "restoran"}, {"en": "hotel", "uz": "mehmonxona"},
            {"en": "park", "uz": "xiyobon"}, {"en": "bridge", "uz": "ko'prik"}, {"en": "building", "uz": "bino"},
            {"en": "floor", "uz": "qavat/pol"}, {"en": "wall", "uz": "devor"}, {"en": "ceiling", "uz": "shift"},
            {"en": "kitchen", "uz": "oshxona"}, {"en": "bedroom", "uz": "yotoqxona"}, {"en": "bathroom", "uz": "hammom"},
            {"en": "summer", "uz": "yoz"}, {"en": "winter", "uz": "qish"}, {"en": "spring", "uz": "bahor"},
            {"en": "autumn", "uz": "kuz"}, {"en": "holiday", "uz": "ta'til"}, {"en": "birthday", "uz": "tug'ilgan kun"},
            {"en": "party", "uz": "ziyofat"}
        ]
    },

    # =========================================================================
    # 2. ELEMENTARY (A2)
    # =========================================================================
    {
        "level": "Elementary",
        "lesson_order": 1,
        "topic_title": "Present Continuous (Hozirgi davomli zamon)",
        "grammar_notes": "Ayni paytda sodir bo'layotgan ish-harakat: am/is/are + fe'l-ing. Masalan: I am studying English now. Look! It is raining. Inkor: She isn't watching TV. Savol: What are you doing?",
        "target_words": [
            {"en": "now", "uz": "hozir"}, {"en": "currently", "uz": "ayni damda"}, {"en": "rain", "uz": "yomg'ir yog'moq"},
            {"en": "snow", "uz": "qor yog'moq"}, {"en": "watch", "uz": "tomosha qilmoq"}, {"en": "wait", "uz": "kutmoq"},
            {"en": "call", "uz": "qo'ng'iroq qilmoq"}, {"en": "talk", "uz": "gaplashmoq"}, {"en": "shout", "uz": "baqirmoq"},
            {"en": "laugh", "uz": "kulmoq"}, {"en": "cry", "uz": "yig'lamoq"}, {"en": "smile", "uz": "jilmaymoq"},
            {"en": "walk", "uz": "piyoda yurmoq"}, {"en": "wear", "uz": "kiyib yurmoq"}, {"en": "carry", "uz": "ko'tarib bormoq"},
            {"en": "cook", "uz": "ovqat pishirmoq"}, {"en": "clean", "uz": "tozalamoq"}, {"en": "wash", "uz": "yuvmoq"},
            {"en": "fix", "uz": "tuzatmoq"}, {"en": "travel", "uz": "sayohat qilmoq"}, {"en": "moment", "uz": "lahza"},
            {"en": "noise", "uz": "shovqin"}, {"en": "quiet", "uz": "tinch"}, {"en": "busy", "uz": "band"},
            {"en": "ready", "uz": "tayyor"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 2,
        "topic_title": "Present Simple vs Present Continuous",
        "grammar_notes": "Present Simple doimiy odatlar va qoidalar (I usually drink tea). Present Continuous faqat hozir sodir bo'layotgan vaqtinchalik harakatlar (I am drinking coffee now). Holat fe'llari (love, hate, want, know, understand) -ing olmaydi.",
        "target_words": [
            {"en": "habit", "uz": "odat"}, {"en": "routine", "uz": "kun tartibi"}, {"en": "temporary", "uz": "vaqtinchalik"},
            {"en": "permanent", "uz": "doimiy"}, {"en": "hate", "uz": "nafratlanmoq"}, {"en": "prefer", "uz": "afzal ko'rmoq"},
            {"en": "need", "uz": "muhtoj bo'lmoq"}, {"en": "want", "uz": "xohlamoq"}, {"en": "believe", "uz": "ishonmoq"},
            {"en": "agree", "uz": "rozi bo'lmoq"}, {"en": "disagree", "uz": "qarshi bo'lmoq"}, {"en": "cost", "uz": "narxi turmoq"},
            {"en": "own", "uz": "egalik qilmoq"}, {"en": "seem", "uz": "tuyulmoq"}, {"en": "look like", "uz": "o'xshamoq"},
            {"en": "sound", "uz": "eshitilmoq"}, {"en": "taste", "uz": "ta'mi bo'lmoq"}, {"en": "smell", "uz": "hidi bo'lmoq"},
            {"en": "seldom", "uz": "kamdan-kam"}, {"en": "rarely", "uz": "juda kam"}, {"en": "every day", "uz": "har kuni"},
            {"en": "at present", "uz": "ayni vaqtda"}, {"en": "at the moment", "uz": "shu daqiqada"}, {"en": "currently", "uz": "hozirda"},
            {"en": "fact", "uz": "haqiqat"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 3,
        "topic_title": "Past Simple: Was va Were",
        "grammar_notes": "To be fe'lining o'tgan zamoni: I/He/She/It -> was, We/You/They -> were. Masalan: I was at home yesterday. They were happy. Inkor: wasn't / weren't: She wasn't tired. Savol: Were you in Samarkand last week?",
        "target_words": [
            {"en": "yesterday", "uz": "kecha"}, {"en": "ago", "uz": "avval"}, {"en": "last week", "uz": "o'tgan hafta"},
            {"en": "last year", "uz": "o'tgan yil"}, {"en": "born", "uz": "tug'ilgan"}, {"en": "famous", "uz": "mashhur"},
            {"en": "rich", "uz": "boy"}, {"en": "poor", "uz": "kambag'al"}, {"en": "sick", "uz": "kasal"},
            {"en": "healthy", "uz": "sog'lom"}, {"en": "afraid", "uz": "qo'rqqan"}, {"en": "brave", "uz": "jasur"},
            {"en": "alone", "uz": "yolg'iz"}, {"en": "together", "uz": "birga"}, {"en": "childhood", "uz": "bolalik"},
            {"en": "history", "uz": "tarix"}, {"en": "ancient", "uz": "qadimiy"}, {"en": "past", "uz": "o'tmish"},
            {"en": "present", "uz": "hozirgi vaqt"}, {"en": "future", "uz": "kelajak"}, {"en": "weather", "uz": "ob-havo"},
            {"en": "sunny", "uz": "quyoshli"}, {"en": "cloudy", "uz": "bulutli"}, {"en": "windy", "uz": "shamolli"},
            {"en": "storm", "uz": "bo'ron"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 4,
        "topic_title": "Past Simple: To'g'ri fe'llar (-ed)",
        "grammar_notes": "To'g'ri fe'llarning o'tgan zamoni fe'lga '-ed' qo'shish bilan yasaladi (play -> played, watch -> watched, live -> lived). Talaffuz qoidalari: /t/, /d/, /id/. Inkor va so'roqda 'did / didn't' ishlatiladi va fe'l asosiy holiga qaytadi.",
        "target_words": [
            {"en": "arrived", "uz": "yetib keldi"}, {"en": "visited", "uz": "tashrif buyurdi"}, {"en": "started", "uz": "boshladi"},
            {"en": "invited", "uz": "taklif qildi"}, {"en": "decided", "uz": "qaror qildi"}, {"en": "stopped", "uz": "to'xtadi"},
            {"en": "planned", "uz": "rejalashtirdi"}, {"en": "passed", "uz": "o'tdi/topshirdi"}, {"en": "failed", "uz": "yiqildi"},
            {"en": "married", "uz": "turmush qurdi"}, {"en": "opened", "uz": "ochdi"}, {"en": "closed", "uz": "yopdi"},
            {"en": "looked", "uz": "qaradi"}, {"en": "asked", "uz": "so'radi"}, {"en": "answered", "uz": "javob berdi"},
            {"en": "returned", "uz": "qaytdi"}, {"en": "changed", "uz": "o'zgartirdi"}, {"en": "happen", "uz": "sodir bo'lmoq"},
            {"en": "remembered", "uz": "esladi"}, {"en": "forgot", "uz": "unutdi"}, {"en": "enjoyed", "uz": "rohatlandi"},
            {"en": "walked", "uz": "yurdi"}, {"en": "waited", "uz": "kutdi"}, {"en": "called", "uz": "qo'ng'iroq qildi"},
            {"en": "cleaned", "uz": "tozaladi"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 5,
        "topic_title": "Past Simple: Noto'g'ri fe'llar (Irregular Verbs) va Did",
        "grammar_notes": "Noto'g'ri fe'llar o'tgan zamonda ildizidan o'zgaradi (go -> went, see -> saw, buy -> bought). Inkor: didn't + V1 (I didn't buy). So'roq: Did + ega + V1? (Did you see that?).",
        "target_words": [
            {"en": "went", "uz": "bordi"}, {"en": "saw", "uz": "ko'rdi"}, {"en": "bought", "uz": "sotib oldi"},
            {"en": "sold", "uz": "sotdi"}, {"en": "made", "uz": "yasadi/qildi"}, {"en": "took", "uz": "oldi"},
            {"en": "gave", "uz": "berdi"}, {"en": "came", "uz": "keldi"}, {"en": "found", "uz": "topdi"},
            {"en": "lost", "uz": "yo'qotdi"}, {"en": "felt", "uz": "his qildi"}, {"en": "told", "uz": "aytdi"},
            {"en": "said", "uz": "dedi"}, {"en": "knew", "uz": "bildi"}, {"en": "thought", "uz": "o'yladi"},
            {"en": "wrote", "uz": "yozdi"}, {"en": "read", "uz": "o'qidi (o'tgan)"}, {"en": "ate", "uz": "yedi"},
            {"en": "drank", "uz": "ichdi"}, {"en": "spoke", "uz": "gapirdi"}, {"en": "met", "uz": "uchratdi"},
            {"en": "left", "uz": "tark etdi"}, {"en": "broke", "uz": "sindirdi"}, {"en": "heard", "uz": "eshitdi"},
            {"en": "paid", "uz": "to'ladi"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 6,
        "topic_title": "There is / There are va Some / Any",
        "grammar_notes": "Biror joyda bir narsa borligini bildirish: There is a book on the desk. There are three pens. Some ijobiy gaplarda (I have some apples). Any inkor va so'roq gaplarda (I don't have any apples. Do you have any milk?).",
        "target_words": [
            {"en": "some", "uz": "bir nechta / biroz"}, {"en": "any", "uz": "hech qanday / biron"}, {"en": "milk", "uz": "sut"},
            {"en": "sugar", "uz": "shakar"}, {"en": "salt", "uz": "tuz"}, {"en": "butter", "uz": "sariyog'"},
            {"en": "cheese", "uz": "pishloq"}, {"en": "cup", "uz": "finjon"}, {"en": "bottle", "uz": "shisha idish"},
            {"en": "plate", "uz": "tarelka"}, {"en": "spoon", "uz": "qoshiq"}, {"en": "fork", "uz": "vilka"},
            {"en": "knife", "uz": "pichoq"}, {"en": "fridge", "uz": "muzlatgich"}, {"en": "shelf", "uz": "javon"},
            {"en": "market", "uz": "bozor"}, {"en": "supermarket", "uz": "supermarket"}, {"en": "bakery", "uz": "novvoyxona"},
            {"en": "price", "uz": "narx"}, {"en": "cheap", "uz": "arzon"}, {"en": "expensive", "uz": "qimmat"},
            {"en": "free", "uz": "bepul/ozod"}, {"en": "item", "uz": "buyum"}, {"en": "piece", "uz": "bo'lak"},
            {"en": "slice", "uz": "tilim"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 7,
        "topic_title": "Countable vs Uncountable Nouns (Much, Many, A lot of)",
        "grammar_notes": "Sanaladigan otlar (Many apples). Sanalmaydigan otlar (Much water). A lot of har ikkalasi bilan ijobiy gaplarda ishlatiladi (A lot of books, a lot of time). How much? (Qancha?) narx va sanalmaydigan otlarga, How many? (Nechta?) sanaladigan otlarga.",
        "target_words": [
            {"en": "much", "uz": "ko'p (sanalmaydigan)"}, {"en": "many", "uz": "ko'p (sanaladigan)"}, {"en": "a lot of", "uz": "juda ko'p"},
            {"en": "little", "uz": "kam (sanalmaydigan)"}, {"en": "few", "uz": "kam (sanaladigan)"}, {"en": "juice", "uz": "sharbat"},
            {"en": "oil", "uz": "yog'"}, {"en": "rice", "uz": "guruch"}, {"en": "flour", "uz": "un"},
            {"en": "traffic", "uz": "tirbandlik"}, {"en": "information", "uz": "ma'lumot"}, {"en": "advice", "uz": "maslahat"},
            {"en": "furniture", "uz": "mebel"}, {"en": "luggage", "uz": "yuk"}, {"en": "passenger", "uz": "yo'lovchi"},
            {"en": "coin", "uz": "tanga"}, {"en": "dollar", "uz": "dollar"}, {"en": "bottle", "uz": "shisha"},
            {"en": "glass", "uz": "stakan"}, {"en": "box", "uz": "quti"}, {"en": "packet", "uz": "paket"},
            {"en": "enough", "uz": "yetarli"}, {"en": "extra", "uz": "qo'shimcha"}, {"en": "total", "uz": "jami"},
            {"en": "amount", "uz": "miqdor"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 8,
        "topic_title": "Sifatlarning qiyosiy darajasi (Comparative Adjectives)",
        "grammar_notes": "Qisqa sifatlarga '-er' qo'shiladi: fast -> faster, tall -> taller. Uzun sifatlar oldidan 'more' qo'yiladi: expensive -> more expensive. Taqqoslash uchun 'than' (qaraganda) ishlatiladi: English is easier than Chinese. Noto'g'ri: good -> better, bad -> worse.",
        "target_words": [
            {"en": "taller", "uz": "balandroq"}, {"en": "shorter", "uz": "pastroq/qisqaroq"}, {"en": "faster", "uz": "tezroq"},
            {"en": "slower", "uz": "sekinroq"}, {"en": "older", "uz": "yoshi kattaroq"}, {"en": "younger", "uz": "yoshroq"},
            {"en": "better", "uz": "yaxshiroq"}, {"en": "worse", "uz": "yomonroq"}, {"en": "farther", "uz": "uzoqroq"},
            {"en": "more interesting", "uz": "qiziqarliroq"}, {"en": "more dangerous", "uz": "xavfliroq"},
            {"en": "safer", "uz": "xavfsizroq"}, {"en": "easier", "uz": "osonroq"}, {"en": "harder", "uz": "qiyinroq"},
            {"en": "heavier", "uz": "og'irroq"}, {"en": "lighter", "uz": "yengilroq"}, {"en": "cleaner", "uz": "tozaroq"},
            {"en": "dirtier", "uz": "iflosroq"}, {"en": "colder", "uz": "sovuqroq"}, {"en": "warmer", "uz": "iliqroq"},
            {"en": "stronger", "uz": "kuchliroq"}, {"en": "weaker", "uz": "kuchsizroq"}, {"en": "than", "uz": "qaraganda"},
            {"en": "compare", "uz": "taqqoslamoq"}, {"en": "difference", "uz": "farq"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 9,
        "topic_title": "Sifatlarning orttirma darajasi (Superlative Adjectives)",
        "grammar_notes": "Eng yuqori daraja: The + sifat + -est (the fastest, the tallest). Uzun sifatlarda: The most + sifat (the most beautiful). Noto'g'ri: the best (eng yaxshi), the worst (eng yomon). Masalan: Everest is the highest mountain in the world.",
        "target_words": [
            {"en": "highest", "uz": "eng baland"}, {"en": "lowest", "uz": "eng past"}, {"en": "deepest", "uz": "eng chuqur"},
            {"en": "longest", "uz": "eng uzun"}, {"en": "shortest", "uz": "eng qisqa"}, {"en": "brightest", "uz": "eng yorqin"},
            {"en": "darkest", "uz": "eng qorong'i"}, {"en": "wisest", "uz": "eng dono"}, {"en": "kindest", "uz": "eng mehribon"},
            {"en": "most famous", "uz": "eng mashhur"}, {"en": "most popular", "uz": "eng ommabop"},
            {"en": "most modern", "uz": "eng zamonaviy"}, {"en": "most crowded", "uz": "eng gavjum"},
            {"en": "most peaceful", "uz": "eng tinch"}, {"en": "world", "uz": "dunyo"}, {"en": "country", "uz": "mamlakat"},
            {"en": "planet", "uz": "sayyora"}, {"en": "mountain", "uz": "tog'"}, {"en": "river", "uz": "daryo"},
            {"en": "lake", "uz": "ko'l"}, {"en": "sea", "uz": "dengiz"}, {"en": "desert", "uz": "cho'l"},
            {"en": "forest", "uz": "o'rmon"}, {"en": "island", "uz": "orol"}, {"en": "nature", "uz": "tabiat"}
        ]
    },
    {
        "level": "Elementary",
        "lesson_order": 10,
        "topic_title": "Future Simple: Will va Won't",
        "grammar_notes": "Kelasi zamon kutilmagan qarorlar, va'dalar va bashoratlar uchun: Will + V1. Inkor: will not -> won't. Masalan: I will help you tomorrow. I won't tell anyone your secret. Savol: Will you come to the party?",
        "target_words": [
            {"en": "tomorrow", "uz": "ertaga"}, {"en": "next week", "uz": "keyingi hafta"}, {"en": "next year", "uz": "kelasi yil"},
            {"en": "soon", "uz": "tez orada"}, {"en": "promise", "uz": "va'da bermoq"}, {"en": "hope", "uz": "umid qilmoq"},
            {"en": "expect", "uz": "kutmoq/umid qilmoq"}, {"en": "predict", "uz": "bashorat qilmoq"}, {"en": "future", "uz": "kelajak"},
            {"en": "decision", "uz": "qaror"}, {"en": "perhaps", "uz": "ehtimol"}, {"en": "maybe", "uz": "balki"},
            {"en": "probably", "uz": "ehtimolki"}, {"en": "certainly", "uz": "albatta"}, {"en": "sure", "uz": "ishonchi komil"},
            {"en": "secret", "uz": "sir"}, {"en": "dream", "uz": "orzu"}, {"en": "goal", "uz": "maqsad"},
            {"en": "plan", "uz": "reja"}, {"en": "succeed", "uz": "muvaffaqiyatga erishmoq"}, {"en": "graduate", "uz": "bitirmoq"},
            {"en": "win", "uz": "yutmoq"}, {"en": "lose", "uz": "yutqazmoq"}, {"en": "pass", "uz": "muvaffaqiyatli topshirmoq"},
            {"en": "score", "uz": "ball/ochko"}
        ]
    },

    # =========================================================================
    # 3. PRE-INTERMEDIATE (B1)
    # =========================================================================
    {
        "level": "Pre-Intermediate",
        "lesson_order": 1,
        "topic_title": "Be going to vs Will (Kelasi zamon farqlari)",
        "grammar_notes": "Oldindan tuzilgan aniq rejalar va dalilga asoslangan bashoratlar uchun 'be going to' (I am going to visit my granny. Look at clouds, it's going to rain). Kutilmagan lahzaviy qarorlar va shaxsiy fikrlar uchun 'will' (The phone is ringing, I'll answer it).",
        "target_words": [
            {"en": "intention", "uz": "maqsad/niyat"}, {"en": "arrangement", "uz": "kelishuv"}, {"en": "spontaneous", "uz": "kutilmagan/o'z-o'zidan"},
            {"en": "evidence", "uz": "dalil/isbot"}, {"en": "cloud", "uz": "bulut"}, {"en": "threat", "uz": "tahdid"},
            {"en": "offer", "uz": "taklif"}, {"en": "refusal", "uz": "rad etish"}, {"en": "warning", "uz": "ogohlantirish"},
            {"en": "ticket", "uz": "chipta"}, {"en": "flight", "uz": "parvoz"}, {"en": "journey", "uz": "sayr/safar"},
            {"en": "pack", "uz": "joylamoq (chamadon)"}, {"en": "luggage", "uz": "yuk"}, {"en": "passport", "uz": "pasport"},
            {"en": "visa", "uz": "viza"}, {"en": "hotel", "uz": "mehmonxona"}, {"en": "reserve", "uz": "band qilmoq"},
            {"en": "book", "uz": "buyurtma qilmoq"}, {"en": "cancel", "uz": "bekor qilmoq"}, {"en": "confirm", "uz": "tasdiqlamoq"},
            {"en": "delay", "uz": "kechiktirmoq"}, {"en": "depart", "uz": "jo'namoq"}, {"en": "arrive", "uz": "yetib kelmoq"},
            {"en": "destination", "uz": "manzil"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 2,
        "topic_title": "Present Perfect: Have/Has + V3 (Hayotiy tajriba)",
        "grammar_notes": "Present Perfect o'tmishda sodir bo'lgan, lekin vaqti noma'lum yoki natijasi hozirgi zamon bilan bog'liq harakatlar: have/has + V3 (Past Participle). Kalit so'zlar: ever, never, already, yet, just. Masalan: Have you ever been to London? I have just eaten lunch.",
        "target_words": [
            {"en": "already", "uz": "allaqachon"}, {"en": "yet", "uz": "hali (inkor/so'roq)"}, {"en": "just", "uz": "hozirgina"},
            {"en": "ever", "uz": "umringizda/hech"}, {"en": "never", "uz": "hech qachon"}, {"en": "experience", "uz": "tajriba"},
            {"en": "result", "uz": "natija"}, {"en": "achieve", "uz": "erishmoq"}, {"en": "accomplish", "uz": "bajarmoq"},
            {"en": "lose", "uz": "yo'qotmoq"}, {"en": "find", "uz": "topmoq"}, {"en": "discover", "uz": "kashf qilmoq"},
            {"en": "invent", "uz": "ixtiro qilmoq"}, {"en": "repair", "uz": "ta'mirlamoq"}, {"en": "break", "uz": "sindirmoq"},
            {"en": "visit", "uz": "ziyorat qilmoq"}, {"en": "see", "uz": "ko'rmoq"}, {"en": "try", "uz": "tatib/sinab ko'rmoq"},
            {"en": "climb", "uz": "tirmashib chiqmoq"}, {"en": "dive", "uz": "sho'ng'imoq"}, {"en": "sail", "uz": "suzib yurmoq"},
            {"en": "change", "uz": "o'zgarmoq"}, {"en": "improve", "uz": "yaxshilanmoq"}, {"en": "grow", "uz": "o'smoq"},
            {"en": "recently", "uz": "yaqinda"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 3,
        "topic_title": "Present Perfect vs Past Simple",
        "grammar_notes": "Past Simple aniq vaqtni talab qiladi (yesterday, in 2020, two days ago): I visited Paris in 2019. Present Perfect esa aniq vaqtni aytmaydi, tajriba va natijaga urg'u beradi: I have visited Paris twice. Did you see...? vs Have you seen...?",
        "target_words": [
            {"en": "specific", "uz": "aniq"}, {"en": "indefinite", "uz": "noaniq"}, {"en": "period", "uz": "davr"},
            {"en": "century", "uz": "asr"}, {"en": "decade", "uz": "o'n yillik"}, {"en": "childhood", "uz": "bolalik"},
            {"en": "youth", "uz": "yoshlik"}, {"en": "opportunity", "uz": "imkoniyat"}, {"en": "career", "uz": "martaba"},
            {"en": "profession", "uz": "kasb"}, {"en": "qualification", "uz": "malaka"}, {"en": "resume", "uz": "rezyume"},
            {"en": "interview", "uz": "suhbat"}, {"en": "hire", "uz": "ishga olmoq"}, {"en": "fire", "uz": "ishdan bo'shatmoq"},
            {"en": "quit", "uz": "tashlab ketmoq"}, {"en": "apply", "uz": "ariza topshirmoq"}, {"en": "position", "uz": "lavozim"},
            {"en": "salary", "uz": "oylik maosh"}, {"en": "bonus", "uz": "mukofot puli"}, {"en": "promotion", "uz": "lavozim ko'tarilishi"},
            {"en": "retire", "uz": "nafaqaga chiqmoq"}, {"en": "previous", "uz": "avvalgi"}, {"en": "current", "uz": "joriy"},
            {"en": "lifelong", "uz": "umrbod"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 4,
        "topic_title": "For va Since (Present Perfect bilan)",
        "grammar_notes": "'Since' ish-harakatning boshlangan vaqt nuqtasini ko'rsatadi (since Monday, since 2015, since I was a child). 'For' ish-harakatning umumiy davomiyligini bildiradi (for 5 years, for two hours, for a long time). Masalan: I have lived here for 10 years.",
        "target_words": [
            {"en": "duration", "uz": "davomiylik"}, {"en": "beginning", "uz": "boshlanish"}, {"en": "continuation", "uz": "davom etish"},
            {"en": "century", "uz": "asr"}, {"en": "moment", "uz": "lahza"}, {"en": "childhood", "uz": "bolalik"},
            {"en": "graduation", "uz": "bitiruv"}, {"en": "marriage", "uz": "nikoh"}, {"en": "anniversary", "uz": "yillik to'y"},
            {"en": "generation", "uz": "avlod"}, {"en": "tradition", "uz": "an'ana"}, {"en": "custom", "uz": "urf-odat"},
            {"en": "friendship", "uz": "do'stlik"}, {"en": "relationship", "uz": "munosabat"}, {"en": "trust", "uz": "ishonch"},
            {"en": "faith", "uz": "e'tiqod"}, {"en": "patience", "uz": "sabr"}, {"en": "effort", "uz": "harakat/sa'y"},
            {"en": "struggle", "uz": "kurash"}, {"en": "success", "uz": "muvaffaqiyat"}, {"en": "failure", "uz": "mag'lubiyat"},
            {"en": "knowledge", "uz": "bilim"}, {"en": "skill", "uz": "ko'nikma"}, {"en": "ability", "uz": "qobiliyat"},
            {"en": "mastery", "uz": "mahorat"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 5,
        "topic_title": "Modals of Obligation: Must, Have to, Should",
        "grammar_notes": "Must — qat'iy shaxsiy majburiyat yoki qonun-qoida (You must wear a seatbelt). Have to — tashqi vaziyat taqozosi bo'lgan majburiyat (I have to get up at 6 AM). Should — maslahat (You should see a doctor). Inkor: mustn't (qat'iy taqiq), don't have to (majbur emassan).",
        "target_words": [
            {"en": "obligation", "uz": "majburiyat"}, {"en": "duty", "uz": "burch"}, {"en": "rule", "uz": "qoida"},
            {"en": "law", "uz": "qonun"}, {"en": "prohibition", "uz": "taqiq"}, {"en": "permission", "uz": "ruxsat"},
            {"en": "advice", "uz": "maslahat"}, {"en": "suggestion", "uz": "taklif"}, {"en": "recommend", "uz": "tavsiya qilmoq"},
            {"en": "warn", "uz": "ogohlantirmoq"}, {"en": "obey", "uz": "bo'ysunmoq"}, {"en": "violate", "uz": "buzmoq (qoidani)"},
            {"en": "fine", "uz": "jarima"}, {"en": "punishment", "uz": "jazo"}, {"en": "responsibility", "uz": "mas'uliyat"},
            {"en": "necessary", "uz": "zarur"}, {"en": "mandatory", "uz": "majburiy"}, {"en": "optional", "uz": "ixtiyoriy"},
            {"en": "urgent", "uz": "shoshilinch"}, {"en": "essential", "uz": "muhim"}, {"en": "safety", "uz": "xavfsizlik"},
            {"en": "danger", "uz": "xavf"}, {"en": "seatbelt", "uz": "xavfsizlik kamari"}, {"en": "helmet", "uz": "shlem"},
            {"en": "license", "uz": "guvohnoma"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 6,
        "topic_title": "Zero and First Conditional (Haqiqiy shart gaplar)",
        "grammar_notes": "Zero Conditional umumiy haqiqat va qonunlar uchun: If + Present Simple, Present Simple (If you heat water to 100 degrees, it boils). First Conditional kelajakdagi real ehtimol: If + Present Simple, will + V1 (If it rains tomorrow, we will stay at home).",
        "target_words": [
            {"en": "condition", "uz": "shart"}, {"en": "consequence", "uz": "oqibat"}, {"en": "possibility", "uz": "ehtimollik"},
            {"en": "heat", "uz": "qizdirmoq"}, {"en": "freeze", "uz": "muzlatmoq"}, {"en": "melt", "uz": "erimoq"},
            {"en": "boil", "uz": "qaynamoq"}, {"en": "burn", "uz": "yonmoq/kuymoq"}, {"en": "gravity", "uz": "tortishish kuchi"},
            {"en": "weather", "uz": "ob-havo"}, {"en": "forecast", "uz": "ob-havo ma'lumoti"}, {"en": "temperature", "uz": "harorat"},
            {"en": "stormy", "uz": "bo'ronli"}, {"en": "raincoat", "uz": "yomg'irpo'sh"}, {"en": "catch", "uz": "ushlamoq/tutmoq"},
            {"en": "miss", "uz": "o'tkazib yubormoq"}, {"en": "traffic jam", "uz": "tirbandlik"}, {"en": "hurry", "uz": "shoshilmoq"},
            {"en": "rush", "uz": "yugurmoq/shoshmoq"}, {"en": "accident", "uz": "baxtsiz hodisa"}, {"en": "prevent", "uz": "oldini olmoq"},
            {"en": "avoid", "uz": "chetlab o'tmoq"}, {"en": "escape", "uz": "qochib qutulmoq"}, {"en": "protect", "uz": "himoya qilmoq"},
            {"en": "secure", "uz": "xavfsiz holga keltirmoq"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 7,
        "topic_title": "Past Continuous (O'tgan davomli zamon: Was/Were + V-ing)",
        "grammar_notes": "O'tmishda ma'lum bir aniq vaqtda davom etayotgan harakat: was/were + V-ing. Masalan: At 8 PM yesterday, I was watching a movie. They were playing football when it started raining.",
        "target_words": [
            {"en": "interruption", "uz": "uzilish/xalaqit"}, {"en": "simultaneous", "uz": "bir vaqtda bo'ladigan"},
            {"en": "background", "uz": "orqa fon"}, {"en": "shine", "uz": "porlamoq"}, {"en": "blow", "uz": "esmoq (shamol)"},
            {"en": "ring", "uz": "jiringlamoq"}, {"en": "drop", "uz": "tushirib yubormoq"}, {"en": "fall", "uz": "yiqilmoq"},
            {"en": "slip", "uz": "sirpanib ketmoq"}, {"en": "crash", "uz": "to'qnashmoq"}, {"en": "scream", "uz": "qichqirmoq"},
            {"en": "whisper", "uz": "pichirlamoq"}, {"en": "wander", "uz": "kezib yurmoq"}, {"en": "chase", "uz": "quvmoq"},
            {"en": "hide", "uz": "yashirinmoq"}, {"en": "shadow", "uz": "soya"}, {"en": "darkness", "uz": "qorong'ilik"},
            {"en": "candle", "uz": "sham"}, {"en": "flashlight", "uz": "fonar"}, {"en": "suddenly", "uz": "to'satdan"},
            {"en": "meanwhile", "uz": "shu vaqtda"}, {"en": "during", "uz": "davomida"}, {"en": "throughout", "uz": "bo'ylab/mobaynida"},
            {"en": "disturb", "uz": "bezovta qilmoq"}, {"en": "bother", "uz": "tashvishga solmoq"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 8,
        "topic_title": "When va While (Past Continuous vs Past Simple)",
        "grammar_notes": "O'tmishda uzun davom etayotgan harakat (Past Continuous) qisqa bir harakat bilan (Past Simple) bo'linib qolsa: While I was cooking, the phone rang. When he arrived, we were having dinner. While odatda continuous bilan, When odatda simple bilan keladi.",
        "target_words": [
            {"en": "overlap", "uz": "ustma-ust tushmoq"}, {"en": "coincidence", "uz": "tasodif"}, {"en": "unexpected", "uz": "kutilmagan"},
            {"en": "interrupt", "uz": "bo'lib qo'ymoq"}, {"en": "distract", "uz": "chalg'itmoq"}, {"en": "focus", "uz": "diqqatni qaratmoq"},
            {"en": "concentrate", "uz": "jamlamoq"}, {"en": "notice", "uz": "payqamoq"}, {"en": "realize", "uz": "anglab yetmoq"},
            {"en": "observe", "uz": "kuzatmoq"}, {"en": "witness", "uz": "guvoh bo'lmoq"}, {"en": "scene", "uz": "voqea joyi"},
            {"en": "crime", "uz": "jinoyat"}, {"en": "investigate", "uz": "tergov qilmoq"}, {"en": "police", "uz": "politsiya"},
            {"en": "detective", "uz": "izquvar"}, {"en": "clue", "uz": "ashyoviy dalil"}, {"en": "suspicious", "uz": "shubhali"},
            {"en": "innocent", "uz": "aybsiz"}, {"en": "guilty", "uz": "aybdor"}, {"en": "confess", "uz": "iqror bo'lmoq"},
            {"en": "deny", "uz": "inkor etmoq"}, {"en": "truth", "uz": "haqiqat"}, {"en": "lie", "uz": "yolg'on"},
            {"en": "honesty", "uz": "rostgo'ylik"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 9,
        "topic_title": "Relative Clauses: Who, Which, That",
        "grammar_notes": "Odamlar uchun 'who' (The man who lives next door is a doctor). Narsalar va hayvonlar uchun 'which' (The car which he bought is fast). Ikkalasi o'rniga ham 'that' ishlatilishi mumkin: The girl that called you.",
        "target_words": [
            {"en": "relative", "uz": "nisbiy"}, {"en": "define", "uz": "ta'riflamoq"}, {"en": "describe", "uz": "tasvirlamoq"},
            {"en": "neighbor", "uz": "qo'shni"}, {"en": "stranger", "uz": "begona"}, {"en": "guest", "uz": "mehmon"},
            {"en": "host", "uz": "mezbon"}, {"en": "audience", "uz": "tomoshabinlar"}, {"en": "crowd", "uz": "olomon"},
            {"en": "author", "uz": "muallif"}, {"en": "writer", "uz": "yozuvchi"}, {"en": "artist", "uz": "rassom"},
            {"en": "scientist", "uz": "olim"}, {"en": "inventor", "uz": "ixtirochi"}, {"en": "leader", "uz": "yetakchi"},
            {"en": "president", "uz": "prezident"}, {"en": "citizen", "uz": "fuqaro"}, {"en": "society", "uz": "jamiyat"},
            {"en": "community", "uz": "jamoa"}, {"en": "gadget", "uz": "qurilma"}, {"en": "device", "uz": "uskuna"},
            {"en": "tool", "uz": "asbob"}, {"en": "machine", "uz": "mashina"}, {"en": "vehicle", "uz": "transport vositasi"},
            {"en": "belong", "uz": "tegishli bo'lmoq"}
        ]
    },
    {
        "level": "Pre-Intermediate",
        "lesson_order": 10,
        "topic_title": "Too, Enough va So / Such",
        "grammar_notes": "Too me'yoridan ortiq, salbiy ma'noda (The soup is too hot to eat). Enough yetarli, sifatdan keyin (He isn't tall enough) yoki otdan oldin keladi (I have enough money). So + sifat (so beautiful). Such + (a/an) + sifat + ot (such a beautiful day).",
        "target_words": [
            {"en": "excessive", "uz": "ortiqcha"}, {"en": "adequate", "uz": "yetarli"}, {"en": "insufficient", "uz": "yetarsiz"},
            {"en": "measure", "uz": "o'lchov"}, {"en": "portion", "uz": "ulush/porsiya"}, {"en": "quantity", "uz": "miqdor"},
            {"en": "weight", "uz": "og'irlik"}, {"en": "height", "uz": "balandlik"}, {"en": "width", "uz": "kenglik"},
            {"en": "length", "uz": "uzunlik"}, {"en": "depth", "uz": "chuqurlik"}, {"en": "heavy", "uz": "og'ir"},
            {"en": "light", "uz": "yengil"}, {"en": "narrow", "uz": "tor"}, {"en": "wide", "uz": "keng"},
            {"en": "crowded", "uz": "gavjum"}, {"en": "empty", "uz": "bo'sh"}, {"en": "full", "uz": "to'la"},
            {"en": "taste", "uz": "ta'm"}, {"en": "spicy", "uz": "achchiq"}, {"en": "sweet", "uz": "shirin"},
            {"en": "sour", "uz": "nordon"}, {"en": "salty", "uz": "sho'r"}, {"en": "delicious", "uz": "mazali"},
            {"en": "terrible", "uz": "daxshatli"}
        ]
    },

    # =========================================================================
    # 4. INTERMEDIATE (B2)
    # =========================================================================
    {
        "level": "Intermediate",
        "lesson_order": 1,
        "topic_title": "Second Conditional (Xayoliy shart mayli)",
        "grammar_notes": "Hozirgi yoki kelasi zamondagi noreal, xayoliy holatlar: If + Past Simple, would + V1. E'tibor bering: to be fe'li barcha shaxslar uchun 'were' bo'lishi mumkin (If I were you, I would study harder. If I won a million dollars, I would travel the world).",
        "target_words": [
            {"en": "hypothetical", "uz": "xayoliy/faraziy"}, {"en": "imaginary", "uz": "tasavvurdagi"}, {"en": "unreal", "uz": "noreal"},
            {"en": "lottery", "uz": "lotereya"}, {"en": "millionaire", "uz": "millioner"}, {"en": "charity", "uz": "xayriya"},
            {"en": "donate", "uz": "ehson qilmoq"}, {"en": "island", "uz": "orol"}, {"en": "castle", "uz": "qasr"},
            {"en": "mansion", "uz": "saroy/hovli"}, {"en": "luxury", "uz": "hashamat"}, {"en": "comfort", "uz": "qulaylik"},
            {"en": "freedom", "uz": "ozodlik"}, {"en": "power", "uz": "kuch/hokimiyat"}, {"en": "govern", "uz": "boshqarmoq"},
            {"en": "change", "uz": "o'zgartirmoq"}, {"en": "eliminate", "uz": "yo'qotmoq"}, {"en": "poverty", "uz": "qashshoqlik"},
            {"en": "disease", "uz": "kasallik"}, {"en": "cure", "uz": "davo"}, {"en": "universe", "uz": "koinot"},
            {"en": "galaxy", "uz": "galaktika"}, {"en": "alien", "uz": "o'zga sayyoralik"}, {"en": "explore", "uz": "tadqiq qilmoq"},
            {"en": "discover", "uz": "kashf etmoq"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 2,
        "topic_title": "Passive Voice (Majhul nisbat: Present & Past Simple)",
        "grammar_notes": "Harakat kim tomonidan bajarilganidan ko'ra ob'ekt muhim bo'lsa majhul nisbat ishlatiladi: To be + V3. Present Simple Passive: am/is/are + V3 (English is spoken everywhere). Past Simple Passive: was/were + V3 (This bridge was built in 1995).",
        "target_words": [
            {"en": "manufacture", "uz": "ishlab chiqarmoq"}, {"en": "produce", "uz": "yetishtirmoq"}, {"en": "construct", "uz": "qurmoq"},
            {"en": "destroy", "uz": "vayron qilmoq"}, {"en": "damage", "uz": "zararlamoq"}, {"en": "invent", "uz": "ixtiro qilmoq"},
            {"en": "discover", "uz": "topmoq/kashf etmoq"}, {"en": "publish", "uz": "nashr qilmoq"}, {"en": "broadcast", "uz": "efirga uzatmoq"},
            {"en": "deliver", "uz": "yetkazib bermoq"}, {"en": "export", "uz": "eksport qilmoq"}, {"en": "import", "uz": "import qilmoq"},
            {"en": "goods", "uz": "tovarlar"}, {"en": "factory", "uz": "zavod"}, {"en": "warehouse", "uz": "omborxona"},
            {"en": "package", "uz": "posilka"}, {"en": "shipment", "uz": "yuk jo'natmasi"}, {"en": "supply", "uz": "ta'minlamoq"},
            {"en": "demand", "uz": "talab"}, {"en": "industry", "uz": "sanoat"}, {"en": "economy", "uz": "iqtisodiyot"},
            {"en": "trade", "uz": "savdo"}, {"en": "market", "uz": "bozor"}, {"en": "consumer", "uz": "iste'molchi"},
            {"en": "supplier", "uz": "ta'minotchi"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 3,
        "topic_title": "Passive Voice (Continuous, Perfect va Modals)",
        "grammar_notes": "Present Continuous Passive: is being done. Present Perfect Passive: has been done. Modals Passive: must be done, can be seen. Masalan: The road is being repaired now. My car has been stolen. All assignments must be submitted on time.",
        "target_words": [
            {"en": "progress", "uz": "rivojlanish/jarayon"}, {"en": "maintenance", "uz": "texnik xizmat"}, {"en": "renovation", "uz": "ta'mirlash"},
            {"en": "restoration", "uz": "qayta tiklash"}, {"en": "investigation", "uz": "tergov"}, {"en": "announcement", "uz": "e'lon"},
            {"en": "inspection", "uz": "tekshiruv"}, {"en": "examination", "uz": "imtihon/ko'rik"}, {"en": "approval", "uz": "ma'qullash"},
            {"en": "rejection", "uz": "rad etish"}, {"en": "regulation", "uz": "tartibga solish"}, {"en": "standard", "uz": "standart"},
            {"en": "requirement", "uz": "talab"}, {"en": "protocol", "uz": "bayonnoma/tartib"}, {"en": "procedure", "uz": "jarayon"},
            {"en": "instruction", "uz": "ko'rsatma"}, {"en": "guideline", "uz": "yo'riqnoma"}, {"en": "safety", "uz": "xavfsizlik"},
            {"en": "measure", "uz": "chora-tadbir"}, {"en": "precaution", "uz": "ehtiyot chorasi"}, {"en": "upgrade", "uz": "takomillashtirish"},
            {"en": "replace", "uz": "almashtirmoq"}, {"en": "install", "uz": "o'rnatmoq"}, {"en": "maintain", "uz": "saqlab turmoq"},
            {"en": "guarantee", "uz": "kafolatlamoq"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 4,
        "topic_title": "Used to vs Would (O'tmishdagi odatlar)",
        "grammar_notes": "O'tmishda muntazam bo'lgan, lekin hozir to'xtagan odatlar yoki holatlar uchun 'used to' ishlatiladi (I used to live in Bukhara. I didn't use to like coffee). 'Would' faqat takrorlangan harakatlar uchun ishlatiladi, holat fe'llari bilan ishlatilmaydi.",
        "target_words": [
            {"en": "nostalgia", "uz": "o'tmish qumsashi"}, {"en": "reminisce", "uz": "xotirlamoq"}, {"en": "childhood", "uz": "bolalik"},
            {"en": "adolescence", "uz": "o'smirlik"}, {"en": "memories", "uz": "xotiralar"}, {"en": "tradition", "uz": "an'ana"},
            {"en": "habitual", "uz": "odatiy"}, {"en": "customary", "uz": "odatlangan"}, {"en": "formerly", "uz": "ilgari"},
            {"en": "previously", "uz": "oldin"}, {"en": "ancient", "uz": "qadimiy"}, {"en": "outdated", "uz": "eskirgan"},
            {"en": "obsolete", "uz": "muomaladan chiqqan"}, {"en": "modernize", "uz": "zamonaviylashtirmoq"},
            {"en": "transform", "uz": "tubdan o'zgarmoq"}, {"en": "evolve", "uz": "rivojlanmoq"}, {"en": "ancestor", "uz": "ajdod"},
            {"en": "heritage", "uz": "meros"}, {"en": "origin", "uz": "kelib chiqish"}, {"en": "root", "uz": "ildiz"},
            {"en": "folk", "uz": "xalq"}, {"en": "tale", "uz": "ertak"}, {"en": "legend", "uz": "afsona"},
            {"en": "myth", "uz": "mif/rivoyat"}, {"en": "culture", "uz": "madaniyat"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 5,
        "topic_title": "Past Perfect (Had + V3: O'tmishdan oldingi harakat)",
        "grammar_notes": "O'tmishdagi ikki harakatdan biri ikkinchisidan oldin sodir bo'lganini bildirish uchun: had + V3. Masalan: When I arrived at the cinema, the movie had already started. By the time he was 20, he had written two books.",
        "target_words": [
            {"en": "preceding", "uz": "oldin keluvchi"}, {"en": "prior", "uz": "avvalgi"}, {"en": "anticipate", "uz": "oldindan sezmoq"},
            {"en": "chronology", "uz": "xronologiya"}, {"en": "sequence", "uz": "ketma-ketlik"}, {"en": "simultaneously", "uz": "bir paytda"},
            {"en": "already", "uz": "allaqachon"}, {"en": "beforehand", "uz": "oldindan"}, {"en": "previously", "uz": "ilgari"},
            {"en": "departure", "uz": "jo'nab ketish"}, {"en": "arrival", "uz": "yetib kelish"}, {"en": "commence", "uz": "boshlanmoq"},
            {"en": "conclude", "uz": "xulosa qilmoq/tugamoq"}, {"en": "terminate", "uz": "tugatmoq"}, {"en": "expire", "uz": "muddati o'tmoq"},
            {"en": "deadline", "uz": "oxirgi muddat"}, {"en": "postpone", "uz": "keyinga qoldirmoq"}, {"en": "schedule", "uz": "rejalashtirmoq"},
            {"en": "reschedule", "uz": "qayta rejalashtirmoq"}, {"en": "coincide", "uz": "mos tushmoq"}, {"en": "delay", "uz": "kechikish"},
            {"en": "punctual", "uz": "vaqtiga rioya qiluvchi"}, {"en": "tardy", "uz": "kechikkan"}, {"en": "interval", "uz": "oraliq"},
            {"en": "duration", "uz": "davomiylik"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 6,
        "topic_title": "Gerunds vs Infinitives (Fe'llardan keyin -ing yoki to-verb)",
        "grammar_notes": "Ba'zi fe'llardan keyin faqat Gerund (-ing) keladi: enjoy, mind, avoid, suggest, admit (I enjoy swimming). Ba'zi fe'llardan keyin faqat To-infinitive keladi: want, hope, decide, promise, refuse (I decided to stay). Ba'zilarida ma'no o'zgaradi: remember, stop.",
        "target_words": [
            {"en": "admit", "uz": "tan olmoq"}, {"en": "avoid", "uz": "o'zini olib qochmoq"}, {"en": "consider", "uz": "o'ylab ko'rmoq"},
            {"en": "deny", "uz": "inkor qilmoq"}, {"en": "enjoy", "uz": "zavqlanmoq"}, {"en": "fancy", "uz": "xohlamoq/yoqtirmoq"},
            {"en": "finish", "uz": "tamomlamoq"}, {"en": "imagine", "uz": "tasavvur qilmoq"}, {"en": "keep", "uz": "davom ettirmoq"},
            {"en": "mind", "uz": "e'tiroz bildirmoq"}, {"en": "postpone", "uz": "orqaga surmoq"}, {"en": "suggest", "uz": "taklif qilmoq"},
            {"en": "agree", "uz": "kelishmoq"}, {"en": "attempt", "uz": "urinib ko'rmoq"}, {"en": "decide", "uz": "qaror qilmoq"},
            {"en": "expect", "uz": "kutmoq"}, {"en": "fail", "uz": "muvaffaqiyatsiz bo'lmoq"}, {"en": "hope", "uz": "umid qilmoq"},
            {"en": "manage", "uz": "uddasidan chiqmoq"}, {"en": "offer", "uz": "taklif etmoq"}, {"en": "plan", "uz": "rejalashtirmoq"},
            {"en": "promise", "uz": "va'da qilmoq"}, {"en": "refuse", "uz": "rad qilmoq"}, {"en": "threaten", "uz": "po'pisa qilmoq"},
            {"en": "hesitate", "uz": "ikkilanmoq"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 7,
        "topic_title": "Reported Speech: Darak gaplarni o'zlashtirish",
        "grammar_notes": "Ko'chirma gapni o'zlashtirma gapga aylantirganda zamonlar bir pog'ona orqaga siljiydi (Backshift): Present Simple -> Past Simple, Present Continuous -> Past Continuous, Will -> Would, Can -> Could. 'He said: I live here' -> 'He said that he lived there'.",
        "target_words": [
            {"en": "declare", "uz": "e'lon qilmoq"}, {"en": "explain", "uz": "tushuntirmoq"}, {"en": "state", "uz": "ta'kidlamoq"},
            {"en": "claim", "uz": "da'vo qilmoq"}, {"en": "insist", "uz": "turib olmoq"}, {"en": "remark", "uz": "qayd etmoq"},
            {"en": "announce", "uz": "ma'lum qilmoq"}, {"en": "inform", "uz": "xabardor qilmoq"}, {"en": "notify", "uz": "ogohlantirmoq"},
            {"en": "confirm", "uz": "tasdiqlamoq"}, {"en": "mention", "uz": "eslatib o'tmoq"}, {"en": "whisper", "uz": "pichirlamoq"},
            {"en": "shout", "uz": "qichqirmoq"}, {"en": "complain", "uz": "shikoyat qilmoq"}, {"en": "criticize", "uz": "tanqid qilmoq"},
            {"en": "praise", "uz": "maqtamoq"}, {"en": "reassure", "uz": "tinchlantirmoq"}, {"en": "argue", "uz": "bahslashmoq"},
            {"en": "debate", "uz": "munozara qilmoq"}, {"en": "clarify", "uz": "oydinlik kiritmoq"}, {"en": "emphasize", "uz": "urg'u bermoq"},
            {"en": "summarize", "uz": "xulosalamoq"}, {"en": "conclude", "uz": "yakunlamoq"}, {"en": "quote", "uz": "iqtibos keltirmoq"},
            {"en": "utter", "uz": "tildan chiqarmoq"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 8,
        "topic_title": "Reported Speech: So'roq va Buyruq gaplar",
        "grammar_notes": "Buyruq gaplar to-infinitive orqali o'zlashtiriladi: He told me to sit down. He warned me not to touch it. Umumiy so'roq gaplarda 'if' yoki 'whether' ishlatiladi: He asked me if I spoke English. Maxsus so'roqda so'roq so'z saqlanadi va gap darak tartibiga o'tadi.",
        "target_words": [
            {"en": "command", "uz": "buyruq bermoq"}, {"en": "order", "uz": "buyurmoq"}, {"en": "instruct", "uz": "yo'l-yo'riq bermoq"},
            {"en": "demand", "uz": "talab qilmoq"}, {"en": "request", "uz": "iltimos qilmoq"}, {"en": "urge", "uz": "undamoq"},
            {"en": "forbid", "uz": "taqiqlamoq"}, {"en": "prohibit", "uz": "man etmoq"}, {"en": "allow", "uz": "ruxsat bermoq"},
            {"en": "permit", "uz": "izn bermoq"}, {"en": "inquire", "uz": "surishtirmoq"}, {"en": "wonder", "uz": "qiziqmoq/o'ylanmoq"},
            {"en": "interrogate", "uz": "so'roqqa tutmoq"}, {"en": "question", "uz": "shubhalanmoq/so'ramoq"}, {"en": "challenge", "uz": "chorlamoq/sinamoq"},
            {"en": "advise", "uz": "maslahat bermoq"}, {"en": "plead", "uz": "yalinmoq/iltijo qilmoq"}, {"en": "beg", "uz": "yolvormoq"},
            {"en": "remind", "uz": "eslatmoq"}, {"en": "invite", "uz": "taklif qilmoq"}, {"en": "encourage", "uz": "ruhlandirmoq"},
            {"en": "persuade", "uz": "ko'ndirmoq"}, {"en": "convince", "uz": "ishontirmoq"}, {"en": "dissuade", "uz": "fikridan qaytarmoq"},
            {"en": "threaten", "uz": "do'q urmoq"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 9,
        "topic_title": "Modals of Deduction: Must, Can't, Might, Could",
        "grammar_notes": "Hozirgi zamondagi mantiqiy taxminlar: Must (100% ishonch — aniq shunday): He must be at home, the light is on. Can't (100% imkonsiz): It can't be true! Might / May / Could (50% ehtimollik): She might be sleeping.",
        "target_words": [
            {"en": "deduction", "uz": "xulosa chiqarish"}, {"en": "certainty", "uz": "ishonch"}, {"en": "probability", "uz": "ehtimollik"},
            {"en": "impossibility", "uz": "imkonsizlik"}, {"en": "likelihood", "uz": "ehtimol"}, {"en": "speculate", "uz": "taxmin qilmoq"},
            {"en": "assume", "uz": "faraz qilmoq"}, {"en": "presume", "uz": "taxmin etmoq"}, {"en": "suppose", "uz": "deb o'ylamoq"},
            {"en": "conclude", "uz": "xulosaga kelmoq"}, {"en": "infer", "uz": "mazmun uqmoq"}, {"en": "evidence", "uz": "dalil"},
            {"en": "proof", "uz": "isbot"}, {"en": "clue", "uz": "belgi/ip uchi"}, {"en": "sign", "uz": "ishora"},
            {"en": "symptom", "uz": "alomat"}, {"en": "indication", "uz": "ko'rsatkich"}, {"en": "obvious", "uz": "ravshan"},
            {"en": "evident", "uz": "yaqqol"}, {"en": "apparent", "uz": "ko'rinib turgan"}, {"en": "vague", "uz": "noaniq"},
            {"en": "ambiguous", "uz": "ikki ma'noli"}, {"en": "mysterious", "uz": "sirli"}, {"en": "baffling", "uz": "hayratda qoldiruvchi"},
            {"en": "puzzling", "uz": "chigal"}
        ]
    },
    {
        "level": "Intermediate",
        "lesson_order": 10,
        "topic_title": "Third Conditional (O'tmishdagi afsuslar va imkonsiz shart)",
        "grammar_notes": "O'tmishda bo'lib o'tgan va uni o'zgartirib bo'lmaydigan noreal shart: If + Past Perfect, would have + V3. Masalan: If I had studied harder, I would have passed the exam. (Lekin o'qimaganman va imtihondan yiqilganman).",
        "target_words": [
            {"en": "regret", "uz": "afsuslanmoq"}, {"en": "remorse", "uz": "vijdon azobi"}, {"en": "disappointment", "uz": "umidsizlik"},
            {"en": "grief", "uz": "qayg'u"}, {"en": "blame", "uz": "ayblamoq"}, {"en": "fault", "uz": "ayb/nuqson"},
            {"en": "error", "uz": "xato"}, {"en": "mistake", "uz": "yanglishish"}, {"en": "blunder", "uz": "qo'pol xato"},
            {"en": "overlook", "uz": "e'tibordan chetda qoldirmoq"}, {"en": "neglect", "uz": "e'tiborsizlik qilmoq"},
            {"en": "missed opportunity", "uz": "qo'ldan boy berilgan imkoniyat"}, {"en": "turning point", "uz": "burilish nuqtasi"},
            {"en": "fate", "uz": "taqdir"}, {"en": "destiny", "uz": "qismat"}, {"en": "consequence", "uz": "oqibat"},
            {"en": "outcome", "uz": "yakuniy natija"}, {"en": "repercussion", "uz": "aks-sado/oqibat"}, {"en": "reflect", "uz": "fikr yuritmoq"},
            {"en": "ponder", "uz": "chuqur o'ylamoq"}, {"en": "hindsight", "uz": "kechikkan aql"}, {"en": "retrospect", "uz": "o'tmishga nazar"},
            {"en": "apologize", "uz": "uzr so'ramoq"}, {"en": "forgive", "uz": "kechirmoq"}, {"en": "reconcile", "uz": "yarashmoq"}
        ]
    },

    # =========================================================================
    # 5. UPPER-INTERMEDIATE (B2+)
    # =========================================================================
    {
        "level": "Upper-Intermediate",
        "lesson_order": 1,
        "topic_title": "Mixed Conditionals (Aralash shart mayllari)",
        "grammar_notes": "O'tmishdagi harakatning hozirgi natijasi: If + Past Perfect, would + V1 (If I had won the lottery yesterday, I would be rich today). Hozirgi doimiy holatning o'tmishdagi ta'siri: If + Past Simple, would have + V3 (If I were braver, I would have spoken to her).",
        "target_words": [
            {"en": "interconnected", "uz": "o'zaro bog'liq"}, {"en": "chronological", "uz": "xronologik"}, {"en": "paradox", "uz": "ziddiyat/paradoks"},
            {"en": "implication", "uz": "kelib chiqadigan xulosa"}, {"en": "contingency", "uz": "kutilmagan holat"}, {"en": "ramification", "uz": "tarmoqlangan oqibat"},
            {"en": "alternative", "uz": "muqobil"}, {"en": "scenario", "uz": "ssenariy"}, {"en": "speculation", "uz": "taxminiy mulohaza"},
            {"en": "dilemma", "uz": "qiyin tanlov"}, {"en": "predicament", "uz": "mushkul ahvol"}, {"en": "resolution", "uz": "yechim"},
            {"en": "compromise", "uz": "murosaga kelish"}, {"en": "bargain", "uz": "savdolashish"}, {"en": "negotiate", "uz": "muzokara olib bormoq"},
            {"en": "mediate", "uz": "vositachilik qilmoq"}, {"en": "arbitrate", "uz": "hakamlik qilmoq"}, {"en": "settle", "uz": "hal qilmoq"},
            {"en": "remedy", "uz": "chora/davo"}, {"en": "alleviate", "uz": "yengillashtirmoq"}, {"en": "mitigate", "uz": "yumshatmoq"},
            {"en": "exacerbate", "uz": "keskinlashtirmoq"}, {"en": "aggravate", "uz": "og'irlashtirmoq"}, {"en": "worsen", "uz": "yomonlashmoq"},
            {"en": "deteriorate", "uz": "inqirozga yuz tutmoq"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 2,
        "topic_title": "Inversion (Salbiy so'zlar bilan teskari tartib)",
        "grammar_notes": "Gapga qat'iy emotsiya yoki urg'u berish uchun salbiy ravishlar gap boshiga chiqariladi va so'roq shakli qo'llaniladi: Never have I seen such beauty! Seldom does he come here. Hardly had I entered when the bell rang. Under no circumstances should you open the door.",
        "target_words": [
            {"en": "seldom", "uz": "kamdan-kam"}, {"en": "rarely", "uz": "kam hollarda"}, {"en": "hardly", "uz": "zo'rg'a"},
            {"en": "scarcely", "uz": "zo'rg'a/arang"}, {"en": "barely", "uz": "zo'rg'a"}, {"en": "under no circumstances", "uz": "hech qanday holatda"},
            {"en": "on no account", "uz": "hech qachon/hech bir sabab bilan"}, {"en": "not only", "uz": "nafaqat"}, {"en": "no sooner", "uz": "ulgurmasdan turib"},
            {"en": "emphasis", "uz": "urg'u"}, {"en": "dramatic", "uz": "hayajonli/keskin"}, {"en": "rhetorical", "uz": "ritorik"},
            {"en": "eloquent", "uz": "notiqona"}, {"en": "persuasive", "uz": "ishontiruvchi"}, {"en": "convincing", "uz": "inontiruvchi"},
            {"en": "compelling", "uz": "o'ziga tortuvchi"}, {"en": "striking", "uz": "hayratlanarli"}, {"en": "remarkable", "uz": "ajoyib"},
            {"en": "extraordinary", "uz": "favqulodda"}, {"en": "profound", "uz": "chuqur/teran"}, {"en": "intensity", "uz": "shiddat"},
            {"en": "exaggerate", "uz": "bo'rttirmoq"}, {"en": "understate", "uz": "kamaytirib ko'rsatmoq"}, {"en": "magnify", "uz": "kattalashtirmoq"},
            {"en": "amplify", "uz": "kuchaytirmoq"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 3,
        "topic_title": "Cleft Sentences (Urg'u beruvchi jumlalar)",
        "grammar_notes": "Biror ma'lumotga alohida diqqat qaratish: 'It is/was ... that' yoki 'What ... is/was'. Masalan: John broke the window -> It was John who broke the window. What I really need right now is a long holiday. The person who helped me was my teacher.",
        "target_words": [
            {"en": "focal point", "uz": "diqqat markazi"}, {"en": "highlight", "uz": "ajratib ko'rsatmoq"}, {"en": "spotlight", "uz": "diqqat markaziga qo'ymoq"},
            {"en": "accentuate", "uz": "alohida ajratmoq"}, {"en": "underline", "uz": "tagiga chizmoq"}, {"en": "stress", "uz": "ta'kidlamoq"},
            {"en": "distinction", "uz": "farq/ajralib turish"}, {"en": "prominent", "uz": "ko'zga ko'ringan"}, {"en": "conspicuous", "uz": "ko'zga tashlanadigan"},
            {"en": "crucial", "uz": "o'ta muhim"}, {"en": "pivotal", "uz": "hal qiluvchi"}, {"en": "paramount", "uz": "birlamchi ahamiyatli"},
            {"en": "essential", "uz": "muhim/zarur"}, {"en": "vital", "uz": "hayotiy zarur"}, {"en": "fundamental", "uz": "asosiy"},
            {"en": "significance", "uz": "ahamiyat"}, {"en": "priority", "uz": "ustuvorlik"}, {"en": "core", "uz": "mag'iz/o'zak"},
            {"en": "essence", "uz": "mohiyat"}, {"en": "substance", "uz": "asos/modda"}, {"en": "noteworthy", "uz": "e'tiborga loyiq"},
            {"en": "exceptional", "uz": "noyob/alohida"}, {"en": "singular", "uz": "yakka/betakror"}, {"en": "unprecedented", "uz": "misli ko'rilmagan"},
            {"en": "unrivaled", "uz": "tengsiz"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 4,
        "topic_title": "Wish and If Only (Istak va Afsuslar)",
        "grammar_notes": "Hozirgi zamondagi norozilik: Wish + Past Simple (I wish I had more time. If only I knew the answer). O'tmishdagi afsus: Wish + Past Perfect (I wish I hadn't eaten that cake). Boshqalarning xatti-harakatidan asabiylashganda: Wish + would + V1 (I wish it would stop raining!).",
        "target_words": [
            {"en": "longing", "uz": "kuchli orziqish"}, {"en": "yearning", "uz": "intiq bo'lish"}, {"en": "aspiration", "uz": "intilish"},
            {"en": "craving", "uz": "kuchli istak"}, {"en": "desire", "uz": "xohish"}, {"en": "frustration", "uz": "hafsala pir bo'lishi"},
            {"en": "irritation", "uz": "g'ashlik/asabiylashish"}, {"en": "annoyance", "uz": "jahl chiqishi"}, {"en": "discontent", "uz": "norozilik"},
            {"en": "dissatisfaction", "uz": "qoniqmaslik"}, {"en": "resentment", "uz": "gina/alam"}, {"en": "grudge", "uz": "adovat"},
            {"en": "bitterness", "uz": "alamzada bo'lish"}, {"en": "nostalgia", "uz": "o'tmish qumsashi"}, {"en": "melancholy", "uz": "tushkunlik/g'am"},
            {"en": "sorrow", "uz": "musibat"}, {"en": "mourning", "uz": "motam"}, {"en": "consolation", "uz": "tasalli"},
            {"en": "solace", "uz": "ko'ngil ovlash"}, {"en": "acceptance", "uz": "tan olish"}, {"en": "resignation", "uz": "taqdirga tan berish"},
            {"en": "optimism", "uz": "nekbinlik/yaxshilikka ishonish"}, {"en": "pessimism", "uz": "badbinlik"}, {"en": "cynicism", "uz": "kinoya/ishonchsizlik"},
            {"en": "idealism", "uz": "orзуparastlik"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 5,
        "topic_title": "Advanced Passive: Impersonal Passive & Reporting",
        "grammar_notes": "Rasmiy yangiliklar va jamoatchilik fikrini yetkazishda: It is said that / He is said to be... Konstruksiyasi: People say that he is rich -> It is said that he is rich / He is said to be rich. They believe that the criminal escaped -> The criminal is believed to have escaped.",
        "target_words": [
            {"en": "allegedly", "uz": "da'vo qilinishicha"}, {"en": "reportedly", "uz": "xabar qilinishicha"}, {"en": "supposedly", "uz": "taxmin qilinishicha"},
            {"en": "purportedly", "uz": "aytishlariga qaraganda"}, {"en": "rumor", "uz": "mish-mish"}, {"en": "speculate", "uz": "tahmin qilmoq"},
            {"en": "estimate", "uz": "baholamoq"}, {"en": "calculate", "uz": "hisoblamoq"}, {"en": "presume", "uz": "taxmin etmoq"},
            {"en": "reckon", "uz": "hisoblamoq/o'ylamoq"}, {"en": "acknowledge", "uz": "tan olmoq"}, {"en": "disclose", "uz": "oshkor qilmoq"},
            {"en": "reveal", "uz": "fosh etmoq"}, {"en": "unveil", "uz": "namoyish qilmoq"}, {"en": "leak", "uz": "sizdirmoq (ma'lumotni)"},
            {"en": "source", "uz": "manba"}, {"en": "spokesperson", "uz": "matbuot kotibi"}, {"en": "statement", "uz": "bayonot"},
            {"en": "press release", "uz": "matbuot xabarnomasi"}, {"en": "communique", "uz": "rasmiy axborot"}, {"en": "briefing", "uz": "qisqa yo'riqnoma"},
            {"en": "coverage", "uz": "yoritish (matbuotda)"}, {"en": "journalist", "uz": "jurnalist"}, {"en": "correspondent", "uz": "muxbir"},
            {"en": "headline", "uz": "sarlavha"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 6,
        "topic_title": "Causative Form: Have / Get something done",
        "grammar_notes": "Ishni o'zi qilmasdan, boshqa birovga qildirganda: have/get + narsa + V3. Masalan: I repaired my car (Men mashinamni o'zim tuzatdim) vs I had my car repaired (Men mashinamni ustaga tuzattirdim). She got her hair cut. I had my documents translated.",
        "target_words": [
            {"en": "delegate", "uz": "vazifani yuklamoq"}, {"en": "outsource", "uz": "tashqi xizmatga bermoq"}, {"en": "commission", "uz": "buyurtma bermoq"},
            {"en": "authorize", "uz": "vakolat bermoq"}, {"en": "assign", "uz": "tayinlamoq"}, {"en": "appoint", "uz": "mansabga qo'ymoq"},
            {"en": "hire", "uz": "yollamoq"}, {"en": "employ", "uz": "ishga olmoq"}, {"en": "contractor", "uz": "pudratchi"},
            {"en": "specialist", "uz": "mutaxassis"}, {"en": "technician", "uz": "texnik usta"}, {"en": "plumber", "uz": "santexnik"},
            {"en": "electrician", "uz": "elektr ustasi"}, {"en": "mechanic", "uz": "mexanik"}, {"en": "carpenter", "uz": "duradgor"},
            {"en": "tailor", "uz": "tikuvchi"}, {"en": "architect", "uz": "arxitektor"}, {"en": "consultant", "uz": "maslahatchi"},
            {"en": "inspection", "uz": "ko'rik"}, {"en": "service", "uz": "xizmat ko'rsatish"}, {"en": "maintenance", "uz": "ta'minot"},
            {"en": "overhaul", "uz": "kapital ta'mir"}, {"en": "refurbish", "uz": "yangilamoq"}, {"en": "custom-made", "uz": "buyurtmaga tayyorlangan"},
            {"en": "tailored", "uz": "moslashtirilgan"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 7,
        "topic_title": "Subjunctive Mood (Talab va Taklif mayli)",
        "grammar_notes": "Rasmiy talab, tavsiya va takliflarda fe'lning boshlang'ich shakli (infinitive without to) ishlatiladi: demand, suggest, recommend, insist + that + shaxs + V1. Masalan: The doctor recommended that he stop smoking. I insist that she be present at the meeting.",
        "target_words": [
            {"en": "imperative", "uz": "o'ta muhim/shart"}, {"en": "vital", "uz": "hayotiy zarur"}, {"en": "mandatory", "uz": "majburiy"},
            {"en": "obligatory", "uz": "burch hisoblangan"}, {"en": "stipulate", "uz": "shart qilib qo'ymoq"}, {"en": "decree", "uz": "farmon bermoq"},
            {"en": "mandate", "uz": "vakolat berilmoq/buyurmoq"}, {"en": "insist", "uz": "qat'iy talab qilmoq"}, {"en": "propose", "uz": "taklif kiritmoq"},
            {"en": "recommend", "uz": "tavsiya bermoq"}, {"en": "advise", "uz": "maslahat bermoq"}, {"en": "request", "uz": "talabnoma bermoq"},
            {"en": "petition", "uz": "arznoma yozmoq"}, {"en": "plead", "uz": "yolvormoq"}, {"en": "motion", "uz": "taklif (yig'ilishda)"},
            {"en": "resolution", "uz": "qaror loyihasi"}, {"en": "statute", "uz": "ustav/qonun"}, {"en": "ordinance", "uz": "farmoyish"},
            {"en": "provision", "uz": "modda/shart"}, {"en": "clause", "uz": "band (shartnomada)"}, {"en": "compliance", "uz": "rioya qilish"},
            {"en": "adhere", "uz": "amal qilmoq"}, {"en": "conform", "uz": "moslashmoq"}, {"en": "abide by", "uz": "bo'ysunmoq"},
            {"en": "enforce", "uz": "majburlab joriy etmoq"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 8,
        "topic_title": "Participle Clauses (-ing va -ed qisqartmalari)",
        "grammar_notes": "Murakkab gaplarni qisqartirish usuli: Seeing the police, the thief ran away (= When he saw the police...). Written in 1920, the book is still famous (= Because it was written...). Having finished his homework, he went to bed (= After he had finished...).",
        "target_words": [
            {"en": "concise", "uz": "lo'nda/qisqa"}, {"en": "brevity", "uz": "qisqalik"}, {"en": "cohesion", "uz": "mantiqiy bog'liqlik"},
            {"en": "coherence", "uz": "izchillik"}, {"en": "abbreviate", "uz": "qisqartirmoq"}, {"en": "condense", "uz": "zichlashtirmoq"},
            {"en": "simplify", "uz": "soddalashtirmoq"}, {"en": "elaborate", "uz": "batafsil bayon qilmoq"}, {"en": "articulate", "uz": "ravon ifodalamoq"},
            {"en": "express", "uz": "ifodalamoq"}, {"en": "convey", "uz": "yetkazmoq (ma'noni)"}, {"en": "depict", "uz": "tasvirlamoq"},
            {"en": "illustrate", "uz": "ko'rsatib bermoq"}, {"en": "exemplify", "uz": "misol keltirmoq"}, {"en": "demonstrate", "uz": "namoyish qilmoq"},
            {"en": "manifest", "uz": "namoyon bo'lmoq"}, {"en": "indicate", "uz": "ko'rsatmoq"}, {"en": "signify", "uz": "anglatmoq"},
            {"en": "denote", "uz": "bildirmoq"}, {"en": "connote", "uz": "yashirin ma'no kasb etmoq"}, {"en": "allude", "uz": "ishora qilmoq"},
            {"en": "hint", "uz": "shama qilmoq"}, {"en": "imply", "uz": "nazarda tutmoq"}, {"en": "infer", "uz": "mantiqan chiqarmoq"},
            {"en": "interpret", "uz": "talqin qilmoq"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 9,
        "topic_title": "Advanced Discourse Markers and Linkers",
        "grammar_notes": "Matn va nutqda fikrlar orasidagi mantiqiy ko'priklar: Ziddiyat (However, Nevertheless, In spite of, Whereas); Qo'shimcha (Furthermore, Moreover, In addition); Sabab-oqibat (Consequently, Therefore, As a result); Xulosa (To sum up, In conclusion).",
        "target_words": [
            {"en": "furthermore", "uz": "bundan tashqari"}, {"en": "moreover", "uz": "qo'shimcha ravishda"}, {"en": "nevertheless", "uz": "shunga qaramay"},
            {"en": "nonetheless", "uz": "baribir"}, {"en": "consequently", "uz": "natijada"}, {"en": "therefore", "uz": "shuning uchun"},
            {"en": "hence", "uz": "demak/shu bois"}, {"en": "thus", "uz": "shunday qilib"}, {"en": "whereas", "uz": "holbuki/esa"},
            {"en": "while", "uz": "bir vaqtda/esa"}, {"en": "conversely", "uz": "aksincha"}, {"en": "on the contrary", "uz": "aksincha"},
            {"en": "notwithstanding", "uz": "qaramasdan"}, {"en": "albeit", "uz": "garchi... bo'lsa ham"}, {"en": "inasmuch as", "uz": "chunki/modomiki"},
            {"en": "likewise", "uz": "shuningdek/xuddi shunday"}, {"en": "similarly", "uz": "o'xshash tarzda"}, {"en": "subsequently", "uz": "keyinchalik"},
            {"en": "accordingly", "uz": "shunga muvofiq"}, {"en": "incidentally", "uz": "aytgancha"}, {"en": "meanwhile", "uz": "shu orada"},
            {"en": "ultimately", "uz": "oxir-oqibat"}, {"en": "eventually", "uz": "vaqti kelib"}, {"en": "essentially", "uz": "mohiyatan"},
            {"en": "predominantly", "uz": "asosan"}
        ]
    },
    {
        "level": "Upper-Intermediate",
        "lesson_order": 10,
        "topic_title": "Phrasal Verbs in Academic and Daily Context",
        "grammar_notes": "Fe'l + predlog qo'shilishi orqali yangi idiomatik ma'no hosil qilish: carry out (amalga oshirmoq), look forward to (intiqlik bilan kutmoq), turn down (rad etmoq), figure out (tushunib yetmoq), put off (kechiktirmoq), come across (duch kelmoq).",
        "target_words": [
            {"en": "carry out", "uz": "bajarmoq/o'tkazmoq"}, {"en": "bring about", "uz": "sabab bo'lmoq"}, {"en": "come across", "uz": "tasodifan uchratmoq"},
            {"en": "figure out", "uz": "yechimini topmoq"}, {"en": "get along", "uz": "chiqishmoq"}, {"en": "give up", "uz": "taslim bo'lmoq"},
            {"en": "look after", "uz": "g'amxo'rlik qilmoq"}, {"en": "look forward to", "uz": "intiqlik bilan kutmoq"},
            {"en": "make out", "uz": "zo'rg'a ilg'amoq/tushunmoq"}, {"en": "pass out", "uz": "hushidan ketmoq"},
            {"en": "put off", "uz": "kechiktirmoq"}, {"en": "put up with", "uz": "chidadimoq/sabr qilmoq"},
            {"en": "run out of", "uz": "tugab qolmoq"}, {"en": "set up", "uz": "tashkil qilmoq"},
            {"en": "take after", "uz": "o'xshamoq (fe'l-atvorda)"}, {"en": "take off", "uz": "havoga ko'tarilmoq/yechmoq"},
            {"en": "turn down", "uz": "rad qilmoq/ovozini pasaytirmoq"}, {"en": "turn into", "uz": "aylanmoq (boshqa narsaga)"},
            {"en": "work out", "uz": "mashq qilmoq/hal bo'lmoq"}, {"en": "break down", "uz": "buzilib qolmoq"},
            {"en": "call off", "uz": "bekor qilmoq"}, {"en": "drop in", "uz": "yo'l-yo'lakay kirib o'tmoq"},
            {"en": "hold on", "uz": "kutib turmoq"}, {"en": "keep up with", "uz": "yetishib bormoq"},
            {"en": "back up", "uz": "qo'llab-quvvatlamoq/nusxa olmoq"}
        ]
    },

    # =========================================================================
    # 6. IELTS (C1)
    # =========================================================================
    {
        "level": "IELTS",
        "lesson_order": 1,
        "topic_title": "IELTS Writing Task 1: Line Graph va Tendensiyalar tasviri",
        "grammar_notes": "Vaqt davomidagi o'zgarishlarni tasvirlash: increase, decrease, fluctuate, plateau, peak at. So'z birikmalari: a dramatic rise, a sharp decline, remain steady. Paraphrasing: The line graph illustrates / demonstrates / reveals...",
        "target_words": [
            {"en": "illustrate", "uz": "yoritib ko'rsatmoq"}, {"en": "fluctuate", "uz": "tebranmoq"}, {"en": "plateau", "uz": "bir maromda qolmoq"},
            {"en": "dramatic", "uz": "keskin/ko'zga ko'rinarli"}, {"en": "sharp", "uz": "o'tkir/keskin"}, {"en": "steady", "uz": "barqaror"},
            {"en": "gradual", "uz": "bosqichma-bosqich"}, {"en": "negligible", "uz": "arzimas"}, {"en": "significant", "uz": "ahamiyatli"},
            {"en": "substantial", "uz": "salmoqli"}, {"en": "peak", "uz": "cho'qqiga chiqmoq"}, {"en": "bottom out", "uz": "eng tubiga tushmoq"},
            {"en": "plummet", "uz": "qulamoq/shiddat bilan pasaymoq"}, {"en": "soar", "uz": "keskin ko'tarilmoq"}, {"en": "skyrocket", "uz": "osmonga sapchimoq"},
            {"en": "dip", "uz": "ozgina pasayib qaytmoq"}, {"en": "oscillate", "uz": "tebranib turmoq"}, {"en": "trend", "uz": "yo'nalish/tendensiya"},
            {"en": "trajectory", "uz": "harakat yo'nalishi"}, {"en": "upward", "uz": "yuqoriga yo'nalgan"}, {"en": "downward", "uz": "pastga yo'nalgan"},
            {"en": "respectively", "uz": "tegishlicha/mos ravishda"}, {"en": "period", "uz": "davr"}, {"en": "timeframe", "uz": "vaqt oralig'i"},
            {"en": "projection", "uz": "kelajak taxmini"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 2,
        "topic_title": "IELTS Writing Task 1: Pie Chart va Bar Chart (Ulushlar va Taqqoslash)",
        "grammar_notes": "Kategoriya va ulushlarni taqqoslash: account for, make up, constitute, comprise. Masalan: Food accounted for 35% of the total budget. Taqqoslash konstruktsiyalari: in comparison with, while, whereas, by contrast, twice as much as.",
        "target_words": [
            {"en": "account for", "uz": "tashkil qilmoq (ulushni)"}, {"en": "constitute", "uz": "tashkil etmoq"}, {"en": "comprise", "uz": "o'z ichiga olmoq"},
            {"en": "proportion", "uz": "mutanosiblik/ulush"}, {"en": "percentage", "uz": "foiz miqdori"}, {"en": "majority", "uz": "ko'pchilik"},
            {"en": "minority", "uz": "kamchilik"}, {"en": "vast majority", "uz": "mutlaq ko'pchilik"}, {"en": "tiny fraction", "uz": "juda kichik qism"},
            {"en": "segment", "uz": "segment/bo'lak"}, {"en": "sector", "uz": "soha"}, {"en": "distribution", "uz": "taqsimot"},
            {"en": "breakdown", "uz": "tarkibiy tahlil"}, {"en": "category", "uz": "toifa"}, {"en": "predominate", "uz": "ustunlik qilmoq"},
            {"en": "surpass", "uz": "ortda qoldirmoq"}, {"en": "outweigh", "uz": "og'irroq kelmoq/ustun kelmoq"}, {"en": "exceed", "uz": "oshmoq"},
            {"en": "lag behind", "uz": "orqada qolmoq"}, {"en": "parallel", "uz": "parallel/teng"}, {"en": "identical", "uz": "aynan bir xil"},
            {"en": "discrepancy", "uz": "nomutanosiblik"}, {"en": "contrast", "uz": "keskin farq"}, {"en": "demographic", "uz": "demografik"},
            {"en": "allocation", "uz": "ajratilgan mablag'/ulush"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 3,
        "topic_title": "IELTS Writing Task 1: Maps (Xarita) va Process (Jarayon) diagrammasi",
        "grammar_notes": "Maps: O'zgarishlar va rekonstruksiyalar tasviri (was demolished, was converted into, was replaced by, expanded to the north). Process: Passiv zamonlar va ketma-ketlik bog'lovchilari (Initially, subsequently, in the following stage, finally).",
        "target_words": [
            {"en": "demolish", "uz": "buzib tashlamoq"}, {"en": "reconstruct", "uz": "qayta qurmoq"}, {"en": "expand", "uz": "kengaytirmoq"},
            {"en": "transform", "uz": "o'zgartirmoq"}, {"en": "convert", "uz": "moslashtirmoq/aylantirmoq"}, {"en": "replace", "uz": "o'rniga qo'ymoq"},
            {"en": "modernize", "uz": "zamonaviylashtirmoq"}, {"en": "relocate", "uz": "joyini o'zgartirmoq"}, {"en": "extend", "uz": "uzaytirmoq"},
            {"en": "erect", "uz": "qad ko'tarmoq"}, {"en": "install", "uz": "o'rnatmoq"}, {"en": "industrial", "uz": "sanoatlashgan"},
            {"en": "residential", "uz": "turar-joy"}, {"en": "pedestrian", "uz": "piyodalar zonasi"}, {"en": "roundabout", "uz": "aylanma yo'l"},
            {"en": "intersection", "uz": "chorraha"}, {"en": "facility", "uz": "qulaylik/bino"}, {"en": "infrastructure", "uz": "infratuzilma"},
            {"en": "raw material", "uz": "xomashyo"}, {"en": "purify", "uz": "tozalamoq"}, {"en": "filter", "uz": "filtrlash"},
            {"en": "package", "uz": "qadoqlash"}, {"en": "distribute", "uz": "tarqatish"}, {"en": "recycle", "uz": "qayta ishlash"},
            {"en": "subsequent", "uz": "keyingi bosqich"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 4,
        "topic_title": "IELTS Writing Task 2: Agree or Disagree Essay",
        "grammar_notes": "Fikrga qo'shilish yoki qo'shilmaslik inshosi strukturasi: Introduction (Paraphrase + Clear Thesis Statement), Body 1 (First strong argument + Example), Body 2 (Second strong argument + Example), Conclusion (Restate Thesis). Bir tomonda qat'iy turish strategiyasi.",
        "target_words": [
            {"en": "thesis", "uz": "tezis/asosiy g'oya"}, {"en": "contention", "uz": "dalil/da'vo"}, {"en": "assertion", "uz": "qat'iy ta'kid"},
            {"en": "unequivocal", "uz": "shubhasiz/ochiq-ravshan"}, {"en": "advocate", "uz": "tarafdor bo'lmoq"}, {"en": "oppose", "uz": "qarshi chiqmoq"},
            {"en": "endorse", "uz": "qo'llab-quvvatlamoq"}, {"en": "refute", "uz": "rad etmoq"}, {"en": "dispute", "uz": "bahslashmoq"},
            {"en": "justify", "uz": "oqlamoq"}, {"en": "legitimate", "uz": "qonuniy/o'rinli"}, {"en": "flawed", "uz": "kamchilikli"},
            {"en": "fallacy", "uz": "xato mantiq"}, {"en": "plausible", "uz": "haqiqatga yaqin"}, {"en": "compelling", "uz": "inkor etib bo'lmas"},
            {"en": "cogent", "uz": "asosli/kuchli"}, {"en": "argument", "uz": "dalil"}, {"en": "counterargument", "uz": "qarshi dalil"},
            {"en": "rebuttal", "uz": "raddiya"}, {"en": "perspective", "uz": "nuqtai nazar"}, {"en": "standpoint", "uz": "qarash"},
            {"en": "stance", "uz": "pozitsiya"}, {"en": "firmly", "uz": "qat'iy ravishda"}, {"en": "untenable", "uz": "himoyasiz/asossiz"},
            {"en": "indisputable", "uz": "munozarasiz"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 5,
        "topic_title": "IELTS Writing Task 2: Advantages and Disadvantages Essay",
        "grammar_notes": "Ijobiy va salbiy tomonlarni muvozanatli tahlil qilish: 'Do advantages outweigh disadvantages?'. Body paragraflarda har ikkala tomonni yoritish, so'ng qaysi biri og'irroq kelishini mantiqiy isbotlash. 'While there are drawbacks, the merits are undeniable.'",
        "target_words": [
            {"en": "advantage", "uz": "afzallik"}, {"en": "drawback", "uz": "kamchilik"}, {"en": "merit", "uz": "fazilat/yutuq"},
            {"en": "demerit", "uz": "nuqson"}, {"en": "benefit", "uz": "foyda"}, {"en": "detriment", "uz": "zarar"},
            {"en": "perk", "uz": "qo'shimcha imtiyoz"}, {"en": "obstacle", "uz": "to'siq"}, {"en": "impediment", "uz": "g'ov"},
            {"en": "downside", "uz": "salbiy jihat"}, {"en": "upside", "uz": "ijobiy tomon"}, {"en": "asset", "uz": "qimmatbaho manba"},
            {"en": "liability", "uz": "yuk/majburiyat"}, {"en": "lucrative", "uz": "daromadli"}, {"en": "adverse", "uz": "nojo'ya/salbiy"},
            {"en": "beneficial", "uz": "manfaatli"}, {"en": "harmful", "uz": "zararli"}, {"en": "outweigh", "uz": "ustun kelmoq"},
            {"en": "surpass", "uz": "oshirib yubormoq"}, {"en": "counterbalance", "uz": "muvozanatga keltirmoq"}, {"en": "compensate", "uz": "qoplamoq"},
            {"en": "trade-off", "uz": "o'zaro almashuv/kelishuv"}, {"en": "dilemma", "uz": "ikki o't orasida qolish"},
            {"en": "double-edged sword", "uz": "ikki tomoni ham tig'li qurol"}, {"en": "proponent", "uz": "tarafdor"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 6,
        "topic_title": "IELTS Writing Task 2: Problem and Solution Essay",
        "grammar_notes": "Global yoki ijtimoiy muammolar va ularning yechimlari: Problem (Causes / Factors) + Solution (Government measures / Individual actions). Modal fe'llar va shart gaplar: Governments should implement policies... If individuals take steps...",
        "target_words": [
            {"en": "phenomenon", "uz": "hodisa"}, {"en": "epidemic", "uz": "keng tarqalgan muammo"}, {"en": "crisis", "uz": "inqiroz"},
            {"en": "scarcity", "uz": "taqchillik"}, {"en": "depletion", "uz": "tugab bitish"}, {"en": "degradation", "uz": "yemirilish/tanazzul"},
            {"en": "pollution", "uz": "ifloslanish"}, {"en": "contamination", "uz": "zaharlanish"}, {"en": "urbanization", "uz": "shaharlashuv"},
            {"en": "congestion", "uz": "tirbandlik"}, {"en": "overpopulation", "uz": "aholi zichligi oshishi"}, {"en": "poverty", "uz": "kambag'allik"},
            {"en": "unemployment", "uz": "ishsizlik"}, {"en": "inequality", "uz": "tengsizlik"}, {"en": "discrimination", "uz": "kamsitish"},
            {"en": "implement", "uz": "amalga oshirmoq"}, {"en": "execute", "uz": "ijro etmoq"}, {"en": "tackle", "uz": "kurashmoq (muammo bilan)"},
            {"en": "combat", "uz": "qarshi kurashmoq"}, {"en": "curb", "uz": "jilovlamoq"}, {"en": "remedy", "uz": "davolamoq/tuzatmoq"},
            {"en": "subsidize", "uz": "dotatsiya bermoq"}, {"en": "incentivize", "uz": "rag'batlantirmoq"}, {"en": "regulate", "uz": "tartibga solmoq"},
            {"en": "impose", "uz": "majburiy joriy qilmoq"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 7,
        "topic_title": "IELTS Writing Task 2: Discuss Both Views and Give Opinion",
        "grammar_notes": "Har ikki qarama-qarshi tomonni betaraf tahlil qilish va o'z mustaqil fikrini bayon qilish: Body 1 (Why some people believe X), Body 2 (Why others advocate Y + Author's stance). Muvozanatli ritorika: 'On the one hand... On the other hand... In my perspective...'",
        "target_words": [
            {"en": "controversial", "uz": "bahsli"}, {"en": "contentious", "uz": "kelishmovchilikka boy"}, {"en": "polarizing", "uz": "ikkiga ajratuvchi"},
            {"en": "divergent", "uz": "turli xil yo'nalgan"}, {"en": "faction", "uz": "guruh/firqa"}, {"en": "camp", "uz": "qarashlar lageri"},
            {"en": "advocate", "uz": "himoyachi/tarafdor"}, {"en": "detractor", "uz": "qoralovchi"}, {"en": "skeptic", "uz": "shubha bilan qarovchi"},
            {"en": "sympathizer", "uz": "hamfikr"}, {"en": "impartial", "uz": "xolis/betaraf"}, {"en": "unbiased", "uz": "beg'araz"},
            {"en": "prejudiced", "uz": "g'arazli"}, {"en": "subjective", "uz": "sub'ektiv"}, {"en": "objective", "uz": "ob'ektiv"},
            {"en": "equitable", "uz": "adolatli"}, {"en": "nuance", "uz": "nozik farq"}, {"en": "subtlety", "uz": "noziklik"},
            {"en": "weigh", "uz": "taroziga qo'ymoq"}, {"en": "appraise", "uz": "qiymat bermoq"}, {"en": "assess", "uz": "baholamoq"},
            {"en": "reconcile", "uz": "yarashtirmoq/moslamoq"}, {"en": "synthesis", "uz": "umumlashtirish"}, {"en": "verdict", "uz": "hukm/xulosa"},
            {"en": "pronouncement", "uz": "rasmiy xulosa"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 8,
        "topic_title": "IELTS Speaking Part 1 & Part 2: Fluency, Idioms & Cohesion",
        "grammar_notes": "Nutq ravonligi (Fluency), pauzalarni to'g'ri to'ldirish (Fillers), idiomatik iboralar va 2 daqiqalik monolog (Cue Card) texnikasi: PPF usuli (Past, Present, Future). Hikoyani boyitish: 'To cut a long story short... It goes without saying that...'",
        "target_words": [
            {"en": "fluency", "uz": "ravonlik"}, {"en": "coherence", "uz": "mantiqiy bog'liqlik"}, {"en": "spontaneity", "uz": "tabiiylik/o'z-o'zidan chiqish"},
            {"en": "hesitation", "uz": "ikkilanish"}, {"en": "stammer", "uz": "duduqlanish"}, {"en": "filler", "uz": "pauza to'ldiruvchi so'z"},
            {"en": "intonation", "uz": "ohang"}, {"en": "pronunciation", "uz": "talaffuz"}, {"en": "enunciation", "uz": "aniq talaffuz qilish"},
            {"en": "expressive", "uz": "ifodali"}, {"en": "anecdote", "uz": "qiziqarli voqea"}, {"en": "chronicle", "uz": "voqealar bayoni"},
            {"en": "vividly", "uz": "yaqqol/ravshan"}, {"en": "fondly", "uz": "mehr bilan"}, {"en": "distinctly", "uz": "aniq-tiniq"},
            {"en": "once in a blue moon", "uz": "juda kamdan-kam"}, {"en": "over the moon", "uz": "boshi osmonda"},
            {"en": "down in the dumps", "uz": "kayfiyati tushkun"}, {"en": "piece of cake", "uz": "juda oson"},
            {"en": "cost an arm and a leg", "uz": "juda qimmatga tushmoq"}, {"en": "hit the nail on the head", "uz": "nishonga aniq urmoq"},
            {"en": "burn the midnight oil", "uz": "tunlari bilan dars qilmoq"}, {"en": "see eye to eye", "uz": "fikri bir joydan chiqmoq"},
            {"en": "spill the beans", "uz": "sirni ochib qo'ymoq"}, {"en": "under the weather", "uz": "tob-toqati yo'q"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 9,
        "topic_title": "IELTS Speaking Part 3: Abstract va Tahliliy fikrlash",
        "grammar_notes": "Murakkab mavzularda chuqur falsafiy fikr yuritish (Society, Technology, Ethics, Culture). Javob berish qoidasi: A-R-E-A (Answer, Reason, Example, Alternative/Impact). 'Broadly speaking... When considering the broader implications...'",
        "target_words": [
            {"en": "abstract", "uz": "mavhum"}, {"en": "philosophical", "uz": "falsafiy"}, {"en": "ethical", "uz": "axloqiy"},
            {"en": "moral", "uz": "ma'naviy"}, {"en": "societal", "uz": "jamiyatga oid"}, {"en": "cultural heritage", "uz": "madaniy meros"},
            {"en": "globalization", "uz": "globallashuv"}, {"en": "technological advancement", "uz": "texnologik taraqqiyot"},
            {"en": "artificial intelligence", "uz": "sun'iy intellekt"}, {"en": "automation", "uz": "avtomatlashtirish"},
            {"en": "implication", "uz": "kutilayotgan oqibat"}, {"en": "ramification", "uz": "tarmoqlangan ta'sir"},
            {"en": "consequence", "uz": "natija"}, {"en": "perspective", "uz": "dunyoqarash"}, {"en": "paradigm", "uz": "namuna/paradigma"},
            {"en": "catalyst", "uz": "turtki/katalizator"}, {"en": "milestone", "uz": "muhim bosqich"}, {"en": "watershed", "uz": "burilish davri"},
            {"en": "sustainability", "uz": "barqarorlik"}, {"en": "conservation", "uz": "asrash/muhofaza"},
            {"en": "biodiversity", "uz": "biologik xilma-xillik"}, {"en": "climate change", "uz": "iqlim o'zgarishi"},
            {"en": "humanitarian", "uz": "insonparvarlik"}, {"en": "altruism", "uz": "boshqalarga yaxshilik qilish"},
            {"en": "solidarity", "uz": "birdamlik"}
        ]
    },
    {
        "level": "IELTS",
        "lesson_order": 10,
        "topic_title": "IELTS Reading & Listening: Paraphrasing va Distractorlarni aniqlash",
        "grammar_notes": "Matn va audioga doir professional ko'nikmalar: Skimming (umumiy ma'noni tez ilg'ash), Scanning (aniq sanalar va ismlarni topish), Synonyms matching (savoldagi so'zning matndagi sinonimini topish), Distractorlar (noto'g'ri variantlar) tuzog'idan qochish.",
        "target_words": [
            {"en": "skimming", "uz": "matnni tez ko'zdan kechirish"}, {"en": "scanning", "uz": "aniq faktni izlash"},
            {"en": "paraphrase", "uz": "boshqacha so'zlar bilan ifodalash"}, {"en": "synonym", "uz": "sinonim"},
            {"en": "antonym", "uz": "antonim"}, {"en": "distractor", "uz": "chalg'ituvchi variant"},
            {"en": "trap", "uz": "tuzoq"}, {"en": "inference", "uz": "mantiqiy xulosa"}, {"en": "imply", "uz": "sha'ma qilmoq"},
            {"en": "context", "uz": "matn mazmuni"}, {"en": "gist", "uz": "asosiy mag'zi"}, {"en": "cohesion", "uz": "izchillik"},
            {"en": "keyword", "uz": "kalit so'z"}, {"en": "comprehend", "uz": "anglamoq"}, {"en": "decipher", "uz": "shifrini yechmoq"},
            {"en": "extract", "uz": "ajratib olmoq"}, {"en": "contradict", "uz": "zid kelmoq"}, {"en": "refute", "uz": "rad etmoq"},
            {"en": "authenticate", "uz": "haqiqiyligini tasdiqlamoq"}, {"en": "verify", "uz": "tekshirmoq"},
            {"en": "accurate", "uz": "aniq"}, {"en": "ambiguous", "uz": "noaniq/ikki xil"}, {"en": "distort", "uz": "buzib ko'rsatmoq"},
            {"en": "mislead", "uz": "yo'ldan urmoq"}, {"en": "scrutinize", "uz": "sinchkovlik bilan o'rganmoq"}
        ]
    }
]


async def seed() -> None:
    """Populates the syllabus table with structured lessons."""
    await init_db()
    logger.info("Checking existing syllabus...")
    count = await count_syllabus_lessons("Beginner")
    if count >= 10:
        logger.info(f"Syllabus already seeded ({count} Beginner lessons found). Skipping or updating...")
    for item in SYLLABUS_DATA:
        await add_syllabus_lesson(
            level=item["level"],
            lesson_order=item["lesson_order"],
            topic_title=item["topic_title"],
            grammar_notes=item["grammar_notes"],
            target_words=item["target_words"],
        )
    logger.info(f"Successfully seeded {len(SYLLABUS_DATA)} lessons across all 6 levels!")


if __name__ == "__main__":
    asyncio.run(seed())
