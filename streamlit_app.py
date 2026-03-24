import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import io
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="项目数据抓取工具", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #ff4b4b; color: white; height: 3em; width: 100%; border-radius: 10px; font-size: 20px; font-weight: bold; }
    .stDownloadButton>button { background-color: #00d4aa; color: white; font-weight: bold; }
    .project-tag { padding: 5px 10px; border-radius: 8px; font-size: 14px; font-weight: bold; display: inline-block; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

st.title("📊 项目数据每日抓取工具")
st.markdown("**专业 · 简洁 · 高效** — 你的专属数据助手")

with st.sidebar:
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
    st.header("🌟 当前支持项目")
    all_projects = ["jeetup项目", "lakhup项目", "kanzplay项目", "falcowin项目", "snakerwin项目", "CW项目"]
    colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#d4a5a5"]
    for i, p in enumerate(all_projects):
        c = colors[i % len(colors)]
        st.markdown(f"<span class='project-tag' style='background-color:{c}; color:black'>{p}</span>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🛠 抓取设置")
    selected_projects = st.multiselect("选择要抓取的项目", options=all_projects, default=all_projects)
    st.caption(f"今天是 {datetime.today().strftime('%Y-%m-%d')}")

uploaded_file = st.file_uploader("🔑 上传 service_account.json 密钥文件", type=["json"])

if uploaded_file is not None:
    try:
        creds = Credentials.from_service_account_info(
            json.loads(uploaded_file.getvalue().decode("utf-8")),
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        st.success("✅ 密钥认证成功")
    except Exception as e:
        st.error(f"❌ 密钥认证失败：{e}")
        st.stop()

    st.markdown("### 📅 选择日期")
    date_options = [(datetime.today() - timedelta(days=i)).date() for i in range(30)][::-1]
    selected_dates = st.multiselect("选择日期", date_options, default=[datetime.today().date()],
                                    format_func=lambda d: d.strftime("%Y-%m-%d"))
    if not selected_dates:
        st.warning("请至少选择一个日期")
        st.stop()

    目标日期列表 = [d.strftime("%Y-%m-%d") for d in selected_dates]
    st.info(f"即将抓取：{', '.join(目标日期列表)}")

    所有表格配置 = [
        {"id": "1UeYJ9e2almMVjO_X0Ts6oE7CmCoNN5IPO82cMMugLBw", "name": "jeetup项目", "sheets": ["ADC", "UD"], "date_col": 1, "result_cols": [12,8]},
        {"id": "1F_cu4GpofGbT0DGqNzO6vTYOUKTreGTRQzIQgnhs6is", "name": "lakhup项目", "sheets": ["ADC"], "date_col": 1, "result_cols": [4,6]},
        {"id": "1LTnKqi_h_fcalboeB75IxVTGjJsh6HtO7_YOYH6oHic", "name": "kanzplay项目", "sheets": ["YSS", "FS", "UD", "pluck", "XCH"], "date_col": 1, "result_cols": [4,6]},
        {"id": "1tSrNji1nheomDN_jjHZpFVJwzY2-DGQ_N-jAqbS95yg", "name": "falcowin项目", "sheets": ["ADC", "YSS", "AdRachel", "FS", "Pizzads","UD"], "date_col": 1, "result_cols": [3,5]},
        {"id": "1laHyK6yB_mmc1ZyC79VCD3WOrkRylDXtzuGJJ9HjLhQ", "name": "snakerwin项目", "sheets": ["ADC", "YOJOY", "YSS", "Pizzads", "AdRachel", "UD", "FS"], "date_col": 1, "result_cols": [5,9]},
        {"id": "1fwzuSCipdMXBwjZtiG7OwiiW9006L-YXT_Qfk1go7ME", "name": "CW项目", "sheets": ["ADC", "YSS", "XM"], "date_col": 1, "result_cols": [3,5]}
    ]

    表格配置列表 = [cfg for cfg in 所有表格配置 if cfg["name"] in selected_projects]
    if not 表格配置列表:
        st.warning("请至少选择一个项目")
        st.stop()

    if st.button("🚀 开始抓取数据", type="primary"):
        with st.spinner("抓取中..."):
            所有结果 = []
            for 配置 in 表格配置列表:
                try:
                    ss = client.open_by_key(配置["id"])
                    for sheet_name in 配置["sheets"]:
                        try:
                            sheet = ss.worksheet(sheet_name)
                            data = sheet.get_all_values()
                            if len(data) <= 1: continue
                            for row in data[1:]:
                                if len(row) >= 配置["date_col"] and row[配置["date_col"]-1].strip() in 目标日期列表:
                                    值 = [row[i-1].strip() if i-1 < len(row) else "" for i in 配置["result_cols"]]
                                    值.extend([配置["name"], sheet_name, row[配置["date_col"]-1].strip()])
                                    所有结果.append(值)
                        except:
                            continue
                except Exception as e:
                    st.error(f"{配置['name']} 打开失败：{e}")

        if 所有结果:
            max_extra = max(len(r)-3 for r in 所有结果) if 所有结果 else 0
            表头 = ["日期", "项目名称", "投放名称", "花费（含服务费+汇损）", "广告消耗"]
            for i in range(3, max_extra+1):
                表头.append(f"额外数据 {i-2}")

            新结果 = []
            for r in 所有结果:
                固定 = [r[-1], r[-3], r[-2]]
                数据 = r[:-3]
                # 把空值或非数字转为 0.00
                处理后数据 = []
                for v in 数据:
                    try:
                        处理后数据.append(float(v.replace(',', '').replace('$', '').replace(' ', '')) if v.strip() else 0.0)
                    except:
                        处理后数据.append(0.0)
                新行 = 固定 + 处理后数据 + [""] * (max_extra - len(数据))
                新结果.append(新行)

            st.success(f"找到 {len(所有结果)} 条数据")

            # 显示时统一格式化为 $ %.2f
            column_config = {
                "日期": st.column_config.DateColumn("日期"),
            }
            column_config["花费（含服务费+汇损）"] = st.column_config.NumberColumn(
                "花费（含服务费+汇损）", format="$ %.2f"
            )
            column_config["广告消耗"] = st.column_config.NumberColumn(
                "广告消耗", format="$ %.2f"
            )
            for i in range(3, max_extra+1):
                col_name = f"额外数据 {i-2}"
                column_config[col_name] = st.column_config.NumberColumn(col_name, format="$ %.2f")

            st.dataframe(
                新结果,
                use_container_width=True,
                hide_index=True,
                column_config=column_config
            )

            # 下载文件也统一用 $ 格式
            output = io.StringIO()
            output.write("\t".join(表头) + "\n")
            for row in 新结果:
                formatted_row = []
                for idx, val in enumerate(row):
                    if idx >= 3 and isinstance(val, (int, float)):
                        formatted_row.append(f"${val:,.2f}")
                    else:
                        formatted_row.append(str(val))
                output.write("\t".join(formatted_row) + "\n")

            st.download_button(
                "📥 下载（可直接导入Excel）",
                output.getvalue(),
                file_name=f"数据_{'_'.join(目标日期列表)}.txt",
                mime="text/plain"
            )
        else:
            st.warning("没有找到匹配数据")

else:
    st.info("请先上传密钥文件")
 
