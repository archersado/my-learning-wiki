from .base_agent import BaseAgent

# Assume tools are passed in __init__ or accessed globally/via context
from ..tools.publisher import Publisher
from datetime import datetime
import os
import re
import requests
import json
from ..config.settings import GITHUB_CONFIG, ECM_CONFIG
from ..tools.wechat_push import WechatPusher
from git import Repo
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.messages import HumanMessage, ChatMessage, AIMessage
import logging
import shutil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="github_push.log",
)

logger = logging.getLogger(__name__)


class DistributionExpert(BaseAgent):
    def __init__(self, llm=None, tools=None):
        super().__init__(llm, tools)
        self.wechatPusher = WechatPusher()
        self.publisher = Publisher()  # Assuming Publisher is available

    def process(self, state: dict) -> dict:
        """
        Checks for new raw data, organizes it, updates knowledge base,
        and passes relevant info to the next agent.
        This is the entry point for the main content workflow.
        """
        try:
            type = state.get("publish_type")
            summary_structed = state.get("summary_structed")
            formatted_content = state.get("formatted_content")
            filtered_content = re.sub(
                r"^---\ntitle.*?\n---\n", "", formatted_content, flags=re.DOTALL
            ).strip()
            match type:
                case "daily":
                    # self.publish_website(formatted_content)
                    # self.publish_ecm(filtered_content, "rss_feeder", "dt_push_ai", "78b4e18bf66f9df456e7749be660c441")
                    # self.publish_ecm(filtered_content, "dt_rss_push", "dt_rss_push_ai", "600335c11fadcedd5540e4eb5f50c45c") 
                    self.publish_wechat(filtered_content)

        except Exception as e:
            print(f"Error inserting articles into MongoDB: {e}")

        # # 1. Retrieve new raw data since last run
        # new_raw_data = self.raw_data_storage.get_new_raw_data(self.last_processed_timestamp)

    def publish_ecm(self, content, app_code, notice_code, secret):
        """Send content to ECM message system."""
        try:
            api_url = ECM_CONFIG["api_url"]
            headers = {
                "Content-Type": "application/json",
                "x-gw-accesskey": ECM_CONFIG["access_key"],
            }

            params = {
                "appkey": app_code,
                "appsecret": secret
            }

            # 准备请求数据
            payload = {
                "appCode": app_code,
                "code": notice_code,
                "context": json.dumps({"content": content}),
            }

            # 发送请求
            response = requests.post(
                api_url, headers=headers, json=payload, params=params, timeout=100000
            )
            response.raise_for_status()

            # 处理响应
            result = response.json()
            if result.get("success") == True:
                print("Successfully sent message to ECM")
                return True
            else:
                print(f"Failed to send message to ECM: {result.get('message')}")
                return False

        except requests.RequestException as e:
            print(f"Error sending message to ECM: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error in publish_ecm: {str(e)}")
            return False


    def to_wechat_blocks(self, items: list[dict[str, any]]) -> list[dict[str, any]]:
        groups = {}
        for it in items:
            section = (it.get("section") or "其它").strip()
            groups.setdefault(section, []).append({
                "subTitle": (it.get("title") or "").strip(),
                "content": (it.get("content") or "").strip(),
                "link": it.get("link"),
                "linkTitle": (it.get("linkTitle") or "来源").strip(),
            })
        blocks = []
        for section, arr in groups.items():
            blocks.append({
                "title": section,
                "content": arr
            })
        return blocks

    def publish_wechat(self, content):
        try:
            articles = []
            if isinstance(content, list) and content:
                articles = self.to_wechat_blocks(content)
            html = self.wechatPusher.render_article(articles)
            media_id = self.wechatPusher.draft(html)
            url = self.wechatPusher.publish(media_id)
            user_list = self.wechatPusher.get_user_list()
            self.wechatPusher.send_template_msg(user_list, url)
        except Exception as e:
            print(f"Error in publish_wechat: {e}")
            return False


    def create_file(self, filepath, content):
        with open(filepath, "w", encoding="utf-8") as f:
            # 写入内容
            if isinstance(content, dict):
                # 如果内容是字典，遍历并格式化
                for key, value in content.items():
                    f.write(f"## {key}\n\n")
                    f.write(f"{value}\n\n")
            elif isinstance(content, list):
                # 如果内容是列表，遍历并格式化
                for item in content:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            f.write(f"## {key}\n\n")
                            f.write(f"{value}\n\n")
                    else:
                        f.write(f"{item}\n\n")
            else:
                # 如果内容是字符串，直接写入
                f.write(f"{content}\n")

        print(f"Successfully created daily file: {filepath}")

    def publish_website(self, content):
        """Creates a markdown file with the content."""
        try:
            # 获取当前日期
            today = datetime.now().strftime("%Y-%m-%d")

            # 创建文件名
            filename_zh = f"{today}-AI-Report.mdx"
            filename_en = f"{today}-AI-Report-en.mdx"

            # 确保输出目录存在+
            
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 完整的文件路径
            filepath_zh = os.path.join(output_dir, filename_zh)
            self.create_file(filepath_zh, content)

            # 写入文件

            prompt = f"""
            将以下全文翻译成 英文, 并用 markdown 格式返回

            要求:
            1. 不要修改原始文章的格式，只是做翻译
            2. 直接返回翻译内容，不要用 ```markdown 包裹

            """
            input = f"""
                原始内容为:
                {content}
            """

            messages = [AIMessage(content=prompt), HumanMessage(content=input)]

            # Use the LLM to extract content
            response = self.llm.invoke(messages)
            translate = response.content.strip()
            filepath_en = os.path.join(output_dir, filename_en)
            self.create_file(filepath_en, translate)


            # 使用配置
            repo_path = GITHUB_CONFIG["repo_path"]
            target_dir = GITHUB_CONFIG["target_dir"]
            github_token = GITHUB_CONFIG["github_token"]
            repo_url = GITHUB_CONFIG["repo_url"]
            repo =  f"https://{github_token}@{repo_url}" 

        
            logging.info(f"Starting to push file")
            success = self.push_to_github(repo_path, target_dir, output_dir, repo)

            if success:
                logging.info(f"Successfully pushed to GitHub")
            else:
                logging.error(f"Failed to push to GitHub")

            # 清理输出目录
            self.clean_output_directory(output_dir)            
            return success
        except Exception as e:
            logging.error(f"Error in publish_website: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def push_to_github(self, repo_path, target_dir, output_dir, repo_url):
        """Push file to GitHub with retry mechanism."""
        try:
            if not os.path.exists(repo_path):
                # 如果仓库不存在，克隆它
                repo = Repo.clone_from(
                   repo_url, repo_path
                )
            else:
                # 如果仓库存在，打开它
                repo = Repo(repo_path)
            target_path = os.path.join(repo_path, target_dir)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            files = []
            for filename in os.listdir(output_dir):
                file_path = os.path.join(output_dir, filename)
                # 只获取文件，不包含目录
                if os.path.isfile(file_path):
                    if "-en" in filename:
                        target_file = os.path.join(target_path, 'en', filename)
                    else:
                        target_file = os.path.join(target_path, 'zh', filename)
                    shutil.copy(file_path, target_file)
                    files.append({
                        'filename': filename,
                        'path': target_file
                    })

            # 确保是最新版本
            origin = repo.remote(name="origin")
            origin.pull()

            # 添加文件
            # repo.index.add([os.path.join(target_dir, filename)])
            for f in files:
                repo.index.add([ f.get("path") ])
            # 提交
            commit_message = (
                f"Add daily report for {datetime.now().strftime('%Y-%m-%d')}"
            )
            repo.index.commit(commit_message)

            # 推送
            origin.push()

            return True
        except Exception as e:
            print(f"Error in push_to_github: {e}")
            raise

    def clean_output_directory(self, output_dir):
        """清理输出目录下的所有文件"""
        try:
            if os.path.exists(output_dir):
                # 删除目录及其所有内容
                shutil.rmtree(output_dir)
                # 重新创建空目录
                os.makedirs(output_dir)
                logger.info(f"Successfully cleaned {output_dir}")
            else:
                logger.warning(f"Directory {output_dir} does not exist")
        except Exception as e:
            logger.error(f"Error cleaning {output_dir}: {e}")
            raise
