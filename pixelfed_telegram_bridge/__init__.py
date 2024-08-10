import requests
from pprint import pprint
import tomllib
import argparse
import os
import bleach
def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=argparse.FileType('rb'))
    parser.add_argument('post_db', type=argparse.FileType('a+', ))

    args = parser.parse_args()
    config = tomllib.load(args.config)
    pixelfed_base_url = config.get("pixelfed_base_url",os.environ.get("PIXELFED_BASE_URL"))
    pixelfed_account_id = config.get("pixelfed_account_id",os.environ.get("PIXELFED_ACCOUNT_ID"))
    telegram_channel_id = config.get("telegram_channel_id",os.environ.get("TELEGRAM_CHANNEL_ID"))
    telegram_admin_id = config.get("telegram_admin_id",os.environ.get("TELEGRAM_ADMIN_ID"))
    telegram_base_url = config.get("telegram_base_url",os.environ.get("TELEGRAM_BASE_URL"))
    telegram_bot_token = config.get("telegram_bot_token",os.environ.get("TELEGRAM_BOT_TOKEN"))
    link_text = config.get("link_text",os.environ.get("LINK_TEXT"))
    def send_post(post):
        try:
            content = ""
            if "content_text" in post:
               content = post["content_text"]
            elif "content" in post:
                content = bleach.clean(post["content"],tags=['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'tg-spoiler', 'a', 'tg-emoji', 'code', 'pre', 'blockquote'],attributes={'a': ['href']},strip=True)
            caption = content+"\n<a href='"+post["url"]+"'>"+link_text+"</a>"
            if "reblog" in post and post["reblog"] != None:
                print("reblog skipping")
            elif post["in_reply_to_id"] != None:
                print("reply ignore")
            elif len(post["media_attachments"]) > 1:
                media = []
                for attachment in post["media_attachments"]:
                    if attachment["type"] == "image":
                        media.append({
                            "type":"photo",
                            "media":attachment["preview_url"]
                        })
                    elif attachment["type"] == "video":
                        media.append({
                            "type":"video",
                            "media":attachment["url"]
                        })
                    else:
                        raise Exception("unkown post type "+attachment["type"])
                media[-1]["parse_mode"] = "html"
                media[-1]["caption"] = caption
                resp = requests.post(f"{telegram_base_url}{telegram_bot_token}/sendMediaGroup", json={
                    "chat_id":telegram_channel_id,
                    "media": media
                }).json()
                if not resp["ok"]:
                    raise Exception("failed to send media")
            elif len(post["media_attachments"]) == 1:
                attachment = post["media_attachments"][0]
                if attachment["type"] == "image":
                    resp = requests.post(f"{telegram_base_url}{telegram_bot_token}/sendPhoto",json={
                        "chat_id":telegram_channel_id,
                        "photo":attachment["preview_url"],
                        "parse_mode": "html",
                        "caption":caption
                    }).json()
                    if not resp["ok"]:
                        raise Exception("failed to send photo")
                elif attachment["type"] == "video":
                    if not requests.post(f"{telegram_base_url}{telegram_bot_token}/sendVideo",json={
                        "chat_id":telegram_channel_id,
                        "video":attachment["url"],
                        "parse_mode": "html",
                        "caption":caption
                    }).json()["ok"]:
                        raise Exception("failed to send video")
                else:
                    raise Exception("unkown attachment type"+attachment["type"])
            elif len(content) > 0:
                if not requests.post(f"{telegram_base_url}{telegram_bot_token}/sendMessage",json={
                    "chat_id":telegram_channel_id,
                    "parse_mode": "html",
                    "text":caption
                }).json()["ok"]:
                    raise Exception("failed to send photo") 
            else:
                raise Exception("non media post")
        except Exception as e:
            if not requests.post(f"{telegram_base_url}{telegram_bot_token}/sendMessage",json={
                    "chat_id":telegram_admin_id,
                    "text":str(e)
                }).json()["ok"]:
                    raise Exception("failed to send debug message") from e
            raise e
    fp = open("posts.txt","a+")
    posts = requests.get(f"{pixelfed_base_url}v1/accounts/{pixelfed_account_id}/statuses").json()
    for post in posts:
        fp.seek(0)
        found = False 
        for line in fp:
            if line.strip() == post["id"].strip():
                found = True
                break
            print(line.strip())
        print(found)
        if not found:
            send_post(post)
            fp.write(post["id"]+"\n")

