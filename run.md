run this command in terminal
source venv/bin/activate
python chatbot.py

=============== make admin account =============================

python -c "
from auth import Session, register
s = Session()
ok, msg = register(s, 'mubeen butt', 'karachi', '35201-1234098-3', 'mubeenbutt853@gmail.com', 'pass1234')
print(ok, msg)
"

=========== promote account to admin ======

python -c "
from db import get_connection
conn = get_connection(); cur = conn.cursor()
cur.execute(\"UPDATE users SET is_admin = TRUE WHERE email = 'mubeenbutt853@gmail.com';\")
conn.commit(); print('Rows updated:', cur.rowcount)
cur.close(); conn.close()
"