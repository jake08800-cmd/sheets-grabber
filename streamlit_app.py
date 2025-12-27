import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="项目数据抓取工具", layout="centered")
st.title("📊 项目数据每日抓取工具")
st.markdown("### 上传密钥 → 输入日期 → 一键抓取 → 下载结果")

with st.sidebar:
    st.header("当前项目配置")
    st.markdown("""
    - jeetup项目 → ADC sheet → 第12列  
    - lakhup项目 → ADC sheet → 第4列  
    - kanzplay项目 → YSS/FS/UD sheet → 第4列  
    - falcowin项目 → ADC/YSS/AdRachel/FS/Pizzads sheet → 第3列  
    """)
    st.caption("今天是 2025年12月27日")

uploaded_file = st.file_uploader("🔑 上传 service_account.json 密钥文件", type=["json"])

if uploaded_file is not None:
    try:
        # 读取上传的文件（是 bytes 类型）
        file_bytes = uploaded_file.getvalue()
        
        # 强制转为字符串，再解析成字典
        file_str = file_bytes.decode("utf-8")
        import json
        service_account_info = json.loads(file_str)
        
        # 现在用字典创建凭证
        creds = Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        st.success("✅ 密钥认证成功！已连接 Google Sheets")
    except json.JSONDecodeError:
        st.error("❌ 文件不是有效的 JSON 格式，请检查是否上传了正确的 service_account.json")
        st.stop()
    except Exception as e:
        st.error(f"❌ 密钥认证失败：{str(e)}")
        st.error("提示：请确保上传的是从 Google Cloud 直接下载的 .json 密钥文件，不要打开编辑过")
        st.stop()
        client = gspread.authorize(creds)
        st.success("✅ 密钥认证成功！")
    except Exception as e:
        st.error(f"❌ 密钥无效：{e}")
        st.stop()

    st.markdown("### 📅 选择要抓取的日期（支持多选）")

selected_dates = st.multiselect(
    "点选日期（按住 Command 可多选，默认今天）",
    options=[(datetime.today() - timedelta(days=i)) for i in range(30)][::-1],
    default=[datetime.today()],
    format_func=lambda d: d.strftime("%Y-%m-%d")
)

if not selected_dates:
    st.warning("请至少选择一个日期")
    st.stop()

目标日期列表 = [d.strftime("%Y-%m-%d") for d in selected_dates]
st.write(f"**将抓取：** {', '.join(目标日期列表)}")

    if not 目标日期列表:
        st.warning("请至少输入一个日期")
        st.stop()

    st.write(f"**抓取日期：** {', '.join(目标日期列表)}")

    表格配置列表 = [
        {"id": "1UeYJ9e2almMVjO_X0Ts6oE7CmCoNN5IPO82cMMugLBw", "name": "jeetup项目", "sheets": ["ADC"], "date_col": 1, "result_cols": [12]},
        {"id": "1F_cu4GpofGbT0DGqNzO6vTYOUKTreGTRQzIQgnhs6is", "name": "lakhup项目", "sheets": ["ADC"], "date_col": 1, "result_cols": [4]},
        {"id": "1LTnKqi_h_fcalboeB75IxVTGjJsh6HtO7_YOYH6oHic", "name": "kanzplay项目", "sheets": ["YSS", "FS", "UD"], "date_col": 1, "result_cols": [4]},
        {"id": "1tSrNji1nheomDN_jjHZpFVJwzY2-DGQ_N-jAqbS95yg", "name": "falcowin项目", "sheets": ["ADC", "YSS","AdRachel","FS","Pizzads"], "date_col": 1, "result_cols": [3]}
    ]

    if st.button("🚀 开始抓取", type="primary"):
        with st.spinner("正在抓取数据..."):
            所有结果 = []
            for 配置 in 表格配置列表:
                try:
                    spreadsheet = client.open_by_key(配置["id"])
                    for sheet_name in 配置["sheets"]:
                        try:
                            sheet = spreadsheet.worksheet(sheet_name)
                            data = sheet.get_all_values()
                            if len(data) > 1:
                                for row in data[1:]:
                                    if len(row) >= 配置["date_col"] and row[配置["date_col"]-1].strip() in 目标日期列表:
                                        值 = [row[i-1].strip() if i <= len(row) else "" for i in 配置["result_cols"]]
                                        值.extend([配置["name"], sheet_name, row[配置["date_col"]-1].strip()])
                                        所有结果.append(值)
                        except:
                            continue
                except Exception as e:
                    st.error(f"无法打开 {配置['name']}：{e}")

        if 所有结果:
            max_cols = max(len(r) - 3 for r in 所有结果)
            表头 = ["日期", "来源项目", "来源Sheet"] + [f"数据列{i}" for i in range(1, max_cols + 1)]

            新结果 = []
            for r in 所有结果:
                数据 = r[:-3]
                新行 = [r[-1], r[-3], r[-2]] + 数据 + [""] * (max_cols - len(数据))
                新结果.append(新行)

            st.success(f"🎉 完成！共 {len(所有结果)} 条数据")
            st.dataframe(新结果, use_container_width=True)

            output = io.StringIO()
            output.write("\t".join(表头) + "\n")
            for row in 新结果:
                output.write("\t".join(map(str, row)) + "\n")

            st.download_button(
                "📥 下载结果文件",
                data=output.getvalue(),
                file_name=f"项目数据_{'_'.join(目标日期列表)}.txt",
                mime="text/plain"
            )
        else:
            st.warning("没有找到数据")

else:
    st.info("👆 请先上传 service_account.json 文件")

st.caption("你的专属数据工具 • 永久免费")
