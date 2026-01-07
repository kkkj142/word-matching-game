import streamlit as st
import pandas as pd
import random
import time
from pathlib import Path

# 设置页面
st.set_page_config(page_title="单词对对碰", page_icon="📚", layout="wide")

# 标题和说明
st.title("📚 单词对对碰平台")
st.markdown("""
欢迎来到单词对对碰！这个平台将帮助你记忆英文单词和中文释义。
请从右侧选择与左侧单词对应的正确释义。
""")

# 读取单词数据
@st.cache_data
def load_word_data():
    try:
        # 使用与程序相同路径下的Excel文件
        file_path = Path(__file__).parent / "dictionary.xlsx"
        df = pd.read_excel(file_path, sheet_name="全版")
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

# 加载单词数据
df = load_word_data()
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

# 游戏控制侧边栏
with st.sidebar:
    st.header("游戏控制")
    
    if st.button("🎮 开始游戏") or st.session_state.game_started:
        if not st.session_state.game_started:
            st.session_state.game_started = True
            st.session_state.current_word_index = 0
            st.session_state.score = 0
            st.session_state.start_time = time.time()
            st.session_state.used_indices = set()
            generate_new_word()
            st.rerun()
        
        # 显示游戏统计
        st.subheader("游戏统计")
        elapsed_time = time.time() - st.session_state.start_time if st.session_state.start_time else 0
        st.metric("得分", st.session_state.score)
        st.metric("进度", f"{st.session_state.current_word_index}/{min(20, total_words)}")
        st.metric("用时", f"{int(elapsed_time)}秒")
        
        # 进度条
        st.progress(st.session_state.current_word_index / min(20, total_words))
        
        if st.button("🔄 重新开始"):
            st.session_state.game_started = False
            st.rerun()
    else:
        st.info("点击「开始游戏」按钮开始游戏")

# 游戏主区域
if st.session_state.game_started:
    # 选择当前单词
    if st.session_state.current_word_index < min(20, total_words):
        # 显示当前单词
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("英文单词")
            st.markdown(f"<h1 style='text-align: center; color: blue;'>{st.session_state.current_english}</h1>", unsafe_allow_html=True)
        
        with col2:
            st.subheader("选择正确的中文释义")
            # 创建选项按钮
            selected_option = st.radio(
                "请选择:", 
                st.session_state.options, 
                key=f"option_{st.session_state.current_word_index}",
                index=None if st.session_state.selected_option is None else st.session_state.options.index(st.session_state.selected_option) if st.session_state.selected_option in st.session_state.options else None
            )
            
            # 更新选中的选项
            if selected_option is not None:
                st.session_state.selected_option = selected_option
            
            # 只有在有选择且未提交时才启用提交按钮
            if st.button("提交答案", use_container_width=True, disabled=st.session_state.selected_option is None or st.session_state.answer_submitted):
                st.session_state.answer_submitted = True
                
                if st.session_state.selected_option == st.session_state.current_chinese:
                    st.session_state.score += 1
                    st.success("✅ 正确！")
                else:
                    st.error(f"❌ 错误！正确答案是: {st.session_state.current_chinese}")
                
                # 短暂延迟后进入下一个单词
                time.sleep(1.5)
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
        
        if st.button("再玩一次", use_container_width=True):
            st.session_state.game_started = False
            st.rerun()

else:
    # 游戏说明
    st.info("""
    ### 游戏说明:
    1. 点击侧边栏的"开始游戏"按钮开始游戏
    2. 你会看到英文单词和四个中文释义选项
    3. 选择你认为正确的中文释义
    4. 每答对一题得1分，共20题
    5. 完成后查看你的得分和用时
    """)
    
    # 显示单词库统计
    st.subheader("单词库信息")
    col1, col2, col3 = st.columns(3)
    col1.metric("总单词量", total_words)
    col2.metric("示例单词", df.iloc[0]['英文'] if total_words > 0 else "无")
    col3.metric("中文释义", df.iloc[0]['中文'] if total_words > 0 else "无")
    
    # 显示部分单词预览
    if total_words > 0:
        st.subheader("单词预览")
        preview_df = df.head(10)[['英文', '中文']]
        st.dataframe(preview_df, use_container_width=True)

# 页脚
st.markdown("---")
st.markdown("单词对对碰平台 | 使用Streamlit和Python制作")
