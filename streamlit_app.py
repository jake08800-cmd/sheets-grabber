import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import io
from datetime import datetime, timedelta
import json

# ================ 美化设置 ================
st.set_page_config(
    page_title="项目数据抓取工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 美化
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        height: 3em;
        width: 100%;
        border-radius: 10px;
        font-size: 20px;
        font-weight: bold;
    }
    .stDownloadButton>button {
        background-color: #00d4aa;
        color: white;
        font-weight: bold;
    }
    .project-tag {
        padding: 5px 10px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ================ 主界面 ================
st.title("📊 项目数据每日抓取工具")
st.markdown("**专业 · 简洁 · 高效** — 你的专属数据助手")

# ================ 侧边栏项目展示 + 多选 ================
with st.sidebar:
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
    st.header("🌟 当前支持项目")
    
    all_projects = [
        "jeetup项目", "lakhup项目", "kanzplay项目",
        "falcowin项目", "snakerwin项目", "CW项目"
    ]
    
    colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#d4a5a5"]

    for i, p in enumerate(all_projects):
        c = colors[i % len(colors)]
        st.markdown(f"<span class='project-tag' style='background-color:{c}; color:black'>{p}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🛠 抓取设置")
    
    selected_projects = st.multiselect(
        "选择要抓取的项目",
        options=all_projects,
        default=all_projects,
        help="不选任何项目将无法抓取"
    )
    
    st.caption(f"今天是 {datetime.today().strftime('%Y-%m-%d')}")

# 上传密钥
uploaded_file = st.file_uploader("🔑 上传 service_account.json 密钥文件（只需一次）", type=["json"])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        file_str = file_bytes.decode("utf-8")
        service_account_info = json.loads(file_str)
        creds = Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        st.success("✅ 密钥认证成功！已连接 Google Sheets")
    except Exception as e:
        st.error(f"❌ 密钥认证失败：{str(e)}")
        st.stop()

    # 多选日历
    st.markdown("### 📅 选择要抓取的日期（支持多选）")
    date_options = [(datetime.today() - timedelta(days=i)).date() for i in range(30)]
    date_options.reverse()
    default_date = datetime.today().date()
    selected_dates = st.multiselect(
        "点选日期（按住 Command 可多选，默认今天）",
        options=date_options,
        default=[default_date],
        format_func=lambda d: d.strftime("%Y-%m-%d"),
        help="可选择多个日期批量抓取"
    )

    if not selected_dates:
        st.warning("请至少选择一个日期")
        st.stop()

    目标日期列表 = [d.strftime("%Y-%m-%d") for d in selected_dates]
    st.info(f"**即将抓取：** {', '.join(目标日期列表)}")

    # 项目配置（6个项目）
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
        with st.spinner("正在从 Google Sheets 抓取数据，请稍等..."):
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
                                    if len(row) >= 配置["date_col"] and row[配置["date_col"] - 1].strip() in 目标日期列表:
                                        值 = [row[i - 1].strip() if i <= len(row) else "" for i in 配置["result_cols"]]
                                        值.extend([配置["name"], sheet_name, row[配置["date_col"] - 1].strip()])
                                        所有结果.append(值)
                        except Exception:
                            continue
                except Exception as e:
                    st.error(f"无法打开 {配置['name']}：{e}")

        if 所有结果:
            # 计算额外列的最大数量（扣除 日期/项目/投放 后的列数）
            max_extra_cols = max(len(r) - 3 for r in 所有结果) if 所有结果 else 0

            # 详细的表头
            表头 = [
                "日期",
                "项目名称",
                "投放名称",
                "花费（含服务费+汇损）",
                "广告消耗"
            ]
            # 如果有超过2个 result_cols 的项目，则补充额外列
            for i in range(3, max_extra_cols + 1):
                表头.append(f"数据列{i}")

            # 构建显示/下载用的数据行
            新结果 = []
            for r in 所有结果:
                固定部分 = [r[-1], r[-3], r[-2]]          # 日期, 项目名称, 投放名称
                数据部分 = r[:-3]                           # 所有 result_cols 的值
                填充 = [""] * (max_extra_cols - len(数据部分))
                新行 = 固定部分 + 数据部分 + 填充
                新结果.append(新行)

            st.success(f"🎉 抓取完成！共找到 **{len(所有结果)}** 条匹配数据")

            # 显示 DataFrame（日期列格式化）
            st.dataframe(
                新结果,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "日期": st.column_config.DateColumn("日期"),
                    "花费（含服务费+汇损）": st.column_config.NumberColumn("花费（含服务费+汇损）", format="¥ %.2f"),
                    "广告消耗": st.column_config.NumberColumn("广告消耗", format="¥ %.2f"),
                }
            )

            # 生成下载文件（使用中文表头 + tab 分隔）
            output = io.StringIO()
            output.write("\t".join(表头) + "\n")
            for row in 新结果:
                output.write("\t".join(map(str, row)) + "\n")

            st.download_button(
                "📥 下载结果文件（TXT / 可导入Excel）",
                data=output.getvalue(),
                file_name=f"项目数据_{'_'.join(目标日期列表)}.txt",
                mime="text/plain"
            )

        else:
            st.warning("所选日期和项目组合内没有找到任何匹配数据")

else:
    st.info("👆 请先上传 service_account.json 密钥文件")
    st.markdown("### 使用步骤：\n1. 上传密钥文件\n2. 在左侧选择项目和日期\n3. 点击开始抓取")

st.markdown("---")
st.caption("你的专属数据抓取工具 • 永久免费 • 随时随地可用")
