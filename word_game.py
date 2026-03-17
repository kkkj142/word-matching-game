import streamlit as st
import pandas as pd
import random
import time
import os
import requests
from pathlib import Path

# 获取当前脚本所在目录
script_dir = Path(__file__).parent
# 切换到脚本所在目录
os.chdir(script_dir)

# 设置页面
st.set_page_config(page_title="单词对对碰", page_icon="📚", layout="wide")

# 标题和说明
st.title("📚 单词对对碰游戏")
st.markdown("""
欢迎来到单词对对碰游戏！这个游戏将帮助你记忆英文单词和中文释义。
请从右侧选择与左侧单词对应的正确释义。
""")


# 读取单词数据
@st.cache_data
def load_word_data(file_name="dictionary.xlsx", sheet_name="全版"):
    try:
        # 使用与程序相同路径下的Excel文件
        file_path = Path(__file__).parent / file_name
        
        # 检查文件是否存在
        if not file_path.exists():
            st.error(f"词库文件不存在: {file_path}")
            # 使用示例数据作为备用
            return pd.DataFrame({
                '英文': ['apple', 'banana', 'computer', 'language', 'book', 'student', 'teacher', 'water', 'fire', 'earth'],
                '中文': ['苹果', '香蕉', '电脑', '语言', '书', '学生', '老师', '水', '火', '地球']
            })
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 根据不同文件的列名进行处理
        if '单词' in df.columns and '释义' in df.columns:
            # 六级词汇正序版.xlsx的列名处理
            df = df.rename(columns={'单词': '英文', '释义': '中文'})
            # 清理释义中的多余换行符
            df['中文'] = df['中文'].str.replace('\n', ' ')
        
        # 清理数据 - 移除空行和无效数据
        df = df.dropna(subset=['英文', '中文'])
        # 移除重复项
        df = df.drop_duplicates(subset=['英文'])
        return df
    except Exception as e:
        st.error(f"无法加载单词数据: {e}")
        # 使用示例数据作为备用
        return pd.DataFrame({
            '英文': ['apple', 'banana', 'computer', 'language', 'book', 'student', 'teacher', 'water', 'fire', 'earth'],
            '中文': ['苹果', '香蕉', '电脑', '语言', '书', '学生', '老师', '水', '火', '地球']
        })


# 添加词库选择相关状态
if 'selected_dictionary' not in st.session_state:
    st.session_state.selected_dictionary = "dictionary.xlsx"
if 'selected_sheet' not in st.session_state:
    st.session_state.selected_sheet = "全版"

# 初始化游戏状态
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'current_word_index' not in st.session_state:
    st.session_state.current_word_index = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'used_indices' not in st.session_state:
    st.session_state.used_indices = set()
if 'options' not in st.session_state:
    st.session_state.options = []
if 'current_english' not in st.session_state:
    st.session_state.current_english = ""
if 'current_chinese' not in st.session_state:
    st.session_state.current_chinese = ""
if 'selected_option' not in st.session_state:
    st.session_state.selected_option = None
if 'answer_submitted' not in st.session_state:
    st.session_state.answer_submitted = False
if 'show_difficulty_modal' not in st.session_state:
    st.session_state.show_difficulty_modal = False
if 'game_history' not in st.session_state:
    st.session_state.game_history = []
if 'wrong_answers' not in st.session_state:
    st.session_state.wrong_answers = []
if 'review_mode' not in st.session_state:
    st.session_state.review_mode = False
if 'current_review_index' not in st.session_state:
    st.session_state.current_review_index = 0
if 'error_notebook' not in st.session_state:
    st.session_state.error_notebook = []
if 'error_notebook_mode' not in st.session_state:
    st.session_state.error_notebook_mode = False
if 'current_error_notebook_index' not in st.session_state:
    st.session_state.current_error_notebook_index = 0

# 统计游戏使用次数（使用CountAPI实现，支持GitHub部署）
# 检查是否已经在本次会话中增加过使用次数
if 'usage_count_increased' not in st.session_state:
    try:
        # 使用CountAPI来存储使用次数
        # 这里使用一个固定的key，你可以替换为自己的key
        count_api_key = "word_game_usage"
        count_api_url = f"https://api.countapi.xyz"
        
        # 增加使用次数
        increment_url = f"{count_api_url}/hit/{count_api_key}"
        response = requests.get(increment_url, timeout=5)
        if response.status_code == 200:
            usage_count = response.json().get('value', 0)
        else:
            usage_count = 0
        
        # 标记已经增加过使用次数
        st.session_state.usage_count_increased = True
    except Exception as e:
        # 如果API调用失败，回退到本地文件存储（仅限本地运行）
        usage_count_file = Path(__file__).parent / "usage_count.txt"
        try:
            if usage_count_file.exists():
                with open(usage_count_file, 'r', encoding='utf-8') as f:
                    usage_count = int(f.read().strip())
            else:
                usage_count = 0
            
            # 增加使用次数
            usage_count += 1
            
            # 保存使用次数
            with open(usage_count_file, 'w', encoding='utf-8') as f:
                f.write(str(usage_count))
            
            # 标记已经增加过使用次数
            st.session_state.usage_count_increased = True
        except Exception as e:
            usage_count = 0
else:
    # 如果已经增加过，获取当前使用次数
    try:
        # 使用CountAPI来获取使用次数
        count_api_key = "word_game_usage"
        count_api_url = f"https://api.countapi.xyz"
        
        # 获取当前使用次数
        get_url = f"{count_api_url}/get/{count_api_key}"
        response = requests.get(get_url, timeout=5)
        if response.status_code == 200:
            usage_count = response.json().get('value', 0)
        else:
            usage_count = 0
    except Exception as e:
        # 如果API调用失败，回退到本地文件存储
        usage_count_file = Path(__file__).parent / "usage_count.txt"
        try:
            if usage_count_file.exists():
                with open(usage_count_file, 'r', encoding='utf-8') as f:
                    usage_count = int(f.read().strip())
            else:
                usage_count = 0
        except Exception as e:
            usage_count = 0

# 可用的词库文件和对应的工作表
available_dictionaries = {
    "基础词库": {
        "file": "dictionary.xlsx",
        "sheets": ["全版", "中译英版", "英译中版"]
    },
    "六级词汇": {
        "file": "六级词汇正序版.xlsx",
        "sheets": ["Sheet1"]
    }
}

# 加载选定的词库数据
dictionary_info = None
for name, info in available_dictionaries.items():
    if info["file"] == st.session_state.selected_dictionary:
        dictionary_info = name
        break

df = load_word_data(st.session_state.selected_dictionary, st.session_state.selected_sheet)
total_words = len(df)


# 生成新单词的函数
def generate_new_word():
    # 确保不重复使用单词
    available_indices = set(range(total_words)) - st.session_state.used_indices
    if not available_indices:
        st.session_state.used_indices = set()
        available_indices = set(range(total_words))

    current_index = random.choice(list(available_indices))
    st.session_state.used_indices.add(current_index)

    current_word = df.iloc[current_index]
    st.session_state.current_english = current_word['英文']
    st.session_state.current_chinese = current_word['中文']

    # 生成选项（3个错误选项 + 1个正确选项）
    incorrect_indices = random.sample(
        list(set(range(total_words)) - {current_index} - st.session_state.used_indices),
        min(3, total_words - len(st.session_state.used_indices) - 1)
    )
    incorrect_options = [df.iloc[i]['中文'] for i in incorrect_indices]

    options = incorrect_options + [st.session_state.current_chinese]
    random.shuffle(options)
    st.session_state.options = options
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    # 添加一个哈希值来标识当前单词，确保选项不会在每次页面刷新时重新生成
    import hashlib
    word_hash = hashlib.md5((st.session_state.current_english + st.session_state.current_chinese).encode()).hexdigest()
    st.session_state.current_word_hash = word_hash


# 游戏控制侧边栏
with st.sidebar:
    st.header("游戏控制")
    

    
    # 开始游戏按钮
    if st.button("🎮 开始游戏"):
        st.session_state.show_difficulty_modal = True
        st.rerun()
    

    
    # 游戏进行中显示游戏统计
    elif st.session_state.game_started:

        # 显示游戏统计
        st.subheader("游戏统计")
        elapsed_time = time.time() - st.session_state.start_time if st.session_state.start_time else 0
        st.metric("得分", st.session_state.score)
        st.metric("进度", f"{st.session_state.current_word_index}/{min(20, total_words)}")
        st.metric("用时", f"{int(elapsed_time)}秒")

        # 进度条
        st.progress(st.session_state.current_word_index / min(20, total_words))

        if st.button("🔄 继续游戏"):
            st.session_state.game_started = False
            st.rerun()
    else:
        st.info("点击「开始游戏」按钮开始游戏")

# 难度选择模态弹窗
if st.session_state.show_difficulty_modal:
    # 使用Streamlit的内置容器
    with st.container():
        # 标题
        st.subheader("选择游戏难度")
        
        # 难度选择
        difficulty = st.radio(
            "请选择你想要使用的词库难度：",
            ["四级", "六级"],
            key="difficulty_select",
            horizontal=False
        )
        
        # 按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("取消", use_container_width=True):
                st.session_state.show_difficulty_modal = False
                st.rerun()
        with col2:
            if st.button("确认", use_container_width=True):
                # 根据选择的难度设置词库
                if difficulty == "四级":
                    st.session_state.selected_dictionary = "dictionary.xlsx"
                    st.session_state.selected_sheet = "全版"
                else:  # 六级
                    st.session_state.selected_dictionary = "六级词汇正序版.xlsx"
                    st.session_state.selected_sheet = "Sheet1"
                
                # 开始游戏
                st.session_state.show_difficulty_modal = False
                st.session_state.game_started = True
                st.session_state.current_word_index = 0
                st.session_state.score = 0
                st.session_state.start_time = time.time()
                st.session_state.used_indices = set()
                st.session_state.game_history = []
                st.session_state.wrong_answers = []
                st.session_state.review_mode = False
                st.session_state.current_review_index = 0
                generate_new_word()
                st.rerun()

# 游戏主区域
elif st.session_state.game_started:
    # 选择当前单词
    if st.session_state.current_word_index < min(20, total_words):
        # 显示当前单词
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("英文单词")
            st.markdown(f"<h1 style='text-align: center; color: blue;'>{st.session_state.current_english}</h1>",
                        unsafe_allow_html=True)

        with col2:
            st.subheader("选择正确的中文释义")
            # 创建选项按钮
            selected_option = st.radio(
                "请选择:",
                st.session_state.options,
                key=f"option_{st.session_state.current_word_index}_{st.session_state.get('current_word_hash', 0)}",
                index=None if st.session_state.selected_option is None else st.session_state.options.index(
                    st.session_state.selected_option) if st.session_state.selected_option in st.session_state.options else None
            )

            # 更新选中的选项
            if selected_option is not None:
                st.session_state.selected_option = selected_option

            # 只有在有选择且未提交时才启用提交按钮
            if st.button("提交答案", use_container_width=True,
                         disabled=st.session_state.selected_option is None or st.session_state.answer_submitted):
                st.session_state.answer_submitted = True

                is_correct = st.session_state.selected_option == st.session_state.current_chinese
                
                # 记录答题情况
                st.session_state.game_history.append({
                    '英文': st.session_state.current_english,
                    '正确答案': st.session_state.current_chinese,
                    '用户选择': st.session_state.selected_option,
                    '是否正确': is_correct
                })
                
                # 如果答错了，添加到错题记录
                if not is_correct:
                    st.session_state.wrong_answers.append({
                        '英文': st.session_state.current_english,
                        '正确答案': st.session_state.current_chinese
                    })
                    
                    # 添加到错题本（避免重复）
                    error_item = {
                        '英文': st.session_state.current_english,
                        '正确答案': st.session_state.current_chinese
                    }
                    # 检查错题本中是否已有该题
                    if not any(item['英文'] == error_item['英文'] for item in st.session_state.error_notebook):
                        st.session_state.error_notebook.append(error_item)

                if is_correct:
                    st.session_state.score += 1
                    st.success("✅ 正确！")
                else:
                    st.error(f"❌ 错误！正确答案是: {st.session_state.current_chinese}")

                # 短暂延迟让用户看到结果
                import time
                time.sleep(1.5)
                
                # 进入下一个单词
                st.session_state.current_word_index += 1
                if st.session_state.current_word_index < min(20, total_words):
                    generate_new_word()
                st.rerun()

    else:
        # 游戏结束
        st.balloons()
        st.success("🎉 游戏完成！")
        elapsed_time = time.time() - st.session_state.start_time
        st.subheader(f"最终得分: {st.session_state.score}/20")
        st.subheader(f"用时: {int(elapsed_time)}秒")

        # 显示所有题目的结果
        st.markdown("---")
        st.subheader("📋 答题结果")
        
        # 创建结果表格
        result_df = pd.DataFrame(st.session_state.game_history)
        
        # 添加序号列
        result_df.insert(0, '序号', range(1, len(result_df) + 1))
        
        # 为是否正确列添加颜色标记
        def highlight_correct(row):
            return ['background-color: lightgreen' if row['是否正确'] else 'background-color: lightcoral' for _ in row]
        
        styled_df = result_df.style.apply(highlight_correct, axis=1)
        st.dataframe(styled_df, use_container_width=True)

        # 错题重做功能
        if st.session_state.wrong_answers:
            st.markdown("---")
            st.subheader("🔄 错题重做")
            st.write(f"你有 {len(st.session_state.wrong_answers)} 道题答错了，点击下方按钮开始重做。")
            
            if st.button("开始重做错题", use_container_width=True):
                st.session_state.game_started = False
                st.session_state.review_mode = True
                st.session_state.current_review_index = 0
                st.rerun()

        # 错题本功能
        if st.session_state.error_notebook:
            st.markdown("---")
            st.subheader("📚 错题本")
            st.write(f"错题本中共有 {len(st.session_state.error_notebook)} 道题。")
            
            # 显示错题本内容
            error_notebook_df = pd.DataFrame(st.session_state.error_notebook)
            error_notebook_df.insert(0, '序号', range(1, len(error_notebook_df) + 1))
            st.dataframe(error_notebook_df, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("重做错题本中的题目", use_container_width=True):
                    st.session_state.game_started = False
                    st.session_state.error_notebook_mode = True
                    st.session_state.current_error_notebook_index = 0
                    st.rerun()
            with col2:
                if st.button("清空错题本", use_container_width=True):
                    st.session_state.error_notebook = []
                    st.rerun()

        if st.button("再玩一次", use_container_width=True):
            st.session_state.game_started = False
            st.session_state.game_history = []
            st.session_state.wrong_answers = []
            st.session_state.review_mode = False
            st.session_state.current_review_index = 0
            st.rerun()

# 错题重做模式
elif st.session_state.review_mode:
    if st.session_state.wrong_answers:
        # 获取当前错题
        current_review_index = st.session_state.current_review_index
        if current_review_index < len(st.session_state.wrong_answers):
            current_error = st.session_state.wrong_answers[current_review_index]
            st.session_state.current_english = current_error['英文']
            st.session_state.current_chinese = current_error['正确答案']
            
            # 只有在需要时生成选项（避免每次刷新都重新生成）
            if 'current_review_options' not in st.session_state or st.session_state.get('last_review_index', -1) != current_review_index:
                # 生成选项（3个错误选项 + 1个正确选项）
                incorrect_options = []
                # 从词库中随机选择3个不同的中文释义作为错误选项
                while len(incorrect_options) < 3:
                    random_index = random.randint(0, total_words - 1)
                    random_chinese = df.iloc[random_index]['中文']
                    if random_chinese != st.session_state.current_chinese and random_chinese not in incorrect_options:
                        incorrect_options.append(random_chinese)
                
                options = incorrect_options + [st.session_state.current_chinese]
                random.shuffle(options)
                st.session_state.current_review_options = options
                st.session_state.last_review_index = current_review_index
            
            # 使用保存的选项
            options = st.session_state.current_review_options
            
            # 显示当前错题
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("英文单词 (错题重做)")
                st.markdown(f"<h1 style='text-align: center; color: orange;'>{st.session_state.current_english}</h1>",
                            unsafe_allow_html=True)

            with col2:
                st.subheader("选择正确的中文释义")
                # 创建选项按钮
                selected_option = st.radio(
                    "请选择:",
                    options,
                    key=f"review_option_{current_review_index}",
                    index=None
                )

                # 只有在有选择时才启用提交按钮
                if st.button("提交答案", use_container_width=True, disabled=selected_option is None):
                    is_correct = selected_option == st.session_state.current_chinese

                    if is_correct:
                        st.success("✅ 正确！这道题已从错题列表中移除。")
                        # 从错题列表中移除这道题
                        st.session_state.wrong_answers.pop(current_review_index)
                        # 保持当前索引不变，因为列表长度减少了1
                        # 清除选项缓存
                        if 'current_review_options' in st.session_state:
                            del st.session_state.current_review_options
                    else:
                        st.error(f"❌ 错误！正确答案是: {st.session_state.current_chinese}")
                        # 继续下一道错题
                        st.session_state.current_review_index += 1
                        # 清除选项缓存
                        if 'current_review_options' in st.session_state:
                            del st.session_state.current_review_options

                    # 短暂延迟让用户看到结果
                    import time
                    time.sleep(1.5)
                    
                    # 检查是否还有错题
                    if not st.session_state.wrong_answers:
                        st.session_state.review_mode = False
                        # 清除选项缓存
                        if 'current_review_options' in st.session_state:
                            del st.session_state.current_review_options
                        if 'last_review_index' in st.session_state:
                            del st.session_state.last_review_index
                        st.rerun()
                    elif st.session_state.current_review_index >= len(st.session_state.wrong_answers):
                        st.session_state.current_review_index = 0
                        # 清除选项缓存
                        if 'current_review_options' in st.session_state:
                            del st.session_state.current_review_options
                        st.rerun()
                    st.rerun()
        else:
            # 所有错题都已重做完成
            st.session_state.review_mode = False
            st.rerun()
    else:
        # 没有错题
        st.success("✅ 没有错题需要重做！")
        if st.button("返回游戏", use_container_width=True):
            st.session_state.review_mode = False
            st.rerun()

# 错题本重做模式
elif st.session_state.error_notebook_mode:
    if st.session_state.error_notebook:
        # 获取当前错题
        current_index = st.session_state.current_error_notebook_index
        if current_index < len(st.session_state.error_notebook):
            current_error = st.session_state.error_notebook[current_index]
            st.session_state.current_english = current_error['英文']
            st.session_state.current_chinese = current_error['正确答案']
            
            # 只有在需要时生成选项（避免每次刷新都重新生成）
            if 'current_error_notebook_options' not in st.session_state or st.session_state.get('last_error_notebook_index', -1) != current_index:
                # 生成选项（3个错误选项 + 1个正确选项）
                incorrect_options = []
                # 从词库中随机选择3个不同的中文释义作为错误选项
                while len(incorrect_options) < 3:
                    random_index = random.randint(0, total_words - 1)
                    random_chinese = df.iloc[random_index]['中文']
                    if random_chinese != st.session_state.current_chinese and random_chinese not in incorrect_options:
                        incorrect_options.append(random_chinese)
                
                options = incorrect_options + [st.session_state.current_chinese]
                random.shuffle(options)
                st.session_state.current_error_notebook_options = options
                st.session_state.last_error_notebook_index = current_index
            
            # 使用保存的选项
            options = st.session_state.current_error_notebook_options
            
            # 显示当前错题
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("英文单词 (错题本重做)")
                st.markdown(f"<h1 style='text-align: center; color: purple;'>{st.session_state.current_english}</h1>",
                            unsafe_allow_html=True)

            with col2:
                st.subheader("选择正确的中文释义")
                # 创建选项按钮
                selected_option = st.radio(
                    "请选择:",
                    options,
                    key=f"error_notebook_option_{current_index}",
                    index=None
                )

                # 只有在有选择时才启用提交按钮
                if st.button("提交答案", use_container_width=True, disabled=selected_option is None):
                    is_correct = selected_option == st.session_state.current_chinese

                    if is_correct:
                        st.success("✅ 正确！这道题已从错题本中移除。")
                        # 从错题本中移除这道题
                        st.session_state.error_notebook.pop(current_index)
                        # 保持当前索引不变，因为列表长度减少了1
                        # 清除选项缓存
                        if 'current_error_notebook_options' in st.session_state:
                            del st.session_state.current_error_notebook_options
                    else:
                        st.error(f"❌ 错误！正确答案是: {st.session_state.current_chinese}")
                        # 继续下一道错题
                        st.session_state.current_error_notebook_index += 1
                        # 清除选项缓存
                        if 'current_error_notebook_options' in st.session_state:
                            del st.session_state.current_error_notebook_options

                    # 短暂延迟让用户看到结果
                    import time
                    time.sleep(1.5)
                    
                    # 检查是否还有错题
                    if not st.session_state.error_notebook:
                        st.session_state.error_notebook_mode = False
                        # 清除选项缓存
                        if 'current_error_notebook_options' in st.session_state:
                            del st.session_state.current_error_notebook_options
                        if 'last_error_notebook_index' in st.session_state:
                            del st.session_state.last_error_notebook_index
                        st.rerun()
                    elif st.session_state.current_error_notebook_index >= len(st.session_state.error_notebook):
                        st.session_state.current_error_notebook_index = 0
                        # 清除选项缓存
                        if 'current_error_notebook_options' in st.session_state:
                            del st.session_state.current_error_notebook_options
                        st.rerun()
                    st.rerun()
        else:
            # 所有错题都已重做完成
            st.session_state.error_notebook_mode = False
            st.rerun()
    else:
        # 错题本为空
        st.success("✅ 错题本为空！")
        if st.button("返回游戏", use_container_width=True):
            st.session_state.error_notebook_mode = False
            st.rerun()

else:
    # 游戏说明
    st.info("""
    ### 游戏说明:
    1. 点击"开始游戏"按钮开始游戏
    2. 选择你想要使用的词库难度
    3. 你会看到英文单词和四个中文释义选项
    4. 选择你认为正确的中文释义
    5. 每答对一题得1分，共20题
    6. 完成后查看你的得分和用时
    7. 错题会自动收录到错题本中
    8. 可以在游戏结束后查看错题本并进行重做
    """)

    # 显示当前选择的词库信息
    st.subheader(f"当前词库: {dictionary_info}")
    st.caption(f"文件: {st.session_state.selected_dictionary} | 工作表: {st.session_state.selected_sheet}")
    
    # 显示单词库统计
    st.subheader("单词库信息")
    col1, col2, col3 = st.columns(3)
    col1.metric("单词量", total_words)
    col2.metric("示例单词", df.iloc[0]['英文'] if total_words > 0 else "无")
    col3.metric("中文释义", df.iloc[0]['中文'] if total_words > 0 else "无")
    
    # 显示词库说明
    st.markdown("---")
    st.subheader("可用词库")
    for dict_name, dict_info in available_dictionaries.items():
        st.markdown(f"**{dict_name}**")
        st.write(f"- 文件: {dict_info['file']}")
        st.write(f"- 工作表: {', '.join(dict_info['sheets'])}")
    
    # 显示部分单词预览
    if total_words > 0:
        st.markdown("---")
        st.subheader("单词预览")
        preview_df = df.head(10)[['英文', '中文']]
        st.dataframe(preview_df, use_container_width=True)

# 页脚
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("单词对对碰游戏 | 使用Streamlit和Python制作")
with col2:
    st.markdown(f"<div style='text-align: right; font-size: 12px; color: #666;'>点击次数: {usage_count}次</div>", unsafe_allow_html=True)
