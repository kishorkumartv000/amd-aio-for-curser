class HI(object):
    __language__ = 'hi'
#----------------
#
# बुनियादी जानकारी
#
#----------------
    WELCOME_MSG = "नमस्ते {}"
    DOWNLOADING = 'डाउनलोड हो रहा है........'
    DOWNLOAD_PROGRESS = """
<b>╭─ प्रगति
│
├ {0}
│
├ पूरा हुआ : <code>{1} / {2}</code>
│
├ शीर्षक : <code>{3}</code>
│
╰─ प्रकार : <code>{4}</code></b>
"""
    UPLOADING = 'अपलोड हो रहा है........'
    ZIPPING = 'जिप किया जा रहा है........'
    TASK_COMPLETED = "डाउनलोड समाप्त हुआ"




#----------------
#
# सेटिंग पैनल
#
#----------------
    INIT_SETTINGS_PANEL = '<b>बॉट सेटिंग्स में आपका स्वागत है</b>'
    LANGUAGE_PANEL = 'यहां बॉट की भाषा चुनें'

    TELEGRAM_PANEL = """
<b>टेलीग्राम सेटिंग्स</b>

एडमिन्स : {2}
अधिकृत उपयोगकर्ता : {3}
अधिकृत चैट्स : {4}
"""
    BAN_AUTH_FORMAT = 'उपयोग करें /command {userid}'
    BAN_ID = 'हटा दिया गया {}'
    USER_DOEST_EXIST = "यह आईडी मौजूद नहीं है"
    USER_EXIST = 'यह आईडी पहले से मौजूद है'
    AUTH_ID = 'सफलतापूर्वक अधिकृत'

    RCLONE_PANEL = '<b>Rclone सेटिंग्स</b>'
    RCLONE_STATUS = 'स्थिति: {}'
    RCLONE = 'Rclone'
    RCLONE_UPLOAD_PATH = 'अपलोड पथ: {}'
    RCLONE_REMOTE_BROWSE = '🗂️ रिमोट ब्राउज़ करें'
    RCLONE_SET_UPLOAD_PATH = '📂 अपलोड पथ सेट करें'
    RCLONE_IMPORT_CONF = '📥 rclone.conf आयात करें'
    RCLONE_COPY = '📄 क्लाउड → क्लाउड कॉपी'
    RCLONE_MOVE = '📦 क्लाउड → क्लाउड मूव'
    RCLONE_BACK = '🔙 वापस'
    RCLONE_SEND_CONF = 'कृपया अपना rclone.conf यहाँ भेजें.'
    RCLONE_CONF_SAVED = '✅ rclone.conf सहेजा गया.'
    RCLONE_DEST_SET = '✅ अपलोड पथ सेट: {}'
    RCLONE_BROWSE_HEADER = '<b>ब्राउज़िंग:</b> {}'
    RCLONE_BROWSE_NEXT = 'Next ▶️'
    RCLONE_BROWSE_PREV = '◀️ Prev'
    RCLONE_BROWSE_UP = '⬆️ ऊपर'
    RCLONE_SELECT_THIS = 'यह फ़ोल्डर चुनें'
    RCLONE_PICK_SOURCE = 'सोर्स चुनें'
    RCLONE_PICK_DEST = 'डेस्टिनेशन चुनें'
    RCLONE_OP_IN_PROGRESS = 'कार्य चल रहा है...'
    RCLONE_OP_DONE = '✅ कार्य पूरा हुआ.'
    RCLONE_OP_FAILED = '❌ विफल: {}'

#----------------
#
# बटन
#
#----------------
    MAIN_MENU_BUTTON = 'मुख्य मेन्यू'
    CLOSE_BUTTON = 'बंद करें'

    TELEGRAM = 'टेलीग्राम'
    CORE = 'कोर'
    PROVIDERS = 'प्रोवाइडर्स'

    LANGUAGE = 'भाषा'
    

    BOT_PUBLIC = 'बॉट सार्वजनिक - {}'
    BOT_LANGUAGE = 'भाषा'
    ANTI_SPAM = 'एंटी स्पैम - {}'

    POST_ART_BUT = "आर्ट पोस्टर : {}"

    SORT_PLAYLIST = 'प्लेलिस्ट को क्रमबद्ध करें : {}'

    PLAYLIST_CONC_BUT = "प्लेलिस्ट एक साथ : {}"
    ARTIST_BATCH_BUT = 'कलाकार बैच अपलोड : {}'



    RCLONE_LINK = 'प्रत्यक्ष लिंक'
    INDEX_LINK = 'इंडेक्स लिंक'
#----------------
#
# त्रुटियाँ
#
#----------------
    ERR_NO_LINK = 'कोई लिंक नहीं मिला :('
    ERR_LINK_RECOGNITION = "क्षमा करें, दिए गए लिंक को पहचानने में असमर्थ हैं।"

#----------------
#
# ट्रैक और एल्बम पोस्ट्स
#
#----------------
    ALBUM_TEMPLATE = """
🎶 <b>शीर्षक :</b> {title}
👤 <b>कलाकार :</b> {artist}
📅 <b>रिलीज़ तिथि :</b> {date}
🔢 <b>कुल ट्रैक :</b> {totaltracks}
📀 <b>कुल वॉल्यूम :</b> {totalvolume}
💫 <b>गुणवत्ता :</b> {quality}
📡 <b>प्रोवाइडर :</b> {provider}
🔞 <b>स्पष्ट :</b> {explicit}
"""

    PLAYLIST_TEMPLATE = """
🎶 <b>शीर्षक :</b> {title}
🔢 <b>कुल ट्रैक :</b> {totaltracks}
💫 <b>गुणवत्ता :</b> {quality}
📡 <b>प्रोवाइडर :</b> {provider}
"""

    SIMPLE_TITLE = """
नाम : {0}
प्रकार : {1}
प्रोवाइडर : {2}
"""
