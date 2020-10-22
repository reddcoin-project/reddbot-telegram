from config import *
from util import *
tippings_json = read_users_tips_list()
for user_username in tippings_json:
    while len(tippings_json[user_username]) > 10:
        del tippings_json[user_username][1]
write_users_tips_list(tippings_json)
