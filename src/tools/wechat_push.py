
import requests
import datetime
import json
import base64
import time
import os


class WechatPusher():
  def get_person_token(self):
    data = {
      "grant_type": "client_credential",
      "appid": os.environ.get("WECHAT_APPID", "wx1fb7fba3052d2de3"),
      "secret": os.environ.get("WECHAT_PERSON_SECRET", "")
    }
    payload = json.dumps(data,  ensure_ascii=False)
    token_res = requests.post("https://api.weixin.qq.com/cgi-bin/stable_token", data=payload)
    token_data = token_res.json()  # 修改此行  
    return token_data.get("access_token")

  def get_token(self):
    data = {
      "grant_type": "client_credential",
      "appid": os.environ.get("WECHAT_APPID", "wx1fb7fba3052d2de3"),
      "secret": os.environ.get("WECHAT_SECRET", "")
    }
    payload = json.dumps(data,  ensure_ascii=False)
    token_res = requests.post("https://api.weixin.qq.com/cgi-bin/stable_token", data=payload)
    token_data = token_res.json()  # 修改此行  
    return token_data.get("access_token")


  def draft(self, content: str):
    token = self.get_token()
    today = datetime.date.today()
    title = f"{today.year}年{today.month}月{today.day}日 AI 最新资讯"
    body = {
        "articles": [
          {
              "title": title,
              "author": "抱抱龙创意科技",
              "digest": f"{today.year}年{today.month}月{today.day}日 AI 最新资讯",
              "content": content,
              "thumb_media_id": "nsHHy-eMc4es7iSFtMtzljMGKiOcBRyDNA_KLpwsNKQmSY_IYgMrCMgbiykCKkKf",
              "need_open_comment": 1,
              "only_fans_can_comment":0,
          }
        ]
      }
    
    headers = {
      "Content-Type": "application/json; charset=utf-8",
      "Accept": "application/json"         
    }
    data = json.dumps(body,  ensure_ascii=False)
    response = requests.post(f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}", data=data, headers=headers)
    return response.json().get('media_id')  # 修改此行
      # return await response.json()  # 修改此行


  def notify(self, media_id: str):
    token = self.get_token()
    body = {
    "filter":{
        "is_to_all": True,
    },
    "mpnews":{
        "media_id": media_id
    },
      "msgtype":"mpnews",
      "send_ignore_reprint":0
    }
    headers = {
      "Content-Type": "application/json; charset=utf-8",
      "Accept": "application/json"         
    }
    data = json.dumps(body,  ensure_ascii=False)
    response = requests.post(f"https://api.weixin.qq.com/cgi-bin/message/mass/sendall?access_token={token}", data=data, headers=headers)
    msg_id = response.json().get('msg_id')  # 修改此行  
    return self.get_notify_polling(msg_id)


  def publish(self, media_id: str):
    token = self.get_token()
    body = {
      "media_id": media_id
    }
    headers = {
      "Content-Type": "application/json; charset=utf-8",
      "Accept": "application/json"         
    }
    data = json.dumps(body,  ensure_ascii=False)
    response = requests.post(f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}", data=data, headers=headers)
    publish_id = response.json().get('publish_id')  # 修改此行  
    return self.get_task_polling(publish_id)


  def publish_news(self, content: str):
    token = self.get_token()
    today = datetime.date.today()
    title = f"{today.year}年{today.month}月{today.day}日 AI 最新资讯"
    body = {
        "articles": [
          {
              "title": title,
              "author": "抱抱龙创意科技",
              "digest": f"{today.year}年{today.month}月{today.day}日 AI 最新资讯",
              "content": content,
              "thumb_media_id": "nsHHy-eMc4es7iSFtMtzljMGKiOcBRyDNA_KLpwsNKQmSY_IYgMrCMgbiykCKkKf",
              "need_open_comment": 1,
              "only_fans_can_comment":0,
          }
        ]
      }
    
    headers = {
      "Content-Type": "application/json; charset=utf-8",
      "Accept": "application/json"         
    }
    data = json.dumps(body,  ensure_ascii=False)
    response = requests.post(f"https://api.weixin.qq.com/cgi-bin/media/uploadnews?access_token={token}", data=data, headers=headers)
    print(response.json())
    return response.json().get('media_id')  # 修改此行


  def get_task_polling(self, publish_id):
    while True:
        token = self.get_token()
        body = {
          "publish_id": publish_id
        }
        publish_body = json.dumps(body,  ensure_ascii=False)      
        headers = {
          "Content-Type": "application/json; charset=utf-8",
          "Accept": "application/json"         
        }      
        response = requests.post(f"https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token={token}", data=publish_body, headers=headers)
        data = response.json()
        status = data.get('publish_status')
        if status == 1:
          time.sleep(10)
        elif status == 2:
          raise Exception('原创审核不通过!')
        elif status == 3:
          raise Exception('发布失败!')      
        elif status == 4:
          raise Exception('平台审核不通过!')        
        elif status == 0: 
          return data.get("article_detail").get("item")[0].get('article_url')

  def get_user_list(self):
    token = self.get_token()
    headers = {
      "Content-Type": "application/json; charset=utf-8",
      "Accept": "application/json"         
    }
    response = requests.get(f"https://api.weixin.qq.com/cgi-bin/user/get?access_token={token}", headers=headers)
    user_list = response.json().get('data').get('openid')  # 修改此行  
    print(user_list)
    return user_list

  def send_template_msg(self, user_list, url):
    token = self.get_token()  
    for user in user_list:
      today = datetime.date.today()    
      payload = {
        "touser": user,
        "template_id": "Bk8yDk2cpA4t_4deJlZ8Cmae5XItzocOSAiKxkpHMl8",
        "url": url,
        "topcolor": "#FF0000",
        "data": {
          "thing4": {
            "value": f"{today.year}年{today.month}月{today.day}日信息日报",
            "color": "#173177"
          },
          "time2": {
            "value": f"{today.year}-{today.month}-{today.day}",
            "color": "#173177"
          },
          "thing14": {
            "value": "抱抱龙科技",
            "color": "#173177"
          },
        }
      }
      data = json.dumps(payload,  ensure_ascii=False)
      headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json"         
      }
      res = requests.post(f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}", data=data, headers=headers)
      print(res)

  def get_notify_polling(self, msg_id: str):
    while True:
        token = self.get_token()
        body = {
          msg_id: msg_id
        }
        response = requests.post(f"https://api.weixin.qq.com/cgi-bin/message/mass/get?access_token={token}", data=body)
        data = response.json()
        status = data.get('msg_status')
        if status == "SENDING":
          time.sleep(10)
        elif status == "SEND_SUCCESS":
          return True
        elif status == "SEND_FAIL":
          raise Exception('发布失败!')      
        elif status == "DELETE":
          raise Exception('已删除!')

  def render_article(self, articles: list[dict]):
    html = ""
    for article in articles:
      title = article.get("title")

      html += f"""
        <section style="max-width: 100%; box-sizing: border-box; color: rgb(62, 62, 62); font-size: 16px; white-space: normal; background-color: rgb(255, 255, 255); overflow-wrap: break-word !important; margin-bottom: 0px;"
          <section class="" powered-by="xiumi.us" style="max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;">
            <section class="" style="max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;">
              <section class="" style="padding-right: 20px;padding-left: 20px;max-width: 100%;box-sizing: border-box;line-height: 0.8;word-wrap: break-word !important;">
            
                <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;text-align: center;word-wrap: break-word !important;">
                  <span style="max-width: 100%;line-height: 24px;box-sizing: border-box;color: rgb(26, 173, 25);font-size: 18px;word-wrap: break-word !important;">
                    {title}
                  </span>
                </p>
                <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;text-align: center;word-wrap: break-word !important;">
                  <span style="max-width: 100%;box-sizing: border-box;letter-spacing: 0px;color: rgb(26, 173, 25);font-size: 20px;word-wrap: break-word !important;">
                  </span>
                </p>
              </section>
            </section>
          </section>
        </section>
        <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">
          <br style="max-width: 100%;box-sizing: border-box !important;word-wrap: break-word !important;">
        </p>
      """
      sections = article.get("content")
      if len(sections) <= 0:
        html += f"""
          <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">
            <span>暂无内容</span>
          </p>
          <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">
            <br style="max-width: 100%;box-sizing: border-box !important;word-wrap: break-word !important;">
          </p>          
        """
      for item in sections:
        subTitle = item.get("subTitle")
        html += f"""
          <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;"><strong>{subTitle}</strong></p>
        """
        content = item.get("content")
        html += f"""
          <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">{content}</p><p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;"><br style="max-width: 100%;box-sizing: border-box !important;word-wrap: break-word !important;"></p>
        """
        link = item.get("link")
        resp = requests.get(f"https://api.2dcode.biz/v1/create-qr-code?data={link}")
        token = self.get_token()
        upload_url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
        files = {
          "media": ("qrcode.png", resp.content, "image/png")
        }
        wx_resp = requests.post(upload_url, files=files, timeout=30)
        wx_resp.raise_for_status()
        wx_json = wx_resp.json()
        if wx_json.get("url"):
            qr_image_url = wx_json["url"]
            html += f"""
              <p style="box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">
                <div>扫码查看更多</div>
                <img src="{qr_image_url}" style="box-sizing: border-box;word-wrap: break-word !important;">
                </img>
              </p>
              <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">
                <br style="max-width: 100%;box-sizing: border-box !important;word-wrap: break-word !important;">
              </p>
            """
        else:
            # 处理错误（如 40001：access_token 失效）
            html += f"""
              <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">
                <span>查看更多请移步: {link}</span>
              </p>
              <p style="max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;">
                <br style="max-width: 100%;box-sizing: border-box !important;word-wrap: break-word !important;">
              </p>
            """

    return html
