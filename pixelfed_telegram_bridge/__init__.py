import requests
from pprint import pprint
import tomllib
import argparse
import os
def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=argparse.FileType('rb'))
    parser.add_argument('post_db', type=argparse.FileType('a+', ))

    args = parser.parse_args()
    config = tomllib.load(args.config)
    pixelfed_base_url = config.get("pixelfed_base_url",os.environ.get("PIXELFED_BASE_URL"))
    pixelfed_account_id = config.get("pixelfed_account_id",os.environ.get("PIXELFED_ACCOUNT_ID"))
    telegram_channel_id = config.get("telegram_channel_id",os.environ.get("TELEGRAM_CHANNEL_ID"))
    telegram_base_url = config.get("telegram_base_url",os.environ.get("TELEGRAM_BASE_URL"))
    telegram_bot_token = config.get("telegram_bot_token",os.environ.get("TELEGRAM_BOT_TOKEN"))
    link_text = config.get("link_text",os.environ.get("LINK_TEXT"))

    fp = open("posts.txt","a+")
    posts = requests.get(f"{pixelfed_base_url}api/pixelfed/v1/accounts/{pixelfed_account_id}/statuses").json()
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
            caption = post["content_text"]+"\n<a href='"+post["url"]+"'>"+link_text+"</a>"
            if len(post["media_attachments"]) > 1:
                media = []
                for attachment in post["media_attachments"]:
                    if attachment["type"] == "image":
                        media.append({
                            "type":"photo",
                            "media":attachment["url"]
                        })
                    else:
                        raise Exception("unkown post type")
                media[-1]["parse_mode"] = "html"
                media[-1]["caption"] = caption
                if not requests.post(f"{telegram_base_url}{telegram_bot_token}/sendMediaGroup", json={
                    "chat_id":telegram_channel_id,
                    "media": media
                }).json()["ok"]:
                    raise Exception("failed to send media")
            elif len(post["media_attachments"]) == 1:
                attachment = post["media_attachments"][0]
                if attachment["type"] == "image":
                    if not requests.post(f"{telegram_base_url}{telegram_bot_token}/sendPhoto",json={
                        "chat_id":telegram_channel_id,
                        "photo":attachment["url"],
                        "parse_mode": "html",
                        "caption":caption
                    }).json()["ok"]:
                        raise Exception("failed to send photo")
                else:
                    raise Exception("unkown attachment type")
            else:
                raise Exception("non media post")
            fp.write(post["id"]+"\n")
